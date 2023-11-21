from maya import cmds

from .maya_object import *

def set(obj:'MayaObject|None'):
    cmds.select(cl=True)
    if obj:
        cmds.select(obj)

def get():
    ret = cmds.ls(sl=True) or []
    return [MayaObject(obj) for obj in ret]

def active():
    ret = cmds.ls(sl=True, tl=True)
    if ret:
        return MayaObject(ret[0])
    return None

def clear():
    cmds.select(cl=True)

