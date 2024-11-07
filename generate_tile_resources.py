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

pi = 3.1415

# ------------------------------------------------------------------------
#   Combine output images 
# ------------------------------------------------------------------------

import cv2
from pathlib import Path
import os

def combine_frames(startingFrame, inputPath):
    frames = []
    current_file = startingFrame
    while True:
        # Check how many zeroes we have to append for file name
        prefix_zeroes = "0"*(4 - len(str(current_file)))
        path = Path(f"{inputPath}\\{prefix_zeroes}{current_file}.png")

        if path.is_file() == False:
            break

        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        frames.append(image)

        current_file += 1

    combined = cv2.hconcat(frames)
    
    return combined

def read_image(inputPath):
    path = Path(f"{inputPath}")

    if path.is_file() == False:
        return

    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return image
    

# ------------------------------------------------------------------------
#   Config Class 
# ------------------------------------------------------------------------

class  Emet_Properties(bpy.types.PropertyGroup):
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
        default="C:\\tmp\\",
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
        default="C:\\tmp\\",
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
        is_Animated = EmetTool.tile_isAnimated
        active_object = bpy.context.active_object
        diffuse_tiles = []
        normal_tiles = []
        temp_path = f"{EmetTool.animation_outputPath}tmp\\"
        rotations = EmetTool.tile_rotations

        scene.render.filepath = temp_path
        for i in range(0, EmetTool.tile_variationCount):
            for j in range(0,rotations):
                active_object.rotation_euler[2] = j * ((pi*2.0)/rotations)
            

                # Render Diffuse

                for obj in bpy.context.selected_objects:
                    diffuse_mat = bpy.data.materials.get(f"Diffuse_{obj.name}")
                    if bpy.data.materials.get(f"Diffuse_{obj.name}"):
                         diffuse_mat = bpy.data.materials.get(f"Diffuse_{obj.name}")
                    else:
                        diffuse_mat = bpy.data.materials.get(f"Diffuse")
                    
                    if "Value" in diffuse_mat.node_tree.nodes:
                        diffuse_mat.node_tree.nodes["Value"].outputs[0].default_value = i
                    obj.data.materials[0] = diffuse_mat 
                    
                    for mod in obj.modifiers:
                        if mod.name == "GeometryNodes":
                            mod.node_group.nodes["Material"].material = diffuse_mat
                            if "Value" in mod.node_group.nodes:
                                bpy.data.node_groups['Geometry Nodes'].nodes['Value'].outputs[0].default_value = i

                
                bpy.ops.render.render(animation=is_Animated, write_still=True, use_viewport=False, layer='', scene='')
                
                if is_Animated:
                    current_tile = combine_frames(1, temp_path)
                else:
                    current_tile = read_image(f"{temp_path}.png")
                    
                diffuse_tiles.append(current_tile)
                
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
                        
        
        # Write Animation Sprite
        output_file = cv2.vconcat(diffuse_tiles)
        cv2.imwrite(f"{EmetTool.tile_outputPath}\\{EmetTool.tile_prefix}_diffuse.png", output_file)
        output_file = cv2.vconcat(normal_tiles)
        cv2.imwrite(f"{EmetTool.tile_outputPath}\\{EmetTool.tile_prefix}_normal.png", output_file)
        
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
        diffuse_mat = null
        if bpy.data.materials.get(f"Diffuse_{obj.name}"):
             diffuse_mat = bpy.data.materials.get(f"Diffuse_{obj.name}")
        else:
            diffuse_mat = bpy.data.materials.get(f"Diffuse")
        diffuse_animation_stripes = []
        normal_mat = null
        if bpy.data.materials.get(f"Normal_{obj.name}"):
            normal_mat = bpy.data.materials.get(f"Normal_{obj.name}")
        else:
            normal_mat = bpy.data.materials.get(f"Normal")
        normal_animation_stripes = []
        active_object.rotation_euler[2] = 0
        temp_path = f"{EmetTool.animation_outputPath}tmp\\"
        scene.render.filepath = temp_path
        rotations = EmetTool.animation_rotations

        for i in range(0,rotations):
            active_object.rotation_euler[2] = i * ((pi*2.0)/rotations)
            

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





classes = [
    Emet_Properties,
    Emet_Render_Tiles_Operator, Emet_Tiles_Panel,
    Emet_Render_Animation_Operator, Emet_Animation_Panel
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.EmetTool = bpy.props.PointerProperty(type=Emet_Properties)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()