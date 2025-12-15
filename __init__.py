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
    if "tile_mixer" in locals():
        importlib.reload(tile_mixer)
    if "environment_helper_utils" in locals():
        importlib.reload(tile_mixer)


from . import actions_mixer
from . import pixelart_renderer
from . import tile_mixer
from . import environment_helper_utils

def register():
    actions_mixer.register()
    pixelart_renderer.register()
    tile_mixer.register()
    environment_helper_utils.register()


def unregister():
    actions_mixer.unregister()
    pixelart_renderer.unregister()
    tile_mixer.unregister()
    environment_helper_utils.unregister()


if __name__ == "__main__":
    register()