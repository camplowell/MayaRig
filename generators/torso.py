from maya import cmds
from typing import List
from ..core import *

name = "torso"

def create_menu():
    """Returns a layout containing:
    - Any options the generator needs to generate
    - A button that generates markers for the limb"""
    layout = cmds.columnLayout(w=250, rs=4)
    type_field = cmds.optionMenu( label='Type')
    cmds.menuItem( label='Simple' )
    cmds.button(
        label='Add', 
        command=lambda _ : _create_markers(
            type_field), 
        w=250)
    cmds.setParent('..')
    return layout

def create_controllers(driver_joints:List[str]):
    """Generates controllers for the driver joints.
    May modify the structure of the driver skeleton."""
    hip_bone = driver_joints[0]
    control_grp = groups.create_control_group(hip_bone, name)

    cog_controller = controls.circle_with_arrows("centerOfGravity", suffix=Suffix.CONTROL, joint=hip_bone, parent=control_grp)
    hip_controller = controls.saddle("hip", suffix=Suffix.CONTROL, joint=hip_bone, parent=cog_controller)

    cmds.parentConstraint(hip_controller, hip_bone)

def create_bind_joints(driver_joints:List[str]):
    """Generates bind joints driven by the driver joints."""
    
    bind_joints = joints.variants(driver_joints, suffix=Suffix.BIND_JOINT, parent_if_exists=True)
    root_parent = joints.get_parent(bind_joints[0])

    if root_parent == naming.driver_grp:
        cmds.parent(bind_joints[0], naming.bind_grp)
    
    for i in range(len(driver_joints)):
        cmds.parentConstraint(driver_joints[i], bind_joints[i])
        cmds.scaleConstraint(driver_joints[i], bind_joints[i])

# IMPLEMENTATION =================================================================================

def _create_markers(type_field):
    marker = joints.marker(Side.CENTER, "centerOfGravity", (0, 0, 0), type_="CoG_simple")
    joints.mark_root(marker, name)