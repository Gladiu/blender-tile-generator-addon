# Blender Tile Generation Addon

TODOs:

- [ ] Remove OpenCV as dependency
  - Same functionality probably can be achieved with Numpy (by default in Blender's Python release) and Blender's native file saving functionality
  - See some usefull links for image saving with Blender [here](https://stackoverflow.com/questions/14982836/rendering-and-saving-images-through-blender-python) and [here](https://blender.stackexchange.com/questions/202145/how-do-you-save-texture-as-an-image-to-disk-with-python)
- [ ] Add a button to create material for normal map rendering
  - This could be done if there was a way to separate normal map from final shader just before it connects to Material Output Node
