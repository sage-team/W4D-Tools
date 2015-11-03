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
    while ord(b) != 0:
        bytes.append(b)
        b = file.read(1)
    return (b"".join(bytes)).decode("utf-8")

def ReadRGBA(file):
    return struct_w4d.RGBA(r=ord(file.read(1)), g=ord(file.read(1)), b=ord(file.read(1)), a=ord(file.read(1)))

def GetChunkSize(data):
    return (data & 0x7FFFFFFF)

def ReadLong(file):
    #binary_format = "<l" long
    return (struct.unpack("<L", file.read(4))[0])

def ReadShort(file):
    #binary_format = "<h" short
    return (struct.unpack("<H", file.read(2))[0])

def ReadSignedShort(file):
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
        pivot.parentID = ReadSignedShort(file)
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
    print("\n### NEW ANIMATION: ###")
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
# Model
#######################################################################################

def ReadModel(file):
    print("\n### MODEL: ###")
    model = struct_w4d.Model()
    model.name = ReadString(file)
    model.hieraName = ReadString(file)
    print(model.name)
    print(model.hieraName)
    return model

#######################################################################################
# Box
#######################################################################################	

def ReadBox(file):
    #print("\n### NEW BOX: ###")
    center = ReadVector(file)
    extend = ReadVector(file)
    return struct_w4d.Box(center = center, extend = extend)

#######################################################################################
# Vertices
#######################################################################################

def ReadMeshVerticesArray(file, chunkEnd):
    verts = []
    while file.tell() < chunkEnd:
        verts.append(ReadVector(file))
    return verts

#######################################################################################
# Faces
#######################################################################################	

def ReadMeshFaces(file, chunkEnd):
    faces = []
    while file.tell() < chunkEnd:
        faces.append((ReadLong(file), ReadLong(file), ReadLong(file)))
    return faces
	
#######################################################################################
# UVCoords
#######################################################################################	

def ReadMeshUVCoords(file, chunkEnd):
    uvCoords = []
    while file.tell() < chunkEnd:
       uvCoords.append((ReadFloat(file), ReadFloat(file)))
    return uvCoords
	
#######################################################################################
# VertexInfluences
#######################################################################################	
	
def ReadMeshVertexInfluences(file, chunkEnd):
    vertInfs = []
    while file.tell()  < chunkEnd:
        vertInf = struct_w4d.MeshVertexInfluences()
        vertInf.boneIdx = ReadShort(file)
        vertInf.boneInf = ReadShort(file)/100
        vertInfs.append(vertInf)
    return vertInfs
	
#######################################################################################
# Texture
#######################################################################################	

def ReadTexture(file):
    #print("Texture")
    tex = struct_w4d.Texture()
    tex.name = ReadString(file)
    tex.type = ReadUnsignedByte(file)
    tex.value = ReadFloat(file)
	
    # read texture animations
    return tex

#######################################################################################
# Material
#######################################################################################	

def ReadMeshMaterial(file, chunkEnd):
    mat = struct_w4d.MeshMaterial()
    mat.diffuse = ReadRGBA(file)
    mat.diffuse_intensity = ReadFloat(file)
    mat.specular = ReadRGBA(file)
    mat.specular_intensity = ReadFloat(file)
    mat.emit = ReadFloat(file)
    mat.alpha = ReadFloat(file)
    mat.textures = []
	
    while file.tell() < chunkEnd:
        Chunktype = ReadLong(file)
        Chunksize = GetChunkSize(ReadLong(file))
        subChunkEnd = file.tell() + Chunksize
		
        if Chunktype == 31:
            mat.textures.append(ReadTexture(file))
        else:
            self.report({'ERROR'}, "unknown chunktype in MeshMaterial: %s" % Chunktype)
            print("!!!unknown chunktype in MeshMaterial: %s" % Chunktype)
            file.seek(Chunksize,1)
    return mat

#######################################################################################
# Mesh
#######################################################################################	

def ReadMeshHeader(file):
    result = struct_w4d.MeshHeader(type =  ReadUnsignedByte(file), meshName = ReadString(file), 
		parentPivot = ReadShort(file), faceCount = ReadLong(file), vertCount = ReadLong(file), 
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

        if Chunktype == 2:
            try:
                MeshHeader = ReadMeshHeader(file)
                print("## MeshName: " + MeshHeader.meshName)
                #print("Header")               
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh Header (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh Header (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 3:
            try:
                MeshVertices = ReadMeshVerticesArray(file, subChunkEnd)
                #print("Vertices")
            except:
                self.report({'ERROR'}, "Mistake while reading Vertices (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Vertices (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 4:
            try:
                MeshNormals = ReadMeshVerticesArray(file, subChunkEnd)
                #print("Normals")
            except:
                self.report({'ERROR'}, "Mistake while reading Normals (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Normals (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 5:
            try:
                MeshFaces = ReadMeshFaces(file, subChunkEnd)
                #print("Faces")
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh Faces (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh Faces (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 6:
            try:
                MeshUVCoords = ReadMeshUVCoords(file, subChunkEnd)
                #print("UVCoords")
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh UVCoords (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh UVCoords (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 7:
            try:
                MeshVerticesInfs = ReadMeshVertexInfluences(file, subChunkEnd)
                #print("VertInfs")
            except:
                self.report({'ERROR'}, "Mistake while reading Usertext (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Usertext (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)
        elif Chunktype == 30:
            try:
                MeshMaterials.append(ReadMeshMaterial(file, subChunkEnd))
                #print("Material")
            except:
                self.report({'ERROR'}, "Mistake while reading Mesh Material (Mesh) Byte:%s" % file.tell())
                print("Mistake while reading Mesh Material (Mesh) Byte:%s" % file.tell())
                e = sys.exc_info()[1]
                print(e)				
        else:
            self.report({'ERROR'}, "unknown chunktype in Mesh: %s" % Chunktype)
            print("!!!unknown chunktype in Mesh: %s" % Chunktype)
            file.seek(Chunksize,1)
    return struct_w4d.Mesh(header = MeshHeader, verts = MeshVertices, normals = MeshNormals, faces = MeshFaces, 
		uvCoords = MeshUVCoords, vertInfs = MeshVerticesInfs, materials = MeshMaterials)

#######################################################################################
# loadTexture
#######################################################################################

def LoadTexture(self, givenfilepath, mesh, material, tex):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    default_tex = script_directory + "\default_tex.dds"

    found_img = False

    basename = os.path.splitext(tex.name)[0]

	#test if image file has already been loaded
    for image in bpy.data.images:
        if basename == os.path.splitext(image.name)[0]:
            img = image
            found_img = True

    # Create texture slot in material
    mTex = material.texture_slots.add()
    mTex.use_map_alpha = True

    if found_img == False:
        img = None
        path = os.path.dirname(givenfilepath) + "/" + basename
        try:
            img = bpy.data.images.load(path + ".tga")
        except:
            try:
                img = bpy.data.images.load(path + ".dds")
            except:
                try:
                    img = bpy.data.images.load(path + ".png")
                except:
                    try:
                        img = bpy.data.images.load(path + ".jpg")
                    except:
                        self.report({'ERROR'}, "Cannot load image " + basename)
                        print("!!! Image file not found " + basename)
                        img = bpy.data.images.load(default_tex)

        cTex = bpy.data.textures.new(tex.name, type = 'IMAGE')
        cTex.image = img
		
        if material.use_transparency:
            cTex.use_alpha = False

        if tex.type == 1:
            cTex.use_normal_map = True
            cTex.filter_size = 0.1
            cTex.use_filter_size_min = True
        mTex.texture = cTex	
    else:
        mTex.texture = bpy.data.textures[tex.name]

    mTex.texture_coords = 'UV'
    mTex.mapping = 'FLAT'
    if tex.type == 1:
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
    Hierarchy = struct_w4d.Hierarchy()
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
        else:
            file.seek(Chunksize, 1)
    file.close()
    return Hierarchy
	
#######################################################################################
# createArmature
#######################################################################################
	
def createArmature(self, Hierarchy, hasMeshes):
    amt = bpy.data.armatures.new(Hierarchy.header.name)
    amt.show_names = True
    rig = bpy.data.objects.new(Hierarchy.header.name, amt)
    rig.location = Hierarchy.header.centerPos
    rig.rotation_mode = 'QUATERNION'
    rig.show_x_ray = True
    rig.track_axis = "POS_X"
    bpy.context.scene.objects.link(rig) # Link the object to the active scene
    bpy.context.scene.objects.active = rig
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.context.scene.update()

	#create the bones from the pivots
    for pivot in Hierarchy.pivots:
        #test for non_bone_pivots
        if pivot.isBone or not hasMeshes:
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
    custom_shape = bpy.ops.mesh.primitive_uv_sphere_add(segments = 12, size = 1.8, location = (0, 0, 0), view_align = True)

    for pivot in Hierarchy.pivots:
        #test for non_bone_pivots
        if pivot.isBone or not hasMeshes:
            bone = rig.pose.bones[pivot.name]
            bone.location = pivot.position
            bone.rotation_mode = 'QUATERNION'
            bone.rotation_quaternion = pivot.rotation
            #bpy.data.objects["Bone"].scale = (4, 4, 4)
            bone.custom_shape = bpy.data.objects["Sphere"]

    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.data.objects['Sphere'].select = True
    bpy.ops.object.delete()
    return rig
	
#######################################################################################
# createAnimation
#######################################################################################

#def createAnimation(self, Animation, Hierarchy, rig, compressed):


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
    Model = None
    Meshes = []
    Hierarchy = None
    Animation = None
    Box = None
    amtName = ""
    rig = None

    while file.tell() < filesize:
        Chunktype = ReadLong(file)
        Chunksize =  GetChunkSize(ReadLong(file))
        chunkEnd = file.tell() + Chunksize
        if Chunktype == 0:
            Model = ReadModel(file)
			
        elif Chunktype == 1:
            Meshes.append(ReadMesh(self, file, chunkEnd))
			
        elif Chunktype == 256:
            Hierarchy = ReadHierarchy(file, self, chunkEnd)

        elif Chunktype == 512:
            Animation = ReadAnimation(file, self, chunkEnd)

        elif Chunktype == 1024:
            Box = ReadBox(file)

        else:
            self.report({'ERROR'}, "unknown chunktype in File: %s" % Chunktype)
            print("!!!unknown chunktype in File: %s" % Chunktype)
            file.seek(Chunksize,1)

    file.close()
	
    # set the lamp to sun mode to make bump maps visible
    try: 
        bpy.data.objects["Lamp"].location = (5.0, 5.0, 5.0)
        bpy.data.lamps["Lamp"].type = "SUN"
    except:
        lamp_data = bpy.data.lamps.new(name="Lamp", type='SUN')
        lamp_object = bpy.data.objects.new(name="Lamp", object_data=lamp_data)
        bpy.context.scene.objects.link(lamp_object)
        lamp_object.location = (5.0, 5.0, 5.0)

    if not Box == None:
        createBox(Box)
	
	#load skeleton file if needed 
    sklpath = ""
    if Model != None and Model.name != Model.hieraName:
        sklpath = os.path.dirname(givenfilepath) + "\\" + Model.hieraName.lower() + ".w4d"
        try:
            Hierarchy = LoadSKL(self, sklpath)
        except:
            self.report({'ERROR'}, "skeleton file not found: " + Model.hieraName) 
            print("!!! skeleton file not found: " + Model.hieraName)
			
    #if (not Animation.header.name == "") and (Hierarchy.header.name == ""):
    #    sklpath = os.path.dirname(givenfilepath) + "\\" + Animation.header.hieraName.lower() + ".w3d"
    #    try:
    #        Hierarchy = LoadSKL(self, sklpath)
    #    except:
    #        self.report({'ERROR'}, "skeleton file not found: " + Animation.header.hieraName) 
    #        print("!!! skeleton file not found: " + Animation.header.hieraName)

    #create skeleton if needed
    if not Hierarchy == None:
        amtName = Hierarchy.header.name
        found = False
        for obj in bpy.data.objects:
            if obj.name == amtName:
                rig = obj
                found = True
        if not found:
		    # if we only have a skeleton, we will create bones from all pivots so we dont lose data
            hasMeshes = False
            if len(Meshes) > 0:
                hasMeshes = True
            rig = createArmature(self, Hierarchy, hasMeshes)
        if len(Meshes) > 0:
            #if a mesh is loaded set the armature invisible
            rig.hide = True

    for m in Meshes:	
        Vertices = m.verts
        Faces = []

        for f in m.faces:
            Faces.append(f)

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
        if len(m.uvCoords) > 0:
            for f in bm.faces:
                f.loops[0][uv_layer].uv = m.uvCoords[Faces[index][0]]
                f.loops[1][uv_layer].uv = m.uvCoords[Faces[index][1]]
                f.loops[2][uv_layer].uv = m.uvCoords[Faces[index][2]]
                index+=1
				
        bm.to_mesh(mesh)

        mesh_ob = bpy.data.objects.new(m.header.meshName, mesh)

		#show the bounding boxes
        #mesh_ob.show_bounds = True
        #mesh_ob.draw_bounds_type = "BOX"
		
        #create the material for each mesh because the same material could be used with multiple textures
        for mat in m.materials:
            material = bpy.data.materials.new(m.header.meshName)
            material.use_shadeless = True
            if mat.alpha < 1.0:
                material.use_transparency = True
                material.transparency_method = "Z_TRANSPARENCY"
            material.alpha = mat.alpha
            material.specular_color = (mat.specular.r, mat.specular.g, mat.specular.b)
            material.diffuse_color = (mat.diffuse.r, mat.diffuse.g, mat.diffuse.b)
            material.specular_intensity = mat.specular_intensity
            material.diffuse_intensity = mat.diffuse_intensity
            mesh.materials.append(material)
			
            for tex in mat.textures:
                LoadTexture(self, givenfilepath, mesh, material, tex)
		
    for m in Meshes: #need an extra loop because the order of the meshes is random
        mesh_ob = bpy.data.objects[m.header.meshName]
        #hierarchy stuff
        if not Hierarchy == None:
            # mesh header attributes
            # 0   -> normal mesh
	        # 1   -> normal mesh - two sided
            # 2   -> normal mesh - camera oriented
            # 128 -> skin
            # 129 -> skin - two sided
            type = m.header.type
            if type == 1 or type == 129:
                mesh.show_double_sided = True
				
            if type == 0 or type == 1 or type == 2:
                for pivot in Hierarchy.pivots:
                    if pivot.name == m.header.meshName:
                        mesh_ob.rotation_mode = 'QUATERNION'
                        mesh_ob.location =  pivot.position
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

            elif type == 128 or type == 129:
                for pivot in Hierarchy.pivots:
                    mesh_ob.vertex_groups.new(pivot.name)
						
                for i in range(len(m.vertInfs)):
                    weight = m.vertInfs[i].boneInf
                    if weight == 0.0:
                        weight = 1.0
                    mesh_ob.vertex_groups[m.vertInfs[i].boneIdx].add([i], weight, 'REPLACE')

                mod = mesh_ob.modifiers.new(amtName, 'ARMATURE')
                mod.object = rig
                mod.use_bone_envelopes = False
                mod.use_vertex_groups = True
				
				#to keep the transformations while mesh is in edit mode!!!
                mod.show_in_editmode = True
                mod.show_on_cage = True
            else:
                print("unsupported meshtype: %i" %type)
                self.report({'ERROR'}, "unsupported meshtype: %i" %type)
        bpy.context.scene.objects.link(mesh_ob) # Link the object to the active scene

    #animation stuff
    if not Animation == None:	
        createAnimation(self, Animation, Hierarchy, rig)
	
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