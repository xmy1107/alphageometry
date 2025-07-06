#!/bin/bash

# 定义输入文件和输出文件
input_files=("gen.txt" "gen1.txt" "gen2.txt" "gen3.txt")
output_file="data.txt"

# 如果输出文件已经存在，先删除
if [ -f "$output_file" ]; then
    rm "$output_file"
fi

# 合并文件内容
for file in "${input_files[@]}"; do
    if [ -f "$file" ]; then
        cat "$file" >> "$output_file"
        echo "" >> "$output_file"  # 可选：添加一个换行符
    else
        echo "Warning: $file not found!"
    fi
done

echo "Files have been successfully merged into $output_file."
