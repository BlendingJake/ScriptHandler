from bpy.types import Panel, PropertyGroup, UIList, Operator, OperatorFileListElement
from bpy.props import StringProperty, CollectionProperty, IntProperty, PointerProperty, BoolProperty
from pathlib import Path
import bpy
from bpy_extras.io_utils import ImportHelper
from os import path


# ---------------------------------------------------------------------------------------------
# MISC FUNCTIONS
# ---------------------------------------------------------------------------------------------
def on_script_index_change(_, context):
    props = context.scene.script_handler

    if 0 <= props.project_index < len(props.projects):
        project = props.projects[props.project_index]

        if 0 <= project.script_index < len(project.scripts):
            script = project.scripts[project.script_index]

            for block in bpy.data.texts:
                if script.filename == block.name:
                    context.space_data.text = block
                    break


# ---------------------------------------------------------------------------------------------
# PANEL
# ---------------------------------------------------------------------------------------------
class ScriptHandlerPanel(Panel):
    bl_idname = "OBJECT_PT_script_handler"
    bl_label = "Script Handler"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        props = scn.script_handler

        layout.label(text="Projects")
        layout.template_list("OBJECT_UL_script_handler_projects", "", props, "projects", props, "project_index", rows=5)

        box = layout.box()

        box.operator("ops.sh_add_project")
        box.operator("ops.sh_remove_project")
        box.operator("ops.sh_rename_project")
        box.prop(props, "new_project_name")

        if 0 <= props.project_index < len(props.projects):
            layout.separator()
            layout.label(text="Scripts")

            project = props.projects[props.project_index]

            row = layout.row()
            row.template_list("OBJECT_UL_script_handler_scripts", "", project, "scripts", project, "script_index",
                              rows=5)

            col = row.column()
            col.operator("ops.sh_move_script_up", text="", icon="TRIA_UP")
            col.operator("ops.sh_move_script_down", text="", icon="TRIA_DOWN")
            col.operator("ops.sh_remove_script", text="", icon="X")

            layout.operator("ops.sh_add_scripts")

            layout.separator()
            layout.operator("ops.sh_load_reload_scripts")
            layout.operator("ops.sh_execute_scripts")


# ---------------------------------------------------------------------------------------------
# UI LISTS
# ---------------------------------------------------------------------------------------------
class OBJECT_UL_script_handler_projects(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        row.label(text=item.name)
        row.label(text="{} File(s)".format(len(item.scripts)))


class OBJECT_UL_script_handler_scripts(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        row.label(text=item.filename)
        row.prop(item, "execute")


# ---------------------------------------------------------------------------------------------
# OPERATORS
# ---------------------------------------------------------------------------------------------
class AddProject(Operator):
    bl_idname = "ops.sh_add_project"
    bl_label = "Add Project"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if props.new_project_name:
            project = props.projects.add()
            project.name = props.new_project_name

        return {"FINISHED"}


class RemoveProject(Operator):
    bl_idname = "ops.sh_remove_project"
    bl_label = "Remove Project"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            props.projects.remove(props.project_index)
            props.project_index = max(0, props.project_index - 1)

        return {"FINISHED"}


class RenameProject(Operator):
    bl_idname = "ops.sh_rename_project"
    bl_label = "Rename Project"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects) and props.new_project_name != "":
            props.projects[props.project_index].name = props.new_project_name

        return {"FINISHED"}


class AddScripts(Operator, ImportHelper):
    bl_idname = "ops.sh_add_scripts"
    bl_label = "Add Script(s)"
    bl_options = {"UNDO", "INTERNAL"}

    filename_ext = ".py"
    files: CollectionProperty(type=OperatorFileListElement)
    directory: StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            project = props.projects[props.project_index]

            project_scripts = set([x.filename for x in project.scripts])
            loaded_scripts = set([x.name for x in bpy.data.texts])
            for file in self.files:
                if file.name and file.name not in project_scripts:
                    script = project.scripts.add()
                    script.filepath = path.join(self.directory, file.name)
                    script.filename = file.name

                    if file.name not in loaded_scripts:
                        bpy.ops.text.open(filepath=script.filepath)

        return {"FINISHED"}


class RemoveScript(Operator):
    bl_idname = "ops.sh_remove_script"
    bl_label = "Remove Script"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            project = props.projects[props.project_index]

            if 0 <= project.script_index < len(project.scripts):
                project.scripts.remove(project.script_index)
                project.script_index = min(len(project.scripts), project.script_index)

        return {"FINISHED"}


class MoveScriptUp(Operator):  # "UP" = closer to 0
    bl_idname = "ops.sh_move_script_up"
    bl_label = "Move Script Up"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            project = props.projects[props.project_index]

            if 0 < project.script_index:
                project.scripts.move(project.script_index, project.script_index-1)
                project.script_index -= 1

        return {"FINISHED"}


class MoveScriptDown(Operator):  # "DOWN" = closer to len(list)
    bl_idname = "ops.sh_move_script_down"
    bl_label = "Move Script Down"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            project = props.projects[props.project_index]

            if project.script_index < len(project.scripts):
                project.scripts.move(project.script_index, project.script_index+1)
                project.script_index += 1

        return {"FINISHED"}


class LoadReloadScripts(Operator):
    bl_idname = "ops.sh_load_reload_scripts"
    bl_label = "(Re)Load Scripts"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            project = props.projects[props.project_index]

            cur_block = context.space_data.text
            for script in project.scripts:
                if script.filename in bpy.data.texts:
                    context.space_data.text = bpy.data.texts[script.filename]
                    bpy.ops.text.reload()
                else:
                    bpy.ops.text.open(filepath=script.filepath)

            if cur_block is not None:
                context.space_data.text = cur_block

        return {"FINISHED"}


class ExecuteScripts(Operator):
    bl_idname = "ops.sh_execute_scripts"
    bl_label = "Execute Scripts"
    bl_options = {"UNDO", "INTERNAL"}

    def execute(self, context):
        props = context.scene.script_handler

        if 0 <= props.project_index < len(props.projects):
            project = props.projects[props.project_index]

            cur_block = context.space_data.text
            for script in project.scripts:
                if script.execute:
                    if script.filename not in bpy.data.texts:  # load before running if needed
                        bpy.ops.text.open(filepath=script.filepath)
                    else:
                        context.space_data.text = bpy.data.texts[script.filename]

                    bpy.ops.text.run_script()

            if cur_block is not None:
                context.space_data.text = cur_block

        return {"FINISHED"}


# ---------------------------------------------------------------------------------------------
# DATA STORAGE
# ---------------------------------------------------------------------------------------------
class ScriptProperties(PropertyGroup):
    filename: StringProperty(name="Name")
    filepath: StringProperty(name="Path")
    execute: BoolProperty(name="Execute", default=False)


class ProjectProperties(PropertyGroup):
    name: StringProperty(name="Name")
    scripts: CollectionProperty(type=ScriptProperties)
    script_index: IntProperty(update=on_script_index_change)


class ScriptHandlerProperties(PropertyGroup):
    projects: CollectionProperty(type=ProjectProperties)
    project_index: IntProperty(update=on_script_index_change)

    new_project_name: StringProperty(name="Project Name")


classes = (  # order is important to avoid errors while registering
    AddProject,
    RemoveProject,
    RenameProject,

    AddScripts,
    RemoveScript,

    MoveScriptUp,
    MoveScriptDown,

    LoadReloadScripts,
    ExecuteScripts,

    ScriptHandlerPanel,

    OBJECT_UL_script_handler_projects,
    OBJECT_UL_script_handler_scripts,

    ScriptProperties,
    ProjectProperties,
    ScriptHandlerProperties
)


# ---------------------------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------------------------
def register():
    from bpy.utils import register_class
    from bpy.types import Scene

    for cls in classes:
        register_class(cls)

    Scene.script_handler = PointerProperty(type=ScriptHandlerProperties)


def unregister():
    from bpy.utils import unregister_class
    from bpy.types import Scene

    for cls in classes:
        unregister_class(cls)

    del Scene.script_handler


if __name__ == "__main__":
    register()
