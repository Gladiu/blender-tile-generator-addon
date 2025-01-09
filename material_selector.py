import bpy


def register():
    bpy.utils.register_class(MATERIAL_UL_matslots_global)
    bpy.utils.register_class(UIEmetMaterialPicker)
    bpy.utils.register_class(MaterialSelectPanelMeta)
    bpy.utils.register_class(EmetAddToMatPicker)

    bpy.types.Scene.MatSelColl = bpy.props.CollectionProperty(type=MaterialSelectPanelMeta)


def unregister():
    bpy.utils.unregister_class(MATERIAL_UL_matslots_global)
    bpy.utils.unregister_class(UIEmetMaterialPicker)
    bpy.utils.unregister_class(MaterialSelectPanelMeta)
    bpy.utils.unregister_class(EmetAddToMatPicker)


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