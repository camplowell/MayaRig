from typing import List, Literal, Tuple
from maya import cmds
from maya.api import OpenMaya as om
from .maya_object import CollisionBehavior, MayaAttribute, MayaDagObject, MayaObject, Side

def _plusMinusAvg(inputs, * , owner:MayaDagObject, side:Side, name:str, suffix:str, dimensions:int, operation:int):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('plusMinusAverage', n=node, au=True)

    node.attr('operation').set_or_connect(operation)

    attr_name = 'input{}D'.format(dimensions)
    for input_i, input in enumerate(inputs):
        node.attr(attr_name)[input_i].set_or_connect(input)
    
    return node.attr('output{}D'.format(dimensions))

def add1D(inputs:'List[float|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='add') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=1, operation=1)

def add2D(inputs:'List[tuple|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='add') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=2, operation=1)

def add3D(inputs:'List[tuple|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='add') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=3, operation=1)

def sub1D(inputs:'List[float|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='sub') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=1, operation=2)

def sub2D(inputs:'List[tuple|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='sub') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=2, operation=2)

def sub3D(inputs:'List[tuple|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='sub') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=3, operation=2)

def avg1D(inputs:'List[float|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='avg') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=1, operation=3)

def avg2D(inputs:'List[tuple|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='avg') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=2, operation=3)

def avg3D(inputs:'List[tuple|MayaAttribute]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='avg') -> MayaAttribute:
    return _plusMinusAvg(inputs, owner=owner, side=side, name=name, suffix=suffix, dimensions=3, operation=3)

def _multiplyDivide1(input1, input2, * , owner:MayaDagObject, side:Side, name:str, suffix:str, operation:str):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('multiplyDivide', n=node, au=True)

    node.attr('operation').set_or_connect(operation)

    node.attr('input1X').set_or_connect(input1)
    node.attr('input2X').set_or_connect(input2)

    return node.attr('outputX')

def _multiplyDivide3(input1, input2, * , owner:MayaDagObject, side:Side, name:str, suffix:str, operation:str):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('multiplyDivide', n=node, au=True)

    node.attr('operation').set_or_connect(operation)

    node.attr('input1').set_or_connect(input1)
    node.attr('input2').set_or_connect(input2)

    return node.attr('output')

def mult1D(input1, input2, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='multiply'):
    return _multiplyDivide1(input1, input2, owner=owner, side=side, name=name, suffix=suffix, operation=1)

def mult3D(input1, input2, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='multiply'):
    return _multiplyDivide1(input1, input2, owner=owner, side=side, name=name, suffix=suffix, operation=1)

def div1D(input1, input2, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='divide'):
    return _multiplyDivide1(input1, input2, owner=owner, side=side, name=name, suffix=suffix, operation=2)

def div3D(input1, input2, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='divide'):
    return _multiplyDivide3(input1, input2, owner=owner, side=side, name=name, suffix=suffix, operation=2)

def pow1D(input1, input2, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='pow'):
    return _multiplyDivide3(input1, input2, owner=owner, side=side, name=name, suffix=suffix, operation=3)

def pow3D(input1, input2, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='pow'):
    return _multiplyDivide3(input1, input2, owner=owner, side=side, name=name, suffix=suffix, operation=3)

def switch1D(firstTerm:'MayaAttribute|float', operation:str, secondTerm:'MayaAttribute|float', ifTrue:'MayaAttribute|float'=1, ifFalse:'MayaAttribute|float'=0, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='switch'):
    operations = ['==', '!=', '>', '>=', '<', '<=']
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('condition', n=node, au=True)

    node.attr('operation').set_or_connect(operations.index(operation))
    
    node.attr('firstTerm').set_or_connect(firstTerm)
    node.attr('secondTerm').set_or_connect(secondTerm)

    node.attr('colorIfTrueR').set_or_connect(ifTrue)
    node.attr('colorIfFalseR').set_or_connect(ifFalse)

    return node.attr('outColorR')

def switch3D(firstTerm:'MayaAttribute|float', operation:str, secondTerm:'MayaAttribute|float', ifTrue:'MayaAttribute|om.MVector|Tuple[float, float, float]', ifFalse:'MayaAttribute|om.MVector|Tuple[float, float, float]', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='switch'):
    operations = ['==', '!=', '>', '>=', '<', '<=']
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('condition', n=node, au=True)

    node.attr('operation').set_or_connect(operations.index(operation))

    node.attr('firstTerm').set_or_connect(firstTerm)
    node.attr('secondTerm').set_or_connect(secondTerm)

    for i, val in enumerate(ifTrue):
            node.attr('colorIfTrue')[i].set_or_connect(val)
    for i, val in enumerate(ifFalse):
            node.attr('colorIfFalse')[i].set_or_connect(val)
    
    return node.attr('outColor')

def _floatMath(floatA:'MayaAttribute|float', floatB:'MayaAttribute|float', operation=0, owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str=''):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('floatMath', n=node, au=True)

    node.attr('operation').set_or_connect(operation)

    node.attr('floatA').set_or_connect(floatA)
    node.attr('floatB').set_or_connect(floatB)

    return node.attr('outFloat')

def min(floatA:'MayaAttribute|float', floatB:'MayaAttribute|float', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='min'):
    return _floatMath(floatA, floatB, owner=owner, side=side, name=name, suffix=suffix, operation=4)

def max(floatA:'MayaAttribute|float', floatB:'MayaAttribute|float', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='max'):
    return _floatMath(floatA, floatB, owner=owner, side=side, name=name, suffix=suffix, operation=5)

def clamp1(input:'MayaAttribute|float', min:'MayaAttribute|float', max:'MayaAttribute|float', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='clamp'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('clamp', n=node, au=True)
    
    node.attr('inputR').set_or_connect(input)
    node.attr('minR').set_or_connect(min)
    node.attr('maxR').set_or_connect(max)
    
    return node.attr('outputR')

def clamp3(input, min, max, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='clamp'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('clamp', n=node, au=True)
    
    node.attr('input').set_or_connect(input)
    node.attr('min').set_or_connect(min)
    node.attr('max').set_or_connect(max)
    
    return node.attr('output')

def reverse1(input, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='invert'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('reverse', n=node, au=True)

    node.attr('inputX').set_or_connect(input)
    
    return node.attr('outputX')

def reverse3(input, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='invert'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('reverse', n=node, au=True)

    node.attr('input').set_or_connect(input)
    
    return node.attr('output')

def matMult(inputs:list, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='matMult'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('multMatrix', n=node, au=True)

    for i, input in enumerate(inputs):
        node.attr('matrixIn')[i].set_or_connect(input)
    
    return node.attr('matrixSum')

def blendMatrix(basis:'MayaAttribute|om.MMatrix', targets:List[dict], * , envelope=1.0, translate:bool=None, rotate:bool=None, scale:bool=None, shear=False, owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='blendMatrix'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('blendMatrix', n=node, au=True)
    translate, rotate, scale = _switchTRS(translate, rotate, scale)
    node.attr('inputMatrix').set_or_connect(basis)
    node.attr('envelope').set_or_connect(envelope)
    for i, target in enumerate(targets):
        attr = node.attr('target')[i]
        if isinstance(target, dict):
            attr.targetMatrix.set_or_connect(target['matrix'])
            attr.weight.set_or_connect(target.get('weight', 1.0))
            attr.translateWeight.set_or_connect(target.get('translate', float(translate)))
            attr.rotateWeight.set_or_connect(target.get('rotate', float(rotate)))
            attr.scaleWeight.set_or_connect(target.get('scale', float(scale)))
            attr.shearWeight.set_or_connect(target.get('shear', float(shear)))
        else:
            attr.targetMatrix.set_or_connect(target)
            attr.translateWeight.set_or_connect(float(translate))
            attr.rotateWeight.set_or_connect(float(rotate))
            attr.scaleWeight.set_or_connect(float(scale))
            attr.shearWeight.set_or_connect(float(shear))
    
    return node.attr('outputMatrix')

def aimMatrix(inputMatrix:'om.MMatrix|MayaAttribute', primaryTarget:'MayaDagObject|om.MVector|MayaAttribute', secondaryTarget:'MayaDagObject|om.MVector|MayaAttribute'=None, * , primaryAxis=(1,0,0), secondaryAxis=(0, 1, 0), primaryMode:Literal['lockAxis', 'aim', 'align']=..., secondaryMode:Literal['lockAxis', 'aim', 'align']=..., preSpace:'om.MMatrix|MayaAttribute'=om.MMatrix(), postSpace:'om.MMatrix|MayaAttribute'=om.MMatrix(), owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='aimMatrix', **kwargs):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.createNode('aimMatrix', n=node)

    node.attr('inputMatrix').set_or_connect(inputMatrix)
    node.attr('primaryTargetVector').set_or_connect(primaryTarget)
    if isinstance(primaryTarget, MayaDagObject):
        if primaryMode is ...:
            primaryMode = 'aim'
        primaryTarget.worldMatrix >> node.attr('primaryTargetMatrix')
    else:
        if primaryMode is ...:
            primaryMode = 'align'
        node.attr('primaryTargetVector').set_or_connect(primaryTarget)
    if isinstance(secondaryTarget, MayaDagObject):
        if secondaryMode is ...:
            secondaryMode = 'aim'
        secondaryTarget.worldMatrix >> node.attr('secondaryTargetMatrix')
    else:
        if secondaryMode is ...:
            secondaryMode = 'align'
        node.attr('secondaryTargetVector').set_or_connect(secondaryTarget)
    node.attr('primaryInputAxis').set_or_connect(primaryAxis)
    node.attr('secondaryInputAxis').set_or_connect(secondaryAxis)
    node.attr('primaryMode').set_or_connect(primaryMode)
    node.attr('secondaryMode').set_or_connect(secondaryMode)
    node.attr('preSpaceMatrix').set_or_connect(preSpace)
    node.attr('postSpaceMatrix').set_or_connect(postSpace)

    return node.attr('outputMatrix')


def composeMatrix(* , translate=None, rotate=None, scale=None, rotateOrder='xyz', inputQuat=None, owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='composeMatrix', **kwargs):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('composeMatrix', n=node, au=True)

    if translate is None:
        node.attr('inputTranslateX').set_or_connect(kwargs.get('translateX', 0))
        node.attr('inputTranslateY').set_or_connect(kwargs.get('translateY', 0))
        node.attr('inputTranslateZ').set_or_connect(kwargs.get('translateZ', 0))
    else:
        node.attr('inputTranslate').set_or_connect(translate)
    if inputQuat is not None:
        node.attr('inputQuat').set_or_connect(inputQuat)
        node.attr('useEulerRotation').set(0)
    elif rotate is None:
        node.attr('inputRotateX').set_or_connect(kwargs.get('rotateX', 0))
        node.attr('inputRotateY').set_or_connect(kwargs.get('rotateY', 0))
        node.attr('inputRotateZ').set_or_connect(kwargs.get('rotateZ', 0))
    else:
        node.attr('inputRotate').set_or_connect(rotate)
    
    if scale is None:
        node.attr('inputScaleX').set_or_connect(kwargs.get('scaleX', 1))
        node.attr('inputScaleY').set_or_connect(kwargs.get('scaleY', 1))
        node.attr('inputScaleZ').set_or_connect(kwargs.get('scaleZ', 1))
    else:
        node.attr('inputScale').set_or_connect(scale)
    
    node.attr('inputRotateOrder').set_or_connect(rotateOrder)
    
    return node.attr('outputMatrix')

class DecomposeMatrixNode(MayaObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._begin_reserving()
        self.inputMatrix = self.attr('inputMatrix')
        self.rotateOrder = self.attr('inputRotateOrder')
        self.outputTranslate = self.attr('outputTranslate')
        self.outputRotate = self.attr('outputRotate')
        self.outputQuat = self.attr('outputQuat')
        self.outputScale = self.attr('outputScale')
        self._end_reserving()

def decomposeMatrix(inputMatrix, * , rotateOrder:str, owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='decomposeMatrix') -> DecomposeMatrixNode:
    node = DecomposeMatrixNode(owner.but_with(side=side, name=name, suffix=suffix).resolve_collisions())
    cmds.shadingNode('decomposeMatrix', n=node, au=True)
    
    node.inputMatrix.set_or_connect(inputMatrix)
    node.rotateOrder.set_or_connect(rotateOrder)

    return node

def eulerToQuat(rotation, rotateOrder='xyz', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='euler2quat'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('eulerToQuat', n=node, au=True)

    node.attr('inputRotate').set_or_connect(rotation)
    node.attr('inputRotateOrder').set_or_connect(rotateOrder)

    return node.attr('outputQuat')

def quatSlerp(t, quat1=(0,0,0,1), quat2=(0,0,0,1), * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='quatSlerp'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('quatSlerp', n=node, au=True)

    node.attr('inputT').set_or_connect(t)
    node.attr('input1Quat').set_or_connect(quat1)
    node.attr('input2Quat').set_or_connect(quat2)

    return node.attr('outputQuat')

def quatInvert(quat, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='quatInvert'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('quatInvert', n=node, au=True)

    node.attr('inputQuat').set_or_connect(quat)

    return node.attr('outputQuat')

def quat2euler(quat:'Tuple[float, float, float, float]|MayaAttribute'=..., rotateOrder:'str|MayaAttribute'='xyz', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='quat2euler', quatX:'float|MayaAttribute'=0, quatY:'float|MayaAttribute'=0, quatZ:'float|MayaAttribute'=0, quatW:'float|MayaAttribute'=1):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('quatToEuler', n=node, au=True)
    if quat is not ...:
        node.attr('inputQuat').set_or_connect(quat)
    else:
        node.attr('inputQuatX').set_or_connect(quatX)
        node.attr('inputQuatY').set_or_connect(quatY)
        node.attr('inputQuatZ').set_or_connect(quatZ)
        node.attr('inputQuatW').set_or_connect(quatW)
    node.attr('inputRotateOrder').set_or_connect(rotateOrder)

    return node.attr('outputRotate')

def quatNormalize(quat:'Tuple[float, float, float, float]|MayaAttribute'=..., * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='quatNormalize', quatX:'float|MayaAttribute'=0, quatY:'float|MayaAttribute'=0, quatZ:'float|MayaAttribute'=0, quatW:'float|MayaAttribute'=1):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('quatNormalize', n=node, au=True)
    if quat is not ...:
        node.attr('inputQuat').set_or_connect(quat)
    else:
        node.attr('inputQuatX').set_or_connect(quatX)
        node.attr('inputQuatY').set_or_connect(quatY)
        node.attr('inputQuatZ').set_or_connect(quatZ)
        node.attr('inputQuatW').set_or_connect(quatW)

    return node.attr('outputQuat')

def quatProd(quat1:'Tuple[float, float, float, float]|MayaAttribute', quat2:'Tuple[float, float, float, float]|MayaAttribute', * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='quatProd'):
    node = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('quatProd', n=node, au=True)

    node.attr('input1Quat').set_or_connect(quat1)
    node.attr('input2Quat').set_or_connect(quat2)

    return node.attr('outputQuat')


def parentConstraint(source:MayaDagObject, target:MayaDagObject, * , connect:bool=True, translate:bool=None, rotate:bool=None, scale:bool=None):
    target_parent = target.parent()
    mat_hold = cmds.xform(target, q=True, m=True)
    cmds.xform(target, m=om.MMatrix.kIdentity)
    target.attr('translate').set((0, 0, 0))

    offsetParent_local = om.MMatrix(target.worldMatrix.get() * source.worldInverseMatrix.get())
    cmds.xform(target, m=mat_hold)

    ret = matMult([offsetParent_local, source.worldMatrix, target_parent.worldInverseMatrix], owner=source, name='{}To{}'.format(source.name, target.name), suffix='matrixParent')
    translate, rotate, scale = _switchTRS(translate, rotate, scale)
    if not (translate and rotate and scale):
        ret=blendMatrix(target.offsetParentMatrix.get_mat(), [ret], translate=translate, rotate=rotate, scale=scale, owner=target, suffix='matrixParentFilter')
    if connect:
        ret >> target.offsetParentMatrix
    return ret

def compositeParent(source:MayaDagObject, rot_source:MayaDagObject, target:MayaDagObject):
    base = parentConstraint(source, target, connect=False)
    rotate = parentConstraint(rot_source, target, connect=False)
    blend = blendMatrix(base, [rotate], rotate=True, owner=target, suffix='compositeParent')
    blend >> target.offsetParentMatrix
    return blend

def spaceSwitch(sources:List[MayaDagObject], target:MayaDagObject, * , control_attr:MayaAttribute=None, control_object:MayaDagObject=None, attr_name='space', niceName:str=None, default=0, options=[], includeParent=True, translate:bool=None, rotate:bool=None, scale:bool=None, rot_source:MayaDagObject=None):
    num_options = len(sources) + int(includeParent)
    if not control_attr:
        num_options = len(sources) + int(includeParent)
        if len(options) != num_options:
            raise ValueError('Expected to be given {} options; got {}'.format(num_options, len(options)))
        control_attr = (control_object or target).addAttr(attr_name, value=default, type_='enum', niceName=niceName, options=options)
    else:
        actual_size = len(control_attr.enum_values())
        if actual_size != num_options:
            raise ValueError('Expected an enum with {} options; got {}'.format(num_options, actual_size))
    
    blend_targets = [(source, {
        'matrix':parentConstraint(source, target, connect=False),
        'weight':switch1D(control_attr, '==', i)
        }) for i, source in enumerate(sources)]
    if rot_source:
        blend_targets.append({'matrix':parentConstraint(rot_source, target, connect=False), 'translate':0.0, 'rotate':1.0, 'scale':0.0, 'shear':0.0})

    blend = blendMatrix(target.offsetParentMatrix.get_mat(), blend_targets, envelope=switch1D(control_attr, '>', 0), translate=translate, rotate=rotate, scale=scale, owner=target)
    blend >> target.offsetParentMatrix
    return blend

def matInterp_cubic(values:'List[om.MMatrix|MayaAttribute]', t:float, * , owner:MayaDagObject=None, side:Side=None, name:str=None, suffix:str='splinePoint') -> MayaAttribute:
    node:MayaDagObject = MayaDagObject(owner.but_with(side=side, name=name, suffix=suffix, onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('wtAddMatrix', n=node, au=True)

    if len(values) != 4:
        raise ValueError('Expected 4 values; got {}'.format(len(values)))
    
    wtMat = node.attr('wtMatrix')
    wtMat[0].matrixIn.set_or_connect(values[0])
    wtMat[0].weightIn.set(pow(1.0 - t, 3))

    wtMat[1].matrixIn.set_or_connect(values[1])
    wtMat[1].weightIn.set(3 * pow(1.0 - t, 2) * t)

    wtMat[2].matrixIn.set_or_connect(values[2])
    wtMat[2].weightIn.set(3 * (1.0 - t, 3) * pow(t, 2))

    wtMat[3].matrixIn.set_or_connect(values[3])
    wtMat[3].weightIn.set(pow(t, 3))

    return node.attr('matrixSum')

def matSpline(values:'List[om.MMatrix|MayaAttribute]', t:float, * , owner:MayaDagObject=None, side:Side=None, name:str=None) -> MayaAttribute:
    interp_mat = matInterp_cubic(values, t, owner=owner, side=side, name=name)
    tangent = MayaDagObject(owner.but_with(side=side, name=name, suffix='tangentMatrix', onCollision=CollisionBehavior.INCREMENT))
    cmds.shadingNode('wtBlendMatrix', n=tangent, au=True)

    wtMat = tangent.attr('wtMatrix')

    wtMat[0].matrixIn.set_or_connect(values[0])
    wtMat[0].weightIn.set(-3 * pow(1 - t, 2))

    wtMat[1].matrixIn.set_or_connect(values[1])
    wtMat[1].weightIn.set(9 * pow(t, 2) - 12 * t + 3)

    wtMat[2].matrixIn.set_or_connect(values[2])
    wtMat[2].weightIn.set(6 * t - 9 * pow(t, 2))

    wtMat[3].matrixIn.set_or_connect(values[3])
    wtMat[3].weightIn.set(3 * pow(t, 2))

    aim = MayaDagObject(owner.but_with(side=side, name=name, suffix='alignToSpline', onCollision=CollisionBehavior.INCREMENT))
    cmds.createNode('aimMatrix', n=aim)
    interp_mat >> aim.attr('inputMatrix')
    tangent.attr('matrixSum') >> aim.attr('primary').primaryTargetMatrix

    return aim.attr('outputMatrix')

def _switchTRS(translate: None, rotate: None, scale: None):
    if translate is not None:
        if rotate is None:
            rotate = not translate
        if scale is None:
            scale = not translate
    elif rotate is not None:
        if translate is None:
            translate = not rotate
        if scale is None:
            scale = not rotate
    elif scale is not None:
        if translate is None:
            translate = not scale
        if rotate is None:
            rotate = not scale
    else:
        translate = True
        rotate = True
        scale = True
    
    return (translate, rotate, scale)