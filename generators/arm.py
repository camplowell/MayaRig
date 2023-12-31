from maya import cmds
from typing import List
import maya.api.OpenMaya as om
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
    _orient_joints(driver_joints)

    control_grp = groups.create_control_group(driver_joints[0], name)
    systems_grp = groups.systems_group(driver_joints[0], name)
    flipped=naming.get_side(driver_joints[0]) == Side.RIGHT

    clavicle = joints.find('clavicle', driver_joints)
    shoulder_loc = None
    arm_space = groups.empty_at(joints.find('shoulder', driver_joints), name, suffix=Suffix.SPACE_SWITCH, parent=control_grp)
    if clavicle:
        clavicle_parent = joints.get_parent(clavicle)
        clavicle_offset = groups.empty_at(clavicle, 'clavicleOffset', parent=clavicle_parent)

        if clavicle_parent == naming.driver_grp:
            cmds.parentConstraint(naming.root_control, clavicle_offset, mo=True)

        cmds.parent(clavicle, clavicle_offset)

        clavicle_curve = clavicle_control(
            'shoulder',
            Suffix.CONTROL,
            clavicle,
            parent=control_grp,
            flipped=flipped
        )
        cmds.parentConstraint(clavicle_curve, clavicle, mo=True)

        shoulder = joints.find('shoulder', driver_joints)
        shoulder_loc = groups.empty_at(shoulder, "shoulderLoc", parent=systems_grp)
        cmds.parentConstraint(clavicle, shoulder_loc, mo=True)
        cmds.parent(arm_space, clavicle_curve)
    
    fk = _create_fk(driver_joints, control_grp, systems_grp, flipped, shoulder_loc=shoulder_loc)
    ik = _create_ik(driver_joints, control_grp, systems_grp, flipped, shoulder_loc=shoulder_loc)

    _ik_switch(driver_joints, fk, ik, control_grp, flipped, arm_space)

    _create_hand(driver_joints, control_grp, flipped)

def create_bind_joints(driver_joints:List[str]):
    """Generates bind joints driven by the driver joints."""
    driver_joints = [joint for joint in driver_joints if joints.to_bind(joint)]
    bind_joints = joints.variants(driver_joints, Suffix.BIND_JOINT, parent_if_exists=True)
    if joints.get_parent(driver_joints[0]).endswith(Suffix.GROUP):
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
    thumb = marker(Side.LEFT, 'thumb', (52, -0.8, 0), type_='knuckle')
    thumb2 = marker(Side.LEFT, 'thumbMCP', (54.6, -2.7, 3.1), type_='finger')
    marker(Side.LEFT, 'thumbDIP', (56.5, -4.1, 4.6), type_='finger')
    thumb_tip = marker(Side.LEFT, 'thumbTip', (58.5, -5.3, 5.9), type_='fingerTip', bind=False)

    joints.orient_normal(
                thumb, 
                joints.get_normal([thumb, thumb2, thumb_tip]))

    joints.start_chain(wrist)
    marker(Side.LEFT, 'pointerCMC', (54.0,  0.1, -0.6), type_='metacarpal'),
    marker(Side.LEFT, 'pointer', (59.4, -0.7, 0.5), type_='knuckle'),
    marker(Side.LEFT, 'pointerPIP', (63.5, -1.3, 1.7), type_='finger'),
    marker(Side.LEFT, 'pointerDIP', (65.6, -1.7, 2.2), type_='finger'),
    marker(Side.LEFT, 'pointerTip', (67.7, -2.3, 2.8), type_='fingerTip', bind=False)

    joints.start_chain(wrist)
    marker(Side.LEFT, 'middleCMC', (54.2,  0.1, -2.2), type_='metacarpal'),
    marker(Side.LEFT, 'middle', (59.8, -0.7, -2.0), type_='knuckle'),
    marker(Side.LEFT, 'middle2', (64.6, -1.4, -1.7), type_='finger'),
    marker(Side.LEFT, 'middle3', (67.1, -1.9, -1.6), type_='finger'),
    marker(Side.LEFT, 'middleTip', (69.5, -2.5, -1.5), type_='fingerTip', bind=False)

    joints.start_chain(wrist)
    marker(Side.LEFT, 'ringCMC', (54.2,  0.0, -3.7), type_='metacarpal'),
    marker(Side.LEFT, 'ring', (59.3, -0.8, -4.5), type_='knuckle'),
    marker(Side.LEFT, 'ring2', (63.8, -1.8, -5.1), type_='finger'),
    marker(Side.LEFT, 'ring3', (66.0, -2.3, -5.4), type_='finger'),
    marker(Side.LEFT, 'ringTip', (68.3, -3.0, -5.7), type_='fingerTip', bind=False)

    joints.start_chain(wrist)
    marker(Side.LEFT, 'pinkyCMC', (54.0, -0.4, -5.3), type_='metacarpal'),
    marker(Side.LEFT, 'pinky', (57.9, -1.3, -6.6), type_='knuckle'),
    marker(Side.LEFT, 'pinky2', (61.9, -2.1, -7.8), type_='finger'),
    marker(Side.LEFT, 'pinky3', (64.0, -2.6, -8.4), type_='finger'),
    marker(Side.LEFT, 'pinkyTip', (66.0, -3.3, -9.0), type_='fingerTip', bind=False)
    
    if side == Side.RIGHT:
        root_r = joints.mirror(root)
        cmds.delete(root)
        root = root_r
    joints.mark_root(root, name, is_symmetrical)
    selection.set_(root)

# Create controls --------------------------------------------------------------------------------

def _orient_joints(driver_joints):
    if 'clavicle' in driver_joints[0]:
        joints.orient(naming.find('clavicle', driver_joints))
    joints.orient(naming.find('shoulder', driver_joints))
    joints.coplanar_orient(naming.find('elbow', driver_joints))

    wrist = joints.find('wrist', driver_joints)
    knuckles = joints.find_all('knuckle', driver_joints)
    for knuckle in knuckles:
        if 'thumb' not in knuckle:
            joints.orient_match(knuckle, wrist, twist=-90)
        for finger in joints.find_children('finger', knuckle):
            joints.orient_match(finger, knuckle)

def _create_fk(driver_joints, control_grp, systems_grp, flipped, shoulder_loc):
    driver_joints = [
        joints.find('shoulder', driver_joints),
        joints.find('elbow', driver_joints),
        joints.find('wrist', driver_joints)
    ]
    fk = joints.variants(driver_joints, Suffix.FK_JOINT, root_parent=systems_grp)
    
    shoulder = joints.find('shoulder', fk)
    shoulder_ctrl = controls.circle(
        'upperArm', Suffix.FK_CONTROL,
        joint = shoulder,
        parent = control_grp,
        flipped = flipped,
        radius=6
    )
    controls.space_switch(
        shoulder_ctrl,
        [(naming.cog_control, 'CoG'), (naming.root_control, 'Layout')], 
        systems_group=systems_grp,
        parent_space_name='Body',
        rotation_only=True
    )
    cmds.orientConstraint(shoulder_ctrl, shoulder)
    if shoulder_loc:
        cmds.pointConstraint(shoulder_loc, shoulder_ctrl)
    else:
        attributes.lock(shoulder_ctrl, 'translation')

    elbow = joints.find('elbow', fk)
    elbow_ctrl = controls.circle(
        'forearm', Suffix.FK_CONTROL,
        joint = elbow,
        parent = shoulder_ctrl,
        flipped = flipped
    )
    attributes.connect(elbow_ctrl, 'rotate', elbow)
    attributes.connect(elbow_ctrl, 'scale', elbow)
    attributes.lock(elbow_ctrl, ['translate', 'rotateX', 'rotateZ'])

    wrist = joints.find('wrist', fk)
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
    
def _create_ik(driver_joints, control_grp, systems_grp, flipped, shoulder_loc):
    driver_joints = [
        joints.find('shoulder', driver_joints),
        joints.find('elbow', driver_joints),
        joints.find('wrist', driver_joints)
    ]
    ik = joints.variants(driver_joints, Suffix.IK_JOINT, root_parent=systems_grp)

    shoulder = naming.find('shoulder', ik)
    elbow = naming.find('elbow', ik)
    wrist = naming.find('wrist', ik)
    if shoulder_loc:
        cmds.pointConstraint(shoulder_loc, shoulder)

    handle = naming.replace(wrist, name=name, suffix=Suffix.IK_HANDLE)
    cmds.ikHandle(n=handle, sj=shoulder, ee=wrist, solver='ikRPsolver')
    cmds.parent(handle, systems_grp) 
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
    
    if naming.get_side(wrist_ctrl) == Side.RIGHT:
        cmds.rotate(0, 180, 180, wrist_ctrl)
        controls.set_rest_pose(wrist_ctrl)

    controls.space_switch(
        wrist_ctrl,
        [(naming.cog_control, 'CoG'), (naming.root_control, 'Layout')], 
        systems_group=systems_grp,
        parent_space_name='Body'
    )
    cmds.pointConstraint(wrist_ctrl, handle)
    cmds.orientConstraint(wrist_ctrl, wrist, mo=True)

    attributes.delete_all(ik)
    return ik

def _ik_switch(driver_joints, fk, ik, control_grp, arm_space, flipped):
    wrist = naming.find('wrist', driver_joints)
    switch, invert = controls.ik_switch(
        name,
        wrist,
        offset = (0, 1.0, -1.5),
        parent = control_grp,
        flipped = flipped
    )

    for i in range(len(fk)):
        fk_joint = fk[i]
        ik_joint = joints.find_equiv(fk_joint, ik)
        driver_joint = joints.find_equiv(fk_joint, driver_joints)
        orient = cmds.orientConstraint([fk_joint, ik_joint], driver_joint)[0]
        attributes.connect(invert, 'output1D', orient, fk_joint + 'W0')
        attributes.connect(switch, naming.IK_SWITCH_ATTR, orient, ik_joint + 'W1')
        scale = cmds.scaleConstraint([fk_joint, ik_joint], driver_joint)[0]
        attributes.connect(invert, 'output1D', scale, fk_joint + 'W0')
        attributes.connect(switch, naming.IK_SWITCH_ATTR, scale, ik_joint + 'W1')

def _create_hand(driver_joints, control_grp, flipped):
    wrist = naming.find('wrist', driver_joints)

    hand_group = groups.empty_at(wrist, 'hand', parent=control_grp, suffix='offset')
    cmds.parentConstraint(wrist, hand_group)
    cmds.scaleConstraint(wrist, hand_group)

    for knuckle in joints.find_children('knuckle', wrist):

        finger_joints = joints.find_children('finger', knuckle, backwards=True)
        finger_joints.append(knuckle)
        finger_joints.reverse()

        finger_name = naming.get_name(knuckle, ignore_num=True)
        root_ctrl = controls.finger_root(
            finger_name, suffix=Suffix.CONTROL, 
            joint=knuckle, 
            parent=hand_group,
            flipped=flipped
        )

        fingerBend = nodes.composeMatrix(naming.replace(knuckle, suffix='bend'))
        attributes.connect(root_ctrl, 'rotate.rotateY', fingerBend, 'inputRotate.inputRotateY')
        prev = root_ctrl
        for joint in finger_joints:
            ctrl = controls.circle(
                naming.get_name(joint, ignore_num=False),
                suffix=Suffix.TWEAK_CONTROL,
                joint=joint,
                parent=prev,
                flipped=flipped,
                radius=1
            )
            if (prev != root_ctrl):
                ctrl_parentOffset = nodes.matMult(naming.replace(joint, suffix='parentOffset'))
                attributes.connect(fingerBend, 'outputMatrix', ctrl_parentOffset, 'matrixIn[0]')
                attributes.copy(ctrl, 'offsetParentMatrix', ctrl_parentOffset, 'matrixIn[1]', type_='matrix')
                attributes.connect(ctrl_parentOffset, 'matrixSum', ctrl, 'offsetParentMatrix')
            cmds.parentConstraint(ctrl, joint)
            cmds.scaleConstraint(ctrl, joint)
            prev = ctrl

# Arm Specific Controls ==========================================================================

def clavicle_control(name: str, suffix:str, joint:str, parent:str, flipped=False, * , size=6):
    name = naming.replace(joint, name=name, suffix=suffix)
    joint_pos = joints.get_position(joint)
    joint_child = joints.get_child(joint)
    child_pos = joints.get_position(joint_child)

    shoulder_length = child_pos.x - joint_pos.x

    radius = attributes.get_control_size(joint) * size

    arc0 = cmds.circle(n='temp#', r=radius, nr=(1, 0, 0), sw=90)[0]
    arc1 = cmds.circle(n="temp#", r=radius, nr=(1, 0, 0), sw=90)[0]
    cmds.move(0.50 * shoulder_length, 0, 0, arc0)
    cmds.move(0.75 * shoulder_length, 0, 0, arc1)
    line0 = cmds.curve(
        n='temp#',
        d=1,
        p=[
            (0.50 * shoulder_length, radius, 0),
            (0.75 * shoulder_length, radius, 0)
        ]
    )
    line1 = cmds.curve(
        n='temp#',
        d=1,
        p=[
            (0.50 * shoulder_length, 0, radius),
            (0.75 * shoulder_length, 0, radius)
        ]
    )
    cmds.rotate(-45, 0, 0, [arc0, arc1, line0, line1])
    cmds.move(0, child_pos.y - joint_pos.y, child_pos.z - joint_pos.z, [arc0, arc1, line0, line1], r=True)
    cmds.move(0, 0, 0, arc0+".scalePivot", arc0+".rotatePivot", absolute=True)

    ret = controls._combine([arc0, arc1, line0, line1], name)
    return controls._to_pos(ret, (joint_pos.x, joint_pos.y, joint_pos.z), parent=parent)