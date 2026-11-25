(() => {
  const DATA_URL = "./models.json";
  let allModels = [];
  let selectedCompare = [];

  const els = {
    search: document.getElementById("filter-search"),
    vram: document.getElementById("filter-vram"),
    precision: document.getElementById("filter-precision"),
    license: document.getElementById("filter-license"),
    arch: document.getElementById("filter-arch"),
    task: document.getElementById("filter-task"),
    resetBtn: document.getElementById("filter-reset"),
    countLabel: document.getElementById("result-count"),
    tbody: document.getElementById("models-tbody"),
    compareTray: document.getElementById("compare-tray"),
    compareTable: document.getElementById("compare-table"),
    clearCompare: document.getElementById("clear-compare"),
    calcHardware: document.getElementById("calc-hardware"),
    calcTask: document.getElementById("calc-task"),
    calcPrecision: document.getElementById("calc-precision"),
    calcPermissive: document.getElementById("calc-permissive"),
    calcOutput: document.getElementById("calc-output"),
  };

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatParams(m) {
    const total = `${m.total_params_b}B`;
    if (m.architecture === "MoE") {
      return `${total} (${m.active_params_b}B active)`;
    }
    return total;
  }

  function formatContext(k) {
    if (k >= 1000) {
      const m = k / 1000;
      return Number.isInteger(m) ? `${m}M` : `${m.toFixed(1)}M`;
    }
    return `${k}K`;
  }

  function licenseStatusClass(tier) {
    if (tier === "permissive-oss") return "status-text status-text--oss";
    if (tier === "community-commercial") return "status-text status-text--community";
    return "status-text status-text--research";
  }

  function matchesFilters(m) {
    const q = (els.search?.value || "").trim().toLowerCase();
    const maxVram = els.vram?.value ? Number(els.vram.value) : null;
    const prec = els.precision?.value || "q4";
    const lic = els.license?.value || "";
    const arch = els.arch?.value || "";
    const task = els.task?.value || "";

    if (q) {
      const hay = `${m.name} ${m.organization} ${m.family} ${m.license} ${m.summary} ${m.primary_use_cases.join(" ")}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }

    if (maxVram !== null) {
      const need = prec === "fp16" ? m.vram_fp16_gb : m.vram_q4_gb;
      if (need > maxVram) return false;
    }

    if (lic && m.license_tier !== lic) return false;
    if (arch && m.architecture !== arch) return false;

    if (task) {
      if (task === "vision") {
        if (!m.modalities.includes("vision")) return false;
      } else if (task === "open_data") {
        if (!m.open_data) return false;
      } else {
        const hasTag = m.primary_use_cases.includes(task) || Boolean(m.capabilities[task]);
        if (!hasTag) return false;
      }
    }

    return true;
  }

  function renderTable() {
    if (!els.tbody) return;
    const prec = els.precision?.value || "q4";
    const filtered = allModels.filter(matchesFilters);

    if (els.countLabel) {
      els.countLabel.textContent = `Showing ${filtered.length} of ${allModels.length} open-source LLMs`;
    }

    if (!filtered.length) {
      els.tbody.innerHTML = `<tr><td colspan="7">No models match the selected filters. Raise the VRAM budget or reset filters.</td></tr>`;
      return;
    }

    els.tbody.innerHTML = filtered
      .map((m) => {
        const vramVal = prec === "fp16" ? m.vram_fp16_gb : m.vram_q4_gb;
        const isCompared = selectedCompare.includes(m.id);
        const tags = escapeHtml(m.primary_use_cases.slice(0, 3).join(", "));
        const runCmd = m.ollama_tag
          ? `<code class="run-cmd">ollama run ${escapeHtml(m.ollama_tag)}</code>`
          : `<span class="model-meta">vLLM / SGLang</span>`;

        return `
          <tr>
            <td>
              <span class="model-name"><a href="${escapeHtml(m.huggingface_url)}" target="_blank" rel="noopener">${escapeHtml(m.name)}</a></span>
              <span class="model-meta">${escapeHtml(m.organization)}, ${escapeHtml(m.architecture)}</span>
              <div class="model-summary">${escapeHtml(m.summary)}</div>
            </td>
            <td class="mono num">${escapeHtml(formatParams(m))}</td>
            <td class="mono num">${escapeHtml(formatContext(m.context_window_k))}</td>
            <td class="mono num">${escapeHtml(vramVal)} GB</td>
            <td><span class="${licenseStatusClass(m.license_tier)}">${escapeHtml(m.license === "CC-BY-NC-4.0" ? "Creative Commons BY-NC 4.0" : m.license)}</span></td>
            <td><div class="tag-list">${tags}</div>${runCmd}</td>
            <td>
              <button type="button" class="key key--sm" data-compare-id="${escapeHtml(m.id)}">
                ${isCompared ? "Selected" : "Compare"}
              </button>
            </td>
          </tr>
        `;
      })
      .join("");
  }

  function renderCompare() {
    if (!els.compareTray || !els.compareTable) return;
    if (!selectedCompare.length) {
      els.compareTray.classList.remove("is-open");
      return;
    }
    els.compareTray.classList.add("is-open");
    const chosen = selectedCompare
      .map((id) => allModels.find((m) => m.id === id))
      .filter(Boolean);

    const rows = [
      ["Organization", (m) => m.organization],
      ["Architecture", (m) => m.architecture],
      ["Parameters", formatParams],
      ["Context window", (m) => formatContext(m.context_window_k)],
      ["VRAM Q4", (m) => `${m.vram_q4_gb} GB`],
      ["VRAM FP16", (m) => `${m.vram_fp16_gb} GB`],
      ["License", (m) => m.license],
      ["Modalities", (m) => m.modalities.join(", ")],
      ["Runtimes", (m) => m.runtimes.join(", ")],
      ["Ollama", (m) => (m.ollama_tag ? `ollama run ${m.ollama_tag}` : "Serve via vLLM / SGLang")],
    ];

    const thead = `<thead><tr><th>Spec</th>${chosen.map((m) => `<th>${escapeHtml(m.name)}</th>`).join("")}</tr></thead>`;
    const tbody = `<tbody>${rows
      .map(
        ([label, fn]) =>
          `<tr><td><strong>${escapeHtml(label)}</strong></td>${chosen
            .map((m) => `<td class="mono num">${escapeHtml(fn(m))}</td>`)
            .join("")}</tr>`
      )
      .join("")}</tbody>`;
    els.compareTable.innerHTML = thead + tbody;
  }

  function renderCalculator() {
    if (!els.calcOutput || !els.calcHardware) return;
    const budget = Number(els.calcHardware.value);
    const task = els.calcTask?.value || "general";
    const prec = els.calcPrecision?.value || "q4";
    const permissiveOnly = Boolean(els.calcPermissive?.checked);
    const vramKey = prec === "fp16" ? "vram_fp16_gb" : "vram_q4_gb";

    const fits = allModels
      .filter((m) => m[vramKey] <= budget)
      .filter((m) => (!permissiveOnly ? true : m.license_tier === "permissive-oss"))
      .sort((a, b) => {
        const aMatch = (a.primary_use_cases.includes(task) ? 2 : 0) + (a.capabilities[task] ? 1 : 0);
        const bMatch = (b.primary_use_cases.includes(task) ? 2 : 0) + (b.capabilities[task] ? 1 : 0);
        if (bMatch !== aMatch) return bMatch - aMatch;
        if (b[vramKey] !== a[vramKey]) return b[vramKey] - a[vramKey];
        return b.context_window_k - a.context_window_k;
      })
      .slice(0, 5);

    if (!fits.length) {
      els.calcOutput.innerHTML = `<div class="calc-item">No models fit ${budget} GB at ${prec.toUpperCase()} with those constraints. Switch to 4-bit quantization or a larger GPU tier.</div>`;
      return;
    }

    els.calcOutput.innerHTML = fits
      .map((m) => {
        const headroom = Math.max(0, Math.round((budget - m[vramKey]) * 10) / 10);
        const cmd = m.ollama_tag
          ? `ollama run ${m.ollama_tag}`
          : `vllm serve ${m.huggingface_url.replace("https://huggingface.co/", "")}`;
        return `
          <div class="calc-item">
            <div>
              <strong>${escapeHtml(m.name)}</strong>
              <span class="calc-item__meta">${escapeHtml(formatParams(m))}, ${escapeHtml(m.license)}</span>
              <span class="calc-item__meta">Needs ~${escapeHtml(m[vramKey])} GB (${headroom} GB left for KV cache)</span>
            </div>
            <code>${escapeHtml(cmd)}</code>
          </div>
        `;
      })
      .join("");
  }

  function bindEvents() {
    [els.search, els.vram, els.precision, els.license, els.arch, els.task].forEach((el) => {
      if (!el) return;
      el.addEventListener("input", renderTable);
      el.addEventListener("change", renderTable);
    });

    if (els.resetBtn) {
      els.resetBtn.addEventListener("click", () => {
        if (els.search) els.search.value = "";
        if (els.vram) els.vram.value = "";
        if (els.precision) els.precision.value = "q4";
        if (els.license) els.license.value = "";
        if (els.arch) els.arch.value = "";
        if (els.task) els.task.value = "";
        renderTable();
      });
    }

    if (els.tbody) {
      els.tbody.addEventListener("click", (e) => {
        const btn = e.target.closest("[data-compare-id]");
        if (!btn) return;
        const id = btn.getAttribute("data-compare-id");
        if (selectedCompare.includes(id)) {
          selectedCompare = selectedCompare.filter((item) => item !== id);
        } else {
          if (selectedCompare.length >= 3) selectedCompare.shift();
          selectedCompare.push(id);
        }
        renderTable();
        renderCompare();
      });
    }

    if (els.clearCompare) {
      els.clearCompare.addEventListener("click", () => {
        selectedCompare = [];
        renderTable();
        renderCompare();
      });
    }

    [els.calcHardware, els.calcTask, els.calcPrecision, els.calcPermissive].forEach((el) => {
      if (!el) return;
      el.addEventListener("change", renderCalculator);
    });
  }

  fetch(DATA_URL)
    .then((r) => r.json())
    .then((data) => {
      allModels = data.models || [];
      bindEvents();
      renderTable();
      renderCalculator();
    })
    .catch(() => {
      // Keep static HTML table intact if fetch fails
    });
})();
