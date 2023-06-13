from maya import cmds
from typing import List
from ..core import *
from ..core.joints import marker

name = "arm"

def create_menu():
    """Returns a layout containing:
    - Any options the generator needs to generate
    - A button that generates markers for the limb"""
    layout = cmds.columnLayout(w=250, rs=4)
    side_field = cmds.optionMenu(label='Side', w=250)
    cmds.menuItem(label='Left')
    cmds.menuItem(label='Right')
    symmetrical_field=cmds.checkBox(label='Symmetrical', v=True)
    clavicle_field=cmds.checkBox(label='Include Shoulders', v=True)
    cmds.button(
        label='Add', 
        command=lambda _ : _create_markers(
            symmetrical_field, 
            side_field,
            clavicle_field), 
        w=250)
    cmds.setParent('..')
    return layout

def create_controllers(driver_joints:List[str]):
    """Generates controllers for the driver joints.
    May modify the structure of the driver skeleton."""
    if 'clavicle' in driver_joints[0]:
        joints.orient(naming.find('clavicle', driver_joints))
    joints.orient(naming.find('shoulder', driver_joints))
    joints.coplanar_orient(naming.find('elbow', driver_joints))

    control_grp = groups.create_control_group(driver_joints[0], name)
    systems_grp = groups.systems_group(driver_joints[0], name)
    flipped=naming.get_side(driver_joints[0]) == Side.RIGHT

    fk = _create_fk(driver_joints, control_grp, systems_grp, flipped)
    ik = _create_ik(driver_joints, control_grp, systems_grp, flipped)

    _ik_switch(driver_joints, fk, ik, control_grp, flipped)

def create_bind_joints(driver_joints:List[str]):
    """Generates bind joints driven by the driver joints."""
    bind_joints = joints.variants(driver_joints, Suffix.BIND_JOINT, parent_if_exists=True)
    if joints.get_parent(driver_joints[0]) == naming.driver_grp:
        cmds.parent(bind_joints[0], naming.bind_grp)
    
    for i in range(len(driver_joints)):
        cmds.parentConstraint(driver_joints[i], bind_joints[i])
        cmds.scaleConstraint(driver_joints[i], bind_joints[i])

    attributes.delete_all(driver_joints)

# Create markers --------------------------------------------------------------------------------
def _create_markers(symmetrical_field, side_field, clavicle_field):
    has_clavicle = cmds.checkBox(clavicle_field, q=True, v=True)
    is_symmetrical = cmds.checkBox(symmetrical_field, q=True, v=True)
    side_str = cmds.optionMenu(side_field, q=True, v=True)
    side = Side.LEFT
    if side_str == 'Right':
        side = Side.RIGHT
    
    selection.clear()
    root = None
    if has_clavicle:
        root = marker(Side.LEFT, 'clavicle', (2, 0, 2))
    shoulder = marker(Side.LEFT, 'shoulder', (10, 0, -4))
    if not has_clavicle:
        root = shoulder
    marker(Side.LEFT, 'elbow', (30, 0, -4.05))
    wrist = marker(Side.LEFT, 'wrist', (50, 0, -2.5))
    """
    marker(Side.LEFT, 'thumbCMC', (52, -0.8, 0))
    marker(Side.LEFT, 'thumbMCP', (54.6, -2.7, 3.1))
    marker(Side.LEFT, 'thumbDIP', (56.5, -4.1, 4.6))
    marker(Side.LEFT, 'thumbTip', (58.5, -5.3, 5.9))

    selection.set_(wrist)
    marker(Side.LEFT, 'pointerCMC', (54.0,  0.1, -0.6))
    marker(Side.LEFT, 'pointerMCP', (59.4, -0.7, 0.5))
    marker(Side.LEFT, 'pointerPIP', (63.5, -1.3, 1.7))
    marker(Side.LEFT, 'pointerDIP', (65.6, -1.7, 2.2))
    marker(Side.LEFT, 'pointerTip', (67.7, -2.3, 2.8))

    selection.set_(wrist)
    marker(Side.LEFT, 'middleCMC', (54.2,  0.1, -2.2))
    marker(Side.LEFT, 'middleMCP', (59.8, -0.7, -2.0))
    marker(Side.LEFT, 'middlePIP', (64.6, -1.4, -1.7))
    marker(Side.LEFT, 'middleDIP', (67.1, -1.9, -1.6))
    marker(Side.LEFT, 'middleTip', (69.5, -2.5, -1.5))

    selection.set_(wrist)
    marker(Side.LEFT, 'ringCMC', (54.2,  0.0, -3.7))
    marker(Side.LEFT, 'ringMCP', (59.3, -0.8, -4.5))
    marker(Side.LEFT, 'ringPIP', (63.8, -1.8, -5.1))
    marker(Side.LEFT, 'ringDIP', (66.0, -2.3, -5.4))
    marker(Side.LEFT, 'ringTip', (68.3, -3.0, -5.7))

    selection.set_(wrist)
    marker(Side.LEFT, 'pinkyCMC', (54.0, -0.4, -5.3))
    marker(Side.LEFT, 'pinkyMCP', (57.9, -1.3, -6.6))
    marker(Side.LEFT, 'pinkyPIP', (61.9, -2.1, -7.8))
    marker(Side.LEFT, 'pinkyDIP', (64.0, -2.6, -8.4))
    marker(Side.LEFT, 'pinkyTip', (66.0, -3.3, -9.0))
    """
    if side == Side.RIGHT:
        root_r = joints.mirror(root)
        cmds.delete(root)
        root = root_r
    joints.mark_root(root, name, is_symmetrical)
    cmds.parent(root, naming.marker_grp)
    selection.set_(root)

# Create controls --------------------------------------------------------------------------------
def _create_fk(driver_joints, control_grp, systems_grp, flipped):
    fk = joints.variants(driver_joints, Suffix.FK_JOINT, root_parent=systems_grp)
    
    shoulder = naming.find('shoulder', fk)
    shoulder_ctrl = controls.circle(
        'upperArm', Suffix.FK_CONTROL,
        joint = shoulder,
        parent = control_grp,
        flipped = flipped,
        radius=6
    )
    attributes.connect(shoulder_ctrl, 'rotate', shoulder)
    attributes.connect(shoulder_ctrl, 'scale', shoulder)
    attributes.lock(shoulder_ctrl, ['translate'])

    elbow = naming.find('elbow', fk)
    elbow_ctrl = controls.circle(
        'forearm', Suffix.FK_CONTROL,
        joint = elbow,
        parent = shoulder_ctrl,
        flipped = flipped
    )
    attributes.connect(elbow_ctrl, 'rotate', elbow)
    attributes.connect(elbow_ctrl, 'scale', elbow)
    attributes.lock(elbow_ctrl, ['translate', 'rotateX', 'rotateZ'])

    wrist = naming.find('wrist', fk)
    wrist_ctrl = controls.circle(
        'wrist', Suffix.FK_CONTROL,
        joint = wrist,
        parent = elbow_ctrl,
        flipped = flipped
    )
    attributes.connect(wrist_ctrl, 'rotate', wrist)
    attributes.connect(wrist_ctrl, 'scale', wrist)
    attributes.lock(wrist_ctrl, ['translate'])

    attributes.delete_all(fk)
    return fk
    
def _create_ik(driver_joints, control_grp, systems_grp, flipped):
    ik = joints.variants(driver_joints, Suffix.IK_JOINT, root_parent=systems_grp)
    

    shoulder = naming.find('shoulder', ik)
    elbow = naming.find('elbow', ik)
    wrist = naming.find('wrist', ik)

    handle = naming.replace(wrist, name=name, suffix=Suffix.IK_HANDLE)
    cmds.ikHandle(n=handle, sj=shoulder, ee=wrist, solver='ikRPsolver')
    cmds.parent(handle, control_grp) 
    controls.set_rest_pose(handle)

    pole = controls.ik_pole(
        name,
        elbow,
        control_grp
    )
    cmds.poleVectorConstraint(pole, handle)

    wrist_ctrl = controls.square(
        'hand', Suffix.IK_CONTROL,
        wrist,
        parent=control_grp
    )
    cmds.parentConstraint(naming.root_control, wrist_ctrl, mo=True)
    cmds.pointConstraint(wrist_ctrl, handle)
    cmds.orientConstraint(wrist_ctrl, wrist)

    attributes.delete_all(ik)
    return ik

def _ik_switch(driver_joints, fk, ik, control_grp, flipped):
    switch, invert = controls.ik_switch(
        name,
        naming.find('wrist', driver_joints),
        offset = (0, 1.0, -1.5),
        parent = control_grp,
        flipped = flipped
    )

    for i in range(len(driver_joints)):
        orient = cmds.orientConstraint([fk[i], ik[i]], driver_joints[i])[0]
        attributes.connect(invert, 'output1D', orient, fk[i] + 'W0')
        attributes.connect(switch, naming.IK_SWITCH_ATTR, orient, ik[i] + 'W1')
        scale = cmds.scaleConstraint([fk[i], ik[i]], driver_joints[i])[0]
        attributes.connect(invert, 'output1D', scale, fk[i] + 'W0')
        attributes.connect(switch, naming.IK_SWITCH_ATTR, scale, ik[i] + 'W1')
