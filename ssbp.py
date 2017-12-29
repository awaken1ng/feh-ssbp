from sstypes import SSWrapMode, SSFilterMode, SSPartType, SSBoundsType, SSBlendType
from utility import read_i16le, read_i32le, read_f32le, read_str_from_pointer, peek


class SSBP:
    def __init__(self, input_buffer, debug=False, dump_initial_frames=False, dump_frames=False):
        self.input_buffer = input_buffer
        self.signature = read_i32le(input_buffer)
        assert self.signature == 0x42505353
        self.version = read_i32le(input_buffer)
        input_buffer.seek(8, 1)  # Step over headflag and imageBaseDir position
        self.cell_data_pointer = read_i32le(input_buffer)
        self.animation_pack_pointer = read_i32le(input_buffer)
        input_buffer.seek(4, 1)  # effectfileArray pointer
        self.cells_count = read_i16le(input_buffer)
        self.animation_pack_count = read_i16le(input_buffer)

        if debug:
            print(f'Cell data pointer {self.cell_data_pointer} | {hex(self.cell_data_pointer)}')
            print(f'Animation pack pointer {self.animation_pack_pointer} | {hex(self.animation_pack_pointer)}')
            print(f'Amount of cells {self.cells_count}')
            print(f'Amount of animation packages {self.animation_pack_count}')
            print('\nReading cell data...')

        # Cell data
        self.cell_maps = {}
        input_buffer.seek(self.cell_data_pointer)
        for _ in range(self.cells_count):
            cell = {
                'name': read_str_from_pointer(input_buffer, read_i32le(input_buffer))
            }

            # Read the cell map and seek back
            with peek(input_buffer, read_i32le(input_buffer)) as name_buffer:
                map_name = read_str_from_pointer(name_buffer, read_i32le(name_buffer))
                cell_map = {
                    'name': map_name,
                    'image path': read_str_from_pointer(name_buffer, read_i32le(name_buffer)),
                    'wrap mode': SSWrapMode.get(read_i16le(name_buffer)),
                    'filter mode': SSFilterMode.get(read_i16le(name_buffer)),
                    'cells': []
                }

            cell.update({
                'index': read_i16le(input_buffer),
                'pos': (read_i16le(input_buffer), read_i16le(input_buffer)),
                'size': (read_i16le(input_buffer), read_i16le(input_buffer))
            })
            input_buffer.seek(2, 1)  # reserved, always 0x0000
            cell['pivot'] = (read_f32le(input_buffer), read_f32le(input_buffer))

            if map_name not in self.cell_maps.keys():
                self.cell_maps[map_name] = cell_map
            self.cell_maps[map_name]['cells'].append(cell)

            if debug:
                cell['map'] = {
                    'name': cell_map['name'],
                    'image path': cell_map['image path'],
                    'wrap mode': cell_map['wrap mode'],
                    'filter mode': cell_map['filter mode']
                }
                print(f'| Cell {cell}')

        # Animation package
        if debug:
            print('\nReading animation packages...')
        self.animation_packages = []
        input_buffer.seek(self.animation_pack_pointer)
        for _ in range(self.animation_pack_count):
            if debug:
                print('\nReading animation package №' + str(_ + 1))
            package = {
                'name': read_str_from_pointer(input_buffer, read_i32le(input_buffer)),
                'animation parts': {'count': None, 'data': []},
                'animations': {'count': None, 'data': []}
            }
            parts_pointer = read_i32le(input_buffer)
            animations_pointer = read_i32le(input_buffer)
            package['animation parts']['count'] = read_i16le(input_buffer)
            package['animations']['count'] = read_i16le(input_buffer)

            if debug:
                package['animation parts']['pointer'] = parts_pointer
                package['animations']['pointer'] = animations_pointer
                print(f'| Animation package {package}')

            with peek(input_buffer, parts_pointer) as parts_buffer:
                if debug:
                    print('Reading parts from animation package ' + package['name'])
                for _ in range(package['animation parts']['count']):
                    animation_part = {
                        'name': read_str_from_pointer(parts_buffer, read_i32le(parts_buffer)),
                        'index': read_i16le(parts_buffer),
                        'parent index': read_i16le(parts_buffer),
                        'type': SSPartType.get(read_i16le(parts_buffer)),
                        'bounds type': SSBoundsType.get(read_i16le(parts_buffer)),
                        'alpha blend type': SSBlendType.get(read_i16le(parts_buffer))
                    }
                    parts_buffer.seek(2, 1)
                    animation_part.update({
                        'animation instance name': read_str_from_pointer(parts_buffer, read_i32le(parts_buffer)),
                        'effect name': read_str_from_pointer(parts_buffer, read_i32le(parts_buffer)),
                        'color': read_str_from_pointer(parts_buffer, read_i32le(parts_buffer))
                    })
                    if debug:
                        print(f'| Animation part {animation_part}')
                    package['animation parts']['data'].append(animation_part)

            with peek(input_buffer, animations_pointer) as animations_buffer:
                if debug:
                    print('Reading animations from animation package ' + package['name'])
                for _ in range(package['animations']['count']):
                    animation = {
                        'name': read_str_from_pointer(animations_buffer, read_i32le(animations_buffer)),
                        'initial frame data': {'pointer': read_i32le(animations_buffer), 'data': {}},
                        'frame data': {'pointer': read_i32le(animations_buffer), 'data': {}},
                        'user data': {'pointer': read_i32le(animations_buffer), 'data': None},
                        'label data': {'pointer': read_i32le(animations_buffer), 'data': {}, 'count': None},
                        'frame count': read_i16le(animations_buffer),
                        'fps': read_i16le(animations_buffer)
                    }
                    animation['label data']['count'] = read_i16le(input_buffer)
                    animation['canvas size'] = (read_i16le(input_buffer), read_i16le(input_buffer))  # width, height
                    animations_buffer.seek(2, 1)

                    if debug:
                        print('| Animation ' + repr(animation))

                    # Read initial frame data for each animation part
                    with peek(input_buffer, animation['initial frame data']['pointer']) as initial_data_buffer:
                        for part_index in range(package['animation parts']['count']):
                            initial_data = {
                                'part index': read_i16le(initial_data_buffer),
                                'invisible': False,
                                'flip h': False,
                                'flip v': False,
                            }
                            initial_data_buffer.seek(2, 1)
                            # Decode the flags
                            flags_value = read_i32le(initial_data_buffer)
                            flags_data = [
                                ('invisible', 0),
                                ('flip h', 1),
                                ('flip v', 2)
                            ]
                            for flag, index in flags_data:
                                if flags_value & (1 << index):
                                    initial_data.update({flag: True})
                            initial_data.update({
                                'cell index': read_i16le(initial_data_buffer),
                                'position x': round(read_i16le(initial_data_buffer) / 10),
                                'position y': round(read_i16le(initial_data_buffer) / 10),
                                'position z': round(read_i16le(initial_data_buffer) / 10),
                                'opacity': read_i16le(initial_data_buffer)
                            })
                            initial_data_buffer.seek(2, 1)
                            initial_data.update({
                                'pivot x': read_f32le(initial_data_buffer),
                                'pivot y': read_f32le(initial_data_buffer),
                                'rotation x': read_f32le(initial_data_buffer),
                                'rotation y': read_f32le(initial_data_buffer),
                                'rotation z': read_f32le(initial_data_buffer),
                                'scale x': read_f32le(initial_data_buffer),
                                'scale y': read_f32le(initial_data_buffer),
                                'size x': read_f32le(initial_data_buffer),
                                'size y': read_f32le(initial_data_buffer),
                                'u move': read_f32le(initial_data_buffer),
                                'v move': read_f32le(initial_data_buffer),
                                'uv rotation': read_f32le(initial_data_buffer),
                                'u scale': read_f32le(initial_data_buffer),
                                'v scale': read_f32le(initial_data_buffer),
                                'bounding radius': read_f32le(initial_data_buffer)
                            })
                            if debug and dump_initial_frames:
                                print(f"|- Initial frame {initial_data}")
                            if part_index not in animation['initial frame data']['data'].keys():
                                animation['initial frame data']['data'][part_index] = []
                            animation['initial frame data']['data'][part_index].append(initial_data)

                    # Read frame data for each animation part
                    with peek(input_buffer, animation['frame data']['pointer']) as frame_data_buffer:
                        for frame_index in range(animation['frame count']):
                            with peek(frame_data_buffer, read_i32le(frame_data_buffer)) as frame_data_buffer:
                                for _ in range(package['animation parts']['count']):
                                    frame = {
                                        'part index': read_i16le(frame_data_buffer),
                                    }
                                    flags_value = read_i32le(frame_data_buffer)
                                    if flags_value:
                                        flags_data = [
                                            ('invisible', 0, 'boolean'),
                                            ('flip h', 1, 'boolean'),
                                            ('flip v', 2, 'boolean'),
                                            ('cell index', 3, 'i16'),
                                            ('position x', 4, 'i16*10.0'),
                                            ('position y', 5, 'i16*10.0'),
                                            ('position z', 6, 'i16*10.0'),
                                            ('pivot x', 7, 'f32'),
                                            ('pivot y', 8, 'f32'),
                                            ('rotation x', 9, 'f32'),
                                            ('rotation y', 10, 'f32'),
                                            ('rotation z', 11, 'f32'),
                                            ('scale x', 12, 'f32'),
                                            ('scale y', 13, 'f32'),
                                            ('opacity', 14, 'i16'),
                                            ('size x', 17, 'f32'),
                                            ('size y', 18, 'f32'),
                                            ('u move', 19, 'f32'),
                                            ('v move', 20, 'f32'),
                                            ('uv rotation', 21, 'f32'),
                                            ('u scale', 22, 'f32'),
                                            ('v scale', 23, 'f32'),
                                            ('bounding radius', 24, 'f32'),
                                            ('vertex transform', 16, 'vertices'),
                                            ('color blend', 15, 'color blend'),
                                            ('instance keyframe', 25, 'i16'),
                                            ('instance start', 26, 'i16'),
                                            ('instance end', 27, 'i16'),
                                            ('instance speed', 28, 'f32'),
                                            ('instance loop', 29, 'i16'),
                                            ('instance loop flags', 30, 'i16')
                                        ]
                                        flags = {}
                                        for flag, index, value_type in flags_data:
                                            if flags_value & (1 << index):
                                                if value_type == 'boolean':
                                                    flags[flag] = True
                                                elif value_type == 'i16':
                                                    flags[flag] = read_i16le(input_buffer)
                                                    if flag == 'instance loop flags':
                                                        # Decode instance loop flags
                                                        instance_flags_data = [
                                                            ('infinity', 0),
                                                            ('reverse', 1),
                                                            ('pingpong', 2),
                                                            ('independent', 3)
                                                        ]
                                                        instance_flags = {}
                                                        for instance_flag, index in instance_flags_data:
                                                            if flags[flag] & (1 << index):
                                                                instance_flags[instance_flag] = True
                                                            else:
                                                                instance_flags[instance_flag] = False
                                                        flags[flag] = instance_flags
                                                elif value_type == 'i16*10.0':
                                                    flags[flag] = round(read_i16le(input_buffer) / 10)
                                                elif value_type == 'f32':
                                                    flags[flag] = read_f32le(input_buffer)
                                                elif value_type == 'vertices':
                                                    flags[flag] = {'flags': None, 'data': []}
                                                    vertices_flags = read_i16le(frame_data_buffer)
                                                    if debug:
                                                        flags[flag]['flags value'] = vertices_flags
                                                    for vertex_index in range(4):
                                                        if vertices_flags & (1 << vertex_index):
                                                            flags[flag]['data'].append(
                                                                (read_i16le(frame_data_buffer), read_i16le(frame_data_buffer)))
                                                elif value_type == 'color blend':
                                                    raise NotImplementedError
                                                    # Not tested
                                                    type_and_flags = read_i16le(input_buffer)
                                                    if type_and_flags & 4096:
                                                        flags[flag] = [{'rate': read_f32le(input_buffer), 'rgba': read_i32le(input_buffer)}]
                                                    else:
                                                        flags[flag] = []
                                                        for vertex_index in range(4):
                                                            if type_and_flags & (1 << vertex_index):
                                                                flags[flag].append({'rate': read_f32le(input_buffer), 'rgba': read_i32le(input_buffer)})
                                        frame.update(flags)

                                    part_index = frame['part index']
                                    if debug and dump_frames:
                                        frame['flags value'] = flags_value
                                        print(f"|- Frame {frame_index + 1} of part {part_index + 1}  {frame}")

                                    if part_index not in animation['frame data']['data'].keys():
                                        animation['frame data']['data'][part_index] = []
                                    animation['frame data']['data'][part_index].append(frame)

                    # TODO Read the user data if it's present
                    if animation['user data']['pointer']:
                        raise NotImplementedError
                        with peek(input_buffer, animation['user data']['pointer']) as user_data_array_buffer:
                            for _ in range(animation['frame count']):
                                with peek(user_data_array_buffer, read_i32le(user_data_array_buffer)) as user_data_buffer:
                                    for _ in range(package['animation parts']['count']):
                                        pass
                                        # for each attribute
                                            # flags_value = read_i16
                                            # part_index= read_i16
                                            # if data_type

                    # Read the label data if it's present
                    if animation['label data']['pointer']:
                        with peek(input_buffer, animation['label data']['pointer']) as label_data_array_buffer:
                            for _ in range(animation['label data']['count']):
                                with peek(label_data_array_buffer, read_i32le(label_data_array_buffer)) as label_data_buffer:
                                    name = read_str_from_pointer(label_data_buffer, read_i32le(label_data_buffer))
                                    time = read_i16le(label_data_buffer)
                                    animation['label data']['data'][name] = time

                    package['animations']['data'].append(animation)
            self.animation_packages.append(package)


if __name__ == "__main__":
    unit = 'ch04_12_Tiki_F_Normal'
    with open(f'data/Unit/{unit}/{unit}.ssbp', 'rb') as file:
        ssbp = SSBP(file, debug=True, dump_initial_frames=False, dump_frames=False)

