


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


class RendererOperator():
    def __init__(self) -> None:
        self.context = None
        self.scene = None
        self.emet_tool = None
        self.matselcoll = None
        self.camera = None
        self.camera_location_cache = None
        self.camera_rotation_cache = None
        self.output_directory = None
        self.output_tmp_directory = None
        self.output_tmp_filename = None
        self.PREFIX = "tmp_tiles"
        #self.scene.render.filepath = None
        self.render_out = []


    def render(self):
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

        # Render rotations
        for _ in range(0, self.emet_tool.rotations):
            # Rotate camera around it's Z axis
            self.camera.rotation_euler[2] += camera_rotation_angle

            # Rotate camera position vector
            x, y = self.camera.location.x, self.camera.location.y
            self.camera.location.x = x * math.cos(camera_rotation_angle) - y * math.sin(camera_rotation_angle)
            self.camera.location.y = x * math.sin(camera_rotation_angle) + y * math.cos(camera_rotation_angle)

            # Render
            bpy.ops.render.render(
                animation=self.emet_tool.isAnimated,
                write_still=True,
                use_viewport=False,
                layer='',
                scene=''
            )

            if self.emet_tool.isAnimated:
                current_tile = combine_frames(self.output_tmp_directory, self.PREFIX)
            else:
                current_tile = read_image(f"{self.output_tmp_filename}.png")

            # TODO: Maybe storing all these in RAM is not ideal if we got some large images and render is running
            # in the background. We could write intermediate horizontal sprites to the tmp directory
            self.render_out.append(current_tile)

        output = cv2.vconcat(self.render_out)
        filepath = os.path.join(self.output_directory, self.emet_tool.output_filename)
        cv2.imwrite(os.path.abspath(filepath), output)


    def _get_render_camera(self):
        cameras = [ob for ob in self.context.scene.objects if ob.type == 'CAMERA']
        if 1 != len(cameras):
            raise ValueError("There should only be one camera in the scene.")
        return cameras[0]


# TODO: Probably inheriting RendererOperator is pointless here, remove it and put everything here
class Emet_Render_Tiles_Operator(bpy.types.Operator, RendererOperator):
    bl_idname = "emet.emet_render_tiles_operator"
    bl_label = "Render Tiles"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Extract data from context
        self.context = context
        self.scene = context.scene
        self.emet_tool = self.scene.EmetTool
        self.matselcoll = self.scene.MatSelColl

        try:
            self._setup_camera()
            self._setup_filepaths()
        except:
            # We can return CANCELLED because we didn't modifiy Blender data
            return {"CANCELLED"}

        try:
            self.render()
            self._cleanup()
        except:
            # At this point Blender data is surely modified so return FINISHED
            return {"FINISHED"}

        return {'FINISHED'}


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

        # In this directory we will create a temp folder to store our outputs. It is inside output_directory.
        # It can't exist as it will be deleted during cleanup.
        self.output_tmp_directory = os.path.join(self.output_directory, f"tmp-render-{datetime.datetime.now()}")
        self.output_tmp_directory = os.path.abspath(self.output_tmp_directory)
        try:
            os.makedirs(self.output_tmp_directory, exist_ok=False)
        except FileExistsError:
            self.report({"ERROR"}, f"There already exists directory with the same name as temp directory: {self.output_tmp_directory}")

        # We set render filepath to temp directory + prefix. All intermediate tiles will be stored in temp directory,
        # with name prefix + tile number
        self.output_tmp_filename = os.path.abspath(os.path.join(self.output_tmp_directory, self.PREFIX))
        self.scene.render.filepath = self.output_tmp_filename


    def _cleanup(self):
        for tmp_file in os.listdir(self.output_tmp_directory):
            if not tmp_file.startswith(self.PREFIX):
                error_msg = f"Detected file not starting with \"{self.PREFIX}\" prefix: {tmp_file}"
                self.report({"ERROR"}, error_msg)
                raise RuntimeError(error_msg)
            filepath = os.path.join(self.output_tmp_directory, tmp_file)
            os.remove(filepath)
        os.rmdir(self.output_tmp_directory)


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
    Emet_Properties,
    Emet_Render_Tiles_Operator, Emet_Tiles_Panel,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.EmetTool = bpy.props.PointerProperty(type=Emet_Properties)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


