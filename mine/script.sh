# 合并数据
./merge.sh
# 处理数据
python process_data.py
# 分割成train和val
./split.sh
# 生成词表
onmt_build_vocab -config AG.yaml -n_sample 7000
# 训练模型
onmt_train -config AG.yaml