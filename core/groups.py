from maya import cmds
from typing import Tuple, List
from .naming import Side, Suffix, exists, replace
from . import naming, joints

def recreate(contents: List[str] = [], n:str = '') -> str:
    if not n:
        raise Exception("Missing required argument: `n`")
    if exists(n):
        cmds.delete(n)
    if contents:
        return cmds.group(contents, n=n)
    return cmds.group(n=n, em=True)

def push_front(contents:List[str] = [], n:str = '') -> str:
    """Pushes `contents` to the front of the group `n`, or creates a new one if it doesn't exist"""
    if not n:
        raise Exception("Missing required argument: `n`")
    if not exists(n):
        if contents:
            return cmds.group(contents, n=n)
        else:
            return cmds.group(n=n, em=True)
    if contents:
        # Use given order of children, moving unspecified existing children to the bottom.
        children = cmds.listRelatives(n, children=True)
        if children:
            for child in children:
                if child not in contents:
                    contents.append(child)
                cmds.parent(child, world=True)
        cmds.parent(contents, n)
    return n

def empty_at(obj: str, name: str, parent=None, * , suffix=Suffix.GROUP, offset:Tuple[float, float, float] = (0, 0, 0)) -> str:
    n = replace(obj, name=name, suffix=suffix)
    if exists(n):
        raise Exception("Object already exists: " + n)
    grp = cmds.group(n=n, em=True)
    # Match the group and obj pivots
    if parent:
        cmds.parent(grp, parent)
        cmds.makeIdentity(grp, a=False, t=True, r=True, s=True)
    match_pivots(obj, grp)
    cmds.move(offset[0], offset[1], offset[2], grp, r=True)
    cmds.makeIdentity(grp, a=True, t=True)
    return grp

def match_pivots(src: str, dest: str):
    pivot = cmds.xform(src, q=True, ws=True, piv=True)
    cmds.xform(dest, ws=True, piv=(pivot[0], pivot[1], pivot[2]))

def create_control_group(root:str, name:str) -> str:
    control_grp = empty_at(root, name, parent=naming.root_control)
    driver_parent = joints.get_parent(root)
    if driver_parent != naming.driver_grp:
        cmds.parentConstraint(driver_parent, control_grp, mo=True)
        cmds.scaleConstraint(driver_parent, control_grp)
    return control_grp

def systems_group(root_driver:str, name:str) -> str:
    fullName = replace(root_driver, name=name, suffix=Suffix.SYSTEM_GROUP)
    if exists(fullName):
        return fullName
    ret = empty_at(root_driver, name, parent=naming.systems_grp, suffix=Suffix.SYSTEM_GROUP)
    driver_parent = joints.get_parent(root_driver)
    if (driver_parent == naming.driver_grp):
        driver_parent = naming.compose(Side.CENTER, "root", "control")
    cmds.parentConstraint(driver_parent, ret)
    cmds.scaleConstraint(driver_parent, ret)
    return ret