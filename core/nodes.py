from maya import cmds
from . import attributes

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

def condition(name: str):
    """Returns a Condition node. Default values have been swapped because Maya's are unintuitive."""
    node = cmds.shadingNode('condition', n=name, au=True)
    attributes.set_(node, 'colorIfFalse', (0, 0, 0))
    attributes.set_(node, 'colorIfTrue', (1, 1, 1))
    return node

def blendMatrix(name: str):
    return cmds.createNode('blendMatrix', n=name)