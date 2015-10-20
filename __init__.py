# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# TODO:

bl_info = {
    'name': 'Import/Export W4D Format (.w4d)',
    'author': 'Tarcontar',
    'version': (0, 0, 1),
    "blender": (2, 6, 5),
    "api": 36079,
    'location': 'File > Import/Export > W4D (.w4d)',
    'description': 'Import or Export the W4D-Format (.w4d)',
    'warning': 'Still in Progress',
	'tracker_url': '',
    'category': 'Import'}

# To support reload properly, try to access a package var, if it's there,
# reload everything
if "bpy" in locals():
    import imp
    if 'import_w4d' in locals():
        imp.reload(import_w3d)
        imp.reload(struct_w3d)

import time
import datetime
import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ImportW3D(bpy.types.Operator, ImportHelper):
    '''Import from W4D file format (.w4d)'''
    bl_idname = 'import_mesh.w4d'
    bl_label = 'Import W4D'
    bl_options = {'UNDO'}
	
    filename_ext = '.w4d'
    filter_glob = StringProperty(default='*.w4d', options={'HIDDEN'})
	
    bpy.types.Object.sklFile = bpy.props.StringProperty(name = 'sklFile', options={'HIDDEN', 'SKIP_SAVE'})

    def execute(self, context):
        from . import import_w4d
        print('Importing file', self.filepath)
        t = time.mktime(datetime.datetime.now().timetuple())
        with open(self.filepath, 'rb') as file:
            import_w4d.MainImport(self.filepath, context, self)
        t = time.mktime(datetime.datetime.now().timetuple()) - t
        print('Finished importing in', t, 'seconds')
        return {'FINISHED'}

		
def menu_func_export(self, context):
    self.layout.operator(ExportW4D.bl_idname, text='W4D (.w4d)')

def menu_func_import(self, context):
    self.layout.operator(ImportW4D.bl_idname, text='W4D (.w4d)')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()
