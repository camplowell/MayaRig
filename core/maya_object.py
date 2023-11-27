from __future__ import annotations

import re
from typing import Any, List
from enum import Enum

from maya import cmds
import maya.api.OpenMaya as om

_VALID_SECTION = re.compile("\\A[a-zA-Z0-9][a-zA-Z0-9]*\\Z")

class Side(str, Enum):
    LEFT = '_l_'
    RIGHT = '_r_'
    CENTER = '_'
    @classmethod
    def opposite(cls, side:Side):
        if side == Side.LEFT:
            return Side.RIGHT
        if side == Side.RIGHT:
            return Side.LEFT
        return side

class Suffix(str, Enum):
    # Controls
    CONTROL = 'control'
    FK_CONTROL = 'fkControl'
    IK_CONTROL = 'ikControl'
    IK_POLE = 'ikPole'
    TWEAK_CONTROL = 'tweakControl'
    SWITCH_CONTROL = 'switch'
    # Joints
    POSE_JOINT = 'pose'
    IK_JOINT = 'ik'
    FK_JOINT = 'fk'
    BIND_JOINT = 'bindJoint'
    # Internal DAG objects
    MARKER = 'marker'
    GROUP = 'grp'
    SYSTEM_GROUP = 'systemGrp'
    OFFSET_GROUP = 'offsetGrp'

class CollisionBehavior(Enum):
    IGNORE = 0,
    THROW = 1,
    REPLACE = 2,
    INCREMENT = 3,

def _expand_name(string:str):
    index = string.find('_')
    initial = string[:index]
    workingStr = string[index:]
    side = None
    if workingStr.startswith(Side.LEFT) or workingStr.startswith(Side.RIGHT):
        side = Side(workingStr[:3])
        workingStr = workingStr[3:]
    else:
        side = Side(workingStr[:1])
        workingStr = workingStr[1:]
    index = workingStr.find('_')
    if index == -1:
        raise ValueError('No suffix')
    name = workingStr[:index]
    suffix = workingStr[index + 1:]
    return (initial, side, name, suffix)

def _resolve_name(*args, number=None):
    if len(args) == 1:
        return str(args[0])
    (initial, side, name, suffix) = args
    return initial + side + name + (str(number) if number else '') + '_' + suffix

class MayaObject(str):
    ROTATE_ORDER = {'xyz':0, 'yzx':1, 'zxy':2, 'xzy':3, 'yxz':4, 'zyx':5}
    def __new__(cls, *args):
        return str.__new__(cls, _resolve_name(*args))
    
    def __init__(self, *args):
        if len(args) == 1:
            try:
                (initial, side, name, suffix) = _expand_name(args[0])
            except:
                (initial, side, name, suffix) = ['', '', '', '']
        elif len(args) == 4:
            (initial, side, name, suffix) = args
        else:
            raise Exception('Expected 1 or 4 argements; got {}'.format(str(len(args))))
        self._isInternal = False
        try:
            if not re.match(_VALID_SECTION, initial):
                raise Exception('Invalid initial: {}'.format(self))
            if not re.match(_VALID_SECTION, name):
                raise Exception('Invalid name: {}'.format(self))
            if not re.match(_VALID_SECTION, suffix):
                raise Exception('Invalid suffix: {}'.format(self))
            self._side = Side(side)
            self._initial = str(initial)
            self._name = str(name)
            self._suffix = str(suffix)
            
            self._isInternal = True
            if self._name[0] != self._name[0].upper():
                cmds.warning('Joint name is not capitalized: {}'.format(self))
        except Exception as e:
            pass
        self._begin_reserving()
        self.visibility = self.attr('visibility')
        self.translate_ = self.attr('translate')
        self.rotate = self.attr('rotate')
        self.scale = self.attr('scale')
        self.offsetParentMatrix = self.attr('offsetParentMatrix')
        self.matrix = self.attr('matrix')
        self.inverseMatrix = self.attr('inverseMatrix')
        self.parentMatrix = self.attr('parentMatrix[0]')
        self.parentInverseMatrix = self.attr('parentInverseMatrix[0]')
        self.worldMatrix = self.attr('worldMatrix[0]')
        self.worldInverseMatrix = self.attr('worldInverseMatrix[0]')
        self.rotateOrder = self.attr('rotateOrder')
        self._end_reserving()

    @classmethod
    def compose(cls, side:Side, name:str, suffix:str, * , initials:str=None):
        """Initialize with separate components."""
        if not initials:
            from .context import Character
            initials = Character.initials
        return cls(initials, side, name, suffix)

    @classmethod
    def from_str(cls, string:str):
        """Initialize with a single string."""
        return cls(string)

    def but_with(self, * , side:Side=None, name:str=None, suffix:str=None, onCollision=CollisionBehavior.IGNORE, flip:bool=False):
        """Returns a copy of self with the specified changes.

        Args:
            side: Set the side of the returned copy.
            name: Set the name of the returned copy.
            suffix: Set the suffix of the returned copy.
            onCollision: How to deal with naming conflicts.

        Returns:
            Self: A copy of self with the specified changes.
        """
        try:
            if side is None:
                side = self._side
            if flip:
                side = Side.opposite(side)
            return type(self)(MayaObject(
                self._initial,
                side, 
                name if name else self._name,
                suffix if suffix else self._suffix
            )).resolve_collisions(onCollision)
        except:
            raise ValueError('Cannot use but_with on extexnal object {}'.format(self))

    def resolve_collisions(self, onCollision=CollisionBehavior.INCREMENT):
        """Deal with naming collisions

        Args:
            onCollision: How to deal with naming collisions.

        Returns:
            Self: The resulting object.
        """
        if onCollision == CollisionBehavior.INCREMENT:
            if not self.is_internal():
                raise ValueError('Cannot increment external object {}'.format(self))
        if not self.exists() or onCollision == CollisionBehavior.IGNORE:
            return self
        if onCollision == CollisionBehavior.THROW:
            raise RuntimeError('Object already exists: {}'.format(self))
        if onCollision == CollisionBehavior.REPLACE:
            cmds.delete(self)
            return self
        if onCollision == CollisionBehavior.INCREMENT:
            return self._increment()
        return self

    def _increment(self):
        name = self._name
        num = 0
        num_match = re.search(r'\d+$', name)
        if num_match:
            num = int(num_match.group())
            name = name[:-len(num_match.group())]
        while cmds.objExists(_resolve_name(self._initial, self._side, name, self._suffix, number=num)):
            num += 1
        
        name += str(num)
        return type(self).compose(self._side, name, self._suffix, initials=self._initial)

    def _assert_exists(self):
        if not self.exists():
            raise RuntimeError('No such object: {}'.format(self))
        
    def is_internal(self):
        return self._isInternal

    @property
    def initial(self):
        """The character's initials"""
        try:
            return self._initial
        except:
            raise ValueError('Cannot get the initial of external object {}'.format(self))
    @property
    def side(self):
        """Which side of the character the object is on"""
        try:
            return self._side
        except:
            raise ValueError('Cannot get the side of external object {}'.format(self))
    @property
    def name(self):
        """The name of the object"""
        try:
            return self._name
        except:
            raise ValueError('Tried to use name for external object {}.'.format(self))
    @property
    def suffix(self):
        """The suffix of the object"""
        try:
            return self._suffix
        except:
            raise ValueError('Cannot get the suffix of external object {}'.format(self))
    
    def exists(self) -> bool:
        """Does this object exist, according to Maya?"""
        return cmds.objExists(self)
    
    def object_type(self) -> str:
        """The node type of the given object"""
        return cmds.objectType(self)
    
    def position(self):
        """Returns the world-space position of the object. (rotation pivot by default)"""
        self._assert_exists()
        return om.MVector(cmds.xform(self, q=True, rp=True, ws=True))
    
    def offset_to(self, other:MayaObject) -> om.MVector:
        self._assert_exists()
        other._assert_exists()
        return other.position() - self.position()

    def set_rest(self):
        """Apply the current transformation of the object into the offset parent matrix"""
        local_matrix = om.MMatrix(cmds.xform(self, q=True, m=True, ws=False))
        offset_parent_matrix = self.attr('offsetParentMatrix').get_mat()
        baked_matrix = local_matrix * offset_parent_matrix
        self.attr('offsetParentMatrix').set(baked_matrix)
        cmds.makeIdentity(self, a=False, t=True, r=True, s=True)

    def children(self, type_:str=None):
        """Get a list of this object's children

        Args:
            type_: Limit results to the given node type.

        Returns:
            List[MayaObject]: This object's children
        """
        kwargs = {'typ':type_} if type_ else {}
        return [MayaObject(child) for child in cmds.listRelatives(self, c=True, **kwargs) or []]
    
    def child(self, type_:str=None):
        """Get this object's the first child.

        Args:
            type_: Limit results to the given node type.

        Returns:
            MayaObject: This object's first child
        """
        children = self.children(type_)
        return children[0] if children else None
    
    def descendants(self, type_:str=None):
        """Get a list of this object's descendants

        Args:
            type_: Limit results to the given node type.

        Returns:
            List[MayaObject]: This object's descendants
        """
        kwargs = {'typ':type_} if type_ else {}
        return [MayaObject(descendant) for descendant in cmds.listRelatives(self, ad=True, **kwargs) or []]
    
    def parent(self):
        """Get this object's parent"""
        parents = cmds.listRelatives(self, p=True)
        if parents:
            return MayaObject(parents[0])
        return None
    
    def ancestors(self):
        """Get this object's ancestors"""
        ancestors = str(cmds.listRelatives(self, f=True)).split('|')[:-1]
        return [MayaObject(ancestor) for ancestor in ancestors or []]
    
    def root_ancestor(self):
        """Get the top-level parent of this object"""
        hierarchy = str(cmds.listRelatives(self, f=True)).split('|')
        return MayaObject(hierarchy[0])

    def attr(self, attribute:str):
        """Get an attribute of this object"""
        return MayaAttribute(self, attribute)
    
    def addAttr(self, attribute:str, value, type_:str, * , channelBox=True, keyable=True, niceName:str=None, lock:bool=False, options:List[str]=None, min:float=None, max:float=None):
        """Add a new attribute.

        Args:
            attribute: The name of the attribute
            value: The initial or default value of the attribute.
            type_: The type of data stored in the attribute
            channelBox: Show in the channel box?
            keyable: Allow keyframes on the attribute?
            niceName: Override the attribute's visible name.
            lock: Lock the attribute?
            options: The options of an enum attribute.

        Returns:
            MayaAttribute: The newly created attribute
        """
        self._assert_exists()
        ret = self.attr(attribute)
        if ret.exists():
            raise RuntimeError('Attribute already exists: {}'.format(ret))
        if type_=='enum':
            cmds.addAttr(self, ln=attribute, at=type_, dv=value, k=keyable, en=':'.join(options))
        elif type_ in ['string', 'stringArray', 'matrix', 'reflectanceRGB', 'spectrumRGB', 'doubleArray', 'floatArray', 'Int32Array', 'vectorArray', 'nurbsCurve', 'nurbsSurface', 'mesh', 'lattice', 'pointArray']:
            cmds.addAttr(self, ln=attribute, dt=type_, k=keyable)
            ret.set(value)
        else:
            kwargs = {}
            if min is not None:
                kwargs['min'] = min
            if max is not None:
                kwargs['max'] = max
            cmds.addAttr(self, ln=attribute, at=type_, dv=value, k=keyable, **kwargs)
        
        if niceName:
            cmds.addAttr(ret, e=True, nn=niceName)
        if channelBox:
            cmds.setAttr(ret, cb=channelBox)
        if lock:
            ret.lock()
        if keyable:
            cmds.setAttr(ret, k=True)
        return ret
    
    def lockAttrs(self, attrs):
        for attr in attrs:
            if attr in ['translate', 'rotate', 'scale']:
                self.attr(attr + 'X').lock()
                self.attr(attr + 'Y').lock()
                self.attr(attr + 'Z').lock()
            else:
                self.attr(attr).lock()
    
    def unlockAttrs(self, attrs):
        for attr in attrs:
            if attr in ['translate', 'rotate', 'scale']:
                self.attr(attr + 'X').unlock()
                self.attr(attr + 'Y').unlock()
                self.attr(attr + 'Z').unlock()
            self.attr(attr).unlock()

    def clear_attributes(self, * , keep:List[str]=[]):
        for attr in cmds.listAttr(self, ud=True) or []:
            if attr not in keep:
                self.attr(attr).delete()

    def _begin_reserving(self):
        """Pause syntactic sugar for setting the value of Maya attributes"""
        self._reserving = True
    
    def _end_reserving(self):
        """Resume syntactic sugar for setting the value of Maya attributes"""
        del self._reserving
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            raise AttributeError('No such attribute: {}'.format(name))
        attr = self.attr(name)
        if attr.exists():
            return attr
        raise AttributeError('No such attribute: {}'.format(attr))

    def __setattr__(self, name:str, value):
        if not (name.startswith('_') or hasattr(self, '_reserving')):
            current = getattr(self, name, self.attr(name))
            if isinstance(current, MayaAttribute) and current.exists():
                current.set(value)
                return
        object.__setattr__(self, name, value)
    
class MayaAttribute(str):
    def __new__(cls, object, attribute):
        return str.__new__(cls, '{}.{}'.format(object, attribute))
    def __init__(self, object, attribute):
        self._obj = object
        self._attr = attribute

    def child(self, attribute:str):
        """Get a child attribute

        Args:
            attribute: The name of the sub-attribute

        Returns:
            MayaAttribute: The child attribute
        """
        return MayaAttribute(self._obj, '{0}.{1}'.format(self._attr, attribute))

    def exists(self) -> bool:
        """Does this attribute exist?"""
        return cmds.objExists(self)
    
    def _assert_exists(self):
        if self.exists():
            return
        raise RuntimeError('No such attribute: {0}'.format(self))
    
    def type(self) -> str:
        """Get the type of this attribute"""
        return cmds.getAttr(self, typ=True)
    
    def get(self, default=None):
        """Get the value of the attribute"""
        if not self.exists() and default is not None:
            return default
        type_ = self.type()
        if type_ in ['float3', 'double3']:
            return self.get_vec()
        if type_ == 'matrix':
            return self.get_mat()
        if type_ == 'string':
            return self.get_str()
        return self._get()
    
    def get_vec(self, default = None):
        """Get the value of this attribute as an MVector"""
        return om.MVector(self._get(default))
    
    def get_mat(self, default=None):
        """Get the value of this attribute as an MMatrix"""
        return om.MMatrix(self._get(default))
    
    def get_bool(self, default=None):
        """Get the value of this attribute as a boolean"""
        return bool(self._get(default))
    
    def get_float(self, default=None):
        """Get the value of this attribute as a floating-point number"""
        return float(self.get(default))
    
    def get_int(self):
        """Get the value of this attribute as an integer"""
        return int(self.get())
    
    def get_str(self):
        """Get the value of this attribute as a string"""
        return str(self._get())
    
    def _get(self, default=None) -> Any:
        if not self.exists():
            if default is not None:
                return default
            raise RuntimeError('No such attribute: {}'.format(self))
        
        ret = cmds.getAttr(self)
        if isinstance(ret, list) and len(ret) == 1:
            return ret[0]
        return ret

    def set(self, value):
        """Set the value of this attribute"""
        kwargs = {}
        if isinstance(value, int) or isinstance(value, float):
            pass
        elif isinstance(value, str):
            if self.type() == 'enum':
                value = self.enum_values().index(value)
            else:
                kwargs['typ'] = 'string'
        elif isinstance(value, om.MVector) or isinstance(value, tuple) and len(value) == 3:
            kwargs['typ'] = 'float3'
        elif isinstance(value, om.MMatrix):
            kwargs['typ'] = 'matrix'
        elif self.exists():
            _type = self.type()
            if _type in ['short2', 'short3', 'long2', 'long3', 'int32Array', 'float2', 'float3', 'double2', 'double3', 'doubleArray', 'matrix', 'pointArray', 'vectorArray', 'string', 'stringArray']:
                kwargs['typ'] = _type
        else:
            raise ValueError('Cannot infer types for non-existent attributes')
        
        if hasattr(value, '__len__') and not isinstance(value, str):
            return cmds.setAttr(self, *value, **kwargs)
        else:
            return cmds.setAttr(self, value, **kwargs)
    
    def set_or_connect(self, value):
        if isinstance(value, MayaAttribute):
            value >> self
        else:
            self.set(value)

    def increment(self, value):
        return self.set(self.get() + value)
    
    def multiply(self, value):
        return self.set(self.get() * value)

    def connect(self, to:MayaAttribute, force:bool=True):
        """Connect the output of this attribute to the input of the given attribute."""
        cmds.connectAttr(self, to, f=force)

    def lock(self, hide=True):
        self._assert_exists()
        self._was_unkeyable = not cmds.getAttr(self, k=True)
        cmds.setAttr(self, l=True, k=False, cb=False)
    
    def unlock(self, show=True):
        self._assert_exists()
        
        was_unkeyable = hasattr(self, '_was_unkeyable') and self._was_unkeyable
        cmds.setAttr(self, l=False, cb=show, k=show and not was_unkeyable)
        try:
            del self._was_unkeyable
        except:
            pass
    
    def delete(self):
        self._assert_exists()
        self.unlock()
        cmds.deleteAttr(self)

    def enum_values(self) -> List[str]:
        return cmds.attributeQuery(self, le=True)
    
    def __getitem__(self, key):
        return type(self)(self._obj, "{}[{}]".format(self._attr, key))
    
    def __setitem__(self, key, value):
        return self[key].set(value)
    
    def _begin_reserving(self):
        """Pause syntactic sugar for setting the value of Maya attributes"""
        self._reserving = True
    
    def _end_reserving(self):
        """Resume syntactic sugar for setting the value of Maya attributes"""
        del self._reserving
    
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError('No such attribute: {}'.format(name))
        attr = self.child(name)
        return attr
    
    def __setattr__(self, name:str, value):
        if not (name.startswith('_') or hasattr(self, '_reserving')):
            current = getattr(self, name, self.child(name))
            if isinstance(current, MayaAttribute) and current.exists():
                current.set(value)
                return
        object.__setattr__(self, name, value)

    def __rshift__(self, other):
        return self.connect(other)
