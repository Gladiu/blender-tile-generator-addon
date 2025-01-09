import bpy


if "bpy" in locals():
    import importlib
    if "pixelart_renderer" in locals():
        importlib.reload(pixelart_renderer)
    if "actions_mixer" in locals():
        importlib.reload(actions_mixer)


from . import pixelart_renderer
from . import actions_mixer

def register():
    pixelart_renderer.register()
    actions_mixer.register()


def unregister():
    pixelart_renderer.unregister()
    actions_mixer.unregister()


if __name__ == "__main__":
    register()