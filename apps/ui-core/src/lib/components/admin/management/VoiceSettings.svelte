<script lang="ts">
  import { onMount, untrack } from "svelte";
  import { fade, scale } from "svelte/transition";
  import { apiClient } from "$lib/utils/apiClient";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { omni } from "$lib/state/omni.svelte";

  import Mic from "lucide-svelte/icons/mic";
  import Moon from "lucide-svelte/icons/moon";
  import MessageSquare from "lucide-svelte/icons/message-square";
  import Save from "lucide-svelte/icons/save";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import Brain from "lucide-svelte/icons/brain";
  import ShieldAlert from "lucide-svelte/icons/shield-alert";
  import BookOpen from "lucide-svelte/icons/book-open";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Plus from "lucide-svelte/icons/plus";
  import Zap from "lucide-svelte/icons/zap";
  import LayoutDashboard from "lucide-svelte/icons/layout-dashboard";

  let wakeTriggers = $state<string[]>([]);
  let sleepTriggers = $state<string[]>([]);
  let greetingTemplate = $state("");
  let farewellTemplate = $state("");
  let isLoading = $state(true);
  let isSaving = $state(false);
  let editingWake = $state<number | null>(null);
  let editingSleep = $state<number | null>(null);
  let isCampaignMode = $state(false);
  let isTogglingCampaign = $state(false);

  // Lexicon State
  let sttOverrides = $state<Record<string, string>>({});
  let sttStopwords = $state<string[]>([]);
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

  // UI Tabs State
  type MainTab = "core" | "brain" | "lexicon" | "ops";
  let activeTab = $state<MainTab>("core");

  function switchTab(id: string) {
    activeTab = id as MainTab;
  }

  async function toggleCampaignMode() {
    isTogglingCampaign = true;
    try {
      const newVal = !isCampaignMode;
      const res = await apiClient.post<any>("/api/v1/settings/campaign-mode", {
        is_campaign_mode: newVal,
      });
      if (res && res.status === "success") {
        isCampaignMode = newVal;
        nanobot.addLog(
          "Fortress Mode: " + (newVal ? "ENGAGED" : "STANDBY"),
          "SYS",
          newVal ? "warning" : "success",
        );
        nanobot.showToast(res.message, "success");
      }
    } catch (e: any) {
      nanobot.showToast("Failed to toggle Campaign Mode", "error");
    } finally {
      isTogglingCampaign = false;
    }
  }

  // V44.0 Voice Onboarding State
  let capturedText = $derived(
    (nanobot.voice.vuiUserQuery || omni.liveTrans || "").toLowerCase(),
  );

  // V44.2 Training Handshake
  $effect(() => {
    const result = nanobot.trainingResult;
    const type = nanobot.trainingType;
    if (!result) return;

    untrack(() => {
      const results = (Array.isArray(result) ? result : [result]).map((r) =>
        r.toLowerCase(),
      );
      if (type === "wake") {
        wakeTriggers = [...new Set([...wakeTriggers, ...results])];
      } else if (type === "sleep") {
        sleepTriggers = [...new Set([...sleepTriggers, ...results])];
      } else if (type === "lexicon_wrong") {
        if (results.length > 0) newOverrideWrong = results[0];
      } else if (type === "lexicon_stop") {
        if (results.length > 0) {
          addStopword(results[0]);
        }
      }

      nanobot.addLog(
        type.startsWith("lexicon")
          ? `Lexicon Capture: ${results.join(", ")}`
          : `Neural Link Established: ${results.length} phrase(s)`,
        "SYS",
        "success",
      );
      nanobot.cancelTraining();
    });
  });

  // V40.0 Cognitive State (Dynamic from Backend)
  let capabilities = $state<any[]>([]);

  function startTraining(
    type: "wake" | "sleep" | "lexicon_wrong" | "lexicon_stop",
  ) {
    nanobot.voice.clearVuiResponse();
    nanobot.setTraining(true, type);
    nanobot.setModality("voice");
    omni.startTrainingRec();
    nanobot.addLog(`Initializing Neural Capture: ${type.toUpperCase()}`, "SYS");
  }

  function cancelTraining() {
    nanobot.setTraining(false, null);
    nanobot.voice.clearVuiResponse();
  }

  function confirmTraining() {
    if (!capturedText) return;
    const lowerText = capturedText.toLowerCase();
    if (nanobot.trainingType === "wake") {
      wakeTriggers = [...new Set([...wakeTriggers, lowerText])];
    } else if (nanobot.trainingType === "sleep") {
      sleepTriggers = [...new Set([...sleepTriggers, lowerText])];
    } else if (nanobot.trainingType === "lexicon_wrong") {
      newOverrideWrong = lowerText;
    } else if (nanobot.trainingType === "lexicon_stop") {
      newStopword = lowerText;
    }
    cancelTraining();
    nanobot.addLog(`Neural Link Established: ${lowerText}`, "SYS", "success");
  }

  // Fetch current settings
  onMount(async () => {
    try {
      const campRes = await apiClient
        .get<any>("/api/v1/settings/campaign-mode")
        .catch(() => null);
      if (campRes && campRes.is_campaign_mode !== undefined) {
        isCampaignMode = campRes.is_campaign_mode;
      }

      const res = await apiClient
        .get<any>("/api/v1/settings/voice")
        .catch(() => null);
      if (res) {
        wakeTriggers = res.wake_words || ["xohi", "oi xohi"];
        sleepTriggers = res.sleep_words || ["tam biet", "ngu di"];
        greetingTemplate =
          res.greeting_template ||
          "Hệ thống Xohi đã sẵn sàng. Em đang nghe đây sếp.";
        farewellTemplate =
          res.farewell_template ||
          "Xohi chuyển sang trạng thái chờ. Hẹn gặp lại sếp sau.";
        capabilities = res.capabilities || [];
      } else {
        wakeTriggers = ["xohi", "hey xohi"];
        sleepTriggers = ["tạm biệt", "ngủ đi"];
        greetingTemplate = "Hệ thống Xohi đã sẵn sàng. Em đang nghe đây sếp.";
        farewellTemplate =
          "Xohi chuyển sang trạng thái chờ. Hẹn gặp lại sếp sau.";
      }

      const lexOverRes = await apiClient
        .get<any>("/api/v1/settings/lexicon/overrides")
        .catch(() => null);
      if (lexOverRes && lexOverRes.overrides) {
        sttOverrides = lexOverRes.overrides;
      }

      const lexStopRes = await apiClient
        .get<any>("/api/v1/settings/lexicon/stopwords")
        .catch(() => null);
      if (lexStopRes && lexStopRes.stopwords) {
        sttStopwords = lexStopRes.stopwords.filter(
          (w: string) => w && w.trim(),
        );
      }
    } finally {
      isLoading = false;
    }
  });

  async function saveSettings() {
    isSaving = true;
    try {
      const capMap = capabilities.reduce(
        (acc, c) => ({ ...acc, [c.id]: c.active }),
        {},
      );

      const res = await apiClient.post<{
        status: string;
        data: {
          wake_words?: string[];
          sleep_words?: string[];
        };
      }>("/api/v1/settings/voice", {
        wake_words: wakeTriggers,
        sleep_words: sleepTriggers,
        greeting_template: greetingTemplate,
        capabilities: capMap,
      });

      if (res && res.status === "success" && res.data) {
        if (res.data.wake_words) wakeTriggers = res.data.wake_words;
        if (res.data.sleep_words) sleepTriggers = res.data.sleep_words;
        nanobot.updateVoiceSettings(
          wakeTriggers,
          sleepTriggers,
          greetingTemplate,
          farewellTemplate,
        );
      }

      nanobot.addLog(
        "Agent Capabilities Synchronized",
        "Nanobot-Core",
        "success",
      );
      nanobot.showToast("Cognitive Matrix committed successfully.", "success");
    } catch (e: any) {
      nanobot.addLog(`Sync Failed: ${e.message}`, "Nanobot-Core", "error");
      nanobot.showToast("Failed to synchronize. See Neural Logs.", "error");
    } finally {
      isSaving = false;
    }
  }

  function addWakeWord() {
    wakeTriggers = [...wakeTriggers, ""];
  }
  function addSleepWord() {
    sleepTriggers = [...sleepTriggers, ""];
  }
  function removeWakeWord(index: number) {
    wakeTriggers = wakeTriggers.filter((_, i) => i !== index);
  }
  function removeSleepWord(index: number) {
    sleepTriggers = sleepTriggers.filter((_, i) => i !== index);
  }
  function toggleCapability(id: string) {
    const cap = capabilities.find((c) => c.id === id);
    if (cap) cap.active = !cap.active;
  }

  // Lexicon CRUD
  async function addOverride() {
    const wrong = newOverrideWrong.trim().toLowerCase();
    const right = newOverrideRight.trim().toLowerCase();
    if (!wrong || !right) return;

    // Optimistic UI
    const snapshot = { ...sttOverrides };
    sttOverrides = { ...sttOverrides, [wrong]: right };
    newOverrideWrong = "";
    newOverrideRight = "";

    try {
      await apiClient.post<any>("/api/v1/settings/lexicon/overrides", {
        wrong_word: wrong,
        right_word: right,
      });
      nanobot.showToast(`Đã thêm luật: ${wrong} ➔ ${right}`, "success");
    } catch (e: any) {
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
      await apiClient.delete<any>(
        `/api/v1/settings/lexicon/overrides/${encodeURIComponent(wrong)}`,
      );
      nanobot.showToast(`Đã xoá luật: ${wrong}`, "success");
    } catch (e: any) {
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
      await apiClient.post<any>("/api/v1/settings/lexicon/stopwords", { word });
      nanobot.showToast(`Đã thêm từ dư thừa: ${word}`, "success");
    } catch (e: any) {
      sttStopwords = snapshot;
      nanobot.showToast("Lỗi khi thêm từ dư thừa.", "error");
    }
  }

  async function deleteStopword(word: string) {
    const snapshot = [...sttStopwords];
    sttStopwords = sttStopwords.filter((w) => w !== word);

    try {
      await apiClient.delete<any>(
        `/api/v1/settings/lexicon/stopwords/${encodeURIComponent(word)}`,
      );
      nanobot.showToast(`Đã xoá từ dư thừa: ${word}`, "success");
    } catch (e: any) {
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
          // Small delay to prevent burst issues if any
          await new Promise((r) => setTimeout(r, 50));
        }
      }
      nanobot.addLog(
        `Neural Matrix Ingested: ${addedCount} units.`,
        "SYS",
        "success",
      );
      nanobot.showToast(`Đã nạp ${addedCount} từ vào hệ thống.`, "success");
    } catch (e: any) {
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
      // Delete old, add new (Lexicon API doesn't have PUT for single word)
      await apiClient.delete(
        `/api/v1/settings/lexicon/stopwords/${encodeURIComponent(oldWord)}`,
      );
      await apiClient.post("/api/v1/settings/lexicon/stopwords", {
        word: newWord,
      });
      editingStopword = null;
      nanobot.showToast(`Cập nhật: ${oldWord} ➔ ${newWord}`, "success");
    } catch (e) {
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
        // Swap keys: delete old, add new with current right
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
        // Update value for existing key
        await apiClient.post("/api/v1/settings/lexicon/overrides", {
          wrong_word: oldWrong,
          right_word: newVal,
        });
        sttOverrides[oldWrong] = newVal;
      }

      editingOverride = null;
      nanobot.showToast("Cập nhật nắn lỗi thành công", "success");
    } catch (e) {
      editingOverride = null;
      nanobot.showToast("Lỗi khi cập nhật nắn lỗi", "error");
    }
  }
</script>

<div
  class="w-full h-full flex flex-col bg-[#050505] text-white selection:bg-cyan-500/30"
>
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-6">
      <div class="relative">
        <div
          class="w-20 h-20 border-2 border-cyan-500/5 border-t-cyan-400 rounded-full animate-spin"
        ></div>
        <div
          class="absolute inset-0 m-auto w-12 h-12 border border-cyan-500/10 border-b-cyan-500 rounded-full animate-spin [animation-direction:reverse]"
        ></div>
      </div>
      <div class="flex flex-col items-center gap-1">
        <h2
          class="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-[0.5em] animate-pulse"
        >
          Initializing Neuro-Link
        </h2>
        <p class="text-[9px] font-mono text-gray-700 uppercase tracking-widest">
          Bridging Cognitive Matrix...
        </p>
      </div>
    </div>
  {:else}
    <!-- HUD HEADER -->
    <header
      class="h-20 border-b border-white/5 bg-black/40 backdrop-blur-3xl flex items-center justify-between px-10 z-50 sticky top-0"
    >
      <div class="flex items-center gap-6">
        <div class="flex flex-col">
          <div class="flex items-center gap-2">
            <div
              class="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-[pulse_2s_infinite] shadow-[0_0_10px_rgba(0,255,255,0.5)]"
            ></div>
            <span
              class="text-[10px] font-mono font-bold text-gray-500 uppercase tracking-[0.3em]"
              >XoHi Nerve Center</span
            >
          </div>
          <h1
            class="text-xl font-bold tracking-tighter text-white/90 uppercase"
          >
            V56.0 Agent Cockpit
          </h1>
        </div>
        <div class="h-8 w-px bg-white/5"></div>
        <div class="flex items-center gap-3">
          <div class="flex flex-col">
            <span class="text-[9px] font-mono text-gray-600 uppercase"
              >Latency</span
            >
            <span class="text-xs font-mono text-emerald-400">12ms</span>
          </div>
          <div class="flex flex-col">
            <span class="text-[9px] font-mono text-gray-600 uppercase"
              >Sync</span
            >
            <div
              class="flex items-center gap-1.5 px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full"
            >
              <div
                class="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.5)]"
              ></div>
              <span
                class="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-widest leading-none"
                >Nominal</span
              >
            </div>
          </div>
        </div>
      </div>

      <!-- MASTER NEURAL LINK BUTTON -->
      <div class="flex items-center gap-4">
        <div class="flex flex-col items-end mr-2">
          <span class="text-[9px] font-mono text-gray-600 uppercase"
            >System Identity</span
          >
          <span class="text-xs font-mono text-white/40"
            >{greetingTemplate.slice(0, 20)}...</span
          >
        </div>
        <button
          onclick={saveSettings}
          disabled={isSaving}
          class="group relative h-12 px-8 bg-cyan-500/10 border border-cyan-500/30 rounded-2xl flex items-center gap-3 transition-all hover:bg-cyan-500/20 hover:border-cyan-400 shadow-[0_0_30px_rgba(0,255,255,0.05)] disabled:opacity-50"
        >
          {#if isSaving}
            <RefreshCw size={14} class="animate-spin text-cyan-400" />
            <span
              class="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-widest"
              >Syncing</span
            >
          {:else}
            <Save
              size={14}
              class="text-cyan-400 group-hover:scale-110 transition-transform"
            />
            <span
              class="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-widest"
              >Commit Matrix</span
            >
          {/if}
          <div
            class="absolute inset-0 bg-cyan-400/5 opacity-0 group-hover:opacity-100 blur-xl transition-opacity"
          ></div>
        </button>
      </div>
    </header>

    <main class="flex-1 flex overflow-hidden">
      <!-- LEFT PANE: COGNITIVE AUGMENTATION -->
      <aside
        class="w-80 border-r border-white/5 bg-black/20 overflow-y-auto custom-scrollbar flex flex-col p-8 gap-10"
      >
        <div>
          <div class="flex items-center gap-3 text-amber-500 mb-6">
            <Brain size={18} />
            <h2 class="text-xs font-mono font-bold uppercase tracking-[0.2em]">
              Neural Modules
            </h2>
          </div>
          <div class="space-y-4">
            {#each capabilities as cap}
              <button
                onclick={() => toggleCapability(cap.id)}
                class="w-full group p-4 bg-white/[0.02] border {cap.active
                  ? 'border-amber-500/30 shadow-[0_0_20px_rgba(245,158,11,0.03)]'
                  : 'border-white/5'} rounded-2xl text-left transition-all hover:bg-white/[0.04]"
              >
                <div class="flex items-center justify-between mb-2">
                  <span
                    class="text-[9px] font-mono font-bold {cap.active
                      ? 'text-amber-400'
                      : 'text-gray-600'} uppercase tracking-widest"
                    >{cap.id}</span
                  >
                  <div
                    class="w-1.5 h-1.5 rounded-full {cap.active
                      ? 'bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(245,158,11,0.5)]'
                      : 'bg-gray-800'}"
                  ></div>
                </div>
                <h3
                  class="text-sm font-bold text-white/80 mb-1 leading-none uppercase tracking-tight group-hover:text-white transition-colors"
                >
                  {cap.name}
                </h3>
                <p
                  class="text-[9px] font-mono text-gray-600 leading-tight line-clamp-2"
                >
                  {cap.desc}
                </p>
              </button>
            {/each}
          </div>
        </div>

        <div class="mt-auto">
          <div class="flex items-center gap-3 text-red-500/70 mb-6">
            <ShieldAlert size={18} />
            <h2 class="text-xs font-mono font-bold uppercase tracking-[0.2em]">
              Security Grid
            </h2>
          </div>
          <button
            onclick={toggleCampaignMode}
            disabled={isTogglingCampaign}
            class="w-full p-5 rounded-3xl border transition-all flex flex-col gap-3 {isCampaignMode
              ? 'bg-red-500/10 border-red-500/30 shadow-[0_0_25px_rgba(239,68,68,0.1)]'
              : 'bg-white/2 border-white/5 opacity-60 hover:opacity-100 hover:bg-white/5'}"
          >
            <div class="flex items-center justify-between">
              <span
                class="text-[10px] font-mono font-bold {isCampaignMode
                  ? 'text-red-400'
                  : 'text-gray-600'} uppercase tracking-widest"
                >Fortress Mode</span
              >
              {#if isTogglingCampaign}
                <RefreshCw size={12} class="animate-spin text-red-400" />
              {:else}
                <div
                  class="w-8 h-4 bg-black/40 rounded-full border border-white/10 relative"
                >
                  <div
                    class="absolute top-0.5 bottom-0.5 w-3 h-3 rounded-full transition-all duration-300 {isCampaignMode
                      ? 'bg-red-500 left-4'
                      : 'bg-gray-700 left-0.5'}"
                  ></div>
                </div>
              {/if}
            </div>
            <p
              class="text-[9px] font-mono text-gray-500 uppercase leading-none tracking-tight"
            >
              Anti-Spam Shield Activation
            </p>
          </button>
        </div>
      </aside>

      <!-- CENTER HUB: NEURAL LINGUISTIC PROCESSING -->
      <section
        class="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.03),transparent_70%)] p-5 md:p-7 xl:p-8"
      >
        <div class="max-w-6xl mx-auto space-y-10 md:space-y-12">
          <!-- DATA MATRIX GRID -->
          <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <!-- LINGUISTIC FREQUENCIES (Wake/Sleep) -->
            <div
              class="bg-white/[0.01] border border-white/5 rounded-[40px] p-6 md:p-7 xl:p-8 flex flex-col max-h-[600px] min-h-[100px]"
            >
              <div class="flex items-center justify-between mb-8 flex-shrink-0">
                <div class="flex items-center gap-3 text-cyan-400">
                  <Mic size={20} />
                  <h2
                    class="text-sm font-mono font-bold uppercase tracking-widest"
                  >
                    Core Triggers
                  </h2>
                </div>
                <div
                  class="px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-lg"
                >
                  <span
                    class="text-[9px] font-mono text-cyan-400 font-bold uppercase"
                    >System Tier 1</span
                  >
                </div>
              </div>

              <div
                class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-8"
              >
                <div class="space-y-4">
                  <div class="flex items-center gap-3">
                    <div class="w-1 h-1 rounded-full bg-cyan-500/40"></div>
                    <span
                      class="text-[10px] font-mono text-gray-600 uppercase tracking-widest"
                      >Wake Triggers (Activation)</span
                    >
                    <button
                      onclick={() => startTraining("wake")}
                      class="p-1.5 rounded-lg border border-cyan-500/20 text-cyan-500/40 hover:text-cyan-400 hover:bg-cyan-500/5 transition-all ml-2 {nanobot.isTraining &&
                      nanobot.trainingType === 'wake'
                        ? 'bg-cyan-500/10 text-cyan-400 animate-pulse'
                        : ''}"
                      title="Train Wake Triggers"
                    >
                      <Mic size={10} />
                    </button>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each wakeTriggers as word, i}
                      <div
                        class="min-h-[38px] px-4 bg-cyan-500/5 border border-cyan-500/10 rounded-xl flex items-center gap-3 transition-all hover:border-cyan-500/40 group/chip"
                        transition:scale={{ duration: 200, start: 0.9 }}
                      >
                        {#if editingWake === i}
                          <input
                            bind:value={wakeTriggers[i]}
                            onblur={() => (editingWake = null)}
                            onkeydown={(e) =>
                              e.key === "Enter" && (editingWake = null)}
                            class="bg-transparent outline-none text-[11px] font-mono text-white/90 w-20 border-b border-cyan-500/30"
                            autofocus
                          />
                        {:else}
                          <button
                            onclick={() => (editingWake = i)}
                            class="text-[11px] font-mono text-cyan-100/80 hover:text-cyan-400 transition-colors tracking-wide leading-none"
                            >{word || "empty"}</button
                          >
                        {/if}
                        <button
                          onclick={() => removeWakeWord(i)}
                          class="text-white/10 hover:text-red-400 transition-colors text-xs"
                          >&times;</button
                        >
                      </div>
                    {/each}
                    <button
                      onclick={addWakeWord}
                      class="w-10 h-10 border border-dashed border-white/10 rounded-xl flex items-center justify-center text-gray-700 hover:text-cyan-400 hover:border-cyan-400/40 transition-all"
                      >+</button
                    >
                  </div>
                </div>

                <div class="space-y-4">
                  <div class="flex items-center gap-3">
                    <div class="w-1 h-1 rounded-full bg-red-500/40"></div>
                    <span
                      class="text-[10px] font-mono text-gray-600 uppercase tracking-widest"
                      >Termination Protocols (Sleep)</span
                    >
                    <button
                      onclick={() => startTraining("sleep")}
                      class="p-1.5 rounded-lg border border-red-500/20 text-red-500/40 hover:text-red-400 hover:bg-red-500/5 transition-all ml-2 {nanobot.isTraining &&
                      nanobot.trainingType === 'sleep'
                        ? 'bg-red-500/10 text-red-400 animate-pulse'
                        : ''}"
                      title="Train Sleep Triggers"
                    >
                      <Mic size={10} />
                    </button>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    {#each sleepTriggers as word, i}
                      <div
                        class="min-h-[38px] px-4 bg-red-500/5 border border-red-500/10 rounded-xl flex items-center gap-3 transition-all hover:border-red-500/40 group/chip"
                        transition:scale={{ duration: 200, start: 0.9 }}
                      >
                        {#if editingSleep === i}
                          <input
                            bind:value={sleepTriggers[i]}
                            onblur={() => (editingSleep = null)}
                            onkeydown={(e) =>
                              e.key === "Enter" && (editingSleep = null)}
                            class="bg-transparent outline-none text-[11px] font-mono text-white/90 w-20 border-b border-red-500/30"
                            autofocus
                          />
                        {:else}
                          <button
                            onclick={() => (editingSleep = i)}
                            class="text-[11px] font-mono text-white/70 hover:text-red-400 transition-colors tracking-wide leading-none"
                            >{word || "empty"}</button
                          >
                        {/if}
                        <button
                          onclick={() => removeSleepWord(i)}
                          class="text-white/10 hover:text-red-400 transition-colors"
                          ><Trash2 size={11} /></button
                        >
                      </div>
                    {/each}
                    <button
                      onclick={addSleepWord}
                      class="w-10 h-10 border border-dashed border-white/10 rounded-xl flex items-center justify-center text-gray-700 hover:text-red-400 hover:border-red-400/40 transition-all"
                      >+</button
                    >
                  </div>
                </div>
              </div>
            </div>

            <!-- LEXICON INTELLIGENCE (Overrides / Stopwords) -->
            <div
              class="bg-white/[0.01] border border-white/5 rounded-[40px] p-6 md:p-7 xl:p-8 flex flex-col max-h-[600px] min-h-[100px]"
            >
              <div class="flex items-center gap-3">
                <div
                  class="flex bg-white/5 p-1 rounded-xl border border-white/5"
                >
                  <button
                    onclick={() => (lexiconTab = "overrides")}
                    class="px-4 py-2 rounded-lg text-[10px] font-mono font-bold uppercase tracking-wider transition-all {lexiconTab ===
                    'overrides'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 shadow-lg'
                      : 'text-gray-600 hover:text-white'}"
                  >
                    Normalization
                  </button>
                  <button
                    onclick={() => (lexiconTab = "stopwords")}
                    class="px-4 py-2 rounded-lg text-[10px] font-mono font-bold uppercase tracking-wider transition-all {lexiconTab ===
                    'stopwords'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 shadow-lg'
                      : 'text-gray-600 hover:text-white'}"
                  >
                    Filtration
                  </button>
                </div>
                <button
                  onclick={() =>
                    startTraining(
                      lexiconTab === "overrides"
                        ? "lexicon_wrong"
                        : "stopwords",
                    )}
                  class="p-2 rounded-xl border border-emerald-500/20 text-emerald-500/40 hover:text-emerald-400 hover:bg-emerald-500/5 transition-all ml-4 {nanobot.isTraining &&
                  (nanobot.trainingType === 'lexicon_wrong' ||
                    nanobot.trainingType === 'stopwords')
                    ? 'bg-emerald-500/10 text-emerald-400 animate-pulse'
                    : ''}"
                  title="Train Lexicon Intelligence"
                >
                  <Mic size={12} />
                </button>
              </div>

              <div class="flex-1 overflow-y-auto custom-scrollbar pr-2">
                {#if lexiconTab === "overrides"}
                  <div class="flex flex-wrap gap-2">
                    {#each Object.entries(sttOverrides) as [wrong, right]}
                      <div
                        class="group relative min-h-[38px] px-4 bg-emerald-500/5 border border-emerald-500/10 rounded-xl flex items-center gap-3 transition-all hover:border-emerald-500/40 shadow-sm"
                      >
                        <div class="flex items-center gap-2">
                          {#if editingOverride === wrong && editingOverrideField === "wrong"}
                            <input
                              value={wrong}
                              onfocusout={(e) =>
                                updateOverride(
                                  wrong,
                                  "wrong",
                                  e.currentTarget.value,
                                )}
                              onkeydown={(e) =>
                                e.key === "Enter" &&
                                updateOverride(
                                  wrong,
                                  "wrong",
                                  e.currentTarget.value,
                                )}
                              class="bg-transparent outline-none text-[11px] font-mono text-white/50 w-20 border-b border-emerald-500/40"
                              autofocus
                            />
                          {:else}
                            <button
                              type="button"
                              onclick={() => {
                                editingOverride = wrong;
                                editingOverrideField = "wrong";
                              }}
                              class="text-[11px] font-mono text-white/40 hover:text-white transition-colors"
                              >{wrong}</button
                            >
                          {/if}

                          <span
                            class="text-[10px] text-emerald-500/30 font-mono"
                            >➔</span
                          >

                          {#if editingOverride === wrong && editingOverrideField === "right"}
                            <input
                              value={right}
                              onfocusout={(e) =>
                                updateOverride(
                                  wrong,
                                  "right",
                                  e.currentTarget.value,
                                )}
                              onkeydown={(e) =>
                                e.key === "Enter" &&
                                updateOverride(
                                  wrong,
                                  "right",
                                  e.currentTarget.value,
                                )}
                              class="bg-transparent outline-none text-[12px] font-mono text-emerald-400 w-20 border-b border-emerald-500/40"
                              autofocus
                            />
                          {:else}
                            <button
                              type="button"
                              onclick={() => {
                                editingOverride = wrong;
                                editingOverrideField = "right";
                              }}
                              class="text-[12px] font-mono text-emerald-400 font-bold hover:text-emerald-300 transition-colors"
                              >{right}</button
                            >
                          {/if}
                        </div>
                        <button
                          type="button"
                          onclick={() => deleteOverride(wrong)}
                          class="text-white/10 hover:text-red-400 transition-colors"
                          ><Trash2 size={11} /></button
                        >
                      </div>
                    {/each}

                    <div
                      class="min-h-[38px] px-4 border border-dashed border-white/10 rounded-xl flex items-center gap-3 bg-white/[0.01]"
                    >
                      <input
                        bind:value={newOverrideWrong}
                        placeholder="STT..."
                        class="w-12 bg-transparent border-none outline-none text-[10px] font-mono text-white/40 placeholder:text-gray-800"
                      />
                      <span class="text-[10px] text-gray-800">➔</span>
                      <input
                        bind:value={newOverrideRight}
                        placeholder="Fix..."
                        class="w-12 bg-transparent border-none outline-none text-[10px] font-mono text-emerald-400/60 placeholder:text-emerald-900/10"
                      />
                      <button
                        onclick={addOverride}
                        class="text-emerald-400/40 hover:text-emerald-400 transition-colors"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                {:else}
                  <div class="flex flex-wrap gap-2">
                    {#each sttStopwords as word, i}
                      <div
                        class="group px-4 py-2 bg-[#0a0a0a]/80 border border-emerald-500/10 rounded-2xl flex items-center gap-3 hover:border-emerald-500/40 transition-all shadow-lg"
                        transition:scale={{ duration: 200, start: 0.9 }}
                      >
                        {#if editingStopword === i}
                          <input
                            bind:value={sttStopwords[i]}
                            onfocusout={() => updateStopword(i, word)}
                            onkeydown={(e) =>
                              e.key === "Enter" && updateStopword(i, word)}
                            class="bg-transparent outline-none text-[11px] font-mono text-white/90 w-20 border-b border-emerald-500/40"
                            autofocus
                          />
                        {:else}
                          <button
                            type="button"
                            onclick={() => (editingStopword = i)}
                            class="text-[11px] font-mono text-white/80 font-bold hover:text-emerald-400 transition-colors"
                            >{word}</button
                          >
                        {/if}
                        <button
                          onclick={() => deleteStopword(word)}
                          class="text-gray-700 hover:text-red-400 transition-colors"
                          ><Trash2 size={12} /></button
                        >
                      </div>
                    {/each}
                    <div
                      class="min-h-[38px] px-4 border border-dashed border-white/10 rounded-xl flex items-center gap-3 bg-white/[0.01]"
                    >
                      <input
                        bind:value={newStopword}
                        placeholder="Filter..."
                        class="w-20 bg-transparent border-none outline-none text-[10px] font-mono text-white/40 placeholder:text-gray-800"
                        onkeydown={(e) => e.key === "Enter" && addStopword()}
                      />
                      <button
                        onclick={() => addStopword()}
                        class="text-emerald-400/40 hover:text-emerald-400 transition-colors"
                      >
                        <Plus size={14} />
                      </button>
                    </div>

                    {#if sttStopwords.length < 5}
                      <button
                        onclick={ingestDefaultStopwords}
                        disabled={isIngesting}
                        class="px-5 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400 hover:bg-emerald-500/20 transition-all flex items-center gap-2 group/sync"
                      >
                        <RefreshCw
                          size={14}
                          class={isIngesting
                            ? "animate-spin"
                            : "group-hover/sync:rotate-180 transition-transform duration-500"}
                        />
                        <span
                          class="text-[10px] font-mono font-bold uppercase tracking-widest"
                        >
                          {isIngesting ? "Ingesting..." : "Sync Brain Matrix"}
                        </span>
                      </button>
                    {/if}
                  </div>
                {/if}
              </div>
            </div>
          </div>

          <!-- NEURAL IDENTITY PROTOCOLS (Greeting & Farewell) -->
          <div class="pt-10 border-t border-white/5">
            <div class="flex items-center gap-3 text-purple-400 mb-8">
              <MessageSquare size={20} />
              <h2
                class="text-sm font-mono font-bold uppercase tracking-[0.2em]"
              >
                {lexiconTab === "overrides"
                  ? "Neural Identity Pulse"
                  : "Vocal Termination Protocol"}
              </h2>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl">
              <!-- GREETING -->
              <div class="space-y-4">
                <span
                  class="text-[9px] font-mono text-gray-600 uppercase tracking-widest px-1"
                  >Engagement Identity (Greeting)</span
                >
                <div class="relative group">
                  <div
                    class="absolute -inset-0.5 bg-purple-500/10 rounded-3xl blur opacity-0 group-hover:opacity-100 transition-opacity"
                  ></div>
                  <textarea
                    bind:value={greetingTemplate}
                    placeholder="Configuring acquisition identity..."
                    class="w-full relative h-36 bg-white/[0.01] border border-white/5 rounded-3xl p-8 text-sm font-mono text-white/70 outline-none focus:border-purple-500/30 transition-all custom-scrollbar"
                  ></textarea>
                  <div
                    class="absolute bottom-6 right-8 text-[8px] font-mono text-gray-800 uppercase tracking-widest"
                  >
                    Tier 4 Greeting
                  </div>
                </div>
              </div>

              <!-- FAREWELL -->
              <div class="space-y-4">
                <span
                  class="text-[9px] font-mono text-gray-600 uppercase tracking-widest px-1"
                  >Disengagement Identity (Farewell)</span
                >
                <div class="relative group">
                  <div
                    class="absolute -inset-0.5 bg-cyan-500/10 rounded-3xl blur opacity-0 group-hover:opacity-100 transition-opacity"
                  ></div>
                  <textarea
                    bind:value={farewellTemplate}
                    placeholder="Configuring termination identity..."
                    class="w-full relative h-36 bg-white/[0.01] border border-white/5 rounded-3xl p-8 text-sm font-mono text-white/70 outline-none focus:border-cyan-500/30 transition-all custom-scrollbar"
                  ></textarea>
                  <div
                    class="absolute bottom-6 right-8 text-[8px] font-mono text-gray-800 uppercase tracking-widest"
                  >
                    Tier 4 Farewell
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>

    <style>
      .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
      }
      .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 20px;
        border: 2px solid transparent;
        background-clip: content-box;
      }
      .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid transparent;
        background-clip: content-box;
      }

      /* Animations for Neural Pulse */
      @keyframes pulse {
        0% {
          transform: scale(1);
          opacity: 1;
        }
        50% {
          transform: scale(1.5);
          opacity: 0.5;
        }
        100% {
          transform: scale(1);
          opacity: 1;
        }
      }
    </style>
  {/if}
</div>
