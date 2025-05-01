import bpy


def register():
    bpy.utils.register_class(TilesMixerPanel)
    bpy.utils.register_class(TilesMixerNodePanel)
    bpy.utils.register_class(TilesMixerProperties)
    bpy.utils.register_class(TileMixerNodeOperator)
    bpy.types.Scene.TileCollectionPointer = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.TileMixer = bpy.props.PointerProperty(type=TilesMixerProperties)


def unregister():
    bpy.utils.unregister_class(TilesMixerPanel)
    bpy.utils.unregister_class(TilesMixerNodePanel)
    bpy.utils.unregister_class(TilesMixerProperties)
    bpy.utils.unregister_class(TileMixerNodeOperator)

class TilesMixerProperties(bpy.types.PropertyGroup):
    foreground_suffix: bpy.props.StringProperty(
        name="",# Name is described in label above
        description="Foreground Object suffix",
        default="FG",
        maxlen=1024,
        subtype='NONE'
    )

    background_suffix: bpy.props.StringProperty(
        name="",# Name is described in label above
        description="Background Object suffix",
        default="BG",
        maxlen=1024,
        subtype='NONE'
    )


class TilesMixerPanel(bpy.types.Panel):
    bl_label = "Tiles Mixer Panel"
    bl_category = "Emet Utils" # TODO: This should be changed
    bl_idname = "tile_mixer.panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        TileMixer = context.scene.TileMixer

        layout.prop(context.scene , "TileCollectionPointer", text="")

        layout.label(text="Foreground object suffix")
        layout.prop(TileMixer, "foreground_suffix", text="")
        layout.label(text="Background object suffix")
        layout.prop(TileMixer, "background_suffix", text="")

class TileMixerNodeOperator(bpy.types.Operator):
    bl_idname = "tile_mixer.operator"
    bl_label = "Minimal Operator"


    def execute(self, context):
        if 'GeometryNodes' not in context.object.modifiers.keys():
            return {'FINISHED'}
        node_object = context.object.modifiers['GeometryNodes'].node_group.nodes

        new_node = node_object.new("FunctionNodeInputBool")
        new_node.label = "enable_in_background_render"
        new_node.location.y += 100

        new_node = node_object.new("FunctionNodeInputBool")
        new_node.label = "enable_in_shadow_render"

        new_node = node_object.new("FunctionNodeInputBool")
        new_node.label = "enable_in_foreground_render"
        new_node.location.y += -100
        
        new_node = node_object.new("GeometryNodeSetMaterial")
        new_node.label = "enable_shadow_material"
        new_node.location.x += -300
        new_node.mute = True

        new_node = node_object.new("GeometryNodeSetMaterial")
        new_node.label = "enable_transparent_material"
        new_node.location.x += 300
        new_node.mute = True

        return bpy.ops.transform.translate('INVOKE_DEFAULT')
    
class TilesMixerNodePanel(bpy.types.Panel):
    bl_label = "Tiles Mixer Node Panel"
    bl_category = "Emet Utils" # TODO: This should be changed
    bl_idname = "tile_mixer.node_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        TileMixer = context.scene.TileMixer

        layout.label(text="Spawn nodes used tile for rendering")
        layout.operator(TileMixerNodeOperator.bl_idname, text="Add nodes", icon="ADD")
