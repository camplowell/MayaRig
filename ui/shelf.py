import os

from maya import cmds

class Shelf:
    '''A simple class to build shelves in maya. Since the build method is empty,
    it should be extended by the derived class to build the necessary shelf elements.
    By default it creates an empty shelf called "customShelf".'''

    def __init__(self, name="customShelf", iconPath:str='', defaultIcon="commandButton.png"):
        self.name = name
        self.iconPath = iconPath

        self.labelBackground = (0, 0, 0, 0)
        self.labelColour = (.9, .9, .9)

        self.defaultIcon=defaultIcon

    def refresh(self):
        self._cleanOldShelf()
        cmds.setParent(self.name)
        self.build()

    def build(self):
        '''This method should be overwritten in derived classes to actually build the shelf
        elements. Otherwise, nothing is added to the shelf.'''
        pass

    def addButton(self, label, icon:str=None, command='', doubleCommand=''):
        '''Adds a shelf button with the specified label, command, double click command and image.'''
        cmds.setParent(self.name)
        if not icon:
            icon = self.defaultIcon
        icon = self.iconPath + icon
        cmds.shelfButton(width=37, height=37, image=icon, l=label, command=command, dcc=doubleCommand, imageOverlayLabel=label, olb=self.labelBackground, olc=self.labelColour)

    def addMenuButton(self, label, icon:str=None, command=''):
        """Adds a shelf button that opens a popup menu when clicked. Returns the created menu."""
        self.addButton(label, icon, command=command)
        return cmds.popupMenu(b=1)

    def addMenuItem(self, parent, label, command='', icon="kinJoint.png"):
        '''Adds a shelf button with the specified label, command, double click command and image.'''
        if icon:
            icon = self.iconPath + icon
        return cmds.menuItem(p=parent, l=label, c=command, i=icon)

    def addSubMenu(self, parent, label, icon=None):
        '''Adds a sub menu item with the specified label and icon to the specified parent popup menu.'''
        if icon:
            icon = self.iconPath + icon
        return cmds.menuItem(p=parent, l=label, i=icon, subMenu=1)
    
    def addSeparator(self):
        cmds.separator(st='shelf', w=12, hr=False)

    def _cleanOldShelf(self):
        '''Checks if the shelf exists and empties it if it does or creates it if it does not.'''
        if cmds.shelfLayout(self.name, ex=1):
            if cmds.shelfLayout(self.name, q=1, ca=1):
                for each in cmds.shelfLayout(self.name, q=1, ca=1):              
                    cmds.deleteUI(each)
        else:
            cmds.shelfLayout(self.name, p="ShelfLayout")