# Reminder Tool-Use Training Workflow

## 1) Dataset

- Cleaned dataset: `data/training_data_llm.cleaned.jsonl`
- Cleaner script: `scripts/clean_training_data_llm.py`


python generate_benchmark_prompts_structured.py --seed-md benchmark/seed.md --output benchmark/prompts_structured.jsonl
python build_tool_eval_cases_from_structured_prompts.py --prompts-jsonl benchmark/prompts_structured.jsonl --output benchmark/tool_eval_cases_structured.jsonl
python init_tool_eval_dataset_dynamic_time.py --cases-jsonl benchmark/tool_eval_cases_structured.jsonl --out-dir benchmark/eval_runs --with-sqlite --overwrite --now 2026-05-26T09:00:00+08:00


python init_tool_eval_dataset_dynamic_time.py --cases-jsonl benchmark/tool_eval_cases_structured.jsonl --out-dir benchmark/eval_runs --with-sqlite --overwrite --now 2026-05-26T09:00:00+08:00
python scripts/run_tool_eval_from_dataset.py --cases-jsonl benchmark/tool_eval_cases_structured.jsonl --eval-dir benchmark/eval_runs --model-path "..." --adapter-path "..." --report benchmark/reports/qwen_580.json


python scripts/clean_training_data_llm.py --input data/training_data2.jsonl --output data/training_data2.cleaned.jsonl --rejects data/training_data2.rejects.jsonl --report data/training_data2.clean_report.json

python scripts/split_jsonl_dataset.py --input data/training_data2.cleaned.jsonl --train-output data/training_data2.train.jsonl --val-output data/training_data2.val.jsonl --val-ratio 0.1 --seed 42 --stratify-by-scenario


```bash
python scripts/export_training_data_llm.py  --api-env configs/data/api_generation.env --output data/training_data_llm_onlytool.jsonl --n 1000 --endpoint responses
```

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

API few-shot tool-call parameter evaluation:

```bash
python scripts/run_toolcall_param_eval_api.py --api-env configs/data/api_generation.env --cases-jsonl benchmark/toolcall_param_cases.jsonl --max-samples 20 --report benchmark/reports/toolcall_param_eval_api.json
```

Or use the example YAML config:

```bash
python scripts/run_toolcall_param_eval_api.py --config configs/eval/toolcall_param_api_eval.example.yaml
```

The API endpoint should be OpenAI-compatible and provide `/chat/completions`. The script injects the four canonical reminder tools from `app.tool_registry` into the prompt and uses four few-shot examples by default. Add `--native-tools` when the provider supports OpenAI `tools` payloads.

##  4) web
```bash
python scripts/chat_web_demo.py --model-path "E:/LLM/Qwen/Qwen2.5-1.5B-Instruct" --adapter-path "outputs/qwen25_15b_dora/checkpoint-580" 
python scripts/chat_web_demo.py --model-path "E:/LLM/Qwen/Qwen2.5-1.5B-Instruct" --adapter-path "outputs/qwen25_15b_dora/checkpoint-800" --stateless 


```

mcp baseline:
```bash
python scripts/reminder_mcp_server_baseline.py --host 127.0.0.1 --port 8765
python scripts/web_mcp_baseline.py --model-path "E:/LLM/Qwen/Qwen2.5-1.5B-Instruct" --adapter-path "outputs/qwen25_15b_dora/checkpoint-580" --mcp-base-url "http://127.0.0.1:8765" --host 127.0.0.1 --port 8018
```

## 5) Local popup reminder watcher

Run one poll:

```bash
python scripts/run_reminder_notifier.py --once
```

Run continuously (default every 5 seconds):

```bash
python scripts/run_reminder_notifier.py --poll-interval 5
```
