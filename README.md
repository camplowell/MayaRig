# Autorigger
<link href="https://cdn.jsdelivr.net/npm/remixicon@3.2.0/fonts/remixicon.css" rel="stylesheet">
<style>
    .box {
        padding-left:16px;
        padding-right:16px;
        padding-top:8px;
        padding-bottom:8px;
        background-color: rgba(128, 128, 128, 0.125);
        border-radius:4px
    }
</style>
## Installation
Drag the repository folder into one of Maya's script folders.
Ensure the script folder itself contains an `__init__.py` file.

<div class="box">
<i class="ri-folder-3-line"></i> MayaRig

<i class="ri-file-code-line"></i> \_\_init\_\_.py
</div>

## Use
To run, execute the following commands:
```python
import MayaRig
MayaRig.main()
```
You can save it into your hotbar to have faster access to the script.

### Main Menu
Create a new character or load an existing character using its marker group.  
If a marker group is already selected when the script is run, it will directly open the edit window.

### Editor
Select a type of limb to create.
The rigger can then place the generated joints and parent the limbs to each other.  
Once you are done, press `Create Metarig` to (re)generate a rig based on the marker joints.

## Limb Types

### Simple
Creates an FK joint chain with circle controllers.
Leaves marker orientations intact.

### Arm
Creates an arm with an FK/IK switch.
Re-orients all markers except the wrist, and automatically places a pole vector control.

### Leg
Creates a humanoid leg with a reverse foot and an FK/IK switch.
Re-orients all markers, and automatically places a pole vector control.

## Layers of the Rig

### Control layer
Animators interact with the rig through controls. These should normally appear as curves.

### Driver Layer
Driver joints form the simplest rig that can fully represent the pose of the character.

### Bind Layer
Bind joints control the deformation of the character, and should be controlled using constraints such that FBX export works properly.

## Naming conventions
General format: `[initial]_([l/r]_)[bone]_[suffix]`
### Suffixes
markers: `marker`

#### Joints
Bind: `bindJoint`
IK: `ikJoint`
FK: `fkJoint`
Driver: `driverJoint`

#### Controls
IK: `ik`
FK: `fk`
Tweak: `tweak`
Default: `[none]`

#### Other
IK inverter: `ikInvert`