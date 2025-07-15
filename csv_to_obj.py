# csv_to_obj.py
import csv
import argparse
import os

def find_column_indices(header):
    """根据表头猜测POSITION, NORMAL, TEXCOORD的起始列索引"""
    indices = {'pos': -1, 'norm': -1, 'uv': -1}
    # 将header转为大写以进行不区分大小写的匹配
    #初始化字典，存储每个属性的起始列索引。这里默认值为-1，表示未找到。
    upper_header = [h.upper() for h in header]
    # 将所有的表头字符串转换为大写，这样在搜索时可以不区分大小写，提高匹配准确性。

    
    try:
        # 查找包含 'POS' 或 'POSITION' 的第一个元素
        indices['pos'] = next(i for i, h in enumerate(upper_header) if 'POS' in h)
        # 推导式和生成器表达式，等价于：
        # indices['pos'] = -1  # 默认设为 -1 表示没找到
        # for i, h in enumerate(upper_header):
        #     if 'POS' in h:
        #         indices['pos'] = i
        # break  # 找到第一个就退出循环
        print(f"检测到位置(Position)数据起始于列: {indices['pos']}")
    except StopIteration:
        print("警告: 在CSV表头中未找到位置(Position)数据。")

    try:
        # 查找包含 'NORM' 或 'NORMAL' 的第一个元素
        indices['norm'] = next(i for i, h in enumerate(upper_header) if 'NORM' in h)
        print(f"检测到法线(Normal)数据起始于列: {indices['norm']}")
    except StopIteration:
        print("警告: 在CSV表头中未找到法线(Normal)数据。")
        
    try:
        # 查找包含 'TEX' 或 'TEXCOORD' 的第一个元素
        indices['uv'] = next(i for i, h in enumerate(upper_header) if 'TEX' in h)
        print(f"检测到UV(TexCoord)数据起始于列: {indices['uv']}")
    except StopIteration:
        print("警告: 在CSV表头中未找到UV(TexCoord)数据。")
        
    return indices

def convert_csv_to_obj(input_file, output_file):
    """
    将RenderDoc导出的CSV文件转换为OBJ模型文件。
    拓扑结构为三角面列表 (Triangle List)。
    示例Class：VTX, IDX, in_POSITION0.x, in_POSITION0.y, in_POSITION0.z, in_NORMAL0.x, in_NORMAL0.y, in_NORMAL0.z, in_NORMAL0.w, in_TANGENT0.x, in_TANGENT0.y, in_TANGENT0.z, in_TANGENT0.w, in_TEXCOORD0.x, in_TEXCOORD0.y, in_TEXCOORD1.x, in_TEXCOORD1.y
    
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            
            # 读取表头
            header = next(reader)
            col_indices = find_column_indices(header)

            if col_indices['pos'] == -1:
                print("错误: CSV文件中必须包含顶点位置数据。脚本终止。")
                return

            # 写入OBJ文件头信息
            outfile.write(f"# Converted from {os.path.basename(input_file)}\n")
            outfile.write(f"# Vertex Count: Approximated from CSV rows\n\n")

            vertices = []
            for row in reader:
                vertices.append(row)

            # 写入顶点数据
            # 写入 v (顶点位置)
            for row in vertices:
                # RenderDoc导出的位置通常是4个分量 (x, y, z, w)
                x, y, z = row[col_indices['pos']:col_indices['pos']+3]
                outfile.write(f"v {x} {y} {z}\n")
            outfile.write("\n")

            # 写入 vt (纹理坐标)
            if col_indices['uv'] != -1:
                for row in vertices:
                    # UV通常是2个分量 (u, v)
                    u, v = row[col_indices['uv']:col_indices['uv']+2]
                    # OBJ格式的V坐标通常需要翻转 (1-v)
                    outfile.write(f"vt {u} {1.0 - float(v)}\n")
                outfile.write("\n")
            
            # 写入 vn (顶点法线)
            if col_indices['norm'] != -1:
                for row in vertices:
                    # 法线通常是3个分量 (nx, ny, nz)
                    nx, ny, nz = row[col_indices['norm']:col_indices['norm']+3]
                    outfile.write(f"vn {nx} {ny} {nz}\n")
                outfile.write("\n")

            # 写入面 f (face)/或者说vertices(Houdini Class)
            # 假设是三角面列表，每3个顶点构成一个面
            num_vertices = len(vertices)
            for i in range(0, num_vertices, 3):
                # 检查以防止索引越界
                if i + 2 < num_vertices:
                    # OBJ索引从1开始
                    i1, i2, i3 = i + 1, i + 2, i + 3
                    
                    # 根据可用的数据构建面定义
                    if col_indices['uv'] != -1 and col_indices['norm'] != -1:
                        # 格式: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3
                        outfile.write(f"f {i1}/{i1}/{i1} {i2}/{i2}/{i2} {i3}/{i3}/{i3}\n")
                    elif col_indices['uv'] != -1:
                        # 格式: f v1/vt1 v2/vt2 v3/vt3
                        outfile.write(f"f {i1}/{i1} {i2}/{i2} {i3}/{i3}\n")
                    elif col_indices['norm'] != -1:
                        # 格式: f v1//vn1 v2//vn2 v3//vn3
                        outfile.write(f"f {i1}//{i1} {i2}//{i2} {i3}//{i3}\n")
                    else:
                        # 格式: f v1 v2 v3
                        outfile.write(f"f {i1} {i2} {i3}\n")

            print(f"转换成功！OBJ文件已保存到: {output_file}")

    except FileNotFoundError:
        print(f"错误: 输入文件 '{input_file}' 未找到。")
    except Exception as e:
        print(f"转换过程中发生错误: {e}")

if __name__ == "__main__":
    # 使用argparse来方便地从命令行接收参数
    parser = argparse.ArgumentParser(description="将RenderDoc导出的顶点CSV文件转换为OBJ模型。")
    parser.add_argument("input", help="输入的CSV文件路径。")
    parser.add_argument("-o", "--output", help="输出的OBJ文件路径。如果未提供，将根据输入文件名自动生成。")
    
    args = parser.parse_args()
    
    # 决定输出文件名
    if args.output:
        output_filename = args.output
    else:
        # 将.csv后缀替换为.obj
        base_name = os.path.splitext(args.input)[0]
        output_filename = f"{base_name}.obj"
        
    convert_csv_to_obj(args.input, output_filename)