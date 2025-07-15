# csv_to_obj.py (v2 - 支持批量转换)
import csv
import argparse
import os

def find_column_indices(header):
    """根据表头猜测POSITION, NORMAL, TEXCOORD的起始列索引"""
    indices = {'pos': -1, 'norm': -1, 'uv': -1}
    # 将header转为大写以进行不区分大小写的匹配
    upper_header = [h.upper() for h in header]
    
    try:
        # 查找包含 'POS' 或 'POSITION' 的第一个元素
        indices['pos'] = next(i for i, h in enumerate(upper_header) if 'POS' in h)
        print(f"  [OK] 检测到位置(Position)数据起始于列: {indices['pos']}")
    except StopIteration:
        print("  [警告] 在CSV表头中未找到位置(Position)数据。")

    try:
        # 查找包含 'NORM' 或 'NORMAL' 的第一个元素
        indices['norm'] = next(i for i, h in enumerate(upper_header) if 'NORM' in h)
        print(f"  [OK] 检测到法线(Normal)数据起始于列: {indices['norm']}")
    except StopIteration:
        print("  [警告] 在CSV表头中未找到法线(Normal)数据。")
        
    try:
        # 查找包含 'TEX' 或 'TEXCOORD' 的第一个元素
        indices['uv'] = next(i for i, h in enumerate(upper_header) if 'TEX' in h)
        print(f"  [OK] 检测到UV(TexCoord)数据起始于列: {indices['uv']}")
    except StopIteration:
        print("  [警告] 在CSV表头中未找到UV(TexCoord)数据。")
        
    return indices

def convert_csv_to_obj(input_filepath, output_filepath):
    """
    将RenderDoc导出的CSV文件转换为OBJ模型文件。
    拓扑结构为三角面列表 (Triangle List)。
    Class举例：VTX, IDX, in_POSITION0.x, in_POSITION0.y, in_POSITION0.z, in_NORMAL0.x, in_NORMAL0.y, in_NORMAL0.z, in_NORMAL0.w, in_TANGENT0.x, in_TANGENT0.y, in_TANGENT0.z, in_TANGENT0.w, in_TEXCOORD0.x, in_TEXCOORD0.y, in_TEXCOORD1.x, in_TEXCOORD1.y

    """
    print(f"正在处理: {input_filepath} -> {output_filepath}")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as infile, \
             open(output_filepath, 'w', encoding='utf-8') as outfile:
            
            reader = csv.reader(infile)
            
            header = next(reader)
            col_indices = find_column_indices(header)

            if col_indices['pos'] == -1:
                print("  [错误] CSV文件中必须包含顶点位置数据。跳过此文件。")
                return False

            outfile.write(f"# Converted from {os.path.basename(input_filepath)}\n\n")

            vertices = list(reader)
            num_vertices = len(vertices)

            if num_vertices == 0:
                print("  [错误] CSV文件中没有数据行。跳过此文件。")
                return False

            # 写入 v (顶点位置)
            for row in vertices:
                x, y, z = row[col_indices['pos']:col_indices['pos']+3]
                outfile.write(f"v {x} {y} {z}\n")
            outfile.write("\n")

            # 写入 vt (纹理坐标)
            if col_indices['uv'] != -1:
                for row in vertices:
                    u, v = row[col_indices['uv']:col_indices['uv']+2]
                    outfile.write(f"vt {u} {1.0 - float(v)}\n")
                outfile.write("\n")
            
            # 写入 vn (顶点法线)
            if col_indices['norm'] != -1:
                for row in vertices:
                    nx, ny, nz = row[col_indices['norm']:col_indices['norm']+3]
                    outfile.write(f"vn {nx} {ny} {nz}\n")
                outfile.write("\n")

            # 写入面 f (face)
            for i in range(0, num_vertices, 3):
                if i + 2 < num_vertices:
                    i1, i2, i3 = i + 1, i + 2, i + 3
                    
                    if col_indices['uv'] != -1 and col_indices['norm'] != -1:
                        outfile.write(f"f {i1}/{i1}/{i1} {i2}/{i2}/{i2} {i3}/{i3}/{i3}\n")
                    elif col_indices['uv'] != -1:
                        outfile.write(f"f {i1}/{i1} {i2}/{i2} {i3}/{i3}\n")
                    elif col_indices['norm'] != -1:
                        outfile.write(f"f {i1}//{i1} {i2}//{i2} {i3}//{i3}\n")
                    else:
                        outfile.write(f"f {i1} {i2} {i3}\n")

            print(f"  [成功] 转换完成！模型已保存到: {output_filepath}")
            return True

    except FileNotFoundError:
        print(f"  [错误] 输入文件 '{input_filepath}' 未找到。")
    except Exception as e:
        print(f"  [错误] 转换过程中发生错误: {e}")
    return False

# ==============================================================================
# 脚本主入口点
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="将RenderDoc导出的顶点CSV文件转换为OBJ模型。支持单文件或批量转换。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # "input" 参数可选。
    # nargs='?' 表示这个参数可以出现0次或1次。
    # default=None 表示如果参数未提供，其值将是 None。
    parser.add_argument(
        "input", 
        nargs='?', 
        default=None,
        help="可选: 要转换的单个CSV文件路径。\n如果留空，脚本将自动转换当前目录下的所有.csv文件。"
    )
    # "-o" 参数现在只在单文件模式下有意义
    parser.add_argument(
        "-o", "--output", 
        help="可选: 输出的OBJ文件路径 (仅在指定单个输入文件时有效)。"
    )
    
    args = parser.parse_args()
    if args.input:
        # **单文件模式**: 用户提供了输入文件名
        print("模式: 单文件转换")
        input_filepath = args.input
        
        # 决定输出文件名
        if args.output:
            output_filepath = args.output
        else:
            base_name = os.path.splitext(input_filepath)[0]
            output_filepath = f"{base_name}.obj"
        
        convert_csv_to_obj(input_filepath, output_filepath)
        
    else:
        # **批量模式**: 用户没有提供输入文件名
        print("模式: 批量转换 (未指定输入文件，将搜索当前目录)")
        
        # 查找当前目录下的所有.csv文件
        # os.listdir('.') 获取当前目录所有文件名
        # f.lower().endswith('.csv') 确保能匹配 .csv, .CSV, .Csv 等
        csv_files = [f for f in os.listdir('.') if f.lower().endswith('.csv')]
        
        if not csv_files:
            print("在当前目录中未找到任何 .csv 文件。")
        else:
            print(f"找到 {len(csv_files)} 个CSV文件，准备开始转换...\n")
            success_count = 0
            fail_count = 0
            for filename in csv_files:
                base_name = os.path.splitext(filename)[0]
                output_filename = f"{base_name}.obj"
                
                if convert_csv_to_obj(filename, output_filename):
                    success_count += 1
                else:
                    fail_count += 1
                print("-" * 20) # 添加分隔符
            
            print("\n批量转换完成！")
            print(f"总计: {success_count} 个成功, {fail_count} 个失败。")