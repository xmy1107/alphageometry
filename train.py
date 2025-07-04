import os
import gin
import jax
import numpy as np
from absl import app, flags, logging
from inference_utils import parse_gin_configuration
from transformer import training_loop, text_dataset, models

FLAGS = flags.FLAGS

flags.DEFINE_string('gin_files', None, 'Comma-separated list of gin config files.')
flags.DEFINE_string('gin_params', None, 'Comma-separated list of gin parameter overrides.')
flags.DEFINE_string('output_dir', '/tmp/checkpoints', 'Directory to save checkpoints.')
flags.DEFINE_integer('train_steps', 1000, 'Number of training steps.')
flags.DEFINE_bool('verbose', False, 'Print inputs and outputs.')

def main(argv):
    # Step 1: Parse gin configuration
    gin_files = FLAGS.gin_files.split(',') if FLAGS.gin_files else []
    gin_params = FLAGS.gin_params.split(',') if FLAGS.gin_params else []
    parse_gin_configuration(gin_files, gin_params)

    # Step 2: Load dataset
    task_config = training_loop.decoder_stack.TransformerTaskConfig()
    train_ds, vocab = text_dataset.load_text_dataset(
        name=task_config.dataset_name,
        split=task_config.train_split,
        sequence_length=task_config.sequence_length,
        batch_size=task_config.batch_size,
        sequential=task_config.sequential_chunks,
        shard_dataset=False
    )

    train_iter = train_ds.as_numpy_iterator()

    # Step 3: Initialize Trainer
    def get_train_iter_fn():
        return train_iter

    trainer = training_loop.Trainer(
        get_training_dataset_iterator=get_train_iter_fn,
        get_test_dataset_iterator=None,
        pretty_print_input_function=None,
        process_summaries_function=models.process_summaries_function(vocab),
        load_dir=None,
        workdir=FLAGS.output_dir,
        replicate_mode=False
    )

    tstate, step, imodel, prngs = trainer.initialize_model()
    task = trainer.create_training_task('train', imodel, prngs, writers={})

    training_loop.clear_interstep_callbacks()
    training_loop.register_interstep_callbacks()

    # Step 4: Training loop
    logging.info("Start training for %d steps", FLAGS.train_steps)
    for i in range(step, step + FLAGS.train_steps):
        try:
            batch = next(train_iter)
        except StopIteration:
            logging.warning("Reached end of dataset. Restarting iterator.")
            train_iter = train_ds.as_numpy_iterator()
            batch = next(train_iter)

        if FLAGS.verbose:
            logging.info("Training step %d input: %s", i, batch)

        tstate, metrics_np = task.run_step(tstate, batch, i)
        training_loop.run_interstep_callbacks("train", i)

        if i % 100 == 0:
            logging.info("Step %d metrics: %s", i, metrics_np)

    # Step 5: Save checkpoint
    trainer.save_checkpoint(tstate, FLAGS.train_steps)
    logging.info("Checkpoint saved at step %d to %s", FLAGS.train_steps, FLAGS.output_dir)

if __name__ == '__main__':
    app.run(main)
