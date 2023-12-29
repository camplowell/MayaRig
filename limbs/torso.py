from maya import cmds

from ..core import selection, controls, nodetree
from ..core.joint import Joint, JointCollection
from ..core.limb import Limb
from ..core.context import Character
from ..core.maya_object import Side, MayaDagObject, Suffix

def _mixLocalRots(pelvis_ctrl:MayaDagObject, middle_ctrl:MayaDagObject, shoulder_ctrl:MayaDagObject, blend:float):
    shoulder_rot = nodetree.eulerToQuat(shoulder_ctrl.rotate, shoulder_ctrl.rotateOrder, owner=shoulder_ctrl)
    pelvis_rot = nodetree.eulerToQuat(pelvis_ctrl.rotate, pelvis_ctrl.rotateOrder, owner=pelvis_ctrl)

    mid_rotOffset = nodetree.quatSlerp(blend, pelvis_rot, shoulder_rot, owner=middle_ctrl)

    mid_rotMat = nodetree.composeMatrix(inputQuat=mid_rotOffset, owner=middle_ctrl)

    mid_offsetParent = nodetree.matMult([mid_rotMat, middle_ctrl.offsetParentMatrix.get()], owner=middle_ctrl)

    mid_offsetParent >> middle_ctrl.offsetParentMatrix

class Forward(Limb):
    key='TorsoFK'
    displayName='Torso'
    @classmethod
    def generateMarkers(cls):
        selection.clear()
        cog = Joint.cog_marker((0, 0, 0))
        cls.mark_root(cog)

        pelvis = Joint.marker(Side.CENTER, 'Pelvis', (0, 0, 0), size=15)
        Joint.marker(Side.CENTER, 'PelvisNib', (0, -12, -4.5))
        selection.set(pelvis)
        
        spine0 = Joint.marker(Side.CENTER, 'Spine0', (0, 0, 0), size=12)
        spine0.addAttr('blend', 0.5, type_='float', keyable=False, min=0, max=1, niceName='Blend hip <--> shoulder')
        spine0.lockAttrs(['translate'])

        spine1 = Joint.marker(Side.CENTER, 'Spine1', (0, 8, 0), size=15)
        spine1.addAttr('blend', 0.8, type_='float', keyable=False, min=0, max=1, niceName='Blend middle <--> shoulder')

        Joint.marker(Side.CENTER, 'Spine2', (0, 16, -1), size=10)
        Joint.marker(Side.CENTER, 'SpineNib', (0, 32, -6))

        selection.set(cog)

    def _generate_controls(self, pose_joints: JointCollection):
        self._orient_joints(pose_joints)
        control_grp = self.control_group
        nodetree.parentConstraint(Character.cog_control, control_grp)

        cmds.makeIdentity(*pose_joints, jo=True) # Ensure spinal joints are aligned to the world
        pelvis_ctrl = self._make_pelvis_control(pose_joints)

        spine0 = pose_joints['Spine0']
        spine1 = pose_joints['Spine1']
        spine2 = pose_joints['Spine2']

        middle_ctrl:MayaDagObject = controls.circle(spine0, 'MiddleTorso', parent=control_grp, position=spine0.to_child(), axis=controls.Axis.Y)
        middle_ctrl.attr('rotateOrder').set('yzx')
        shoulder_ctrl:MayaDagObject = controls.saddle(spine1, 'UpperTorso', parent=control_grp, stretch=(1, -1, 1), axis=controls.Axis.Y, position=spine1.to_child() + (0.5 * spine2.to_child()))
        shoulder_ctrl.attr('rotateOrder').set('yzx')

        _mixLocalRots(pelvis_ctrl, middle_ctrl, shoulder_ctrl, spine0.attr('blend').get())

        controls.display_transform(spine0, middle_ctrl, self.systems_group)
        controls.display_transform(spine2, shoulder_ctrl, self.systems_group)

        cmds.orientConstraint(middle_ctrl, spine0)
        cmds.orientConstraint(middle_ctrl, spine1, w=1 - spine1.attr('blend').get())
        cmds.orientConstraint(shoulder_ctrl, spine1, w=spine1.attr('blend').get())
        cmds.orientConstraint(shoulder_ctrl, spine2)
        pelvis_ctrl.lockAttrs(['translate'])
        middle_ctrl.lockAttrs(['translate', 'scale'])
        shoulder_ctrl.lockAttrs(['translate', 'scale'])
    
    def _generate_bind_joints(self, pose_joints: JointCollection):
        to_bind = ['Pelvis', 'Spine0', 'Spine1', 'Spine2']
        bind_joints = Joint.variants([pose_joints[joint] for joint in to_bind], suffix=Suffix.BIND_JOINT, root_parent=Character.bind_grp)
        for joint in bind_joints:
            joint.unlockAttrs(['translate', 'rotate', 'scale'])

        for key in to_bind:
            cmds.parentConstraint(pose_joints[key], bind_joints[key])
        return JointCollection(bind_joints)
    
    def _cleanup(self, pose_joints: JointCollection, bind_joints: JointCollection):
        for joint in pose_joints:
            joint.clear_attributes()
        for joint in bind_joints:
            joint.clear_attributes()

    def _orient_joints(self, pose_joints:JointCollection):
        for joint in pose_joints:
            joint.orient_world()

    def _make_pelvis_control(self, pose_index:JointCollection):
        cog_bone = pose_index.pop('CoG')
        pelvis = pose_index['Pelvis']
        pelvis_nib = pose_index.pop('PelvisNib')
        spine0 = pose_index['Spine0']
        spine0.unlockAttrs(['translate'])

        cmds.parent(pelvis, cog_bone.parent())
        cog_children = cog_bone.children()
        if cog_children:
            cmds.parent(cog_children, pelvis)
        
        cog_bone.dissolve()

        pelvis_ctrl = controls.saddle(pelvis, 'Pelvis', parent=self.control_group, axis=controls.Axis.Y)
        pelvis_ctrl.attr('rotateOrder').set('yzx')

        nib_pos = pelvis_nib.position()
        pelvis_children = pelvis.children()
        if pelvis_children:
            cmds.parent(pelvis_children, w=True)
        cmds.move(*nib_pos, pelvis, r=False)
        if pelvis_children:
            cmds.parent(pelvis_children, pelvis, a=True)
        pelvis_nib.dissolve()
        nodetree.parentConstraint(pelvis_ctrl, pelvis)
        return pelvis_ctrl

class Simple(Limb):
    key='TorsoSimple'
    displayName='Torso'

    @classmethod
    def generateMarkers(cls):
        selection.clear()

        cog = Joint.cog_marker((0, 0, 0))
        cls.mark_root(cog)

        Joint.marker(Side.CENTER, 'Pelvis', (0, 0, 0), size=10)

        selection.set(cog)

    def _generate_controls(self, pose_joints: JointCollection):
        nodetree.parentConstraint(Character.cog_control, self.control_group)

        cmds.makeIdentity(*pose_joints, jo=True) # Ensure spinal joints are aligned to the world
        cog_bone = pose_joints.pop('CoG')
        pelvis = pose_joints['Pelvis']

        cmds.parent(pelvis, cog_bone.parent())
        cog_children = cog_bone.children()
        if cog_children:
            cmds.parent(cog_children, pelvis)
        
        cog_bone.dissolve()
        pelvis_ctrl = controls.saddle(pelvis, 'Pelvis', parent=self.control_group, axis=controls.Axis.Y)
        pelvis_ctrl.attr('rotateOrder').set('yzx')
        nodetree.parentConstraint(pelvis_ctrl, pelvis)

    def _generate_bind_joints(self, pose_joints: JointCollection) -> JointCollection:
        bind_joints = Joint.variants(pose_joints, suffix=Suffix.BIND_JOINT, root_parent=Character.bind_grp)
        if bind_joints[0].parent() == Character.pose_grp:
            cmds.parent(bind_joints[0], Character.bind_grp)
        cmds.parentConstraint(pose_joints[0], bind_joints[0])
        return bind_joints
    
    def _cleanup(self, pose_joints: JointCollection, bind_joints: JointCollection):
        for joint in pose_joints:
            joint.clear_attributes()
        for joint in bind_joints:
            joint.clear_attributes()