import bpy
import math
import random
import datetime

# ------------------------------------------------------------------------
#   Combine output images
# ------------------------------------------------------------------------

import cv2
from pathlib import Path
import os
import numpy as np


def combine_frames(inputPath, prefix):
    # Get everything that is a file and starts with prefix from inputPath
    filepaths = []
    for f in os.listdir(inputPath):
        fp = os.path.join(inputPath, f)
        if not os.path.isfile(fp) or not f.startswith(prefix):
            continue
        filepaths.append(fp)
    filepaths.sort()

    images = [cv2.imread(filepath, cv2.IMREAD_UNCHANGED) for filepath in filepaths]
    return cv2.hconcat(images)


def read_image(inputPath):
    path = Path(f"{inputPath}")

    if path.is_file() == False:
        return

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return image


class Emet_Properties(bpy.types.PropertyGroup):
    isAnimated : bpy.props.BoolProperty(
        name = "Is Animated?",
        description="Is tile animated",
        default = False,
    )

    output_directory: bpy.props.StringProperty(
        name = "Output directory",
        description="Choose output directory",
        default = ".",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    output_filename: bpy.props.StringProperty(
        name="Output file name",
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


class Emet_Render_Tiles_Operator(bpy.types.Operator):
    bl_idname = "emet.emet_render_tiles_operator"
    bl_label = "Render Tiles"
    bl_options = {'REGISTER', 'UNDO'}


    def __init__(self) -> None:
        self.context = None
        self.scene = None
        self.emet_tool = None
        self.matselcoll = None
        self.actions_prop_coll = None
        self.camera = None
        self.camera_location_cache = None
        self.camera_rotation_cache = None
        self.output_directory = None
        self.output_tmp_directory = None
        self.output_tmp_tiles_directory = None
        self.output_tmp_strips_directory = None
        self.output_tmp_filename = None
        self.TILE_PREFIX = "tmp_tile"
        self.STRIP_PREFIX = "tmp_hstrip"
        self.render_out = []


    def execute(self, context):
        # Extract data from context
        self.context = context
        self.scene = context.scene
        self.emet_tool = self.scene.EmetTool
        self.matselcoll = self.scene.MatSelColl
        self.actions_prop_coll = self.scene.ActionsPropColl

        try:
            self._setup_camera()
            self._setup_filepaths()
        except:
            # We can return CANCELLED because we didn't modifiy Blender data
            return {"CANCELLED"}

        try:
            self._render()
            os.rmdir(self.output_tmp_directory)
            self.camera.location = self.camera_location_cache
            self.camera.rotation_euler = self.camera_rotation_cache
        except Exception as e:
            self.report({"ERROR"}, str(e))
            # At this point Blender data is surely modified so return FINISHED
            return {"FINISHED"}

        return {'FINISHED'}


    def _render(self):
        # Apply materials
        for member in self.matselcoll:
            obj = bpy.context.scene.objects[member.name]
            mat = bpy.data.materials[member.active_index_mat]
            obj.data.materials[0] = mat

        # Setup camera
        x, y = self.camera.location.x, self.camera.location.y
        camera_vector_mag = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
        self.camera.location.x = camera_vector_mag * 1 # Yes this is very verbose - sue me
        self.camera.location.y = 0
        self.camera.rotation_euler[2] = math.pi / 2
        camera_rotation_angle = math.pi * 2.0 / self.emet_tool.rotations

        # Main rendering loop
        for member in self.matselcoll:
            obj = bpy.context.scene.objects[member.name]
            mat = bpy.data.materials[member.active_index_mat]

        for actions_mixer_row in self.actions_prop_coll:
            is_animated = self._set_animations(actions_mixer_row)
            # Render rotations
            for _ in range(0, self.emet_tool.rotations):
                # Rotate camera around it's Z axis
                self.camera.rotation_euler[2] += camera_rotation_angle

                # Rotate camera position vector
                x, y = self.camera.location.x, self.camera.location.y
                self.camera.location.x = x * math.cos(camera_rotation_angle) - y * math.sin(camera_rotation_angle)
                self.camera.location.y = x * math.sin(camera_rotation_angle) + y * math.cos(camera_rotation_angle)

                self._render_hstrip(is_animated)
                self._tiles_cleanup()

        # Save to sprite sheet
        self._hstrips_stack()
        self._hstrips_cleanup()


    def _hstrips_stack(self):
        strips_files = os.listdir(self.output_tmp_strips_directory)
        strips_files.sort(key=lambda x: int(x.replace(self.STRIP_PREFIX, "").replace(".png", "")))
        strips = [cv2.imread(os.path.join(self.output_tmp_strips_directory, filename), cv2.IMREAD_UNCHANGED) for filename in strips_files]
        max_w = 0
        for strip in strips:
            if strip.shape[1] > max_w:
                max_w = strip.shape[1]
        for i, strip in enumerate(strips):
            h, w, d = strip.shape
            blank = np.zeros((h, max_w, d), strip.dtype)
            blank[0:h, 0:w] = strip
            strips[i] = blank
        cv2.imwrite(os.path.join(self.output_directory, self.emet_tool.output_filename), cv2.vconcat(strips))


    def _set_animations(self, actions_mixer_row):
        character_armature = self.scene.CharacterPointer
        prop_armature = self.scene.PropPointer
        is_animated = False
        character_frame_end = 0
        prop_frame_end = 0
        if actions_mixer_row.character_action_name in bpy.data.actions \
                and actions_mixer_row.character_action_name != "None" \
                and character_armature.animation_data != None:
            character_armature.animation_data.action = bpy.data.actions[actions_mixer_row.character_action_name]
            character_frame_end = bpy.data.actions[actions_mixer_row.character_action_name].frame_end
            is_animated = True
        if actions_mixer_row.prop_action_name in bpy.data.actions \
                and actions_mixer_row.prop_action_name != "None" \
                and prop_armature.animation_data != None:
            prop_armature.animation_data.action = bpy.data.actions[actions_mixer_row.prop_action_name]
            prop_frame_end = bpy.data.actions[actions_mixer_row.prop_action_name].frame_end
            is_animated = True

        if is_animated:
            self.scene.frame_start = 1
            self.scene.frame_end = int(character_frame_end if character_frame_end > prop_frame_end else prop_frame_end)

        return is_animated


    def _render_hstrip(self, is_animated):
        bpy.ops.render.render(
            animation=is_animated,
            write_still=True,
            use_viewport=False,
            layer='',
            scene=''
        )

        hstrip = combine_frames(self.output_tmp_tiles_directory, self.TILE_PREFIX)
        hstrip_name = self.STRIP_PREFIX + str(len(os.listdir(self.output_tmp_strips_directory))) + ".png"
        hstrip_path = os.path.join(self.output_tmp_strips_directory, hstrip_name)
        cv2.imwrite(hstrip_path, hstrip)


    def _get_render_camera(self):
        cameras = [ob for ob in self.context.scene.objects if ob.type == 'CAMERA']
        if 1 != len(cameras):
            error_msg = "There should only be one camera in the scene."
            self.report({"ERROR"}, error_msg)
            raise ValueError(error_msg)
        return cameras[0]


    def _setup_camera(self):
        self.camera = self._get_render_camera()
        self.camera_location_cache = self.camera.location
        self.camera_rotation_cache = self.camera.rotation_euler


    def _setup_filepaths(self):
        # User provides output directory, which **must** exist. Here will be the output file placed
        if not os.path.exists(self.emet_tool.output_directory):
            error_msg = f"Output directory: {self.emet_tool.output_directory} does not exist!"
            self.report({"ERROR"}, error_msg)
            raise RuntimeError(error_msg)
        self.output_directory = os.path.abspath(self.emet_tool.output_directory)

        # Create temporary directory to store outputs. It will contain two subdirectories to store tiles and strips
        # separately, to ease joining them together later
        self.output_tmp_directory = os.path.join(self.output_directory, f"tmp-render-{datetime.datetime.now()}")
        self.output_tmp_directory = os.path.abspath(self.output_tmp_directory)
        self.output_tmp_tiles_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "tiles"))
        self.output_tmp_strips_directory = os.path.abspath(os.path.join(self.output_tmp_directory, "strips"))
        try:
            os.makedirs(self.output_tmp_directory, exist_ok=False)
            os.makedirs(self.output_tmp_strips_directory, exist_ok=False)
            os.makedirs(self.output_tmp_tiles_directory, exist_ok=False)
        except FileExistsError:
            self.report({"ERROR"}, f"Could not create temp directories")

        # We set render filepath to temp tiles directory + prefix. All intermediate tiles will be stored in temp directory,
        # with name prefix + tile number
        self.output_tmp_filename = os.path.abspath(os.path.join(self.output_tmp_tiles_directory, self.TILE_PREFIX))
        self.scene.render.filepath = self.output_tmp_filename


    def _hstrips_cleanup(self):
        self._cleanup(self.output_tmp_strips_directory, self.STRIP_PREFIX)


    def _tiles_cleanup(self):
        self._cleanup(self.output_tmp_tiles_directory, self.TILE_PREFIX)


    def _cleanup(self, path, prefix):
        for tmp_file in os.listdir(path):
            if not tmp_file.startswith(prefix):
                error_msg = f"Detected file not starting with \"{prefix}\" prefix: {tmp_file}"
                self.report({"ERROR"}, error_msg)
                raise RuntimeError(error_msg)
            filepath = os.path.join(path, tmp_file)
            os.remove(filepath)
        os.rmdir(path)


class Emet_Tiles_Panel(bpy.types.Panel):
    bl_label = "Tiles"
    bl_category = "Emet Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        EmetTool = scene.EmetTool

        layout.label(text="Select objects to pick materials")
        layout.prop(EmetTool, "rotations")
        layout.prop(EmetTool, "isAnimated")
        layout.prop(EmetTool, "output_filename")
        layout.prop(EmetTool, "output_directory")

        layout.operator(Emet_Render_Tiles_Operator.bl_idname, text="Render Tiles", icon="SCENE")


classes = [
    Emet_Properties, Emet_Render_Tiles_Operator, Emet_Tiles_Panel,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.EmetTool = bpy.props.PointerProperty(type=Emet_Properties)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


