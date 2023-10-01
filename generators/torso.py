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
    cog_bone = joints.find("CoG_simple", driver_joints)
    pelvis_bone = joints.find("pelvis", driver_joints)
    control_grp = groups.create_control_group(cog_bone, name)

    cog_controller = controls.circle_with_arrows("centerOfGravity", suffix=Suffix.CONTROL, joint=cog_bone, parent=control_grp, radius=20)
    pelvis_controller = controls.saddle("hip", suffix=Suffix.CONTROL, joint=pelvis_bone, parent=cog_controller, radius=16)

    cmds.parentConstraint(pelvis_controller, pelvis_bone)

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
    center_of_gravity = joints.marker(Side.CENTER, "centerOfGravity", (0, 0, 0), type_="CoG_simple", bind=False)
    attributes.set_(center_of_gravity, 'radius', 2)
    pelvis = joints.marker(Side.CENTER, "pelvis", (0, 0, 0), type_="pelvis")
    joints.mark_root(center_of_gravity, name)