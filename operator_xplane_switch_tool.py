import collections

import bpy

from bpy_types import Panel
from bpy.props import IntProperty, FloatProperty
from math import degrees, radians

# manipulators we support in this tool

MANIP_COMMAND_KNOB = "command_knob"
MANIP_COMMAND_SWITCH_LEFT_RIGHT = "command_switch_left_right"
MANIP_COMMAND_SWITCH_UP_DOWN = "command_switch_up_down"

MANIPULATORS_COMMAND_POS_NEG = {
    MANIP_COMMAND_KNOB,
    MANIP_COMMAND_SWITCH_LEFT_RIGHT,
    MANIP_COMMAND_SWITCH_UP_DOWN,
}

MANIP_COMMAND_KNOB2 = "command_knob2"
MANIP_COMMAND_SWITCH_LEFT_RIGHT2 = "command_switch_left_right2"
MANIP_COMMAND_SWITCH_UP_DOWN2 = "command_switch_up_down2"

MANIPULATORS_COMMAND_TOGGLE = {
    MANIP_COMMAND_KNOB2,
    MANIP_COMMAND_SWITCH_LEFT_RIGHT2,
    MANIP_COMMAND_SWITCH_UP_DOWN2,
}


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
    locator = parent_or_self_with_name(active_object, 'locator')

    rotator = None
    manipulator = None

    if locator != None:
        rotator = child_or_self_with_name(locator, 'rotator')
        manipulator = child_or_self_with_name(locator, 'manipulator')

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
        layout.use_property_split = True
        layout.use_property_decorate = False
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

        box_outer = layout.box()
        row = box_outer.row()
        row.label(text='rotator:', icon='OBJECT_DATA')
        box = row.box()
        box.label(text=rotator.name if rotator != None else '', icon='EDITMODE_HLT')

        anim_angles = []
        dataref_values = []
        if rotator != None and rotator.animation_data != None:
            for fc in rotator.animation_data.action.fcurves:
                if fc.data_path.endswith('rotation_axis_angle'):
                    for key in fc.keyframe_points:
                        anim_angles.append(round(degrees(key.co[1]), 2))
                elif fc.data_path.endswith('xplane.datarefs[0].value'):
                    for key in fc.keyframe_points:
                        dataref_values.append(round(key.co[1], 2))

            box_inner = box_outer.box()
            box_inner.label(text='current settings:')
            box_inner.use_property_split = True
            box_inner.use_property_decorate = False

            if len(rotator.xplane.datarefs) > 0:
                dr0 = rotator.xplane.datarefs[0]

                row = box_inner.row()
                row.prop(dr0, 'path', text='dataref path')
                row = box_inner.row()
                row.prop(dr0, "anim_type", text='animation type')

                row = box_inner.row()
                split = row.split(factor=0.4)
                left_side = split.column(align=True)
                left_side.alignment = 'RIGHT'
                right_side = split.column()
                left_side.label(text='dataref values:')
                right_side.label(text=str(dataref_values))

                left_side.label(text='axis rotation angles:')
                right_side.label(text=f'{anim_angles}')

        col = box_outer.column(align=False)
        col.operator("xplane.switch_rotator_configure", text="Configure Animation")

        box_outer = layout.box()
        row = box_outer.row()
        row.label(text='manipulator:', icon='OBJECT_DATA')
        box = row.box()
        box.label(text=manipulator.name if manipulator != None else '', icon='EDITMODE_HLT')

        if manipulator != None:
            box_inner = box_outer.box()
            box_inner.label(text='current settings:')

            box_inner.prop(manipulator.xplane.manip, "enabled")

            if manipulator.xplane.manip.enabled:
                box_inner.prop(manipulator.xplane.manip, "type", text="Type")

                manipType = manipulator.xplane.manip.type
                box_inner.prop(manipulator.xplane.manip, "cursor", text="Cursor")
                if manipType != "noop":
                    box_inner.prop(manipulator.xplane.manip, "tooltip", text="Tooltip")

                if manipType in MANIPULATORS_COMMAND_TOGGLE:
                    box_inner.prop(manipulator.xplane.manip, "command")
                elif manipType in MANIPULATORS_COMMAND_POS_NEG:
                    box_inner.prop(manipulator.xplane.manip, "positive_command")
                    box_inner.prop(manipulator.xplane.manip, "negative_command")

            # col = box_outer.column(align=False)
            # col.operator("xplane.switch_manipulator_configure", text="Configure")


class OBJECT_OT_ConfigureSwitchRotator(bpy.types.Operator):
    bl_idname = "xplane.switch_rotator_configure"
    bl_label = "Configure switch rotator animations"
    bl_options = {'REGISTER', 'UNDO'}

    num_pos: IntProperty(
        name="Number of positions",
        description="The number of switch positions",
        default=2,
        soft_max=6,
        max=20,
        min=2
    )

    min_angle: FloatProperty(
        name="Minimum angle",
        description="The dataref value for minimum angle",
        default=-20,
        max=180.0,
        min=-180.0
    )
    min_value: FloatProperty(
        name="Minimum value",
        description="The dataref value for minimum angle",
        default=0,
        max=1e6,
        min=-1e6
    )
    max_angle: FloatProperty(
        name="Maximum angle",
        description="The maximum animation angle",
        default=20,
        max=180.0,
        min=-180.0
    )
    max_value: FloatProperty(
        name="Maximum value",
        description="The dataref value for maximum angle",
        default=1,
        max=1e6,
        min=-1e6
    )

    @classmethod
    def poll(cls, context):
        # need at least 2 objects selected and 1 active
        return context.active_object is not None

    def execute(self, context):
        if context.active_object == None:
            self.report({'INFO'}, 'No active object selected')
            return {'FINISHED'}

        locator, rotator_obj, manipulator = find_switch_components(context.active_object)

        if rotator_obj is None:
            self.report({'INFO'}, 'Unable to locate a rotator object')
            return {'FINISHED'}

        # set the rotation mode to axis and angle (defaults to 0 degrees about y)
        rotator_obj.rotation_mode = 'AXIS_ANGLE'

        if len(rotator_obj.xplane.datarefs) == 0:
            rotator_obj.xplane.datarefs.add()

        # clear the current animation frames
        rotator_obj.animation_data_clear()

        # the steps in angle and value
        angle_step = (self.max_angle - self.min_angle) / (self.num_pos - 1)
        value_step = (self.max_value - self.min_value) / (self.num_pos - 1)

        # the initial angle and value
        angle = self.min_angle
        value = self.min_value

        for i in range(1, self.num_pos + 1):
            # set the axis rotation w value
            rotator_obj.rotation_axis_angle[0] = radians(angle)
            # add a keyframe for the angle component (index 0) at frame 3
            rotator_obj.keyframe_insert(data_path="rotation_axis_angle", frame=i, index=0)

            rotator_obj.xplane.datarefs[0].value = value
            rotator_obj.keyframe_insert(data_path="xplane.datarefs[0].value", frame=i)

            angle += angle_step
            value += value_step

        return {'FINISHED'}


class OBJECT_OT_ConfigureSwitchManipulator(bpy.types.Operator):
    bl_idname = "xplane.switch_manipulator_configure"
    bl_label = "Configure switch rotator animations"
    bl_options = {'REGISTER', 'UNDO'}


# Class List
classes = (
    VIEW3D_PT_XPlaneSwitchUI,
    OBJECT_OT_ConfigureSwitchRotator,
    OBJECT_OT_ConfigureSwitchManipulator
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
