import bpy

def _get_geometry_nodes(_1, _2):
    nodes = bpy.data.node_groups
    geometry_nodes = [(x, x, "") for x in nodes.keys() if nodes[x].type == 'GEOMETRY' and nodes[x].is_modifier == True]
    geometry_nodes.insert(0, ("None", "None", ""))
    return geometry_nodes

def register():
    bpy.utils.register_class(EnvironmentHelperMixerPanel)
    bpy.utils.register_class(EnvironmentHelperMixerToggleBoolOperator)
    bpy.utils.register_class(EnvironmentHelperMixerAddGeometryNodes)
    bpy.types.Scene.BackgroundIsEnabled = bpy.props.BoolProperty(
        name="Enable Background Toggle",# Name is described in label above
        description="",
        default=False
    )

    bpy.types.Scene.CollisionIsEnabled = bpy.props.BoolProperty(
        name="Enable Collision Toggle",# Name is described in label above
        description="",
        default=False
    )

    bpy.types.Scene.ForegroundIsEnabled = bpy.props.BoolProperty(
        name="Enable Foreground Toggle",# Name is described in label above
        description="",
        default=False
    )
    
    bpy.types.Scene.SelectedGeometryNodes = bpy.props.EnumProperty(
        name="",# Name is described in label above
        description="Actions available in current scope",
        items=_get_geometry_nodes
    )

def unregister():
    bpy.utils.unregister_class(EnvironmentHelperMixerPanel)
    bpy.utils.unregister_class(EnvironmentHelperMixerToggleBoolOperator)
    bpy.utils.unregister_class(EnvironmentHelperMixerAddGeometryNodes)

def set_bool_in_geometry_nodes(geometry_nodes, bool_name, value):
    geometry_nodes = geometry_nodes.nodes
    for node_key in geometry_nodes.keys():
        if geometry_nodes[node_key].label == bool_name:
            geometry_nodes[node_key].boolean = value

class EnvironmentHelperMixerPanel(bpy.types.Panel):
    bl_label = "EnvironmentHelper Mixer Panel"
    bl_category = "Emet Utils" # TODO: This should be changed
    bl_idname = "environment_helper_utils.panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        layout.prop(context.scene, "BackgroundIsEnabled", text="Toggle Background Render Bool")
        layout.prop(context.scene, "CollisionIsEnabled", text="Toggle Collision Render Bool")
        layout.prop(context.scene, "ForegroundIsEnabled", text="Toggle Foreground Render Bool")
        layout.operator(EnvironmentHelperMixerToggleBoolOperator.bl_idname, text="Toggle above boolean in ALL Geometry Nodes", icon="ADD")
        layout.label(text="Geometry nodes to apply in selected objects")
        layout.prop(context.scene, "SelectedGeometryNodes", text="")
        layout.operator( EnvironmentHelperMixerAddGeometryNodes.bl_idname, text="Apply Geometry Nodes to selected meshes", icon="ADD")

class EnvironmentHelperMixerToggleBoolOperator(bpy.types.Operator):
    bl_idname = "environment_helper_utils.background_operator"
    bl_label = "Minimal Operator"

    def execute(self, context):

        for node in bpy.data.node_groups:
            set_bool_in_geometry_nodes(node, "enable_in_background_render", context.scene.BackgroundIsEnabled)
            set_bool_in_geometry_nodes(node, "enable_in_collision_render", context.scene.CollisionIsEnabled)
            set_bool_in_geometry_nodes(node, "enable_in_foreground_render", context.scene.ForegroundIsEnabled)
        
        return {'FINISHED'}

class EnvironmentHelperMixerAddGeometryNodes(bpy.types.Operator):
    bl_idname = "environment_helper_utils.nodes_operator"
    bl_label = "Minimal Operator"

    def execute(self, context):
        sel_objs = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH']
        selected_geometry_nodes = context.scene.SelectedGeometryNodes
        if selected_geometry_nodes == 'None' or selected_geometry_nodes == "":
            self.report({'INFO'}, ('No geometry Nodes selected!'))
            return {'FINISHED'}
        if len(sel_objs) == 0:
            self.report({'INFO'}, ('Please select a mesh to use this operator'))
            return {'FINISHED'}
        for obj in sel_objs:
            if len(obj.modifiers) == 0:
                obj.modifiers.new("Geometry Nodes", type='NODES')

            for idx, mod in enumerate(obj.modifiers):
                if mod.type == 'NODES':
                    obj.modifiers[idx].node_group = bpy.data.node_groups[selected_geometry_nodes]

        return {'FINISHED'}