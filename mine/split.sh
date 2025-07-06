#!/bin/bash

cd $(pwd)
# 定义文件名
src_file="src.txt"
tgt_file="tgt.txt"
src_train="src-train.txt"
tgt_train="tgt-train.txt"
src_val="src-val.txt"
tgt_val="tgt-val.txt"

# 获取行数
total_lines=$(wc -l < "$src_file")

# 计算 90% 和 10% 的行数
train_lines=$(echo "$total_lines * 0.9 / 1" | bc)  # 强制转为整数
val_lines=$(echo "$total_lines - $train_lines" | bc)

# 拷贝前 90% 行作为训练集
head -n "$train_lines" "$src_file" > "$src_train"
head -n "$train_lines" "$tgt_file" > "$tgt_train"

# 拷贝后 10% 行作为验证集
tail -n "$val_lines" "$src_file" > "$src_val"
tail -n "$val_lines" "$tgt_file" > "$tgt_val"

echo "数据已成功拆分为训练集和验证集。"

