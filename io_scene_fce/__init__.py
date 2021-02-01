# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2021
#
# ##### END LICENSE BLOCK #####

bl_info = {
    "name": "NFS4 FCE Format",
    "author": "Dummiesman",
    "version": (0, 0, 1),
    "blender": (2, 90, 1),
    "location": "File > Import-Export",
    "description": "Import NFS4 FCE files",
    "warning": "",
    "doc_url": "https://github.com/Dummiesman/FCE_Import/",
    "tracker_url": "https://github.com/Dummiesman/FCE_Import/",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy
import textwrap 

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        )

from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )


class ImportFCE(bpy.types.Operator, ImportHelper):
    """Import from NFS4 FCE file format"""
    bl_idname = "import_scene.fce"
    bl_label = 'Import NFS4 FCE File'
    bl_options = {'UNDO'}

    filename_ext = ".fce"
    filter_glob: StringProperty(default="*.fce", options={'HIDDEN'})

    def execute(self, context):
        from . import import_fce
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_fce.load(self, context, **keywords)


# Add to a menu
def menu_func_import_fce(self, context):
    self.layout.operator(ImportFCE.bl_idname, text="NFS4 (.fce)")


# Register factories
def register():
    bpy.utils.register_class(ImportFCE)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_fce)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_fce)
    bpy.utils.unregister_class(ImportFCE)


if __name__ == "__main__":
    register()
