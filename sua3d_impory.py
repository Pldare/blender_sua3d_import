bl_info = {
    "name": "Import Lisomn_Binary Motion (.sua3d,.sua3s,.sua3o)",
    "description": "Import Lisomn_Binary Motion.",
    "author": "Lisomn",
    "version": (2020, 6, 3),
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

def get_float(file):
    return struct.unpack("<f",file.read(4))[0]

def get_long(file):
    return struct.unpack("<I",file.read(4))[0]

def get_str(file):
    str_size=get_long(file)
    return str(struct.unpack("<"+str(str_size)+"s",file.read(str_size))[0],encoding="utf-8")

def make_bone(amt,bone_name):
    bpy.ops.object.mode_set(mode='EDIT')
    bone = amt.edit_bones.new(bone_name)
    bone.tail[2]=1
    bpy.ops.object.posemode_toggle()
    return bone

def make_amt(arm_name):
    amt=""
    if arm_name in bpy.data.armatures.keys():
        amt = bpy.data.armatures[arm_name]
    else:
        amt=bpy.data.armatures.new(arm_name)
    return amt

def make_obj(amt,arm_name):
    obj=""
    if arm_name+".amt" in bpy.data.objects.keys():
        obj = bpy.data.objects[arm_name+".amt"]
    else:
        obj=bpy.data.objects.new(arm_name + ".amt", amt)
        bpy.context.scene.objects.link(obj)
    return obj

def set_frame_end(key):
    bpy.context.scene.frame_end=key
    bpy.context.scene.sync_mode = 'FRAME_DROP'
    #bpy.context.scene.render.fps = 60
    #bpy.context.scene.render.fps_base = 1
def set_frame_fps(key):
    bpy.context.scene.render.fps = key
    bpy.context.scene.render.fps_base = 1

def load_frame(file,bone_name,obj,begin_value):
    type1=get_str(file).split("_")
    xyz_list=["X","Y","Z"]
    xyz_id=xyz_list.index(type1[1])
    type2=get_str(file)
    use_bone=obj.pose.bones[bone_name]
    if type2 != "Null":
        if type2 == "Value":
            frame_value=get_float(file)
            if type1[0] == "ROT":
                use_bone.rotation_euler[xyz_id]=frame_value
                use_bone.keyframe_insert(data_path="rotation_euler",frame=begin_value,index=xyz_id)
            elif type1[0] == "TRANS":
                use_bone.location[xyz_id]=frame_value
                use_bone.keyframe_insert(data_path="location",frame=begin_value,index=xyz_id)
            return 1
        else:
            max_count=get_long(file)
            rel_count=get_long(file)
            for i in range(0,rel_count):
                frame_key=get_long(file)
                frame_value=get_float(file)
                if type1[0] == "ROT":
                    use_bone.rotation_euler[xyz_id]=frame_value
                    use_bone.keyframe_insert(data_path="rotation_euler",frame=begin_value+frame_key,index=xyz_id)
                elif type1[0] == "TRANS":
                    use_bone.location[xyz_id]=frame_value
                    use_bone.keyframe_insert(data_path="location",frame=begin_value+frame_key,index=xyz_id)
            return begin_value+max_count
    else:
        return 0
                

def load_sua3o(file_name):
    file=open(file_name,"rb")
    print(file_name)
    arm_name=get_str(file).split("|")[-1]
    amt=make_amt(arm_name)
    obj=make_obj(amt,arm_name)
    bpy.context.scene.objects.active=obj
    bone_name=arm_name#.split("|")[-1]
    bone=make_bone(amt,bone_name)
    obj.pose.bones[bone_name].rotation_mode = 'XYZ'
    bpy.ops.object.posemode_toggle()
    
    begin_value=int(get_float(file))
    
    sub_frame_list=[]
    for i in range(0,9):
        sub_frame=load_frame(file,bone_name,obj,begin_value)
        sub_frame_list.append(sub_frame)
    bpy.ops.object.posemode_toggle()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    return max(sub_frame_list)
    
def load_sua3b(file_name):
    file=open(file_name,"rb")
    print(file_name)
    arm_name=get_str(file)
    amt=make_amt(arm_name)
    obj=make_obj(amt,arm_name)
    bpy.context.scene.objects.active=obj
    bone_name=get_str(file)
    bone=make_bone(amt,bone_name)
    obj.pose.bones[bone_name].rotation_mode = 'XYZ'
    bpy.ops.object.posemode_toggle()
    
    parent_name=get_str(file)
    
    begin_value=int(get_float(file))
    
    sub_frame_list=[]
    for i in range(0,9):
        sub_frame=load_frame(file,bone_name,obj,begin_value)
        sub_frame_list.append(sub_frame)
    bpy.ops.object.posemode_toggle()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.editmode_toggle()
    return max(sub_frame_list)#[max(sub_frame_list),parent_name]
    
    

def load_sua3s(root_dir,file_name):
    file=open(file_name,"rb")
    file_begin=get_float(file)
    file_count=get_long(file)
    max_list=[]
    for i in range(0,file_count):
        sub_name1=get_str(file)
        sub_name=""
        if sub_name1 == "bone_anim":
            block_count=get_long(file)
            for a in range(0,block_count):
                sub_name=get_str(file).replace("\\","/")
                max_frame=import_sua3(root_dir+"/"+sub_name)
                max_list.append(max_frame)
        else:
            #sub_name=get_str(file).replace("\\","/")
            max_frame=import_sua3(root_dir+"/"+sub_name1)
            max_list.append(max_frame)
    set_frame_end(max(max_list))
    file_fps=get_float(file)
    set_frame_fps(file_fps)
    
def import_sua3(file_name):
    if file_name.endswith(".sua3s"):
        load_sua3s(os.path.dirname(os.path.dirname(file_name)),file_name)
    elif file_name.endswith(".sua3o"):
        max_frame=load_sua3o(file_name)
        return max_frame
    elif file_name.endswith(".sua3b"):
        max_frame=load_sua3b(file_name)
        return max_frame
    #elif file_name.endswith(".sua3b"):
    #elif file_name.endswith(".sua3o"):
    #dir=os.path.dirname(os.path.dirname(file_name))
    #print(dir)
    #bpy.ops.screen.frame_jump()

class ImportSua3d(bpy.types.Operator, ImportHelper):
    bl_idname = "import.sua3"
    bl_label = "Import sua3b sua3s sua3o"

    filename_ext = ".sua3d,.sua3s,.sua3o"
    filter_glob = StringProperty(default="*.sua3[sob]", options={'HIDDEN'})
    filepath = StringProperty(name="File Path", maxlen=1024, default="")

    #bone_axis = EnumProperty(name="Bone Axis",
    #       description="Flip bones to extend along the Y axis",
    #       items=[
    #           ('Y', "Preserve", ""),
    #           ('fucku',"fucku","")
    #       ],
    #       default='Y')

    def execute(self, context):
        print(self.properties.filepath)
        import_sua3(self.properties.filepath)
        #import_sua3d(self.properties.filepath,self.bone_axis)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(ImportSua3d.bl_idname, text="Lisomn Motion (.sua3b,.sua3s,.sua3o)")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)

if __name__ == "__main__":
    register()
