import os
from ssbp import SSBP

if __name__ == "__main__":
    unit = 'ch04_12_Tiki_F_Normal'

    with open(f'data/Unit/{unit}/{unit}.ssbp', 'rb') as file:
        ssbp = SSBP(file, debug=True)
        print('---')

        for animation_package in ssbp.animation_packages:
            animation_parts = animation_package['animation parts']['data']
            for animation in animation_package['animations']['data']:
                print(animation)
                print(f"Canvas size - {animation['canvas size']}")

                if not os.path.exists(f'output/{unit}'):
                    os.mkdir(f'output/{unit}')
                if not os.path.exists(f'output/{unit}/frames'):
                    os.mkdir(f'output/{unit}/frames/')

                with open(f"output/{unit}/frames/{animation['name']}.initial_frame_data", 'w') as output:
                    output.write(f"Animation name - {animation['name']}\n")
                    output.write(f"Canvas size - {animation['canvas size']}\n")
                    output.write(f"Frames - {animation['frame count']}\n")
                    output.write(f"FPS - {animation['fps']}\n\n")

                    for part_data in animation_parts:
                        part_index = part_data['index']
                        frame = animation['initial frame data']['data'][part_index][0]
                        print(frame)
                        print(animation_parts[part_index])
                        print()
                        output.write(str(frame) + '\n')

                with open(f"output/{unit}/frames/{animation['name']}.frame_data", 'w') as output:
                    output.write(f"Animation name - {animation['name']}\n")
                    output.write(f"Canvas size - {animation['canvas size']}\n")
                    output.write(f"Frames - {animation['frame count']}\n")
                    output.write(f"FPS - {animation['fps']}\n\n")

                    output.write('Animation parts\n')
                    for part in animation_parts:
                        output.write(str(part) + '\n')
                    output.write('\n')

                    for part_data in animation_parts:
                        part_index = part_data['index']
                        frame_data = animation['frame data']['data'][part_index]
                        for frame_index, frame in enumerate(frame_data):
                            output.write(f"Part {part_index + 1} Frame {frame_index + 1} | {frame}\n")