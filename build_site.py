#!/usr/bin/env python3
"""Build static SEO HTML pages, sitemap.xml, robots.txt, and llms.txt from models.json."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
BASE_URL = "https://developer-assistants.github.io/open-source-llms"
REPO_URL = "https://github.com/developer-assistants/open-source-llms"
GSC_META = '<meta name="google-site-verification" content="HqgfQrEQATXaycciOAu8GzuJP8BSRHtaR1JrgBtnApU" />'
UPDATED_AT = "2026-11-25"

NAV_ITEMS = [
    ("index.html", "Directory"),
    ("best-open-source-llm.html", "Best models"),
    ("free-large-language-models.html", "Free LLMs"),
    ("local-llms-by-vram.html", "By VRAM"),
    ("open-source-coding-llms.html", "Coding"),
    ("open-source-reasoning-llms.html", "Reasoning"),
    ("open-source-llm-licenses.html", "Licenses"),
    ("self-hosted-llm-inference.html", "Serving"),
]


def load_models() -> list[dict[str, Any]]:
    data = json.loads((ROOT / "models.json").read_text(encoding="utf-8"))
    return data["models"]


def fmt_params(m: dict[str, Any]) -> str:
    total = int(m["total_params_b"]) if float(m["total_params_b"]).is_integer() else m["total_params_b"]
    if m["architecture"] == "MoE":
        active = int(m["active_params_b"]) if float(m["active_params_b"]).is_integer() else m["active_params_b"]
        return f"{total}B ({active}B active)"
    return f"{total}B"


def fmt_ctx(k: int) -> str:
    if k >= 1000:
        m = k / 1000
        return f"{int(m)}M" if m.is_integer() else f"{m:.1f}M"
    return f"{k}K"


def license_pill(m: dict[str, Any]) -> str:
    tier = m["license_tier"]
    cls = "pill pill--oss" if tier == "permissive-oss" else (
        "pill pill--community" if tier == "community-commercial" else "pill pill--research"
    )
    return f'<span class="{cls}">{html.escape(m["license"])}</span>'


def render_rows(models: list[dict[str, Any]], include_compare: bool = False) -> str:
    rows = []
    for m in models:
        tags = "".join(
            f'<span class="pill pill--tag">{html.escape(t)}</span>'
            for t in m["primary_use_cases"][:3]
        )
        run_cmd = (
            f'<code>ollama run {html.escape(m["ollama_tag"])}</code>'
            if m["ollama_tag"]
            else '<span class="model-org">vLLM / SGLang</span>'
        )
        action_td = (
            f'<td><button type="button" class="btn btn--sm" data-compare-id="{html.escape(m["id"])}">Compare</button></td>'
            if include_compare
            else ""
        )
        rows.append(
            f"""          <tr>
            <td>
              <span class="model-name"><a href="{html.escape(m['huggingface_url'])}" target="_blank" rel="noopener">{html.escape(m['name'])}</a></span>
              <span class="model-org">{html.escape(m['organization'])} · {html.escape(m['architecture'])}</span>
              <div class="model-summary">{html.escape(m['summary'])}</div>
            </td>
            <td class="mono">{html.escape(fmt_params(m))}</td>
            <td class="mono">{html.escape(fmt_ctx(m['context_window_k']))}</td>
            <td class="mono">{html.escape(str(m['vram_q4_gb']))} GB</td>
            <td>{license_pill(m)}</td>
            <td>{tags}<div style="margin-top:0.35rem">{run_cmd}</div></td>
            {action_td}
          </tr>"""
        )
    return "\n".join(rows)


def render_header(current_file: str) -> str:
    links = []
    for fname, label in NAV_ITEMS:
        aria = ' aria-current="page"' if fname == current_file else ""
        links.append(f'<a href="./{fname}"{aria}>{html.escape(label)}</a>')
    links.append(f'<a href="{REPO_URL}" target="_blank" rel="noopener">GitHub</a>')
    return f"""  <header class="site-header">
    <div class="container site-header__inner">
      <a class="brand" href="./index.html">
        <span>Open Source LLMs</span>
        <span class="brand__badge">2026</span>
      </a>
      <nav class="nav" aria-label="Primary">
        {"".join(links)}
      </nav>
    </div>
  </header>"""


def render_footer() -> str:
    return f"""  <footer class="site-footer">
    <div class="container site-footer__inner">
      <div>
        Maintained by <a href="https://github.com/developer-assistants">developer-assistants</a>.
        Dataset updated {UPDATED_AT} under the MIT License.
      </div>
      <div class="nav">
        <a href="./models.json">models.json</a>
        <a href="./llms.txt">llms.txt</a>
        <a href="./sitemap.xml">sitemap.xml</a>
        <a href="{REPO_URL}">Repository</a>
      </div>
    </div>
  </footer>"""


def wrap_page(
    *,
    filename: str,
    title: str,
    description: str,
    body_html: str,
    json_ld: str,
    include_gsc: bool = False,
    include_js: bool = False,
) -> str:
    canonical = f"{BASE_URL}/" if filename == "index.html" else f"{BASE_URL}/{filename}"
    gsc_line = f"\n  {GSC_META}" if include_gsc else ""
    script_line = '\n  <script src="./app.js" defer></script>' if include_js else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">{gsc_line}
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{BASE_URL}/assets/preview.svg">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(description)}">
  <meta name="twitter:image" content="{BASE_URL}/assets/preview.svg">
  <link rel="icon" href="./assets/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="./styles/site.css">
  <script type="application/ld+json">
{json_ld}
  </script>
</head>
<body>
{render_header(filename)}
  <main>
{body_html}
  </main>
{render_footer()}{script_line}
</body>
</html>
"""


def build_index(models: list[dict[str, Any]]) -> str:
    permissive_count = sum(1 for m in models if m["license_tier"] == "permissive-oss")
    local_count = sum(1 for m in models if m["vram_q4_gb"] <= 24)
    moe_count = sum(1 for m in models if m["architecture"] == "MoE")

    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "Dataset",
                    "name": "Open Source LLMs Directory (2026)",
                    "description": "Structured directory comparing 26 open source LLMs and free large language models by parameter count, VRAM requirement, context window, license, and inference runtime.",
                    "url": f"{BASE_URL}/",
                    "license": "https://opensource.org/licenses/MIT",
                    "dateModified": UPDATED_AT,
                    "creator": {
                        "@type": "Organization",
                        "name": "developer-assistants",
                        "url": "https://github.com/developer-assistants",
                    },
                },
                {
                    "@type": "FAQPage",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": "What is the best open source LLM right now?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": "For multi-GPU reasoning and coding clusters, DeepSeek-R1, DeepSeek-V3.1, Qwen3-235B-A22B, and Qwen3-Coder-480B lead under MIT and Apache 2.0 licenses. For a single 24 GB consumer GPU, Qwen3-32B, DeepSeek-R1-Distill-Qwen-32B, Devstral Small 24B, and Gemma 3 27B give the strongest local performance.",
                            },
                        },
                        {
                            "@type": "Question",
                            "name": "Which free large language models allow unrestricted commercial use?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": "Models under Apache 2.0 or MIT licenses allow commercial hosting, fine-tuning, and product integration without monthly active user caps. Examples include DeepSeek-R1, DeepSeek-V3.1, Qwen3, Mistral Small 3.1, Devstral Small, GLM-4.5, gpt-oss-120b, gpt-oss-20b, Phi-4, and OLMo 2.",
                            },
                        },
                        {
                            "@type": "Question",
                            "name": "How much VRAM do I need to run an open source LLM locally?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": "At 4-bit quantization (Q4_K_M or AWQ), an 8B model needs roughly 5 to 6 GB of VRAM, a 14B model needs about 10 GB, a 24B to 32B model fits inside 16 to 24 GB, and a 70B dense model requires around 42 GB plus space for the KV cache.",
                            },
                        },
                        {
                            "@type": "Question",
                            "name": "What is the difference between open source LLMs and open-weight models?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": "Open-weight models publish downloadable weights and inference code, often under Apache 2.0, MIT, or custom community licenses, without releasing the full pretraining corpus. Truly open-source models like OLMo 2 release weights, training datasets, intermediate checkpoints, and training recipes together.",
                            },
                        },
                    ],
                },
            ],
        },
        indent=2,
    )

    body = f"""    <section class="hero">
      <div class="container hero__grid">
        <div>
          <p class="eyebrow">Open source LLMs · Verified 2026 directory</p>
          <h1>Compare 26 open source LLMs by VRAM, license, and task</h1>
          <p class="lead">Filter free large language models from DeepSeek, Qwen, Llama, Gemma, Mistral, GLM, Kimi, OpenAI gpt-oss, Phi, and OLMo. Check exact 4-bit and FP16 memory requirements, commercial terms, and runnable Ollama or vLLM commands.</p>
          <div class="hero__actions">
            <a class="btn btn--primary" href="#directory">Browse model matrix</a>
            <a class="btn" href="#vram-calculator">VRAM fit calculator</a>
            <a class="btn" href="{REPO_URL}" target="_blank" rel="noopener">GitHub CLI &amp; JSON</a>
          </div>
        </div>

        <aside class="metrics-card" aria-label="Dataset summary">
          <div class="metric-box">
            <span class="metric-val metric-val--accent">{len(models)}</span>
            <span class="metric-lbl">Verified open-weight LLMs</span>
          </div>
          <div class="metric-box">
            <span class="metric-val">{permissive_count}</span>
            <span class="metric-lbl">Apache 2.0 or MIT</span>
          </div>
          <div class="metric-box">
            <span class="metric-val">{local_count}</span>
            <span class="metric-lbl">Fit on 24 GB GPU (Q4)</span>
          </div>
          <div class="metric-box">
            <span class="metric-val">{moe_count}</span>
            <span class="metric-lbl">Mixture-of-Experts</span>
          </div>
          <div class="metric-box metric-box--wide">
            <div class="cli-bar"><span>$</span>python3 llm_advisor.py --recommend --vram 24 --task coding --permissive-only</div>
          </div>
        </aside>
      </div>
    </section>

    <section class="section" id="directory">
      <div class="container">
        <div class="section-head">
          <h2>Interactive open source LLM matrix</h2>
          <p>Filter all {len(models)} models by available GPU memory, quantization precision, commercial license tier, architecture, and primary workload.</p>
        </div>

        <form class="filter-bar" onsubmit="return false;">
          <div class="field">
            <label for="filter-search">Search model or family</label>
            <input id="filter-search" type="search" placeholder="DeepSeek, Qwen, Llama, 32B...">
          </div>
          <div class="field">
            <label for="filter-vram">Max GPU VRAM</label>
            <select id="filter-vram">
              <option value="">Any memory</option>
              <option value="8">Up to 8 GB (Laptop)</option>
              <option value="16">Up to 16 GB (RTX 4060 Ti / M-series)</option>
              <option value="24">Up to 24 GB (RTX 3090 / 4090)</option>
              <option value="48">Up to 48 GB (A6000 / L40S)</option>
              <option value="80">Up to 80 GB (A100 / H100)</option>
              <option value="256">Up to 256 GB (Multi-GPU)</option>
            </select>
          </div>
          <div class="field">
            <label for="filter-precision">Quantization</label>
            <select id="filter-precision">
              <option value="q4">4-bit (GGUF Q4 / AWQ)</option>
              <option value="fp16">16-bit (FP16 / BF16)</option>
            </select>
          </div>
          <div class="field">
            <label for="filter-license">License tier</label>
            <select id="filter-license">
              <option value="">All licenses</option>
              <option value="permissive-oss">Apache 2.0 / MIT</option>
              <option value="community-commercial">Community Commercial</option>
              <option value="non-commercial-research">Research / Non-Commercial</option>
            </select>
          </div>
          <div class="field">
            <label for="filter-arch">Architecture</label>
            <select id="filter-arch">
              <option value="">Dense and MoE</option>
              <option value="Dense">Dense</option>
              <option value="MoE">Mixture-of-Experts (MoE)</option>
            </select>
          </div>
          <div class="field">
            <label for="filter-task">Workload</label>
            <select id="filter-task">
              <option value="">All tasks</option>
              <option value="coding">Coding</option>
              <option value="reasoning">Reasoning &amp; math</option>
              <option value="agentic">Agentic tool use</option>
              <option value="local">Local / laptop</option>
              <option value="rag">Long-context RAG</option>
              <option value="vision">Vision / multimodal</option>
              <option value="open_data">Open training data</option>
            </select>
          </div>
        </form>

        <div class="toolbar">
          <span id="result-count">Showing {len(models)} of {len(models)} open-source LLMs</span>
          <button type="button" class="btn btn--sm" id="filter-reset">Reset filters</button>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Parameters</th>
                <th>Context</th>
                <th>VRAM (Q4)</th>
                <th>License</th>
                <th>Use cases &amp; runtime</th>
                <th>Compare</th>
              </tr>
            </thead>
            <tbody id="models-tbody">
{render_rows(models, include_compare=True)}
            </tbody>
          </table>
        </div>

        <div class="compare-tray" id="compare-tray" aria-live="polite">
          <div class="compare-tray__head">
            <h3>Side-by-side model comparison</h3>
            <button type="button" class="btn btn--sm" id="clear-compare">Clear selection</button>
          </div>
          <div class="table-wrap">
            <table id="compare-table"></table>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="vram-calculator">
      <div class="container">
        <div class="section-head">
          <h2>Local LLM hardware and VRAM fit calculator</h2>
          <p>Select your GPU memory or Apple Silicon unified memory budget to see the strongest models that leave room for KV cache.</p>
        </div>
        <div class="calc-grid">
          <div class="card">
            <div class="field" style="margin-bottom:0.85rem">
              <label for="calc-hardware">Hardware preset</label>
              <select id="calc-hardware">
                <option value="8">8 GB VRAM (RTX 4060 / 16 GB laptop)</option>
                <option value="16">16 GB VRAM (RTX 4060 Ti / 24 GB Mac)</option>
                <option value="24" selected>24 GB VRAM (RTX 3090 / RTX 4090 / 32 GB Mac)</option>
                <option value="48">48 GB VRAM (A6000 / L40S / 64 GB Mac)</option>
                <option value="80">80 GB VRAM (A100 / H100 / 128 GB Mac)</option>
                <option value="320">4x 80 GB H100 (320 GB cluster)</option>
                <option value="640">8x 80 GB H100 (640 GB cluster)</option>
              </select>
            </div>
            <div class="field" style="margin-bottom:0.85rem">
              <label for="calc-task">Primary task</label>
              <select id="calc-task">
                <option value="general">General chat &amp; writing</option>
                <option value="coding">Coding &amp; IDE agents</option>
                <option value="reasoning">Reasoning &amp; math</option>
                <option value="agentic">Tool calling &amp; agents</option>
                <option value="rag">Document RAG</option>
                <option value="multimodal">Vision &amp; images</option>
              </select>
            </div>
            <div class="field" style="margin-bottom:0.85rem">
              <label for="calc-precision">Weights precision</label>
              <select id="calc-precision">
                <option value="q4" selected>4-bit (GGUF Q4_K_M / AWQ / MXFP4)</option>
                <option value="fp16">16-bit (FP16 / BF16)</option>
              </select>
            </div>
            <label style="display:flex;align-items:center;gap:0.5rem;font-size:0.9rem;cursor:pointer">
              <input id="calc-permissive" type="checkbox">
              Apache 2.0 and MIT licenses only
            </label>
          </div>
          <div class="calc-results" id="calc-output">
            <div class="calc-item">
              <div>
                <strong>Qwen3-32B</strong> <span class="model-org">· 32.8B · Apache-2.0</span>
                <div class="model-org">Needs ~20 GB (4 GB left for KV cache)</div>
              </div>
              <code>ollama run qwen3:32b</code>
            </div>
            <div class="calc-item">
              <div>
                <strong>Gemma 3 27B</strong> <span class="model-org">· 27.4B · Gemma License</span>
                <div class="model-org">Needs ~17 GB (7 GB left for KV cache)</div>
              </div>
              <code>ollama run gemma3:27b</code>
            </div>
            <div class="calc-item">
              <div>
                <strong>Devstral Small (24B)</strong> <span class="model-org">· 24B · Apache-2.0</span>
                <div class="model-org">Needs ~15 GB (9 GB left for KV cache)</div>
              </div>
              <code>ollama run devstral:24b</code>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Focused comparison guides</h2>
          <p>Dedicated breakdowns by use case, hardware budget, license terms, and serving engine.</p>
        </div>
        <div class="cluster-grid">
          <a class="cluster-card" href="./best-open-source-llm.html">
            <h3>Best open source LLM by category</h3>
            <p>Top picks for frontier clusters, single 24 GB GPUs, laptops, coding, vision, and RAG.</p>
          </a>
          <a class="cluster-card" href="./free-large-language-models.html">
            <h3>Free large language models for commercial use</h3>
            <p>Self-hosted Apache 2.0, MIT, and community-licensed models with zero per-token API fees.</p>
          </a>
          <a class="cluster-card" href="./local-llms-by-vram.html">
            <h3>Local LLMs by VRAM (8 GB to 80 GB)</h3>
            <p>Exact hardware sizing for consumer GPUs, Apple Silicon Macs, and workstation cards.</p>
          </a>
          <a class="cluster-card" href="./open-source-coding-llms.html">
            <h3>Open source coding LLMs</h3>
            <p>Compare Qwen3-Coder, DeepSeek-V3.1, Devstral Small, Qwen2.5-Coder, and Kimi K2.</p>
          </a>
          <a class="cluster-card" href="./open-source-reasoning-llms.html">
            <h3>Open source reasoning LLMs</h3>
            <p>Chain-of-thought models including DeepSeek-R1, Qwen3, GLM-4.5, gpt-oss, and Phi-4.</p>
          </a>
          <a class="cluster-card" href="./open-source-llm-licenses.html">
            <h3>Open source LLM licenses explained</h3>
            <p>Apache 2.0 and MIT vs Llama Community, Gemma, Modified MIT, and CC-BY-NC.</p>
          </a>
          <a class="cluster-card" href="./self-hosted-llm-inference.html">
            <h3>Self-hosted inference engines</h3>
            <p>When to pick Ollama, llama.cpp, vLLM, or SGLang for local and production serving.</p>
          </a>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Frequently asked questions</h2>
        </div>
        <div class="faq-list">
          <div class="faq-item">
            <h3>What is the best open source LLM right now?</h3>
            <p>On multi-GPU servers, DeepSeek-R1, DeepSeek-V3.1, Qwen3-235B-A22B, and Qwen3-Coder-480B lead on reasoning and software engineering under MIT and Apache 2.0 terms. On a single 24 GB GPU, Qwen3-32B, DeepSeek-R1-Distill-Qwen-32B, Devstral Small 24B, and Gemma 3 27B give the highest output quality without cluster hardware.</p>
          </div>
          <div class="faq-item">
            <h3>Which free large language models allow unrestricted commercial use?</h3>
            <p>Models published under Apache 2.0 or MIT let you host, fine-tune, and ship commercial products without active-user ceilings. That group includes DeepSeek-R1, DeepSeek-V3.1, the Qwen3 line, Mistral Small 3.1, Devstral Small, GLM-4.5, gpt-oss-120b, gpt-oss-20b, Phi-4, and OLMo 2.</p>
          </div>
          <div class="faq-item">
            <h3>How much VRAM do I need to run an open source LLM locally?</h3>
            <p>At 4-bit quantization, an 8B dense model takes 5 to 6 GB of VRAM, a 14B model takes around 10 GB, a 24B to 32B model fits inside 16 to 24 GB, and a 70B dense model needs about 42 GB before KV cache. Leave 2 to 6 GB of spare memory if you plan to use 32K or 128K context windows.</p>
          </div>
          <div class="faq-item">
            <h3>What is the difference between open source LLMs and open-weight models?</h3>
            <p>Most releases in this directory are open-weight: the weights and inference code are free to download, while the pretraining corpus stays private. Fully open-source releases such as AllenAI OLMo 2 also publish the training datasets, data-filtering scripts, and intermediate checkpoints under Apache 2.0.</p>
          </div>
        </div>
      </div>
    </section>"""

    return wrap_page(
        filename="index.html",
        title="Open Source LLMs Directory & Comparison (2026) | Free Large Language Models",
        description="Compare 26 open source LLMs and free large language models by VRAM, license, context window, coding, and reasoning. Interactive hardware calculator and Python CLI.",
        body_html=body,
        json_ld=json_ld,
        include_gsc=True,
        include_js=True,
    )


def build_subpage(
    *,
    filename: str,
    title: str,
    description: str,
    h1: str,
    lede: str,
    eyebrow: str,
    filtered_models: list[dict[str, Any]],
    sections_html: str,
) -> str:
    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Open Source LLMs", "item": f"{BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": h1, "item": f"{BASE_URL}/{filename}"},
            ],
        },
        indent=2,
    )

    body = f"""    <section class="hero">
      <div class="container">
        <div class="breadcrumbs"><a href="./index.html">Open Source LLMs</a> / {html.escape(h1)}</div>
        <p class="eyebrow">{html.escape(eyebrow)}</p>
        <h1>{html.escape(h1)}</h1>
        <p class="lead">{html.escape(lede)}</p>
        <div class="hero__actions">
          <a class="btn btn--primary" href="./index.html#directory">Open interactive directory</a>
          <a class="btn" href="./index.html#vram-calculator">Check VRAM fit</a>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Matching models ({len(filtered_models)})</h2>
        </div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Parameters</th>
                <th>Context</th>
                <th>VRAM (Q4)</th>
                <th>License</th>
                <th>Use cases &amp; runtime</th>
              </tr>
            </thead>
            <tbody>
{render_rows(filtered_models, include_compare=False)}
            </tbody>
          </table>
        </div>
      </div>
    </section>

{sections_html}"""

    return wrap_page(
        filename=filename,
        title=title,
        description=description,
        body_html=body,
        json_ld=json_ld,
        include_gsc=False,
        include_js=False,
    )


def build_all() -> None:
    models = load_models()
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "models.json").write_text((ROOT / "models.json").read_text(encoding="utf-8"), encoding="utf-8")

    pages: dict[str, str] = {}
    pages["index.html"] = build_index(models)

    # 1. Best open source LLM
    best_ids = [
        "deepseek-r1",
        "deepseek-v3-1",
        "qwen3-235b-a22b",
        "qwen3-32b",
        "qwen3-coder-480b",
        "llama-4-maverick",
        "llama-4-scout",
        "gemma-3-27b",
        "devstral-small",
        "glm-4-5",
        "kimi-k2",
        "gpt-oss-120b",
        "gpt-oss-20b",
    ]
    by_id = {m["id"]: m for m in models}
    best_models = [by_id[i] for i in best_ids if i in by_id]
    pages["best-open-source-llm.html"] = build_subpage(
        filename="best-open-source-llm.html",
        title="Best Open Source LLM in 2026: Ranked by Hardware & Workload",
        description="Find the best open source LLM for coding, reasoning, RAG, multimodal vision, and local 24 GB GPUs. Side-by-side specs for DeepSeek, Qwen3, Llama 4, Gemma 3, and gpt-oss.",
        h1="Best open source LLM by workload and GPU tier",
        lede="There is no single winner across every hardware budget. Pick the strongest open-weight model for your exact GPU memory, latency target, and commercial license requirements.",
        eyebrow="Selection guide · Best open source LLM",
        filtered_models=best_models,
        sections_html="""    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Category winners at a glance</h2>
        </div>
        <div class="card-grid">
          <div class="card">
            <h3>Frontier reasoning cluster</h3>
            <p><strong>DeepSeek-R1</strong> and <strong>DeepSeek-V3.1</strong> deliver top math, logic, and code generation under the MIT license when you have multi-GPU H100 or B200 capacity.</p>
          </div>
          <div class="card">
            <h3>Best single 24 GB GPU model</h3>
            <p><strong>Qwen3-32B</strong> handles general chat, multilingual work, and coding on one RTX 3090 or RTX 4090 at 4-bit quantization under Apache 2.0.</p>
          </div>
          <div class="card">
            <h3>Best local coding agent</h3>
            <p><strong>Devstral Small (24B)</strong> and <strong>Qwen2.5-Coder-32B</strong> pair low latency with multi-file editing and fill-in-the-middle completion.</p>
          </div>
          <div class="card">
            <h3>Best long-context RAG</h3>
            <p><strong>Llama 4 Scout</strong> stretches context to 10M tokens on a single quantized 80 GB GPU, while <strong>Llama 4 Maverick</strong> handles 1M tokens with multimodal inputs.</p>
          </div>
        </div>
      </div>
    </section>""",
    )

    # 2. Free large language models
    free_commercial = [m for m in models if m["license_tier"] in ("permissive-oss", "community-commercial")]
    pages["free-large-language-models.html"] = build_subpage(
        filename="free-large-language-models.html",
        title="Free Large Language Models (2026): Self-Hosted & Commercial-Ready",
        description="Directory of 24 free large language models you can download, self-host, and run with zero API token fees under Apache 2.0, MIT, Llama, and Gemma licenses.",
        h1="Free large language models you can self-host",
        lede="Every model listed here has free downloadable weights and allows commercial deployment either without restrictions (Apache 2.0 and MIT) or under permissive community terms.",
        eyebrow="Zero API fees · Free large language models",
        filtered_models=free_commercial,
        sections_html="""    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>How free self-hosted LLMs compare to paid APIs</h2>
          <p>Downloading weights removes per-token billing, vendor rate limits, and third-party data retention. Your cost shifts to local electricity or rented GPU hours, which becomes cheaper than commercial APIs once a team runs steady batch jobs or private code assistants.</p>
        </div>
        <pre><code># Run a free Apache 2.0 model locally in two commands
ollama pull qwen3:8b
ollama run qwen3:8b</code></pre>
      </div>
    </section>""",
    )

    # 3. Local LLMs by VRAM
    local_models = sorted([m for m in models if m["vram_q4_gb"] <= 80], key=lambda x: x["vram_q4_gb"])
    pages["local-llms-by-vram.html"] = build_subpage(
        filename="local-llms-by-vram.html",
        title="Local Open Source LLMs by VRAM: 8 GB, 16 GB, 24 GB, 48 GB & 80 GB",
        description="Match open source LLMs to your exact GPU VRAM or Apple Silicon unified memory. Tested 4-bit and FP16 sizing for laptops, RTX 4090, and single H100 servers.",
        h1="Local open source LLMs by VRAM tier",
        lede="Memory bandwidth and VRAM capacity decide which models run smoothly on your machine. These 4-bit estimates leave practical headroom for context KV cache.",
        eyebrow="Hardware sizing · Local LLMs",
        filtered_models=local_models,
        sections_html="""    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Quick VRAM rule of thumb</h2>
        </div>
        <div class="card-grid">
          <div class="card">
            <h3>8 GB VRAM (laptops)</h3>
            <p>Run 4B to 8B models at Q4_K_M: <strong>Gemma 3 4B</strong>, <strong>Qwen3-8B</strong>, and <strong>Llama 3.1 8B</strong>.</p>
          </div>
          <div class="card">
            <h3>16 GB VRAM (mid-range GPU / 24 GB Mac)</h3>
            <p>Step up to 12B to 24B models: <strong>gpt-oss-20b</strong>, <strong>Phi-4 (14B)</strong>, <strong>Gemma 3 12B</strong>, and <strong>Mistral Small 3.1 (24B)</strong>.</p>
          </div>
          <div class="card">
            <h3>24 GB VRAM (RTX 3090 / 4090)</h3>
            <p>Sweet spot for dense 24B to 32B models: <strong>Qwen3-32B</strong>, <strong>DeepSeek-R1-Distill-Qwen-32B</strong>, <strong>Gemma 3 27B</strong>, and <strong>Devstral Small</strong>.</p>
          </div>
          <div class="card">
            <h3>48 GB to 80 GB VRAM</h3>
            <p>Fits 70B dense and 100B+ MoE models: <strong>Llama 3.3 70B</strong>, <strong>GLM-4.5-Air</strong>, <strong>gpt-oss-120b</strong>, and <strong>Llama 4 Scout</strong>.</p>
          </div>
        </div>
      </div>
    </section>""",
    )

    # 4. Coding LLMs
    coding_models = [m for m in models if "coding" in m["primary_use_cases"] or m["capabilities"]["coding"]]
    pages["open-source-coding-llms.html"] = build_subpage(
        filename="open-source-coding-llms.html",
        title="Best Open Source Coding LLMs (2026): Local IDE & Agentic Models",
        description="Compare open source LLMs for coding, autocomplete, and repository-scale software agents: Qwen3-Coder, DeepSeek-V3.1, Devstral Small, Qwen2.5-Coder, and Kimi K2.",
        h1="Open source coding LLMs for IDE and agent workflows",
        lede="Coding workloads split into two different jobs: fast low-latency inline autocomplete (dense 8B to 32B models) and multi-file agentic refactoring (large MoE or dedicated agent models).",
        eyebrow="Software engineering · Coding LLMs",
        filtered_models=coding_models,
        sections_html="""    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Pairing a coding model with your editor</h2>
          <p>Use Continue, Cline, Aider, or OpenCode pointed at a local Ollama or vLLM OpenAI-compatible endpoint (<code>http://localhost:11434/v1</code> or <code>http://localhost:8000/v1</code>). Dense 24B to 32B models keep latency under a second for autocomplete, while MoE models handle multi-file diffs and terminal debugging.</p>
        </div>
      </div>
    </section>""",
    )

    # 5. Reasoning LLMs
    reasoning_models = [m for m in models if m["capabilities"]["reasoning"]]
    pages["open-source-reasoning-llms.html"] = build_subpage(
        filename="open-source-reasoning-llms.html",
        title="Best Open Source Reasoning LLMs (2026): DeepSeek-R1, Qwen3, GLM-4.5 & gpt-oss",
        description="Compare open-weight reasoning and math LLMs with chain-of-thought and hybrid thinking modes, from 8B laptop models to 671B clusters.",
        h1="Open source reasoning LLMs",
        lede="Reasoning models allocate extra inference tokens to verify math, code logic, and multi-step planning before writing the final answer.",
        eyebrow="Chain of thought · Reasoning LLMs",
        filtered_models=reasoning_models,
        sections_html="""    <section class="section">
      <div class="container">
        <div class="section-head">
          <h2>Hybrid thinking vs always-on reasoning</h2>
          <p>Models such as <strong>Qwen3</strong>, <strong>DeepSeek-V3.1</strong>, and <strong>GLM-4.5</strong> let you toggle thinking mode per request, so simple formatting prompts stay fast while hard debugging prompts use full chain of thought. Dedicated reasoning models like <strong>DeepSeek-R1</strong> always emit reasoning traces.</p>
        </div>
      </div>
    </section>""",
    )

    # 6. Licenses
    pages["open-source-llm-licenses.html"] = build_subpage(
        filename="open-source-llm-licenses.html",
        title="Open Source LLM Licenses Explained: Apache 2.0, MIT, Llama & Gemma",
        description="Compare commercial terms across open source LLM licenses. Understand Apache 2.0, MIT, Llama Community MAU caps, Gemma terms, Modified MIT, and CC-BY-NC.",
        h1="Open source LLM licenses explained",
        lede="Before deploying a free large language model in production, verify whether its license is standard OSI-approved Apache 2.0 or MIT, a community license with commercial clauses, or research-only.",
        eyebrow="Compliance & legal · LLM licensing",
        filtered_models=models,
        sections_html="""    <section class="section">
      <div class="container">
        <div class="card-grid">
          <div class="card">
            <h3>Permissive OSS (Apache 2.0 / MIT)</h3>
            <p>Allows commercial hosting, fine-tuning, distillation, and redistribution with copyright notice. Apache 2.0 adds an explicit patent grant.</p>
          </div>
          <div class="card">
            <h3>Community Commercial</h3>
            <p>Llama Community, Gemma, and Modified MIT allow commercial products for most organizations, while adding clauses such as Meta's 700M monthly active user threshold or restrictions on training competing base models.</p>
          </div>
          <div class="card">
            <h3>Research / Non-Commercial</h3>
            <p>Mistral Research License (MRL) and CC-BY-NC-4.0 allow free evaluation and academic work, while commercial production requires a separate enterprise agreement.</p>
          </div>
        </div>
      </div>
    </section>""",
    )

    # 7. Self-hosted inference
    pages["self-hosted-llm-inference.html"] = build_subpage(
        filename="self-hosted-llm-inference.html",
        title="Self-Hosted LLM Inference: Ollama vs llama.cpp vs vLLM vs SGLang",
        description="Choose the right serving engine for open source LLMs. Compare Ollama, llama.cpp, vLLM, and SGLang by throughput, quantization format, and hardware support.",
        h1="Self-hosted LLM inference engines compared",
        lede="The same open-weight model behaves very differently depending on the runtime. Pick local GGUF runners for single-user workstations and PagedAttention servers for concurrent API traffic.",
        eyebrow="Deployment · Serving runtimes",
        filtered_models=[m for m in models if "vLLM" in m["runtimes"]][:12],
        sections_html="""    <section class="section">
      <div class="container">
        <div class="card-grid">
          <div class="card">
            <h3>Ollama &amp; LM Studio</h3>
            <p>Fastest path on macOS, Linux, and Windows desktops. Pulls GGUF weights in one command and exposes a local OpenAI-compatible API.</p>
          </div>
          <div class="card">
            <h3>llama.cpp</h3>
            <p>Low-level C++ engine behind Ollama with fine-grained control over CPU/GPU layer offloading, KV cache quantization, and speculative decoding.</p>
          </div>
          <div class="card">
            <h3>vLLM</h3>
            <p>Production GPU server with PagedAttention, continuous batching, AWQ/FP8/MXFP4 kernels, and tensor parallelism across multi-GPU nodes.</p>
          </div>
          <div class="card">
            <h3>SGLang</h3>
            <p>High-throughput serving runtime featuring RadixAttention prefix caching for multi-turn agent loops, structured JSON outputs, and large MoE clusters.</p>
          </div>
        </div>
        <pre><code># Serve an Apache 2.0 model with an OpenAI-compatible endpoint using vLLM
vllm serve Qwen/Qwen3-32B --tensor-parallel-size 1 --max-model-len 32768</code></pre>
      </div>
    </section>""",
    )

    for fname, content in pages.items():
        (DOCS / fname).write_text(content, encoding="utf-8")

    # sitemap.xml
    urls_xml = []
    for fname in pages:
        loc = f"{BASE_URL}/" if fname == "index.html" else f"{BASE_URL}/{fname}"
        prio = "1.0" if fname == "index.html" else "0.8"
        urls_xml.append(
            f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{UPDATED_AT}</lastmod>
    <priority>{prio}</priority>
  </url>"""
        )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls_xml)
        + "\n</urlset>\n"
    )
    (DOCS / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    # robots.txt
    robots = f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n"
    (DOCS / "robots.txt").write_text(robots, encoding="utf-8")

    # llms.txt (root + docs)
    llms_lines = [
        "# Open Source LLMs Directory (developer-assistants/open-source-llms)",
        "",
        "> Verified 2026 catalog of 26 open source LLMs and free large language models compared by parameter count, VRAM requirement, context window, license tier, and inference runtime.",
        "",
        "## Primary URLs",
        f"- Web Directory & VRAM Calculator: {BASE_URL}/",
        f"- GitHub Repository & Python CLI: {REPO_URL}",
        f"- Machine-Readable Dataset (JSON): {BASE_URL}/models.json",
        "",
        "## Comparison Guides",
        f"- Best Open Source LLM by Workload: {BASE_URL}/best-open-source-llm.html",
        f"- Free Large Language Models (Commercial-Ready): {BASE_URL}/free-large-language-models.html",
        f"- Local LLMs by VRAM (8 GB to 80 GB): {BASE_URL}/local-llms-by-vram.html",
        f"- Open Source Coding LLMs: {BASE_URL}/open-source-coding-llms.html",
        f"- Open Source Reasoning LLMs: {BASE_URL}/open-source-reasoning-llms.html",
        f"- Open Source LLM Licenses Explained: {BASE_URL}/open-source-llm-licenses.html",
        f"- Self-Hosted LLM Inference (Ollama, llama.cpp, vLLM, SGLang): {BASE_URL}/self-hosted-llm-inference.html",
        "",
        "## Indexed Models",
    ]
    for m in models:
        llms_lines.append(
            f"- {m['name']} ({m['organization']}): {fmt_params(m)}, {fmt_ctx(m['context_window_k'])} context, "
            f"~{m['vram_q4_gb']} GB VRAM (Q4), {m['license']} ({m['huggingface_url']})"
        )
    llms_text = "\n".join(llms_lines) + "\n"
    (ROOT / "llms.txt").write_text(llms_text, encoding="utf-8")
    (DOCS / "llms.txt").write_text(llms_text, encoding="utf-8")
    print(f"Built {len(pages)} HTML pages, sitemap.xml, robots.txt, and llms.txt.")


if __name__ == "__main__":
    build_all()
