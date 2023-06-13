from typing import Any, List
from maya import cmds
from .naming import attr_path, exists

DATA_TYPES = ['string', 'stringArray', 'matrix', 'reflectanceRGB', 'spectrumRGB', 'doubleArray', 'floatArray', 'Int32Array', 'vectorArray', 'nurbsCurve', 'nurbsSurface', 'mesh', 'lattice', 'pointArray']
CONTROL_SCALE = 'controlScale'

def get(obj: str, attr: str) -> Any:
    ret = cmds.getAttr(attr_path(obj, attr))
    if isinstance(ret, list) and len(ret) == 1:
        return ret[0]
    return ret

def set_(obj: str, attr: str, value, type_: str=None, lock:bool=False, keyable:bool=False):
    if isinstance(value, str):
        type_='string'
    if type_ in ['bool', 'short', 'long', 'float', 'double', 'int', 'float']:
        type_=None
    if isinstance(value, tuple):
        if type_:
            return cmds.setAttr(attr_path(obj, attr), *value, type=type_, l=lock, k=keyable)
        else:
            return cmds.setAttr(attr_path(obj, attr), *value, l=lock, k=keyable)
    else:
        if type_:
            return cmds.setAttr(attr_path(obj, attr), value, type=type_, l=lock, k=keyable)
        else:
            return cmds.setAttr(attr_path(obj, attr), value, l=lock, k=keyable)
    
def add(obj: str, attr: str, value, type_:str, lock:bool=False, hidden:bool=False, keyable:bool=False, * , niceName:str=None):
    selection = cmds.ls(selection=True)
    cmds.select(obj, r=True)
    if type_ in DATA_TYPES:
        cmds.addAttr(ln=attr, dt=type_, h=hidden)
    else:
        cmds.addAttr(ln=attr, at=type_, h=hidden)
    if niceName:
        cmds.addAttr(attr_path(obj, attr), e=True, nn=niceName)
    cmds.select(selection, r=True)
    set_(obj, attr, value, type_, lock, keyable)

def add_enum(obj:str, attr:str, values, active:int, hidden:bool=False, keyable=False, niceName:str=None):
    cmds.addAttr(obj, ln=attr, at='enum', en=values, h=hidden)
    if niceName:
        cmds.addAttr(attr_path(obj, attr), e=True, nn=niceName)
    set_(obj, attr, active, keyable=keyable)

def set_range(obj: str, attr: str, min_ = None, max_ = None):
    if min_ is not None:
        cmds.addAttr(attr_path(obj, attr), e=True, min=min_)
    if max_ is not None:
        cmds.addAttr(attr_path(obj, attr), e=True, max=max_)

def lock(obj: str, attributes):
    if (isinstance(attributes, str)):
        attributes = [attributes]
    for attribute in attributes:
        cmds.setAttr(attr_path(obj, attribute), lock=True)

def unlock(obj: str, attributes):
    if isinstance(attributes, str):
        attributes = [attributes]
    for attribute in attributes:
        cmds.setAttr(attr_path(obj, attribute), lock=False)

def connect(from_obj: str, from_attr: str, to_obj: str, to_attr: str = None, force=True):
    if not to_attr:
        to_attr = from_attr
    cmds.connectAttr(attr_path(from_obj, from_attr), attr_path(to_obj, to_attr), f=force)

def delete(obj:str, attribute: str):
    if isinstance(obj, list):
        for i in obj:
            delete(i, attribute)
        return
    if isinstance(attribute, list):
        for attr in attribute:
            delete(obj, attr)
        return
    if not exists(obj, attribute):
        raise Exception("Attribute doesn't exist:", attr_path(obj, attribute))
    unlock(obj, attribute)
    cmds.deleteAttr(attr_path(obj, attribute))

def delete_except(obj, keep:List[str]):
    if isinstance(obj, list):
        for item in obj:
            delete_all(item)
        return
    attrs = cmds.listAttr(obj, ud=True)
    if attrs:
        unlock(obj, attrs)
        for attr in attrs:
            if attr in keep:
                continue
            cmds.setAttr(attr_path(obj, attr), lock=False)
            cmds.deleteAttr(attr_path(obj, attr))

def delete_all(obj):
    if isinstance(obj, list):
        for item in obj:
            delete_all(item)
        return
    attrs = cmds.listAttr(obj, ud=True)
    if attrs:
        unlock(obj, attrs)
        for attr in attrs:
            cmds.setAttr(attr_path(obj, attr), lock=False)
            cmds.deleteAttr(attr_path(obj, attr))

def increment(obj:str, attr:str, val):
    set_(obj, attr, get(obj, attr) + val)

def decrement(obj: str, attr: str, val):
    set_(obj, attr, get(obj, attr) - val)

def multiply(obj: str, attr: str, val):
    set_(obj, attr, get(obj, attr) * val)

def divide(obj: str, attr: str, val):
    set_(obj, attr, get(obj, attr) / val)

def add_control_size(obj:str, default:float = 1):
    add(obj, CONTROL_SCALE, default, type_='float', keyable=True)
    set_range(obj, CONTROL_SCALE, min_=0.0)

def get_control_size(obj:str):
    if exists(obj, CONTROL_SCALE):
        return get(obj, CONTROL_SCALE)
    print("Missing control scale: ", attr_path(obj, CONTROL_SCALE))
    return 1

def set_control_size(obj: str, val:float):
    set_(obj, CONTROL_SCALE, val)