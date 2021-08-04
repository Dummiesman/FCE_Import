# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2021
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh, mathutils
import time, struct, io, math, os
from bpy_extras.io_utils import axis_conversion

from io_scene_fce.fce_header import *

# constants
HEADER_SIZE = 8248

# globals
global tpages
tpages = {}

global tpage_materials
tpage_materials = {}

######################################################
# HELPERS
######################################################
def get_tpage(fce_path, tpage_num):
    global tpages
    if tpage_num in tpages:
        return tpages[tpage_num]
    
    base = os.path.basename(fce_path)
    fce_name = os.path.splitext(base)[0]
    fce_dir = os.path.dirname(fce_path)
    
    # NFS4
    tpage_file = fce_name + "{0:0=2d}".format(tpage_num) + ".tga"
    tpage_path = os.path.join(fce_dir, tpage_file)

    if os.path.exists(tpage_path):
        img = bpy.data.images.load(tpage_path)
        if img is not None:
            tpages[tpage_num] = img
            img.alpha_mode = 'CHANNEL_PACKED'
        return img
    
    # MCO
    tpage_file = "{0:0=4d}".format(tpage_num) + ".bmp"
    tpage_path = os.path.join(fce_dir, tpage_file)
    if os.path.exists(tpage_path):
        img = bpy.data.images.load(tpage_path)
        if img is not None:
            tpages[tpage_num] = img
            img.alpha_mode = 'CHANNEL_PACKED'
        return img
    
    return None

def get_tpage_material(fce_path, tpage_num):
    global tpage_materials
    if tpage_num in tpage_materials:
        return tpage_materials[tpage_num]
        
    # create a new material
    mtl = bpy.data.materials.new(name="tpage_" + str(tpage_num))
    tpage_materials[tpage_num] = mtl
    
    mtl.use_nodes = True
    mtl.use_backface_culling = True

    mtl.specular_intensity = 0.1
    mtl.blend_method = 'HASHED' 
    
    bsdf = mtl.node_tree.nodes["Principled BSDF"]
        
    # setup textures
    tpage_texture = get_tpage(fce_path, tpage_num)
    if tpage_texture is not None:
        tex_image_node = mtl.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image_node.image = tpage_texture
        tex_image_node.location = mathutils.Vector((-640.0, 20.0))
        
        mtl.node_tree.links.new(bsdf.inputs['Base Color'], tex_image_node.outputs['Color'])
        mtl.node_tree.links.new(bsdf.inputs['Alpha'], tex_image_node.outputs['Alpha'])
    
    return mtl    

######################################################
# IMPORT MAIN FILES
######################################################
def load_dummy(file, fce_header, dummy_index):
    scn = bpy.context.scene

    obj_name = fce_header.dummy_names[dummy_index]
    ob = bpy.data.objects.new(obj_name, None)
    
    ob.empty_display_type = 'SPHERE'
    ob.empty_display_size = 0.25
    ob.show_name = True
    
    scn.collection.objects.link(ob)
    
    # set object position
    dummy_position = fce_header.dummy_coords[dummy_index]
    ob.location = (dummy_position[0], dummy_position[2], dummy_position[1])


def load_part(file, fce_path, fce_header, part_index):
    # create a Blender object and link it
    scn = bpy.context.scene

    obj_name = fce_header.part_names[part_index]
    me = bpy.data.meshes.new(obj_name + '_Mesh')
    ob = bpy.data.objects.new(obj_name, me)

    bm = bmesh.new()
    bm.from_mesh(me)
    
    scn.collection.objects.link(ob)
    
    # add shape keys
    ob.shape_key_add(name="Basis")
    dmg_sk = bm.verts.layers.shape.new("Damage")

    # set object position
    part_position = fce_header.part_coords[part_index]
    ob.location = (part_position[0], part_position[2], part_position[1])
    
    # materials remapping
    ob_material_remap = {}
    
    # create layers for this object
    uv_layer = bm.loops.layers.uv.new()
    
    # read vertices
    file.seek(HEADER_SIZE + fce_header.vert_table_offset + (12 * fce_header.part_first_vert_indices[part_index]), 0)
    for x in range(fce_header.part_num_vertices[part_index]):
        vx, vz, vy = struct.unpack('<fff', file.read(12))
        vert = bm.verts.new((vx, vy, vz))
    bm.verts.ensure_lookup_table()
    
    # read damage vertices
    file.seek(HEADER_SIZE + fce_header.dmg_verts_offset + (12 * fce_header.part_first_vert_indices[part_index]), 0)
    for x in range(fce_header.part_num_vertices[part_index]):
        vx, vz, vy = struct.unpack('<fff', file.read(12))
        vert = bm.verts[x]
        vert[dmg_sk] = (vx, vy, vz)

    # read faces
    fce_triangle_size = 56
    file.seek(HEADER_SIZE + fce_header.triangles_table_offset + (fce_triangle_size * fce_header.part_first_tri_indices[part_index]), 0)
    for x in range(fce_header.part_num_triangles[part_index]):
        # read face data
        tpage = struct.unpack('<L', file.read(4))[0]
        index0, index1, index2 = struct.unpack('<LLL', file.read(12))
        file.seek(12, 1) # seek past padding
        flags = struct.unpack('<L', file.read(4))[0]
        face_uv = struct.unpack('<ffffff', file.read(24))
        
        backface_flag = (flags & 0x04) != 0
        
        # get material index
        face_material_remapped = -1
        if tpage in ob_material_remap:
            face_material_remapped = ob_material_remap[tpage]
        else:
            material = get_tpage_material(fce_path, tpage)
            ob.data.materials.append(material)
            
            ob_material_remap[tpage] = len(ob.data.materials) - 1
            face_material_remapped = len(ob.data.materials) - 1
         
        
        # create face
        try:
            verts = (bm.verts[index0], bm.verts[index1], bm.verts[index2])
            face = bm.faces.new(verts)
            face.smooth = True
            
            for uv_loop in range(3):
                face.loops[uv_loop][uv_layer].uv = (face_uv[uv_loop], 1 - face_uv[uv_loop + 3])
            
            if face_material_remapped >= 0:
                face.material_index = face_material_remapped
            
            # create backface
            if backface_flag:
                bverts = (bm.verts.new(verts[2].co, verts[2]), bm.verts.new(verts[1].co, verts[1]), bm.verts.new(verts[0].co, verts[0]))
                backface= bm.faces.new(bverts)
                backface.smooth = True
                
                for uv_loop in range(3):
                    backface.loops[3 - uv_loop - 1][uv_layer].uv = (face_uv[uv_loop], 1 - face_uv[uv_loop + 3])
                
                if face_material_remapped >= 0:
                    backface.material_index = face_material_remapped
                    
                bm.verts.ensure_lookup_table()
        except Exception as e:
            print("Failed to create face: " + str(e))


    # calculate normals
    bm.normal_update()
    
    # free resources
    bm.to_mesh(me)
    bm.free()


######################################################
# IMPORT
######################################################
def load_fce(filepath,
             context):

    print("importing FCE: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.perf_counter()
    file = open(filepath, 'rb')
    
    # reset globals
    global tpages
    tpages = {}

    global tpage_materials
    tpage_materials = {}

    # check magic
    mco_header = 0x00101015
    nfs4_header = 0x00101014
    
    magic, unknown = struct.unpack('<LL', file.read(8))
    if magic != nfs4_header and magic != mco_header:
        file.close()
        raise Exception("Not a valid FCE file. Magic is incorrect.")
    
    # read header
    fce_header = FCEHeader(file)
    
    # load parts
    for part_index in range(fce_header.part_count):
        load_part(file, filepath, fce_header, part_index)
    
    # load dummies
    for dummy_index in range(fce_header.dummy_count):
        load_dummy(file, fce_header, dummy_index)
        
    print(" done in %.4f sec." % (time.perf_counter() - time1))
    
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_fce(filepath,
             context,
             )

    return {'FINISHED'}
