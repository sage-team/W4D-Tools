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
	
#chunk 259 (references a hierarchy file)
class HierarchyFile(Struct):
    name = ""

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
# Model
#######################################################################################

#chunk 0
class Model(Struct):
    name = ""
    hieraName = name # is the name of the model by default
	
#######################################################################################
# Box
#######################################################################################	

#chunk 1024
class Box(Struct): 
    center = Vector((0.0, 0.0 ,0.0))
    extend = Vector((0.0, 0.0 ,0.0))
	
#######################################################################################
# VertexInfluences
#######################################################################################

#chunk 7
class MeshVertexInfluences(Struct):
    boneIdx = 0
    boneInf = 0.0
	
#######################################################################################
#  Texture Animation
#######################################################################################		

#chunk 32
#class TextureAnimation(Struct):
    #not sure what values we need here
	
#######################################################################################
# Texture
#######################################################################################	
	
#chunk 31
class Texture(Struct):
    name = ""
    type = 0 #0 standard, 1 normal, 2 displacement
    value = 0.0 # factor for normal, displacement etc
    animations = []
	
#######################################################################################
# Material
#######################################################################################	

#chunk 30
class MeshMaterial(Struct):
    diffuse = RGBA()
    diffuse_intensity = 0.0
    specular = RGBA()
    specular_intensity = 0.0
    emit = 0.0
    alpha = 1.0
    textures = []
	
#######################################################################################
# Mesh
#######################################################################################	

#chunk 2
class MeshHeader(Struct):
    type = 0
    # 0   -> normal mesh
	# 1   -> normal mesh - two sided
    # 2   -> normal mesh - camera oriented
    # 128 -> skin
	# 129 -> skin - two sided
   
    meshName = ""
    parentPivot = 0
    faceCount = 0
    vertCount = 0
    minCorner = Vector((0.0, 0.0 ,0.0))
    maxCorner = Vector((0.0, 0.0 ,0.0))
    sphCenter = Vector((0.0, 0.0 ,0.0))
    sphRadius = 0.0

#chunk 1
class Mesh(Struct):
    header = MeshHeader()
    verts = []
    normals = []
    faces = []
    uvCoords = []	
    vertInfs = []
    materials = []