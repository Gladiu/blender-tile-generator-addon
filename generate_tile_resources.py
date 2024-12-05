bl_info = {
    "name": "Emet Tools",
    "author": "Maurycy Kujawski",
    "version": (1, 0),
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
    filepaths.sort(reverse=True)

    images = [cv2.imread(filepath, cv2.IMREAD_UNCHANGED) for filepath in filepaths]
    return cv2.hconcat(images)


def read_image(inputPath):
    path = Path(f"{inputPath}")

    if path.is_file() == False:
        return

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return image


def get_render_camera(context):
    """
    Get camera for render. If there is any other number of cameras in the scene
    than one return None as we can't auto determine which to use for render.
    """
    cameras = [ob for ob in context.scene.objects if ob.type == 'CAMERA']
    if len(cameras) == 1:
        return cameras[0]
    return None


def apply_noise(mat, obj):
    """
    If applicable - apply noise
    """
    random_int = random.randint(1, 100)
    if "Value" in mat.node_tree.nodes:
        mat.node_tree.nodes["Value"].outputs[0].default_value = random_int
    for mod in obj.modifiers:
        if mod.name == "GeometryNodes":
            mod.node_group.nodes["Material"].material = mat
            if "Value" in mod.node_group.nodes:
                bpy.data.node_groups['Geometry Nodes'].nodes['Value'].outputs[0].default_value = random_int


def render(matselcoll):
    # Apply materials to rendered objects
    for member in matselcoll:
        obj = bpy.context.scene.objects[member.name]
        mat = bpy.data.materials[member.active_index_mat]
        obj.data.materials[0] = mat

    # Get a camera - we only expect one to be present in the scene
    camera = get_render_camera(bpy.context)
    if None == camera:
        return # ERROR
    x, y = camera.location.x, camera.location.y
    camera_vector_mag = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
    camera.location.x = camera_vector_mag * 1 # Yes this is very verbose - sue me
    camera.location.y = 0
    camera.rotation_euler[2] = math.pi / 2
    camera_rotation_angle = math.pi * 2.0 / rotations
    for _ in range(0, EmetTool.tile_variationCount):
        for _ in range(0,rotations):
            # Apply noise
            for member in matselcoll:
                obj = bpy.context.scene.objects[member.name]
                mat = bpy.data.materials[member.active_index_mat]
                apply_noise(mat, obj)

            # Rotate camera around Z
            camera.rotation_euler[2] += camera_rotation_angle

            # Rotate camera position vector
            x, y = camera.location.x, camera.location.y
            camera.location.x = x * math.cos(camera_rotation_angle) - y * math.sin(camera_rotation_angle)
            camera.location.y = x * math.sin(camera_rotation_angle) + y * math.cos(camera_rotation_angle)

            # Render Diffuse
            bpy.ops.render.render(
                animation=is_Animated,
                write_still=True,
                use_viewport=False,
                layer='',
                scene=''
            )

            if is_Animated:
                current_tile = combine_frames(EmetTool.tile_outputPath, prefix)
            else:
                current_tile = read_image(f"{temp_path}.png")

            diffuse_tiles.append(current_tile)
    return


class EmetAddToMatPicker(bpy.types.Operator):
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
    bl_label = "Material picker"
    bl_category = "Emet Utils"
    bl_idname = "OBJECT_PT_ui_emet_material_picker"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        #print(bpy.context.selected_objects)
        layout = self.layout
        MatSelColl = context.scene.MatSelColl

        # Operator that adds selected objects to MatSelColl as MaterialSelectPanelMeta
        layout.operator(
            EmetAddToMatPicker.bl_idname,
            text=EmetAddToMatPicker.bl_label,
            icon="SCENE"
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
#   Config Class
#   UI Properties
# ------------------------------------------------------------------------

# TODO: Rename it
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
    tile_variationCount : bpy.props.IntProperty(
        name = "Number of Variations",
        description="Number of tiles to generate",
        default = 1,
        min = 1,
        max = 25
        )

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

    animation_startingFrame : bpy.props.IntProperty(
        name = "First Frame",
        description="Frame on which animation starts",
        default = 0,
        min = 0,
        max = 100
        )

    animation_prefix: bpy.props.StringProperty(
        name="Name",
        description="Output file prefix",
        default="",
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

    animation_outputPath: bpy.props.StringProperty(
        name = "Output",
        description="Choose output directory",
        default = os.path.join(".", "tmp"),
        maxlen=1024,
        subtype='DIR_PATH'
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
        # TODO: This should be set to false because we **should** cleanup after ourselves
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
        for _ in range(0, self.emet_tool.tile_variationCount):
            # Apply noise in between variations
            for member in self.matselcoll:
                obj = bpy.context.scene.objects[member.name]
                mat = bpy.data.materials[member.active_index_mat]
                apply_noise(mat, obj)

            # Render rotations
            for _ in range(0, self.emet_tool.rotations):
                # Apply noise

                # Rotate camera around Z
                self.camera.rotation_euler[2] += camera_rotation_angle

                # Rotate camera position vector
                x, y = self.camera.location.x, self.camera.location.y
                self.camera.location.x = x * math.cos(camera_rotation_angle) - y * math.sin(camera_rotation_angle)
                self.camera.location.y = x * math.sin(camera_rotation_angle) + y * math.cos(camera_rotation_angle)

                # Render Diffuse
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

        # TODO: Normal:
        # https://blender.stackexchange.com/questions/191091/bake-a-texture-map-with-python/191841#191841
        # TODO: Purge animation operator it duplicates features here

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
        # Perform any necessary setup here before calling univeral function - render
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

        # TODO: Do this for animation renderer
        #cache_isanimated = self.emet_tool.isAnimated
        #self.emet_tool.isAnimated = True
        self.render()
        #self.emet_tool.isAnimated = cache_isanimated

        return {'FINISHED'}


        # Calculate vector magnitude in x/y plane to keep proper offset from rendered object
        # z axis is not touched so it has to be properly setup by the user
        

"""
                # Render Normal

                for obj in bpy.context.selected_objects:  
                    
                    if bpy.data.materials.get(f"Normal_{obj.name}"):
                        normal_mat = bpy.data.materials.get(f"Normal_{obj.name}")
                    else:
                        normal_mat = bpy.data.materials.get(f"Normal")
                        
                    if "Value" in diffuse_mat.node_tree.nodes:
                        normal_mat.node_tree.nodes["Value"].outputs[0].default_value = i
                    obj.data.materials[0] = normal_mat
                    
                    for mod in obj.modifiers:
                        if mod.name == "GeometryNodes":
                            mod.node_group.nodes["Material"].material = normal_mat
                            if "Value" in mod.node_group.nodes:
                                bpy.data.node_groups['Geometry Nodes'].nodes['Value'].outputs[0].default_value = i
                             
                                
                
                bpy.ops.render.render(animation=is_Animated, write_still=True, use_viewport=False, layer='', scene='')
                
                if is_Animated:
                    current_tile = combine_frames(1, temp_path)
                else:
                    current_tile = read_image(f"{temp_path}.png")
                    
                normal_tiles.append(current_tile)

#"""                
        # Write Animation Sprite
        # TODO: Check if file exists and display warning before writing, or
        # change the name so it is different
        

"""
        cv2.imwrite(filepath, output)
        output = cv2.vconcat(normal_tiles)
        cv2.imwrite(
            f"{EmetTool.tile_prefix}_normal.png",
            output
        )"""
        # Clean up

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
        
        layout.label(text="Set active object to mesh")
        layout.prop(EmetTool, "tile_variationCount")
        layout.prop(EmetTool, "rotations")
        layout.prop(EmetTool, "isAnimated")
        layout.prop(EmetTool, "tile_prefix")
        layout.prop(EmetTool, "tile_outputPath")
        
        layout.operator(Emet_Render_Tiles_Operator.bl_idname, text="Render Tiles", icon="SCENE")

# ------------------------------------------------------------------------
#   Animation Classes 
# ------------------------------------------------------------------------
    

class Emet_Render_Animation_Operator(bpy.types.Operator):
    bl_idname = "emet.emet_render_animation_operator"
    bl_label = "Render Animation"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        EmetTool = scene.EmetTool
        active_object = bpy.context.active_object
        mesh = active_object.children[0]
        print("Mesh: ", type(active_object.children[0]))
        return {'FINISHED'}

        diffuse_mat = None
        if bpy.data.materials.get(f"Diffuse_{obj.name}"):
             diffuse_mat = bpy.data.materials.get(f"Diffuse_{obj.name}")
        else:
            diffuse_mat = bpy.data.materials.get(f"Diffuse")
        diffuse_animation_stripes = []
        normal_mat = None
        if bpy.data.materials.get(f"Normal_{obj.name}"):
            normal_mat = bpy.data.materials.get(f"Normal_{obj.name}")
        else:
            normal_mat = bpy.data.materials.get(f"Normal")
        normal_animation_stripes = []
        active_object.rotation_euler[2] = 0
        temp_path = f"{EmetTool.animation_outputPath}tmp"
        scene.render.filepath = temp_path
        rotations = EmetTool.animation_rotations

        for i in range(0,rotations):
            active_object.rotation_euler[2] = i * ((math.pi*2.0)/rotations)
            

            # Render Diffuse
            active_object.children[0].data.materials[0] = diffuse_mat
            bpy.ops.render.render(animation=True, use_viewport=True, layer='', scene='')
            animation_stripe = combine_frames(1, temp_path)
            diffuse_animation_stripes.append(animation_stripe)

            
            # Render Normal

            active_object.children[0].data.materials[0] = normal_mat
            bpy.ops.render.render(animation=True, use_viewport=True, layer='', scene='')
            animation_stripe = combine_frames(1, temp_path)
            normal_animation_stripes.append(animation_stripe)

            
        # Write Animation Sprite
        output_file = cv2.vconcat(diffuse_animation_stripes)
        active_object.rotation_euler[2] = 0
        cv2.imwrite(f"{EmetTool.animation_outputPath}\\{EmetTool.animation_prefix}_diffuse.png", output_file)
        output_file = cv2.vconcat(normal_animation_stripes)
        cv2.imwrite(f"{EmetTool.animation_outputPath}\\{EmetTool.animation_prefix}_normal.png", output_file)
        
        # Clean up
        active_object.children[0].data.materials[0] = diffuse_mat
        active_object.rotation_euler[2] = 0
        
        return {'FINISHED'}

class Emet_Animation_Panel(bpy.types.Panel):
    bl_label = "Animation"
    bl_category = "Emet Utils"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        EmetTool = scene.EmetTool
        
        layout.label(text="Set active object to armature")
        layout.prop(EmetTool, "animation_startingFrame")
        layout.prop(EmetTool, "animation_prefix")
        layout.prop(EmetTool, "animation_outputPath")
        
        layout.operator(Emet_Render_Animation_Operator.bl_idname, text="Render Animation", icon="SCENE")


#my_array: bpy.types.CollectionProperty(type=MyIntProp)

classes = [
    Emet_Properties,
    Emet_Render_Tiles_Operator, Emet_Tiles_Panel,
    Emet_Render_Animation_Operator, Emet_Animation_Panel,
    MATERIAL_UL_matslots_global, UIEmetMaterialPicker, MaterialSelectPanelMeta,
    EmetAddToMatPicker
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.EmetTool = bpy.props.PointerProperty(type=Emet_Properties)
    bpy.types.Scene.MatSelColl = bpy.props.CollectionProperty(type=MaterialSelectPanelMeta)
    print("startingggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg")


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()