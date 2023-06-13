from maya import cmds
from .core import *
from . import editor

def main():
    if load(None, broadcastErrors=False):
        return
    win = 'create_or_open'
    if cmds.window(win, exists=True):
        cmds.deleteUI(win)
    cmds.window(win, rtf=True, title="Create or Load")
    mainLayout = cmds.columnLayout(columnOffset=('both', 3))
    cmds.rowColumnLayout(
        nc=2,
        parent=mainLayout,
        columnWidth=[(1,125), (2, 175)]
    )
    cmds.text(label="Character name: ", align='right')
    name_field = cmds.textField()
    cmds.text(label = 'Character initials: ', align = 'right')
    initials_field = cmds.textField()

    cmds.columnLayout(parent=mainLayout,w=300)
    cmds.button(label="Create", command=lambda _ : create(win, name_field, initials_field), w=300)
    cmds.separator(style='single', w=300, h=8)
    cmds.button(label="Load", command=lambda _ : load(win), w=300)
    
    cmds.showWindow()
    cmds.window(win, edit=True, w=100, h = 100)

def create(win, name_field, initials_field):
    name = cmds.textField(name_field, q=True, text=True).replace(' ', '_')
    initials = cmds.textField(initials_field, q=True, text=True)
    if not name:
        cmds.error("Character name missing")
        return
    if not initials:
        cmds.error("Character initials missing")
        return
    cmds.deleteUI(win)
    
    naming.set_active_character(name, initials)

    cmds.group(name=naming.marker_grp, em=True)
    attributes.add(naming.marker_grp, 'initials', initials, 'string', lock=True)
    editor.open_()

def load(win, broadcastErrors=True):
    selected = cmds.ls(selection=True)
    if not selected or len(selected) != 1:
        if broadcastErrors:
            cmds.error("Please select the character markers group")
        return False
    active = selected[0]
    if ("_markers" not in active) or (not exists(active, 'initials')):
        if broadcastErrors:
            cmds.error("Selected item is not a character marker group")
        return False
    if win:
        cmds.deleteUI(win)

    name = active[:active.find("_markers")]
    initials=attributes.get(active, "initials")
    naming.set_active_character(name, initials)
    editor.open_()
    return True