#Written by Michael Schnabel
#Last Modification 19.10.2015
#Structs of the W4D Format 
from mathutils import Vector, Quaternion

class Struct:
    def __init__ (self, *argv, **argd):
        if len(argd):
            # Update by dictionary
            self.__dict__.update (argd)
        else:
            # Update by position
            attrs = filter (lambda x: x[0:2] != "__", dir(self))
            for n in range(len(argv)):
                setattr(self, attrs[n], argv[n])
			
#######################################################################################
# Basic Structs
#######################################################################################
			
class RGBA(Struct):
    r = 0
    g = 0
    b = 0
    a = 0
	
#######################################################################################
# Hierarchy
#######################################################################################

#chunk 257
class HierarchyHeader(Struct):
    name = ""
    pivotCount = 0
    centerPos = Vector((0.0, 0.0 ,0.0))

#chunk 258
class HierarchyPivot(Struct):
    name = ""
    parentID = -1
    isBone = 1 #default 1
    position = Vector((0.0, 0.0 ,0.0))
    rotation = Quaternion((1.0, 0.0, 0.0, 0.0))

# chunk 256
class Hierarchy(Struct):
    header = HierarchyHeader()
    pivots = []
	
#######################################################################################
# Animation
#######################################################################################

#chunk 513
class AnimationHeader(Struct):
    name = ""
    hieraName = ""
    numFrames = 0
    frameRate = 0
	
class TimeCodedAnimationKey(Struct):
    frame = 0
    value = 0
	
#chunk 514
class TimeCodedAnimationChannel(Struct):
    vectorLen = 0
    type = 0
    pivot = 0 
    timeCodedKeys = []
	
#chunk 512
class Animation(Struct):
    header = AnimationHeader()
    channels = [] 
	
#######################################################################################
# Box
#######################################################################################	

#chunk 1024
class Box(Struct): 
    center = Vector((0.0, 0.0 ,0.0))
    extend = Vector((0.0, 0.0 ,0.0))
	
#######################################################################################
# Texture
#######################################################################################	
	
class MaterialTexture(Struct):
    name = ""
    attribute = 0 #0 standard, 1 normal
    txCoords = []	
	
#######################################################################################
# Material
#######################################################################################	

#chunk 6
class MeshMaterial(Struct):
    diffuse = RGBA()
    diffuseIntensity = 0.0
    specular = RGBA()
    specularIntensity = 0.0
    emit = 0.0
    ambient = 0.0          
    translucency = 0.0  
    textures = []

#######################################################################################
# Vertices
#######################################################################################

#chunk 4
class MeshVertexInfluences(Struct):
    boneIdx = 0
    bone2Idx = 0
    boneInf = 0.0
    bone2Inf = 0.0
	
#######################################################################################
# Faces
#######################################################################################	

#chunk 5
class MeshFace(Struct):
    vertIds = []
	
#######################################################################################
# Mesh
#######################################################################################	

#chunk 1
class MeshHeader(Struct):
    attrs = 0
    # 0   -> normal mesh
	# 1   -> normal mesh - two sided
    # 2   -> normal mesh - camera oriented
    # 512 -> skin
	# 513 -> skin - two sided
   
    meshName = ""
    parentPivot = 0
    faceCount = 0
    vertCount = 0
    minCorner = Vector((0.0, 0.0 ,0.0))
    maxCorner = Vector((0.0, 0.0 ,0.0))
    sphCenter = Vector((0.0, 0.0 ,0.0))
    sphRadius = 0.0

#chunk 0
class Mesh(Struct):
    header = MeshHeader()
    verts = []
    normals = []
    vertInfs = []
    faces = []
    materials = []