from typing import List

from .core import groups, controls
from .core.maya_object import Suffix
from .core.context import Character
from .core.joint import Joint, JointCollection
from .core.limb import Limb

from maya import cmds

def prepare():
    Character.initialize()

def build():
    groups.create_output()
    _create_pose_joints()
    _generate_rig()

def _generate_rig():
    Character.layout_control = controls.circle_with_arows(Character.controls_grp, 'Layout', Character.controls_grp, axis=controls.Axis.Y, radius=Character.layout_size())
    pose_joints = JointCollection([Joint(obj) for obj in Character.pose_grp.descendants(type_='joint')])
    if 'CoG' in pose_joints:
        Character.cog_control = controls.circle_with_arows(pose_joints['CoG'], 'CenterOfGravity', Character.layout_control, axis=controls.Axis.Y)
    else:
        Character.cog_control = Character.layout_control
    roots = [joint for joint in pose_joints if joint.is_root()]
    roots.reverse()
    for root in roots:
        cmds.reorder(root, b=True)
    for root in roots:
        chain = root.chain()
        Limb.generators()[chain[0].generator()].buildRig(chain)

def _create_pose_joints():
    markers = [Joint(obj) for obj in Character.marker_grp.descendants(type_='joint')]
    roots = [joint for joint in markers if joint.is_root()]
    roots.reverse()
    for marker_root in roots:
        if marker_root.but_with(suffix=Suffix.POSE_JOINT).exists():
            continue
        pose_chain = Joint.variants(marker_root.chain(), suffix=Suffix.POSE_JOINT)
        cmds.makeIdentity(list(pose_chain), a=True, r=True, s=True)
        if pose_chain[0].parent() == Character.marker_grp:
            cmds.parent(pose_chain[0], Character.pose_grp)
        if marker_root.is_symmetrical():
            pose_chain[0].mirror()

def bind():
    print('Got command to bind!')