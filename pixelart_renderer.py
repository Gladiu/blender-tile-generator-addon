import bpy
import math
from copy import deepcopy
import datetime

# ------------------------------------------------------------------------
#   Combine output images
# ------------------------------------------------------------------------

import cv2
from pathlib import Path
import os
import numpy as np

# Globuls
animation_render = "0"
tile_render = "1"

def return_smaller_affix(x, prefix):
    # Cutting out: prefix, .png
    # This leaves only number to be compared
    return int(x[len(prefix):-4])

def combine_frames(inputPath, prefix):
    # Get everything that is a file and starts with prefix from inputPath
    filepaths = []
    if len(os.listdir(inputPath)) == 0:
        return []
    files = []
    for f in os.listdir(inputPath):
        fp = os.path.join(inputPath, f)
        if not os.path.isfile(fp) or not f.startswith(prefix):
            continue
        files.append(f)
    files.sort(key = lambda x:  return_smaller_affix(x, prefix))
    # Add back .png
    # This slicing of string could have been avoided if i bothered to write better sorting of paths
    for f in files:
        filepaths.append(os.path.join(inputPath, str(f)))

    images = [cv2.imread(filepath, cv2.IMREAD_UNCHANGED) for filepath in filepaths]
    return cv2.hconcat(images)


def read_image(inputPath):
    path = Path(f"{inputPath}")

    if path.is_file() == False:
        return

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return image

class EMET_properties(bpy.types.PropertyGroup):

    enable_bg_fg_render: bpy.props.BoolProperty(
        name="Foreground & background render",# Name is described in label above
        description="IN GEOMETRY NODES Divide render result for foreground and background render",
    )

    output_directory: bpy.props.StringProperty(
        name = "",# Name is described in label above
        description="Choose output directory",
        default = ".",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    output_filename: bpy.props.StringProperty(
        name="",# Name is described in label above
        description="Output file prefix",
        default="output.png",
        maxlen=1024,
        subtype='FILE_NAME'
    )

    rotations : bpy.props.IntProperty(
        name = "Rotations",
        description="How many rotations around Z axis do you want to render",
        default = 8,
        min = 1,
        max = 8
    )
    render_types = [
                (animation_render,"Animation Render","Animation Render"),
                (tile_render,"Tile Render","Tile Render"),
                ]

    selected_render: bpy.props.EnumProperty(name="", # Name is described in label above
                                     description="Selected Render Mode",
                                     default="0",
                                     items=render_types)


def set_bool_in_objects_geometry_nodes(object, bool_name, value):
    if 'GeometryNodes' in object.modifiers.keys():
        nodes = object.modifiers['GeometryNodes'].node_group.nodes
        for node_key in nodes.keys():
            if nodes[node_key].label == bool_name:
                enable_in_shadow_render = nodes[node_key]
                enable_in_shadow_render.boolean = value
                return
    else:
        raise ValueError("No Geometry Nodes in object!")

def set_bool_in_geometry_nodes(geometry_nodes, bool_name, value):
    geometry_nodes = geometry_nodes.nodes
    for node_key in geometry_nodes.keys():
        if geometry_nodes[node_key].label == bool_name:
            enable_in_shadow_render = geometry_nodes[node_key]
            enable_in_shadow_render.boolean = value

def set_set_material_params_geometry_nodes(object, set_material_name, mute_value, default_material):
    if 'GeometryNodes' in object.modifiers.keys():
        nodes = object.modifiers['GeometryNodes'].node_group.nodes
        for node_key in nodes.keys():
            if nodes[node_key].label == set_material_name:
                shadow_material_setter = nodes[node_key]
                shadow_material_setter.mute = mute_value
                if default_material != None:
                    shadow_material_setter.inputs['Material'].default_value = default_material
                return
    else:
        raise ValueError("No Geometry Nodes in object!")
        
def set_holdout_to_object(object, holdout_state):
    if object.type == 'ARMATURE':
        for child in object.children:
            child.is_holdout = holdout_state
    else:
        object.is_holdout = holdout_state

def make_all_renders_same_width(render_array):
    # Shaping different sizes of strips to have same size
    max_w = 0
    for py_strip in render_array:
        strip = np.asarray(deepcopy(py_strip))
        if strip.shape[1] > max_w:
            max_w = strip.shape[1]
    for i, strip in enumerate(render_array):
        strip =  np.asarray(strip)
        h, w, d = strip.shape
        blank = np.zeros((h, max_w, d), strip.dtype)
        blank[0:h, 0:w] = strip
        render_array[i] = blank

class EMET_OT_render_tiles_operator(bpy.types.Operator):
    bl_idname =  "emet.render_tiles_operator"
    bl_label = "Render"
    bl_options = {'REGISTER', 'UNDO'}

    context = None
    scene = None
    emet_tool = None
    actions_prop_coll = None
    camera = None
    camera_location_cache = None
    camera_rotation_cache = None
    output_directory = None
    output_tmp_directory = None
    output_tmp_tiles_directory = None
    output_tmp_strips_directory = None
    output_tmp_background_directory = None
    output_tmp_shadow_directory = None
    output_tmp_foreground_directory = None
    output_tmp_filename = None
    TILE_PREFIX = "tmp_tile"
    STRIP_PREFIX = "tmp_hstrip"
    render_out = []


    def execute(self, context):
        # Extract data from context
        self.context = context
        self.scene = context.scene
        self.emet_tool = self.scene.EmetTool
        self.actions_prop_coll = self.scene.ActionsPropColl
        try:
            self._setup_camera()
            self._setup_filepaths()
        except:
            # We can return CANCELLED because we didn't modifiy Blender data
            return {"CANCELLED"}

        try:
            if self.emet_tool.selected_render == animation_render:
                self._render_animation()
                #os.rmdir(self.output_tmp_directory)
            elif self.emet_tool.selected_render == tile_render:
                self._render_tile()
                #os.rmdir(self.output_tmp_directory)
            
            current_camera = self._get_render_camera()
            current_camera.location = self.camera_location_cache
            current_camera.rotation_euler = self.camera_rotation_cache
        except Exception as e:
            self.report({"ERROR"}, str(e))
            # At this point Blender data is surely modified so return FINISHED
            return {"FINISHED"}

        return {'FINISHED'}


    def _render_tile(self):
        foreground_affix = self.scene.TileMixer.foreground_affix 
        background_affix = self.scene.TileMixer.background_affix 
        object_dict = self.context.scene.TileCollectionPointer.objects

        tile_dict = {} # Its key is tile index, and its value is name are objects belonging to this index
        # This entire mental gymnastic is to allow multi character number to be an index
        # As well as to allow trailing numbers in tile names
        for key in object_dict.keys():
            currently_parsed_key = ""
            for char in key:
                currently_parsed_key = currently_parsed_key + char
                if len(currently_parsed_key) > 0 and currently_parsed_key.isdigit() == False:
                    # Get to the point where our string was a number
                    currently_parsed_key = currently_parsed_key[:-1]
                    if currently_parsed_key == '':
                        continue

                    currently_parsed_index = int(currently_parsed_key)
                    if currently_parsed_index not in tile_dict.keys():
                        tile_dict[currently_parsed_index] = []
                    # We dont check if value exists in this array since its impossible to have 2 same names in blender
                    tile_dict[currently_parsed_index].append(object_dict[key])
                    break
        
        # Now we have a dictionary where key is index, and value are names of the nodes to render

        # Sort by key
        tile_dict = dict(sorted(tile_dict.items()))

        # Hide all objects
        for key in tile_dict.keys():
            current_tile = tile_dict[key]
            for object in current_tile:
                object.hide_render = True
        # Render 
        for key in tile_dict.keys():
            current_tile = tile_dict[key]
            for object in current_tile:
                object.hide_render = False
                # Move camera position vector
                object_x = object.location.x
                object_y = object.location.y
                self.camera.location.x = self.camera_location_cache.x + object_x 
                self.camera.location.y = self.camera_location_cache.y + object_y 

                # Lets determine if we render Background or foreground
                if background_affix in object.name:
                    for temp_object in current_tile:
                        if 'GeometryNodes' in temp_object.modifiers.keys():
                            set_bool_in_objects_geometry_nodes(temp_object, 'enable_in_background_render', True)
                    self.scene.render.filepath = os.path.abspath(os.path.join(self.output_tmp_background_directory, str(key)))
                    
                if foreground_affix in object.name:
                    for temp_object in current_tile:
                        if 'GeometryNodes' in temp_object.modifiers.keys():
                            set_bool_in_objects_geometry_nodes(temp_object, 'enable_in_foreground_render', True)
                    self.scene.render.filepath = os.path.abspath(os.path.join(self.output_tmp_foreground_directory, str(key)))

                bpy.ops.render.render(animation=False, write_still=True, use_viewport=False, layer='', scene='')
                
                # Cleanup
                if background_affix in object.name:
                    for temp_object in current_tile:
                        if 'GeometryNodes' in temp_object.modifiers.keys():
                            set_bool_in_objects_geometry_nodes(temp_object, 'enable_in_background_render', False)
                    
                if foreground_affix in object.name:
                    for temp_object in current_tile:
                        if 'GeometryNodes' in temp_object.modifiers.keys():
                            set_bool_in_objects_geometry_nodes(temp_object, 'enable_in_foreground_render', False)

                object.hide_render = True

        for key in tile_dict.keys():
            current_tile = tile_dict[key]
            for object in current_tile:
                object.hide_render = False

        render_array = []

        background_renders = []
        foreground_renders = []
        background_renders = combine_frames( self.output_tmp_background_directory, '')
        if len(background_renders) != 0:
            render_array.append(background_renders)

        foreground_renders = combine_frames( self.output_tmp_foreground_directory, '')
        if len(foreground_renders) != 0:
            render_array.append(foreground_renders)

        cv2.imwrite(os.path.join(self.output_directory, self.emet_tool.output_filename), cv2.vconcat(render_array))


    def _render_animation(self):

        render_object = self.scene.CharacterPointer
        bg_fg_enabled = self.emet_tool.enable_bg_fg_render
    
        # We set render filepath to temp tiles directory + prefix. All intermediate tiles will be stored in temp directory,
        # with name prefix + tile number
        self.output_tmp_filename = os.path.abspath(os.path.join(self.output_tmp_tiles_directory, self.TILE_PREFIX))
        self.scene.render.filepath = self.output_tmp_filename
        
        for actions_mixer_row in self.actions_prop_coll:
            prop_name = actions_mixer_row.prop_for_action_name
            if prop_name != 'None': # KURWAAAAAA BLENDER HAS 'None' and None  # KURWAAA its not blender, its us in @ref action_mixer.py
                bpy.data.objects[prop_name].hide_render = True

        render_types = ['Single Render']
        if bg_fg_enabled:
            render_types = ['Background', 'Foreground', 'Prop' ]
            # Reset Everything
            for node in bpy.data.node_groups:
                    set_bool_in_geometry_nodes(node, 'enable_in_background_render', False)
                    set_bool_in_geometry_nodes(node, 'enable_in_foreground_render', False)

        # We will store background render and foreground renders here

        # TODO: Add option to split background and foreground to different files 
        render_target = []
        # Key is prop name/file name and value is animation 
        render_target_prop_anim = {} # Render target animation that has prop will be rendered separately
        render_prop_anim = {} # Prop doing animation on its own
        render_wearable = {}

        # Main Loop
        for render_type in render_types:

            for node in bpy.data.node_groups:
                if render_type == 'Background':
                    set_bool_in_geometry_nodes(node, 'enable_in_background_render', True)
                if render_type == 'Foreground':
                    set_bool_in_geometry_nodes(node, 'enable_in_foreground_render', True)
                if render_type == 'Prop':
                    set_bool_in_geometry_nodes(node, 'enable_in_background_render', True)
                    set_bool_in_geometry_nodes(node, 'enable_in_foreground_render', True)
            if render_type == 'Prop':
                set_holdout_to_object(render_object, True)
            wearable_dict = self.context.scene.WearableCollectionPointer.objects
            for key in wearable_dict.keys():
                wearable = wearable_dict[key]
                wearable.hide_render = True

            # Setup camera
            x, y = self.camera.location.x, self.camera.location.y
            camera_vector_mag = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
            self.camera.location.x = camera_vector_mag * 1 # Yes this is very verbose - sue me # Its cute but it wont stop my sphagetti
            self.camera.location.y = 0
            self.camera.rotation_euler[2] = math.pi / 2
            camera_rotation_angle = math.pi * 2.0 / self.emet_tool.rotations

            for actions_mixer_row in self.actions_prop_coll:
                is_animated = self._set_animations(actions_mixer_row)
                if actions_mixer_row.prop_for_action_name != 'None':
                    current_prop = bpy.data.objects[actions_mixer_row.prop_for_action_name]
                    if current_prop.name not in render_target_prop_anim.keys():
                        render_target_prop_anim[current_prop.name] = []
                        render_prop_anim[current_prop.name] = []


                # Render rotations
                for _ in range(0, self.emet_tool.rotations):
                    # Rotate camera around it's Z axis
                    self.camera.rotation_euler[2] += camera_rotation_angle

                    # Rotate camera position vector
                    x, y = self.camera.location.x, self.camera.location.y
                    self.camera.location.x = x * math.cos(camera_rotation_angle) - y * math.sin(camera_rotation_angle)
                    self.camera.location.y = x * math.sin(camera_rotation_angle) + y * math.cos(camera_rotation_angle)

                    if render_type != 'Prop':
                        # Render H strip
                        bpy.ops.render.render(
                            animation=is_animated,
                            write_still=True,
                            use_viewport=False,
                            layer='',
                            scene=''
                        )

                        if actions_mixer_row.prop_for_action_name != 'None':
                            # Save prop animation to different buffer
                            hstrip = combine_frames(self.output_tmp_tiles_directory, self.TILE_PREFIX)
                            render_target_prop_anim[actions_mixer_row.prop_for_action_name].append(hstrip)

                            # Now render for the prop alone
                            current_prop = bpy.data.objects[actions_mixer_row.prop_for_action_name]
                            current_prop.hide_render = False

                            set_holdout_to_object(render_object, True)
                            bpy.ops.render.render(
                                animation=is_animated,
                                write_still=True,
                                use_viewport=False,
                                layer='',
                                scene=''
                            )
                            current_prop.hide_render = True
                            set_holdout_to_object(render_object, False)
                            hstrip = combine_frames(self.output_tmp_tiles_directory, self.TILE_PREFIX)
                            render_prop_anim[actions_mixer_row.prop_for_action_name].append(hstrip)
                            self._cleanup(self.output_tmp_tiles_directory, self.TILE_PREFIX)
                        else:
                            hstrip = combine_frames(self.output_tmp_tiles_directory, self.TILE_PREFIX)
                            render_target.append(hstrip)   
                            self._cleanup(self.output_tmp_tiles_directory, self.TILE_PREFIX)

                    if render_type == 'Prop':
                        wearable_dict = self.context.scene.WearableCollectionPointer.objects
                        for key in wearable_dict.keys():
                            wearable = wearable_dict[key]
                            wearable.hide_render = False
                            bpy.ops.render.render(
                                animation=is_animated,
                                write_still=True,
                                use_viewport=False,
                                layer='',
                                scene=''
                            )
                            if wearable.name not in render_wearable.keys():
                                render_wearable[wearable.name] = []
                            wearable.hide_render = True
                            hstrip = combine_frames(self.output_tmp_tiles_directory, self.TILE_PREFIX)
                            render_wearable[key].append(hstrip)
                            self._cleanup(self.output_tmp_tiles_directory, self.TILE_PREFIX)


            # Unset all nodes variables and all holdouts
            for node in bpy.data.node_groups:
                if render_type == 'Background':
                    set_bool_in_geometry_nodes(node, 'enable_in_background_render', False)
                if render_type == 'Foreground':
                    set_bool_in_geometry_nodes(node, 'enable_in_foreground_render', False)
            if render_type == 'Prop':
                set_holdout_to_object(render_object, False)
                wearable_dict = self.context.scene.WearableCollectionPointer.objects
                for key in wearable_dict.keys():
                    wearable = wearable_dict[key]
                    wearable.hide_render = False

        make_all_renders_same_width(render_target)
        render_target = cv2.vconcat(render_target)

        # Finally concatenating everything into one strip
        
        cv2.imwrite(os.path.join(self.output_directory, self.emet_tool.output_filename), render_target)
        for key in render_target_prop_anim.keys():
            if key != 'None':
                current_array = render_target_prop_anim[key]
                make_all_renders_same_width(current_array)
                current_array = cv2.vconcat(current_array)
                file_name = self.emet_tool.output_filename[:-4] + "_" + str(key) + ".png"
                cv2.imwrite(os.path.join(self.output_directory, file_name), current_array)

        for key in render_prop_anim.keys():
            if key != 'None':
                current_array = render_prop_anim[key]
                make_all_renders_same_width(current_array)
                current_array = cv2.vconcat(current_array)
                file_name = str(key) + ".png"
                cv2.imwrite(os.path.join(self.output_directory, file_name), current_array)

        for key in render_wearable.keys():
            if key != 'None':
                current_array = render_wearable[key]
                make_all_renders_same_width(current_array)
                current_array = cv2.vconcat(current_array)
                file_name = str(key) + ".png"
                cv2.imwrite(os.path.join(self.output_directory, file_name), current_array)
            
        
    def _set_animations(self, actions_mixer_row):
        character_armature = self.scene.CharacterPointer
        is_animated = False
        character_frame_end = 0
        prop_frame_end = 0
        if character_armature.type != 'ARMATURE' \
                and actions_mixer_row.character_action_name in bpy.data.actions \
                and actions_mixer_row.character_action_name != "None":
            is_animated = True
            character_frame_end = bpy.data.actions[actions_mixer_row.character_action_name].frame_end
        elif actions_mixer_row.character_action_name in bpy.data.actions \
                and actions_mixer_row.character_action_name != "None" \
                and character_armature.animation_data != None:
            character_armature.animation_data.action = bpy.data.actions[actions_mixer_row.character_action_name]
            character_frame_end = bpy.data.actions[actions_mixer_row.character_action_name].frame_end
            is_animated = True

        if is_animated:
            self.scene.frame_start = 1
            self.scene.frame_end = int(character_frame_end if character_frame_end > prop_frame_end else prop_frame_end)
        return is_animated

    def _get_render_camera(self):
        cameras = [ob for ob in self.context.scene.objects if ob.type == 'CAMERA']
        if 1 != len(cameras):
            error_msg = "There should only be one camera in the scene."
            self.report({"ERROR"}, error_msg)
            raise ValueError(error_msg)
        return cameras[0]


    def _setup_camera(self):
        self.camera = self._get_render_camera()
        self.camera_location_cache = deepcopy(self.camera.location)
        self.camera_rotation_cache = deepcopy(self.camera.rotation_euler)


    def _setup_filepaths(self):
        # User provides output directory, which **must** exist. Here will be the output file placed
        if not os.path.exists(self.emet_tool.output_directory):
            error_msg = f"Output directory: {self.emet_tool.output_directory} does not exist!"
            self.report({"ERROR"}, error_msg)
            raise RuntimeError(error_msg)
        self.output_directory = os.path.abspath(self.emet_tool.output_directory)

        # Create temporary directory to store outputs. It will contain two subdirectories to store tiles and strips
        # separately, to ease joining them together later
        self.output_tmp_directory = os.path.join(self.output_directory, f"tmp-render-{datetime.datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}")
        self.output_tmp_directory = os.path.abspath(self.output_tmp_directory)
        self.output_tmp_tiles_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "tiles"))
        self.output_tmp_strips_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "strips"))
        self.output_tmp_background_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "background"))
        self.output_tmp_shadow_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "shadow"))
        self.output_tmp_foreground_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "foreground"))
        try:
            os.makedirs(self.output_tmp_directory, exist_ok=False)
            os.makedirs(self.output_tmp_strips_directory, exist_ok=False)
            os.makedirs(self.output_tmp_tiles_directory, exist_ok=False)
            os.makedirs(self.output_tmp_background_directory, exist_ok=False)
            os.makedirs(self.output_tmp_shadow_directory, exist_ok=False)
            os.makedirs(self.output_tmp_foreground_directory, exist_ok=False)
        except:
            self.report({"ERROR"}, f"Could not create temp directories")

    def _tiles_cleanup(self):
        self._cleanup(self.output_tmp_background_directory, self.TILE_PREFIX)
        self._cleanup(self.output_tmp_foreground_directory, self.TILE_PREFIX)
        self._cleanup(self.output_tmp_tiles_directory, self.TILE_PREFIX)


    def _cleanup(self, path, prefix):
        for tmp_file in os.listdir(path):
            if not tmp_file.startswith(prefix):
                error_msg = f"Detected file not starting with \"{prefix}\" prefix: {tmp_file}"
                self.report({"ERROR"}, error_msg)
                raise RuntimeError(error_msg)
            filepath = os.path.join(path, tmp_file)
            os.remove(filepath)
        #os.rmdir(path)


class EMET_PT_tiles(bpy.types.Panel):
    bl_label = "Renderer Panel"
    bl_category = "Emet Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        EmetTool = scene.EmetTool

        layout.prop(EmetTool, "rotations")
        layout.prop(EmetTool, "enable_bg_fg_render")
        # Commenting this out, maybe this will be usefull in future
        #layout.label(text="Shadow Catcher Material")
        #layout.prop(context.scene , "ShadowMaterialPointer" , text="")
        #layout.label(text="Transparent Material")
        #layout.prop(context.scene , "TransparentMaterialPointer" , text="")
        layout.label(text="Output File name")
        layout.prop(EmetTool, "output_filename")
        layout.label(text="Output Directory")
        layout.prop(EmetTool, "output_directory")
        layout.label(text="Selected Render Type")
        layout.prop(EmetTool, "selected_render")

        layout.operator(EMET_OT_render_tiles_operator.bl_idname, text="Render", icon="SCENE")


classes = [
    EMET_properties, EMET_OT_render_tiles_operator, EMET_PT_tiles,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.EmetTool = bpy.props.PointerProperty(type=EMET_properties)
    bpy.types.Scene.ShadowMaterialPointer  = bpy.props.PointerProperty(type=bpy.types.Material)
    bpy.types.Scene.TransparentMaterialPointer  = bpy.props.PointerProperty(type=bpy.types.Material)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


