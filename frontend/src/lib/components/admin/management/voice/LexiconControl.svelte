<script lang="ts">
  import { onMount } from "svelte";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Filter from "lucide-svelte/icons/filter";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Plus from "lucide-svelte/icons/plus";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { normalizeVn } from "$lib/utils/text";

  let {
    sttOverrides = $bindable(),
    sttStopwords = $bindable(),
    onStartTraining,
  } = $props<{
    sttOverrides: Record<string, string>;
    sttStopwords: string[];
    onStartTraining: (type: "lexicon_wrong" | "lexicon_stop") => void;
  }>();

  // R82: Safe initialization for bindable props
  onMount(() => {
    if (sttOverrides === undefined) sttOverrides = {};
    if (sttStopwords === undefined) sttStopwords = [];
  });

  let lexiconTab = $state<"overrides" | "stopwords">("overrides");
  let newOverrideWrong = $state("");
  let newOverrideRight = $state("");
  let newStopword = $state("");
  let editingOverride = $state<string | null>(null);
  let editingOverrideField = $state<"wrong" | "right">("wrong");
  let editingStopword = $state<number | null>(null);
  let isIngesting = $state(false);

  const RECOMMENDED_STOPWORDS = [
    "à",
    "ờ",
    "ừ",
    "ừm",
    "ha",
    "hả",
    "nhỉ",
    "nhé",
    "nha",
    "đó",
    "thế",
    "vậy",
    "mà",
    "thì",
    "là",
    "của",
    "ấy",
    "ô",
    "hề",
    "dạ",
    "vâng",
    "ồ",
    "úi",
    "chao",
    "ôi",
    "nè",
    "đấy",
    "kia",
    "này",
    "với",
    "nhưng",
    "những",
    "chứ",
    "thôi",
  ];

  async function addOverride() {
    const wrong = newOverrideWrong.trim().toLowerCase();
    const right = newOverrideRight.trim().toLowerCase();
    if (!wrong || !right) return;
    const snapshot = { ...sttOverrides };
    sttOverrides = { ...sttOverrides, [wrong]: right };
    newOverrideWrong = "";
    newOverrideRight = "";
    try {
      await apiClient.post("/api/v1/settings/lexicon/overrides", {
        wrong_word: wrong,
        right_word: right,
      });
      nanobot.showToast(`Đã thêm luật: ${wrong} ➔ ${right}`, "success");
    } catch {
      sttOverrides = snapshot;
      nanobot.showToast("Lỗi khi thêm luật.", "error");
    }
  }

  async function deleteOverride(wrong: string) {
    const snapshot = { ...sttOverrides };
    const newOvs = { ...sttOverrides };
    delete newOvs[wrong];
    sttOverrides = newOvs;
    try {
      await apiClient.delete(
        `/api/v1/settings/lexicon/overrides/${encodeURIComponent(wrong)}`,
      );
      nanobot.showToast(`Đã xoá luật: ${wrong}`, "success");
    } catch {
      sttOverrides = snapshot;
      nanobot.showToast("Lỗi khi xoá luật.", "error");
    }
  }

  async function addStopword(providedWord?: string) {
    const word = (providedWord || newStopword).trim().toLowerCase();
    if (!word || sttStopwords.includes(word)) return;
    const snapshot = [...sttStopwords];
    sttStopwords = [...sttStopwords, word];
    if (!providedWord) newStopword = "";
    try {
      await apiClient.post("/api/v1/settings/lexicon/stopwords", { word });
      nanobot.showToast(`Đã thêm từ dư thừa: ${word}`, "success");
    } catch {
      sttStopwords = snapshot;
      nanobot.showToast("Lỗi khi thêm từ dư thừa.", "error");
    }
  }

  async function deleteStopword(word: string) {
    const snapshot = [...sttStopwords];
    sttStopwords = sttStopwords.filter((w) => w !== word);
    try {
      await apiClient.delete(
        `/api/v1/settings/lexicon/stopwords/${encodeURIComponent(word)}`,
      );
      nanobot.showToast(`Đã xoá từ dư thừa: ${word}`, "success");
    } catch {
      sttStopwords = snapshot;
      nanobot.showToast("Lỗi khi xoá từ dư thừa.", "error");
    }
  }

  async function ingestDefaultStopwords() {
    isIngesting = true;
    nanobot.addLog("Initializing Neural Matrix Ingestion...", "SYS");
    let addedCount = 0;
    try {
      for (const word of RECOMMENDED_STOPWORDS) {
        if (!sttStopwords.includes(word)) {
          await apiClient.post("/api/v1/settings/lexicon/stopwords", { word });
          sttStopwords = [...sttStopwords, word];
          addedCount++;
          await new Promise((r) => setTimeout(r, 50));
        }
      }
      nanobot.addLog(
        `Neural Matrix Ingested: ${addedCount} units.`,
        "SYS",
        "success",
      );
      nanobot.showToast(`Đã nạp ${addedCount} từ vào hệ thống.`, "success");
    } catch {
      nanobot.addLog("Neural Matrix Ingestion Interrupted", "SYS", "error");
      nanobot.showToast("Lỗi khi nạp dữ liệu.", "error");
    } finally {
      isIngesting = false;
    }
  }

  async function updateStopword(index: number, oldWord: string) {
    const newWord = sttStopwords[index].trim().toLowerCase();
    if (!newWord || newWord === oldWord) {
      sttStopwords[index] = oldWord;
      editingStopword = null;
      return;
    }
    try {
      await apiClient.delete(
        `/api/v1/settings/lexicon/stopwords/${encodeURIComponent(oldWord)}`,
      );
      await apiClient.post("/api/v1/settings/lexicon/stopwords", {
        word: newWord,
      });
      editingStopword = null;
      nanobot.showToast(`Cập nhật: ${oldWord} ➔ ${newWord}`, "success");
    } catch {
      sttStopwords[index] = oldWord;
      editingStopword = null;
      nanobot.showToast("Lỗi khi cập nhật từ dư thừa", "error");
    }
  }

  async function updateOverride(
    oldWrong: string,
    field: "wrong" | "right",
    newValue: string,
  ) {
    const newVal = newValue.trim().toLowerCase();
    const currentRight = sttOverrides[oldWrong];
    if (
      !newVal ||
      (field === "wrong" && newVal === oldWrong) ||
      (field === "right" && newVal === currentRight)
    ) {
      editingOverride = null;
      return;
    }
    try {
      if (field === "wrong") {
        await apiClient.delete(
          `/api/v1/settings/lexicon/overrides/${encodeURIComponent(oldWrong)}`,
        );
        await apiClient.post("/api/v1/settings/lexicon/overrides", {
          wrong_word: newVal,
          right_word: currentRight,
        });
        const next = { ...sttOverrides };
        delete next[oldWrong];
        next[newVal] = currentRight;
        sttOverrides = next;
      } else {
        await apiClient.post("/api/v1/settings/lexicon/overrides", {
          wrong_word: oldWrong,
          right_word: newVal,
        });
        sttOverrides[oldWrong] = newVal;
      }
      editingOverride = null;
      nanobot.showToast("Cập nhật nắn lỗi thành công", "success");
    } catch {
      editingOverride = null;
      nanobot.showToast("Lỗi khi cập nhật nắn lỗi", "error");
    }
  }

  // Handle capture external training results
  $effect(() => {
    if (nanobot.trainingType === "lexicon_wrong" && nanobot.trainingResult) {
      newOverrideWrong = (
        Array.isArray(nanobot.trainingResult)
          ? nanobot.trainingResult[0]
          : nanobot.trainingResult
      ).toLowerCase();
      nanobot.cancelTraining();
    } else if (
      nanobot.trainingType === "lexicon_stop" &&
      nanobot.trainingResult
    ) {
      addStopword(
        (Array.isArray(nanobot.trainingResult)
          ? nanobot.trainingResult[0]
          : nanobot.trainingResult
        ).toLowerCase(),
      );
      nanobot.cancelTraining();
    }
  });
</script>

<div
  class="bg-black/40 backdrop-blur-md border border-white/10 rounded-[2.5rem] p-5 sm:p-8 flex flex-col shadow-2xl min-h-[420px] max-h-[600px] transition-all"
>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center flex-nowrap gap-4 w-full">
      <div
        class="flex p-1 bg-black/40 rounded-full border border-white/5 backdrop-blur-md flex-1 max-w-[240px] flex-shrink-0"
      >
        <button
          onclick={() => (lexiconTab = "overrides")}
          class="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-wider transition-all duration-300 {lexiconTab ===
          'overrides'
            ? 'bg-cyan-900/40 border border-cyan-500/30 text-cyan-400 shadow-[0_0_10px_rgba(8,145,178,0.2)]'
            : 'bg-transparent text-zinc-500 hover:text-zinc-300 hover:bg-white/5'}"
        >
          <Sparkles
            size={12}
            class={lexiconTab === "overrides"
              ? "text-cyan-400"
              : "text-zinc-600"}
          />
          <span class="truncate uppercase leading-none">NORMALIZE</span>
        </button>
        <button
          onclick={() => (lexiconTab = "stopwords")}
          class="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold tracking-wider transition-all duration-300 {lexiconTab ===
          'stopwords'
            ? 'bg-cyan-900/40 border border-cyan-500/30 text-cyan-400 shadow-[0_0_10px_rgba(8,145,178,0.2)]'
            : 'bg-transparent text-zinc-500 hover:text-zinc-300 hover:bg-white/5'}"
        >
          <Filter
            size={12}
            class={lexiconTab === "stopwords"
              ? "text-cyan-400"
              : "text-zinc-600"}
          />
          <span class="truncate uppercase leading-none">FILTER</span>
        </button>
      </div>
      <div class="flex-1"></div>
      <button
        onclick={() =>
          onStartTraining(
            lexiconTab === "overrides" ? "lexicon_wrong" : "lexicon_stop",
          )}
        class="p-3 rounded-2xl border border-emerald-500/20 text-emerald-500/40 hover:text-emerald-400 hover:bg-emerald-500/5 transition-all duration-300 flex-shrink-0"
      >
        <RefreshCw size={18} />
      </button>
    </div>
  </div>

  <div class="flex-1 overflow-y-auto custom-scrollbar pr-3 space-y-4">
    {#if lexiconTab === "overrides"}
      <div class="space-y-3">
        {#each Object.entries(sttOverrides) as [wrong, right]}
          <div
            class="group relative p-2.5 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl flex items-center justify-between transition-all duration-300 overflow-hidden"
          >
            <div class="flex items-center gap-4 min-w-0 mr-2">
              <button
                onclick={() => {
                  editingOverride = wrong;
                  editingOverrideField = "wrong";
                }}
                class="text-[10px] font-mono font-bold text-zinc-400 hover:text-zinc-200 truncate max-w-[120px]"
              >
                {#if editingOverride === wrong && editingOverrideField === "wrong"}
                  <input
                    value={wrong}
                    onfocusout={(e) =>
                      updateOverride(wrong, "wrong", e.currentTarget.value)}
                    onkeydown={(e) =>
                      e.key === "Enter" &&
                      updateOverride(wrong, "wrong", e.currentTarget.value)}
                    class="bg-transparent outline-none border-b border-emerald-500/40 w-full"
                    autofocus
                  />
                {:else}
                  {wrong}
                {/if}
              </button>
              <div class="w-8 h-px bg-zinc-800 flex-shrink-0"></div>
              <button
                onclick={() => {
                  editingOverride = wrong;
                  editingOverrideField = "right";
                }}
                class="text-[10px] font-mono font-bold text-emerald-400 hover:text-emerald-300 truncate max-w-[120px]"
              >
                {#if editingOverride === wrong && editingOverrideField === "right"}
                  <input
                    value={right}
                    onfocusout={(e) =>
                      updateOverride(wrong, "right", e.currentTarget.value)}
                    onkeydown={(e) =>
                      e.key === "Enter" &&
                      updateOverride(wrong, "right", e.currentTarget.value)}
                    class="bg-transparent outline-none border-b border-emerald-500/40 w-full"
                    autofocus
                  />
                {:else}
                  {right}
                {/if}
              </button>
            </div>
            <button
              onclick={() => deleteOverride(wrong)}
              class="opacity-0 group-hover:opacity-100 text-zinc-700 hover:text-red-400 transition-all flex-shrink-0"
            >
              <Trash2 size={12} />
            </button>
          </div>
        {/each}
        <div
          class="p-2.5 bg-black/20 border border-dashed border-white/5 rounded-xl flex items-center justify-between group/add mt-2"
        >
          <div class="flex items-center gap-4">
            <input
              bind:value={newOverrideWrong}
              placeholder="ERR..."
              class="w-20 bg-transparent text-[10px] font-mono text-zinc-500 placeholder:text-zinc-800 focus:text-zinc-300 outline-none"
            />
            <div class="text-zinc-800">➔</div>
            <input
              bind:value={newOverrideRight}
              placeholder="CORRECT"
              class="w-24 bg-transparent text-[10px] font-mono text-emerald-500 placeholder:text-emerald-900/30 focus:text-emerald-400 outline-none"
            />
          </div>
          <button
            onclick={addOverride}
            class="p-2 rounded-xl text-emerald-500/40 group-hover/add:text-emerald-500 hover:bg-emerald-500/10 transition-all"
          >
            <Plus size={18} />
          </button>
        </div>
      </div>
    {:else}
      <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-2">
        {#each sttStopwords as word, i}
          <div
            class="group relative h-8 px-3 bg-zinc-900/60 border border-white/5 rounded-lg flex items-center justify-center hover:bg-zinc-800 transition-all ring-1 ring-white/5 hover:ring-emerald-500/20 shadow-lg animate-in overflow-hidden"
          >
            {#if editingStopword === i}
              <input
                bind:value={sttStopwords[i]}
                onfocusout={() => updateStopword(i, word)}
                onkeydown={(e) => e.key === "Enter" && updateStopword(i, word)}
                class="bg-transparent outline-none text-[10px] font-mono text-emerald-400 w-full min-w-[3rem]"
                autofocus
              />
            {:else}
              <button
                onclick={() => (editingStopword = i)}
                class="text-[10px] font-mono font-bold text-zinc-400 truncate w-full text-center"
                >{word}</button
              >
            {/if}
            <button
              onclick={() => deleteStopword(word)}
              class="absolute right-1 opacity-0 group-hover:opacity-100 text-zinc-700 hover:text-red-400 transition-all bg-zinc-950/80 rounded p-0.5"
            >
              <Trash2 size={10} />
            </button>
          </div>
        {/each}
        <div
          class="flex items-center px-3 py-1.5 bg-black/20 border border-dashed border-white/5 rounded-full transition-all hover:border-emerald-500/20 group/add"
        >
          <input
            bind:value={newStopword}
            placeholder="ADD FILTER..."
            class="w-24 bg-transparent text-[10px] font-mono text-zinc-500 placeholder:text-zinc-800 focus:text-zinc-300 outline-none"
            onkeydown={(e) => e.key === "Enter" && addStopword()}
          />
          <button
            onclick={() => addStopword()}
            class="ml-2 text-zinc-800 group-hover/add:text-emerald-500"
          >
            <Plus size={14} />
          </button>
        </div>
        {#if sttStopwords.length < 5}
          <button
            onclick={ingestDefaultStopwords}
            disabled={isIngesting}
            class="w-full mt-4 p-4 bg-emerald-600/10 border border-emerald-500/20 rounded-2xl text-emerald-400 font-bold text-[10px] uppercase tracking-[0.3em] hover:bg-emerald-500/20 transition-all flex items-center justify-center gap-3 active:scale-[0.98]"
          >
            <RefreshCw size={16} class={isIngesting ? "animate-spin" : ""} />
            {isIngesting
              ? "Hydrating Cognitive Matrix..."
              : "Sync Neural Lexicon"}
          </button>
        {/if}
      </div>
    {/if}
  </div>
</div>
