#Written by Michael Schnabel
#Last Modification 21.10.2015
#Exports the W4D Format 
import bpy
import operator
import struct
import os
import math
import sys
import bmesh
from bpy.props import *
from mathutils import Vector, Quaternion
from . import struct_w4d, import_w4d

#TODO 


HEAD = 8 #4(long = chunktype) + 4 (long = chunksize)

#######################################################################################
# Basic Methods
#######################################################################################

def getStringSize(string):
    return len(string) + 1 #binary 0

def WriteString(file, string):
    file.write(bytes(string, 'UTF-8'))
	#write binary 0 to file
    file.write(struct.pack('B', 0))
		
def WriteRGBA(file, rgba):
    file.write(struct.pack("B", rgba.r))
    file.write(struct.pack("B", rgba.g))
    file.write(struct.pack("B", rgba.b))
    file.write(struct.pack("B", rgba.a))
	
# only if the chunk has subchunks -> else: WriteLong(file, data)
def MakeChunkSize(data):
    return (data | 0x80000000)

def WriteLong(file, num):
    file.write(struct.pack("<L", num))

def WriteSignedLong(file, num):
    file.write(struct.pack("<l", num))	
	
def WriteShort(file, num):
    file.write(struct.pack("<H", num))

def WriteSignedShort(file, num):
    file.write(struct.pack("<h", num))
	
def WriteLongArray(file, array):
    for a in array:
        WriteLong(file, a)

def WriteFloat(file, num):
    file.write(struct.pack("<f", num))
	
def WriteSignedByte(file, num):
    file.write(struct.pack("<b", num))

def WriteUnsignedByte(file, num):
    file.write(struct.pack("<B", num))
	
def WriteVector(file, vec):
    WriteFloat(file, vec[0])
    WriteFloat(file, vec[1])
    WriteFloat(file, vec[2])
	
def WriteQuaternion(file, quat):
    #changes the order from wxyz to xyzw
    WriteFloat(file, quat[1])
    WriteFloat(file, quat[2])
    WriteFloat(file, quat[3])
    WriteFloat(file, quat[0])
	
#######################################################################################
# Triangulate
#######################################################################################	

def triangulate(mesh):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces = bm.faces)
    bm.to_mesh(mesh)
    bm.free()
	
#######################################################################################
# Hierarchy
#######################################################################################

def getHeaderChunkSize(header):
    return 16 + getStringSize(header.name)

def WriteHierarchyHeader(file, header):
    WriteLong(file, 257) #chunktype
    WriteLong(file, getHeaderChunkSize(header)) #chunksize
	
    WriteString(file, header.name)
    WriteLong(file, header.pivotCount)
    WriteVector(file, header.centerPos)
	
def getPivotsChunkSize(pivots):
    size = 0
    for pivot in pivots:
        size += 31 + getStringSize(pivot.name)
    return size

def WritePivots(file, pivots):
    WriteLong(file, 258) #chunktype
    WriteLong(file, getPivotsChunkSize(pivots)) #chunksize
	
    for pivot in pivots:
        WriteString(file, pivot.name)
        WriteSignedShort(file, pivot.parentID)
        WriteUnsignedByte(file, pivot.isBone)
        WriteVector(file, pivot.position)
        WriteQuaternion(file, pivot.rotation)

def WriteHierarchy(file, hierarchy):
    print("\n### NEW HIERARCHY: ###")
    WriteLong(file, 256) #chunktype
    
    size = HEAD + getHeaderChunkSize(hierarchy.header) + HEAD + getPivotsChunkSize(hierarchy.pivots) 

    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteHierarchyHeader(file, hierarchy.header)
    print("Header")
    WritePivots(file, hierarchy.pivots)
    print("Pivots")

#######################################################################################
# Animation
#######################################################################################
	
def WriteAnimationHeader(file, size, header):
    WriteLong(file, 513) #chunktype
    WriteLong(file, size) #chunksize

    WriteString(file, header.name)
    WriteString(file, header.hieraName)
    WriteLong(file, header.numFrames)
    WriteLong(file, header.frameRate)

def WriteTimeCodedAnimationChannel(file, channel):
    WriteLong(file, 514) #chunktype
    size = 6 + (len(channel.timeCodedKeys) * channel.vectorLen) * 4
    WriteLong(file, size) #chunksize
	
    WriteShort(file, channel.vectorLen)
    WriteShort(file, channel.type)
    WriteShort(file, channel.pivot)

    if channel.vectorLen == 1:
        for f in channel.timeCodedKeys:
            WriteFloat(file, f)
    elif channel.vectorLen == 4:
        for quat in channel.timeCodedKeys:
            WriteQuaternion(file, quat)

def WriteAnimation(file, animation):
    print("\n### NEW ANIMATION: ###")
    WriteLong(file, 512) #chunktype
	
    headerSize = len(header.name) + len(header.hieraName) + 8
    channelsSize = 0
    for channel in animation.channels:
        channelsSize += HEAD + 6 + (len(channel.timeCodedKeys) * channel.vectorLen) * 4
    size = HEAD + headerSize + channelsSize		
	
    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteAnimationHeader(file, headerSize, animation.header)
    print("Header")
    for channel in animation.channels:
        WriteAnimationChannel(file, channel)
        print("Channel")
	
#######################################################################################
# Model
#######################################################################################

def getModelChunkSize(model):
    return getStringSize(model.name) + getStringSize(model.hieraName)

def WriteModel(file, model):
    print("\n### NEW MODEL: ###")
    WriteLong(file, 0) #chunktype
    WriteLong(file, getModelChunkSize(model)) #chunksize	

    print(model.name)
    WriteString(file, model.name)
    print(model.hieraName)
    WriteString(file, model.hieraName)
			
#######################################################################################
# Box
#######################################################################################	

def WriteBox(file, box):
    print("\n### NEW BOX: ###")
    WriteLong(file, 1024) #chunktype
    WriteLong(file, 24) #chunksize
	
    WriteVector(file, box.center)
    WriteVector(file, box.extend)
	
#######################################################################################
# Vertices
#######################################################################################

def getMeshVerticesChunkSize(vertices):
    size = len(vertices) * 12
    return size

def WriteMeshVerticesArray(file, vertices):
    WriteLong(file, 3) #chunktype
    WriteLong(file, getMeshVerticesChunkSize(vertices)) #chunksize
	
    for vert in vertices:
        WriteVector(file, vert)

#######################################################################################
# Normals
#######################################################################################

def getMeshNormalsArrayChunkSize(normals):
    size = len(normals) * 12
    return size
	
def WriteMeshNormalsArray(file, normals):
    WriteLong(file, 4) #chunktype
    WriteLong(file, getMeshNormalsArrayChunkSize(normals)) #chunksize
	
    for norm in normals:
        WriteVector(file, norm)
	
#######################################################################################
# Faces
#######################################################################################	

def getMeshFaceArrayChunkSize(faces):
    size = len(faces) * 12
    return size

def WriteMeshFaceArray(file, faces):
    WriteLong(file, 5) #chunktype
    WriteLong(file, getMeshFaceArrayChunkSize(faces)) #chunksize
	
    for face in faces:
        WriteLong(file, face[0])
        WriteLong(file, face[1])
        WriteLong(file, face[2])
		
#######################################################################################
# uvCoords
#######################################################################################	

def getMeshUVCoordsChunkSize(uvCoords):
    return len(uvCoords) * 8

def WriteMeshUVCoords(file, uvCoords):
    WriteLong(file, 6) #chunktype
    WriteLong(file, MakeChunkSize(getMeshUVCoordsChunkSize(uvCoords))) #chunksize
	
    for uv in uvCoords:
        WriteFloat(file, uv[0])
        WriteFloat(file, uv[1])
		
#######################################################################################
# VertexInfluences
#######################################################################################	
		
def getMeshVertexInfluencesChunkSize(influences):
    size = len(influences) * 4
    return size

def WriteMeshVertexInfluences(file, influences):
    WriteLong(file, 7) #chunktype
    WriteLong(file, getMeshVertexInfluencesChunkSize(influences)) #chunksize

    for inf in influences:
        WriteShort(file, inf.boneIdx)
        WriteShort(file, int(inf.boneInf * 100))
		
#######################################################################################
# Texture
#######################################################################################	

def getTextureChunkSize(texture):
    size = getStringSize(texture.name) + 1
    return size
	
def WriteTexture(file, texture):
    WriteLong(file, 31) #chunktype
    WriteLong(file,  MakeChunkSize(getTextureChunkSize(texture))) #chunksize
	
    WriteString(file, texture.name)
    WriteUnsignedByte(file, texture.type)
    WriteFloat(file, texture.value)
	
    #write animation chunks
		
#######################################################################################
# Material
#######################################################################################	

def getMaterialChunkSize(material):
    size = 28
    for texture in material.textures:
        size += HEAD + getTextureChunkSize(texture)
    return size

def WriteMeshMaterial(file, material):
    WriteLong(file, 30) #chunktype
    WriteLong(file, MakeChunkSize(getMaterialChunkSize(material))) #chunksize
	
    WriteRGBA(file, material.diffuse)
    WriteFloat(file, material.diffuse_intensity)
    WriteRGBA(file, material.specular)
    WriteFloat(file, material.specular_intensity)
    WriteFloat(file, material.emit)
    WriteFloat(file, material.alpha)
 
    for texture in material.textures:
        WriteTexture(file, texture)
		
#######################################################################################
# Mesh
#######################################################################################	

def getMeshHeaderChunkSize(header):
    size = 51 + getStringSize(header.meshName)
    return size

def WriteMeshHeader(file, header): 
    WriteLong(file, 2) #chunktype
    WriteLong(file, getMeshHeaderChunkSize(header)) #chunksize

    WriteUnsignedByte(file, header.type)
    WriteString(file, header.meshName)
    WriteShort(file, header.parentPivot)
    WriteLong(file, header.faceCount)
    WriteLong(file, header.vertCount)
    WriteVector(file, header.minCorner)
    WriteVector(file, header.maxCorner)
    WriteVector(file, header.sphCenter)
    WriteFloat(file, header.sphRadius)
	
def WriteMesh(file, mesh):
    print("\n### NEW MESH: ###")
    WriteLong(file, 1) #chunktype
	
    size = HEAD + getMeshHeaderChunkSize(mesh.header)
    size += HEAD + getMeshVerticesChunkSize(mesh.verts)
    size += HEAD + getMeshNormalsArrayChunkSize(mesh.normals)
    size += HEAD + getMeshFaceArrayChunkSize(mesh.faces)
    size += HEAD + getMeshUVCoordsChunkSize(mesh.uvCoords)
    if len(mesh.vertInfs) > 0:
        size += HEAD + getMeshVertexInfluencesChunkSize(mesh.vertInfs)
    for mat in mesh.materials:
        size += HEAD + getMaterialChunkSize(mat)

    WriteLong(file, MakeChunkSize(size)) #chunksize
	
    WriteMeshHeader(file, mesh.header)
    print(mesh.header.meshName)
    #print("Header")
    WriteMeshVerticesArray(file, mesh.verts)
    #print("Vertices")
    WriteMeshNormalsArray(file, mesh.normals)
    #print("Normals")
    WriteMeshFaceArray(file, mesh.faces)
    #print("Faces")
    WriteMeshUVCoords(file, mesh.uvCoords)
    #print("uvCoords")
    if len(mesh.vertInfs) > 0:
        WriteMeshVertexInfluences(file, mesh.vertInfs) 
        #print("Vertex Influences")
    for mat in mesh.materials:
        WriteMeshMaterial(file, mat)
        #print("Material")
		
#######################################################################################
# Mesh Sphere
#######################################################################################	

def calculateMeshSphere(mesh, Header):
    # get the point with the biggest distance to x and store it in y
    x = mesh.vertices[0]
    y = mesh.vertices[1]
    dist = ((y.co[0] - x.co[0])**2 + (y.co[1] - x.co[1])**2 + (y.co[2] - x.co[2])**2)**(1/2)
    for v in mesh.vertices:
        curr_dist = ((v.co[0] - x.co[0])**2 + (v.co[1] - x.co[1])**2 + (v.co[2] - x.co[2])**2)**(1/2)
        if (curr_dist > dist):
            dist = curr_dist
            y = v
					
    #get the point with the biggest distance to y and store it in z
    z = mesh.vertices[2]
    dist = ((z.co[0] - y.co[0])**2 + (z.co[1] - y.co[1])**2 + (z.co[2] - y.co[2])**2)**(1/2)
    for v in mesh.vertices:
        curr_dist = ((v.co[0] - y.co[0])**2 + (v.co[1] - y.co[1])**2 + (v.co[2] - y.co[2])**2)**(1/2)
        if (curr_dist > dist):
            dist = curr_dist
            z = v   
             
    # the center of the sphere is between y and z
    vec_y = Vector(y.co.xyz)
    vec_z = Vector(z.co.xyz)
    y_z = ((vec_z - vec_y)/2)
    m = Vector(vec_y + y_z)
    radius = y_z.length

    #test if any of the vertices is outside the sphere (if so update the sphere)
    for v in mesh.vertices:
        curr_dist = ((v.co[0] - m[0])**2 + (v.co[1] - m[1])**2 + (v.co[2] - m[2])**2)**(1/2)
        if curr_dist > radius:
            delta = (curr_dist - radius)/2
            radius += delta
            m += (Vector(v.co.xyz - m)).normalized() * delta  	 	
    Header.sphCenter = m
    Header.sphRadius = radius

#######################################################################################
# Main Export
#######################################################################################	

def MainExport(givenfilepath, self, context, EXPORT_MODE = 'M'):
    #print("Run Export")
    Hierarchy = struct_w4d.Hierarchy()
    amtName = ""
    modelName = ""
	
    roottransform = struct_w4d.HierarchyPivot()
    roottransform.name = "ROOTTRANSFORM"
    roottransform.parentID = -1
    Hierarchy.pivots.append(roottransform)
    
	#switch to object mode
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')
	
    # Get all the armatures in the scene.
    rigList = [object for object in bpy.context.scene.objects if object.type == 'ARMATURE']

    if len(rigList) == 1:
        rig = rigList[0]
        amtName = rig.name
        for bone in rig.pose.bones:
            pivot = struct_w4d.HierarchyPivot()
            pivot.name = bone.name
            if not bone.parent == None:
                ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == bone.parent.name] #return an array of indices (in this case only one value)
                pivot.parentID = ids[0]
            else:
                pivot.parentID = 0
            pivot.position = bone.location
            pivot.rotation = bone.rotation_quaternion
            Hierarchy.pivots.append(pivot)
    else:
        context.report({'ERROR'}, "only one armature allowed!")
        print("Error: only one armature allowed!") 
	
    objList = []
    # Get all the mesh objects in the scene.
    objList = [object for object in bpy.context.scene.objects if object.type == 'MESH']
	
    if EXPORT_MODE == 'M' or EXPORT_MODE == 'S' or EXPORT_MODE == 'HAM':
        modelName = (os.path.splitext(os.path.basename(givenfilepath))[0]).upper()
        print(modelName)
        if not EXPORT_MODE == 'S':
            sknFile = open(givenfilepath, "wb")
		
            Model = struct_w4d.Model()
            Model.name = modelName
            Model.hieraName = amtName
            WriteModel(sknFile, Model)
		
        for mesh_ob in objList: 
            if mesh_ob.name == "BOUNDINGBOX":
                Box = struct_w4d.Box()
                Box.center = mesh_ob.location
                box_mesh = mesh_ob.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface = True)
                Box.extend = Vector((box_mesh.vertices[0].co.x * 2, box_mesh.vertices[0].co.y * 2, box_mesh.vertices[0].co.z))
			
                if not EXPORT_MODE == 'S':
                    WriteBox(sknFile, Box)
            else:
                Mesh = struct_w4d.Mesh()
                Header = struct_w4d.MeshHeader()			
		
                verts = []
                normals = [] 
                faces = []
                uvs = []
                vertInfs = []

                Header.meshName = mesh_ob.name
                mesh = mesh_ob.to_mesh(bpy.context.scene, False, 'PREVIEW', calc_tessface = True)
		
                triangulate(mesh)
		
                Header.vertCount = len(mesh.vertices)
                Mesh.vertInfs = []
                group_lookup = {g.index: g.name for g in mesh_ob.vertex_groups}
                groups = {name: [] for name in group_lookup.values()}
                for v in mesh.vertices:
                    verts.append(v.co.xyz)
                    normals.append(v.normal)
                    uvs.append((0.0, 0.0)) #just to fill the array 
				
				    #vertex influences
                    vertInf = struct_w4d.MeshVertexInfluences()
                    if len(v.groups) > 0:
				        #has to be this complicated, otherwise the vertex groups would be corrupted
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.vertex_groups[v.groups[0].group].name] #return an array of indices (in this case only one value)
                        if len(ids) > 0:
                            vertInf.boneIdx = ids[0]
                        vertInf.boneInf = v.groups[0].weight
                        Mesh.vertInfs.append(vertInf)
                    elif len(v.groups) > 1:
                        #has to be this complicated, otherwise the vertex groups would be corrupted
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.vertex_groups[v.groups[0].group].name] #return an array of indices (in this case only one value)
                        if len(ids) > 0:
                            vertInf.boneIdx = ids[0]
                        vertInf.boneInf = v.groups[0].weight
                        #has to be this complicated, otherwise the vertex groups would be corrupted
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.vertex_groups[v.groups[1].group].name] #return an array of indices (in this case only one value)
                        if len(ids) > 0:
                            vertInf.boneIdx = ids[0]
                        vertInf.xtraInf = v.groups[1].weight
                        Mesh.vertInfs.append(vertInf)
                    elif len(v.groups) > 2: 
                        context.report({'ERROR'}, "max 2 bone influences per vertex supported!")
                        print("Error: max 2 bone influences per vertex supported!")
	
                calculateMeshSphere(mesh, Header)
			
                Mesh.verts = verts
                Mesh.normals = normals
                Header.minCorner = Vector((mesh_ob.bound_box[0][0], mesh_ob.bound_box[0][1], mesh_ob.bound_box[0][2]))
                Header.maxCorner =  Vector((mesh_ob.bound_box[6][0], mesh_ob.bound_box[6][1], mesh_ob.bound_box[6][2]))

                for face in mesh.polygons:
                    faces.append((face.vertices[0], face.vertices[1], face.vertices[2]))
                Mesh.faces = faces
			
                Header.faceCount = len(faces)
			
		        #uv coords
                bm = bmesh.new()
                bm.from_mesh(mesh)

                uv_layer = bm.loops.layers.uv.verify()
                #bm.faces.layers.tex.verify()
			
                index = 0
                for f in bm.faces:
                    uvs[Mesh.faces[index][0]] = f.loops[0][uv_layer].uv
                    uvs[Mesh.faces[index][1]] = f.loops[1][uv_layer].uv
                    uvs[Mesh.faces[index][2]] = f.loops[2][uv_layer].uv
                    index+=1   
				
                Mesh.uvCoords = uvs
                Mesh.materials = [] 
                meshMaterial = struct_w4d.MeshMaterial()
			
                for mat in mesh.materials:
                    matName = (os.path.splitext(os.path.basename(mat.name))[1])[1:]
                    material = struct_w4d.MeshMaterial()
                    material.textures = []
                    for tex in mat.texture_slots:
                        if not (tex == None):
                            texture = struct_w4d.Texture()
                            texture.name = tex.name
                            material.textures.append(texture)
                    Mesh.materials.append(material)
			
                if len(mesh_ob.vertex_groups) > 0:					
                    Header.type = 128 #type skin
                else:
                    Header.type = 0 #type normal mesh
                    pivot = struct_w4d.HierarchyPivot()
                    pivot.name = mesh_ob.name
                    pivot.parentID = 0
                    if not mesh_ob.parent_bone == "":
                        ids = [index for index, pivot in enumerate(Hierarchy.pivots) if pivot.name == mesh_ob.parent_bone] #return an array of indices (in this case only one value)
                        pivot.parentID = ids[0]
                    pivot.isBone = 0
                    pivot.position = mesh_ob.location
                    pivot.rotation = mesh_ob.rotation_quaternion
                    Header.parentPivot = len(Hierarchy.pivots)
                    Hierarchy.pivots.append(pivot)	

                Mesh.header = Header	
                if not EXPORT_MODE == 'S':				
                    WriteMesh(sknFile, Mesh)

    Hierarchy.header.pivotCount = len(Hierarchy.pivots)
		
    sklPath = givenfilepath.replace(".w4d", "_skl.w4d")
    sklName = (os.path.splitext(os.path.basename(sklPath))[0])
	
    print(EXPORT_MODE)
    if EXPORT_MODE == 'S':
        sklFile = open(sklPath.replace(sklName, amtName.lower()), "wb")
        Hierarchy.header.name = amtName
        WriteHierarchy(sklFile, Hierarchy)
        sklFile.close()
				
    #write the hierarchy to the skn file (has no armature data)
    elif EXPORT_MODE == 'HAM':
        Hierarchy.header.name = modelName	  
        WriteHierarchy(sknFile, Hierarchy)
    try:
        sknFile.close()  
    except:
        print("")