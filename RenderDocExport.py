# RenderDoc Python console, powered by python 3.6.4.
# The 'pyrenderdoc' object is the current CaptureContext instance.
# The 'renderdoc' and 'qrenderdoc' modules are available.
# Documentation is available: https://renderdoc.org/docs/python_api/index.html

import sys
import csv

# Configuration
folderName = "D:/capMesh1"
startIndex = 1200
endIndex = 2000

isPrint = False

# Import renderdoc if not already imported (e.g. in the UI)
if 'renderdoc' not in sys.modules and '_renderdoc' not in sys.modules:
	import renderdoc

# Alias renderdoc for legibility
rd = renderdoc

# We'll need the struct data to read out of bytes objects
import struct
import os

# We base our data on a MeshFormat, but we add some properties
class MeshData(rd.MeshFormat):
	indexOffset = 0
	name = ''

def pySaveTexture(resourceId, eventId, controller, textureType="texture"):
	"""
	Save texture to disk. All textures are saved in a single folder.
	Args:
		resourceId: The resource ID of the texture
		eventId: The event ID for naming
		controller: The replay controller
		textureType: Type identifier for filename (e.g., "texture", "output")
	"""
	texsave = rd.TextureSave()
	texsave.resourceId = resourceId
	if texsave.resourceId == rd.ResourceId.Null():
		return False

	# Create main texture folder if it doesn't exist
	textureFolder = "{0}/textures".format(folderName)
	if not os.path.exists(textureFolder):
		os.makedirs(textureFolder)

	# Generate unique filename with eventId and resourceId
	filename = "{0}_event{1}_{2}".format(textureType, eventId, str(int(texsave.resourceId)))
	
	# Set texture save parameters
	texsave.mip = 0
	texsave.slice.sliceIndex = 0
	texsave.alpha = rd.AlphaMapping.Preserve
	texsave.destType = rd.FileType.PNG

	# Save texture to the main texture folder
	outTexPath = "{0}/{1}.png".format(textureFolder, filename)
	controller.SaveTexture(texsave, outTexPath)
	print("Saved texture: {0}".format(outTexPath))
	return True

def findIndexDrawLoop(d, index):
	"""Recursively search for a draw call with specific index"""
	ret = None
	if d.eventId == index:
		return d
	
	for c in d.children:
		ret = findIndexDrawLoop(c, index)
		if ret:
			return ret
	
	return ret

def findIndexDraw(index, controller):
	"""Find draw call by index"""
	ret = None
	for d in controller.GetDrawcalls():
		if d.eventId == index:
			ret = d
			return ret

		for c in d.children:
			ret = findIndexDrawLoop(c, index)
			if ret:
				return ret	
	return ret

def unpackData(fmt, data):
	"""
	Unpack vertex data according to format specification
	Args:
		fmt: Format specification
		data: Raw byte data
	Returns:
		Unpacked tuple of values
	"""
	if isPrint:
		print("Unpacking data...")
	
	# Format character mapping for different component types and byte widths
	formatChars = {}
	#                                 012345678
	formatChars[rd.CompType.UInt]  = "xBHxIxxxL"
	formatChars[rd.CompType.SInt]  = "xbhxixxxl"
	formatChars[rd.CompType.Float] = "xxexfxxxd" # only 2, 4 and 8 are valid

	# These types have identical decodes, but we might post-process them
	formatChars[rd.CompType.UNorm] = formatChars[rd.CompType.UInt]
	formatChars[rd.CompType.UScaled] = formatChars[rd.CompType.UInt]
	formatChars[rd.CompType.SNorm] = formatChars[rd.CompType.SInt]
	formatChars[rd.CompType.SScaled] = formatChars[rd.CompType.SInt]

	# We need to fetch compCount components
	vertexFormat = str(fmt.compCount) + formatChars[fmt.compType][fmt.compByteWidth]

	# Unpack the data
	value = struct.unpack_from(vertexFormat, data, 0)

	# If the format needs post-processing such as normalisation, do that now
	if fmt.compType == rd.CompType.UNorm:
		divisor = float((2 ** (fmt.compByteWidth * 8)) - 1)
		value = tuple(float(i) / divisor for i in value)
	elif fmt.compType == rd.CompType.SNorm:
		maxNeg = -float(2 ** (fmt.compByteWidth * 8)) / 2
		divisor = float(-(maxNeg-1))
		value = tuple((float(i) if (i == maxNeg) else (float(i) / divisor)) for i in value)

	# If the format is BGRA, swap the two components
	if fmt.BGRAOrder():
		value = tuple(value[i] for i in [2, 1, 0, 3])

	return value

def getMeshInputs(controller, draw):
	"""
	Get mesh input data and save associated textures
	Args:
		controller: Replay controller
		draw: Draw call information
	Returns:
		List of MeshData objects describing vertex inputs
	"""
	state = controller.GetPipelineState()

	# Get the index & vertex buffers, and fixed vertex inputs
	ib = state.GetIBuffer()
	vbs = state.GetVBuffers()
	attrs = state.GetVertexInputs()
	
	# Extract textures used by fragment shader - all textures saved to single folder
	usedDescriptors = state.GetReadOnlyResources(renderdoc.ShaderStage.Fragment)
	for usedDescriptor in usedDescriptors:
		res = usedDescriptor.descriptor.resource
		if res != rd.ResourceId.Null():
			print("Found texture resource: {0}".format(res))
			if not pySaveTexture(res, draw.eventId, controller, "input"):
				break
	
	meshInputs = []

	for attr in attrs:
		# We don't handle instance attributes
		if attr.perInstance:
			raise RuntimeError("Instanced properties are not supported!")
		
		meshInput = MeshData()
		meshInput.indexResourceId = ib.resourceId
		meshInput.indexByteOffset = ib.byteOffset
		meshInput.indexByteStride = ib.byteStride
		meshInput.baseVertex = draw.baseVertex
		meshInput.indexOffset = draw.indexOffset
		meshInput.numIndices = draw.numIndices

		# If the draw doesn't use an index buffer, don't use it even if bound
		if not (draw.flags & rd.ActionFlags.Indexed):
			meshInput.indexResourceId = rd.ResourceId.Null()

		# The total offset is the attribute offset from the base of the vertex
		meshInput.vertexByteOffset = attr.byteOffset + vbs[attr.vertexBuffer].byteOffset + draw.vertexOffset * vbs[attr.vertexBuffer].byteStride
		meshInput.format = attr.format
		meshInput.vertexResourceId = vbs[attr.vertexBuffer].resourceId
		meshInput.vertexByteStride = vbs[attr.vertexBuffer].byteStride
		meshInput.name = attr.name

		meshInputs.append(meshInput)

	return meshInputs

def getIndices(controller, mesh):
	"""
	Extract index data from mesh
	Args:
		controller: Replay controller
		mesh: Mesh data object
	Returns:
		List of indices
	"""
	# Get the character for the width of index
	indexFormat = 'B'
	if mesh.indexByteStride == 2:
		indexFormat = 'H'
	elif mesh.indexByteStride == 4:
		indexFormat = 'I'

	# Duplicate the format by the number of indices
	indexFormat = str(mesh.numIndices) + indexFormat

	# If we have an index buffer
	if mesh.indexResourceId != rd.ResourceId.Null():
		# Fetch the data
		ibdata = controller.GetBufferData(mesh.indexResourceId, mesh.indexByteOffset, 0)
		# Unpack all the indices, starting from the first index to fetch
		offset = mesh.indexOffset * mesh.indexByteStride
		indices = struct.unpack_from(indexFormat, ibdata, offset)

		# Apply the baseVertex offset
		return [i + mesh.baseVertex for i in indices]
	else:
		# With no index buffer, just generate a range
		return tuple(range(mesh.numIndices))

def printMeshData(controller, meshData, draw):
	"""
	Export mesh data to CSV file and save output textures
	Args:
		controller: Replay controller
		meshData: List of mesh input data
		draw: Draw call information
	"""
	if isPrint:
		print("Processing mesh data...")
	
	indices = getIndices(controller, meshData[0])

	csvArray = []
	fileheader = []
	formatxyzw = [".x", ".y", ".z", ".w"]

	if isPrint:
		print("Mesh configuration:")
	
	# Build CSV header
	fileheader.append("VTX")
	fileheader.append("IDX")
	for attr in meshData:
		if not attr.format.Special():
			if isPrint:
				print("\t%s:" % attr.name)
				print("\t\t- vertex: %s / %d stride" % (attr.vertexResourceId, attr.vertexByteStride))
				print("\t\t- format: %s x %s @ %d" % (attr.format.compType, attr.format.compCount, attr.vertexByteOffset))
			
			headFormat = "{0}{1}"
			for i in range(0, attr.format.compCount):
				newStr = headFormat.format(attr.name, formatxyzw[i])
				fileheader.append(newStr)

	# Create models folder if it doesn't exist
	modelsFolder = "{0}/models".format(folderName)
	if not os.path.exists(modelsFolder):
		os.makedirs(modelsFolder)

	# Create CSV file with EID in filename, all in models folder
	csvArray.append(fileheader)
	outPath = "{0}/model_event{1}.csv".format(modelsFolder, draw.eventId)
	csvFile = open(outPath, "w", newline='')
	writer = csv.writer(csvFile)
	
	# Save output textures to the main texture folder
	for inputIter in draw.outputs:
		if not pySaveTexture(inputIter, draw.eventId, controller, "output"):
			break

	# Process each vertex
	i = 0
	for idx in indices:
		# Build vertex data array
		indiceArray = []
		
		if isPrint:
			print("Vertex %d is index %d:" % (i, idx))
		
		indiceArray.append(i)
		indiceArray.append(idx)
		
		for attr in meshData:
			if not attr.format.Special():
				# This is the data we're reading from. This would be good to cache instead of
				# re-fetching for every attribute for every index
				offset = attr.vertexByteOffset + attr.vertexByteStride * idx
				data = controller.GetBufferData(attr.vertexResourceId, offset, 0)

				# Get the value from the data
				value = unpackData(attr.format, data)
				
				for j in range(0, attr.format.compCount):
					indiceArray.append(value[j])

				if isPrint:
					print("\tAttribute '%s': %s" % (attr.name, value))

		csvArray.append(indiceArray)
		i = i + 1

	writer.writerows(csvArray)
	csvFile.close()
	print("Saved mesh data: {0}".format(outPath))

def sampleCodePreDraw(controller, draw):
	"""
	Process individual draw call if within specified range
	Args:
		controller: Replay controller
		draw: Draw call information
	"""
	if draw.eventId >= startIndex and draw.eventId <= endIndex:
		# Move to that draw
		controller.SetFrameEvent(draw.eventId, True)

		if isPrint:
			print("Decoding mesh inputs at %d: %s\n\n" % (draw.eventId, draw.name))

		# Calculate the mesh input configuration
		meshInputs = getMeshInputs(controller, draw)
		
		# Fetch and export the data from the mesh inputs
		printMeshData(controller, meshInputs, draw)

def sampleCodeRecursion(controller, draw):
	"""
	Recursively process draw calls and their children
	Args:
		controller: Replay controller
		draw: Draw call information
	"""
	sampleCodePreDraw(controller, draw)
	
	for d in draw.children:
		sampleCodeRecursion(controller, d)

def sampleCode(controller):
	"""
	Main processing function - iterate through all root draw calls
	Args:
		controller: Replay controller
	"""
	for draw in controller.GetRootActions():
		sampleCodeRecursion(controller, draw)

def loadCapture(filename):
	"""
	Load and initialize capture file for replay
	Args:
		filename: Path to RenderDoc capture file
	Returns:
		Tuple of (capture_handle, controller)
	"""
	if isPrint:
		print("Loading capture file...")
	
	# Open a capture file handle
	cap = rd.OpenCaptureFile()

	# Open a particular file - see also OpenBuffer to load from memory
	status = cap.OpenFile(filename, '', None)

	# Make sure the file opened successfully
	if status != rd.ReplayStatus.Succeeded:
		raise RuntimeError("Couldn't open file: " + str(status))

	# Make sure we can replay
	if not cap.LocalReplaySupport():
		raise RuntimeError("Capture cannot be replayed")

	# Initialise the replay
	status, controller = cap.OpenCapture(rd.ReplayOptions(), None)

	if status != rd.ReplayStatus.Succeeded:
		raise RuntimeError("Couldn't initialise replay: " + str(status))

	return (cap, controller)

# Main execution logic
if 'pyrenderdoc' in globals():
	# Running inside RenderDoc UI
	if isPrint:
		print("Running inside RenderDoc UI...")
	pyrenderdoc.Replay().BlockInvoke(sampleCode)
else:
	# Running as standalone script
	if isPrint:
		print("Running as standalone script...")
	
	rd.InitialiseReplay(rd.GlobalEnvironment(), [])

	if len(sys.argv) <= 1:
		if isPrint:
			print('Usage: python3 {} filename.rdc'.format(sys.argv[0]))
		sys.exit(0)

	cap, controller = loadCapture(sys.argv[1])

	sampleCode(controller)

	controller.Shutdown()
	cap.Shutdown()

	rd.ShutdownReplay()

print("Export completed!")
print("Textures saved in: {0}/textures/".format(folderName))
print("Models saved in: {0}/models/".format(folderName))