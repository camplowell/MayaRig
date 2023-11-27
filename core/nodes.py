from typing import Tuple
from .maya_object import *

class PlusMinusAverageNode(MayaObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._begin_reserving()
        self.operation = self.attr('operation')
        self.input1D = self.attr('input1D')
        self.input2D = self.attr('input2D')
        self.input3D = self.attr('input3D')
        self.output1D = self.attr('output1D')
        self.output2D = self.attr('output2D')
        self.output3D = self.attr('output3D')
        self._end_reserving()

    ADD = 1
    SUB = 2
    AVG = 3

class MultiplyDivideNode(MayaObject):
    NO_OP = 0
    MULT = 1
    DIV = 2
    POW = 3
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.operation = self.attr('operation')
        self.input1 = self.attr('input1')
        self.input1X = self.attr('input1X')
        self.input2 = self.attr('input2')
        self.input2X = self.attr('input2X')
        self.output = self.attr('output')
        self.outputX = self.attr('outputX')
        self._end_reserving()

class ConditionNode(MayaObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._begin_reserving()
        self.colorIfTrue = self.attr('colorIfTrue')
        self.colorIfFalse = self.attr('colorIfFalse')
        self.firstTerm = self.attr('firstTerm')
        self.secondTerm = self.attr('secondTerm')
        self.operation = self.attr('operation')
        self.outColor = self.attr('outColor')
        self._end_reserving()
    
    EQUAL = 0
    NOT_EQUAL = 1
    GREATER = 2
    GREATER_OR_EQUAL = 3
    LESS = 4
    LESS_OR_EQUAL = 5

class ReverseNode(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.input = self.attr('input')
        self.inputX = self.attr('inputX')
        self.output = self.attr('output')
        self.outputX = self.attr('outputX')
        self._end_reserving()

class MultMatrixNode(MayaObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._begin_reserving()
        self.matrixIn = self.attr('matrixIn')
        self.matrixSum = self.attr('matrixSum')
        self._end_reserving()

class ComposeMatrixNode(MayaObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._begin_reserving()
        self.inputTranslate = self.attr('inputTranslate')
        self.inputRotate = self.attr('inputRotate')
        self.inputScale = self.attr('inputScale')
        self.inputRotateOrder = self.attr('inputRotateOrder')

        self.outputMatrix = self.attr('outputMatrix')
        self._end_reserving()

class DecomposeMatrixNode(MayaObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._begin_reserving()
        self.inputRotateOrder = self.attr('inputRotateOrder')
        self.inputMatrix = self.attr('outputMatrix')

        self.outputTranslate = self.attr('outputTranslate')
        self.outputRotate = self.attr('outputRotate')
        self.outputScale = self.attr('outputScale')
        self._end_reserving()

class BlendMatrixNode(MayaObject):
    class Target(MayaAttribute):
        def __init__(self, *args):
            super().__init__(*args)
            self._begin_reserving()
            self.targetMatrix = self.child('targetMatrix')
            self.weight = self.child('weight')
            self.scaleWeight = self.child('scaleWeight')
            self.translateWeight = self.child('translateWeight')
            self.rotateWeight = self.child('rotateWeight')
            self.shearWeight = self.child('shearWeight')
            self._end_reserving()
    
    class TargetList(MayaAttribute):
        def __init__(self, obj:MayaObject, attr:str):
            super().__init__(obj, attr)

        def __getitem__(self, key):
            raw = super().__getitem__(key)
            return BlendMatrixNode.Target(raw._obj, raw._attr)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._begin_reserving()
        self.inputMatrix = self.attr('inputMatrix')
        self.target = BlendMatrixNode.TargetList(self, 'target')
        self.outputMatrix = self.attr('outputMatrix')
        self.envelope = self.attr('envelope')
        self._end_reserving()

class EulerToQuatNode(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.inputRotate = self.attr('inputRotate')
        self.rotateOrder = self.attr('inputRotateOrder')
        self.outputQuat = self.attr('outputQuat')
        self._end_reserving()

class QuatToEulerNode(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.inputQuat = self.attr('inputQuat')
        self.outputRotate = self.attr('outputRotate')
        self.rotateOrder = self.attr('inputRotateOrder')
        self._end_reserving()

class QuatSlerpNode(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.input1Quat = self.attr('input1Quat')
        self.input2Quat = self.attr('input2Quat')
        self.inputT = self.attr('inputT')
        self.outputQuat = self.attr('outputQuat')
        self._end_reserving()

class QuatInvertNode(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.inputQuat = self.attr('inputQuat')
        self.outputQuat = self.attr('outputQuat')
        self._end_reserving()

class CombinationShapeNode(MayaObject):
    MULTIPLICATION = 0
    MINIMUM = 1
    SMOOTH = 2
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.inputWeight = self.attr('inputWeight')
        self.outputWeight = self.attr('outputWeight')
        self.combinationMethod = self.attr('combinationMethod')
        self._end_reserving()

class FloatMathNode(MayaObject):
    MIN = 4
    MAX = 5
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.floatA = self.attr('floatA')
        self.floatB = self.attr('floatB')
        self.outFloat = self.attr('outFloat')
        self.operation = self.attr('operation')
        self._end_reserving()

class ClampNode(MayaObject):
    def __init__(self, *args):
        super().__init__(*args)
        self._begin_reserving()
        self.input = self.attr('input')
        self.min = self.attr('min')
        self.max = self.attr('max')
        self.output = self.attr('output')
        self._end_reserving()

class Nodes:
    @classmethod
    def subtract(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='subtract') -> PlusMinusAverageNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = PlusMinusAverageNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('plusMinusAverage', n=ret, au=True)
        ret.operation.set(ret.SUB)
        return ret
    
    @classmethod
    def add(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='add') -> PlusMinusAverageNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = PlusMinusAverageNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('plusMinusAverage', n=ret, au=True)
        ret.operation.set(ret.ADD)
        return ret
    
    @classmethod
    def average(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='average') -> PlusMinusAverageNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = PlusMinusAverageNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('plusMinusAverage', n=ret, au=True)
        ret.operation.set(ret.AVG)
        return ret
    
    @classmethod
    def multiply(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='multiply') -> MultiplyDivideNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = MultiplyDivideNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('multiplyDivide', n=ret, au=True)
        ret.operation.set(ret.MULT)
        return ret
    
    @classmethod
    def divide(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='divide') -> MultiplyDivideNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = MultiplyDivideNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('multiplyDivide', n=ret, au=True)
        ret.operation.set(ret.DIV)
        return ret
    
    @classmethod
    def power(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='power') -> MultiplyDivideNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = MultiplyDivideNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('multiplyDivide', n=ret, au=True)
        ret.operation.set(ret.POW)
        return ret
    
    @classmethod
    def switch(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='switch') -> ConditionNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = ConditionNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('condition', n=ret, au=True)
        ret.colorIfTrue.set((1, 1, 1))
        ret.colorIfFalse.set((0, 0, 0))
        ret.operation.set(ret.GREATER)
        return ret
    
    @classmethod
    def compare(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='compare') -> ConditionNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = ConditionNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('condition', n=ret, au=True)
        ret.colorIfTrue.set((1, 1, 1))
        ret.colorIfFalse.set((0, 0, 0))
        ret.operation.set(ret.EQUAL)
        return ret

    @classmethod
    def min(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='min') -> FloatMathNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = FloatMathNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('floatMath', n=ret, au=True)
        ret.operation.set(FloatMathNode.MIN)
        return ret

    @classmethod
    def smin(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='smin') -> CombinationShapeNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = CombinationShapeNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.createNode('combinationShape', n=ret)
        ret.combinationMethod.set(CombinationShapeNode.SMOOTH)
        return ret
    
    @classmethod
    def max(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='max') -> FloatMathNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = FloatMathNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('floatMath', n=ret, au=True)
        ret.operation.set(FloatMathNode.MAX)
        return ret
    
    @classmethod
    def clamp(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='clamp') -> ClampNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = ClampNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('clamp', n=ret, au=True)
        return ret
    
    @classmethod
    def invert(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='invert') -> ReverseNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = ReverseNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('reverse', n=ret, au=True)
        return ret

    @classmethod
    def matMult(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='matMult') -> MultMatrixNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = MultMatrixNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('multMatrix', n=ret, au=True)
        return ret

    @classmethod
    def composeMatrix(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='composeMatrix') -> ComposeMatrixNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = ComposeMatrixNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('composeMatrix', n=ret, au=True)
        return ret
    
    @classmethod
    def decomposeMatrix(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='decomposeMatrix') -> DecomposeMatrixNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = DecomposeMatrixNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('decomposeMatrix', n=ret, au=True)
        return ret
    
    @classmethod
    def blendMatrix(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='blendMatrix') -> BlendMatrixNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = BlendMatrixNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.createNode('blendMatrix', n=ret)
        return ret
    
    @classmethod
    def euler2quat(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='euler2quat') -> EulerToQuatNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = EulerToQuatNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('eulerToQuat', n=ret, au=True)
        return ret
    
    @classmethod
    def quat2euler(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='quat2euler') -> QuatToEulerNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = EulerToQuatNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('quatToEuler', n=ret, au=True)
        return ret
    
    @classmethod
    def quatSlerp(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='quatSlerp') -> QuatSlerpNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = QuatSlerpNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('quatSlerp', n=ret, au=True)
        ret.attr('input1QuatW').set(1.0)
        ret.attr('input2QuatW').set(1.0)
        return ret
    
    @classmethod
    def quatInvert(cls, * , owner:MayaObject=None, side:Side=None, name:str=None, suffix:str='quatInvert') -> QuatInvertNode:
        name = name if name else owner.name
        side = side if side else owner.side
        initials = owner.initial if owner else None
        ret = QuatInvertNode.compose(side, name, suffix, initials=initials).resolve_collisions()
        cmds.shadingNode('quatInvert', n=ret, au=True)
        return ret
    
    class Structures:
        @classmethod
        def parentConstraint(cls, source:MayaObject, target: MayaObject, * , connect:bool=True, translate:bool=None, rotate:bool=None, scale:bool=None):
            target_parent = target.parent()
            mat_hold = cmds.xform(target, q=True, m=True)
            cmds.xform(target, m=om.MMatrix.kIdentity)
            target.attr('translate').set((0, 0, 0))

            offsetParent_local = om.MMatrix(target.worldMatrix.get() * source.worldInverseMatrix.get())
            cmds.xform(target, m=mat_hold)

            offset_mat = Nodes.matMult(side=target.side, name='{}To{}'.format(source.name, target.name), suffix='matrixParent')
            offset_mat.matrixIn[0] = offsetParent_local
            source.worldMatrix >> offset_mat.matrixIn[1]
            if target.attr('inheritsTransform').get_bool():
                target_parent.worldInverseMatrix >> offset_mat.matrixIn[2]

            ret = offset_mat.matrixSum
            translate, rotate, scale = _switchTRS(translate, rotate, scale)
            if not (translate and rotate and scale):
                transform_filter = Nodes.blendMatrix(owner=offset_mat, suffix='transformFilter')
                transform_filter.inputMatrix = source.offsetParentMatrix.get_mat()
                offset_mat.matrixSum >> transform_filter.target[0].targetMatrix
                transform_filter.target[0].translateWeight = int(translate)
                transform_filter.target[0].rotateWeight = int(rotate)
                transform_filter.target[0].scaleWeight = int(scale)
                transform_filter.target[0].shearWeight = 0

                ret = transform_filter.outputMatrix

            if connect:
                ret >> target.offsetParentMatrix
            return ret
        
        @classmethod
        def compositeParent(cls, base_source:MayaObject, rot_source:MayaObject, target:MayaObject):
            base = Nodes.Structures.parentConstraint(base_source, target, connect=False)
            rotate = Nodes.Structures.parentConstraint(rot_source, target, connect=False)
            handle_blend = Nodes.blendMatrix(owner=target)
            base >> handle_blend.inputMatrix
            rotate >> handle_blend.target[0].targetMatrix
            handle_blend.target[0].translateWeight.set(0)
            handle_blend.target[0].scaleWeight.set(0)
            handle_blend.target[0].shearWeight.set(0)

            handle_blend.outputMatrix >> target.offsetParentMatrix


        @classmethod
        def spaceSwitch(cls, sources:List[MayaObject], target:MayaObject, * , attr:MayaAttribute=None, controller:MayaObject=None, name:str='space', niceName:str=None, defaultValue:int=0, options=[], includeParent=True, translate=None, rotate=None, scale=None, connect=True, lock_rot:MayaObject=None):
            if not attr:
                controller = controller if controller else target
                desired_options = len(sources) + int(includeParent)
                if len(options) != desired_options:
                    raise ValueError('Expected an enum with {} values; got {}'.format(desired_options, len(options)))
                attr = controller.addAttr(name, value=defaultValue, type_='enum', niceName=niceName, options=options)
            
            constraints = [(source, cls.parentConstraint(source, target, connect=False)) for source in sources]
            blend_node = Nodes.blendMatrix(owner=target, suffix='spaceBlend')
            blend_node.inputMatrix.set(target.offsetParentMatrix.get())

            
            if includeParent:
                envelope_cond = Nodes.switch(owner=target, suffix='spaceEnvelope')
                attr >> envelope_cond.firstTerm
                envelope_cond.secondTerm.set(0)
                envelope_cond.attr('outColorR') >> blend_node.envelope
                offset = 1
            else:
                offset = 0
                blend_node.envelope.set(1)
            
            translate, rotate, scale = _switchTRS(translate, rotate, scale)
            if lock_rot:
                rotate = False
            for i, (source, mat) in enumerate(constraints):
                mat >> blend_node.target[i].targetMatrix
                blend_node.target[i].translateWeight = int(translate)
                blend_node.target[i].rotateWeight = int(rotate)
                blend_node.target[i].scaleWeight = int(scale)
                blend_node.target[i].shearWeight = 0

                condition = Nodes.compare(side=target.side, name='{}To{}'.format(source.name, target.name))
                attr >> condition.firstTerm
                condition.secondTerm.set(i + offset)
                condition.attr('outColorR') >> blend_node.target[i].weight
            if lock_rot:
                i = len(constraints)
                rot_mat = cls.parentConstraint(lock_rot, target, connect=False)
                rot_mat >> blend_node.target[i].targetMatrix
                blend_node.target[i].translateWeight = 0
                blend_node.target[i].scaleWeight = 0
                blend_node.target[i].shearWeight = 0
            
            if connect:
                blend_node.outputMatrix >> target.offsetParentMatrix
            
            else:
                return blend_node.outputMatrix
            


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