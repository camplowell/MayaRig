from typing import List, Tuple

import maya.api.OpenMaya as om
from maya import cmds

from .context import Character
from .maya_object import MayaObject, Suffix, Side, CollisionBehavior
from .nodes import Nodes

def create(obj:MayaObject, contents:List[MayaObject]=[], * , parent:MayaObject=None, position:'om.MVector|Tuple[float, float, float]|None'=None, onCollision=CollisionBehavior.IGNORE):
    if onCollision == CollisionBehavior.IGNORE and obj.exists():
        children = obj.children()
        if children:
            for child in obj.children():
                if child not in contents:
                    contents.append(child)
                cmds.parent(child, world=True)
        if contents:
            cmds.parent(contents, obj)
        return obj
    
    obj = obj.resolve_collisions(onCollision=onCollision)
    return _new(obj, contents, parent, position)

def new(side:Side, name:str, contents:List[MayaObject]=[], * , parent:MayaObject=None, position:'om.MVector|Tuple[float, float, float]|None' = None, suffix=Suffix.GROUP, onCollision:CollisionBehavior = CollisionBehavior.INCREMENT):
    """Create a new group"""
    group = MayaObject.compose(side, name, suffix, initials=Character.initials).resolve_collisions(onCollision)
    return _new(group, contents, parent, position)

def _new(group:MayaObject, contents:List[MayaObject]=[], parent:MayaObject=None, position:'om.MVector|Tuple[float, float, float]|None'=None):
    cmds.group(n=group, em=True)
    if parent:
        cmds.parent(group, parent)
    if position:
        cmds.move(*position, group, r=False, ws=True)
    if contents:
        cmds.parent(*contents, group)
    group.set_rest()
    return MayaObject(group)

def new_at(ref:MayaObject, name:str=None, contents:List[MayaObject]=[], * , suffix:str=Suffix.GROUP, parent:MayaObject=None, offset:'om.MVector|Tuple[float, float, float]' = (0, 0, 0), onCollision:CollisionBehavior = CollisionBehavior.INCREMENT):
    """Create a group at a specific object"""
    position = ref.position() + om.MVector(offset)
    
    group = create(MayaObject(ref.but_with(name=name, suffix=suffix)), contents=contents, parent=parent, position=position, onCollision=onCollision)
    
    return group

def control_group(root:MayaObject, name:str):
    control_group = MayaObject(root.but_with(name=name, suffix=Suffix.GROUP))
    if control_group.exists():
        return control_group
    _new(control_group, parent=Character.controls_grp, position=root.position())
    pose_parent = root.parent()
    if pose_parent != Character.pose_grp:
        Nodes.Structures.parentConstraint(pose_parent, control_group)
    return control_group

def systems_group(root:MayaObject, name:str) -> MayaObject:
    system_group = MayaObject(root.but_with(name=name, suffix=Suffix.SYSTEM_GROUP))
    if system_group.exists():
        return system_group
    _new(system_group, parent=Character.systems_grp, position=root.position())
    pose_parent = root.parent()
    if pose_parent != Character.pose_grp:
        Nodes.Structures.parentConstraint(pose_parent, system_group)
    return system_group

def create_output():
    create(Character.output_grp, onCollision=CollisionBehavior.IGNORE, contents=[
        create(Character.controls_grp, onCollision=CollisionBehavior.REPLACE),
        create(Character.internals_grp, onCollision=CollisionBehavior.IGNORE, contents=[
            create(Character.geometry_grp, onCollision=CollisionBehavior.IGNORE),
            create(Character.pose_grp, onCollision=CollisionBehavior.REPLACE),
            create(Character.systems_grp, onCollision=CollisionBehavior.REPLACE),
            create(Character.bind_grp, onCollision=CollisionBehavior.REPLACE)
        ])
    ])
    Character.systems_grp.visibility.set(0)