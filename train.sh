python train_model.py \
  --gin_files="transformer/configs/base.gin,transformer/configs/task/default.gin" \
  --gin_params="Trainer.batch_size = 8" \
  --train_steps=5000 \
  --output_dir="/path/to/checkpoints"

