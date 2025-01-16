import bpy

"""
Thanks to this our changes in other modules are propagated after reload.
"""
if "bpy" in locals():
    import importlib
    if "pixelart_renderer" in locals():
        importlib.reload(pixelart_renderer)
    if "actions_mixer" in locals():
        importlib.reload(actions_mixer)
    if "material_selector" in locals():
        importlib.reload(material_selector)


from . import pixelart_renderer
from . import actions_mixer
from . import material_selector

def register():
    pixelart_renderer.register()
    actions_mixer.register()
    material_selector.register()


def unregister():
    pixelart_renderer.unregister()
    actions_mixer.unregister()
    material_selector.unregister()


if __name__ == "__main__":
    register()