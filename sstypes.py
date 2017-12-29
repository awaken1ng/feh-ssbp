from enum import Enum


class Enum(Enum):
    @classmethod
    def get(cls, _type):
        return cls._value2member_map_.get(_type)


class SSWrapMode(Enum):
    clamp = 0
    repeat = 1
    mirror = 2
    num = 3


class SSFilterMode(Enum):
    nearest = 0
    linear = 1
    num = 2


class SSPartType(Enum):
    null = 0
    normal = 1
    text = 2
    instance = 3
    effect = 4
    num = 5


class SSBoundsType(Enum):
    none = 0
    quad = 1
    aabb = 2
    circle = 3
    circle_smin = 4
    circle_smax = 5
    num = 6


class SSBlendType(Enum):
    mix = 0
    mul = 1
    add = 2
    sub = 3
    num = 4


class AnimationInstance:
    def __init__(self, keyframe, start, end, speed, loop, infinity, reverse, pingpong, independent):
        self.keyframe = keyframe
        self.start = start
        self.end = end
        self.speed = speed
        self.loop = bool(loop)
        self.infinity = infinity
        self.reverse = reverse
        self.pingpong = pingpong
        self.independent = independent


class SSPartState:
    def __init__(self,
                 part_index,
                 hide=False,
                 flip_h=False,
                 flip_v=False,
                 cell_index=-1,
                 position_x=0,
                 position_y=0,
                 position_z=0,
                 alpha=255,
                 pivot_x=0.0,
                 pivot_y=0.0,
                 rotation_x=0.0,
                 rotation_y=0.0,
                 rotation_z=0.0,
                 scale_x=1.0,
                 scale_y=1.0,
                 size_x=1.0,
                 size_y=1.0,
                 uv_translation_x=0.0,
                 uv_translation_y=0.0,
                 uv_rotation=0.0,
                 uv_scale_x=1.0,
                 uv_scale_y=1.0,
                 bounding_radius=0.0):
        self.part = part_index
        self.hide = hide
        self.flph = flip_h
        self.flpv = flip_v
        self.cell = cell_index
        self.posx = position_x
        self.posy = position_y
        self.posz = position_z
        self.alph = alpha
        self.pvtx = pivot_x
        self.pvty = pivot_y
        self.rotx = rotation_x
        self.roty = rotation_y
        self.rotz = rotation_z
        self.sclx = scale_x
        self.scly = scale_y
        self.sizx = size_x
        self.sizy = size_y
        self.uvtx = uv_translation_x
        self.uvty = uv_translation_y
        self.uvrz = uv_rotation
        self.uvsx = uv_scale_x
        self.uvsy = uv_scale_y
        self.bndr = bounding_radius
        self.parent = None
        self.vertex = None
        self.instance = None
        self.vertices = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def __iter__(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def from_dict(self, frame):
        self.part = frame['part index']
        self.hide = frame['invisible']
        self.flph = frame['flip h']
        self.flpv = frame['flip v']
        self.cell = frame['cell index']
        self.posx = frame['position x']
        self.posy = frame['position y']
        self.posz = frame['position z']
        self.alph = frame['opacity']
        self.pvtx = frame['pivot x']
        self.pvty = frame['pivot y']
        self.rotx = frame['rotation x']
        self.roty = frame['rotation y']
        self.rotz = frame['rotation z']
        self.sclx = frame['scale x']
        self.scly = frame['scale y']
        self.sizx = frame['size x']
        self.sizy = frame['size y']
        self.uvtx = frame['u move']
        self.uvty = frame['v move']
        self.uvrz = frame['uv rotation']
        self.uvsx = frame['u scale']
        self.uvsy = frame['v scale']
        self.bndr = frame['bounding radius']
        self.vertex = None
        self.instance = None
        if 'vertex transform' in frame.keys():
            self.vertex = frame['vertex transform']
        if 'instance keyframe' in frame.keys():
            self.instance = AnimationInstance(
                frame['instance keyframe'],
                frame['instance start'],
                frame['instance end'],
                frame['instance speed'],
                frame['instance loop'],
                frame['instance loop flags']['infinity'],
                frame['instance loop flags']['reverse'],
                frame['instance loop flags']['pingpong'],
                frame['instance loop flags']['independent']
            )
        return self

    def to_dict(self):
        return {
            'part index':      self.part,
            'invisible':       self.hide,
            'flip h':          self.flph,
            'flip v':          self.flpv,
            'cell index':      self.cell,
            'position x':      self.posx,
            'position y':      self.posy,
            'position z':      self.posz,
            'opacity':         self.alph,
            'pivot x':         self.pvtx,
            'pivot y':         self.pvty,
            'rotation x':      self.rotx,
            'rotation y':      self.roty,
            'rotation z':      self.rotz,
            'scale x':         self.sclx,
            'scale y':         self.scly,
            'size x':          self.sizx,
            'size y':          self.sizy,
            'u move':          self.uvtx,
            'v move':          self.uvty,
            'uv rotation':     self.uvrz,
            'u scale':         self.uvsx,
            'v scale':         self.uvsy,
            'bounding radius': self.bndr,
            'vertex transform': self.vertex
        }

    def __repr__(self):
        output = f"<SSPartState "
        if self.part:
            output += f"PART={     self.part.index :2} "
        else:
            output += f"PART=-1 "
        output += f"HIDE={repr(self.hide):5} " \
               f"FLPH={repr(self.flph):5} " \
               f"FLPV={repr(self.flpv):5} "

        if self.cell:
            output += f"CELL={     self.cell.index :2} "
        else:
            output += f"CELL=-1 "
        return output + \
               f"POSX={     self.posx:4} " \
               f"POSY={     self.posy:4} " \
               f"ALPH={     self.alph:3} " \
               f"PVTX={     self.pvtx:7.2} " \
               f"PVTY={     self.pvty:7.2} " \
               f"ROTZ={     self.rotz:7.2f} " \
               f"SCLX={     self.sclx} " \
               f"SCLY={     self.scly} " \
               f"SIZX={     self.sizx:6.2f} " \
               f"SIZY={     self.sizy:6.2f}>"
               #f"UVTX={     self.uvtx} " \
               #f"UVTY={     self.uvty} " \
               #f"UVRZ={     self.uvrz} " \
               #f"UVSX={     self.uvsx} " \
               #f"UVSY={     self.uvsy} " \
               #f"BNDR={     self.bndr}>"


class SSAnimationPart:
    def __init__(self,
                 name=None,
                 index=None,
                 parent_index=None,
                 bounds_type=None,
                 alpha_blend_type=None,
                 animation_instance_name=None,
                 effect_name=None, color=None):
        self.name = name
        self.index = index
        self.parent_index = parent_index
        self.parent = None
        self.bounds_type = bounds_type
        self.alpha_blend_type = alpha_blend_type
        self.animation_instance_name = animation_instance_name if animation_instance_name else None
        self.effect_name = effect_name if effect_name else None
        self.color = color if color else None

    def __iter__(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    def from_dict(self, part):
        self.name = part['name']
        self.index = part['index']
        self.parent_index = part['parent index']
        self.type = part['type']
        self.bounds_type = part['bounds type']
        self.alpha_blend_type = part['alpha blend type']
        self.animation_instance_name = part['animation instance name']
        self.effect_name = part['effect name']
        self.color = part['color']
        return self

    def __repr__(self):
        return f"<SSAnimationPart name='{self.name}', index={self.index}, parent index={self.parent_index}, " \
               f"bounds type='{self.bounds_type.name}', alpha blend type='{self.alpha_blend_type.name}', " \
               f"animation instance name='{self.animation_instance_name}', effect name='{self.effect_name}', " \
               f"color='{self.color}'>"


class SSVector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        self.x = other + self.x
        self.y = other + self.y
        return self

    def __sub__(self, other):
        self.x = other - self.x
        self.y = other - self.y
        return self

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        else:
            raise IndexError

    def __setitem__(self, key, value):
        if isinstance(value, int) or isinstance(value, float):
            if key == 0:
                self.x = value
            elif key == 1:
                self.y = value
            else:
                raise IndexError
        else:
            raise TypeError('Value has to be integer or float')

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __repr__(self):
        return f"<SSVector2 ({self.x}, {self.y})>"


class SSCell:
    def __init__(self, name=None, index=None, position=None, size=None, pivot=None):
        self.name = name
        self.index = index
        self.position = position
        self.size = size
        self.pivot = pivot

    def from_dict(self, cell):
        self.name = cell['name']
        self.index = cell['index']
        self.position = SSVector2(cell['pos'][0], cell['pos'][1])
        self.size = SSVector2(cell['size'][0], cell['size'][1])
        self.pivot = SSVector2(cell['pivot'][0], cell['pivot'][1])
        return self

    def __repr__(self):
        return f"<SSCell name='{self.name}' " \
                       f"index={self.index}, " \
                       f"position=({self.position.x}, {self.position.y}), " \
                       f"size=({self.size.x}, {self.size.y}), " \
                       f"pivot=({self.pivot.x}, {self.pivot.y})>"