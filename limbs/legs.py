import math
from typing import List, Dict
from maya import cmds
import maya.api.OpenMaya as om
from maya import mel

from ..core.limb import Limb
from ..core.maya_object import MayaDagObject, MayaObject, Side, Suffix
from ..core.joint import Joint, JointCollection
from ..core import selection, controls, groups, twist_joint
from ..core.nodes import Nodes
from ..core.context import Character
from ..core.half_joint import half_joint

class HumanoidLeg(Limb):
    key = 'HumanoidLeg'
    displayName = 'Leg'

    @classmethod
    def generateMarkers(cls, * , side=Side.LEFT, symmetrical=True):
        hip = Joint.marker(Side.LEFT, 'Hip', (7, 80, 0), size=8)
        hip.addAttr('poleSize', 2, type_='float', keyable=False, min=0.0)
        hip.addAttr('twistRest', (0, 0, -45), type_='float3', keyable=False)
        Joint.marker(Side.LEFT, 'Knee', (7, 45, 1), size=7)
        ankle = Joint.marker(Side.LEFT, 'Ankle', (7, 10, -1), size=5)
        ankle.addAttr('footControlOutset', 2, type_='float', keyable=False)
        Joint.marker(Side.LEFT, 'Heel', (7, 0, -9))
        selection.set(ankle)
        Joint.marker(Side.LEFT, 'BallOfFoot', (7, 1.5, 8), size=5)
        Joint.marker(Side.LEFT, 'TipOfToe', (7, 1, 16))
        selection.set(ankle)
        Joint.marker(Side.LEFT, 'FootBankInner', (4, 0, 9), type_='Inner')
        selection.set(ankle)
        Joint.marker(Side.LEFT, 'FootBankOuter', (14, 0, 7), type_='Outer')

        if side == Side.RIGHT:
            hip_r = hip.mirror()
            cmds.delete(hip)
            hip = hip_r
        cls.mark_root(hip, symmetrical=symmetrical)
        selection.set(hip)

    def _generate_controls(self, pose_joints: JointCollection):
        self._orient_joints(pose_joints)
        core_joints = JointCollection([pose_joints['Hip'], pose_joints['Knee'], pose_joints['Ankle'], pose_joints['BallOfFoot'], pose_joints['TipOfToe']])
        
        
        ik_switch = controls.fkIkSwitch(pose_joints['Ankle'], name='Leg', parent=self.control_group, position=(10, 5, 0), size=5, default=1)
        fk = self._generate_fk(pose_joints, core_joints, ik_switch)
        ik = self._generate_ik(pose_joints, core_joints, ik_switch)

        self._ik_switch(core_joints, fk, ik, ik_switch)
    
    def _generate_bind_joints(self, pose_joints: JointCollection) -> JointCollection:
        to_bind = [pose_joints['Hip'], pose_joints['Knee'], pose_joints['Ankle'], pose_joints['BallOfFoot']]
        bind_joints = Joint.variants(to_bind, suffix=Suffix.BIND_JOINT, root_parent=Character.bind_grp)
        generated = JointCollection([])
        if bind_joints[0].parent() == Character.pose_grp:
            cmds.parent(bind_joints[0], Character.bind_grp)
        for index, pose_joint in enumerate(to_bind):
            if pose_joint.joint_type() == 'Hip':
                generated.extend(twist_joint.ballJointTwist(pose_joint, bind_joints[index], self.systems_group, 2))
                generated.extend([half_joint(bind_joints[index], self.systems_group)])
            elif pose_joint.joint_type() == 'Knee':
                generated.extend([half_joint(bind_joints[index], self.systems_group)])
            else:
                cmds.parentConstraint(pose_joint, bind_joints[index])
        bind_joints.extend(generated)
        return bind_joints
    
    def _cleanup(self, pose_joints: JointCollection, bind_joints: JointCollection):
        pose_joints.pop('Heel').dissolve()
        pose_joints.pop('Inner').dissolve()
        pose_joints.pop('Outer').dissolve()
        for joint in pose_joints:
            joint.clear_attributes(keep=[])
        for joint in bind_joints:
            joint.clear_attributes(keep=[])
    
    def _orient_joints(self, joints:JointCollection):
        joints['Hip'].orient(secondaryAxis='zdown')
        joints['Knee'].orient_to(joints['Knee'].normal(), secondaryAxis='zdown')
        joints['Ankle'].orient_world()
        joints['BallOfFoot'].orient_world()


    def _generate_fk(self, pose, core_joints, ik_switch):
        fk_pose = Joint.variants(core_joints, suffix=Suffix.FK_JOINT, root_parent=self.systems_group, clear_attributes=True)

        hip_ctrl = controls.circle(
            pose['Hip'],
            'UpperLeg', suffix=Suffix.FK_CONTROL,
            parent=self.control_group,
            position=0.5 * pose['Hip'].to_child()
        )
        Nodes.Structures.spaceSwitch([Character.cog_control], hip_ctrl, controller=hip_ctrl, options=['hip', 'CoG'], rotate=True)
        Nodes.Structures.parentConstraint(hip_ctrl, fk_pose['Hip'])
        hip_ctrl.lockAttrs(['translate'])
        ik_switch.attr('fk') >> hip_ctrl.visibility

        knee_ctrl = controls.circle(
            pose['Knee'],
            'LowerLeg', suffix=Suffix.FK_CONTROL,
            parent=hip_ctrl,
            position = 0.33 * pose['Knee'].to_child()
        )
        Nodes.Structures.parentConstraint(knee_ctrl, fk_pose['Knee'])
        knee_ctrl.lockAttrs(['translate', 'rotateX', 'rotateY'])
        ik_switch.attr('fk') >> knee_ctrl.visibility

        ankle_ctrl = controls.circle(
            pose['Ankle'],
            'Ankle', suffix=Suffix.FK_CONTROL,
            parent=knee_ctrl,
            axis=controls.Axis.Y
        )
        ik_switch.attr('fk') >> ankle_ctrl.visibility
        Nodes.Structures.parentConstraint(ankle_ctrl, fk_pose['Ankle'])
        ankle_ctrl.lockAttrs(['translate'])

        toe_ctrl = controls.circle(
            pose['BallOfFoot'],
            'Toe', suffix=Suffix.FK_CONTROL,
            parent=ankle_ctrl,
            axis=controls.Axis.Z
        )
        Nodes.Structures.parentConstraint(toe_ctrl, fk_pose['BallOfFoot'])
        toe_ctrl.lockAttrs(['translate', 'rotateY', 'rotateZ'])
        ik_switch.attr('fk') >> toe_ctrl.visibility

        return fk_pose

    def _generate_ik(self, pose:Dict[str, Joint], core_joints, ik_switch:MayaDagObject):
        mel.eval('ik2Bsolver;')
        ik_pose = Joint.variants(core_joints, suffix=Suffix.IK_JOINT, root_parent=self.systems_group, clear_attributes=True)

        legOff:om.MVector = (ik_pose['Ankle'].position() - ik_pose['Hip'].position())
        legDir:om.MVector = legOff.normal()
        kneeDir:om.MVector = (ik_pose['Knee'].position() - ik_pose['Hip'].position()).normalize()
        offsetDir:om.MVector = (kneeDir - legDir * (kneeDir * legDir)).normalize()
        pole = controls.octahedron(
            pose['Hip'],
            self.key, suffix='ikPole',
            parent=self.control_group,
            position=pose['Hip'].position() + offsetDir * legOff.length(),
            radius=pose['Hip'].attr('poleSize').get_float(),
            relative=False
        )
        ik_switch.attr('ik') >> pole.visibility
        pole.addAttr('automation', value=1.0, type_='float', min=0, max=1, keyable=True)
        pole.addAttr('followFoot', value=1.0, type_='float', min=0, max=1, keyable=True)
        pole.addAttr('twist', value=0.0, type_='float', min=-180, max=180, keyable=True)
        pole.lockAttrs(['rotate', 'scale'])
        pole.attr('showManipDefault').set(1) # Translate

        handle = MayaDagObject(cmds.ikHandle(
            n=self.control_group.but_with(suffix='ikHandle'),
            sj=ik_pose['Hip'],
            ee=ik_pose['Ankle'],
            sol='ik2Bsolver'
        )[0])
        cmds.poleVectorConstraint(pole, handle)

        foot_ctrl = _foot_ctrl(pose, parent=self.control_group)
        ik_switch.attr('ik') >> foot_ctrl.visibility
        Nodes.Structures.parentConstraint(Character.layout_control, foot_ctrl)
        
        pole_orient_hip = groups.new_at(self.control_group, parent=self.systems_group, name='LegPole', suffix='followHip')
        cmds.aimConstraint(foot_ctrl, pole_orient_hip, aim=(0, -1, 0), wut='objectrotation', u=(1, 0, 0), wu=(1, 0, 0), wuo=pose['Hip'].parent())

        pole_orient_foot = groups.new_at(self.control_group, parent=pole_orient_hip, name='LegPole', suffix='followFoot')
        cmds.aimConstraint(foot_ctrl, pole_orient_foot, aim=(0, -1, 0), wut='objectrotation', u=(1, 0, 0), wu=(1, 0, 0), wuo=foot_ctrl)

        pole_auto = groups.new_at(self.control_group, parent=pole_orient_hip, name='LegPole', suffix='automation')
        pole_orient_blend = Nodes.blendMatrix(owner=pole_auto)
        pole_orient_blend.inputMatrix.set(pole_auto.offsetParentMatrix.get())
        Nodes.Structures.parentConstraint(pole_orient_hip, pole_auto, connect=False) >> pole_orient_blend.target[0].targetMatrix
        Nodes.Structures.parentConstraint(pole_orient_foot, pole_auto, connect=False) >> pole_orient_blend.target[1].targetMatrix

        pole.attr('followFoot') >> pole_orient_blend.target[1].weight
        follow_hip = Nodes.invert(owner = pole)
        pole.attr('followFoot') >> follow_hip.inputX
        follow_hip.outputX >> pole_orient_blend.target[0].weight

        pole_orient_blend.outputMatrix >> pole_auto.offsetParentMatrix

        pole.attr('twist') >> pole_auto.attr('rotateY')

        Nodes.Structures.compositeParent(pole_auto, Character.layout_control, pole)

        heel_piv = groups.new_at(pose['Heel'], suffix='pivot', parent=self.systems_group)
        Nodes.Structures.parentConstraint(foot_ctrl, heel_piv)
        outer_piv = groups.new_at(pose['Outer'], suffix='pivot', parent=heel_piv)
        inner_piv = groups.new_at(pose['Inner'], suffix='pivot', parent=outer_piv)
        ball_floor_piv = groups.new_at(pose['BallOfFoot'], suffix='floorPivot', parent=inner_piv, offset=(0, -pose['BallOfFoot'].position().y, 0))
        tip_piv = groups.new_at(pose['TipOfToe'], suffix='pivot', parent=ball_floor_piv)
        tap_piv = groups.new_at(pose['BallOfFoot'], suffix='tap', parent=tip_piv)
        flex_piv = groups.new_at(pose['BallOfFoot'], suffix='pivot', parent=tap_piv)

        cmds.parent(handle, flex_piv)

        foot_ctrl.addAttr('bank', value=0, min=-90, max=90, type_='float')
        foot_ctrl.addAttr('roll', value=0, min=-90, max=180, type_='float')
        foot_ctrl.addAttr('toeFlex', value=30, min=0, max=100, type_='float')
        foot_ctrl.addAttr('toeTap', value=0, min=-90, max=90, type_='float')

        rollBack_invert = Nodes.min(owner=foot_ctrl, suffix='rollBack')
        rollBack_invert.floatA.set(0)
        foot_ctrl.attr('roll') >> rollBack_invert.floatB
        rollBack_invert.outFloat >> heel_piv.attr('rotateX')

        bank_selector = Nodes.switch(owner=foot_ctrl, name='FootBank')
        foot_ctrl.attr('bank') >> bank_selector.firstTerm

        bank_selector.attr('colorIfTrueG').set(0)
        foot_ctrl.attr('bank') >> bank_selector.attr('colorIfFalseG')
        foot_ctrl.attr('bank') >> bank_selector.attr('colorIfTrueR')

        if foot_ctrl.side == Side.LEFT:
            bank_selector.attr('outColorR') >> inner_piv.attr('rotateZ')
            bank_selector.attr('outColorG') >> outer_piv.attr('rotateZ')
        else:
            bank_selector.attr('outColorR') >> outer_piv.attr('rotateZ')
            bank_selector.attr('outColorG') >> inner_piv.attr('rotateZ')

        # Calculate the preroll of the foot
        preroll = Nodes.min(owner=ball_floor_piv, suffix='preroll')
        preroll.floatA.set(90 - math.degrees(math.acos(ball_floor_piv.offset_to(pose['TipOfToe']).normal().y)))
        rollForward = Nodes.max(owner=foot_ctrl, suffix='rollForward')
        rollForward.floatA.set(0)
        foot_ctrl.attr('roll') >> rollForward.floatB
        rollForward.outFloat >> preroll.floatB
        
        # Calculate the flex of the foot
        desired_flex = Nodes.subtract(owner=foot_ctrl, suffix='desiredFlex')
        rollForward.outFloat >> desired_flex.input1D[0]
        preroll.outFloat >> desired_flex.input1D[1]

        flex = Nodes.min(owner=foot_ctrl, suffix='flex')
        desired_flex.output1D >> flex.floatA
        foot_ctrl.attr('toeFlex') >> flex.floatB

        # Calculate the overflow to rotate at the toe tip
        overflow = Nodes.subtract(owner=foot_ctrl, suffix='overflow')
        rollForward.outFloat >> overflow.input1D[0]
        preroll.outFloat >> overflow.input1D[1]
        flex.outFloat >> overflow.input1D[2]

        # Apply to the offset groups
        foot_ctrl.attr('toeTap') >> tap_piv.attr('rotateX')
        preroll.outFloat >> ball_floor_piv.attr('rotateX')
        overflow.output1D >> tip_piv.attr('rotateX')
        tap_comp = Nodes.subtract(owner=flex_piv)
        flex.outFloat >> tap_comp.input1D[0]
        foot_ctrl.attr('toeTap') >> tap_comp.input1D[1]
        tap_comp.output1D >> flex_piv.attr('rotateX')

        foot_handle = MayaDagObject(cmds.ikHandle(
            n=ik_pose['Ankle'].but_with(suffix='ikHandle'),
            sj=ik_pose['Ankle'],
            ee=ik_pose['BallOfFoot'],
            sol='ikSCsolver'
        )[0])
        cmds.parent(foot_handle, flex_piv)
        toe_handle = MayaDagObject(cmds.ikHandle(
            n=ik_pose['BallOfFoot'].but_with(name='Toe', suffix='ikHandle'),
            sj=ik_pose['BallOfFoot'],
            ee=ik_pose['TipOfToe'],
            sol='ikSCsolver'
        )[0])
        cmds.parent(toe_handle, tap_piv)

        return ik_pose

    def _ik_switch(self, pose, fk_index, ik_index, ik_switch:MayaDagObject):
        Nodes.Structures.compositeParent(pose['Ankle'], Character.layout_control, ik_switch)

        for key, pose_joints in pose.items():
            Nodes.Structures.spaceSwitch(
                [fk_index[key], ik_index[key]],
                pose_joints[0],
                attr=ik_switch.attr('ik'),
                includeParent=False
            )


def _foot_ctrl(pose:JointCollection, parent:MayaDagObject):
    outset = pose['Ankle'].attr('footControlOutset').get_float()
    ankle_pos = pose['Ankle'].position()
    min_x = min(pose['Inner'].position().x, pose['Outer'].position().x) - outset
    max_x = max(pose['Inner'].position().x, pose['Outer'].position().x) + outset
    min_z = min(pose['Heel'].position().z, pose['TipOfToe'].position().z) - outset
    max_z = max(pose['Heel'].position().z, pose['TipOfToe'].position().z) + outset

    ankle_ctrl = MayaDagObject(pose['Ankle'].but_with(name='Foot', suffix=Suffix.CONTROL).resolve_collisions())
    cmds.curve(n=ankle_ctrl, d=1, p=[
        om.MVector(min_x, 0, min_z) - ankle_pos,
        om.MVector(max_x, 0, min_z) - ankle_pos,
        om.MVector(max_x, 0, max_z) - ankle_pos,
        om.MVector(min_x, 0, max_z) - ankle_pos,
        om.MVector(min_x, 0, min_z) - ankle_pos
    ])

    return controls.place_ctrl(ankle_ctrl, pose['Ankle'], parent=parent)