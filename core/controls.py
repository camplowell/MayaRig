from enum import Enum
from math import asin, cos, degrees, sqrt
from typing import List, Tuple

from maya import cmds
import maya.api.OpenMaya as om

from .joint import Joint
from .nodes import Nodes
from .maya_object import CollisionBehavior, MayaObject, Side, Suffix
from . import groups, selection

class Axis(Enum):
    X = 0
    Y = 1
    Z = 2

_VECTORS = {Axis.X:om.MVector(1, 0, 0), Axis.Y:om.MVector(0, 1, 0), Axis.Z:om.MVector(0, 0, 1)}
_ROTATIONS = {Axis.X:(0, 0, -90), Axis.Y:(0, 0, 0), Axis.Z:(90, 0, 0)}
_UP = (0, 1, 0)

def circle(ref:Joint, name:str, parent:MayaObject, * , axis=Axis.X, position:Tuple[float, float, float]=(0, 0, 0), suffix:str=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT, stretch:Tuple[float, float, float]=(1, 1, 1), relative=True, **kwargs) -> MayaObject:
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    radius = ref.control_size()
    cmds.circle(n=ctrl, nr=_UP, r=radius)[0]
    cmds.scale(*stretch, ctrl)
    cmds.makeIdentity(a=True, s=True)
    cmds.rotate(*_ROTATIONS[axis], ctrl)
    cmds.makeIdentity(a=True, r=True)

    return place_ctrl(ctrl, ref, parent=parent, position=position, relative=relative)

def square(ref:Joint, name:str, parent:MayaObject, * , axis=Axis.X, position:Tuple[float, float, float]=(0, 0, 0), suffix:str=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT, stretch:Tuple[float, float, float]=(1,1,1), relative=True, **kwargs) -> MayaObject:
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    radius = ref.control_size() * sqrt(2)
    cmds.circle(n=ctrl, nr=_UP, r=radius, d=1, s=4)[0]
    cmds.rotate(0, 45, 0, ctrl)
    cmds.makeIdentity(a=True, r=True)
    cmds.scale(*stretch, ctrl)
    cmds.makeIdentity(a=True, s=True)
    cmds.rotate(*_ROTATIONS[axis], ctrl)
    cmds.makeIdentity(a=True, r=True)

    return place_ctrl(ctrl, ref, parent=parent, position=position, relative=relative)

def octahedron(ref:Joint, name:str, parent:MayaObject, * , position:Tuple[float, float, float]=(0, 0, 0), suffix:str=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT, relative=True, inherit_transforms=False, **kwargs) -> MayaObject:
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    if 'radius' in kwargs:
        r = kwargs['radius']
    else:
        r = ref.control_size()
    
    cmds.curve(n=ctrl, d=1, p=[
        (r, 0, 0), (0, r, 0), (-r, 0, 0), (0, -r, 0), (r, 0, 0), (0, 0, r), (0, r, 0), (0, 0, -r), (-r, 0, 0), (0, 0, r), (0, -r, 0), (0, 0, -r), (r, 0, 0)
    ])
    return place_ctrl(ctrl, ref, parent=parent, position=position, relative=relative, inherit_transforms=inherit_transforms)

def circle_with_arows(ref:Joint, name:str, parent:MayaObject, * , axis=Axis.X, position:Tuple[float, float, float]=(0, 0, 0), suffix:str=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT, relative=True, arrow_width=0.125, arrow_length=0.125, **kwargs) -> MayaObject:
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    if 'radius' in kwargs:
        radius = kwargs['radius']
    else:
        radius = ref.control_size()
    
    arrow_angle = asin(arrow_width)
    arrow_slide = cos(arrow_angle)
    arrow_angle = degrees(arrow_angle)

    arrow_width *= radius
    arrow_length *= radius
    arrow_slide *= radius

    arrow_head = arrow_slide + arrow_length
    arrow_tip = arrow_slide + arrow_length + 2 * arrow_width
    arc1 = cmds.circle(n='temp#', r=radius, nr= (0, 1, 0), sw=90 - 2 * arrow_angle)[0]
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
    quarter1 = combine_curves([arc1, arrow1])
    quarter2 = cmds.duplicate(quarter1, rc=True)[0]
    cmds.rotate(0, 90, 0, quarter2, r=True)
    quarter3 = cmds.duplicate(quarter2, rc=True)[0]
    cmds.rotate(0, 90, 0, quarter3, r=True)
    quarter4 = cmds.duplicate(quarter3, rc=True)[0]
    cmds.rotate(0, 90, 0, quarter4, r=True)
    combine_curves([quarter1, quarter2, quarter3, quarter4], name=ctrl)

    cmds.rotate(*_ROTATIONS[axis], ctrl)
    ctrl.set_rest()
    return place_ctrl(ctrl, ref, parent=parent, position=position, relative=relative)

def saddle(ref:Joint, name:str, parent:MayaObject, * , axis=Axis.X, position:Tuple[float, float, float]=(0, 0, 0), suffix:str=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT, stretch:Tuple[float, float, float]=(1, 1, 1), relative=True, **kwargs) -> MayaObject:
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    radius = ref.control_size()
    cmds.circle(n=ctrl, nr=_UP, r=radius)[0]
    pts = ctrl.attr('cv')
    cmds.move(0,-0.5 * radius, 0, pts[1], pts[5], r=True) # Front/back
    cmds.move(0, 0.5 * radius, 0, pts[3], pts[7], r=True) # Left/right
    cmds.scale(*stretch, ctrl)
    cmds.makeIdentity(a=True, s=True)
    cmds.rotate(*_ROTATIONS[axis], ctrl)
    ctrl.set_rest()

    return place_ctrl(ctrl, ref, parent=parent, position=position, relative=relative)

def pointer(ref:Joint, name:str, parent:MayaObject, * , axis=Axis.X, tangent:Tuple[float, float, float]=(0,1,0), suffix:str=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT, tipScale=0.25, **kwargs) -> MayaObject:
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    distance = ref.control_size() * 1.5
    radius = distance * tipScale
    mult = -1 if ref.side == Side.RIGHT else 1
    tangent = om.MVector(tangent) * mult
    circle = cmds.circle(n='temp#', nr=_VECTORS[axis], r=radius)[0]
    cmds.move(*(tangent * (distance + radius)), circle)
    line = cmds.curve(n='temp#', d=1, p=[
        (0, 0, 0),
        tangent * distance
    ])
    combine_curves([circle, line], ctrl)
    return place_ctrl(ctrl, ref, parent=parent)

def fkIkSwitch(ref:Joint, name:str, parent:MayaObject, * , position:Tuple[float, float, float], relative=True, suffix:str=Suffix.SWITCH_CONTROL, onCollision=CollisionBehavior.INCREMENT, size:float=None, default=0):
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    if not size:
        size = ref.control_size()
    
    if ctrl.side == Side.RIGHT:
        position = om.MVector(-position[0], position[1], position[2])

    fk = _text_curve('FK', scale=size)
    ik = _text_curve('IK', scale=size)

    fk_curves = [MayaObject(curve) for curve in cmds.listRelatives(fk, shapes=True)]
    ik_curves = [MayaObject(curve) for curve in cmds.listRelatives(ik, shapes=True)]
    
    combine_curves([fk, ik], ctrl)

    ctrl.addAttr('ik', value=default, type_='enum', options=['FK', 'IK'], niceName='Posing')
    fk_visibility = MayaObject(cmds.shadingNode('reverse', n=ctrl.but_with(suffix='fkVisibility').resolve_collisions(), au=True))
    ctrl.attr('ik') >> fk_visibility.attr('inputX')
    fk_visibility.attr('outputX') >> ctrl.addAttr('fk', 1, type_='enum', options=['Off', 'On'], keyable=False, channelBox=False)

    for curve in fk_curves:
        ctrl.attr('fk') >> curve.attr('visibility')
    for curve in ik_curves:
        ctrl.attr('ik') >> curve.attr('visibility')

    return place_ctrl(ctrl, ref, parent=parent, position=position, relative=relative, rotate=False)

def place_ctrl(ctrl:MayaObject, ref:Joint, parent:MayaObject=None, position:Tuple[float, float, float] = (0, 0, 0), relative=True, inherit_transforms=True, * , rotate=True):
    """Places a control (assumed to be at the origin) and sets its rest position."""
    if relative:
        if position[0] or position[1] or position[2]:
            localPos:om.MVector = om.MVector(position).transformAsNormal(ref.worldInverseMatrix.get()) * om.MVector(position).length() if rotate else position
            cmds.move(*localPos, ctrl, r=False)
            cmds.move(0, 0, 0, ctrl.attr('rotatePivot'), ctrl.attr('scalePivot'), r=False)
            cmds.makeIdentity(ctrl, a=True, t=True)
        cmds.matchTransform(ctrl, ref, pos=True, scl=True, rot=rotate)
    else:
        cmds.move(*position, ctrl, ws=True, r=False)
    
    if not inherit_transforms:
        ctrl.attr('inheritsTransform').set(0)
    
    if parent:
        cmds.parent(ctrl, parent)
    
    ctrl.set_rest()

    return ctrl

def combine_curves(curves:List[str], name:'str|MayaObject'='temp#'):
    """Combine multiple curves into a single object (placed at the world origin)"""
    out = cmds.group(n=name, em=True)
    cmds.parent(curves, out)
    cmds.makeIdentity(curves, a=True, t=True, r=True, s=True)
    for curve_transform in curves:
        shapes = cmds.listRelatives(curve_transform, shapes=True)
        cmds.parent(shapes, out, s=1, r=1)
        cmds.delete(curve_transform)
    cmds.select(out)
    return MayaObject(out)

def display_transform(source:MayaObject, target:MayaObject, systems_group:MayaObject):
    #target_parent = target.parent()
    offset_grp = groups.new_at(source, suffix='displayOffset', parent=systems_group)
    Nodes.Structures.parentConstraint(target, offset_grp)
    prev_selection = selection.get()
    selection.set(target)

    cluster = MayaObject(cmds.cluster(n=source.but_with(suffix='cluster'), bs=True, rel=True)[1])
    cmds.parent(cluster, offset_grp)
    cluster.set_rest()
    cmds.parentConstraint(source, cluster, mo=True)

    selection.set(prev_selection)


def _text_curve(text_obj:str, name:str='temp#', * , scale=1.0, font='Sans Serif'):
    text_obj, makeText = cmds.textCurves(f=font, t=text_obj)
    cmds.scale(scale, scale, scale, text_obj)

    # Extract the actual curve objects so they can be combined
    curve_transforms = cmds.listRelatives(
        cmds.listRelatives(text_obj, ad=True, ni=True, typ='nurbsCurve'),
        p=True,
        typ='transform'
    )
    cmds.parent(curve_transforms, w=True)
    cmds.delete(text_obj, makeText)
    joined = combine_curves(curve_transforms, name=name)

    cmds.xform(joined, cp=True) # Center the pivot
    cmds.move(0, 0, 0, rpr=True) # Move to (0, 0, 0) in world space
    cmds.makeIdentity(joined, a=True)
    return joined