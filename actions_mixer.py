import bpy


def register():
    bpy.utils.register_class(ActionsMixerPanel)
    bpy.utils.register_class(ActionsMixerRow)
    bpy.utils.register_class(ActionsMixerAddRow)
    bpy.utils.register_class(ActionsMixerRemoveRow)

    # TODO: Change name!
    bpy.types.Scene.ActionsPropColl = bpy.props.CollectionProperty(type=ActionsMixerRow)
    bpy.types.Scene.CharacterPointer = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.PropCollectionPointer = bpy.props.PointerProperty(type=bpy.types.Collection)
    bpy.types.Scene.WearableCollectionPointer = bpy.props.PointerProperty(type=bpy.types.Collection)


def unregister():
    bpy.utils.unregister_class(ActionsMixerPanel)
    bpy.utils.unregister_class(ActionsMixerRow)
    bpy.utils.unregister_class(ActionsMixerAddRow)
    bpy.utils.unregister_class(ActionsMixerRemoveRow)


def _get_actions_names(_1, _2):
    # Ad memorem to JS for helping me figure this out
    action_names = [(x, x, "") for x in bpy.data.actions.keys() if "PREFIX_FOR_DELETION" not in x]
    action_names.insert(0, ("None", "None", ""))
    return action_names

def _get_prop_names(_1, _2):
    return_names = None
    prop_collection = bpy.context.scene.PropCollectionPointer
    if prop_collection:
        return_names = [(x, x, "") for x in prop_collection.objects.keys()]
        return_names.insert(0, ("None", "None", ""))
    else:
        print("Prop collection is empty!")
    return return_names

class ActionsMixerRow(bpy.types.PropertyGroup):
    character_action_name: bpy.props.EnumProperty(
        name="",# Name is described in label above
        description="Actions available in current scope",
        items=_get_actions_names
    )

    prop_for_action_name: bpy.props.EnumProperty(
        name="",# Name is described in label above
        description="Actions available in current scope",
        items=_get_prop_names
    )


class ActionsMixerPanel(bpy.types.Panel):
    bl_label = "Actions Mixer Panel"
    bl_category = "Emet Utils" # TODO: This should be changed
    bl_idname = "actions_mixer.panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        ActionsPropColl = context.scene.ActionsPropColl

        grid = layout.grid_flow(row_major=True, columns=2, align=True)
        grid.label(text="Object name")
        grid.label(text="Props collection name (Cant be null)")
        grid.prop(context.scene, "CharacterPointer", text="")
        grid.prop(context.scene, "PropCollectionPointer", text="")
        row = layout.row()
        row.operator(ActionsMixerAddRow.bl_idname, text="Add row", icon="ADD")
        row.operator(ActionsMixerRemoveRow.bl_idname, text="Remove row", icon="REMOVE")
        grid.label(text="Action name")
        grid.label(text="Prop name")
        for member in ActionsPropColl:
            grid.prop(member, "character_action_name")
            grid.prop(member, "prop_for_action_name")

        layout.label(text="Wearable collection name")
        layout.prop(context.scene, "WearableCollectionPointer", text="")


class ActionsMixerAddRow(bpy.types.Operator):
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