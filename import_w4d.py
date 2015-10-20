#Written Michael Schnabel
#Last Modification 19.10.2015
#Loads the W4D Format
import bpy
import operator
import struct
import os
import math
import sys
import bmesh
from bpy.props import *
from mathutils import Vector, Quaternion
from . import struct_w4d 

#TODO 

#######################################################################################
# Basic Methods
#######################################################################################

def ReadString(file):
    bytes = []
    b = file.read(1)
    while ord(b)!=0:
        bytes.append(b)
        b = file.read(1)
    return (b"".join(bytes)).decode("utf-8")

def ReadRGBA(file):
    return struct_w3d.RGBA(r=ord(file.read(1)), g=ord(file.read(1)), b=ord(file.read(1)), a=ord(file.read(1)))

def GetChunkSize(data):
    return (data & 0x7FFFFFFF)

def ReadLong(file):
    #binary_format = "<l" long
    return (struct.unpack("<L", file.read(4))[0])

def ReadShort(file):
    #binary_format = "<h" short
    return (struct.unpack("<H", file.read(2))[0])

def ReadUnsignedShort(file):
    return (struct.unpack("<h", file.read(2))[0])

def ReadLongArray(file,chunkEnd):
    LongArray = []
    while file.tell() < chunkEnd:
        LongArray.append(ReadLong(file))
    return LongArray

def ReadFloat(file):
    #binary_format = "<f" float
    return (struct.unpack("f", file.read(4))[0])

def ReadSignedByte(file):
    return (struct.unpack("<b", file.read(1))[0])

def ReadUnsignedByte(file):
    return (struct.unpack("<B", file.read(1))[0])

def ReadVector(file):
    return Vector((ReadFloat(file), ReadFloat(file), ReadFloat(file)))

def ReadQuaternion(file):
    quat = (ReadFloat(file), ReadFloat(file), ReadFloat(file), ReadFloat(file))
    #change order from xyzw to wxyz
    return Quaternion((quat[3], quat[0], quat[1], quat[2]))

#######################################################################################
# Hierarchy
#######################################################################################

def ReadHierarchyHeader(file):
    HierarchyHeader = struct_w4d.HierarchyHeader()
    HierarchyHeader.name = ReadString(file)
    HierarchyHeader.pivotCount = ReadLong(file)
    HierarchyHeader.centerPos = ReadVector(file)
    return HierarchyHeader

def ReadPivots(file, chunkEnd):
    pivots = []
    while file.tell() < chunkEnd:
        pivot = struct_w4d.HierarchyPivot()
        pivot.name = ReadString(file)
        pivot.parentID = ReadLong(file)
        pivot.isBone = ReadUnsignedByte(file)
        pivot.position = ReadVector(file)
        pivot.rotation = ReadQuaternion(file)
        pivots.append(pivot)
    return pivots

def ReadHierarchy(file, self, chunkEnd):
    #print("\n### NEW HIERARCHY: ###")
    HierarchyHeader = struct_w4d.HierarchyHeader()
    Pivots = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 257:
            HierarchyHeader = ReadHierarchyHeader(file)
            #print("Header")
        elif chunkType == 258:
            Pivots = ReadPivots(file, subChunkEnd)
            #print("Pivots")
        else:
            self.report({'ERROR'}, "unknown chunktype in Hierarchy: %s" % chunkType)
            print("!!!unknown chunktype in Hierarchy: %s" % chunkType)
            file.seek(chunkSize, 1)
    return struct_w4d.Hierarchy(header = HierarchyHeader, pivots = Pivots)

#######################################################################################
# Animation
#######################################################################################

def ReadAnimationHeader(file):
    return struct_w4d.AnimationHeader(name = ReadString(file), hieraName = ReadString(file), numFrames = ReadLong(file), frameRate = ReadLong(file))

def ReadTimeCodedAnimationChannel(file, self, chunkEnd):
    VectorLen = ReadShort(file)
    Type = ReadShort(file)
    Pivot = ReadShort(file)
    TimeCodedKeys = []
    if VectorLen == 1:
        while file.tell() < chunkEnd:
            key = struct_w4d.TimeCodedAnimationKey()
            key.frame = ReadShort(file)
            key.value = ReadFloat(file)
            TimeCodedKeys.append(key)
    elif VectorLen == 4:
        while file.tell() < chunkEnd:
            key = struct_w4d.TimeCodedAnimationKey()
            key.frame = ReadShort(file)
            key.value = ReadQuaternion(file)
            TimeCodedKeys.append(key)
    else:
        self.report({'ERROR'}, "!!!unsupported vector len %s" % VectorLen)
        print("!!!unsupported vector len %s" % VectorLen)
        while file.tell() < chunkEnd:
            file.read(1)
    return struct_w4d.AnimationChannel(vectorLen = VectorLen, type = Type, pivot = Pivot, timeCodedKeys = TimeCodedKeys)

def ReadAnimation(file, self, chunkEnd):
    #print("\n### NEW ANIMATION: ###")
    Header = struct_w4d.AnimationHeader()
    Channels = []
    while file.tell() < chunkEnd:
        chunkType = ReadLong(file)
        chunkSize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + chunkSize
        if chunkType == 513:
            Header = ReadAnimationHeader(file)
        elif chunkType == 514:
            Channels.append(ReadTimeCodedAnimationChannel(file, self, subChunkEnd))
        else:
            self.report({'ERROR'}, "unknown chunktype in Animation: %s" % chunkType)
            print("!!!unknown chunktype in Animation: %s" % chunkType)
            file.seek(chunkSize, 1)
    return struct_w4d.Animation(header = Header, channels = Channels)

#######################################################################################
# Box
#######################################################################################	

def ReadBox(file):
    #print("\n### NEW BOX: ###")
    center = ReadVector(file)
    extend = ReadVector(file)
    return struct_w4d.Box(center = center, extend = extend)

#######################################################################################
# Texture
#######################################################################################	



#######################################################################################
# Material
#######################################################################################	


#######################################################################################
# Vertices
#######################################################################################

def ReadMeshVerticesArray(file, chunkEnd):
    verts = []
    while file.tell() < chunkEnd:
        verts.append(ReadVector(file))
    return verts

def ReadMeshVertexInfluences(file, chunkEnd):
    vertInfs = []
    while file.tell()  < chunkEnd:
        vertInf = struct_w4d.MeshVertexInfluences()
        vertInf.boneIdx = ReadShort(file)
        vertInf.bone2Idx = ReadShort(file)
        vertInf.boneInf = ReadShort(file)/100
        vertInf.bone2Inf = ReadShort(file)/100
        vertInfs.append(vertInf)
    return vertInfs

#######################################################################################
# Faces
#######################################################################################	

def ReadMeshFaceArray(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append(ReadMeshFace(file))
    return faces

#######################################################################################
# Mesh
#######################################################################################	

def ReadMeshHeader(file):
    result = struct_w4d.MeshHeader(attrs =  ReadLong(file), meshName = ReadFixedString(file), 
		containerName = ReadFixedString(file), faceCount = ReadLong(file), vertCount = ReadLong(file), 
		#bounding volumes
		minCorner = ReadVector(file),
		maxCorner = ReadVector(file),
		sphCenter = ReadVector(file),
		sphRadius =  ReadFloat(file))
    return result

def ReadMesh(self, file, chunkEnd):
    MeshHeader = struct_w4d.MeshHeader()
    MeshVerticesInfs = []
    MeshVertices = []
    MeshNormals = []
    MeshFaces = []
    MeshMaterials = []

    #print("\n### NEW MESH: ###")
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize

        if Chunktype == 1:
            try:
                MeshHeader = ReadMeshHeader(file)
                #print("## Name: " + MeshHeader.meshName)
                #print("Header")
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh Header (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh Header (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 2:
            try:
                MeshVertices = ReadMeshVerticesArray(file, subChunkEnd)
                #print("Vertices")
            except:
                self.report({'ERROR'}, "Mistake while reading Vertices (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Vertices (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 3:
            try:
                MeshNormals = ReadMeshVerticesArray(file, subChunkEnd)
                #print("Normals")
            except:
                self.report({'ERROR'}, "Mistake while reading Normals (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Normals (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 4:
            try:
                MeshVerticesInfs = ReadMeshVertexInfluences(file, subChunkEnd)
                #print("VertInfs")
            except:
                self.report({'ERROR'}, "Mistake while reading Usertext (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Usertext (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 5:
            try:
                MeshFaces = ReadMeshFaceArray(file, subChunkEnd)
                #print("Faces")
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh Faces (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh Faces (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 6:
            try:
                MeshMaterials = ReadMeshMaterial(file, subChunkEnd)
                #print("Faces")
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh Material (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh Material (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)				
        else:
            self.report({'ERROR'}, "unknown chunktype in Mesh: %s" % Chunktype)
            print("!!!unknown chunktype in Mesh: %s" % Chunktype)
            file.seek(Chunksize,1)
    return struct_w3d.Mesh(header = MeshHeader, verts = MeshVertices, normals = MeshNormals, vertInfs = MeshVerticesInfs, faces = MeshFaces)

#######################################################################################
# loadTexture
#######################################################################################

def LoadTexture(self, givenfilepath, mesh, texName, tex_type, destBlend):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    default_tex = script_directory + "\default_tex.dds"

    found_img = False

    basename = os.path.splitext(texName)[0]

	#test if image file has already been loaded
    for image in bpy.data.images:
        if basename == os.path.splitext(image.name)[0]:
            img = image
            found_img = True

    # Create texture slot in material
    mTex = mesh.materials[0].texture_slots.add()
    mTex.use_map_alpha = True

    if found_img == False:
        tgapath = os.path.dirname(givenfilepath) + "/" + basename + ".tga"
        ddspath = os.path.dirname(givenfilepath) + "/" + basename + ".dds"
        img = None
        try:
            img = bpy.data.images.load(tgapath)
        except:
            try:
                img = bpy.data.images.load(ddspath)
            except:
                self.report({'ERROR'}, "Cannot load image " + basename)
                print("!!! Image file not found " + basename)
                img = bpy.data.images.load(default_tex)

        cTex = bpy.data.textures.new(texName, type = 'IMAGE')
        cTex.image = img

        if destBlend == 0:
            cTex.use_alpha = True
        else:
            cTex.use_alpha = False

        if tex_type == "normal":
            cTex.use_normal_map = True
            cTex.filter_size = 0.1
            cTex.use_filter_size_min = True
        mTex.texture = cTex	
    else:
        mTex.texture = bpy.data.textures[texName]

    mTex.texture_coords = 'UV'
    mTex.mapping = 'FLAT'
    if tex_type == "normal":
       mTex.normal_map_space = 'TANGENT'
       mTex.use_map_color_diffuse = False
       mTex.use_map_normal = True
       mTex.normal_factor = 1.0
       mTex.diffuse_color_factor = 0.0

#######################################################################################
# loadSkeleton 
#######################################################################################

def LoadSKL(self, sklpath):
    #print("\n### SKELETON: ###")
    Hierarchy = struct_w3d.Hierarchy()
    file = open(sklpath, "rb")
    file.seek(0,2)
    filesize = file.tell()
    file.seek(0,0)

    while file.tell() < filesize:
        chunkType = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize
        if chunkType == 256:
            Hierarchy = ReadHierarchy(file, self, chunkEnd)
            file.seek(chunkEnd, 0)
        else:
            file.seek(Chunksize, 1)
    file.close()
    return Hierarchy
	
#######################################################################################
# createArmature
#######################################################################################
	
def createArmature(self, Hierarchy, amtName, subObjects):
    amt = bpy.data.armatures.new(Hierarchy.header.name)
    amt.show_names = True
    rig = bpy.data.objects.new(amtName, amt)
    rig.location = Hierarchy.header.centerPos
    rig.rotation_mode = 'QUATERNION'
    rig.show_x_ray = True
    rig.track_axis = "POS_X"
    bpy.context.scene.objects.link(rig) # Link the object to the active scene
    bpy.context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.context.scene.update()

    non_bone_pivots = []
    for obj in subObjects: 
        non_bone_pivots.append(Hierarchy.pivots[obj.boneIndex])

	#create the bones from the pivots
    for pivot in Hierarchy.pivots:
        #test for non_bone_pivots
        if non_bone_pivots.count(pivot) > 0:
                continue #do not create a bone
        bone = amt.edit_bones.new(pivot.name)
        if pivot.parentID > 0:
            parent_pivot =  Hierarchy.pivots[pivot.parentID]
            parent = amt.edit_bones[parent_pivot.name]
            bone.parent = parent
            size = pivot.position.x
        bone.head = Vector((0.0, 0.0, 0.0))
	    #has to point in y direction that the rotation is applied correctly
        bone.tail = Vector((0.0, 0.1, 0.0))

    #pose the bones
    bpy.ops.object.mode_set(mode = 'POSE')
    
    script_directory = os.path.dirname(os.path.abspath(__file__))
    bone_file = script_directory + "\\bone.W3D"
	
    bone_shape = loadBoneMesh(self, bone_file)

    for pivot in Hierarchy.pivots:
        #test for non_bone_pivots
        if non_bone_pivots.count(pivot) > 0:
                continue #do not create a bone
        bone = rig.pose.bones[pivot.name]
        bone.location = pivot.position
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_euler = pivot.eulerAngles
        bone.rotation_quaternion = pivot.rotation
        #bpy.data.objects["Bone"].scale = (4, 4, 4)
        bone.custom_shape = bpy.data.objects["skl_bone"]

    bpy.ops.object.mode_set(mode = 'OBJECT')
	
	#delete the mesh afterwards
    for ob in bpy.context.scene.objects:
        if ob.type == 'MESH' and ob.name.startswith("skl_bone"):
            ob.delete()
    return rig
	
#######################################################################################
# createAnimation
#######################################################################################

def createAnimation(self, Animation, Hierarchy, rig, compressed):
    bpy.data.scenes["Scene"].render.fps = Animation.header.frameRate
    bpy.data.scenes["Scene"].frame_start = 1
    bpy.data.scenes["Scene"].frame_end = Animation.header.numFrames

	#create the data
    translation_data = []
    for pivot in range (0, len(Hierarchy.pivots)):
        pivot = []
        for frame in range (0, Animation.header.numFrames):
            frame = []
            frame.append(None)
            frame.append(None)
            frame.append(None)
            pivot.append(frame)
        translation_data.append(pivot)
	
    for channel in Animation.channels:
        if (channel.pivot == 0):
            continue   #skip roottransform
        rest_rotation = Hierarchy.pivots[channel.pivot].rotation
        pivot = Hierarchy.pivots[channel.pivot] 
        try:
            obj = rig.pose.bones[pivot.name]
        except:
            obj = bpy.data.objects[pivot.name]
			
        # ANIM_CHANNEL_X
        if channel.type == 0:   
            if compressed:
                for key in channel.timeCodedKeys:
                    translation_data[channel.pivot][key.frame][0] = key.value
            else:
                for frame in range(channel.firstFrame, channel.lastFrame):
                    translation_data[channel.pivot][frame][0] = channel.data[frame - channel.firstFrame]
        # ANIM_CHANNEL_Y
        elif channel.type == 1:   
            if compressed:
                for key in channel.timeCodedKeys:
                    translation_data[channel.pivot][key.frame][1] = key.value
            else:
                for frame in range(channel.firstFrame, channel.lastFrame):
                    translation_data[channel.pivot][frame][1] = channel.data[frame - channel.firstFrame]
        # ANIM_CHANNEL_Z
        elif channel.type == 2:  
            if compressed:
                for key in channel.timeCodedKeys:
                    translation_data[channel.pivot][key.frame][2] = key.value
            else:
                for frame in range(channel.firstFrame, channel.lastFrame):
                    translation_data[channel.pivot][frame][2] = channel.data[frame - channel.firstFrame]
		
	    # ANIM_CHANNEL_Q
        elif channel.type == 6:  
            obj.rotation_mode = 'QUATERNION'
            if compressed:
                for key in channel.timeCodedKeys:
                    obj.rotation_quaternion = rest_rotation * key.value
                    obj.keyframe_insert(data_path='rotation_quaternion', frame = key.frame) 
            else:
                for frame in range(channel.firstFrame, channel.lastFrame):
                    obj.rotation_quaternion = rest_rotation * channel.data[frame - channel.firstFrame]
                    obj.keyframe_insert(data_path='rotation_quaternion', frame = frame)  
        else:
            self.report({'ERROR'}, "unsupported channel type: %s" %channel.type)
            print("unsupported channel type: %s" %channel.type)

    for pivot in range(1, len(Hierarchy.pivots)):
        rest_location = Hierarchy.pivots[pivot].position
        rest_rotation = Hierarchy.pivots[pivot].rotation 
        lastFrameLocation = Vector((0.0, 0.0, 0.0))
        try:
            obj = rig.pose.bones[Hierarchy.pivots[pivot].name]
        except:
            obj = bpy.data.objects[Hierarchy.pivots[pivot].name]
			
        for frame in range (0, Animation.header.numFrames):
            bpy.context.scene.frame_set(frame)	
            pos = Vector((0.0, 0.0, 0.0))

            if not translation_data[pivot][frame][0] == None:
                pos[0] = translation_data[pivot][frame][0]
                if not translation_data[pivot][frame][1] == None:
                    pos[1] = translation_data[pivot][frame][1]
                if not translation_data[pivot][frame][2] == None:	
                    pos[2] = translation_data[pivot][frame][2]
                obj.location = rest_location + (rest_rotation * pos)
                obj.keyframe_insert(data_path='location', frame = frame) 
                lastFrameLocation = pos
					
            elif not translation_data[pivot][frame][1] == None:
                pos[1] = translation_data[pivot][frame][1]
                if not translation_data[pivot][frame][2] == None:
                    pos[2] = translation_data[pivot][frame][2]
                obj.location = rest_location + (rest_rotation * pos)
                obj.keyframe_insert(data_path='location', frame = frame) 
                lastFrameLocation = pos
				
            elif not translation_data[pivot][frame][2] == None:
                pos[2] = translation_data[pivot][frame][2]
                obj.location = rest_location + (rest_rotation * pos)
                obj.keyframe_insert(data_path='location', frame = frame)			
                lastFrameLocation = pos

#######################################################################################
# create Box
#######################################################################################
		
def createBox(Box):	
    name = "BOUNDINGBOX" #to keep name always equal (sometimes it is "BOUNDING BOX")
    x = Box.extend[0]/2
    y = Box.extend[1]/2
    z = Box.extend[2]

    verts = [(x, y, z), (-x, y, z), (-x, -y, z), (x, -y, z), (x, y, 0), (-x, y, 0), (-x, -y, 0), (x, -y, 0)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]

    cube = bpy.data.meshes.new(name)
    box = bpy.data.objects.new(name, cube)
    mat = bpy.data.materials.new("BOUNDINGBOX.Material")
    mat.use_shadeless = True
    cube.materials.append(mat)
    box.location = Box.center
    bpy.context.scene.objects.link(box)
    cube.from_pydata(verts, [], faces)
    cube.update(calc_edges = True)
    #set render mode to wireframe
    box.draw_type = 'WIRE'
	
#######################################################################################
# Main Import
#######################################################################################

def MainImport(givenfilepath, context, self):
    file = open(givenfilepath,"rb")
    file.seek(0,2)
    filesize = file.tell()
    file.seek(0,0)
    Meshes = []
    Box = struct_w4d.Box()
    Hierarchy = struct_w4d.Hierarchy()
    Animation = struct_w4d.Animation()
    CompressedAnimation = struct_w3d.CompressedAnimation()
    HLod = struct_w3d.HLod()
    amtName = ""

    while file.tell() < filesize:
        Chunktype = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize
        if Chunktype == 0:
            m = ReadMesh(self, file, chunkEnd)
            Meshes.append(m)
            file.seek(chunkEnd,0)

        elif Chunktype == 256:
            Hierarchy = ReadHierarchy(file, self, chunkEnd)
            file.seek(chunkEnd,0)

        elif Chunktype == 512:
            Animation = ReadAnimation(file, self, chunkEnd)
            file.seek(chunkEnd,0)

        elif Chunktype == 1024:
            Box = ReadBox(file)
            file.seek(chunkEnd,0)

        else:
            self.report({'ERROR'}, "unknown chunktype in File: %s" % Chunktype)
            print("!!!unknown chunktype in File: %s" % Chunktype)
            file.seek(Chunksize,1)

    file.close()

    if not Box.name == "":
        createBox(Box)
	
	#load skeleton (_skl.w4d) file if needed 
    sklpath = ""
    if HLod.header.modelName != HLod.header.HTreeName:
        sklpath = os.path.dirname(givenfilepath) + "\\" + HLod.header.HTreeName.lower() + ".w3d"
        try:
            Hierarchy = LoadSKL(self, sklpath)
        except:
            self.report({'ERROR'}, "skeleton file not found: " + HLod.header.HTreeName) 
            print("!!! skeleton file not found: " + HLod.header.HTreeName)
			
    elif (not Animation.header.name == "") and (Hierarchy.header.name == ""):
        sklpath = os.path.dirname(givenfilepath) + "\\" + Animation.header.hieraName.lower() + ".w3d"
        try:
            Hierarchy = LoadSKL(self, sklpath)
        except:
            self.report({'ERROR'}, "skeleton file not found: " + Animation.header.hieraName) 
            print("!!! skeleton file not found: " + Animation.header.hieraName)
			
    elif (not CompressedAnimation.header.name == "") and (Hierarchy.header.name == ""):
        sklpath = os.path.dirname(givenfilepath) + "\\" + CompressedAnimation.header.hieraName.lower() + ".w3d"
        try:
            Hierarchy = LoadSKL(self, sklpath)
        except:
            self.report({'ERROR'}, "skeleton file not found: " + CompressedAnimation.header.hieraName) 
            print("!!! skeleton file not found: " + CompressedAnimation.header.hieraName)

    #create skeleton if needed
    if Hierarchy.header.name.endswith('_SKL'):
        amtName = Hierarchy.header.name
        found = False
        for obj in bpy.data.objects:
            if obj.name == amtName:
                rig = obj
                found = True
        if not found:
            rig = createArmature(self, Hierarchy, amtName)
            rig.sklFile = sklpath
			#rig['sklFile'] = sklpath
        if len(Meshes) > 0:
            #if a mesh is loaded set the armature invisible
            rig.hide = True

    for m in Meshes:	
        Vertices = m.verts
        Faces = []

        for f in m.faces:
            Faces.append(f.vertIds)

        #create the mesh
        mesh = bpy.data.meshes.new(m.header.meshName)
        mesh.from_pydata(Vertices,[],Faces)
        mesh.uv_textures.new("UVW")

        bm = bmesh.new()
        bm.from_mesh(mesh)

        #create the uv map
        uv_layer = bm.loops.layers.uv.verify()
        bm.faces.layers.tex.verify()

        index = 0
        if len(m.matlPass.txStage.txCoords)>0:
            for f in bm.faces:
                f.loops[0][uv_layer].uv = m.matlPass.txStage.txCoords[Faces[index][0]]
                f.loops[1][uv_layer].uv = m.matlPass.txStage.txCoords[Faces[index][1]]
                f.loops[2][uv_layer].uv = m.matlPass.txStage.txCoords[Faces[index][2]]
                index+=1
				
        bm.to_mesh(mesh)

        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)

		#show the bounding boxes
        #mesh_ob.show_bounds = True
        #mesh_ob.draw_bounds_type = "BOX"
		
    for m in Meshes: #need an extra loop because the order of the meshes is random
        mesh_ob = bpy.data.objects[m.header.meshName]
        #hierarchy stuff
        if Hierarchy.header.pivotCount > 0:
            # mesh header attributes
            #        0      -> normal mesh
			#        8192   -> normal mesh - two sided
            #        32768  -> normal mesh - cast shadow
            #        40960  -> normal mesh - two sided - cast shadow
            #        131072 -> skin
            #        139264 -> skin - two sided
			#        143360 -> skin - two sided - hidden
			#        163840 -> skin - cast shadow
            #        172032 -> skin - two sided - cast shadow
            #        393216 -> normal mesh - camera oriented (points _towards_ camera)
            type = m.header.attrs
            if type == 8192 or type == 40960 or type == 139264 or type == 143360 or type == 172032:
                mesh.show_double_sided = True
				
            if type == 0 or type == 8192 or type == 32768 or type == 40960 or type == 393216:
                for pivot in Hierarchy.pivots:
                    if pivot.name == m.header.meshName:
                        mesh_ob.rotation_mode = 'QUATERNION'
                        mesh_ob.location =  pivot.position
                        mesh_ob.rotation_euler = pivot.eulerAngles
                        mesh_ob.rotation_quaternion = pivot.rotation
						
                        #test if the pivot has a parent pivot and parent the corresponding bone to the mesh if it has
                        if pivot.parentID > 0:
                            parent_pivot = Hierarchy.pivots[pivot.parentID]
                            try:
                                mesh_ob.parent = bpy.data.objects[parent_pivot.name]								
                            except:
                                mesh_ob.parent = bpy.data.objects[amtName]
                                mesh_ob.parent_bone = parent_pivot.name
                                mesh_ob.parent_type = 'BONE'

            elif type == 131072 or type == 139264 or type == 143360 or type == 163840 or type == 172032:
                for pivot in Hierarchy.pivots:
                    mesh_ob.vertex_groups.new(pivot.name)
						
                for i in range(len(m.vertInfs)):
                    weight = m.vertInfs[i].boneInf
                    if weight == 0.0:
                        weight = 1.0
                    mesh_ob.vertex_groups[m.vertInfs[i].boneIdx].add([i], weight, 'REPLACE')
					
					#two bones are not working yet
                    #mesh_ob.vertex_groups[m.vertInfs[i].xtraIdx].add([i], m.vertInfs[i].xtraInf, 'REPLACE')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True
				
				#to keep the transformations while mesh is in edit mode!!!
                mod.show_in_editmode = True
                mod.show_on_cage = True
            else:
                print("unsupported meshtype attribute: %i" %type)
                self.report({'ERROR'}, "unsupported meshtype attribute: %i" %type)
        bpy.context.scene.objects.link(mesh_ob) # Link the object to the active scene

    #animation stuff
    if not Animation.header.name == "":	
        try:
            createAnimation(self, Animation, Hierarchy, rig, False)
        except:
            #the animation could be completely without a rig and bones
            createAnimation(self, Animation, Hierarchy, None, False)
			
    elif not CompressedAnimation.header.name == "":	
        createAnimation(self, CompressedAnimation, Hierarchy, rig, True)
        #try:
        #    createAnimation(self, CompressedAnimation, Hierarchy, rig, True)
        #except:
        #    #the animation could be completely without a rig and bones
        #    createAnimation(self, CompressedAnimation, Hierarchy, None, True)
	
    #to render the loaded textures				
    bpy.context.scene.game_settings.material_mode = 'GLSL'
    #set render mode to textured or solid
    for scrn in bpy.data.screens:
        if scrn.name == 'Default':
            for area in scrn.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            if len(bpy.data.textures) > 1:
                                space.viewport_shade = 'TEXTURED'
                            else:
                                space.viewport_shade = 'SOLID'