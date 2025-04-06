import bpy

"""
Thanks to this our changes in other modules are propagated after reload.
"""
if "bpy" in locals():
    import importlib
    if "actions_mixer" in locals():
        importlib.reload(actions_mixer)
    if "pixelart_renderer" in locals():
        importlib.reload(pixelart_renderer)


from . import actions_mixer
from . import pixelart_renderer

def register():
    actions_mixer.register()
    pixelart_renderer.register()


def unregister():
    actions_mixer.unregister()
    pixelart_renderer.unregister()


if __name__ == "__main__":
    register()