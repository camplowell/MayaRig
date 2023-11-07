from maya import cmds
import maya.api.OpenMaya as om
from . import attributes, naming

def subtract(name: str):
    node = cmds.shadingNode('plusMinusAverage', n=name, au=True)
    attributes.set_(node, 'operation', 2)
    return node

def switch(name:str):
    node = cmds.shadingNode('condition', n=name, au=True)
    attributes.set_(node, 'operation', 2)
    return node

def matMult(name:str):
    return cmds.shadingNode('multMatrix', n=name, au=True)

def composeMatrix(name:str):
    return cmds.shadingNode('composeMatrix', n=name, au=True)

def decomposeMatrix(name:str):
    return cmds.shadingNode('decomposeMatrix', n=name, au=True)

def condition(name: str):
    """Returns a Condition node. Default values have been swapped because Maya's are unintuitive."""
    node = cmds.shadingNode('condition', n=name, au=True)
    attributes.set_(node, 'colorIfFalse', (0, 0, 0))
    attributes.set_(node, 'colorIfTrue', (1, 1, 1))
    return node

def blendMatrix(name: str):
    return cmds.createNode('blendMatrix', n=name)

def matrixParent(source: str, target: str, connect=True):
    """
    Returns a matMult node that mimics the behavior of a Parent constraint.

    Connects to the target's offset parent matrix by default.
    """
    target_parent = cmds.listRelatives(target, p=True)[0]
    offset_mat = matMult(naming.replace(
        target,
        name="{0}To{1}".format(naming.get_name(target), naming.get_name(source)),
        suffix='matrix_parent'
    ))
    # Translate the parent offset matrix into the virtual parent's space
    offsetParent_local = om.MMatrix(attributes.get(target, 'worldMatrix[0]')) * om.MMatrix(attributes.get(source, 'worldInverseMatrix[0]'))

    attributes.set_(
        offset_mat, 
        'matrixIn[0]', 
        offsetParent_local, 
        type_='matrix')
    attributes.connect(source, 'worldMatrix[0]', offset_mat, 'matrixIn[1]')
    attributes.connect(target_parent, 'worldInverseMatrix[0]', offset_mat, 'matrixIn[2]')
    if connect:
        attributes.connect(offset_mat, 'matrixSum', target, 'offsetParentMatrix')
    return offset_mat