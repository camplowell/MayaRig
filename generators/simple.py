from maya import cmds
from typing import List
from ..core import *

name = "simple"

def create_menu():
    """Returns a layout containing:
    - Any options the generator needs to generate
    - A button that generates markers for the limb"""
    layout = cmds.columnLayout(w=250, rs=4)
    side_field = cmds.optionMenu(label='Side', w=250)
    cmds.menuItem(label='Left')
    cmds.menuItem(label='Center')
    cmds.menuItem(label='Right')
    symmetrical_field=cmds.checkBox(label='Symmetrical', v=True)
    cmds.button(
        label='Add', 
        command=lambda _ : _create_markers(
            symmetrical_field, 
            side_field), 
        w=250)
    cmds.setParent('..')
    return layout

def create_controllers(driver_joints:List[str]):
    """Generates controllers for the driver joints.
    May modify the structure of the driver skeleton."""
    control_grp = groups.create_control_group(driver_joints[0], naming.get_name(driver_joints[0]))
    parent = control_grp
    axis = attributes.get(driver_joints[0], 'axis')
    for bone in driver_joints:
        if exists(bone, 'axis'):
            axis = attributes.get(bone, 'axis')
        normal = [0, 0, 0]
        normal[axis] = 1
        ctrl = controls.ellipse(
            name=naming.get_name(bone), suffix=Suffix.CONTROL,
            joint=bone,
            parent=parent,
            normal=tuple(normal))
        parent = ctrl
        cmds.parentConstraint(ctrl, bone)
        cmds.scaleConstraint(ctrl, bone)

def create_bind_joints(driver_joints:List[str]):
    """Generates bind joints driven by the driver joints."""
    bind_joints = joints.variants(driver_joints, suffix=Suffix.BIND_JOINT, parent_if_exists=True)
    root_parent = joints.get_parent(bind_joints[0])
    if root_parent == naming.driver_grp:
        cmds.parent(bind_joints[0], naming.bind_grp)
    for i in range(len(driver_joints)):
        cmds.parentConstraint(driver_joints[i], bind_joints[i])
        cmds.scaleConstraint(driver_joints[i], bind_joints[i])

    attributes.delete_all(driver_joints)

def _create_markers(symmetrical_field, side_field):
    side_str = cmds.optionMenu(side_field, q=True, v=True)
    side = Side.CENTER
    if side_str == 'Left':
        side = Side.LEFT
    elif side_str == 'Right':
        side = Side.RIGHT
    joint = joints.marker(side, 'joint', (0, 0, 0))
    joints.mark_root(joint, name, cmds.checkBox(symmetrical_field, q=True, v=True))
    attributes.add_enum(joint, 'axis', 'X:Y:Z:', active=0, keyable=True)