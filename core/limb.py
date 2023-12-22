from __future__ import annotations

from abc import ABC, abstractclassmethod, abstractmethod
from warnings import warn
from typing import Dict, List, Type

from maya import cmds

from .joint import Joint, JointCollection
from .context import Character
from .maya_object import MayaDagObject
from . import groups

from .nodes import Nodes

class Limb(ABC):
    key:str
    displayName:str

    control_group:MayaDagObject=None
    systems_group:MayaDagObject=None
    _limb_types: Dict[str, Type[Limb]] = {}
    def __init_subclass__(cls, **kwargs) -> None:
        if cls.key in Limb._limb_types:
            warn('Limb type {} already exists! Overriding...'.format(cls.key))
        Limb._limb_types[cls.key] = cls
    
    @classmethod
    def generators(cls):
        return Limb._limb_types.copy()
    
    @classmethod
    def buildRig(cls, pose_joints:JointCollection):
        cls(pose_joints)
        pass

    def __init__(self, pose_joints:JointCollection):
        if type(pose_joints) == list:
            pose_joints = JointCollection(pose_joints)
        self._ws_systems = None
        self.pose_joints = pose_joints
        self.control_group = groups.control_group(self.pose_joints[0], type(self).displayName)
        self.systems_group = groups.systems_group(self.pose_joints[0], type(self).displayName)
        self._generate_controls(self.pose_joints)
        self.pose_joints = JointCollection([joint for joint in self.pose_joints if joint.exists()])
        self.bind_joints = self._generate_bind_joints(self.pose_joints)

        self._cleanup(self.pose_joints, self.bind_joints)

    @property
    def ws_systems(self):
        if not self._ws_systems:
            self._ws_systems = groups.new_at(self.systems_group, name=type(self).displayName, suffix='wsSystems', parent=self.systems_group)
            Nodes.Structures.parentConstraint(Character.layout_control, self._ws_systems, rotate=True)
        return self._ws_systems


    @abstractclassmethod
    def generateMarkers(cls):
        """Generate any markers associated with the limb. 
        
        This allows the user to place the limb on the character before generating the rest of the rig.
        """
        cmds.error('generateMarkers is not implemented for {}'.format(cls))
        pass

    @abstractmethod
    def _generate_controls(self, pose_joints:JointCollection):
        """Generate any controls associated with the limb.

        Args:
            pose_joints: A (possibly mirrored) copy of the marker joints. Represents the current pose of the character.
        """
        cmds.warning('_generate_controls is not implemented for {}'.format(type(self)))
        pass

    @abstractmethod
    def _generate_bind_joints(self, pose_joints:JointCollection) -> JointCollection:
        """Generate the set of joints (and other deformers) responsible for deforming the character.

        These should be connected to the pose joints by constraints, to ensure the animation can be baked and exported.

        Args:
            pose_joints (JointCollection): Represents the current pose of the character. Recently pruned.

        Returns:
            JointCollection: The joints that will deform the character. Should be children of Character.bind_grp
        """
        cmds.warning('_generate_bind_joints is not implemented for {}'.format(type(self)))
        return JointCollection([])

    @abstractmethod
    def _cleanup(self, pose_joints:JointCollection, bind_joints:JointCollection):
        """Minimize the rig, deleting anything that doesn't serve a functional purpose.

        Args:
            pose_joints: Represents the current pose of the character.
            bind_joints: Deforms the character
        """
        cmds.warning('_prune_pose_joints is not implemented for {}'.format(type(self)))
        pass
    
    @classmethod
    def mark_root(cls, root:Joint, symmetrical:bool = False):
        """Marks a marker as root and parents it to the marker group."""
        root.mark_root(cls.key, symmetrical)
        if root.parent() != Character.marker_grp:
            cmds.parent(root, Character.marker_grp)
