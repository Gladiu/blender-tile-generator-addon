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
import time

# ------------------------------------------------------------------------
#   Combine output images
# ------------------------------------------------------------------------

import cv2
from pathlib import Path
import os

def combine_frames(startingFrame, inputPath):
    frames = []
    print(inputPath)
    current_file = startingFrame
    files = os.listdir(inputPath)
    files.sort()
    print(files)
    #while True:
    #    # Check how many zeroes we have to append for file name
    #    prefix_zeroes = "0"*(4 - len(str(current_file)))
    #    path = Path(os.path.join(inputPath, f"{prefix_zeroes}{current_file}.png"))

    #    if path.is_file() == False:
    #        print("Fak no file")
    #        break
    #    else:
    #        print("file")

    #    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    #    frames.append(image)

    #    current_file += 1

    combined = cv2.hconcat(frames)

    return combined

def read_image(inputPath):
    path = Path(f"{inputPath}")

    if path.is_file() == False:
        return

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return image


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

    tile_isAnimated : bpy.props.BoolProperty(
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

    tile_rotations : bpy.props.IntProperty(
        name = "Rotations",
        description="How many rotations around Z axis do you want to render",
        default = 1,
        min = 1,
        max = 8
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

    animation_rotations : bpy.props.IntProperty(
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

class Emet_Render_Tiles_Operator(bpy.types.Operator):
    bl_idname = "emet.emet_render_tiles_operator"
    bl_label = "Render Tiles"
    bl_options = {'REGISTER'}

    def execute(self, context):
        scene = context.scene
        EmetTool = scene.EmetTool
        MatSelColl = scene.MatSelColl
        is_Animated = EmetTool.tile_isAnimated
        active_object = bpy.context.active_object
        diffuse_tiles = []
        normal_tiles = []
        #temp_path = os.path.join(EmetTool.animation_outputPath, "tmp")
        temp_path = os.path.join(EmetTool.animation_outputPath)
        rotations = EmetTool.tile_rotations

        for member in MatSelColl:
            obj = bpy.context.scene.objects[member.name]
            obj.data.materials[0] = bpy.data.materials[member.active_index_mat]
            print(obj.data.materials[0])

        cameras = [ob for ob in bpy.context.scene.objects if ob.type == 'CAMERA']
        if len(cameras) > 1:
            print("Whoa... how many cameras do u need partner?")
        camera = cameras[0]

        scene.render.filepath = os.path.abspath(temp_path)
        print(scene.render.filepath)

        # TODO: Cache original camera position and restore it afterwards in cleanup

        # Calculate vector magnitude in x/y plane to keep proper offset from rendered object
        # z axis is not touched so it has to be properly setup by the user
        x, y = camera.location.x, camera.location.y
        camera_vector_mag = math.sqrt(math.pow(x, 2) + math.pow(y, 2))
        camera.location.x = camera_vector_mag * 1 # Yes this is very verbose - sue me
        camera.location.y = 0
        camera.rotation_euler[2] = math.pi / 2
        camera_rotation_angle = math.pi * 2.0 / rotations
        for i in range(0, EmetTool.tile_variationCount):
            for j in range(0,rotations):
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
                    current_tile = combine_frames(1, temp_path)
                else:
                    current_tile = read_image(f"{temp_path}.png")

                diffuse_tiles.append(current_tile)

                """
                for obj in bpy.context.selected_objects:
                    diffuse_mat = bpy.data.materials.get(f"Diffuse_{obj.name}")
                    if bpy.data.materials.get(f"Diffuse_{obj.name}"):
                        diffuse_mat = bpy.data.materials.get(f"Diffuse_{obj.name}")
                    else:
                        diffuse_mat = bpy.data.materials.get(f"Diffuse")
                """

                """
                    if "Value" in diffuse_mat.node_tree.nodes:
                        diffuse_mat.node_tree.nodes["Value"].outputs[0].default_value = i
                    obj.data.materials[0] = diffuse_mat 


                    for mod in obj.modifiers:
                        if mod.name == "GeometryNodes":
                            mod.node_group.nodes["Material"].material = diffuse_mat
                            if "Value" in mod.node_group.nodes:
                                bpy.data.node_groups['Geometry Nodes'].nodes['Value'].outputs[0].default_value = i
                """


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
        output = cv2.vconcat(diffuse_tiles)
        filepath = os.path.join(
            EmetTool.tile_outputPath,
            f"{EmetTool.tile_prefix}_diffuse.png"
        )
        filepath = os.path.abspath(filepath)
        print(os.path.abspath(filepath))
        print(cv2.imwrite(filepath, output))

        """
        cv2.imwrite(filepath, output)
        output = cv2.vconcat(normal_tiles)
        cv2.imwrite(
            f"{EmetTool.tile_prefix}_normal.png",
            output
        )"""
        # Clean up

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
        
        layout.label(text="Set active object to mesh")
        layout.prop(EmetTool, "tile_variationCount")
        layout.prop(EmetTool, "tile_rotations")
        layout.prop(EmetTool, "tile_isAnimated")
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
        layout.prop(EmetTool, "animation_rotations")
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