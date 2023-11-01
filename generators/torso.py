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
    cmds.menuItem( label='FK' )
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

    cog_bone = joints.find("CoG", driver_joints)
    control_grp = groups.create_control_group(cog_bone, name)
    
    style = attributes.get(cog_bone, 'style')
    pelvis_bone = joints.find('pelvis', driver_joints)
    cog_controller = controls.circle_with_arrows("centerOfGravity", suffix=Suffix.CONTROL, joint=cog_bone, parent=control_grp, radius=20)

    pelvis_controller = controls.saddle("hip", suffix=Suffix.CONTROL, joint=pelvis_bone, parent=cog_controller, radius=16)
    cmds.parentConstraint(pelvis_controller, pelvis_bone)

    if (style == 0):
        return
    if (style == 1):
        systems_grp = groups.systems_group(cog_bone, name)
        spine0 = joints.find('spine0', driver_joints)
        spine1 = joints.find('spine1', driver_joints)
        spine2 = joints.find('spine2', driver_joints)
        middleTorso_offset = groups.empty_at(spine0, 'middleTorso', suffix=Suffix.OFFSET, parent=cog_controller, offset=0.5 * joints.offset_to(spine0, spine1))
        middleTorso_fk = controls.circle(
            'middleTorso', suffix=Suffix.CONTROL, 
            joint=spine0,
            radius=16,
            normal=(0, 1, 0),
            slide=0.5,
            parent=middleTorso_offset
        )
        shoulder_fk = controls.saddle(
            'upperTorso', suffix=Suffix.CONTROL,
            joint=spine2,
            radius=16,
            depth=-4,
            parent=cog_controller
        )
        cmds.orientConstraint(pelvis_controller, middleTorso_offset, w=attributes.get(spine0, 'weight_pelvis'))
        cmds.orientConstraint(shoulder_fk, middleTorso_offset, w=attributes.get(spine0, 'weight_shoulder'))

        cmds.pointConstraint(pelvis_bone, spine0)
        cmds.orientConstraint(middleTorso_fk, spine0)

        cmds.orientConstraint(middleTorso_fk, spine1, w=attributes.get(spine1, 'weight_middle'))
        cmds.orientConstraint(shoulder_fk, spine1, w=attributes.get(spine1, 'weight_shoulder'))

        cmds.orientConstraint(shoulder_fk, spine2)

        controls.display_transform(middleTorso_fk, spine0, systems_grp)
        controls.display_transform(shoulder_fk, spine2, systems_grp)

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
    type_str = cmds.optionMenu(type_field, q=True, v=True)

    center_of_gravity = joints.marker(Side.CENTER, "centerOfGravity", (0, 0, 0), type_="CoG", bind=False)
    attributes.set_(center_of_gravity, 'radius', 2)
    joints.mark_root(center_of_gravity, name)

    if type_str == 'Simple':
        attributes.add(center_of_gravity, 'style', 0, type_='number')
        pelvis = joints.marker(Side.CENTER, "pelvis", (0, 0, 0), type_="pelvis")
        selection.set_(center_of_gravity)
        return
    if type_str == 'FK':
        attributes.add(center_of_gravity, 'style', 1, type_='float')

        hip = joints.marker(Side.CENTER, 'pelvis', (0, 0, 0), type_="pelvis")
        joints.marker(Side.CENTER, 'pelvisNib', (0, -14, -4), type_="pelvisNib", bind=False)
        selection.set_(center_of_gravity)

        spine0 = joints.marker(Side.CENTER, 'spine0', (0, 0, 0), type_='spine0')
        attributes.add(spine0, 'weight_pelvis', 0.5, type_='float', keyable=True)
        attributes.add(spine0, 'weight_shoulder', 0.5, type_='float', keyable=True)

        spine1 = joints.marker(Side.CENTER, 'spine1', (0, 8, 0), type_='spine1')
        attributes.add(spine1, 'weight_middle', 0.1, type_='float', keyable=True)
        attributes.add(spine1, 'weight_shoulder', 0.9, type_='float', keyable=True)

        joints.marker(Side.CENTER, 'spine2', (0, 17, -4), type_='spine2')
        joints.marker(Side.CENTER, 'neckBase', (0, 32, -6), type_='neckBase')
        selection.set_(center_of_gravity)
        return
