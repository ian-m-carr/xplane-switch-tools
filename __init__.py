import sys
import bpy
import importlib

from . import operator_xplane_switch_tool

bl_info = {
    "name": "(IMC) Blender X-Plane switch tools",
    "author": "Ian Carr",
    "description": "Blender Add-on for managing X-Plane switch manipulators and animations",
    "blender": (3, 1, 0),
    "version": (0, 1, 0),
    "warning": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Object",
}

modules = [
    operator_xplane_switch_tool
]

classes = [
]


def reload() -> None:
    global modules

    for m in modules:
        importlib.reload(m)


_need_reload = "xplane_switch_tools" in sys.modules
if _need_reload:
    reload()


# ----------------REGISTER--------------.


def register() -> None:
    if bpy.app.background:
        return
    for m in modules:
        if hasattr(m, 'registry'):
            for c in m.registry:
                bpy.utils.register_class(c)
        if hasattr(m, 'register'):
            m.register()

    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    if bpy.app.background:
        return
    for m in modules:
        if hasattr(m, 'registry'):
            for c in m.registry:
                bpy.utils.unregister_class(c)
        if hasattr(m, 'unregister'):
            m.unregister()

    for cls in classes:
        bpy.utils.unregister_class(cls)
