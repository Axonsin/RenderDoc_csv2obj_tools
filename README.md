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
- 无需额外依赖包，使用Python标准库

## 安装

直接下载 `csv_to_obj.py` 文件即可使用，无需安装额外包。

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
# 转换和该脚本目录下的所有CSV文件
python csv_to_obj.py
```

## 支持的CSV格式

该工具专门设计用于处理RenderDoc导出的顶点数据，支持以下列类型的自动检测：

### 必需数据
- **位置数据**: 包含 `POS` 或 `POSITION` 的列（如 `in_POSITION0.x`, `in_POSITION0.y`, `in_POSITION0.z`）

### 可选数据
- **法线数据**: 包含 `NORM` 或 `NORMAL` 的列（如 `in_NORMAL0.x`, `in_NORMAL0.y`, `in_NORMAL0.z`）
- **纹理坐标**: 包含 `TEX` 或 `TEXCOORD` 的列（如 `in_TEXCOORD0.x`, `in_TEXCOORD0.y`）

### 示例CSV格式（RenderDoc Mesh Viewer VSinput，不是VS out和GS/DS out）
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


## 许可证

本项目采用MIT许可证。

## 更新日志

### v1.5
- 添加批量转换功能
- 改进列检测算法
- 增强错误处理
- 添加详细的控制台输出

### v1.0
- 基础CSV到OBJ转换功能
- 支持位置、法线和UV数据
- 单文件转换模式
