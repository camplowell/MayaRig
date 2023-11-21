from __future__ import annotations
from typing import Dict, Iterable, Tuple, List
import warnings

from maya import cmds
import maya.api.OpenMaya as om

from .maya_object import MayaObject, Side, Suffix, CollisionBehavior

from . import selection

_GENERATOR_ATTR = 'autorigLimb'
_SYMMETRY_ATTR = 'symmetrical'
_JOINT_TYPE_ATTR = 'mayaRigJoint'
_CONTROL_SIZE_ATTR = 'controlSize'

class Joint(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)

        self._begin_reserving()
        self.radius = self.attr('radius')
        self._end_reserving()
    
    @classmethod
    def marker(cls, side:Side, name:str, pos:'om.MVector|Tuple[float, float, float]', size:float=None, * , type_:str=None, onCollision=CollisionBehavior.INCREMENT):
        """Create a new marker joint.

        Args:
            side: The side of the character the new marker is on.
            name: What to call the new marker.
            pos: Where to put the new marker.
            type_: Override the type parameter of the created marker; defaults to `name`.
            onCollision: How to handle naming collisions.

        Returns:
            Joint: The new marker joint
        """
        if not type_:
            type_ = name
        marker = Joint.compose(side, name, Suffix.MARKER).resolve_collisions(onCollision)
        cmds.joint(n=marker, p=pos)
        if size:
            marker.addAttr(_CONTROL_SIZE_ATTR, value=size, type_='float', keyable=False)
        marker.addAttr(_JOINT_TYPE_ATTR, value=type_, type_='string', channelBox=False, lock=True)
        return marker

    @classmethod
    def cog_marker(cls, pos:'om.MVector|Tuple[float, float, float]'):
        ret = Joint.marker(Side.CENTER, 'CenterOfGravity', pos=pos, size=20, type_='CoG', onCollision=CollisionBehavior.THROW)
        ret.radius = 2
        return ret

    @classmethod
    def variants(cls, joints:'List[Joint]|JointCollection', suffix:str, * , remap_parent=True, clear_attributes=False, keep_root=True, root_parent=None, onCollision=CollisionBehavior.THROW) -> JointCollection:
        """ Create a variation of an existing collection of joints.

        Args:
            joints: The joints to duplicate
            suffix: The suffix of the new chain
            remap_parent: Parent new bones to the specified variant of its parent, if it exists.
            clear_attributes: Do not transfer user-defined attributes to the new chain.
            keep_root: Keep root bones marked as such in the new chain.
            root_parent: Override the parent of the first bone in the chain.
            onCollision: What to do if the given bones already exist. `IGNORE` will cause issues.

        Returns:
            JointCollection: The new joint chain.
        """
        if onCollision == CollisionBehavior.IGNORE:
            warnings.warn('Ignoring naming conflicts on Joints.variants may cause issues!')
        joints = list(joints)
        dups = cmds.duplicate(joints, po=True, n='temp#')
        ret = []
        for i in range(len(dups)):
            new_joint = joints[i].but_with(suffix=suffix, onCollision=onCollision)
            cmds.rename(dups[i], new_joint)
            ret.append(new_joint)
            if not keep_root:
                new_joint.clear_root()
            if clear_attributes:
                new_joint.clear_attributes(keep=[_JOINT_TYPE_ATTR])
            
            current_parent = new_joint.parent()
            if i == 0 and root_parent and current_parent != root_parent:
                cmds.parent(new_joint, root_parent)
            elif (remap_parent or (current_parent in joints)) and current_parent.is_internal():
                desired_parent = current_parent.but_with(suffix=suffix)
                if current_parent != desired_parent and desired_parent.exists():
                    cmds.parent(new_joint, desired_parent)
        return JointCollection(ret)

    def mark_root(self, generator:str, symmetrical:bool=False):
        """Mark a joint as the root of a Limb.

        Args:
            generator (str): Indicates the Limb that will handle control generation.
            symmetrical: Automatically mirror the limb when generating controls?
        """
        self._assert_exists()
        self.addAttr(_GENERATOR_ATTR, value=generator, type_='string', channelBox=True, lock=True)
        self.addAttr(_SYMMETRY_ATTR, value=symmetrical, type_='bool', channelBox=True, keyable=False)
    
    def mirror(self, *, mirrorBehavior=True, remap_parent=True):
        """Generate a mirrored version of the given joint and all of its descendants.

        Args:
            mirrorBehavior: Mirror the behavior of the joints. Analagous to the same option in Maya's mirror operation.
            remap_parent: Parent the result to the mirrored version of this joint's parent, if it exists.

        Returns:
            Joint: The mirrored version of this joint.
        """
        flipped = self.but_with(flip=True)
        if flipped.exists():
            cmds.warning('{} already exists!'.format(flipped))
            return flipped
        _flipped = cmds.mirrorJoint(self, mirrorYZ=True, mirrorBehavior=mirrorBehavior, sr=[self.side, Side.opposite(self.side)])
        if _flipped[0] != flipped:
            raise AssertionError('Mirroring joints is creating the wrong name!:\n  {}\n  {}'.format(_flipped[0], flipped))
        parent = self.parent()
        if parent and remap_parent:
            desired_parent = parent.but_with(flip=True)
            if desired_parent.exists() and flipped.parent() != desired_parent:
                cmds.parent(flipped, desired_parent, r=True)
                cmds.move( # Flip the joint's local y and z positions (secondary axis)
                    flipped.attr('tx').get_float(),
                    -flipped.attr('ty').get_float(),
                    -flipped.attr('tz').get_float(),
                    flipped,
                    ls=True,
                    r=False
                )
        return flipped 

    def clear_root(self):
        """Remove properties indicating that a joint is a root joint."""
        if self.is_root():
            self.attr(_GENERATOR_ATTR).delete()
            self.attr(_SYMMETRY_ATTR).delete()
    
    def is_root(self):
        """Is the given joint the root of a limb?"""
        self._assert_exists()
        return self.attr(_GENERATOR_ATTR).exists() and self.attr(_SYMMETRY_ATTR).exists()
    
    def clear_attributes(self, * , keep: List[str] = [_JOINT_TYPE_ATTR, _GENERATOR_ATTR, _SYMMETRY_ATTR]):
        return super().clear_attributes(keep=keep)
    
    def chain(self):
        """Get the joint descendants of this Joint, but not children of other roots"""
        self._assert_exists()
        if not self.is_root():
            raise ValueError('Cannot get the chain of a non-root Joint')
        chain:List[Joint] = []
        frontier = [self]
        while frontier:
            parent = frontier.pop()
            chain.append(parent)
            children = [Joint(child) for child in parent.children(type_='joint')]
            if children:
                frontier.extend([child for child in children if not child.is_root()])
        return JointCollection(chain)
    
    def generator(self):
        """Get the generator of a root joint"""
        if not self.is_root():
            raise Exception('Cannot get generator on non-root joint')
        return self.attr(_GENERATOR_ATTR).get_str()
    
    def is_symmetrical(self):
        """Is this root joint symmetrical?"""
        if not self.is_root():
            raise Exception('Cannot get symmetry of non-root joint')
        return self.attr(_SYMMETRY_ATTR).get_bool()
    
    def joint_type(self):
        """Get the indicated type of this joint"""
        return self.attr(_JOINT_TYPE_ATTR).get_str()

    def control_size(self):
        """Get the control size of this joint"""
        return self.attr(_CONTROL_SIZE_ATTR).get_float()
    
    def to_child(self) -> om.MVector:
        """Get the offset to the first joint child"""
        self._assert_exists()
        child = self.child(type_='joint')
        if not child:
            raise RuntimeError('No child to get the offset to!')
        return self.offset_to(child)

    def dissolve(self):
        """Remove this joint from its joint chain, transferring its children to its parent."""
        self._assert_exists()
        children = self.children()
        if children:
            cmds.parent(children, self.parent())
        cmds.delete(self)

    def position(self):
        self._assert_exists()
        return om.MVector(cmds.joint(self, q=True, p=True))
    
    def orient(self, * , flip_right=True, secondaryAxis='yup'):
        cmds.joint(self, e=True, oj='xyz', sao=secondaryAxis, ch=False, zso=True)

        if flip_right and self.side == Side.RIGHT:
            self.flip_joint_orient()
    
    def orient_world(self, * , flip_right=False):
        parent = self.parent()
        siblings = parent.children()
        cmds.parent(siblings, w=True)

        cmds.joint(self, e=True, oj='none', zso=True)

        cmds.parent(siblings, parent)
        if flip_right and self.side == Side.RIGHT:
            self.flip_joint_orient()
    
    def orient_to(self, normal:Tuple[float, float, float], * , target:MayaObject=None, secondaryAxis='yup', flip_right=True, twist=0, relativeTo:MayaObject=None):
        UPVEC = {'yup':(0, 1, 0), 'ydown':(0,-1, 0), 'zup':(0, 0, 1), 'zdown':(0, 0,-1)}
        sel = selection.get()
        children = self.children()
        if target is None:
            if not children:
                raise ValueError('Cannot infer target for {} (no children)'.format(self))
            target = children[0]
        if children:
            cmds.parent(children, w=True)
        
        aim=om.MVector(1,0,0)
        up = om.MVector(UPVEC[secondaryAxis])
        if flip_right and self.side == Side.RIGHT:
            aim *= -1
            twist *= -1
        kwargs = {}
        if relativeTo:
            kwargs['wut'] = 'objectrotation'
            kwargs['wuo'] = relativeTo
        temp_constraint = cmds.aimConstraint(children[0], self, aimVector=aim, upVector=up, worldUpVector=normal, **kwargs)
        cmds.delete(temp_constraint)
        cmds.makeIdentity(self, a=True, t=False, r=True, s=True)
        cmds.joint(self, e=True, zso=True)
        
        if twist:
            self.attr('jointOrientX').increment(twist)
        if children:
            cmds.parent(children, self)
        
        selection.set(sel)
    
    def orient_match(self, ref:Joint, flip_right=True, twist=0, worldSpace=False):
        if worldSpace:
            parent = self.parent()
            siblings = parent.children()
            cmds.parent(siblings, w=True)
            cmds.joint(self, e=True, o=cmds.joint(ref, q=True, o=True), zso=True)
            cmds.parent(siblings, parent)
        else:
            flipping = flip_right and self.side == Side.RIGHT
            if flipping:
                twist *= -1
            self.orient_to((0,1,0), flip_right=flip_right, twist=twist, relativeTo=ref)

    def normal(self, * , before=None, after=None):
        if not before:
            before = self.parent()
        if not after:
            after = self.child()
        if isinstance(before, MayaObject):
            before = self.offset_to(before)
        else:
            before = om.MVector(before) - self.position()
        if isinstance(after, MayaObject):
            after = self.offset_to(after)
        else:
            after = om.MVector(after) - self.position()

        return om.MVector((before ^ after).normalize())

    def flip_joint_orient(self):
        children = self.children()
        if children:
            cmds.parent(children, w=True)
        
        cmds.rotate(180, 180, 0, self, r=True, os=True)
        cmds.makeIdentity(self, a=True, r=True)
        cmds.joint(self, e=True, zso=True)
        
        if children:
            cmds.parent(children, self)

class JointCollection(Iterable):
    def __init__(self, joints:List[Joint]):
        self._joints = list(joints)
        self._cache:Dict[str, List[Joint]] = dict()
    
    def __getitem__(self, index):
        if type(index) == int:
            return self._joints[index]
        
        if index in self._cache:
            hits = self._cache[index]
        else:
            hits = []
            for joint in self._joints:
                if joint.exists() and joint.joint_type() == index:
                    hits.append(joint)
        
        hits = [joint for joint in hits if joint.exists()]
        
        if not hits:
            if index in self._cache:
                del self._cache[index]
            raise IndexError('No joint found for key {}'.format(index))
        
        self._cache[index] = hits
        if len(hits) == 1:
            return hits[0]
        
        return hits
    
    def __contains__(self, item):
        return bool(self[item])
    
    def __iter__(self):
        self._joints = [joint for joint in self._joints if joint.exists()]
        self._i = 0
        return self
    
    def __next__(self):
        if self._i >= len(self._joints):
            raise StopIteration
        ret = self[self._i]
        self._i += 1
        return ret
    
    def pop(self, index):
        if type(index) == str and index not in self._cache:
            found = False
            for i, joint in enumerate(self._joints):
                if joint.exists() and joint.joint_type() == index:
                    index = i
                    found = True
                    break
            if not found:
                raise IndexError('No joint found for key {}'.format(index))
        if type(index) == int:
            ret = self._joints.pop(index)
            type_ = ret.joint_type()
            if type_ in self._cache:
                self._cache[type_].remove(ret)
            return ret
        
        ret = self._cache[index].pop(0)
        self._joints.remove(ret)
        return ret
    
    def popAll(self, index):
        if index in self._cache:
            hits = [joint for joint in self._cache[index] if joint.exists()]
            del self._cache[index]
        else:
            hits = [joint for joint in self._joints if joint.exists() and joint.joint_type() == index]
        
        for hit in hits:
            self._joints.remove(hit)
        
        return hits

    def items(self):
        ret = dict()
        self._joints = [joint for joint in self._joints if joint.exists()]
        for joint in self._joints:
            type_ = joint.joint_type()
            if type_ in ret:
                ret[type_].append(joint)
            else:
                ret[type_] = [joint]
        self._cache = ret
        return ret.items()

    def __str__(self) -> str:
        return str(self._joints)