import os
import math
from ssbp import SSBP
from PIL import Image
from PIL.Image import alpha_composite
from split_cell import split_cellmap
from sstypes import SSCell, SSVector2, SSAnimationPart, SSPartState
from utility import create_identity_matrix, translation_matrix_m, rotation_matrix_m, scale_matrix_m


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
        #self.animation_packages = ssbp.animation_packages
        self.animation_packages = {}
        for animation_package in ssbp.animation_packages:
            animations = {}
            for animation in animation_package['animations']['data']:
                animations[animation['name']] = animation
            animation_package['animations'] = animations
            self.animation_packages[animation_package['name']] = animation_package

        self.cells = []
        for cell_map in [ssbp.cell_maps[key]['cells'] for key in ssbp.cell_maps]:
            self.cells.extend(cell_map)

        self.export_path = export_path

    def join_frame_data(self, animation, time):
        frame_data = {}
        for part_index in animation['frame data']['data']:
            frame = animation['frame data']['data'][part_index][time]
            frame_data[frame['part index']] = frame
        if time == 0:
            # Apply initial data over the frame data
            for part_index in animation['initial frame data']['data']:
                initial_frame = animation['initial frame data']['data'][part_index][0]
                frame_data[initial_frame['part index']].update(initial_frame)
        return frame_data

    def render_frame(self, package_name, animation_name, time, debug=True, export_parts=False):
        animation_parts = self.animation_packages[package_name]['animation parts']['data']
        animation = self.animation_packages[package_name]['animations'][animation_name]
        canvas_size = animation['canvas size']
        canvas_scale = 1
        canvas_size = (round(canvas_size[0] * canvas_scale), round(canvas_size[1] * canvas_scale))

        canvas = Image.new('RGBA', canvas_size, (255, 255, 255, 0))

        frame_data = []
        _frame_data = self.join_frame_data(animation, time)

        # Calculate matrices
        for part_index in sorted(_frame_data):
            if part_index == 0:
               matrix = create_identity_matrix()
            else:
               parent_index = animation_parts[part_index]['parent index']
               matrix = _frame_data[parent_index]['matrix']

            matrix = translation_matrix_m(matrix,
                                         _frame_data[part_index]['position x'],
                                         _frame_data[part_index]['position y'],
                                         _frame_data[part_index]['position z'])
            # matrix = rotation_matrix_m(matrix,
            #                           math.radians(_frame_data[part_index]['rotation x']),
            #                           math.radians(_frame_data[part_index]['rotation y']),
            #                           math.radians(_frame_data[part_index]['rotation z']))
            matrix = scale_matrix_m(matrix,
                                   _frame_data[part_index]['scale x'],
                                   _frame_data[part_index]['scale y'],
                                   1.0)
            _frame_data[part_index]['matrix'] = matrix

        # Wrap data
        for part_index in _frame_data:
            # Wrap frame data into SSPartState
            part_state = SSPartState(part_index).from_dict(_frame_data[part_index])
            # Wrap part data into SSAnimationPart
            part_state.part = SSAnimationPart().from_dict(animation_parts[part_state.part])
            if _frame_data[part_index]['cell index'] != -1:
                # Wrap cell data into SSCell
                cell_data = self.cells[_frame_data[part_index]['cell index']]
                part_state.cell = SSCell().from_dict(cell_data)
            else:
                part_state.cell = None
            part_state.matrix = _frame_data[part_index]['matrix']
            frame_data.append(part_state)

        for state in frame_data:
            # Find parents
            for _part_state in frame_data:
                if _part_state.part.index == state.part.parent_index:
                    state.parent = _part_state
                    state.part.parent = _part_state.part

            # Default to cell map pivot
            if state.cell:
                if state.pvtx == 0.0:
                    state.pvtx = state.cell.pivot.x
                if state.pvty == 0.0:
                    state.pvty = state.cell.pivot.y

            # Save parent posx, posy and rotz
            state._posx = 0
            state._posy = 0
            state._rotz = 0
            for parent in state:
                state._posx += parent.posx
                state._posy += parent.posy
                state._rotz += parent.rotz

            # Update vertices
            pivot = SSVector2(0, 0)
            if state.cell:
                cpx = state.cell.pivot.x + 0.5
                if state.flph: cpx = 1 - cpx
                pivot.x = cpx * state.sizx

                cpy = -state.cell.pivot.y + 0.5
                if state.flpv: cpy = 1 - cpy
                pivot.y = cpy * state.sizy
            else:
                pivot.x = 0.5 * state.sizx
                pivot.y = 0.5 * state.sizy

            sx = -pivot.x
            ex = sx + state.sizx
            sy = +pivot.y
            ey = sy - state.sizy

            vtxPosX = [sx, ex, sx, ex]
            vtxPosY = [sy, sy, ey, ey]
            vtxOfs = SSVector2(0, 0)

            if state.vertex:  # or color blend
                raise NotImplementedError
            else:
                for i in range(4):
                    state.vertices[i * 3 + 0] = vtxPosX[i] + vtxOfs.x
                    state.vertices[i * 3 + 1] = vtxPosY[i] + vtxOfs.y
                    state.vertices[i * 3 + 2] = 0
                    vtxOfs += 1

        for state in frame_data:
            if state.instance:
                print('! Animation instances are not implemented')
            if state.vertex:
                print('! Vertex transformation is not implemented')
            if state.hide or not state.cell:
                continue

            try:
                # Open the part sprite
                part_sprite = Image.open(
                    os.path.join(self.export_path, f"tex/{state.cell.name}.png"))
            except FileNotFoundError:
                print(f"! {unit}/tex/{state.cell.name}.png wasn't found, skipping")
                continue

            if state.flph or state.sclx < 0:
                part_sprite = part_sprite.transpose(Image.FLIP_LEFT_RIGHT)
                # state.pvty = -state.pvty
            if state.flpv or state.scly < 0:
                part_sprite = part_sprite.transpose(Image.FLIP_TOP_BOTTOM)
                # state.pvtx = -state.pvtx
            if abs(state.sclx) != 1.0 or abs(state.scly) != 1.0:
                part_sprite = part_sprite.resize(
                    (round(abs(state.sclx) * state.sizx),
                     round(abs(state.scly) * state.sizy)),
                    resample=Image.BICUBIC
                )
            if state.rotz + state._rotz:
                part_sprite = part_sprite.rotate(
                    angle=round(state.rotz + state._rotz),
                    resample=Image.BICUBIC,
                    expand=True,
                    center=(
                        round((state.sizx / 2) - state.cell.pivot.x * state.sizx),
                        round((state.sizy / 2) + state.cell.pivot.y * state.sizy)
                    )
                )

            absx = (canvas_size[0] - state.sizx) / 2  # center the part
            absy = (canvas_size[1] - state.sizy) / 2  # at canvas center
            absx += state.matrix[12]  # x
            absy -= state.matrix[13]  # y
            absx -= (state.pvtx * state.sizx)  # pivot
            absy -= (state.pvty * state.sizy)  # offset
            absx += (state.sizx - part_sprite.size[0]) / 2  # offset for dimension changes after sprite manipulation
            absy += (state.sizy - part_sprite.size[1]) / 2  # e.g., canvas expansion after rotation

            absx = round(absx)
            absy = round(absy + 95)
            if debug:
                print(f"- Parent rotation {state._rotz:.2f} | Pivot offset ({round(state.pvtx * state.sizx)}, {round(state.pvty * state.sizy)}) | Matrix {state.matrix[12:-2]} | Vertices {state.vertices[:-3]}")
                print(f"- {state}")
                for parent in state:
                    print(f"| {parent}")

            canvas.alpha_composite(part_sprite, dest=(absx, absy))
            if export_parts:
                part_canvas = Image.new('RGBA', canvas_size, (255, 255, 255, 0))
                part_canvas.alpha_composite(part_sprite, dest=(absx, absy))
                part_canvas.save(
                    os.path.join(
                        self.export_path,
                        f"{animation_name}-{time}-{state.part.index}-{state.part.name}.png"
                    )
                )
        return canvas


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
        sprite = fd.render_frame('body_anim', 'Idle', 0)
        sprite.save(f'output/{unit}/body_anim-Idle-0.png')
        # sprite.show()
