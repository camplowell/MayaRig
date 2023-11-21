import os

from .ui.shelf import Shelf
from .core.context import Character
from .limbs import torso, legs, arms

_PACKAGE_NAME = __name__[:__name__.rindex('.')]

def main():
    prepare()
    RigShelf()

class RigShelf(Shelf):
    def __init__(self):
        super().__init__(name='RigGen', iconPath=getIconPath(), defaultIcon='button.png')
        self.refresh()
    
    def build(self):
        self.addButton(label='Build', command=package_command('build()'), icon='button_build.png')
        self.addButton(label='Bind', command=package_command('bind()'), icon='button_joint.png')
        self.addSeparator()
        torso_menu = self.addMenuButton('Torso', icon='button_torso.png')
        self.addMenuItem(torso_menu, 'FK Torso', package_limb(torso.Forward))
        self.addMenuItem(torso_menu, 'Simple Torso', package_limb(torso.Simple))
        legs_menu = self.addMenuButton('Legs')
        self.addMenuItem(legs_menu, 'Humanoid', package_limb(legs.HumanoidLeg))
        arm_menu = self.addMenuButton('Arms')
        self.addMenuItem(arm_menu, 'Humanoid', package_limb(arms.HumanoidArm))

def prepare():
    Character.initialize()

def package_command(command:str):
    """Outputs a Python script that runs a given function in commands.py"""
    return '''
import {package}
{package}.prepare()
{package}.commands.{command}
    '''.format(
        package = _PACKAGE_NAME,
        command=command
    )

def package_prepare():
    """Outputs a Python script that initializes the character"""
    return '''
import {package}
{package}.package.prepare()
'''.format(
        package = _PACKAGE_NAME,
    )

def package_limb(limb:type):
    """Outputs a Python script that builds a Limb's markers"""
    return '''
import {package}
{package}.prepare()
{limb_module}.{limb}.generateMarkers()
    '''.format(
        package = _PACKAGE_NAME,
        limb_module=limb.__module__,
        limb = limb.__name__
    )

def getIconPath():
    ret = os.path.join(os.path.dirname(__file__), 'icons/')
    return ret