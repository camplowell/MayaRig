from maya import cmds

from .joint import Joint
from .maya_object import MayaDagObject, MayaObject

def half_joint(joint:Joint, systems_grp:MayaDagObject):
	ref_pose = joint.duplicate(suffix='restPose', parent=systems_grp)
	half_joint = joint.duplicate(name=joint.name + 'Half')
	half_joint.radius.set(half_joint.radius.get() * 1.5)
	constraint = MayaObject(cmds.orientConstraint(ref_pose, half_joint, w=0.5)[0])
	cmds.orientConstraint(joint, half_joint, w=0.5)
	constraint.attr('interpType').set(2)
	return half_joint
	