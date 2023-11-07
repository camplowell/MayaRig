from maya import cmds
from typing import List, Tuple
from .core import *

from .generators import simple, arm, leg, torso

def open_():
    win = 'autorig_edit'
    if cmds.window(win, exists=True):
        cmds.deleteUI(win)
    cmds.window(win, rtf=True, title="Rig Editor")
    mainLayout = cmds.columnLayout()

    createLayout = cmds.frameLayout(label = "Create", parent=mainLayout, mh=2)

    cmds.columnLayout(parent=createLayout, cat=('both', 4), w=258)
    createMenu = cmds.optionMenu(label='Create', w=250)
    cmds.setParent(createLayout)
    createTabs = cmds.tabLayout(tabsVisible=False, w=258)
    cmds.optionMenu( createMenu, e=True,
        changeCommand=lambda _: cmds.tabLayout(
            createTabs,
            e=True, 
            sti=cmds.optionMenu(createMenu, q=True, sl=True)))
    
    tabs = []
    registered_generators = dict()

    register_generator(simple, tabs, createMenu, registered_generators)
    register_generator(arm, tabs, createMenu, registered_generators)
    register_generator(leg, tabs, createMenu, registered_generators)
    register_generator(torso, tabs, createMenu, registered_generators)

    cmds.tabLayout(createTabs, edit=True, tabLabel=tabs)
    cmds.setParent(mainLayout)
    cmds.button(label="Create Metarig", command=lambda _ : create_metarig(registered_generators), w=258)
    cmds.showWindow()
    cmds.window(win, edit=True, w=100, h = 100)

def register_generator(generator, tabs:list, createMenu, registered_generators:dict):
    registered_generators[generator.name] = generator
    tabs.append((generator.create_menu(), generator.name))
    cmds.menuItem(parent=createMenu, label=generator.name)

def create_metarig(registered_generators):
    create_rig_groups()
    create_driver_bones()

    create_layout_control()
    chains = get_roots()
    for generator, chain in chains:
        registered_generators[generator].create_controllers(chain)

    chains = get_roots()
    for generator, chain in chains:
        registered_generators[generator].create_bind_joints(chain)
    
    attributes.set_(naming.no_touch_grp, 'visibility', False)

def get_roots() -> List[Tuple[str, List[str]]]:
    ret = []
    all_drivers = cmds.listRelatives(naming.driver_grp, ad=True, type='joint')
    roots = [obj for obj in all_drivers if joints.is_root(obj)]
    for root in roots:
        chain = joints.get_chain(root)
        generator = joints.get_generator(root)
        ret.append((generator, chain))
    ret.reverse()
    return ret

def create_driver_bones():
    """Create driver bones from all limb roots"""
    all_markers = cmds.listRelatives(naming.marker_grp, ad=True, type='joint')
    roots = [obj for obj in all_markers if joints.is_root(obj)]
    roots.reverse()
    for root in roots:
        if exists(naming.replace(root, suffix=Suffix.DRIVER_JOINT)):
            continue
        chain = joints.variants(joints.get_chain(root), suffix=Suffix.DRIVER_JOINT, parent_if_exists=True, keep_root=True)
        cmds.makeIdentity(chain, a=True, r=True, s=True)
        if joints.get_parent(root) == naming.marker_grp:
            cmds.parent(chain[0], naming.driver_grp)
        if joints.is_symmetrical(root):
            joints.mirror(chain[0])

def create_rig_groups():
    """Create or re-create the groups making up the final rig"""
    groups.push_front(n=naming.geometry_grp)
    groups.recreate(n=naming.bind_grp)
    groups.recreate(n=naming.driver_grp)
    groups.recreate(n=naming.systems_grp)
    
    groups.push_front(
        [
            naming.geometry_grp, 
            naming.bind_grp, 
            naming.driver_grp, 
            naming.systems_grp
        ], 
        n=naming.no_touch_grp)
    groups.recreate(n=naming.control_grp)

    groups.push_front([naming.control_grp, naming.no_touch_grp], n=naming.character_grp)

def create_layout_control():
    ctrl = controls.circle_with_arrows("layout", Suffix.CONTROL, parent=naming.control_grp, radius=50)
    naming.root_control = ctrl
    cog_ctrl = controls.circle_with_arrows('CoG', Suffix.CONTROL, parent=ctrl, joint=joints.find_child('CoG', naming.driver_grp), radius=20)
    naming.cog_control = cog_ctrl
    return ctrl