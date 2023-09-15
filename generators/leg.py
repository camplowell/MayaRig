from maya import cmds
import maya.api.OpenMaya as om
from typing import List
from ..core import *
from ..core.joints import marker

name = "leg"

def create_menu():
    """Returns a layout containing:
    - Any options the generator needs to generate
    - A button that generates markers for the limb"""
    layout = cmds.columnLayout(w=250, rs=4)
    side_field = cmds.optionMenu(label='Side', w=250)
    cmds.menuItem(label='Left')
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
    reverse_foot_drivers = [
        naming.find('heel', driver_joints),
        naming.find('footBankInner', driver_joints),
        naming.find('footBankOuter', driver_joints)
    ]
    hip = naming.find('hip', driver_joints)
    knee = naming.find('knee', driver_joints)
    ankle = naming.find('ankle', driver_joints)
    ball = naming.find('ballOfFoot', driver_joints)
    tip = naming.find('tipOfToe', driver_joints)
    driver_joints = [hip, knee, ankle, ball, tip]

    joints.orient(hip, secondaryAxisOrient='zup')
    joints.coplanar_orient(knee)
    joints.world_orient(ankle)
    joints.world_orient(ball, flip_right = True)

    control_grp = groups.create_control_group(driver_joints[0], name)
    systems_grp = groups.systems_group(driver_joints[0], name)
    flipped=naming.get_side(driver_joints[0]) == Side.RIGHT

    fk = _create_fk(
        driver_joints, 
        control_grp,
        systems_grp, 
        flipped)
    ik = _create_ik(
        driver_joints, 
        reverse_foot_drivers, 
        control_grp,
        systems_grp, 
        flipped)

    _ik_switch(driver_joints, fk, ik, control_grp, flipped)

    for joint in reverse_foot_drivers:
        children = cmds.listRelatives(joint, c=True)
        if children:
            cmds.parent(children, ankle)
        cmds.delete(joint)

def create_bind_joints(driver_joints:List[str]):
    """Generates bind joints driven by the driver joints."""
    
    hip = naming.find('hip', driver_joints)
    knee = naming.find('knee', driver_joints)
    ankle = naming.find('ankle', driver_joints)
    ball = naming.find('ballOfFoot', driver_joints)
    to_bind = [hip, knee, ankle, ball]
    
    bind_joints = joints.variants(to_bind, Suffix.BIND_JOINT, parent_if_exists=True)
    if joints.get_parent(driver_joints[0]) == naming.driver_grp:
        cmds.parent(bind_joints[0], naming.bind_grp)
    
    for i in range(len(bind_joints)):
        cmds.parentConstraint(driver_joints[i], bind_joints[i])
        cmds.scaleConstraint(driver_joints[i], bind_joints[i])

    attributes.delete_all(driver_joints)

# Create markers --------------------------------------------------------------------------------
def _create_markers(symmetrical_field, side_field):
    is_symmetrical = cmds.checkBox(symmetrical_field, q=True, v=True)
    side_str = cmds.optionMenu(side_field, q=True, v=True)
    side = Side.LEFT
    if side_str == 'Right':
        side = Side.RIGHT
    
    selection.clear()
    hip = marker(Side.LEFT, 'hip', (7, 80, 0))
    marker(Side.LEFT, 'knee', (7, 45, 1))
    ankle = marker(Side.LEFT, 'ankle', (7, 10, -1))
    marker(Side.LEFT, 'heel', (7, 0, -9), bind=False)
    selection.set_(ankle)
    marker(Side.LEFT, 'ballOfFoot', (7, 1.5, 8))
    marker(side.LEFT, 'tipOfToe', (7, 0, 16))
    selection.set_(ankle)
    marker(side.LEFT, 'footBankInner', (4, 0, 9), bind=False)
    selection.set_(ankle)
    marker(side.LEFT, 'footBankOuter', (14, 0, 7), bind=False)

    if side == Side.RIGHT:
        hip_r = joints.mirror(hip)
        cmds.delete(hip)
        hip = hip_r
    joints.mark_root(hip, name, is_symmetrical)
    cmds.parent(hip, naming.marker_grp)

    selection.set_(hip)

# Create controls --------------------------------------------------------------------------------
def _create_fk(driver_joints, control_grp, systems_grp, flipped):
    fk = joints.variants(driver_joints, Suffix.FK_JOINT, root_parent=systems_grp)
    
    hip = naming.find('hip', fk)
    hip_ctrl = controls.circle(
        'upperLeg', Suffix.FK_CONTROL,
        joint = hip,
        parent = control_grp,
        flipped = flipped,
        radius=8
    )
    attributes.connect(hip_ctrl, 'rotate', hip)
    attributes.connect(hip_ctrl, 'scale', hip)
    attributes.lock(hip_ctrl, ['translate'])

    knee = naming.find('knee', fk)
    knee_ctrl = controls.circle(
        'lowerLeg', Suffix.FK_CONTROL,
        joint = knee,
        parent = hip_ctrl,
        flipped = flipped,
        radius=7
    )
    attributes.connect(knee_ctrl, 'rotate', knee)
    attributes.connect(knee_ctrl, 'scale', knee)
    attributes.lock(knee_ctrl, ['translate', 'rotateX', 'rotateZ'])

    ankle = naming.find('ankle', fk)
    ankle_ctrl = controls.ellipse(
        'ankle', Suffix.FK_CONTROL,
        joint = ankle,
        parent = knee_ctrl,
        normal=(0, 1, 0),
        size=(6, 6, 6)
    )
    attributes.connect(ankle_ctrl, 'rotate', ankle)
    attributes.connect(ankle_ctrl, 'scale', ankle)
    attributes.lock(ankle_ctrl, ['translate'])

    toe=naming.find('ballOfFoot', fk)
    toe_ctrl = controls.ellipse(
        'toe', Suffix.FK_CONTROL,
        joint=toe,
        parent=ankle_ctrl,
        normal=(0, 0, 1),
        size=(6, 4, 1)
    )
    attributes.connect(toe_ctrl, 'rotate', toe)
    attributes.connect(toe_ctrl, 'scale', ankle)
    attributes.lock(toe_ctrl, ['translate', 'rotateY', 'rotateZ'])

    attributes.delete_all(fk)
    return fk
    
def _create_ik(driver_joints, reverse_foot_drivers, control_grp, systems_grp, flipped):
    ik = joints.variants(driver_joints, Suffix.IK_JOINT, root_parent=systems_grp)

    hip = naming.find('hip', ik)
    knee = naming.find('knee', ik)
    ankle = naming.find('ankle', ik)
    ball = naming.find('ballOfFoot', ik)
    tip = naming.find('tipOfToe', ik)

    heel = naming.find('heel', reverse_foot_drivers)
    inner = naming.find('footBankInner', reverse_foot_drivers)
    outer = naming.find('footBankOuter', reverse_foot_drivers)

    handle = cmds.ikHandle(
        n=naming.replace(ankle, name=name, suffix=Suffix.IK_HANDLE), 
        sj=hip, 
        ee=ankle, 
        solver='ikRPsolver')[0]

    pole = controls.ik_pole(
        name,
        joint=knee,
        parent=control_grp,
        center_on_parent=True
    )
    cmds.poleVectorConstraint(pole, handle)

    foot_ctrl = controls.foot(
        'foot',
        ankle, heel, tip, inner, outer,
        parent=control_grp,
        flipped=flipped
    )
    cmds.parentConstraint(naming.root_control, foot_ctrl, mo=True)
    attributes.add(foot_ctrl, 'rollBack', 0, type_='float', keyable=True)
    attributes.set_range(foot_ctrl, 'rollBack', min_=0, max_=180)
    attributes.add(foot_ctrl, 'rollForward', 0, type_='float', keyable=True)
    attributes.set_range(foot_ctrl, 'rollForward', min_=0, max_=180)
    attributes.add(foot_ctrl, 'toeFlex', 30, type_='float', keyable=True)
    attributes.set_range(foot_ctrl, 'toeFlex', min_=0, max_=100)
    attributes.add(foot_ctrl, 'toeTap', 0, type_='float', keyable=True)
    attributes.set_range(foot_ctrl, 'toeTap', min_=-100, max_=100)
    attributes.add(foot_ctrl, 'bank', 0, type_='float', keyable=True)
    attributes.set_range(foot_ctrl, 'toeTap', min_=-100, max_=100)
    
    heel_piv = groups.empty_at(heel, 'heel', suffix='pivot', parent=foot_ctrl)
    outer_piv = groups.empty_at(outer, 'outer', suffix='pivot', parent=heel_piv)
    inner_piv = groups.empty_at(inner, 'inner', suffix='pivot', parent=outer_piv)
    tip_piv = groups.empty_at(tip, 'tip', suffix='pivot', parent=inner_piv)
    ball_piv = groups.empty_at(ball, 'ballOfFoot', suffix='pivot', parent=tip_piv)
    toe_piv = groups.empty_at(ball, 'toe', suffix='pivot', parent=ball_piv)

    cmds.parent(handle, ball_piv)

    rollBack_invert = nodes.subtract(naming.replace(ankle, name='footRollBack', suffix='invert'))
    attributes.set_(rollBack_invert, 'input1D[0]', 0)
    attributes.connect(foot_ctrl, 'rollBack', rollBack_invert, 'input1D[1]')
    attributes.connect(rollBack_invert, 'output1D', heel_piv, 'rotateX')

    bank_cond = nodes.switch(naming.replace(ankle, name='footBank', suffix='cond'))
    attributes.connect(foot_ctrl, 'bank', bank_cond, 'firstTerm')
    attributes.set_(bank_cond, 'colorIfFalse.colorIfFalseR', 0)
    attributes.connect(foot_ctrl, 'bank', bank_cond, 'colorIfFalse.colorIfFalseG')
    attributes.connect(foot_ctrl, 'bank', bank_cond, 'colorIfTrue.colorIfTrueR')
    if (flipped):
        attributes.connect(bank_cond, 'outColor.outColorG', inner_piv, 'rotateZ')
        attributes.connect(bank_cond, 'outColor.outColorR', outer_piv, 'rotateZ')
    else:
        attributes.connect(bank_cond, 'outColor.outColorR', inner_piv, 'rotateZ')
        attributes.connect(bank_cond, 'outColor.outColorG', outer_piv, 'rotateZ')

    roll_sub = nodes.subtract(naming.replace(ankle, name='footRoll', suffix='sub'))
    attributes.connect(foot_ctrl, 'rollForward', roll_sub, 'input1D[0]')
    attributes.connect(foot_ctrl, 'toeFlex', roll_sub, 'input1D[1]')
    roll_cond = nodes.switch(naming.replace(ankle, name='footRoll', suffix='cond'))
    attributes.connect(roll_sub, 'output1D', roll_cond, 'firstTerm')
    attributes.set_(roll_cond, 'colorIfFalse.colorIfFalseR', 0)
    attributes.connect(foot_ctrl, 'rollForward', roll_cond, 'colorIfFalse.colorIfFalseG')
    attributes.connect(roll_sub, 'output1D', roll_cond, 'colorIfTrue.colorIfTrueR')
    attributes.connect(foot_ctrl, 'toeFlex', roll_cond, 'colorIfTrue.colorIfTrueG')
    attributes.connect(roll_cond, 'outColor.outColorR', tip_piv, 'rotateX')
    attributes.connect(roll_cond, 'outColor.outColorG', ball_piv, 'rotateX')

    toe_sub = nodes.subtract(naming.replace(ankle, name='toeTap', suffix='sub'))
    attributes.connect(foot_ctrl, 'toeTap', toe_sub, 'input1D[0]')
    attributes.connect(roll_cond, 'outColor.outColorG', toe_sub, 'input1D[1]')
    attributes.connect(toe_sub, 'output1D', toe_piv, 'rotateX')

    handle = cmds.ikHandle(
        n=naming.replace(ankle, name='foot', suffix=Suffix.IK_HANDLE), 
        sj=ankle, 
        ee=ball, 
        solver='ikRPsolver')[0]
    cmds.parent(handle, ball_piv)
    cmds.makeIdentity(a=True, t=True, r=True, s=True)

    handle = cmds.ikHandle(
        n=naming.replace(ankle, name='toe', suffix=Suffix.IK_HANDLE), 
        sj=ball, 
        ee=tip, 
        solver='ikRPsolver')[0]
    cmds.parent(handle, toe_piv)
    cmds.makeIdentity(a=True, t=True, r=True, s=True)

    controls.set_rest_pose(handle)

    attributes.delete_all(ik)
    return ik

def _ik_switch(driver_joints, fk, ik, control_grp, flipped):
    ankle = naming.find('ankle', driver_joints)
    switch, invert = controls.ik_switch(
        name,
        ankle,
        offset = (2, 0, -0.5),
        parent = control_grp,
        flipped = flipped
    )
    attributes.set_(switch, naming.IK_SWITCH_ATTR, 1.0)

    for i in range(len(driver_joints)):
        orient = cmds.orientConstraint([fk[i], ik[i]], driver_joints[i])[0]
        attributes.connect(invert, 'output1D', orient, fk[i] + 'W0')
        attributes.connect(switch, naming.IK_SWITCH_ATTR, orient, ik[i] + 'W1')
        scale = cmds.scaleConstraint([fk[i], ik[i]], driver_joints[i])[0]
        attributes.connect(invert, 'output1D', scale, fk[i] + 'W0')
        attributes.connect(switch, naming.IK_SWITCH_ATTR, scale, ik[i] + 'W1')
    
    ankle_fk = naming.find('ankle', fk)
    ankle_ik = naming.find('ankle', ik)
    switch_parent = cmds.parentConstraint([ankle_fk, ankle_ik], switch, mo=True)[0]
    attributes.connect(invert, 'output1D', switch_parent, ankle_fk + 'W0')
    attributes.connect(switch, naming.IK_SWITCH_ATTR, switch_parent, ankle_ik + 'W1')
    