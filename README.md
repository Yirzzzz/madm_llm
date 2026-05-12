# Reminder Tool-Use Training Workflow

## 1) Dataset

- Cleaned dataset: `data/training_data_llm.cleaned.jsonl`
- Cleaner script: `scripts/clean_training_data_llm.py`

## 2) Config-Driven LoRA/DoRA Training

Train with LoRA:

```bash
python scripts/train_adapter.py --config configs/train/qwen25_15b_lora.yaml
```

Train with DoRA:

```bash
python scripts/train_adapter.py --config configs/train/qwen25_15b_dora.yaml
```

Only edit YAML to switch backbone, dataset, output path, and PEFT settings.

## 3) Quick Tool-Use Evaluation

```bash
python scripts/eval_tooluse_model.py --config configs/eval/qwen25_15b_tooluse_eval.yaml
```

The report is written to the `output.report_file` configured in YAML.
