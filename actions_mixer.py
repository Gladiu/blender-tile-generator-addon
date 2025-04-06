import bpy


def register():
    bpy.utils.register_class(ActionsMixerPanel)
    bpy.utils.register_class(ActionsMixerRow)
    bpy.utils.register_class(ActionsMixerAddRow)
    bpy.utils.register_class(ActionsMixerRemoveRow)

    # TODO: Change name!
    bpy.types.Scene.ActionsPropColl = bpy.props.CollectionProperty(type=ActionsMixerRow)
    bpy.types.Scene.CharacterPointer = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda _, obj: obj.type == "ARMATURE", # Filter to only allow armatures
    )
    bpy.types.Scene.PropPointer = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=lambda _, obj: obj.type == "ARMATURE", # Filter to only allow armatures
    )


def unregister():
    bpy.utils.unregister_class(ActionsMixerPanel)
    bpy.utils.unregister_class(ActionsMixerRow)
    bpy.utils.unregister_class(ActionsMixerAddRow)
    bpy.utils.unregister_class(ActionsMixerRemoveRow)


def _get_actions_names(_1, _2):
    action_names = [(x, x, "") for x in bpy.data.actions.keys()]
    action_names.insert(0, ("None", "None", ""))
    return action_names


class ActionsMixerRow(bpy.types.PropertyGroup):
    character_action_name: bpy.props.EnumProperty(
        name="",
        description="Actions available in current scope",
        items=_get_actions_names
    )

    prop_action_name: bpy.props.EnumProperty(
        name="",
        description="Actions available in current scope",
        items=_get_actions_names
    )


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

        grid = layout.grid_flow(row_major=True, columns=2, align=True)
        grid.label(text="Object name")
        grid.label(text="Object name")
        grid.prop(context.scene, "CharacterPointer", text="")
        grid.prop(context.scene, "PropPointer", text="")
        grid.label(text="Action name")
        grid.label(text="Action name")
        for member in ActionsPropColl:
            grid.prop(member, "character_action_name")
            grid.prop(member, "prop_action_name")
        row = layout.row()
        row.operator(ActionsMixerAddRow.bl_idname, text="Add row", icon="ADD")
        row.operator(ActionsMixerRemoveRow.bl_idname, text="Remove row", icon="REMOVE")


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