# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# !/bin/bash
set -e
set -x

# 自己创建了环境
# virtualenv -p python3 .
# source ./bin/activate

# pip install --require-hashes -r requirements.txt

# gdown --folder https://bit.ly/alphageometry
DATA=ag_ckpt_vocab

MELIAD_PATH=meliad_lib/meliad
# mkdir -p $MELIAD_PATH
# git clone https://github.com/google-research/meliad $MELIAD_PATH
export PYTHONPATH=$PYTHONPATH:$MELIAD_PATH

DDAR_ARGS=(
  --defs_file=$(pwd)/defs.txt \
  --rules_file=$(pwd)/rules.txt \
);

BATCH_SIZE=2
BEAM_SIZE=2
DEPTH=2

SEARCH_ARGS=(
  --beam_size=$BEAM_SIZE
  --search_depth=$DEPTH
)

LM_ARGS=(
  --ckpt_path=$DATA \
  --vocab_path=$DATA/geometry.757.model \
  --gin_search_paths=$MELIAD_PATH/transformer/configs \
  --gin_file=base_htrans.gin \
  --gin_file=size/medium_150M.gin \
  --gin_file=options/positions_t5.gin \
  --gin_file=options/lr_cosine_decay.gin \
  --gin_file=options/seq_1024_nocache.gin \
  --gin_file=geometry_150M_generate.gin \
  --gin_param=DecoderOnlyLanguageModelGenerate.output_token_losses=True \
  --gin_param=TransformerTaskConfig.batch_size=$BATCH_SIZE \
  --gin_param=TransformerTaskConfig.sequence_length=128 \
  --gin_param=Trainer.restore_state_variables=False
);

echo $PYTHONPATH


# log_file="$(pwd)/alphageometry.log"
# > "$log_file"
# problems_file="$(pwd)/imo_ag_30.txt"
# problem_names=$(sed -n '1~2p' "$problems_file")
# while IFS= read -r problem_name; do
#     echo "===== 开始处理问题: $problem_name =====" | tee -a "$log_file"
#     # python -m alphageometry \
#     #     --alsologtostderr \
#     #     --problems_file="$problems_file" \
#     #     --problem_name="$problem_name" \
#     #     --mode=ddar \
#     #     "${DDAR_ARGS[@]}" >> "$log_file" 2>&1
#     python -m alphageometry \
#         --alsologtostderr \
#         --problems_file="$problems_file" \
#         --problem_name="$problem_name" \
#         --mode=alphageometry \
#         "${DDAR_ARGS[@]}" \
#         "${SEARCH_ARGS[@]}" \
#         "${LM_ARGS[@]}" >> "$log_file" 2>&1

    
#     echo "===== 完成问题: $problem_name =====" | tee -a "$log_file"
# done <<< "$problem_names"

# echo "所有问题处理完成，日志已保存至: $log_file"

# Run DDAR
python -m alphageometry \
--alsologtostderr \
--problems_file=$(pwd)/examples.txt \
--problem_name=orthocenter_aux \
--mode=ddar \
"${DDAR_ARGS[@]}"
# --problems_file=$(pwd)/imo_ag_30.txt \
# --problem_name=translated_imo_2005_p5 \


# Run AlphaGeometry
# log_file="$(pwd)/alphageometry.log"
# > "$log_file"
# python -m alphageometry \
# --alsologtostderr \
# --problems_file=$(pwd)/examples.txt \
# --problem_name=orthocenter \
# --mode=alphageometry \
# "${DDAR_ARGS[@]}" \
# "${SEARCH_ARGS[@]}" \
# "${LM_ARGS[@]}" >> "$log_file" 2>&1
# 2>&1 | grep "TensorRT\|GPU"
# 将 stderr 重定向到 stdout