# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name" : "RenderFarts",
    "author" : "Sakari Niittymaa",
    "description" : "Render image in parts.",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 5),
    "location" : "Properties > Render > RenderFarts",
    "warning" : "",
    "category" : "Render"
}

# ------------------------------------------------------------------------
#    Imports
# ------------------------------------------------------------------------

import os, webbrowser
from datetime import datetime

import numpy as np
import bpy

from bpy.app.handlers import persistent
from bpy.types import Operator, Panel, UIList, PropertyGroup
from bpy.props import StringProperty, IntProperty, BoolProperty, PointerProperty, CollectionProperty


# ------------------------------------------------------------------------
#    Helpers
# ------------------------------------------------------------------------

# RenderChunk object to store data for image parts
class RF_RenderPart():
    def __init__(self, name, border_min_x, border_max_x, border_min_y, border_max_y):
        self.name = name
        self.border_min_x = border_min_x
        self.border_max_x = border_max_x
        self.border_min_y = border_min_y
        self.border_max_y = border_max_y
render_parts = []

# Utilities
# ----------------------------------------------------
class RF_Utils():    

    # List all class methods with or without dunders
    # Or just use python dir() e.g: print(dir(imbuf))
    def list_class_methods(cls, dunders_included = True):
        method_list = None
        if dunders_included is True:
            method_list = [func for func in dir(cls) if callable(getattr(cls, func))]
        else:
            method_list = [func for func in dir(cls) if callable(getattr(cls, func)) and not func.startswith("__")]
        print(method_list)
        return method_list

    # List all object attributes
    def list_object_attributes(obj):
        for att in dir(obj):
            print (att, getattr(obj,att))

    def flat_list(l, iteration=1):
        flattened_list = l
        try:
            for i in range(iteration):
                flattened_list = [y for x in flattened_list for y in x]
            return flattened_list
        except Exception as e:
            print(e)

    # Valid file name by parsing out illegal / invalid chars
    def validate_filename(name):  # could reuse for other presets
        for char in " !@#$%^&*(){}:\";'[]<>,.\\/?":
            name = name.replace(char, '_')
        return name.lower().strip()

    # Get the directory of the currently-executing addon
    def get_script_dir():
        script_file = os.path.realpath(__file__)
        return os.path.dirname(script_file)

    # Get currently opened blend file folder
    def get_blend_file_folder():
        filepath = bpy.data.filepath
        directory = os.path.dirname(filepath)
        #directory_path = os.path.join(directory, bl_info['name'])
        return directory

    # Get list of rendered files filenames
    # https://blenderartists.org/t/how-to-read-files-name-in-current-folder/1117301/3
    def get_files_in_folder(path, file_extension = True):
        path = os.path.realpath(bpy.path.abspath(path))
        render_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if (file.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif'))):
                    if file_extension is not True:
                        # Remove file extension if needed
                        render_files.append(os.path.splitext(os.path.basename(file))[0])
                    else:
                        render_files.append(file)
        return render_files

    # Refresh render list with found image filenames
    def refresh_render_list(scene):
        # Clear render_list and add image filenames to it
        render_files = RF_Utils.get_files_in_folder(scene.render_settings.render_folder)
        scene.render_list.clear()
        prefix = str(scene.render_settings.filename_prefix).replace(" ", "")
        for file in render_files:
            # Add only names that starts with 'prefix' to list
            if str(file).startswith(prefix):
                item = scene.render_list.add()
                item.image_name = file
        
        # Update rendered parts value in UI
        scene.render_settings.rendered_parts_count = len(render_files)
        
        # Check if all parts rendered
        if (len(render_files) == scene.render_settings.total_parts_count):
            scene.render_settings.all_parts_rendered = True
        else:
            scene.render_settings.all_parts_rendered = False

    # Refresh render parts for rendering process to get not-rendered images based on image files
    def refresh_render_parts(scene):        
        rndr = scene.render
        parts_count = scene.render_settings.parts_count
        scene.render_settings.total_parts_count = parts_count * parts_count
        leading_zeros = len(str(scene.render_settings.total_parts_count)) - 1
        RF_Utils.refresh_render_list(scene)
        render_parts.clear()
        for row in range(parts_count):
            for column in range(parts_count):
                filename = scene.render_settings.filename_prefix + "_{}_{}".format(str(row + 1).zfill(leading_zeros), str(column + 1).zfill(leading_zeros))
                if not any(filename == os.path.splitext(listitem.image_name)[0] for listitem in scene.render_list):
                    border_min_x = (1 / parts_count) * row
                    border_max_x = (1 / parts_count) * (row + 1)
                    border_min_y = (1 / parts_count) * column
                    border_max_y = (1 / parts_count) * (column + 1)
                    temp_part = RF_RenderPart(filename, border_min_x, border_max_x, border_min_y, border_max_y)
                    render_parts.append(temp_part)        

    # Create dummy image file for reserving image slot 
    # before rendering huge images with multiple computers.
    # It's not bulletproof but still can prevent multiple
    # instance of same image rendering process.
    def create_dummy_image(image_name, image_format, path):
        filepath = os.path.realpath(bpy.path.abspath(path)) + '.' + str(image_format).lower()
        open(filepath, 'a').close()

    # Check if all image parts is reandered and return valid list
    def get_all_image_parts(context, file_extension = True):
        scene = context.scene
        rendered_images = RF_Utils.get_files_in_folder(scene.render_settings.render_folder)
        return rendered_images 

    # Merge all image parts to final image
    def merge_image_parts(context):

        scene = context.scene
        rndr = scene.render
        
        # Refresh and get all rendered images from list
        RF_Utils.refresh_render_list(scene)
        rendered_images = []
        for item in scene.render_list:
            rendered_images.append(item.image_name)
        
        parts_count = scene.render_settings.parts_count
        total_parts_count = scene.render_settings.total_parts_count = parts_count * parts_count

        # Read all images to array of images in pixels
        if rendered_images:

            # Render settings
            final_image_name = 'FINAL_EPIC_' + scene.render_settings.filename_prefix + rndr.file_extension
            final_image_filepath = os.path.join(scene.render_settings.render_folder, final_image_name)
            final_resolution_multiplier = rndr.resolution_percentage / 100
            final_image_width = int(rndr.resolution_x * final_resolution_multiplier)
            final_image_height = int(rndr.resolution_y * final_resolution_multiplier)
            part_width = int(round(final_image_width / parts_count))
            part_height = int(round(final_image_height / parts_count))

            image_pixel_count = int(final_image_width * final_image_height)
            part_pixel_count = int(image_pixel_count / total_parts_count)

            # Empty arrays for every pixel
            # final_image_pixels = [None] * part_pixel_count * total_parts_count         
            final_image_pixels = []       
            image_pixels = []        

            # Parse out numbers from names
            # name_numbers = []
            # for image in rendered_images:
            #     num = image.split('.')[0]
            #     name_numbers.append([num.split('_')[1], num.split('_')[2]])
                            
            # Order rendered part names to row-major order
            rendered_images_ordered = []            
            for y in range(parts_count, 0, -1):
                for x in range(parts_count):
                    rendered_images_ordered.append(rendered_images[(y-1)+(x*parts_count)])

            # Get all pixels from image parts
            for image in rendered_images_ordered:
                filepath = os.path.join(scene.render_settings.render_folder, image)
                filepath = os.path.realpath(bpy.path.abspath(filepath))
                loaded_pixels = list(bpy.data.images.load(filepath, check_existing=True).pixels)
                # image_pixels.append(loaded_pixels[:])
                image_pixels.append([loaded_pixels[ipx:ipx+4] for ipx in range(0, len(loaded_pixels), 4)])

            # Create final image pixels by loopin all image parts pixels
            for i in range(len(image_pixels)):
                for x in range(part_width):
                    for y in range(part_height):
                        # TODO: Not sure if this ordering pixels properly to final image. Output is mess still.
                        px_index = (x + y * part_width) + (i * (part_width * part_height))
                        # final_image_pixels[px_index] = image_pixels[i][y]   
                        final_image_pixels.append(image_pixels[i][y])         

            # Flatten needed levels from array
            # final_image_pixels = RF_Utils.flat_list(final_image_pixels, 1)

            # DEBUG: Create text file from data
            # for line in final_image_pixels:
            #     print(line, file=open("D:\\" + bl_info['name'] + "_Final_Image_Pixels.txt", "a"))

            # final_image_pixels = np.array(final_image_pixels)

        # Check if there is enoug pixel images in array
        # if len(final_image_pixels) == image_pixel_count or len(final_image_pixels) == image_pixel_count * 4:

            try:
                # Save output image
                output_image = bpy.data.images.new(final_image_name, alpha=True, width=final_image_width, height=final_image_height)
                output_image.alpha_mode = 'STRAIGHT'
                # output_image.pixels = bytes([int(pix*255) for pix in final_image_pixels])
                # output_image.pixels = final_image_pixels.ravel()
                output_image.pixels = final_image_pixels
                output_image.filepath_raw = final_image_filepath
                output_image.file_format = scene.render.image_settings.file_format
                output_image.save()          

                # Open folder when merge complete
                path = os.path.realpath(bpy.path.abspath(scene.render_settings.render_folder))
                webbrowser.open('file:///' + path)

            except Exception as e:
                excepName = type(e).__name__
                RF_Utils.show_message_box("Cannot merge images properly: " + excepName, "Merge Failed", "ERROR")
                print(e)

    # Show pop-up message window for user
    def show_message_box(message = "", title = "Message", icon = 'INFO'):
        def draw(self, context):
            self.layout.label(text=message)
        bpy.context.window_manager.popup_menu(draw, title = title, icon = icon)

# ------------------------------------------------------------------------
#    Properties (_PROP_)
# ------------------------------------------------------------------------

class RF_PROP_RenderSettings (PropertyGroup):
    render_folder: StringProperty(
        name="Render Folder",
        description="Choose a Output Folder For " + bl_info['name'],
        default="//",
        maxlen=1024,
        subtype='DIR_PATH'
    )
    filename_prefix: StringProperty(
        name="Filename Prefix",
        description="Identification Prefix String for " + bl_info['name'] + " Filename",
        default="Fart"
    )
    parts_count: IntProperty(
        name="Parts Count",
        description="Total Parts Count (e.g. 4 x 4 = 16)",
        default=4,
        min=1
    )
    rendered_parts_count: IntProperty(
        name="Rendered Parts Count",
        default=0,
        min=0
    )
    total_parts_count: IntProperty(
        name="Total Parts Count",
        description="Total Parts Count (e.g. 4 x 4 = 16)",
        default=0,
        min=1
    )
    crop_border: BoolProperty(
        name="Crop to Render Region",
        description="Crop Render to Parts",
        default=True
    )
    overwrite_files: BoolProperty(
        name="Overwrite Images",
        description="Overwrite Exist Image Files",
        default=False
    )    
    show_render_window: BoolProperty(
        name="Show Render Window",
        description="Show Render Window While Rendering",
        default=True
    )
    stop_rendering: BoolProperty(
        name="Rendering in Progress",
        default=False
    )
    all_parts_rendered: BoolProperty(
        name="All parts rendered",
        default=False
    )

class RF_PROP_RenderListItem (PropertyGroup):
    image_name: StringProperty()
    image_id: IntProperty()


# ------------------------------------------------------------------------
#    Operators (_OT_)
# ------------------------------------------------------------------------

# OT: Initialize
# ----------------------------------------------------

class RF_OT_Init(Operator):
    bl_label = "Initialize " + bl_info['name']
    bl_idname = "rp.init"
    bl_description = "Initialize " + bl_info['name'] + " addon"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):       
        print(self.bl_label)
        scene = context.scene
        #scene.render_settings.render_folder = scene.render.filepath  
        RF_Utils.refresh_render_list(scene)      
        return{'FINISHED'}

# OT: Start Rendering Images/Chunks
# ----------------------------------------------------
# https://blender.stackexchange.com/a/153254/497

class RF_OT_StartRender(Operator):
    bl_label = "Start Rendering"
    bl_idname = "rp.start_render"
    bl_description = "Start Rendering Process"

    _timer = None
    stop = None
    rendering = None
    render_complete = None

    '''
    # Disable/enable button
    @classmethod
    def poll(self, context):
        return context.scene.render_settings.all_parts_rendered == False
    '''

    def pre(self, dummy, event):
        self.render_complete = False
        self.rendering = True

    def post(self, dummy, event):
        self.rendering = False

    def complete(self, dummy, event):
        #print('RENDER COMPLETE')        
        self.render_complete = True

    def cancelled(self, dummy, event):
        print('RENDER CANCELLED')
        self.stop = True

    def remove_handlers(self, context, event):
        bpy.app.handlers.render_pre.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_complete.remove(self.complete)
        bpy.app.handlers.render_cancel.remove(self.cancelled)
        context.window_manager.event_timer_remove(self._timer)

    def execute(self, context):        

        print(self.bl_label)

        context.scene.render_settings.stop_rendering = False

        # Define the variables during execution. This allows to define when called from a button
        self.stop = False
        self.rendering = False
        self.render_complete = True

        bpy.app.handlers.render_pre.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_complete.append(self.complete)
        bpy.app.handlers.render_cancel.append(self.cancelled)

        # The timer gets created and the modal handler is added to the window manager
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):

        scene = context.scene
        rndr = scene.render

        if event.type in {'ESC'} or scene.render_settings.stop_rendering is True:
            self.remove_handlers(context, event)
            self.report({'WARNING'}, 'User interuption')
            RF_Utils.show_message_box("Render will be stop after the current frame finishes", self.bl_description, "ERROR")
            return {'FINISHED'}

        # This event is signaled and will start the render if available
        if event.type == 'TIMER':

            # Nothing is currently rendering. Proceed to render.
            if self.render_complete is True and self.rendering is False and scene.render_settings.stop_rendering is False:
                
                RF_Utils.refresh_render_parts(scene)

                # If cancelled or no more chunks to render, finish.
                if True in (not render_parts, self.stop is True):
                    # We remove the handlers and the modal timer to clean everything
                    self.remove_handlers(context, event)
                    return {"FINISHED"} 
                
                try:
                    # Setup active chunk and filepath
                    chunk = render_parts[0]
                    filepath = os.path.join(scene.render_settings.render_folder, chunk.name)
                    rndr.filepath = filepath 

                    # Setup border sizes
                    rndr.border_min_x = chunk.border_min_x
                    rndr.border_max_x = chunk.border_max_x
                    rndr.border_min_y = chunk.border_min_y
                    rndr.border_max_y = chunk.border_max_y 

                    rndr.use_border = True
                    rndr.use_crop_to_border = scene.render_settings.crop_border                 
                
                    if scene.render_settings.show_render_window is True:
                        # TODO: Render image skips last dummy image while render window is active.
                        #RF_Utils.create_dummy_image(chunk.name, rndr.image_settings.file_format, filepath)
                        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
                    else:
                        # Create small dummy image before rendering to prevent multiple renderings                    
                        RF_Utils.create_dummy_image(chunk.name, rndr.image_settings.file_format, filepath)
                        bpy.ops.render.render(write_still=True)

                except Exception as e:
                    excepName = type(e).__name__
                    RF_Utils.show_message_box(str(e)[:-1], "Render Failed", "ERROR")
                    return {"FINISHED"} 

        return {"PASS_THROUGH"}

# OT: Stop Rendering Process
# ----------------------------------------------------

class RF_OT_StopRender(Operator):
    bl_label = "Stop Rendering"
    bl_idname = "rp.stop_render"
    bl_description = "Stop the Rendering Process"

    # Disable/enable button
    @classmethod
    def poll(self, context):
        return context.scene.render_settings.all_parts_rendered is False and context.scene.render_settings.rendered_parts_count > 0
    
    def execute(self, context):
        scene = context.scene
        print(self.bl_label)
        scene.render_settings.stop_rendering = True
        RF_Utils.show_message_box("Render will be stop after the current frame finishes", self.bl_description, "ERROR")        
        return{'FINISHED'}

# OT: Refresh Render List
# ----------------------------------------------------

class RF_OT_RefreshList(Operator):
    bl_label = "Refresh List"
    bl_idname = "rp.refresh_list"
    bl_description = "Refresh Rendering List"
    def execute(self, context):
        print(self.bl_label)
        scene = context.scene
        RF_Utils.refresh_render_list(scene)
        return{'FINISHED'}

# OT: Open Render Folder
# ----------------------------------------------------

class RF_OT_OpenRenderFolder(Operator):
    bl_label = "Open Folder"
    bl_idname = "rp.open_render_folder"
    bl_description = "Open Render Folder"
    def execute(self, context):
        scene = context.scene
        print(self.bl_label + ': ' + scene.render_settings.render_folder)
        # path = os.path.realpath(scene.render_settings.render_folder)
        path = os.path.realpath(bpy.path.abspath(scene.render_settings.render_folder))
        webbrowser.open('file:///' + path)

        return{'FINISHED'}

# OT: Reset Render Border
# ----------------------------------------------------

class RF_OT_ResetBorder(Operator):
    bl_label = "Reset Render Border"
    bl_idname = "rp.reset_border"
    bl_description = "Reset Render Border to the Current Camera Resolution"
    def execute(self, context):
        print(self.bl_label)
        scene = context.scene
        rndr = scene.render        
        rndr.border_min_x = 0
        rndr.border_min_y = 0
        rndr.border_max_x = rndr.resolution_x
        rndr.border_max_y = rndr.resolution_y
        return{'FINISHED'}

# OT: Merge Images
# ----------------------------------------------------

class RF_OT_MergeImages(Operator):
    bl_label = "Merge Images"
    bl_idname = "rp.merge_images"
    bl_description = "Merge Images to One Image After ALL Parts is Rendered. Works only when images not rendered with Crop to Render Region feature"

    '''
    # Disable button for cropped version because it's not work properly yet
    @classmethod
    def poll(self, context):
        return context.scene.render_settings.all_parts_rendered is True
    '''
    
    def execute(self, context):
        scene = context.scene
        print(self.bl_label)  
        RF_Utils.merge_image_parts(context)
        return{'FINISHED'}

# ------------------------------------------------------------------------
#    Panel (_PT_)
# ------------------------------------------------------------------------

class RF_PT_Panel (Panel):
    bl_label = bl_info['name']
    bl_idname = "RF_PT_Panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        #layout.operator("rp.init_renderparts", icon="FILE_REFRESH")

        # Render
        row = layout.row()
        row.label(text="Render:")
        row = layout.row()
        box = row.box()
        row.scale_y = 1.5
        #row.scale_x = 1.5
        box.alignment = 'CENTER'
        box.operator("rp.start_render", icon="RENDER_STILL")        
        box.operator("rp.stop_render", icon="X")

        # Settings
        row = layout.row()
        row.label(text="Settings:")
        row = layout.row()
        box = row.box()    

        box.prop(scene.render_settings, "render_folder")
        box.prop(scene.render_settings, "parts_count")
        box.prop(scene.render_settings, "crop_border")
        box.prop(scene.render_settings, "show_render_window")
        #box.prop(scene.render_settings, "overwrite_files")

        # Rendering Process
        row = layout.row()
        row.label(text="Rendering Process:")
        row = layout.row()
        box = row.box()       
        box.alignment = 'RIGHT'
        if (scene.render_settings.rendered_parts_count == 0):
            process_counter = '0'
        else:
            process_counter = str(scene.render_settings.rendered_parts_count) + ' / ' + str(scene.render_settings.total_parts_count)
        box.label(text="Rendered Parts: " + process_counter) 
        box.template_list("RF_UL_RenderList", "", scene, "render_list", scene, "render_list_index", rows=3, maxrows=3)
        
        # Buttons
        box.operator("rp.refresh_list", icon="FILE_REFRESH")        
        box.operator("rp.open_render_folder", icon="FILE_FOLDER")
        box.operator("rp.reset_border", icon="SELECT_SET")
        
        # Merge Images
        '''
        row = layout.row()
        #TODO: Merge images feature not work properly
        row.label(text="Finalize Image (EXPERIMENTAL):")
        row = layout.row()
        box = row.box()
        row.scale_y = 1.5
        box.operator("rp.merge_images", icon="FILE_IMAGE")
        '''
        
        row = layout.row()
        row.alignment = 'RIGHT'
        row.label(text=bl_info['name'] + ' - ' + str(bl_info['version']).strip('()'))

# ------------------------------------------------------------------------
#    UIList (_UL_)
# ------------------------------------------------------------------------

class RF_UL_RenderList (UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.7)
        split.label(text=item.image_name, icon = 'IMAGE_DATA')


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

@persistent
def init_renderparts_member(dummy):
    bpy.ops.rp.init('INVOKE_DEFAULT')

classes = (

    # Operators
    RF_OT_Init,
    RF_OT_StartRender,
    RF_OT_StopRender,
    RF_OT_RefreshList,
    RF_OT_OpenRenderFolder,
    RF_OT_ResetBorder,
    RF_OT_MergeImages,

    # Panel
    RF_PT_Panel,
    
    # List
    RF_PROP_RenderSettings,
    RF_PROP_RenderListItem,
    RF_UL_RenderList,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Custom scene properties
    bpy.types.Scene.render_settings = PointerProperty(type = RF_PROP_RenderSettings)
    bpy.types.Scene.render_list = CollectionProperty(type = RF_PROP_RenderListItem)
    bpy.types.Scene.render_list_index = IntProperty(name = "Index for render_list", default = 0) 

    # Used for initial image list update
    bpy.app.handlers.load_post.append(init_renderparts_member)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    # Custom scene properties
    del bpy.types.Scene.render_settings
    del bpy.types.Scene.render_list 
    del bpy.types.Scene.render_list_index

    bpy.app.handlers.load_post.remove(init_renderparts_member)

if __name__ == "__main__": register()