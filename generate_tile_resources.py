bl_info = {
    "name": "Emet Tools",
    "author": "Maurycy Kujawski, Jakub Szukała",
    "version": (2, 0),
    "blender": (4, 1, 0),
    "location": "View3D > Sidebar > Example tab",
    "description": "Example with multiple panels",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"}
# README
# TO INSTALL OPENCV IN BLENDER
# Go to blender python directory and run those commands to install opencv
# ./python3.5m -m ensurepip
# ./python3.5m -m pip install --upgrade pip
# ./python3.5m -m pip install opencv-python


import bpy
import math
import random

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


class EmetAddToMatPicker(bpy.types.Operator):
    """
    This operator grabs currently selected objects and adds them to
    scene's MatSelColl (CollectionProperty(type=MaterialSelectPanelMeta))
    """
    bl_idname = "emet.emet_add_to_mat_picker"
    bl_label = "Select objects for material picker"
    bl_options = {'REGISTER'}

    def execute(self, context):
        MatSelColl = context.scene.MatSelColl
        MatSelColl.clear()
        for obj in bpy.context.selected_objects:
            prop = MatSelColl.add()
            prop.name = obj.name
            prop.active_index_mat = 0
        return {'FINISHED'}


class MATERIAL_UL_matslots_global(bpy.types.UIList):
    """
    Draws list of materials for UIEmetMaterialPicker picker.
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item:
                layout.prop(item, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


class UIEmetMaterialPicker(bpy.types.Panel):
    """
    Panel exposing material picker properties and operators.
    """
    bl_label = "Material picker"
    bl_category = "Emet Utils"
    bl_idname = "OBJECT_PT_ui_emet_material_picker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        MatSelColl = context.scene.MatSelColl

        # Operator that adds selected objects to MatSelColl as MaterialSelectPanelMeta
        layout.operator(
            EmetAddToMatPicker.bl_idname,
            text=EmetAddToMatPicker.bl_label,
            icon="SELECT_SET"
        )

        # Draw material picker for each selected member
        for member in MatSelColl:
            layout.label(text=member.name)
            layout.template_list(
                "MATERIAL_UL_matslots_global",
                "",
                bpy.data,
                "materials",
                member,
                "active_index_mat"
            )


# ------------------------------------------------------------------------
#   Config Classes
#   UI Properties
# ------------------------------------------------------------------------

class MaterialSelectPanelMeta(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Object Name",
        description="Selected object name",
        default="",
        maxlen=1024,
    )

    active_index_mat: bpy.props.IntProperty(
        name = "Active Index Material",
        description = "Index of currently selected material in global material scope",
        default = 0,
        min = 0
    )


class Emet_Properties(bpy.types.PropertyGroup):
    isAnimated : bpy.props.BoolProperty(
        name = "Is Animated?",
        description="Is tile animated",
        default = False,
    )

    tile_prefix: bpy.props.StringProperty(
        name="Name",
        description="Output file prefix",
        default="",
        maxlen=1024,
        subtype='FILE_NAME'
    )

    tile_outputPath: bpy.props.StringProperty(
        name = "Output",
        description="Choose output directory",
        default = os.path.join(".", "tmp"),
        maxlen=1024,
        subtype='DIR_PATH'
    )

    rotations : bpy.props.IntProperty(
        name = "Rotations",
        description="How many rotations around Z axis do you want to render",
        default = 8,
        min = 1,
        max = 8
    )


# ------------------------------------------------------------------------
#   Tiles Classes
# ------------------------------------------------------------------------

class RendererOperator():
    def __init__(self) -> None:
        self.context = None
        self.scene = None
        self.emet_tool = None
        self.matselcoll = None
        self.camera = None
        self.camera_location_cache = None
        self.camera_rotation_cache = None
        self.PREFIX = "tmp_tiles"
        self.temp_path = None
        #self.scene.render.filepath = None
        self.render_out = []


    def render(self):
        # Prepare render temp directory
        os.makedirs(self.emet_tool.tile_outputPath, exist_ok=True)

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
                current_tile = combine_frames(self.emet_tool.tile_outputPath, self.PREFIX)
            else:
                current_tile = read_image(f"{self.temp_path}.png")

            self.render_out.append(current_tile)

        output = cv2.vconcat(self.render_out)
        filepath = os.path.join(
            self.emet_tool.tile_outputPath,
            f"{self.emet_tool.tile_prefix}_diffuse.png"
        )
        filepath = os.path.abspath(filepath)
        cv2.imwrite(filepath, output)


    def _get_render_camera(self):
        cameras = [ob for ob in self.context.scene.objects if ob.type == 'CAMERA']
        if 1 != len(cameras):
            raise ValueError("There should only be one camera in the scene.")
        return cameras[0]


class Emet_Render_Tiles_Operator(bpy.types.Operator, RendererOperator):
    bl_idname = "emet.emet_render_tiles_operator"
    bl_label = "Render Tiles"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Perform any necessary setup here before calling universal rendering function
        self.context = context
        self.scene = context.scene
        self.emet_tool = self.scene.EmetTool
        self.matselcoll = self.scene.MatSelColl
        self.camera = self._get_render_camera()
        self.camera_location_cache = self.camera.location
        self.camera_rotation_cache = self.camera.rotation_euler # Should this be deep copied?
        self.PREFIX = "tmp_tiles"
        self.temp_path = os.path.abspath(os.path.join(self.emet_tool.tile_outputPath, self.PREFIX))
        self.scene.render.filepath = os.path.abspath(self.temp_path)
        self.render_out = []

        self.render()

        return {'FINISHED'}


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
        layout.prop(EmetTool, "tile_prefix")
        layout.prop(EmetTool, "tile_outputPath")

        layout.operator(Emet_Render_Tiles_Operator.bl_idname, text="Render Tiles", icon="SCENE")


class NODE_OT_normals_node_template(bpy.types.Operator):
    bl_label = "Render Tiles"
    bl_idname = "node.normals_node_template"
    bl_options = {'REGISTER'}

    def execute(self, context):
        mat = context.active_object.active_material
        tree = mat.node_tree
        links = tree.links

        vector_transform_node = tree.nodes.new(type='ShaderNodeVectorTransform')
        vector_transform_node.location = 0, 0
        vector_transform_node.vector_type = 'NORMAL'
        vector_transform_node.convert_from = 'OBJECT'
        vector_transform_node.convert_to = 'CAMERA'

        vector_mult = tree.nodes.new(type='ShaderNodeVectorMath')
        vector_mult.location = 400, 0
        vector_mult.operation = 'MULTIPLY'
        vector_mult.inputs[1].default_value = 1.0, 1.0, -1.0

        links.new(vector_transform_node.outputs[0], vector_mult.inputs[0])

        return {'FINISHED'}


class NODE_PT_node_templates_panel(bpy.types.Panel):
    bl_label = "Node Templates Panel"
    bl_idname = "node.node_templates_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Node Templates'
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context): # This tells when to show
        return (context.space_data.type == 'NODE_EDITOR' and
                context.space_data.tree_type == 'ShaderNodeTree')

    def draw(self, context):
        layout = self.layout
        layout.label(text="Click on the button to generate one of node templates")
        layout.operator(NODE_OT_normals_node_template.bl_idname, text="Normals template", icon="SCENE")


classes = [
    Emet_Properties,
    Emet_Render_Tiles_Operator, Emet_Tiles_Panel,
    MATERIAL_UL_matslots_global, UIEmetMaterialPicker, MaterialSelectPanelMeta,
    EmetAddToMatPicker, NODE_PT_node_templates_panel, NODE_OT_normals_node_template
]


def register():
    print("Registering Emet Tools...")
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.EmetTool = bpy.props.PointerProperty(type=Emet_Properties)
    bpy.types.Scene.MatSelColl = bpy.props.CollectionProperty(type=MaterialSelectPanelMeta)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()