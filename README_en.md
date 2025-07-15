# CSV to OBJ Converter


A Python tool for converting vertex CSV files exported from RenderDoc into OBJ 3D model files.

[简体中文](./README_zh_cn.md)

## Features

- **Intelligent Column Detection**: Automatically detects position, normal, and texture coordinate columns in CSV files
- **Batch Conversion**: Supports single file conversion or batch processing of all CSV files in the current directory
- **Triangle List Support**: Designed for triangle list topology commonly used in games
- **Flexible Output**: Generates appropriate OBJ face formats based on available data
- **Encoding Compatibility**: Supports UTF-8 encoding for correct handling of Chinese and other characters

## System Requirements

- Python 3.6+
- RenderDoc v1.39
- No extra dependencies, uses only Python standard library

## Installation

Simply download the `csv_to_obj.py` file, no extra installation required.

## About RenderDocExport.py

This repository also includes `RenderDocExport.py`, a script **designed to run inside the Python Shell environment of RenderDoc**. It will export three folders in RenderDoc:
- All VS input data Mesh CSVs in the capture file
- All textures in the capture file as PNG
- All textures in the capture file as EXR

**Note: This script is NOT intended to be run in a terminal/command line, but must be executed inside RenderDoc's built-in Python Shell.**

```python
# Configuration
folderName = "D:/capMesh1" # Save path
startIndex = 1200 # Start export EID (limit DrawCall range)
endIndex = 2000   # End export EID
```
Typical usage:

1. Open the capture file in RenderDoc and enter the Mesh Viewer.
2. Open RenderDoc's Python Shell (`Window` → `Python Shell`).
3. Load and run `RenderDocExport.py` in the Python Shell to export all mesh vertex data as CSV files.

The exported CSV files can then be converted using `csv_to_obj.py` from this project.

Python API for RenderDoc: [Python for RenderDoc](https://renderdoc.org/docs/python_api/examples/renderdoc_intro.html#)

## Usage

### Single File Conversion

```bash
# Convert a single CSV file, output filename is generated automatically
python csv_to_obj.py input.csv

# Specify output filename
python csv_to_obj.py input.csv -o output.obj
```

### Batch Conversion

```bash
# Convert all CSV files in the script directory
python csv_to_obj.py
```

## Supported CSV Format

This tool is specifically designed for vertex data exported from RenderDoc, and supports automatic detection of the following column types:

### Required Data
- **Position Data**: Columns containing `POS` or `POSITION` (e.g., `in_POSITION0.x`, `in_POSITION0.y`, `in_POSITION0.z`)

### Optional Data
- **Normal Data**: Columns containing `NORM` or `NORMAL` (e.g., `in_NORMAL0.x`, `in_NORMAL0.y`, `in_NORMAL0.z`)
- **Texture Coordinates**: Columns containing `TEX` or `TEXCOORD` (e.g., `in_TEXCOORD0.x`, `in_TEXCOORD0.y`)

### Standard Example CSV Format (RenderDoc Mesh Viewer VSinput, **NOT** VS out & GS/DS out)
```
VTX,IDX,in_POSITION0.x,in_POSITION0.y,in_POSITION0.z,in_NORMAL0.x,in_NORMAL0.y,in_NORMAL0.z,in_TEXCOORD0.x,in_TEXCOORD0.y
0,0,1.0,2.0,3.0,0.0,1.0,0.0,0.5,0.5
1,1,4.0,5.0,6.0,0.0,1.0,0.0,0.0,1.0
2,2,7.0,8.0,9.0,0.0,1.0,0.0,1.0,0.0
```

## Output Format

The generated OBJ file includes:

- **Vertex Positions** (`v`): 3D coordinates
- **Texture Coordinates** (`vt`): UV coordinates (if available, V coordinate is automatically flipped)
- **Vertex Normals** (`vn`): Normal vectors (if available)
- **Face Definitions** (`f`): Triangle face indices (vertex references)

### Face Format Examples
```obj
# With position, UV, and normal
f 1/1/1 2/2/2 3/3/3

# With position and UV only
f 1/1 2/2 3/3

# With position and normal only
f 1//1 2//2 3//3

# With position only
f 1 2 3
```

## Command Line Options

```
usage: csv_to_obj.py [-h] [-o OUTPUT] [input]

Convert vertex CSV files exported from RenderDoc to OBJ models. Supports single file or batch conversion.

positional arguments:
  input                 Optional: Path to a single CSV file to convert.
                        If omitted, the script will automatically convert all .csv files in the current directory.

optional arguments:
  -h, --help            Show help message and exit
  -o OUTPUT, --output OUTPUT
                        Optional: Path to the output OBJ file (only valid when a single input file is specified).
```

## Examples
A sample file `carpet.csv` is provided for you to try conversion.

### Example 1: Convert a single file
```bash
python csv_to_obj.py carpet.csv
# Output: mesh_data.obj
```

### Example 2: Specify output filename
```bash
python csv_to_obj.py carpet.csv -o my_model.obj
# Output: my_model.obj
```

### Example 3: Batch conversion
```bash
python csv_to_obj.py
# Automatically converts all .csv files in the current directory
```

## Error Handling

The tool includes comprehensive error handling:

- File existence check
- Required data column validation
- Empty file detection
- Format error prompts
- Batch conversion statistics report

## Technical Details

### Coordinate System Conversion
- V texture coordinate is automatically flipped (`1.0 - v`) to conform to OBJ format

### Face Indices
- OBJ files use 1-based indices
- Similar to Houdini: vertex class references point class to build faces
- Automatically handles correspondence of triangle vertex, UV, and normal indices

# FAQ

## Texture Export Issues

### Q1: Why are exported PNG textures black/transparent, but EXR format works fine?

**Reason:**
- **Data format limitation**: PNG uses 8-bit integer format (0-255), while EXR supports 32-bit float
- **Dynamic range difference**: Some textures contain data outside PNG's representable range
- **Special-purpose textures**: Normal maps, depth maps, HDR textures may contain special value ranges

**Common scenarios:**
- HDR environment maps or emissive materials
- Normal maps with values in [-1,1]
- Depth buffer data
- Textures used for data storage (not traditional color data)
- Improper alpha channel handling

**Solutions:**
1. **Use EXR format**: For float textures, normal maps, depth maps
2. **Check texture properties**: Choose the right format based on texture type
3. **Export both formats**: The script supports this, choose as needed

### Q2: How to decide whether to use PNG or EXR format?

**Recommended:**
- **PNG**: Regular color textures, UI textures, simple maps
- **EXR**: HDR textures, normal maps, depth maps, metallic/roughness maps, **when PNG appears transparent/black**

## UV Coordinate Issues

### Q3: Sometimes UVs don't match—why do exported model UVs need to be flipped 180°?

**Reason:**
Different graphics APIs use different texture coordinate systems:
- **OpenGL**: V origin at bottom-left, increases upwards
- **DirectX**: V origin at top-left, increases downwards
- **Vulkan**: Similar to DirectX, V increases downwards

**RenderDoc impact:**
RenderDoc may use a unified coordinate system for export; adjust as needed for your target platform.

**Solution:**
Just flip it in your UV editor (most of the time a 180° flip works).

### Q4: UVs display inconsistently in different 3D software—what to do?

**Common cases:**
- Exported from DirectX game, UVs are upside down in Blender
- Exported from OpenGL game, need flipping in some software

**Suggestions:**
1. **Export two versions**: Original and flipped UV
2. **Record original API**: Mark API type in filename
3. **Use import options**: Most 3D software provides UV flip options

## Performance

### Q5: Exporting many textures is slow—what can I do?

**Optimization tips:**
1. **Adjust export range**: Narrow `startIndex` and `endIndex`
2. **Skip duplicate textures**: Add resource ID cache to avoid saving duplicates
3. **Selective export**: Only export needed texture formats
4. **Batch processing**: Split large capture files into segments

**Tip:** If you encounter other issues, try:
1. Checking RenderDoc console error messages
2. Verifying capture file integrity
3. Ensuring write permissions for the target folder
4. **Refer to RenderDoc official docs for latest API info** (API changed significantly in v1.37)

## License

This project is licensed under the MIT License.

## Changelog

### v2.0
- Add RenderDoc Export Batch: exports three folders (csv, png, exr)

### v1.5
- Add batch conversion
- Improved column detection
- Enhanced error handling
- More detailed console output

### v1.0
- Basic CSV to OBJ conversion
- Support for position, normal, and UV data
- Single file conversion mode
