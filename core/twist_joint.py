from . import selection
from .context import Character
from maya import cmds
from maya.api import OpenMaya as om

from .maya_object import CollisionBehavior, MayaAttribute, MayaDagObject, Suffix
from .joint import Joint, JointCollection
from . import nodetree, groups

def swingTwist(target:'MayaDagObject'):
	"""Returns a swing and twist Euler (rotate order taken from target)"""
	reference:om.MQuaternion = om.MEulerRotation(*target.attr('twistRest').get_vec((0, 0, 0)), target.rotateOrder.get()).asQuaternion()
	reference_twist:om.MQuaternion = om.MQuaternion(reference.x, 0, 0, reference.w).normal()
	
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

def _createTwistSubdivisions(joint:Joint, swing_joint:MayaDagObject, twist_joint:MayaDagObject, subdivisions=1) -> JointCollection:
	bind_joints = JointCollection([])

	step = joint.child().translate_.get_vec() * (1.0 / (subdivisions + 1))
	selection.set(joint.but_with(suffix=Suffix.BIND_JOINT))
	for i in range(subdivisions + 1):
		t = i / (subdivisions + 1)
		step_joint = joint.but_with(name='{}Twist'.format(joint.name), suffix=Suffix.BIND_JOINT).resolve_collisions()
		cmds.joint(n=step_joint, p=step if i > 0 else (0, 0, 0), r=True, rad=joint.radius.get())
		step_joint.set_joint_type('Twist')
		cmds.orientConstraint(swing_joint, step_joint, w=(1.0 - t))
		if i > 0:
			cmds.orientConstraint(twist_joint, step_joint, w=t)
		bind_joints.push(step_joint)
	return bind_joints

def ballJointTwist(joint:Joint, systems_grp:MayaDagObject, subdivisions=1) -> JointCollection:
	twist_grp = groups.new_at(joint, suffix='twistGrp', parent=systems_grp)
	nodetree.parentConstraint(joint.parent(), twist_grp)

	twist_root = joint.but_with(suffix='noTwistRaw')
	twist_tip = joint.but_with(suffix='twistRaw')
	cmds.duplicate(joint, n=twist_root, po=True)
	selection.set(twist_root)
	cmds.joint(n=twist_tip, p=joint.child().translate_.get(), r=True, rad=joint.radius.get())
	cmds.parent(twist_root, twist_grp)

	swing, twist = swingTwist(joint)
	swing >> twist_root.rotate
	twist >> twist_tip.rotate
	
	return _createTwistSubdivisions(joint, twist_root, twist_tip, subdivisions=subdivisions)
