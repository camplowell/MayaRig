from maya import cmds
from . import attributes
PALLETTE = {
    'shadow red':       (0.389, 0.040, 0.000),
    'shadow orange':    (0.498, 0.153, 0.000),
    'shadow yellow':    (0.517, 0.322, 0.000),
    'shadow green':     (0.294, 0.283, 0.000),
    'shadow aqua':      (0.000, 0.369, 0.298),
    'shadow blue':      (0.000, 0.247, 0.401),
    'shadow purple':    (0.455, 0.000, 0.329),

    'midtone red':       (0.616, 0.000, 0.024),
    'midtone orange':    (0.686, 0.227, 0.012),
    'midtone yellow':    (0.710, 0.463, 0.078),
    'midtone green':     (0.475, 0.456, 0.000),
    'midtone aqua':      (0.000, 0.498, 0.403),
    'midtone blue':      (0.000, 0.379, 0.639),
    'midtone purple':    (0.664, 0.084, 0.492),

    'highlight red':    (1.000, 0.094, 0.086),
    'highlight orange': (1.000, 0.300, 0.082),
    'highlight yellow': (0.995, 0.736, 0.000),
    'highlight green':  (0.556, 0.724, 0.000),
    'highlight aqua':   (0.000, 0.766, 0.505),
    'highlight blue':   (0.444, 0.618, 1.000),
    'highlight purple': (1.000, 0.397, 0.603),
}

def set_(obj:str, color):
    if isinstance(color, tuple):
        return cmds.color(obj, rgb=color)
    if isinstance(color, int):
        return cmds.color(obj, ud=color)
    return cmds.color(obj, rgb=PALLETTE[color])
    