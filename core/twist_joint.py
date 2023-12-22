from collections import namedtuple
from typing import NamedTuple
from maya import mel, cmds
from maya.api import OpenMaya as om

from .maya_object import MayaAttribute, MayaDagObject
from .joint import Joint
from . import nodetree, groups

def swingTwist(target:'MayaDagObject'):
	"""Returns a swing and twist Euler (rotate order taken from target)"""
	reference:om.MQuaternion = om.MEulerRotation(*target.attr('twistRest').get_vec((0, 0, 0)), target.rotateOrder.get()).asQuaternion()
	reference_twist:om.MQuaternion = om.MQuaternion(reference.x, 0, 0, reference.w).normal()
	reference_swing = reference_twist.inverse() * reference
	
	rotation = nodetree.decomposeMatrix(
		nodetree.matMult(
			[
				target.worldMatrix.get() * target.parent().worldInverseMatrix.get(),
				target.offsetParentMatrix, 
				target.parent().worldMatrix.get() * target.worldInverseMatrix.get()
			], 
			owner=target
		), 
		rotateOrder=target.rotateOrder, 
		owner=target
	).outputQuat

	relative_rotation = nodetree.quatProd(rotation, reference.inverse(), owner=target)

	relative_twist = nodetree.quatNormalize(
		quatX=relative_rotation.obj.attr('outputQuatX'), 
		quatW=relative_rotation.obj.attr('outputQuatW'), 
		owner=target)
	
	relative_swing = nodetree.quatProd(
		nodetree.quatInvert(relative_twist, owner=target),
		relative_rotation,
		owner=target
	)

	swing = nodetree.quatProd(
		nodetree.quatProd(
			reference_twist.inverse(),
			relative_swing,
			owner=target
		),
		reference,
		owner=target
	)

	twist = nodetree.quatProd(
		reference_twist,
		relative_twist,
		owner=target
	)

	

	swing_euler = nodetree.quat2euler(
		swing,
		rotateOrder=target.rotateOrder,
		owner=target
	)

	twist_euler = nodetree.quat2euler(
		twist,
		rotateOrder=target.rotateOrder,
		owner=target
	)

	return (swing_euler, twist_euler)

def ballJointTwist(joint:Joint, systems_grp:MayaDagObject, parent:MayaDagObject, subdivisions=1):
	mel.eval('ik2Bsolver;')
	twist_grp = groups.new_at(joint, suffix='twistGrp', parent=systems_grp)
	nodetree.parentConstraint(joint.parent(), twist_grp)

	twist_root = joint.but_with(suffix='noTwistRaw')
	twist_tip = joint.but_with(suffix='twistRaw')
	cmds.duplicate(joint, n=twist_root, po=True)
	cmds.duplicate(joint.child(), n=twist_tip, po=True)
	cmds.parent(twist_root, twist_grp)
	cmds.parent(twist_tip, twist_root)

	swing, twist = swingTwist(joint)
	swing >> twist_root.rotate
	twist >> twist_tip.rotate

	twist_root.attr('displayLocalAxis').set(1)
	twist_tip.attr('displayLocalAxis').set(1)
	
	twist_step = nodetree.mult3D(twist, (1.0 / subdivisions, 0.0, 0.0), owner=joint)
	