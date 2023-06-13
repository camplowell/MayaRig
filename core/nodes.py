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