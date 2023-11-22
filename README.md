# Autorigger

## Download

### Manual Download
1. Download the repository using `Code -> Download ZIP`.  
2. Extract the ZIP file and rename the extracted folder to `MayaRig`. Drag it into one of Maya's script folders.
3. Create an (empty) `__init__.py` file in the script folder if there isn't one already.

### Git
> Note: This method of installation makes it relatively easy to manage updates, but involves the command line. 
1. If you do not have git installed on your computer, install it.
2. Open one of Maya's scripts folder in a terminal or command line of some sort.
3. Enter the following command:
```bash
git clone git@github.com:camplowell/MayaRig.git
```
4. Create an (empty) `__init__.py` in the script folder if there isn't one already.

---

Maya's Scripts folder should now contain at least these two items:
> 📁 MayaRig  
> 📄 \_\_init\_\_.py

## Installing

Run the following python script in Maya's script editor:
```python 
import MayaRig
MayaRig.main()
```

A new shelf called MayaRig will be created, with all the things the utility can do.  

## Updating
Update the script with one of the following methods, then re-install using the Maya script.

### Manual Download
Re-download and replace the `MayaRig` folder in Maya's script folder

Then rerun the Maya script:
```python 
import MayaRig
MayaRig.main()
```
### Git
Open the `MayaRig` folder in a terminal.  
Enter the following command:
```bash
git pull
```
Then rerun the Maya script:
```python 
import MayaRig
MayaRig.main()
```

## Use

### Global Operations
#### Build
Build the controls and bind rig for the character.

#### Bind
TODO. Will eventually bind the character geometry to the bind rig and enter weight painting mode.

### Limb Creation
These buttons will spawn a menu, giving you more detailed options on what limb to create.

> Due to limitations in the API, you may have to click these buttons twice after restarting Maya.
> 
> To mitigate this issue, you can optionally add the installation script to the end of your `userSetup.py` file, usually found at `MAYA_APP_DIR/<version>/scripts`.

#### Torso
Builds the main torso for the rig. Currently available in the following varieties:
- FK: A torso rig with rotation-based controls.
- Simple: A CoG and a pelvis. That's it.


#### Leg
Builds rear limbs. Currently available in the following varieties:
- Humanoid: A humanoid leg. These can deal with shoes that have elevated toes!

#### Arm
Builds front limbs. Currently available in the following varieties:
- Humanoid: A humanoid arm with 5 fingers. The wrist orientation is kept, so keep that in mind!