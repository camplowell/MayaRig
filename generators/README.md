# Generators
Generators are responsible for creating the actual rig.

In order to play nice with the rest of the program, they need a few public methods.  
Here is a template for a generator:

```python
from maya import cmds
from typing import List
from ..core import *

name = "generator_name"

def create_menu():
    """Returns a layout containing:
    - Any options the generator needs to generate
    - A button that generates markers for the limb"""

def create_controllers(driver_joints:List[str]):
    """Generates controllers for the driver joints.
    May modify the structure of the driver skeleton."""

def create_bind_joints(driver_joints:List[str]):
    """Generates bind joints driven by the driver joints."""
```

When creating the marker joints, any joints with no parents inside the generator should be marked as root:

```python
joints.mark_root(marker, name, is_symmetrical)
```

This tells the code to delegate generation of controls back to you later.

## Modifying the Driver Bones
`generate_controllers` can modify the structure of the driver skeleton.  
However, any deleted driver bones **MUST** move its children to another joint before doing so.

This allows generators to parent limbs to one another without any guesswork.