import struct

class FCEHeader:
    def __init__(self, file):
        self.num_triangles, self.num_vertices, self.num_arts = struct.unpack('<LLL', file.read(12))
        self.vert_table_offset, self.normals_table_offset, self.triangles_table_offset = struct.unpack('<LLL', file.read(12))
        
        temp_store_offsets = struct.unpack('<LLL', file.read(12))
        
        self.undmg_verts_offset, self.undmg_normals_offset = struct.unpack('<LL', file.read(8))
        self.dmg_verts_offset, self.dmg_normals_offset = struct.unpack('<LL', file.read(8))
        
        unk_area_offset, self.driver_movement_offset, unk_offset_a, unk_offset_b = struct.unpack('<LLLL', file.read(16))
        
        self.model_extents = struct.unpack('<fff', file.read(12))
        
        # dummies
        self.dummy_count = struct.unpack('<L', file.read(4))[0]
        self.dummy_coords = []
        for x in range(16):
            dummy_coord = struct.unpack('<fff', file.read(12))
            self.dummy_coords.append(dummy_coord)
        
        # parts
        self.part_count = struct.unpack('<L', file.read(4))[0]
        self.part_coords = []
        for x in range(64):
            part_coord = struct.unpack('<fff', file.read(12))
            self.part_coords.append(part_coord)
            
        self.part_first_vert_indices = struct.unpack('<64L', file.read(256))
        self.part_num_vertices = struct.unpack('<64L', file.read(256))
        self.part_first_tri_indices = struct.unpack('<64L', file.read(256))
        self.part_num_triangles = struct.unpack('<64L', file.read(256))
        
        # colors
        self.color_count = struct.unpack('<L', file.read(4))[0]
        self.primary_colors = []
        self.interior_colors = []
        self.secondary_colors = []
        self.hair_colors = []
        
        for x in range(16):
            self.primary_colors.append(struct.unpack('<BBBB', file.read(4)))
        for x in range(16):
            self.interior_colors.append(struct.unpack('<BBBB', file.read(4)))
        for x in range(16):
            self.secondary_colors.append(struct.unpack('<BBBB', file.read(4)))
        for x in range(16):
            self.hair_colors.append(struct.unpack('<BBBB', file.read(4)))
        
        # the rest
        unknown_table = file.read(260)
        
        self.dummy_names = []
        for x in range(16):
            dummy_name_bytes = bytearray(file.read(64))
            dummy_name = dummy_name_bytes.decode("utf-8").rstrip('\x00')
            self.dummy_names.append(dummy_name)

        self.part_names = []
        for x in range(64):
            part_name_bytes = bytearray(file.read(64))
            part_name = part_name_bytes.decode("utf-8").rstrip('\x00')
            self.part_names.append(part_name)
            
        unknown_table_2 = file.read(528)