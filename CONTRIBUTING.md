# Contributing to open-source-llms

Pull requests that add new open-weight or open-source LLMs, correct VRAM measurements, or update license metadata are welcome.

## Dataset schema (`models.json`)

Each entry in `models.json` uses the following required fields:

- `id`: lowercase slug (for example, `qwen3-32b`).
- `name`: official model release name.
- `organization`: creator organization.
- `family`: model family name (DeepSeek, Qwen, Llama, Gemma, Mistral, GLM, Kimi, gpt-oss, Phi, OLMo, Command).
- `architecture`: `"Dense"` or `"MoE"`.
- `total_params_b`: total parameter count in billions.
- `active_params_b`: active parameters per token in billions (equal to `total_params_b` for dense models).
- `context_window_k`: native context window in thousands of tokens (for example, `128` for 128K, `1000` for 1M).
- `license`: official license name.
- `license_tier`: `"permissive-oss"`, `"community-commercial"`, or `"non-commercial-research"`.
- `open_data`: boolean (`true` only when pretraining corpora and training code are publicly released).
- `vram_q4_gb`: practical VRAM in GB at 4-bit quantization.
- `vram_fp16_gb`: practical VRAM in GB at FP16 / BF16.
- `modalities`: array such as `["text"]` or `["text", "vision"]`.
- `capabilities`: object with booleans for `reasoning`, `coding`, `tool_calling`, `multilingual`, `long_context`, and `local_friendly`.
- `primary_use_cases`: array of workload tags.
- `runtimes`: supported inference engines.
- `ollama_tag`: official Ollama tag string or `null`.
- `huggingface_url` and `repo_url`: official HTTPS links.
- `summary`: one plain technical sentence without hype or marketing phrases.

## Verification before opening a PR

```bash
python3 build_site.py
python3 llm_advisor.py --validate
python3 -m unittest discover -s tests -v
```
