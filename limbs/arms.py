

from maya import mel

from ..core import groups, selection, controls
from ..core.limb import Limb
from ..core.maya_object import *
from ..core.joint import Joint, JointCollection
from ..core.nodes import Nodes
from ..core.context import Character

class HumanoidArm(Limb):
    key='ArmHumanoid'
    displayName='Arm'

    @classmethod
    def generateMarkers(cls, * , has_clavicle=True, side=Side.LEFT, symmetrical=True):
        selection.clear()
        root = None
        if has_clavicle:
            clavicle = Joint.marker(Side.LEFT, 'Clavicle', (2, 0, 2), size=10)
            root = clavicle
        shoulder = Joint.marker(Side.LEFT, 'Shoulder', (13, -1, -3.5), size=6)
        if not has_clavicle:
            root = shoulder
        
        elbow = Joint.marker(Side.LEFT, 'Elbow', (31, -1, -4.5), size=5)
        elbow.addAttr('poleSize', 2, type_='float', keyable=False, min=0)
        wrist = Joint.marker(Side.LEFT, 'Wrist', (52, -1, -2.5), size=5)

        start_z = 0.5
        cls._finger_markers('Pointer', (53.0, -1.0, -0.6), 59.4, start_z, length=9.3)
        selection.set(wrist)
        start_z -= 2.3
        cls._finger_markers('Middle', (53.5, -1.0, -2.2), 59.8, start_z, length=9.7)
        selection.set(wrist)
        start_z -= 2.3
        cls._finger_markers('Ring', (53.5, -1.2, -3.8), 59.5, start_z, length=9.0)
        selection.set(wrist)
        start_z -= 2.3
        pinky = cls._finger_markers('Pinky', (53.0, -1.6, -5.4), 59.2, start_z, length=8.0)
        pinky[0].addAttr('controlSize', 1.2, type_='float', min=0)

        selection.set(wrist)
        Joint.marker(Side.LEFT, 'Thumb', (52, -0.8, -0.2), size=2, type_='Knuckle')
        Joint.marker(Side.LEFT, 'Thumb2', (52, -4.9,-0.1), size=2, type_='Finger')
        Joint.marker(Side.LEFT, 'Thumb3', (52, -7.0,-0.1), size=2, type_='Finger')
        Joint.marker(Side.LEFT, 'ThumbTip', (52, -9.0,-0.2), size=2, type_='FingerTip')

        if side == Side.RIGHT:
            root_r = root.mirror()
            cmds.delete(root)
            root = root_r
        cls.mark_root(root, symmetrical=symmetrical)
        selection.set(root)

    def _generate_controls(self, pose_joints: JointCollection):
        self._orient_joints(pose_joints)
        if 'Clavicle' in pose_joints:
            clavicle = _clavicle_control(pose_joints['Clavicle'], 'Shoulder', parent=self.control_group)
            cmds.parentConstraint(clavicle, pose_joints['Clavicle'])
            
        ik_switch = controls.fkIkSwitch(pose_joints['Wrist'], name='Arm', parent=self.control_group, position=(0, 5, -10), size=5, default=0)
        core_joints = JointCollection([pose_joints['Shoulder'], pose_joints['Elbow'], pose_joints['Wrist']])
        fk = self._generate_fk(core_joints, ik_switch, clavicle if 'Clavicle' in pose_joints else self.control_group)
        ik = self._generate_ik(core_joints, ik_switch)
        self._ik_switch(core_joints, fk, ik, ik_switch)
        self._hand_controls(pose_joints)

    def _generate_bind_joints(self, pose_joints: JointCollection) -> JointCollection:
        bind_joints:JointCollection = Joint.variants(pose_joints, suffix=Suffix.BIND_JOINT)

        for i, joint in enumerate(bind_joints):
            if joint.joint_type() == 'FingerTip':
                joint.dissolve()
            else:
                cmds.parentConstraint(pose_joints[i], joint)

        return bind_joints
    
    def _cleanup(self, pose_joints: JointCollection, bind_joints: JointCollection):
        return super()._cleanup(pose_joints, bind_joints)

    @classmethod
    def _finger_markers(cls, finger, metacarpal_pos, start_x, start_z, length):
        start_y = metacarpal_pos[1]
        return [
            Joint.marker(Side.LEFT, '{}CMC'.format(finger), metacarpal_pos, type_='Metacarpal'),
            Joint.marker(Side.LEFT, '{}'.format(finger),    (start_x + 0.00 * length, start_y - 0.0,  start_z), size=1.2, type_='Knuckle'),
            Joint.marker(Side.LEFT, '{}2'.format(finger),   (start_x + 0.50 * length, start_y - 0.0,  start_z), size=1.2, type_='Finger'),
            Joint.marker(Side.LEFT, '{}3'.format(finger),   (start_x + 0.75 * length, start_y - 0.1,  start_z), size=1.2, type_='Finger'),
            Joint.marker(Side.LEFT, '{}Tip'.format(finger), (start_x + 1.00 * length, start_y - 0.2,  start_z), size=1.2, type_='FingerTip')
        ]

    def _orient_joints(self, pose_joints:JointCollection):
        if 'Clavicle' in pose_joints:
            pose_joints['Clavicle'].orient()
        pose_joints['Shoulder'].orient()
        pose_joints['Elbow'].orient_to(pose_joints['Elbow'].normal())
        
        
        for metacarpal in pose_joints['Metacarpal']:
            metacarpal.orient_match(pose_joints['Wrist'])
        for knuckle in pose_joints['Knuckle']:
            fingerJoints = [Joint(joint) for joint in knuckle.descendants(type_='joint')]
            fingerJoints.reverse()
            if 'Thumb' in knuckle: # Preserve thumb orientation
                normal = -knuckle.normal(after=fingerJoints[-1])
                cmds.parent(fingerJoints[0], w=True)
                mult = -1 if knuckle.side == Side.RIGHT else 1
                temp_constraint = cmds.aimConstraint(fingerJoints[0], knuckle, wu=mult * normal)
                cmds.aimConstraint(pose_joints['Knuckle'][0], knuckle, wu=mult * normal)
                cmds.delete(temp_constraint)
                cmds.makeIdentity(knuckle, a=True, t=False, r=True, s=True)
                cmds.joint(knuckle, e=True, zso=True)
                cmds.parent(fingerJoints[0], knuckle)
                if knuckle.side == Side.RIGHT:
                    knuckle.flip_joint_orient()
            else:
                knuckle.orient_match(pose_joints['Wrist'], twist=-90)
            for joint in fingerJoints:
                if joint.child():
                    joint.orient_match(knuckle)
        

    def _generate_fk(self, pose_joints:JointCollection, ik_switch:MayaObject, shoulder_parent:MayaObject):
        fk = Joint.variants(pose_joints, Suffix.FK_JOINT, root_parent=self.systems_group)
        upper_fk = controls.circle(
            fk['Shoulder'],
            'UpperArm', suffix=Suffix.FK_CONTROL,
            parent=shoulder_parent
        )
        upper_fk.rotateOrder.set(MayaObject.ROTATE_ORDER['xyz'])
        Nodes.Structures.spaceSwitch([Character.cog_control, Character.layout_control], upper_fk, options=['Shoulders', 'CoG', 'Layout'], defaultValue=1, rotate=True)
        Nodes.Structures.parentConstraint(upper_fk, fk['Shoulder'])
        ik_switch.attr('fk') >> upper_fk.visibility
        upper_fk.lockAttrs(['translate'])

        forearm_fk = controls.circle(
            fk['Elbow'],
            'Forearm', suffix=Suffix.FK_CONTROL,
            parent=upper_fk
        )
        Nodes.Structures.parentConstraint(forearm_fk, fk['Elbow'])
        ik_switch.attr('fk') >> forearm_fk.visibility
        forearm_fk.lockAttrs(['translate', 'rotateX', 'rotateZ'])

        wrist_fk = controls.circle(
            fk['Wrist'],
            'Wrist', suffix=Suffix.FK_CONTROL,
            parent=forearm_fk
        )
        upper_fk.rotateOrder.set(MayaObject.ROTATE_ORDER['yzx'])
        Nodes.Structures.parentConstraint(wrist_fk, fk['Wrist'])
        ik_switch.attr('fk') >> wrist_fk.visibility
        wrist_fk.lockAttrs(['translate'])

        return fk
    
    def _generate_ik(self, pose:JointCollection, ik_switch:MayaObject):
        ik = Joint.variants(pose, Suffix.IK_JOINT, root_parent=self.systems_group)
        Nodes.Structures.parentConstraint(pose[0].parent(), ik[0])
        mel.eval('ik2Bsolver;')

        armOff:om.MVector = (ik['Wrist'].position() - ik['Shoulder'].position())
        armDir:om.MVector = armOff.normal()
        elbowDir:om.MVector = (ik['Elbow'].position() - ik['Shoulder'].position()).normalize()
        offsetDir:om.MVector = (elbowDir - armDir * (elbowDir * armDir)).normalize()
        pole = controls.octahedron(
            pose['Elbow'],
            self.key, suffix='ikPole',
            parent=self.control_group,
            position=pose['Elbow'].position() + offsetDir * armOff.length(),
            radius=pose['Elbow'].attr('poleSize').get_float(2),
            relative=False
        )
        Nodes.Structures.spaceSwitch([Character.cog_control, Character.layout_control], pole, options=['Shoulders', 'CoG', 'Layout'], translate=True, lock_rot=Character.layout_control)
        ik_switch.attr('ik') >> pole.visibility
        pole.lockAttrs(['rotate', 'scale'])
        pole.attr('showManipDefault').set(1) # Translate

        handle = MayaObject(cmds.ikHandle(
            n=self.control_group.but_with(suffix='ikHandle'),
            sj=ik['Shoulder'],
            ee=ik['Wrist'],
            sol='ik2Bsolver'
        )[0])
        cmds.parent(handle, self.systems_group)
        cmds.poleVectorConstraint(pole, handle)

        ik_wrist = controls.square(
            pose['Wrist'],
            'Hand', suffix=Suffix.IK_CONTROL,
            parent=self.control_group,
            position=pose['Wrist'].position(),
            relative=False
        )
        ik_wrist.rotateOrder.set(MayaObject.ROTATE_ORDER['yzx'])
        ik_switch.attr('ik') >> ik_wrist.visibility
        Nodes.Structures.spaceSwitch([Character.cog_control, Character.layout_control], ik_wrist, options=['Shoulders', 'CoG', 'Layout'], defaultValue=1)
        Nodes.Structures.parentConstraint(ik_wrist, handle)
        cmds.orientConstraint(ik_wrist, ik['Wrist'], mo=True)
        return ik
    
    def _ik_switch(self, pose:JointCollection, fk:JointCollection, ik:JointCollection, switch:MayaObject):
        Nodes.Structures.compositeParent(pose['Wrist'], Character.layout_control, switch)

        for key, pose_joints in pose.items():
            Nodes.Structures.spaceSwitch(
                [fk[key], ik[key]],
                pose_joints[0],
                attr=switch.attr('ik'),
                includeParent=False
            )
    
    def _hand_controls(self, pose:JointCollection):
        hand_grp = groups.new_at(pose['Wrist'], parent=self.control_group, suffix=Suffix.OFFSET_GROUP)
        Nodes.Structures.parentConstraint(pose['Wrist'], hand_grp)
        if len(pose['Metacarpal']) > 2:
            curl = pose['Metacarpal'][-1]
            curl_control = controls.square(
                curl, 
                'HandCurl', 
                parent=hand_grp, 
                axis=controls.Axis.Z, 
                position= 0.5 * curl.to_child() + om.MVector(0, 0, -1.5 * curl.control_size()),
                stretch= (0.5 * curl.to_child().length() / curl.control_size(), 0, 1)
            )
            for i, metacarpal in enumerate(pose['Metacarpal'][2:]):
                fac = (i + 1)  / (len(pose['Metacarpal']) - 2)
                fac *= fac
                falloff = Nodes.multiply(owner=metacarpal)
                falloff.input1X.set(fac)
                curl_control.attr('rotateZ') >> falloff.input2X
                falloff.outputX >> metacarpal.attr('rotateZ')
        for knuckle in pose['Knuckle']:
            finger_joints = [Joint(joint) for joint in knuckle.descendants(type_='joint')[1:]]
            finger_joints.append(knuckle)
            finger_joints.reverse()

            finger_name = knuckle.name
            root_ctrl = controls.pointer(
                knuckle,
                finger_name,
                parent= hand_grp,
                tangent=(0,0,1)
            )
            Nodes.Structures.parentConstraint(knuckle.parent(), root_ctrl)
            root_ctrl.lockAttrs(['translate'])
            if 'Thumb' in knuckle:
                root_ctrl.addAttr('bendRate', 0.75, type_='float', min=0)
                bend_fac = Nodes.multiply(owner=root_ctrl)
                root_ctrl.attr('rotateY') >> bend_fac.input1X
                root_ctrl.attr('bendRate') >> bend_fac.input2X
                fingerBend = Nodes.composeMatrix(owner=root_ctrl, suffix='bend')
                bend_fac.outputX >> fingerBend.attr('inputRotateY')
            else:
                fingerBend = Nodes.composeMatrix(owner=root_ctrl, suffix='bend')
                root_ctrl.attr('rotateY') >> fingerBend.attr('inputRotateY')
            prev = root_ctrl
            for joint in finger_joints:
                ctrl = controls.circle(
                    joint,
                    joint.name,
                    parent=prev
                )
                ctrl.lockAttrs(['translate', 'rotateX', 'rotateZ'])
                if prev != root_ctrl:
                    ctrl_parentOffset = Nodes.matMult(owner=ctrl, suffix='offset')
                    fingerBend.outputMatrix >> ctrl_parentOffset.matrixIn[0]
                    ctrl_parentOffset.matrixIn[1].set(ctrl.offsetParentMatrix.get())
                    ctrl_parentOffset.matrixSum >> ctrl.offsetParentMatrix
                Nodes.Structures.parentConstraint(ctrl, joint)
                prev = ctrl

def _clavicle_control(ref:Joint, name: str, parent:MayaObject, suffix=Suffix.CONTROL, onCollision=CollisionBehavior.INCREMENT):
    ctrl = MayaObject(ref.but_with(name=name, suffix=suffix)).resolve_collisions(onCollision)
    radius = ref.control_size()
    to_child = ref.to_child()

    arc0 = cmds.circle(n='temp#', r=radius, nr=(1, 0, 0), sw=90)[0]
    arc1 = cmds.duplicate(arc0)[0]
    x0 = 0.5 * to_child.x
    x1 = 0.75 * to_child.x
    cmds.move(x0, 0, 0, arc0)
    cmds.move(x1, 0, 0, arc1)
    line0 = cmds.curve(n='temp#', d=1, p=[(x0, radius, 0), (x1, radius, 0)])
    line1 = cmds.curve(n='temp#', d=1, p=[(x0, 0, radius), (x1, 0, radius)])
    controls.combine_curves([arc0, arc1, line0, line1], ctrl)
    cmds.rotate(-45, 0, 0, ctrl)
    cmds.move(0, max(0, to_child.y), to_child.z, ctrl)
    cmds.move(0, 0, 0, ctrl.attr('rotatePivot'), ctrl.attr('scalePivot'), r=False)
    cmds.makeIdentity(a=True)
    ctrl.rotateOrder.set(5)
    rot = -om.MVector(ref.attr('jointOrient').get())
    cmds.rotate(*rot, ctrl)
    cmds.makeIdentity(a=True)
    ctrl.rotateOrder.set(0)
    return controls.place_ctrl(ctrl, ref, parent=parent)