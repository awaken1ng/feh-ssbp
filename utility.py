import struct
import math


# Utility functions for file reading
def read_u8le(input_buffer):
    return struct.unpack('<B', input_buffer.read(1))[0]


def read_i16le(input_buffer):
    return struct.unpack('<h', input_buffer.read(2))[0]


def read_i32le(input_buffer):
    return struct.unpack('<i', input_buffer.read(4))[0]


def read_f32le(input_buffer):
    return struct.unpack('<f', input_buffer.read(4))[0]


def read_str(input_stream):
    # Reads string from buffer, stops on 0x00 and returns the read string
    character = read_u8le(input_stream)
    string = ''
    while character != 0:
        string += chr(character)
        character = read_u8le(input_stream)
    return string


def read_str_from_pointer(input_stream, pointer):
    # Read the string from pointer, seeks back to previous position
    current_position = input_stream.tell()
    input_stream.seek(pointer)
    string = read_str(input_stream)
    input_stream.seek(current_position)
    return string


class peek:
    # Context manager, goes to position in the buffer and goes back
    # Usage example:
    # with peek(input_buffer, pointer) as pointer_buffer:
    #     pointer_buffer.read(4)
    def __init__(self, input_buffer, position):
        self.input_buffer = input_buffer
        self.position = position

    def __enter__(self):
        self.initial_position = self.input_buffer.tell()
        self.input_buffer.seek(self.position)
        return self.input_buffer

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.input_buffer.seek(self.initial_position)


def create_matrix():
    # Return empty 4x4 matrix
    return [
    # 0    1    2    3
    0.0, 0.0, 0.0, 0.0,
    # 4    5    6    7
    0.0, 0.0, 0.0, 0.0,
    # 8    9   10   11
    0.0, 0.0, 0.0, 0.0,
    #12   13   14   15
    0.0, 0.0, 0.0, 0.0
]


def create_identity_matrix():
    return create_scale_matrix(1, 1, 1)


def create_scale_matrix(x, y, z):
    matrix = create_matrix()
    matrix[4 * 0 + 0] = x    # 0
    matrix[4 * 1 + 1] = y    # 5
    matrix[4 * 2 + 2] = z    # 10
    matrix[4 * 3 + 3] = 1.0  # 15
    return matrix


def create_translation_matrix(x, y, z):
    matrix = create_identity_matrix()
    matrix[4 * 3 + 0] = x    # 12
    matrix[4 * 3 + 1] = y    # 13
    matrix[4 * 3 + 2] = z    # 14
    return matrix


def multiply_matrix(m0, m1):
    matrix = create_matrix()
    for i in range(16):
        j = i & ~3
        k = i & 3
        matrix[i] = m0[j + 0] * m1[0 + k] \
                  + m0[j + 1] * m1[4 + k] \
                  + m0[j + 2] * m1[8 + k] \
                  + m0[j + 3] * m1[12 + k]
    return matrix


def matrix4rotationX(matrix, rad):
    matrix[4 * 0 + 0] = 1.0

    matrix[4 * 1 + 1] = math.cos(rad)
    matrix[4 * 1 + 2] = math.sin(rad)

    matrix[4 * 2 + 1] = -math.cos(rad)
    matrix[4 * 2 + 2] = -math.sin(rad)

    matrix[4 * 3 + 3] = 1.0

    return matrix


def matrix4rotationY(matrix, rad):
    matrix[4 * 0 + 0] = math.cos(rad)
    matrix[4 * 0 + 2] = -math.sin(rad)

    matrix[4 * 1 + 1] = 1.0

    matrix[4 * 2 + 0] = math.sin(rad)
    matrix[4 * 2 + 2] = math.cos(rad)

    matrix[4 * 3 + 3] = 1.0
    return matrix


def matrix4rotationZ(matrix, rad):
    matrix[4 * 0 + 0] = math.cos(rad)
    matrix[4 * 0 + 1] = -math.sin(rad)
    matrix[4 * 0 + 2] = 0.0
    matrix[4 * 0 + 3] = 0.0

    matrix[4 * 1 + 0] = math.sin(rad)
    matrix[4 * 1 + 1] = math.cos(rad)
    matrix[4 * 1 + 2] = 0.0
    matrix[4 * 1 + 3] = 0.0

    matrix[4 * 2 + 0] = 0.0
    matrix[4 * 2 + 1] = 0.0
    matrix[4 * 2 + 2] = 1.0
    matrix[4 * 2 + 3] = 0.0

    matrix[4 * 3 + 0] = 0.0
    matrix[4 * 3 + 1] = 0.0
    matrix[4 * 3 + 2] = 0.0
    matrix[4 * 3 + 3] = 1.0
    return matrix


def rotation_matrix_m(matrix, rad_x, rad_y, rad_z):
    if rad_x:
        _m = create_identity_matrix()
        _m = matrix4rotationX(_m, rad_x)
        matrix = multiply_matrix(matrix, _m)
    if rad_y:
        _m = create_identity_matrix()
        _m = matrix4rotationY(_m, rad_y)
        matrix = multiply_matrix(matrix, _m)
    if rad_z:
        _m = create_identity_matrix()
        _m = matrix4rotationZ(_m, rad_z)
        matrix = multiply_matrix(matrix, _m)
    return matrix


def translation_matrix_m(matrix, x, y, z):
    m2 = create_translation_matrix(x, y, z)
    return multiply_matrix(matrix, m2)


def scale_matrix_m(matrix, x, y, z):
    m2 = create_scale_matrix(x, y, z)
    return multiply_matrix(matrix, m2)


def rotate_around(point, center, angle):
    # Rotate a point around the center by angle
    angle = math.radians(-angle)
    return (
        center[0] + (point[0] - center[0]) * math.cos(angle) - (
                point[1] - center[1]) * math.sin(angle),
        center[1] + (point[0] - center[0]) * math.sin(angle) + (
                point[1] - center[1]) * math.cos(angle)
    )