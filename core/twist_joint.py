from . import selection
from maya import cmds
from maya.api import OpenMaya as om

from .maya_object import MayaAttribute, MayaDagObject, Suffix
from .joint import Joint, JointCollection
from . import nodetree, groups

def swingTwist(rotation:MayaAttribute, reference:om.MQuaternion, owner:MayaDagObject):
	"""Returns a swing and twist Euler (rotate order taken from owner)"""
	reference_twist:om.MQuaternion = om.MQuaternion(reference.x, 0, 0, reference.w).normal()
	reference_twist_euler:om.MVector = reference_twist.asEulerRotation().asVector()

	relative_rot = nodetree.quatProd(rotation, reference.inverse(), owner=owner, suffix='relativeRot')
	relative_twist = nodetree.quatNormalize(
		quatX=relative_rot.obj.attr('outputQuatX'),
		quatW=relative_rot.obj.attr('outputQuatW'),
		owner=owner,
		suffix='relativeTwist'
	)

	relative_swing = nodetree.quatProd(
		nodetree.quatInvert(relative_twist, owner=owner, suffix='relativeTwistInv'),
		relative_rot,
		owner=owner,
		suffix='relativeSwing'
	)

	swing = nodetree.quatProd(
		nodetree.quatProd(
			reference_twist.inverse(),
			relative_swing,
			owner=owner
		),
		reference,
		owner=owner,
		suffix='swing'
	)

	swing_euler = nodetree.quat2euler(
		swing,
		owner.rotateOrder,
		owner=owner,
		suffix='swingEuler'
	)

	relative_twist_euler = nodetree.quat2euler(
		relative_twist,
		rotateOrder='xyz',
		owner=owner,
		suffix='relativeTwistEuler'
	)

	twist_euler = nodetree.add3D(
		[
			relative_twist_euler,
			reference_twist_euler
   		],
		owner=owner,
		suffix='twistEuler'
	)

	return swing_euler, twist_euler

def _createTwistSubdivisions(joint:Joint, bind_joint:Joint, swing_joint:MayaDagObject, twist_joint:MayaDagObject, steps=2) -> JointCollection:
	bind_joints = JointCollection([bind_joint])
	children = bind_joint.children()
	if children:
		cmds.parent(*children, w=True)
	cmds.parentConstraint(swing_joint, bind_joint)
	step = joint.child().translate_.get_vec() * (1.0 / (steps + 1))
	selection.set(joint.but_with(suffix=Suffix.BIND_JOINT))
	for i in range(steps):
		t = (i + 1) / (steps)
		step_joint = joint.but_with(name='{}Twist'.format(joint.name), suffix=Suffix.BIND_JOINT).resolve_collisions()
		cmds.joint(n=step_joint, p=step, r=True, rad=joint.radius.get() * 0.5)
		step_joint.set_joint_type('Twist')
		cmds.orientConstraint(swing_joint, step_joint, w=(1.0 - t))
		cmds.orientConstraint(twist_joint, step_joint, w=t)
		bind_joints.push(step_joint)
	if children:
		cmds.parent(*children, bind_joints[-1])
	return bind_joints

def ballJointTwist(joint:Joint, bind_joint:Joint, systems_grp:MayaDagObject, steps=2) -> JointCollection:
	twist_grp = groups.new_at(joint, suffix='twistGrp', parent=systems_grp)
	nodetree.parentConstraint(joint.parent(), twist_grp)

	twist_root = joint.but_with(suffix='noTwistRaw')
	twist_tip = joint.but_with(suffix='twistRaw')
	cmds.duplicate(joint, n=twist_root, po=True)
	selection.set(twist_root)
	cmds.joint(n=twist_tip, p=joint.child().translate_.get(), r=True, rad=joint.radius.get())
	cmds.parent(twist_root, twist_grp)

	rotation = nodetree.decomposeMatrix(
		nodetree.matMult(
			[
				joint.worldMatrix.get() * joint.parent().worldInverseMatrix.get(),
				joint.offsetParentMatrix, 
				joint.parent().worldMatrix.get() * joint.worldInverseMatrix.get()
			], 
			owner=joint
		), 
		rotateOrder=joint.rotateOrder, 
		owner=joint
	).outputQuat


	reference:om.MQuaternion = om.MEulerRotation(*joint.attr('twistRest').get_vec((0, 0, 0)), joint.rotateOrder.get()).asQuaternion()

	swing, twist = swingTwist(rotation, reference, joint)
	swing >> twist_root.rotate
	twist >> twist_tip.rotate
	
	return _createTwistSubdivisions(joint, bind_joint, twist_root, twist_tip, steps=steps)
