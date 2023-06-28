from maya import cmds

def set_(obj: str):
    if (obj):
        cmds.select(obj, r=True)
    else:
        cmds.select(cl=True)

def clear():
    cmds.select(cl=True)

def get():
    return cmds.ls(sl=True)

def active():
    selected = get()
    if selected:
        return selected[0]
    return None