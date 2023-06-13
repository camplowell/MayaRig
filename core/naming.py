import re
from typing import List, Tuple
from enum import Enum
from maya import cmds
"""
Naming Conventions:
General format: [initial]_([l/r]_)[bone]_[suffix]
"""

class Side(str, Enum):
    LEFT = '_l_'
    RIGHT = '_r_'
    CENTER = '_'

# Suffixes
class Suffix(str, Enum):
    marker = 'marker'
    DRIVER_JOINT = 'driver'
    IK_JOINT = 'ikJoint'
    FK_JOINT = 'fkJoint'
    BIND_JOINT = 'bindJoint'
    GROUP = 'grp'
    SYSTEM_GROUP = 'systems'
    IK_SWITCH = 'ikSwitch'
    IK_INVERT = 'ikInvert'
    CONTROL = 'control'
    IK_CONTROL = 'ikControl'
    FK_CONTROL = 'fkControl'
    IK_HANDLE = 'ikHandle'

# Attributes
SYMMETRICAL_ATTR = 'symmetrical'
ROOT_ATTR = 'limbRoot'
IK_SWITCH_ATTR = 'FK_IK'

# Active Character -------------------------------------------------------------------------------

_initials = None
_name = None

marker_grp = None
character_grp = None
bind_grp = None
geometry_grp = None
driver_grp = None
systems_grp = None
control_grp = None
no_touch_grp = None

root_control = None

def set_active_character(name: str, initials: str):
    global _initials, _name
    global marker_grp
    global character_grp
    global bind_grp
    global geometry_grp
    global driver_grp
    global systems_grp
    global control_grp
    global no_touch_grp
    global root_control

    _name = name
    _initials = initials
    
    marker_grp = _name + '_markers'
    character_grp = _name.upper()
    bind_grp = _initials + '_BIND'
    geometry_grp = _initials + '_GEO'
    driver_grp = _initials + '_DRIVER'
    control_grp = _initials + '_CONTROLS'
    systems_grp = _initials + '_SYSTEMS'
    no_touch_grp = _initials + '_DO_NOT_TOUCH'

    root_control = compose(Side.CENTER, 'root', Suffix.CONTROL)

# Query scene ------------------------------------------------------------------------------------

def exists(obj: str, attribute: str = None) -> bool:
    if attribute:
        return cmds.objExists(attr_path(obj, attribute))
    return cmds.objExists(obj)

def find(name: str, list: List[str], suffix = None, ignore_num=True):
    for n in list:
        if name == get_name(n, ignore_num=ignore_num):
            if suffix is None or suffix == get_suffix(n):
                return n
    raise Exception(name, "not found in ", list)

# New names --------------------------------------------------------------------------------------

def compose(side:Side, name:str, suffix:str) -> str:
    return _initials + side + name + '_' + suffix

def new(side:Side, name:str, suffix:str) -> str:
    return _increment_until_free(compose(side, name, suffix))

# Name variants ----------------------------------------------------------------------------------

def replace(base: str, * , side:Side=None, name:str=None, suffix:str=None):
    _side = get_side(base)
    _name, _num = get_name(base, separate_num=True)
    _suffix = get_suffix(base)

    if side is not None:
        _side = side
    if name is not None:
        _name = name
    if suffix is not None:
        _suffix = suffix
    
    return compose(_side, _name + _num, _suffix)

def flip(base: str):
    _side = get_side(base)
    if _side == Side.LEFT:
        return base.replace(Side.LEFT, Side.RIGHT)
    if _side == Side.RIGHT:
        return base.replace(Side.RIGHT, Side.LEFT)
    return base

# Decompose names --------------------------------------------------------------------------------

def get_name(obj: str, * , ignore_num = False, separate_num = False):
    name = obj[_name_start(obj):]
    if '_' in name:
        name = name[:name.find('_')]
    if not (ignore_num or separate_num):
        return name
    
    num_match = re.search(r'\d+$', name)
    num = ''
    if num_match:
        num = num_match.group()
        name = name[:-len(num)]
    if ignore_num:
        return name
    return name, num

def get_side(obj: str):
    if Side.LEFT in obj:
        return Side.LEFT
    if Side.RIGHT in obj:
        return Side.RIGHT
    return Side.CENTER

def get_suffix(obj: str):
    name_idx = _name_start(obj)
    suffix_idx = obj.find('_', name_idx)
    if suffix_idx == -1:
        return ''
    return obj[suffix_idx + 1:]

# Attribute Names --------------------------------------------------------------------------------

def attr_path(obj: str, attribute: str):
    return "{0}.{1}".format(obj, attribute)

# Helper methods ---------------------------------------------------------------------------------

def _name_start(name: str):
    if '_' not in name:
        return 0
    return max(
        name.find('_') + 1,
        name.find(Side.LEFT) + 3,
        name.find(Side.RIGHT) + 3
    )

def _increment_until_free(name: str):
    while (cmds.objExists(name)):
        name = _increment_name(name)
    return name

def _increment_name(name: str):
    suffixStart = name.find('_', _name_start(name))
    num_match = re.search(r'\d+$', name[:suffixStart])
    if (num_match):
        current_idx = num_match.group()
        return name[:suffixStart - len(current_idx)] + str(int(current_idx) + 1) + name[suffixStart:]
    else:
        return name[:suffixStart] + '1' + name[suffixStart:]