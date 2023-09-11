from maya import cmds
import maya.api.OpenMaya as om
from typing import List

from . import naming
from .naming import Side, Suffix, exists
from . import attributes, colors, selection

GENERATOR_ATTRIBUTE = 'autorig_limb'
SYMMETRY_ATTRIBUTE = 'symmetrical'
JOINT_TYPE_ATTR = 'MayaRigJoint'
BIND_ATTR = 'Bind'

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

def get_child(root:str):
    return cmds.listRelatives(root, type='joint')[0]

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

def marker(side:Side, name:str, pos, type_:str = None, bind=True) -> str:
    ret = cmds.joint(n=naming.new(side, name, Suffix.marker), p=pos)
    attributes.add_control_size(ret)
    if not type_:
        type_ = name
    mark_type(ret, type_)
    attributes.add(ret, BIND_ATTR, bind, type_='bool')
    return ret

def _flip_joint_orientation(joint):
    children = cmds.listRelatives(joint, c=True)
    if children:
        cmds.parent(children, w=True)
    attributes.multiply(joint, 'jointOrientX', -1)
    attributes.decrement(joint, 'jointOrientY', 180)
    cmds.parent(children, joint)

def orient(joint, flip_right = True, secondaryAxisOrient='yup', twist=0):
    if isinstance(joint, list):
        for obj in joint:
            orient(obj, flip_right)
    cmds.joint(joint, e=True, oj='xyz', secondaryAxisOrient=secondaryAxisOrient, ch=False, zso=True)
    if flip_right and naming.get_side(joint) == Side.RIGHT:
        _flip_joint_orientation(joint)

def orient_normal(obj:str, flip_right=True, normal=(0,1,0), twist=0):
    sel = selection.get()
    children = cmds.listRelatives(obj, children=True)
    if children:
        cmds.parent(children, w=True)

    temp_constraint = cmds.aimConstraint(children[0], obj, aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpVector=normal)
    cmds.delete(temp_constraint)
    cmds.makeIdentity(obj, a=True, t=False, r=True, s=True)
    cmds.joint(obj, edit=True, zeroScaleOrient=True)
    if twist:
        attributes.increment(obj, 'jointOrientX', twist)
    
    if flip_right and naming.get_side(obj) == Side.RIGHT:
        attributes.decrement(obj, 'jointOrientY', 180)
    
    if children:
        cmds.parent(children, obj)
    selection.set_(sel)

def twist_align(obj:str, normal, flip_right=True, twist=0):
    children = cmds.listRelatives(obj, children=True)
    if children:
        cmds.parent(children, w=True)
    
    target_pos = (om.MVector(cmds.joint(obj, q=True, p=True)) +
        om.MVector(cmds.xform(obj, q=True, m=True, ws=True)[0:3]))

    tgt = cmds.createNode('transform')  # looks like locator version doesn't work on maya 2012+
    cmds.xform(tgt, t=target_pos, a=True)
    const = cmds.aimConstraint(tgt, obj, aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpVector=normal)
    cmds.delete(const, tgt)
    
    cmds.makeIdentity(obj, a=True, t=False, r=True, s=True)
    cmds.joint(obj, edit=True, zeroScaleOrient=True)

    if twist:
        attributes.increment(obj, 'jointOrientX', twist)
    
    if flip_right and naming.get_side(obj) == Side.RIGHT:
        attributes.decrement(obj, 'jointOrientY', 180)
    
    if children:
        cmds.parent(children, obj)

def get_normal(objects:List[str], * , other_side = False):
    pos0 = om.MVector(cmds.joint(objects[0], q=True, p=True))
    pos1 = om.MVector(cmds.joint(objects[1], q=True, p=True))
    pos2 = om.MVector(cmds.joint(objects[2], q=True, p=True))

    to_parent = pos0 - pos1
    to_child =  pos2 - pos1

    normal = om.MVector((to_parent ^ to_child).normalize())
    return -normal if other_side else normal

def coplanar_orient(obj: str, flip_right=True, plane_child=None, other_side=False):
    parent = cmds.listRelatives(obj, parent=True)[0]
    if not plane_child:
        plane_child = cmds.listRelatives(obj, children=True)[0]
    
    normal = get_normal([parent, obj, plane_child], other_side = other_side)

    orient_normal(obj, flip_right, normal)

def orient_match(obj:str, ref:str = None, flip_right=True, twist=0):
    if not ref:
        ref = cmds.listRelatives(obj, parent=True)[0]

    normal = cmds.xform(ref, q=True, m=True, ws=True)[4:7]
    orient_normal(obj, flip_right, normal, twist)

def world_orient(obj:str, flip_right=False):
    parent = cmds.listRelatives(obj, parent=True)[0]
    cmds.parent(obj, w=True)

    cmds.joint(obj, e=True, oj="none", zso=True)

    cmds.parent(obj, parent)
    
    if flip_right and naming.get_side(obj) == Side.RIGHT:
        _flip_joint_orientation(obj)

def twist(obj:str, degrees:float):
    children = cmds.listRelatives(obj, children=True)
    if children:
        cmds.parent(children, w=True)

    attributes.increment(obj, 'jointOrientX', degrees)

    if children:
        cmds.parent(children, obj)

def mark_type(obj:str, type_:str):
    if exists(obj, JOINT_TYPE_ATTR):
        attributes.set_(obj, JOINT_TYPE_ATTR, type_)
    else:
        attributes.add(obj, JOINT_TYPE_ATTR, type_, type_="string")

def start_chain(parent:str = None):
    if parent:
        selection.set_(parent)
    else:
        selection.clear()

def to_bind(obj:str):
    return attributes.get(obj, BIND_ATTR)

def matches_type(obj: str, type_:str):
    return exists(obj, JOINT_TYPE_ATTR) and attributes.get(obj, JOINT_TYPE_ATTR) == type_

def find_child(type_:str, obj:str) -> str:
    for child in cmds.listRelatives(obj, type='joint', ad=True):
        if matches_type(child, type_):
            return child
    return None

def find_children(type_:str, obj:str, * , backwards:bool=False) -> List[str]:
    ret = [child for child in cmds.listRelatives(obj, type='joint', ad=True) if matches_type(child, type_)]

    if not backwards:
        ret.reverse()
    return ret

def find(type_:str, joints:List[str]):
    for obj in joints:
        if matches_type(obj, type_):
            return obj

def find_all(type_:str, joints:List[str]):
    return [joint for joint in joints if matches_type(joint, type_)]

def find_equiv(joint:str, collection:List[str]):
    obj_name = naming.get_name(joint)
    for obj in collection:
        if naming.get_name(obj) == obj_name:
            return obj
    return None