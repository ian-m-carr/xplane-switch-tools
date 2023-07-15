import bpy

from bpy_types import Panel
from math import degrees


def parent_or_self_with_name(active_object: bpy.types.Object, name: str) -> bpy.types.Object:
    if active_object == None:
        return None

    # is this the one?
    if name in active_object.name:
        return active_object

    return parent_or_self_with_name(active_object.parent, name)


def getChildren(myObject):
    children = []
    for ob in bpy.data.objects:
        if ob.parent == myObject:
            children.append(ob)
    return children


def child_or_self_with_name(active_object: bpy.types.Object, name: str) -> bpy.types.Object:
    if active_object == None:
        return None

    # is this the one?
    if name in active_object.name:
        return active_object

    for child in getChildren(active_object):
        match = child_or_self_with_name(child, name)
        if match != None:
            return match

    return None


def extract_animation_data(rotator_object: bpy.types.Object) -> list[float]:
    # empty object or no animation data?
    if rotator_object == None or rotator_object.animation_data == None:
        return []

    angles = ()
    dataref_vals = ()

    # looking for an axis_angle rotation curve
    for fc in rotator_object.animation_data.action.fcurves:
        # looking for the 'W' values the actual angles
        if fc.data_path.endswith('rotation_axis_angle') and fc.array_index == 0:
            # how many points are animated
            angles = fc.keyframe_points

        elif 'xplane.datarefs[0].value' in fc.data_path:
            dataref_vals = fc.keyframe_points

    # we have no animated points for the rotation angle!
    return (angles, dataref_vals)


def find_switch_components(active_object) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    '''
    Find the locator, rotator and manipulator
    :param active_object:
    :return:
    '''

    # up the chain for the locator
    locator = parent_or_self_with_name(active_object, '_locator')

    rotator = None
    manipulator = None

    if locator != None:
        rotator = child_or_self_with_name(locator, '_rotator')
        manipulator = child_or_self_with_name(locator, '_manipulator')

    return (locator, rotator, manipulator)


class VIEW3D_PT_XPlaneSwitchUI(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "X-Plane Switch Tools"
    bl_context = "objectmode"
    bl_category = 'Item'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        obj_name = obj.name if obj != None else ''
        if obj is not None:
            name = obj.name
        row = layout.row()
        row.label(text="Active object is: ", icon='OBJECT_DATA')
        box = row.box()
        box.label(text=obj_name, icon='EDITMODE_HLT')

        col = layout.column()
        col.label(text="Detected switch settings:")

        locator, rotator, manipulator = find_switch_components(obj)

        row = layout.row()
        row.label(text='Locator:', icon='OBJECT_DATA')
        box = row.box()
        box.label(text=locator.name if locator != None else '', icon='EDITMODE_HLT')

        row = layout.row()
        row.label(text='rotator:', icon='OBJECT_DATA')
        box = row.box()
        box.label(text=rotator.name if rotator != None else '', icon='EDITMODE_HLT')

        anim_angles = []
        dataref_values = []
        if rotator != None and rotator.animation_data != None:
            for fc in rotator.animation_data.action.fcurves:
                if fc.data_path.endswith('rotation_axis_angle'):
                    for key in fc.keyframe_points:
                        anim_angles.append(round(degrees(key.co[1]),2))
                elif fc.data_path.endswith('xplane.datarefs[0].value'):
                    for key in fc.keyframe_points:
                        dataref_values.append(round(key.co[1],2))

            box1 = layout.box()
            box1.label(text='current settings:')
            row = box1.row()
            row.label(text='dataref path:')
            box = row.box()
            box.label(text=rotator.xplane.datarefs[0].path)
            row = box1.row()
            row.label(text='dataref values:')
            box = row.box()
            box.label(text=str(dataref_values))
            row = box1.row()
            row.label(text='axis rotation angles:')
            box = row.box()
            box.label(text=f'{anim_angles}')

        row = layout.row()
        row.label(text='manipulator:', icon='OBJECT_DATA')
        box = row.box()
        box.label(text=manipulator.name if manipulator != None else '', icon='EDITMODE_HLT')

        col = layout.column(align=False)
        # col.operator("mesh.cross_section_add", text="Generate")


class OBJECT_OT_ConfigureSwitch(bpy.types.Operator):
    """Add a cross section"""
    bl_idname = "xplane.switch_configure"
    bl_label = "Add cross-section"
    bl_options = {'REGISTER', 'UNDO'}


# Class List
classes = (
    VIEW3D_PT_XPlaneSwitchUI,
    OBJECT_OT_ConfigureSwitch
)


# Register all operators and panels
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
