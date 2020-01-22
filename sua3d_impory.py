
bl_info = {
    "name": "Import Lisomn_Binary Motion (.sua3d)",
    "description": "Import Lisomn_Binary Motion.",
    "author": "Lisomn",
    "version": (2020, 101, 22),
    "blender": (2, 7, 9),
    "location": "File > Import > Lisomn_Binary Motion",
    "Lisomn_url": "https://space.bilibili.com/8720154",
    "category": "Import-Export",
}

import bpy, math, shlex, struct, os, sys, glob

from bpy.props import *
from bpy_extras.io_utils import ImportHelper, unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image
from mathutils import Matrix, Quaternion, Vector

def load_sua3d(filename,faxis):
    fname = filename.split("/")[-1].split("\\")[-1].split(".")[0]
    file = open(filename, "rb")
    magic = struct.unpack("<16s",file.read(16))[0]
    if magic != b"\xbf#Lisomn_Binary#":
        raise Exception("Not an sua3d file: '%s'", magic)
    bone_name_size = struct.unpack("<I",file.read(4))[0]
    bone_name=struct.unpack("<"+str(bone_name_size)+"s",file.read(bone_name_size))[0]
    parent = struct.unpack("<f",file.read(4))[0]
    print(bone_name,":sua3d bone_name:",parent,":parent")
    bpy.ops.object.armature_add(view_align=False, enter_editmode=False, location=(0, 0, 0), layers=(True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False))
    bpy.ops.object.editmode_toggle()
    #bpy.context.object.data.name = str(bone_name,encoding="utf-8")
    bpy.ops.object.posemode_toggle()
    bpy.context.object.pose.bones["Bone"].rotation_mode = 'XYZ'
    obj = bpy.context.object
    axis_info=[]
    axis_set=[0,1,2]
    #         x z y
    axis_set_y=[0,2,1]
    if faxis == 'Y':
        axis_info=axis_set_y
    max_frame=250
    for i in range(0,9):
        type1_size = struct.unpack("<I",file.read(4))[0]
        type1 = struct.unpack("<"+str(type1_size)+"s",file.read(type1_size))[0]
        type2_size = struct.unpack("<I",file.read(4))[0]
        type2 = struct.unpack("<"+str(type2_size)+"s",file.read(type2_size))[0]
        motion_type = struct.unpack("<I",file.read(4))[0]
        print(type1,type2,motion_type)
        if motion_type != 0:
            sindex=0
            if motion_type == 1:
                #TODO one value
                frame_key = struct.unpack("<f",file.read(4))[0]
                if type1 == b'Rot':
                    if type2 == b'X':
                        obj.pose.bones["Bone"].rotation_euler[0]=frame_key
                        sindex=0
                    elif type2 == b'Y':
                        obj.pose.bones["Bone"].rotation_euler[1]=frame_key
                        sindex=1
                    elif type2 == b'Z':
                        sindex=2
                        obj.pose.bones["Bone"].rotation_euler[2]=frame_key
                    obj.pose.bones["Bone"].keyframe_insert(data_path="rotation_euler",frame=0,index=sindex)
                elif type1 == b'Trans':
                    if type2 == b'X':
                        obj.pose.bones["Bone"].location[0]=frame_key
                        sindex=0
                    elif type2 == b'Y':
                        obj.pose.bones["Bone"].location[1]=frame_key
                        sindex=1
                    elif type2 == b'Z':
                        obj.pose.bones["Bone"].location[2]=frame_key
                        sindex=2
                    obj.pose.bones["Bone"].keyframe_insert(data_path="location",frame=0,index=sindex)
            elif motion_type == 2:
                motion_count=struct.unpack("<I",file.read(4))[0]
                if motion_count > max_frame:
                    max_frame=motion_count
                rel_count=struct.unpack("<I",file.read(4))[0]
                for a in range(0,rel_count):
                    frame_time=struct.unpack("<I",file.read(4))[0]
                    frame_key=struct.unpack("<f",file.read(4))[0]
                    if type1 == b'Rot':
                        if type2 == b'X':
                            obj.pose.bones["Bone"].rotation_euler[0]=frame_key
                            sindex=0
                        elif type2 == b'Y':
                            obj.pose.bones["Bone"].rotation_euler[1]=frame_key
                            sindex=1
                        elif type2 == b'Z':
                            sindex=2
                            obj.pose.bones["Bone"].rotation_euler[2]=frame_key
                        obj.pose.bones["Bone"].keyframe_insert(data_path="rotation_euler",frame=frame_time,index=sindex)
                    elif type1 == b'Trans':
                        if type2 == b'X':
                            obj.pose.bones["Bone"].location[0]=frame_key
                            sindex=0
                        elif type2 == b'Y':
                            obj.pose.bones["Bone"].location[1]=frame_key
                            sindex=1
                        elif type2 == b'Z':
                            obj.pose.bones["Bone"].location[2]=frame_key
                            sindex=2
                        obj.pose.bones["Bone"].keyframe_insert(data_path="location",frame=frame_time,index=sindex)
    if max_frame != 250:
        bpy.context.scene.frame_end=max_frame
    obj.pose.bones["Bone"].name=str(bone_name,encoding="utf-8")
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    bpy.context.scene.sync_mode = 'FRAME_DROP'
    bpy.context.scene.render.fps = 60
    bpy.context.scene.render.fps_base = 1
    
                    
                

def import_sua3d(filename,axiss):
    if filename.endswith(".sua3d"):
        load_sua3d(filename,axiss)
    dir=os.path.dirname(filename)
    bpy.ops.screen.frame_jump()

class ImportSua3d(bpy.types.Operator, ImportHelper):
    bl_idname = "import.sua3d"
    bl_label = "Import sua3d"

    filename_ext = ".sua3d"
    filter_glob = StringProperty(default="*.sua3d", options={'HIDDEN'})
    filepath = StringProperty(name="File Path", maxlen=1024, default="")

    bone_axis = EnumProperty(name="Bone Axis",
           description="Flip bones to extend along the Y axis",
           items=[
               ('Y', "Preserve", ""),
               ('fucku',"fucku","")
           ],
           default='Y')

    def execute(self, context):
        print(self.properties.filepath)
        import_sua3d(self.properties.filepath,self.bone_axis)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(ImportSua3d.bl_idname, text="Lisomn Motion (.sua3d)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
    if len(sys.argv) > 4 and sys.argv[-2] == '--':
        if "*" in sys.argv[-1]:
            batch_many(glob.glob(sys.argv[-1]))
        else:
            batch(sys.argv[-1])
    elif len(sys.argv) > 4 and sys.argv[4] == '--':
        batch_many(sys.argv[5:])