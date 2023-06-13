from maya import cmds
import maya.api.OpenMaya as om
from typing import List, Tuple

from . import naming
from .naming import Side, Suffix, exists
from . import attributes, colors

GENERATOR_ATTRIBUTE = 'autorig_limb'
SYMMETRY_ATTRIBUTE = 'symmetrical'

def get_chain(root: str):
    """Returns a list of the root's child joints in the same generator."""
    if not is_root(root):
        raise Exception("Invalid chain root: ", root)
    chain: List[str] = []
    frontier = [root]
    while frontier:
        parent = str(frontier.pop())
        chain.append(parent)
        relatives = cmds.listRelatives(parent, type='joint')
        if (relatives):
            children = [obj for obj in relatives if not is_root(obj)]
            frontier.extend(children)
    return chain

def variants(joints: List[str], suffix:str, * , parent_if_exists=False, clear_attributes=False, keep_root=False, root_parent = None):
    """Creates a duplicate of the given joints, keeping internal parent/child relationships
    Does not recreate bones if they exist already.
    """
    dups = cmds.duplicate(joints, po=True, n='temp')
    ret = []
    for i in range(len(dups)):
        new_joint = naming.replace(joints[i], suffix=suffix)
        cmds.rename(dups[i], new_joint)
        ret.append(new_joint)
        if not keep_root:
            clear_root(new_joint)
        if clear_attributes:
            attributes.delete_all(new_joint)
        
        current_parent = get_parent(new_joint)
        if i == 0 and root_parent and current_parent != root_parent:
            cmds.parent(new_joint, root_parent)
        elif parent_if_exists:
            desired_parent = naming.replace(get_parent(joints[i]), suffix=suffix)
            if current_parent != desired_parent and exists(desired_parent):
                cmds.parent(new_joint, desired_parent)
    return ret

def get_parent(obj: str):
    parent_list = cmds.listRelatives(obj, p=True)
    if parent_list:
        return parent_list[0]
    return None    

def is_root(obj: str):
    """Returns if the given joint is the root of a limb"""
    return exists(obj, GENERATOR_ATTRIBUTE) and exists(obj, SYMMETRY_ATTRIBUTE)

def get_generator(obj: str) -> str:
    if not is_root(obj):
        raise Exception("Tried to get generator of non-root joint:", obj)
    return attributes.get(obj, GENERATOR_ATTRIBUTE)

def is_symmetrical(obj: str) -> bool:
    if not is_root(obj):
        raise Exception("Tried to get symmetry of non-root joint:", obj)
    return attributes.get(obj, SYMMETRY_ATTRIBUTE)

def mark_root(joint: str, limb_type: str, symmetrical:bool=False):
    attributes.add(joint, GENERATOR_ATTRIBUTE, limb_type, type_='string')
    attributes.add(joint, SYMMETRY_ATTRIBUTE, symmetrical, type_='bool')
    if is_symmetrical:
        colors.set_(joint, 'midtone blue')
def clear_root(joint:str):
    if exists(joint, GENERATOR_ATTRIBUTE):
        attributes.delete(joint, GENERATOR_ATTRIBUTE)
    if exists(joint, SYMMETRY_ATTRIBUTE):
        attributes.delete(joint, SYMMETRY_ATTRIBUTE)

def mirror(joint: str, mirrorBehavior = True, parent_if_exists = True):
    """Mirror a joint and its children"""
    if exists(naming.flip(joint)):
        return
    children = cmds.listRelatives(joint, ad=True)
    side = naming.get_side(joint)
    if children:
        for child in children:
            cside = naming.get_side(child)
            if side == Side.CENTER:
                side = cside
                continue
            if side != cside and cside != Side.CENTER:
                raise Exception("Both left and right sides under the mirrored joint: ", joint)
    ret = None
    if side == side.CENTER:
        ret = cmds.mirrorJoint(joint, mirrorYZ = True, mirrorBehavior = mirrorBehavior)
    else:
        fside = Side.RIGHT
        if side == Side.RIGHT:
            fside = Side.LEFT
        ret = cmds.mirrorJoint(joint, mirrorYZ = True, mirrorBehavior = mirrorBehavior, sr=[side, fside])
    if parent_if_exists:
        desired_parent = naming.flip(get_parent(joint))
        if exists(desired_parent) and get_parent(ret[0]) != desired_parent:
            cmds.parent(ret[0], desired_parent, r=True)
            cmds.move(
                attributes.get(ret[0], 'tx'),
                -attributes.get(ret[0], 'ty'),
                -attributes.get(ret[0], 'tz'),
                ret[0],
                ls=True
            )
    return ret

def marker(side:Side, name:str, pos) -> str:
    ret = cmds.joint(n=naming.new(side, name, Suffix.marker), p=pos)
    attributes.add_control_size(ret)
    return ret

def orient(joint, flip_right = True, secondaryAxisOrient='yup'):
    if isinstance(joint, list):
        for obj in joint:
            orient(obj, flip_right)
    cmds.joint(joint, e=True, oj='xyz', secondaryAxisOrient=secondaryAxisOrient, ch=False, zso=True)
    if flip_right and naming.get_side(joint) == Side.RIGHT:
        children = cmds.listRelatives(joint, c=True)
        cmds.parent(children, w=True)
        attributes.decrement(joint, 'jointOrientX', 180)
        attributes.decrement(joint, 'jointOrientY', 180)
        cmds.parent(children, joint)

def coplanar_orient(obj: str, flip_right=True):
    parent = cmds.listRelatives(obj, parent=True)[0]
    children = cmds.listRelatives(obj, children=True)

    obj_pos = om.MVector(cmds.joint(obj, q=True, p=True))
    parent_pos = om.MVector(cmds.joint(parent, q=True, p=True))
    child_pos = om.MVector(cmds.joint(children[0], q=True, p=True))

    to_parent = parent_pos - obj_pos
    to_child = child_pos - parent_pos
    cmds.parent(children, w=True)
    normal = om.MVector((to_parent ^ to_child).normalize())
    
    temp_constraint = cmds.aimConstraint(children[0], obj, aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpVector=normal)
    cmds.delete(temp_constraint)
    cmds.makeIdentity(obj, a=True, t=False, r=True, s=True)
    cmds.joint(obj, edit=True, zeroScaleOrient=True)
    
    if flip_right and naming.get_side(obj) == Side.RIGHT:
        #attributes.decrement(obj, 'jointOrientX', 180)
        attributes.decrement(obj, 'jointOrientY', 180)
    cmds.parent(children, obj)

def world_orient(obj:str, flip_right=False):
    parent = cmds.listRelatives(obj, parent=True)[0]
    cmds.parent(obj, w=True)

    cmds.joint(obj, e=True, oj="none", zso=True)

    cmds.parent(obj, parent)
    
    if flip_right and naming.get_side(obj) == Side.RIGHT:
        children = cmds.listRelatives(obj, children=True)
        if children:
            cmds.parent(children, w=True)
        attributes.decrement(obj, 'jointOrientX', 180)
        attributes.decrement(obj, 'jointOrientY', 180)
        if children:
            cmds.parent(children, obj)
