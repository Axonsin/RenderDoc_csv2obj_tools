
[English Version](./README_en.md)
# CSV to OBJ Converter

一个用于将RenderDoc导出的顶点CSV文件转换为OBJ 3D模型文件的Python工具。

## 功能特性

-  **智能列检测**: 自动识别CSV文件中的位置(Position)、法线(Normal)和纹理坐标(TexCoord)数据列
-  **批量转换**: 支持单文件转换或批量处理当前目录下的所有CSV文件
-  **三角面支持**: 专门为游戏中的三角面列表(Triangle List)拓扑结构设计
-  **灵活输出**: 根据可用数据自动生成合适的OBJ面格式
-  **编码兼容**: 支持UTF-8编码，确保中文等字符正确处理

## 系统要求

- Python 3.6+
- RenderDoc v.1.39
- 无需额外依赖包，使用Python标准库


## 安装

直接下载 `csv_to_obj.py` 文件即可使用，无需安装额外包。

## RenderDocExport.py 说明

本仓库还包含 `RenderDocExport.py`，该脚本**专为在 RenderDoc 程序内的 Python Shell 环境下运行而设计**，在 RenderDoc 中会导出三个文件夹，每个文件夹包含：
- 该截帧文件内的所有VS input data Mesh csv
- 截帧文件内的所有Texture into png
- 截帧文件内的所有Texture into exr。

**请注意：此脚本不是在终端（命令行）运行的，而是需要在 RenderDoc 的内置 Python Shell 中执行。**

```python
# Configuration
folderName = "D:/capMesh1" # 保存路径
startIndex = 1200 # 起始导出EID。限定DrawCall遍历范围
endIndex = 2000 # 终止导出EID

```
典型用法：

1. 在 RenderDoc 打开捕获截帧文件，进入 Mesh Viewer。
2. 打开 RenderDoc 的 Python Shell（菜单栏：`Window` → `Python Shell`）。
3. 在 Python Shell 中加载并运行 `RenderDocExport.py`/或者直接进行，即可导出当前 Mesh Viewer 的顶点数据为 CSV 文件。

这样导出的 CSV 文件可直接用本项目的 `csv_to_obj.py` 进行转换。

Python API for RenderDoc: [Pyhon for RenderDoc](https://renderdoc.org/docs/python_api/examples/renderdoc_intro.html#)

## 使用方法

### 单文件转换

```bash
# 转换单个CSV文件，输出文件名自动生成
python csv_to_obj.py input.csv

# 指定输出文件名
python csv_to_obj.py input.csv -o output.obj
```

### 批量转换

```bash
# 转换该脚本目录下的所有CSV文件
python csv_to_obj.py
```

## 支持的CSV格式

该工具专门设计用于处理RenderDoc导出的顶点数据，支持以下列类型的自动检测：

### 必需数据
- **位置数据**: 包含 `POS` 或 `POSITION` 的列（如 `in_POSITION0.x`, `in_POSITION0.y`, `in_POSITION0.z`）

### 可选数据
- **法线数据**: 包含 `NORM` 或 `NORMAL` 的列（如 `in_NORMAL0.x`, `in_NORMAL0.y`, `in_NORMAL0.z`）
- **纹理坐标**: 包含 `TEX` 或 `TEXCOORD` 的列（如 `in_TEXCOORD0.x`, `in_TEXCOORD0.y`）

### 标准示例CSV格式（RenderDoc Mesh Viewer VSinput，**NOT** VS out & GS/DS out）
```
VTX,IDX,in_POSITION0.x,in_POSITION0.y,in_POSITION0.z,in_NORMAL0.x,in_NORMAL0.y,in_NORMAL0.z,in_TEXCOORD0.x,in_TEXCOORD0.y
0,0,1.0,2.0,3.0,0.0,1.0,0.0,0.5,0.5
1,1,4.0,5.0,6.0,0.0,1.0,0.0,0.0,1.0
2,2,7.0,8.0,9.0,0.0,1.0,0.0,1.0,0.0
```

## 输出格式

生成的OBJ文件包含：

- **顶点位置** (`v`): 3D坐标，
- **纹理坐标** (`vt`): UV坐标（如果可用，V坐标会自动翻转）
- **顶点法线** (`vn`): 法线向量（如果可用）
- **面定义** (`f`): 三角面索引，又称为vertex

### 面格式示例
```obj
# 包含位置、UV和法线
f 1/1/1 2/2/2 3/3/3

# 仅包含位置和UV
f 1/1 2/2 3/3

# 仅包含位置和法线
f 1//1 2//2 3//3

# 仅包含位置
f 1 2 3
```

## 命令行选项

```
usage: csv_to_obj.py [-h] [-o OUTPUT] [input]

将RenderDoc导出的顶点CSV文件转换为OBJ模型。支持单文件或批量转换。

positional arguments:
  input                 可选: 要转换的单个CSV文件路径。
                        如果留空，脚本将自动转换当前目录下的所有.csv文件。

optional arguments:
  -h, --help            显示帮助信息并退出
  -o OUTPUT, --output OUTPUT
                        可选: 输出的OBJ文件路径 (仅在指定单个输入文件时有效)。
```

## 使用示例
本项目提供了carpet.csv供您尝试转换。

### 例子1：转换单个文件
```bash
python csv_to_obj.py carpet.csv
# 输出: mesh_data.obj
```

### 例子2：指定输出文件名
```bash
python csv_to_obj.py carpet.csv -o my_model.obj
# 输出: my_model.obj
```

### 例子3：批量转换
```bash
python csv_to_obj.py
# 自动转换当前目录下所有 .csv 文件
```

## 错误处理

工具包含完善的错误处理机制：

-  文件不存在检查
-  必需数据列验证
-  空文件检测
-  格式错误提示
-  批量转换统计报告

## 技术细节

### 坐标系转换
- V纹理坐标自动翻转（`1.0 - v`）以适应OBJ格式规范

### 面索引
- OBJ文件使用1基索引（从1开始计数）
- 其实就是引用Houdini的类似处理机制：由vertex class引用point class，并以此构建成面
- 自动处理三角面的顶点、UV和法线索引对应关系


*Thinking...*

> 用户要求我把之前关于PNG/EXR问题和UV翻转问题的回答整理成README文档中的FAQ部分。我需要用清晰、简洁的格式来呈现这些技术问题和解决方案，让用户能够快速理解问题原因和解决方法。
> 
> 我应该：
> 1. 使用标准的FAQ格式
> 2. 简化技术术语，但保持准确性
> 3. 提供实用的解决方案
> 4. 用Markdown格式编写
> 5. 按照重要性和常见程度排序

# FAQ 

## 纹理导出问题

### Q1: 为什么导出的PNG纹理是黑色/透明的，但EXR格式可以正常使用？

**原因：**
- **数据格式限制**：PNG使用8位整数格式（0-255），而EXR支持32位浮点格式
- **动态范围差异**：某些纹理包含超出PNG表示范围的数据
- **特殊用途纹理**：法线贴图、深度贴图、HDR纹理等可能包含特殊数值范围

**常见问题场景：**
- HDR环境贴图或发光材质
- 法线贴图包含[-1,1]范围的值
- 深度缓冲区数据
- 用作数据存储的纹理（非传统颜色数据）
- Alpha通道处理不当

**解决方案：**
1. **使用EXR格式**：对于浮点纹理、法线贴图、深度贴图
2. **检查纹理属性**：根据纹理类型选择合适的保存格式
3. **同时导出两种格式**：当前脚本已实现，可根据需要选择使用

### Q2: 如何判断应该使用PNG还是EXR格式？

**推荐选择：**
- **PNG适用**：普通颜色纹理、UI纹理、简单贴图
- **EXR适用**：HDR纹理、法线贴图、深度贴图、金属度/粗糙度贴图、**PNG图像为透明/黑的时候**

## UV坐标问题

### Q3: 有时候uv会对不上，为什么导出的模型UV坐标需要翻转180°？

**原因：**
不同图形API使用不同的纹理坐标系统：
- **OpenGL**：V坐标原点在左下角，向上递增
- **DirectX**：V坐标原点在左上角，向下递增  
- **Vulkan**：类似DirectX，V坐标向下递增

**RenderDoc影响：**
RenderDoc可能统一使用某种坐标系统导出，在不同目标平台需要相应调整。

**解决方案：**
自己调吧，大部分在uv编辑器里转个180°就行了（bushi）

### Q4: UV坐标在不同3D软件中显示不一致怎么办？

**常见情况：**
- 从DirectX游戏导出，在Blender中UV上下颠倒
- 从OpenGL游戏导出，在某些软件中需要翻转

**解决建议：**
1. **导出两个版本**：原始UV和翻转UV版本
2. **记录原始API**：在文件名中标注来源API类型
3. **使用目标软件的导入选项**：多数3D软件提供UV翻转选项

## 性能

### Q5: 导出大量纹理时速度很慢怎么办？

**优化建议：**
1. **调整导出范围**：请缩小`startIndex`和`endIndex`范围
2. **跳过重复纹理**：添加资源ID缓存避免重复保存
3. **选择性导出**：只导出需要的纹理格式
4. **分批处理**：将大型capture文件分段处理


**提示：** 如果遇到其他问题，建议：
1. 检查RenderDoc控制台输出的错误信息
2. 确认capture文件的完整性
3. 验证目标文件夹的写入权限
4. **请参考RenderDoc官方文档获取最新API信息**，API在1.37版本就曾发生过python函数接口的重大变化


## 许可证

本项目采用MIT许可证。

## 更新日志

### v2.0
- 添加RenderDoc Export Batch，导出三个文件夹：csv,png,exr

### v1.5
- 添加批量转换功能
- 改进列检测算法
- 增强错误处理
- 添加详细的控制台输出

### v1.0
- 基础CSV到OBJ转换功能
- 支持位置、法线和UV数据
- 单文件转换模式
