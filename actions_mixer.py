import bpy


def register():
    bpy.utils.register_class(ActionsMixerPanel)
    bpy.utils.register_class(ActionsMixerRow)
    bpy.utils.register_class(ActionsMixerAddRow)
    bpy.utils.register_class(ActionsMixerRemoveRow)

    # TODO: Change name!
    bpy.types.Scene.ActionsPropColl = bpy.props.CollectionProperty(type=ActionsMixerRow)


def unregister():
    bpy.utils.unregister_class(ActionsMixerPanel)
    bpy.utils.unregister_class(ActionsMixerRow)
    bpy.utils.unregister_class(ActionsMixerAddRow)
    bpy.utils.unregister_class(ActionsMixerRemoveRow)


def _get_actions_names(_1, _2):
    action_names = [(f"ACT{i}", x[0], "") for i, x in enumerate(bpy.data.actions.items())]
    action_names.insert(0, ("NONE", "None", ""))
    return action_names


class ActionsMixerRow(bpy.types.PropertyGroup):
    character_action_name: bpy.props.EnumProperty(
        name="Action names",
        description="Actions available in current scope",
        items=_get_actions_names
    )

    prop_action_name: bpy.props.EnumProperty(
        name="Action names",
        description="Actions available in current scope",
        items=_get_actions_names
    )

    frame_start: bpy.props.IntProperty(
        "Frame start",
        description="Frame from which to start rendering",
        default=1,
        min=0
    )

    frame_end: bpy.props.IntProperty(
        "Frame end",
        description="Frame up to which render action",
        default=10,
        min=0
    )


# TODO: This should **only** be displayed if the animated checkbox is set
class ActionsMixerPanel(bpy.types.Panel):
    bl_label = "Actions Mixer Panel"
    bl_category = "Emet Utils" # TODO: This should be changed
    bl_idname = "SCENE_PT_ui_actions_mixer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        ActionsPropColl = context.scene.ActionsPropColl

        grid = layout.grid_flow(row_major=True, columns=4, align=True)
        grid.label(text="Character action name")
        grid.label(text="Prop action name")
        grid.label(text="Frame start")
        grid.label(text="Frame end")
        for member in ActionsPropColl:
            grid.prop(member, "character_action_name")
            grid.prop(member, "prop_action_name")
            grid.prop(member, "frame_start")
            grid.prop(member, "frame_end")
        row = layout.row()
        row.operator(ActionsMixerAddRow.bl_idname, text="Add row", icon="SCENE")
        row.operator(ActionsMixerRemoveRow.bl_idname, text="Remove row", icon="SCENE")


class ActionsMixerAddRow(bpy.types.Operator):
    """
    """
    bl_idname = "actions_mixer.add_row"
    bl_label = "Row Actions Mixer Add Operator"
    bl_options = {'REGISTER'}

    def execute(self, context):
        ActionsPropColl = context.scene.ActionsPropColl
        ActionsPropColl.add()
        return {'FINISHED'}


class ActionsMixerRemoveRow(bpy.types.Operator):
    """
    """
    bl_idname = "actions_mixer.remove_row"
    bl_label = "Row Actions Mixer Remove Operaotr"
    bl_options = {'REGISTER'}

    def execute(self, context):
        ActionsPropColl = context.scene.ActionsPropColl
        ActionsPropColl.remove(len(ActionsPropColl) - 1)
        return {'FINISHED'}