import os
from ssbp import SSBP
from PIL import Image
from PIL.Image import FLIP_LEFT_RIGHT, FLIP_TOP_BOTTOM, alpha_composite
from split_cell import split_cellmap


# Override the Image class to disable the check for destination value < 0
class _Image(Image.Image):
    def alpha_composite(self, im, dest=(0,0), source=(0,0)):
        if not isinstance(source, (list, tuple)):
            raise ValueError("Source must be a tuple")
        if not isinstance(dest, (list, tuple)):
            raise ValueError("Destination must be a tuple")
        if not len(source) in (2, 4):
            raise ValueError("Source must be a 2 or 4-tuple")
        if not len(dest) == 2:
            raise ValueError("Destination must be a 2-tuple")
        if min(source) < 0:
            raise ValueError("Source must be non-negative")
        if len(source) == 2:
            source = source + im.size
        if source == (0,0) + im.size:
            overlay = im
        else:
            overlay = im.crop(source)
        box = dest + (dest[0] + overlay.width, dest[1] + overlay.height)
        if box == (0,0) + self.size:
            background = self
        else:
            background = self.crop(box)
        result = alpha_composite(background, overlay)
        self.paste(result, box)
Image.Image = _Image


class SSFrameDecoder:
    def __init__(self, ssbp, export_path):
        self.ssbp = ssbp
        self.cell_maps = ssbp.cell_maps
        self.animation_packages = ssbp.animation_packages
        self.cells = []
        for cell_map in [ssbp.cell_maps[key]['cells'] for key in ssbp.cell_maps]:
            self.cells.extend(cell_map)

        self.export_path = export_path
    def export_frame(self, first_frame_only=True, export_parts=False, debug=False):
        for animation_package in self.animation_packages:
            animation_package_name = animation_package['name']
            animation_parts = animation_package['animation parts']['data']
            animations = animation_package['animations']['data']
            for animation_index, animation in enumerate(animations):
                animation_name = animation['name']
                canvas_size = animation['canvas size']
                frame_count = animation['frame count']
                initial_frame_data = animation['initial frame data']['data']
                main_frame_data = animation['frame data']['data']

                if debug:
                    print(f'| Animation name: {animation_name}')
                state = {}
                if first_frame_only:
                    frame_count = 1

                for frame_index in range(frame_count):
                    # Join the frame data
                    frame_data = []
                    for part_index in main_frame_data:
                        frame_data.append(main_frame_data[part_index][frame_index])
                    if frame_index == 0:
                        for part_index in initial_frame_data:
                            initial_frame = initial_frame_data[part_index][0]
                            for index, part in enumerate(frame_data):
                                if part['part index'] == initial_frame['part index']:
                                    frame_data[index].update(initial_frame)

                    # Update the part states for current frame
                    for part in frame_data:
                        if frame_index == 0:
                            state[part['part index']] = part
                        else:
                            state[part['part index']].update(part)

                    if debug:
                        print(f'| Frame {frame_index + 1}')
                    canvas = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
                    for part in frame_data:
                        part_state = state[part['part index']]
                        part_index = part_state['part index']
                        part_data = animation_parts[part_index]
                        if debug:
                            print(f"| {part_data['name']} {part_data['type']} | {part_state}")
                        parent_index = animation_parts[part_index]['parent index']
                        cell_index = part_state['cell index']
                        cell_data = self.cells[cell_index] if cell_index != -1 else None
                        if parent_index != -1 and cell_index != -1 and not part_state['invisible'] and part_data['type'].value == 1:
                            try:
                                # Get the parent data
                                parent_pos_x = parent_pos_y = parent_rot_z = 0
                                while parent_index != -1:
                                    parent_part_state = state[parent_index]
                                    parent_part_data = animation_parts[parent_index]
                                    if debug:
                                        print(f"- {parent_part_data['name']} {parent_part_data['type']} | {parent_part_state}")
                                    parent_pos_x += parent_part_state['position x']
                                    parent_pos_y += parent_part_state['position y']
                                    parent_rot_z += parent_part_state['rotation z']
                                    parent_index = animation_parts[parent_index]['parent index']

                                # Open the sprite
                                part = Image.open(os.path.join(self.export_path, f"tex/{cell_data['name']}.png"))

                                # TODO implement these
                                if part_state['position z'] != 0.0 or part_state['opacity'] != 255 \
                                        or part_state['pivot x'] != 0.0 or part_state['pivot y'] != 0.0 \
                                        or part_state['rotation x'] != 0.0 or part_state['rotation y'] != 0.0 \
                                        or part_state['u move'] != 0.0 or part_state['v move'] != 0.0 \
                                        or part_state['uv rotation'] != 0.0 \
                                        or part_state['u scale'] != 1.0 or part_state['v scale'] != 1.0 \
                                        or part_state['bounding radius'] != 0.0:
                                    raise NotImplementedError
                                if 'vertex transform' in part_state.keys():
                                    raise NotImplementedError

                                # Pre-process the part if necessary before pasting onto canvas
                                if part_state['flip h'] or part_state['scale x'] < 0:
                                    part = part.transpose(FLIP_LEFT_RIGHT)
                                if part_state['flip v'] or part_state['scale y'] < 0:
                                    part = part.transpose(FLIP_TOP_BOTTOM)
                                if part_state['rotation z'] + parent_rot_z != 0.0:
                                    part = part.rotate(part_state['rotation z'] + parent_rot_z, resample=Image.BICUBIC, expand=False)
                                if abs(part_state['scale x']) != 1.0 or abs(part_state['scale y']) != 1.0:
                                    part = part.resize(
                                        (round(abs(part_state['scale x']) * part_state['size x']),
                                         round(abs(part_state['scale y']) * part_state['size y'])),
                                        resample=Image.BICUBIC
                                    )
                                if part.size[0] != part_state['size x'] or part.size[1] != part_state['size y']:
                                    # Resize the image
                                    # WARNING Can clip the parts
                                    # If expand is True when rotating the part, this shouldn't be necessary
                                    resized_part = Image.new('RGBA', (round(part_state['size x']), round(part_state['size y'])), (255, 255, 255, 0))
                                    cx = (part_state['size x'] - part.size[0]) / 2
                                    cy = (part_state['size y'] - part.size[1]) / 2
                                    resized_part.alpha_composite(part, dest=(round(cx), round(cy)))
                                    part = resized_part

                                # Center the part at the canvas center
                                abs_x = (canvas_size[0] - part_state['size x']) / 2
                                abs_y = (canvas_size[1] - part_state['size y']) / 2
                                # Apply the relative offset
                                offset_x = cell_data['pivot'][0] * cell_data['size'][0]
                                offset_y = cell_data['pivot'][1] * cell_data['size'][1]
                                abs_x += part_state['position x'] + parent_pos_x - offset_x
                                abs_y -= part_state['position y'] + parent_pos_y + offset_y

                                # Workaround for centering the sprite
                                # TODO proper centering
                                abs_x -= 10
                                abs_y += 95

                                canvas.alpha_composite(part, dest=(round(abs_x), round(abs_y)))
                                canvas.save(os.path.join(self.export_path,
                                                         f'{animation_package_name}-{animation_name}-{frame_index + 1}.png'))
                                if export_parts:
                                    part_canvas = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
                                    part_canvas.alpha_composite(part, dest=(round(abs_x), round(abs_y)))
                                    part_canvas.save(os.path.join(self.export_path,
                                                                  f'{animation_package_name}-{animation_name}-{frame_index + 1}-{part_index}.png'))
                            except FileNotFoundError:
                                print(f"! {unit}/tex/{cell_data['name']}.png wasn't found, skipping")
                                pass


if __name__ == "__main__":
    unit = 'ch04_12_Tiki_F_Normal'

    with open(f'data/Unit/{unit}/{unit}.ssbp', 'rb') as file:
        ssbp = SSBP(file, debug=False, dump_initial_frames=False, dump_frames=False)

        for path in ['output', f'output/{unit}', f'output/{unit}/tex']:
            if not os.path.exists(path):
                os.mkdir(path)

        if ssbp.cells_count / 1.2 > len([name for name in os.listdir(f'output/{unit}/tex') if not os.path.isdir(name)]):
            print(f'Splitting the {unit} cell map')
            split_cellmap(unit, ssbp)
        fd = SSFrameDecoder(ssbp, export_path=f'output/{unit}')
        fd.export_frame(debug=True, first_frame_only=True, export_parts=False)

