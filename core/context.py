import re
from maya import cmds
import maya.api.OpenMaya as om
from .maya_object import MayaObject, Side, Suffix

_NAME_ATTR = 'rigGenName'
_INITIALS_ATTR = 'rigGenInitials'
_LAYOUT_SIZE_ATTR = 'layoutSize'

def _camelCase(string: str):
    words = string.split(' ')
    return ''.join([word.capitalize() for word in words])

class CancelledError(RuntimeError):
    pass

class Character:
    raw_name:str = None
    name:str = None
    initials:str = None

    marker_grp:MayaObject = None
    output_grp:MayaObject = None
    internals_grp:MayaObject = None

    geometry_grp:MayaObject = None
    pose_grp:MayaObject = None
    systems_grp:MayaObject = None
    bind_grp:MayaObject = None

    layout_control:MayaObject = None
    cog_control:MayaObject = None
    
    @classmethod
    def setCharacter(cls, initials, name):
        cls.raw_name = name
        cls.name = _camelCase(name)
        cls.initials = initials

        cls.marker_grp = MayaObject(cls.name + '_markers')
        cls.output_grp = MayaObject(cls.name)
        cls.internals_grp = MayaObject('{}_DO_NOT_TOUCH'.format(cls.initials))

        cls.controls_grp = MayaObject.compose(Side.CENTER, 'Controls', Suffix.GROUP, initials=initials)
        cls.geometry_grp = MayaObject.compose(Side.CENTER, 'Geometry', Suffix.GROUP, initials=initials)
        cls.pose_grp = MayaObject.compose(Side.CENTER, 'Pose', Suffix.GROUP, initials=initials)
        cls.systems_grp = MayaObject.compose(Side.CENTER, 'Systems', Suffix.GROUP, initials=initials)
        cls.bind_grp = MayaObject.compose(Side.CENTER, 'Bind', Suffix.GROUP, initials=initials)

    @classmethod
    def initialize(cls):
        _load()
        if cls.marker_grp and cls.marker_grp.exists():
            return
        result = cmds.layoutDialog(ui=_create_ui)
        if result == 'dismiss':
            raise CancelledError('Character creation cancelled.')
    
    @classmethod
    def layout_size(cls):
        return cls.marker_grp.attr(_LAYOUT_SIZE_ATTR).get_float()

def _load():
    """Find a character to use as context"""
    def _try_set(object):
        object = MayaObject(object)
        name_attr = object.attr(_NAME_ATTR)
        initials_attr = object.attr(_INITIALS_ATTR)
        if (name_attr.exists() and initials_attr.exists()):
            Character.setCharacter(initials_attr.get_str(), name_attr.get_str())
            return True
        return False
    # Try to infer the character using the active object hierarchy
    active = cmds.ls(sl=True, tl=True, l=True)
    if active:
        for obj in active[0].split('|'):
            if obj and _try_set(obj):
                return True
    # Grab the first character in the scene
    dagIt = om.MItDag(om.MItDag.kBreadthFirst, om.MFn.kTransform)
    while not dagIt.isDone():
        object = om.MFnDependencyNode(dagIt.currentItem()).absoluteName()
        if _try_set(object):
            return True
        dagIt.next()
    return False

def _create_ui():
    form = cmds.setParent(q=True)
    cmds.formLayout(form, e=True, width=100)

    name_label = cmds.text(label='Name: ', align='right')
    name_field = cmds.textField()
    initials_label = cmds.text(label='Initials: ', align='right')
    initials_field = cmds.textField()

    cmds.formLayout(
        form, 
        e=True,
        attachForm=[
            (name_label, 'top', 8), (name_field, 'top', 5),
            (name_field, 'left', 75), (name_field, 'right', 5),
            (initials_field, 'left', 75), (initials_field, 'right', 5),
            #(b1, 'left', 5)
        ],
        attachControl=[
            (name_label, 'right', 5, name_field),
            (initials_label, 'top', 8, name_field), (initials_field, 'top', 5, name_field),
            (initials_label, 'right', 5, initials_field),
            #(b1, 'top', initials_field)
        ]
    )
    
    def submit(*args):
        name = str(cmds.textField(name_field, q=True, tx=True))
        initials = str(cmds.textField(initials_field, q=True, tx=True))

        if not (name and re.match(r'^(?:[A-Za-z][a-zA-Z0-9]*(?:\s|$))+$', name)):
            cmds.error('Invalid character name: {}'.format(name))
            return
        if not (initials and re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', initials)):
            cmds.error('Invalid character initials: {}'.format(initials))
            return
        Character.setCharacter(initials, name)

        char_grp = MayaObject(cmds.group(n='{}_markers'.format(Character.name), em=True))
        char_grp.addAttr(_NAME_ATTR, value=name, type_='string', lock=True)
        char_grp.addAttr(_INITIALS_ATTR, value=initials, type_='string', lock=True)
        char_grp.addAttr(_LAYOUT_SIZE_ATTR, value=50, type_='float', keyable=False)

        cmds.layoutDialog(dismiss='confirm')
    
    b1 = cmds.button(l='Cancel', c='cmds.layoutDialog(dismiss="dismiss")')
    b2 = cmds.button(l='Create', c=submit)
    
    cmds.formLayout(
        form, e=True,
        attachForm=[(b1, 'left', 5), (b2, 'right', 5)],
        attachControl=[(b1, 'top', 5, initials_field), (b2, 'top', 5, initials_field)],
        attachPosition=[(b1, 'right', 5, 50), (b2, 'left', 5, 50)]
    )


# def _create_ui():
#     form = cmds.setParent(q=True)
#     cmds.formLayout(form, e=True, width=300)

#     name_label = cmds.text(label='Name: ', align='right')
#     name_field = cmds.textField()
#     initials_label = cmds.text(label='Initials: ', align='right')
#     initials_field = cmds.textField()

#     def onCreate(*args):
#         name = str(cmds.textField(name_field, q=True, tx=True))
#         initial = str(cmds.textField(initials_field, q=True, tx=True))
#         if not (name and re.match(r'^(?:[A-Za-z][a-zA-Z0-9]*(?:\s|$))+$', name)):
#             cmds.error('Invalid character name: {}'.format(name))
#             return
#         if not (initial and re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', initial)):
#             cmds.error('Invalid character initials: {}'.format(initial))
#             return
#         Character.setCharacter(initial, name)
#         char_grp = cmds.group(n='{}_markers'.format(Character.sanitizedName()), em=True)
#         cmds.addAttr(char_grp, ln=_NAME_ATTR, dt='string')
#         cmds.setAttr('{}.{}'.format(char_grp, _NAME_ATTR), name, typ='string', l=True)
#         cmds.addAttr(char_grp, ln=_INITIALS_ATTR, dt='string')
#         cmds.setAttr('{}.{}'.format(char_grp, _INITIALS_ATTR), initial, typ='string', l=True)
#         cmds.layoutDialog(dismiss='Done')

#     b1 = cmds.button(l='Cancel', c='cmds.layoutDialog(dismiss="CANCELLED")')
#     b2 = cmds.button(l='Create', c=onCreate)

#     cmds.formLayout(
#         form, 
#         e=True,
#         attachForm=[(name_label, 'top', 5)],
#         attachControl=[(name_field, 'left', 5, name_label)]
#     )