# Model Learning Policy

Model learning and fine-tuning are last-resort candidates.

The benchmark loop may create:

- `outputs/model_learning/training_candidate_report.md`
- `outputs/model_learning/training_dataset_candidate.jsonl`

It must not automatically run fine-tuning or alter production model weights.

Training candidates must exclude benchmark test leakage.

