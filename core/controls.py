import math
from maya import cmds
import maya.api.OpenMaya as om
from typing import List

from . import naming, groups, attributes, nodes
from .naming import Side, Suffix

# Control curves

def circle(name:str, suffix:str, joint:str, parent:str, flipped=False, * , radius=4, slide=0):
    name = naming.replace(joint, name=name, suffix=suffix)
    if flipped:
        slide = -slide
    radius *= attributes.get_control_size(joint)
    ret = cmds.circle(n=name, nr = (1, 0, 0), cx = slide, r=radius)[0]

    return _match_joint(ret, joint, parent=parent)

def ellipse(name:str, suffix:str, joint:str, parent:str, * , normal=(1, 0, 0), size=(4, 4, 4)):
    name = naming.replace(joint, name=name, suffix=suffix)
    scale=attributes.get_control_size(joint)
    ret = cmds.circle(n=name, nr=normal, r=1)[0]
    cmds.scale(
        scale * size[0],
        scale * size[1],
        scale * size[2],
        ret
    )
    cmds.makeIdentity(a=True, s=True)
    return _match_joint(ret, joint, parent=parent)

def square(name: str, suffix:str, joint:str, parent:str, flipped=False, * , size=4, slide=0):
    name=naming.replace(joint, name=name, suffix=suffix)
    size *= attributes.get_control_size(joint)
    if flipped:
        slide = -slide
    ret = cmds.curve(n=name, d=1, p=[
        (slide, -size, -size),
        (slide,  size, -size),
        (slide,  size,  size),
        (slide, -size,  size),
        (slide, -size, -size)
    ])
    return _match_joint(ret, joint, parent=parent)

def ik_pole(name: str, joint: str, parent:str=None, * , size: float = 2, dist=2.0, center_on_parent=False):
    name = naming.replace(joint, name=name, suffix='pole')
    r = 0.5 * size * attributes.get_control_size(joint)

    ret = cmds.curve(n=name, d=1, p=[
        ( r, 0, 0),
        ( 0, r, 0),
        (-r, 0, 0),
        ( 0,-r, 0),
        ( r, 0, 0),
        ( 0, 0, r),
        ( 0, r, 0),
        ( 0, 0,-r),
        (-r, 0, 0),
        ( 0, 0, r),
        ( 0,-r, 0),
        ( 0, 0,-r),
        ( r, 0, 0),
    ])
    """
    circle_x = cmds.circle(nr=(1, 0, 0), r=radius)[0]
    circle_y = cmds.circle(nr=(0, 1, 0), r=radius)[0]
    circle_z = cmds.circle(nr=(0, 0, 1), r=radius)[0]
    ret = _combine([circle_x, circle_y, circle_z], name)
"""
    pos = _pole_position(joint, dist, center_on_parent=center_on_parent)
    return _to_pos(ret, pos, parent)

def ik_switch(name: str, joint:str, offset, parent:str, flipped=False, * , size=5):
    name = naming.replace(joint, name=name, suffix=Suffix.IK_SWITCH)
    size *= attributes.get_control_size(joint)
    fk = _text_curve('fk#', text='FK', scale=size)
    ik = _text_curve('ik#', 'IK', scale=size)

    fk_curves = cmds.listRelatives(fk, shapes=True)
    ik_curves = cmds.listRelatives(ik, shapes=True)

    ctrl = _combine([fk, ik], name)
    cmds.matchTransform(ctrl, joint, pos=True)
    if flipped:
        offset = (-offset[0], offset[1], offset[2])
    cmds.move(size * offset[0], size * offset[1], size * offset[2], ctrl, r=True)
    cmds.parent(ctrl, parent)
    set_rest_pose(ctrl)

    attributes.add(ctrl, naming.IK_SWITCH_ATTR, 0, type_='float', niceName='FK / IK', keyable=True)
    attributes.set_range(ctrl, naming.IK_SWITCH_ATTR, min_=0, max_=1)

    inverter = nodes.subtract(naming.replace(name, suffix=Suffix.IK_INVERT))
    attributes.set_(inverter, 'input1D[0]', 1.0)
    attributes.connect(ctrl, naming.IK_SWITCH_ATTR, inverter, 'input1D[1]')
    for curve in fk_curves:
        attributes.connect(inverter, 'output1D', curve, 'visibility')
    for curve in ik_curves:
        attributes.connect(ctrl, naming.IK_SWITCH_ATTR, curve, 'visibility')

    return ctrl, inverter

def foot(name:str, ankle:str, heel:str, toe:str, inner:str, outer:str, parent:str, flipped=False):
    heel_pos = om.MVector(cmds.joint(heel, q=True, p=True))
    toe_pos = om.MVector(cmds.joint(toe, q=True, p=True))
    inner_pos = om.MVector(cmds.joint(inner, q=True, p=True))
    outer_pos = om.MVector(cmds.joint(outer, q=True, p=True))
    ankle_pos = om.MVector(cmds.joint(ankle, q=True, p=True))

    outset=attributes.get_control_size(ankle)
    min_x = min(inner_pos.x, outer_pos.x) - outset
    max_x = max(inner_pos.x, outer_pos.x) + outset
    min_z = heel_pos.z - outset
    max_z = toe_pos.z + outset

    ankle_ctrl = cmds.curve(
        n=naming.replace(ankle, name=name, suffix=Suffix.IK_CONTROL),
        d=1,
        p=[
            om.MVector(min_x, 0, min_z) - ankle_pos,
            om.MVector(max_x, 0, min_z) - ankle_pos,
            om.MVector(max_x, 0, max_z) - ankle_pos,
            om.MVector(min_x, 0, max_z) - ankle_pos,
            om.MVector(min_x, 0, min_z) - ankle_pos
        ]
    )
    return _match_joint(ankle_ctrl, ankle, parent=parent)

def circle_with_arrows(name:str, suffix:str, joint:str = None, parent:str = None, * , offset = (0, 0, 0), radius=5, arrow_width=0.125, arrow_length=0.125):
    if joint:
        radius *= attributes.get_control_size(joint)
        name = naming.replace(joint, name=name, suffix=suffix)
    else:
        name = naming.compose(Side.CENTER, name, suffix)
    
    arrow_angle = math.asin(arrow_width)
    arrow_slide = math.cos(arrow_angle)
    arrow_angle = math.degrees(arrow_angle)
    
    arrow_width *= radius
    arrow_length *= radius
    arrow_slide *= radius
    
    arrow_head = arrow_slide + arrow_length
    arrow_tip = arrow_slide + arrow_length + 2 * arrow_width

    arc1 = cmds.circle(n='temp#', r=radius, nr=(0, 1, 0), sw=90 - 2 * arrow_angle)[0]
    cmds.rotate(0, arrow_angle, 0, arc1)
    arrow1 = cmds.curve(n='temp#', d=1, p=[
        (-arrow_width, 0, -arrow_slide),
        (-arrow_width, 0, -arrow_head),
        (-2*arrow_width, 0, -arrow_head),
        (0, 0, -arrow_tip),
        (2*arrow_width, 0, -arrow_head),
        (arrow_width, 0, -arrow_head),
        (arrow_width, 0, -arrow_slide)
    ])
    quarter1 = _combine([arc1, arrow1], name='quarter#')
    quarter2 = cmds.duplicate(quarter1, rc=True)[0]
    cmds.rotate(0, 90, 0, quarter2, r=True)
    quarter3 = cmds.duplicate(quarter2, rc=True)[0]
    cmds.rotate(0, 90, 0, quarter3, r=True)
    quarter4 = cmds.duplicate(quarter3, rc=True)[0]
    cmds.rotate(0, 90, 0, quarter4, r=True)
    ret = _combine([quarter1, quarter2, quarter3, quarter4], name=name)
    if joint:
        return _match_joint(ret, joint, parent=parent, offset=offset)
    else:
        return _to_pos(ret, offset, parent)

def finger_root(name:str, suffix:str, joint:str, parent:str, flipped=False, * , offset = 2.0, size = 1.0):
    name=naming.replace(joint, name=name, suffix=suffix)
    size *= attributes.get_control_size(joint)
    offset *= size
    if flipped:
        offset = -offset
        size = -size
    ret = cmds.curve(n=name, d=1, p=[
        (0, 0,     0),
        (0, 0,     offset),
        (0, -size, offset + size),
        (0, 0,     offset + 2 * size),
        (0, size,  offset + size),
        (0, 0,     offset)
    ])
    return _match_joint(ret, joint, parent=parent)

# Transformations --------------------------------------------------------------------------------

def reset_transforms(obj: str):
    for attribute in ["translate", "rotate", "scale", "jointOrient"]:
        value = 1 if attribute == "scale" else 0
        for axis in "XYZ":
            if cmds.attributeQuery(attribute + axis, node=obj, exists=True):
                attribute_name = "{}.{}{}".format(obj, attribute, axis)
                if not cmds.getAttr(attribute_name, lock=True):
                    cmds.setAttr(attribute_name, value)

def set_rest_pose(obj: str):
    local_matrix = om.MMatrix(cmds.xform(obj, q=True, m=True, ws=False))
    offset_parent_matrix = om.MMatrix(attributes.get(obj, 'offsetParentMatrix'))
    baked_matrix = local_matrix * offset_parent_matrix
    cmds.setAttr(attributes.attr_path(obj, 'offsetParentMatrix'), baked_matrix, type='matrix')
    reset_transforms(obj)
    return obj

# Helper methods ---------------------------------------------------------------------------------

def _match_joint(control: str, joint: str, * , offset = (0, 0, 0), parent: str):
    cmds.matchTransform(control, joint)
    if parent:
        cmds.parent(control, parent)
    cmds.move(offset[0], offset[1], offset[2], control, r=True)
    set_rest_pose(control)
    return control

def _to_pos(control: str, pos, parent: str):
    cmds.move(pos[0], pos[1], pos[2], control)
    if parent:
        cmds.parent(control, parent)
    set_rest_pose(control)
    return control

def _combine(curves:List[str], name:str, parent:str=None):
    """Combine the given curves into a single object"""
    crvGrp = groups.empty_at(curves[0], 'tmp', parent)
    cmds.parent(curves, crvGrp)
    cmds.makeIdentity(curves, a=True, t=True, r=True, s=True)
    for crv in curves:
        shape = cmds.listRelatives(crv, shapes=True)
        cmds.parent(shape, crvGrp, s=1, r=1)
        cmds.delete(crv)
    cmds.select(crvGrp)
    return cmds.rename(crvGrp, name)

def _pole_position(obj: str, distance: float, center_on_parent=False):
    """Place a pole vector"""
    parent = cmds.listRelatives(obj, parent=True)[0]
    children = cmds.listRelatives(obj, children=True)

    obj_pos = om.MVector(cmds.joint(obj, q=True, p=True, a=True))
    parent_pos = om.MVector(cmds.joint(parent, q=True, p=True, a=True))
    child_pos = om.MVector(cmds.joint(children[0], q=True, p=True, a=True))

    pole_vec = ((obj_pos - parent_pos).normalize() + (obj_pos - child_pos).normalize()).normalize()

    parent_pos = om.MVector(cmds.xform(parent, q=True, rp=True, ws=True))
    distance *= (obj_pos - parent_pos).length()
    return om.MVector((parent_pos if center_on_parent else obj_pos) + pole_vec * distance)

def _text_curve(name:str, text:str, scale:float):
    raw = cmds.textCurves(f='Lucida Grande', t=text)

    cmds.scale(scale, scale, scale, raw[0])
    curves = cmds.listRelatives(
        cmds.listRelatives(raw, ad=True, ni=True, type='nurbsCurve'),
        p=True,
        type="transform"
    )
    cmds.parent(curves, w=True)
    cmds.delete(raw[0])

    joined = _combine(curves, name)

    cmds.xform(joined, cp=True) # Center the pivot
    cmds.move(0, 0, 0, joined, rpr=True) # Move to (0, 0, 0) in world space
    cmds.makeIdentity(joined, a=True, t=True, r=True, s=True) # Ensure this is the rest position
    return joined