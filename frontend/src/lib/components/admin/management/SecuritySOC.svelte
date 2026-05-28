<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX_ADMIN } from "$lib/core/constants/z_index_admin";
  import Shield from "@lucide/svelte/icons/shield";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Activity from "@lucide/svelte/icons/activity";
  import Lock from "@lucide/svelte/icons/lock";
  import Unlock from "@lucide/svelte/icons/unlock";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import Fingerprint from "@lucide/svelte/icons/fingerprint";
  import Search from "@lucide/svelte/icons/search";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Ban from "@lucide/svelte/icons/ban";
  import Eye from "@lucide/svelte/icons/eye";
  import Cpu from "@lucide/svelte/icons/cpu";
  import { fade, scale, fly } from "svelte/transition";

  // --- ELITE V2.2: Strict Identity Contracts ---
  interface AuditLog {
    timestamp: string;
    action: string;
    actor: string;
    ip: string;
    suspicious: boolean;
    ms?: number;
    risk_reason?: string;
    [key: string]: unknown;
  }

  interface SecurityDraft {
    id: string;
    requested_by_email: string;
    action_type: string;
    description: string;
    payload: Record<string, unknown>;
    created_at: string;
  }

  interface SecurityStats {
    is_read_only: boolean;
    ai_status: string;
    threat_level: string;
    active_keys: number;
  }

  const nanobot = useNanobot();

  interface ContainerInfo {
    name: string;
    id: string;
    state: string;
    status: string;
    image: string;
    cpu: string;
    mem_usage: string;
    mem_perc: string;
    pids: string;
  }

  // --- Reactive States (Runes) ---
  let drafts = $state<SecurityDraft[]>([]);
  let logs = $state<AuditLog[]>([]);
  let stats = $state<SecurityStats>({
    is_read_only: false,
    ai_status: "ACTIVE",
    threat_level: "LOW",
    active_keys: 0
  });
  let containers = $state<ContainerInfo[]>([]);
  let whitelistPhones = $state<string[]>([]);
  let newPhone = $state('');
  let phoneLoading = $state(false);
  
  let isLoading = $state<boolean>(true);
  let isActionLoading = $state<string | null>(null);
  let opLoading = $state<string | null>(null); // Name of container being operated on
  let searchTerm = $state<string>("");
  let filterLevel = $state<string>("ALL");
  let selectedLogs = $state<Set<number>>(new Set());
  let detailLog = $state<AuditLog | null>(null);

  // --- Derived Computations ---
  // Elite V2.2: Sort containers by RAM consumption descending so heavy containers are highlighted first
  let sortedContainers = $derived(
    [...containers].sort((a, b) => {
      const getVal = (c: ContainerInfo) => {
        const perc = parseFloat(c.mem_perc || '0');
        return isNaN(perc) ? 0 : perc;
      };
      return getVal(b) - getVal(a);
    })
  );

  let filteredLogs = $derived(
    logs.filter(l => {
      const matchesSearch = !searchTerm || 
        l.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
        l.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
        l.ip.includes(searchTerm);
      const matchesLevel = filterLevel === "ALL" || 
        (filterLevel === "SUSPICIOUS" && l.suspicious) ||
        (filterLevel === "CLEAN" && !l.suspicious);
      return matchesSearch && matchesLevel;
    })
  );

  // --- Operational Logic ---
  async function loadSOCData(): Promise<void> {
    isLoading = true;
    try {
      const t: number = Date.now();
      const [draftsRes, logsRes, statusRes, containersRes, phoneRes] = await Promise.all([
        apiClient.get<SecurityDraft[]>(`/api/v1/security/drafts?t=${t}`),
        apiClient.get<AuditLog[]>(`/api/v1/security/audit-logs?limit=100&t=${t}`),
        apiClient.get<SecurityStats>(`/api/v1/security/status?t=${t}`),
        apiClient.get<ContainerInfo[]>(`/api/v1/security/containers?t=${t}`),
        apiClient.get<string[]>(`/api/v1/security/whitelist/phones?t=${t}`)
      ]);

      // Robust extraction based on Elite apiClient V45 standards
      drafts = (draftsRes as any).data || draftsRes;
      logs = (logsRes as any).data || logsRes;
      const rawStats = (statusRes as any).data || statusRes;
      if (rawStats) {
        stats = { ...stats, ...rawStats };
      }
      containers = (containersRes as any).data || containersRes || [];
      whitelistPhones = (phoneRes as any).data || phoneRes || [];

      // [DEBUG LOG CONSOLE] Verification of live container resource data
      console.log("[SOC] Polled Containers Live Data:", containers);
    } catch (e) {
      console.error("[SOC] Load Critical Failure", e);
    } finally {
      isLoading = false;
    }
  }

  async function addPhone(): Promise<void> {
    if (!newPhone.trim()) return;
    phoneLoading = true;
    try {
      const res: any = await apiClient.post(`/api/v1/security/whitelist/phones`, {
        phone: newPhone.trim()
      });
      const data = res.data || res;
      if (data.success) {
        newPhone = '';
        nanobot.ui.showToast(data.message, "success");
        await loadSOCData();
      } else {
        nanobot.ui.showToast(data.message || "Lỗi thêm số", "error");
      }
    } catch (e) {
      nanobot.ui.showToast("Lỗi thêm số điện thoại", "error");
    } finally {
      phoneLoading = false;
    }
  }

  async function removePhone(phone: string): Promise<void> {
    const confirmed = await nanobot.ui.showConfirm({
      title: "GỠ WHITELIST SỐ ĐIỆN THOẠI",
      message: `Bạn có chắc chắn muốn gỡ số điện thoại ${phone} khỏi danh sách trắng không?`,
      confirmLabel: "XÁC NHẬN GỠ",
      cancelLabel: "HỦY"
    });
    if (!confirmed) return;
    try {
      const res: any = await apiClient.delete(`/api/v1/security/whitelist/phones/${phone}`);
      const data = res.data || res;
      if (data.success) {
        nanobot.ui.showToast(data.message, "success");
        await loadSOCData();
      } else {
        nanobot.ui.showToast(data.message || "Lỗi gỡ số", "error");
      }
    } catch (e) {
      nanobot.ui.showToast("Lỗi gỡ số điện thoại", "error");
    }
  }

  async function handleContainerAction(containerName: string, action: 'start' | 'stop' | 'restart'): Promise<void> {
    const actionLabel = action === 'start' ? 'BẬT (ENABLE)' : action === 'stop' ? 'TẮT (DISABLE)' : 'KHỞI ĐỘNG LẠI (RESTART)';
    const confirmed = await nanobot.ui.showConfirm({
      title: "CẢNH BÁO HỆ THỐNG SOC",
      message: `[SOC WARNING] Xác nhận thực hiện thao tác ${actionLabel} trên container ${containerName}?`,
      confirmLabel: "XÁC NHẬN CHẠY",
      cancelLabel: "QUAY LẠI"
    });
    if (!confirmed) return;
    
    opLoading = containerName;
    try {
      const res: any = await apiClient.post(`/api/v1/security/containers/action`, {
        container_name: containerName,
        action
      });
      const data = res.data || res;
      nanobot.ui.showToast(data.message || "Thao tác thành công", "success");
      await loadSOCData();
    } catch (e) {
      console.error("[SOC] Subprocess execution error", e);
      nanobot.ui.showToast("Lỗi gửi lệnh điều khiển container", "error");
    } finally {
      opLoading = null;
    }
  }

  function toggleSelectAll(): void {
    if (selectedLogs.size === filteredLogs.length) {
      selectedLogs = new Set();
    } else {
      selectedLogs = new Set(filteredLogs.map((_, i) => i));
    }
  }

  function toggleSelect(index: number): void {
    const newSet = new Set(selectedLogs);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    selectedLogs = newSet;
  }

  async function bulkAction(type: 'BLACKLIST' | 'REVOKE'): Promise<void> {
    const targets: string[] = Array.from(selectedLogs).map(idx => 
      type === 'BLACKLIST' ? filteredLogs[idx].ip : filteredLogs[idx].actor
    );
    
    if (targets.length === 0) return;

    try {
      nanobot.ui.showToast(`Đang thực hiện ${type} cho ${targets.length} mục tiêu...`, "warning");
      await apiClient.post("/api/v1/security/bulk-action", {
        action: type,
        targets: targets
      });
      nanobot.ui.showToast("Chiến dịch an ninh hoàn tất", "success");
      selectedLogs = new Set();
      await loadSOCData();
    } catch (e) {
      nanobot.ui.showToast("Thao tác quân sự thất bại", "error");
    }
  }

  async function handleDraft(id: string, action: 'approve' | 'reject'): Promise<void> {
    isActionLoading = id;
    try {
      await apiClient.post(`/api/v1/security/drafts/${id}/${action}`, {});
      nanobot.ui.showToast(action === 'approve' ? "Authorized Mutation" : "Rejected Mutant", "success");
      await loadSOCData();
    } catch (e) {
      nanobot.ui.showToast("Duyệt lỗi", "error");
    } finally {
      isActionLoading = null;
    }
  }

  async function toggleMartialLaw(): Promise<void> {
    try {
      const newStatus: boolean = !stats.is_read_only;
      await apiClient.post("/api/v1/security/martial-law", { enabled: newStatus });
      stats.is_read_only = newStatus;
      nanobot.ui.showToast(newStatus ? "MARTIAL LAW ACTIVE" : "MARTIAL LAW DISARMED", newStatus ? "warning" : "success");
    } catch (e) {
      nanobot.ui.showToast("Switch failed", "error");
    }
  }

  // --- [ELITE V2.2] Real-time Sinusoidal Oscilloscope Math ---
  let phase = $state(0);
  let animFrameId: number;

  function animLoop() {
    phase += 0.04;
    animFrameId = requestAnimationFrame(animLoop);
  }

  let cpuPath = $derived.by(() => {
    let points = [];
    const avgCpu = containers.reduce((acc, c) => acc + parseFloat(c.cpu || '0'), 0) / (containers.length || 1);
    const amp = 8 + avgCpu * 0.35; // Amplitude adjusts to CPU load
    const freq = 0.04 + (avgCpu * 0.0005);
    
    for (let x = 0; x <= 300; x += 4) {
      const y = 30 + Math.sin(x * freq + phase) * amp;
      points.push(`${x},${y}`);
    }
    return `M ${points.join(" L ")}`;
  });

  let ramPath = $derived.by(() => {
    let points = [];
    const avgRam = containers.reduce((acc, c) => acc + parseFloat(c.mem_perc || '0'), 0) / (containers.length || 1);
    const amp = 8 + avgRam * 0.25; // Amplitude adjusts to RAM load
    const freq = 0.035;
    
    for (let x = 0; x <= 300; x += 4) {
      const y = 30 + Math.sin(x * freq - phase * 0.7) * amp; // Scrolls reverse
      points.push(`${x},${y}`);
    }
    return `M ${points.join(" L ")}`;
  });

  async function clearLogs(): Promise<void> {
    const confirmed = await nanobot.ui.showConfirm({
      title: "CẢNH BÁO TỐI CAO SOC",
      message: "[SOC WARNING] Bạn có chắc chắn muốn XÓA SẠCH toàn bộ Nhật ký an ninh (Audit Trail)? Hành động này không thể hoàn tác!",
      confirmLabel: "XÓA HOÀN TOÀN",
      cancelLabel: "HỦY BỎ"
    });
    if (!confirmed) return;
    try {
      await apiClient.post("/api/v1/security/audit-logs/clear", {});
      nanobot.ui.showToast("Nhật ký an ninh đã được làm sạch", "success");
      await loadSOCData();
    } catch (e) {
      console.error("[SOC] Clear logs error:", e);
      nanobot.ui.showToast("Lỗi làm sạch log", "error");
    }
  }

  onMount(() => {
    loadSOCData();
    animLoop();
    const interval = setInterval(loadSOCData, 10000); // 10s cycle for live resources
    return () => {
      clearInterval(interval);
      cancelAnimationFrame(animFrameId);
    };
  });
</script>

<div class="h-full flex flex-col bg-[#020408] text-gray-300 font-mono overflow-hidden relative selection:bg-cyan-500/30">
  <!-- HUD Ambient Layer -->
  <div class="absolute inset-0 pointer-events-none z-0">
    <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(6,182,212,0.03)_0%,transparent_70%)]"></div>
    <div class="absolute inset-0 opacity-[0.02]" style="background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px); background-size: 32px 32px;"></div>
    <div class="absolute inset-0 bg-gradient-to-b from-transparent via-cyan-500/[0.02] to-transparent h-full w-full animate-[scanline_10s_linear_infinite]"></div>
  </div>

  <!-- Tactical Header -->
  <header class="z-10 p-4 bg-black/60 backdrop-blur-xl border-b border-cyan-500/20 flex flex-col gap-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="relative">
          <div class="absolute -inset-2 bg-cyan-500/20 blur-xl rounded-full"></div>
          <Activity size={24} class="text-cyan-400 relative animate-pulse" />
        </div>
        <div>
          <h1 class="text-xl font-black tracking-tighter text-white flex items-center gap-2">
            TRINITY SOC <span class="text-[9px] px-1.5 py-0.5 border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 rounded">ELITE V2.2</span>
          </h1>
          <div class="flex items-center gap-4 mt-0.5">
             <span class="text-[8px] text-gray-500 font-bold tracking-widest flex items-center gap-1">
               <div class="w-1 h-1 rounded-full bg-emerald-500"></div> System Healthy
             </span>
             <span class="text-[8px] text-cyan-500/60 font-bold tracking-widest">Sector 7-G Node</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2">
        {#each [
          { label: 'Pulse', val: stats.ai_status, color: 'text-cyan-400', tip: 'Nhịp đập thời gian thực của AI Engine (Trinity)' },
          { label: 'Threat', val: stats.threat_level, color: stats.threat_level === 'LOW' ? 'text-emerald-400' : 'text-rose-500', tip: 'Mức độ đe dọa hệ thống dựa trên phân tích log' },
          { label: 'Keys', val: stats.active_keys, color: 'text-purple-400', tip: 'Số lượng Key AI Gemini đang hoạt động trong vòng xoay' }
        ] as stat}
          <div 
            title={stat.tip}
            class="px-3 py-1.5 bg-white/[0.02] border border-white/5 rounded flex flex-col items-center min-w-[70px] cursor-help hover:border-cyan-500/30 transition-colors"
          >
            <span class="text-[7px] text-gray-500 font-black">{stat.label}</span>
            <span class="text-xs font-black {stat.color} tracking-tighter">{stat.val}</span>
          </div>
        {/each}
        <button 
          onclick={toggleMartialLaw}
          title="Bật Lockdown để kích hoạt Thiết Quân Luật (Chế độ Chỉ đọc toàn hệ thống)"
          class="px-4 py-1.5 rounded border transition-all active:scale-95 flex flex-col items-center min-w-[90px]
                 {stats.is_read_only ? 'bg-rose-500/20 border-rose-500/40 text-rose-500' : 'bg-white/5 border-white/10 text-gray-400'}"
        >
          <span class="text-[7px] font-black">Lockdown</span>
          <span class="text-xs font-black tracking-tighter">{stats.is_read_only ? 'ACTIVE' : 'DISARMED'}</span>
        </button>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="flex items-center gap-3 bg-black/40 p-2 rounded-lg border border-cyan-500/20 focus-within:border-cyan-500/50 transition-all">
      <div class="relative flex-1">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-cyan-500/40" />
        <input 
          type="text" 
          bind:value={searchTerm}
          placeholder="ENTER TARGET SIGNATURE..."
          class="w-full bg-transparent border-none focus:ring-0 text-[10px] pl-9 text-cyan-100 placeholder:text-gray-700 font-bold tracking-widest outline-none"
        />
      </div>
      
      <div class="flex items-center gap-1 border-x border-white/10 px-3">
        {#each ["ALL", "SUSPICIOUS", "CLEAN"] as level}
          <button 
            onclick={() => filterLevel = level}
            class="px-2 py-1 rounded text-[8px] font-black transition-all
                   {filterLevel === level ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30' : 'text-gray-600 hover:text-gray-400'}"
          >
            {level}
          </button>
        {/each}
      </div>

      <button 
        onclick={clearLogs} 
        title="Làm sạch toàn bộ nhật ký an ninh (Flush Audit Logs)" 
        class="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/30 text-rose-400 rounded text-[8px] font-black transition-all flex items-center gap-1 cursor-pointer border border-rose-500/20"
      >
        <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
        LÀM SẠCH LOG
      </button>

      <button onclick={loadSOCData} class="p-2 text-gray-500 hover:text-cyan-400 transition-colors">
        <RefreshCw size={14} class={isLoading ? 'animate-spin' : ''} />
      </button>
    </div>
  </header>

  <main class="flex-1 flex overflow-hidden z-10">
    <!-- Action Sidebar (Floating) -->
    {#if selectedLogs.size > 0}
      <div 
        class="absolute bottom-6 left-1/2 -translate-x-1/2 bg-cyan-600 text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-6 border border-cyan-400/50 backdrop-blur-md animate-in slide-in-from-bottom-4"
        style="z-index: {Z_INDEX_ADMIN.HUD_FLOATING};"
      >
        <span class="text-xs font-black tracking-widest ">{selectedLogs.size} Targets Locked</span>
        <div class="flex gap-2">
          <button onclick={() => bulkAction('BLACKLIST')} class="flex items-center gap-2 px-3 py-1 bg-black/20 hover:bg-black/40 rounded-full text-[10px] font-black transition-all">
            <Ban size={12} /> Blacklist
          </button>
          <button onclick={() => bulkAction('REVOKE')} class="flex items-center gap-2 px-3 py-1 bg-black/20 hover:bg-black/40 rounded-full text-[10px] font-black transition-all">
            <Trash2 size={12} /> Revoke
          </button>
          <button onclick={() => selectedLogs = new Set()} class="p-1 hover:bg-white/10 rounded-full"><X size={14} /></button>
        </div>
      </div>
    {/if}
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Live Core Infrastructure (SOC Container Monitor) -->
      {#if containers.length > 0}
        <div class="p-6 border-b border-cyan-500/10 space-y-4 bg-cyan-950/[0.01]">
          <div class="flex justify-between items-center">
            <h2 class="text-[10px] font-black flex items-center gap-2 text-cyan-400 tracking-widest">
              <span class="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-ping"></span>
              CORE INFRASTRUCTURE RESOURCES (LIVE STATS)
            </h2>
            <span class="text-[8px] text-gray-500 font-mono tracking-widest">{containers.length} CONTAINER(S) ACTIVE</span>
          </div>

          <div class="flex gap-4 overflow-x-auto scrollbar-mission pb-2">
            <!-- Neon Oscilloscope card -->
            <div class="bg-cyan-950/[0.02] border border-cyan-500/20 rounded-xl p-4 flex flex-col justify-between h-[128px] overflow-hidden relative group w-[320px] shrink-0">
              <div class="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_top_right,rgba(6,182,212,0.05)_0%,transparent_60%)]"></div>
              <div class="flex justify-between items-start z-10">
                <div class="flex flex-col">
                  <span class="text-[8px] text-cyan-400 font-black tracking-widest uppercase">TRINITY NEURAL OSCILLOSCOPE</span>
                  <span class="text-[7px] text-gray-500 font-mono tracking-wider mt-0.5">Real-time system pulse telemetry</span>
                </div>
                <div class="flex gap-3 text-[7px] font-mono">
                  <div class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-cyan-400"></span> CPU Wave</div>
                  <div class="flex items-center gap-1"><span class="w-1 h-1 rounded-full bg-purple-400"></span> RAM Wave</div>
                </div>
              </div>

              <!-- SVG Sine Wave Canvas -->
              <div class="w-full h-[55px] relative overflow-hidden mt-1">
                <svg class="w-full h-full" viewBox="0 0 300 60" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="cyan-glow" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stop-color="#06b6d4" stop-opacity="0.1" />
                      <stop offset="50%" stop-color="#06b6d4" stop-opacity="0.8" />
                      <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.1" />
                    </linearGradient>
                    <linearGradient id="purple-glow" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stop-color="#a855f7" stop-opacity="0.1" />
                      <stop offset="50%" stop-color="#a855f7" stop-opacity="0.8" />
                      <stop offset="100%" stop-color="#a855f7" stop-opacity="0.1" />
                    </linearGradient>
                  </defs>
                  <!-- Sine paths -->
                  <path d={ramPath} fill="none" stroke="url(#purple-glow)" stroke-width="1.5" stroke-linecap="round" />
                  <path d={cpuPath} fill="none" stroke="url(#cyan-glow)" stroke-width="2" stroke-linecap="round" />
                </svg>
              </div>

              <div class="flex justify-between items-center text-[7px] text-gray-600 font-mono mt-1 pt-1 border-t border-white/5">
                <span>FREQ: { (0.04 + (containers.reduce((acc, c) => acc + parseFloat(c.cpu || '0'), 0) / (containers.length || 1)) * 0.0005).toFixed(4) } GHz</span>
                <span>AMP: { (8 + (containers.reduce((acc, c) => acc + parseFloat(c.cpu || '0'), 0) / (containers.length || 1)) * 0.35).toFixed(1) } mV</span>
              </div>
            </div>

            {#each sortedContainers as c}
              <div class="bg-white/[0.01] border border-white/5 rounded-xl p-4 hover:bg-white/[0.02] hover:border-cyan-500/20 transition-all duration-300 relative overflow-hidden group w-[220px] shrink-0 h-[128px] flex flex-col justify-between">
                {#if opLoading === c.name}
                  <div class="absolute inset-0 bg-black/85 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-2" transition:fade>
                    <div class="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                    <span class="text-[8px] text-cyan-400 font-black tracking-widest uppercase">CONTROLLING...</span>
                  </div>
                {/if}

                <!-- Card Header -->
                <div class="flex justify-between items-start mb-2">
                  <div class="flex flex-col gap-0.5 min-w-0">
                    <div class="flex items-center gap-1.5">
                      <span class="w-1.5 h-1.5 rounded-full {
                        c.state === 'running' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' :
                        c.state === 'exited' ? 'bg-orange-500 shadow-[0_0_8px_rgba(249,115,22,0.5)]' : 'bg-rose-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'
                      }"></span>
                      <span class="text-[10px] font-mono font-black text-gray-200 truncate">{c.name.replace('fast_platform_', '')}</span>
                    </div>
                    <span class="text-[7px] text-gray-500 truncate max-w-[120px]">{c.image}</span>
                  </div>

                  <!-- Professional Operations Control -->
                  <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {#if c.state === 'running'}
                      <button 
                        onclick={() => handleContainerAction(c.name, 'restart')}
                        class="w-5 h-5 rounded bg-cyan-500/10 hover:bg-cyan-500/30 text-cyan-400 transition-all flex items-center justify-center cursor-pointer"
                        title="Restart Container"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H12v4"></path></svg>
                      </button>
                      <button 
                        onclick={() => handleContainerAction(c.name, 'stop')}
                        class="w-5 h-5 rounded bg-rose-500/10 hover:bg-rose-500/30 text-rose-400 transition-all flex items-center justify-center cursor-pointer"
                        title="Stop Container"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>
                      </button>
                    {:else}
                      <button 
                        onclick={() => handleContainerAction(c.name, 'start')}
                        class="w-5 h-5 rounded bg-emerald-500/10 hover:bg-emerald-500/30 text-emerald-400 transition-all flex items-center justify-center cursor-pointer"
                        title="Start Container"
                      >
                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path></svg>
                      </button>
                    {/if}
                  </div>
                </div>

                <!-- Metrics -->
                <div class="grid grid-cols-2 gap-2 border-t border-white/5 pt-1.5 text-[9px]">
                  <div class="flex flex-col">
                    <span class="text-[7px] text-gray-500 font-bold block mb-0.5">CPU</span>
                    <span class="font-bold text-gray-300">{c.cpu}</span>
                    <div class="w-full bg-white/5 h-0.5 rounded-full mt-0.5 overflow-hidden">
                      <div class="bg-cyan-500 h-full rounded-full transition-all duration-500" style="width: {c.cpu}"></div>
                    </div>
                  </div>

                  <div class="flex flex-col">
                    <div class="flex justify-between">
                      <span class="text-[7px] text-gray-500 font-bold block">RAM</span>
                      <span class="text-[7px] font-mono {
                        parseFloat(c.mem_perc) > 85 ? 'text-rose-400 font-black animate-pulse' :
                        parseFloat(c.mem_perc) > 70 ? 'text-orange-400 font-bold' : 'text-emerald-400'
                      }">{c.mem_perc}</span>
                    </div>
                    <span class="font-bold text-gray-300 truncate mt-0.5">{c.mem_usage.split(' / ')[0]}</span>
                    <div class="w-full bg-white/5 h-0.5 rounded-full mt-0.5 overflow-hidden">
                      <div class="h-full rounded-full transition-all duration-500 {
                        parseFloat(c.mem_perc) > 85 ? 'bg-rose-500' :
                        parseFloat(c.mem_perc) > 70 ? 'bg-orange-500' : 'bg-emerald-500'
                      }" style="width: {c.mem_perc}"></div>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <div 
        title="Nhật ký truy vết các hành động thời gian thực của toàn bộ Admin và Hệ thống"
        class="grid grid-cols-[40px_100px_1fr_200px_100px] gap-4 px-6 py-3 border-b border-white/5 bg-white/[0.02] text-[9px] font-black text-gray-500 tracking-widest cursor-help"
      >
        <div class="flex items-center">
          <input 
            type="checkbox" 
            checked={selectedLogs.size === filteredLogs.length && filteredLogs.length > 0}
            onclick={toggleSelectAll}
            class="rounded border-white/10 bg-transparent text-cyan-500 focus:ring-0" 
          />
        </div>
        <div>Timestamp</div>
        <div>Operational Action</div>
        <div>Actor Identity</div>
        <div class="text-right">Risk Pulse</div>
      </div>

      <div class="flex-1 overflow-y-auto scrollbar-mission">
        {#each filteredLogs as log, i (log.timestamp + i)}
          <div 
            class="grid grid-cols-[40px_100px_1fr_200px_100px] gap-4 px-6 py-2.5 border-b border-white/[0.03] items-center hover:bg-cyan-500/[0.03] transition-all group relative {log.suspicious ? 'bg-rose-500/[0.02]' : ''}"
            in:fade={{ delay: i * 5 }}
          >
            <div class="absolute left-0 top-0 bottom-0 w-1 bg-cyan-500 opacity-0 group-hover:opacity-100 transition-opacity {log.suspicious ? 'bg-rose-500' : ''}"></div>
            <div class="flex items-center">
              <input type="checkbox" checked={selectedLogs.has(i)} onchange={() => toggleSelect(i)} class="rounded border-white/10 bg-transparent text-cyan-500 focus:ring-0" />
            </div>
            <div class="text-[10px] text-gray-600 font-mono">{new Date(log.timestamp).toLocaleTimeString([], { hour12: false })}</div>
            <div class="flex flex-col min-w-0">
              <span class="text-[11px] font-bold text-gray-200 truncate group-hover:text-cyan-400 transition-colors tracking-tight">{log.action}</span>
              <span class="text-[8px] text-gray-600 font-black">{log.ms?.toFixed(1) || 0} MS</span>
            </div>
            <div class="flex flex-col"><span class="text-[10px] font-black text-cyan-500/80 truncate">{log.actor}</span><span class="text-[9px] text-gray-600 font-mono italic">{log.ip}</span></div>
            <div class="flex justify-end items-center gap-3">
              <button onclick={() => detailLog = log} class="p-1.5 opacity-0 group-hover:opacity-100 bg-white/5 hover:bg-cyan-500/20 text-cyan-400 rounded transition-all"><Eye size={12} /></button>
              {#if log.suspicious}<ShieldAlert size={10} class="text-rose-500 animate-pulse" />{:else}<div class="w-1 h-1 rounded-full bg-emerald-500/40"></div>{/if}
            </div>
          </div>
        {/each}
      </div>
    </div>

    <!-- Mutation Aside -->
    <aside class="w-[300px] border-l border-white/5 bg-black/40 flex flex-col">
      <div 
        title="Hàng đợi phê duyệt các thao tác nhạy cảm (Cần Lockdown: ACTIVE)"
        class="p-4 border-b border-white/5 flex items-center justify-between cursor-help hover:bg-white/[0.02] transition-colors"
      >
        <span class="text-[10px] font-black tracking-widest text-white">Neural Queue</span>
        <span class="text-[10px] px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded border border-purple-500/20">{drafts.length} PENDING</span>
      </div>
      <div class="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-mission">
        {#each drafts as draft (draft.id)}
          <div class="bg-white/[0.02] border border-white/10 p-4 rounded-xl group relative overflow-hidden">
             <div class="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity"><Fingerprint size={48} /></div>
             <div class="relative z-10">
               <span class="text-[8px] text-purple-400 font-black mb-1 block">ID_{draft.id.slice(0,6)}</span>
               <h4 class="text-[10px] font-black text-white mb-3 leading-tight">{draft.action_type}</h4>
               <div class="flex gap-2">
                 <button onclick={() => handleDraft(draft.id, 'approve')} class="flex-1 py-1.5 bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-400 border border-cyan-500/30 text-[9px] font-black rounded transition-all">Confirm</button>
                 <button onclick={() => handleDraft(draft.id, 'reject')} class="px-2 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 border border-rose-500/20 text-[9px] font-black rounded transition-all"><X size={12} /></button>
               </div>
             </div>
          </div>
        {/each}
      </div>

      <!-- Whitelist Phone Numbers (Anti-Spam) -->
      <div class="p-4 border-t border-white/5 space-y-4 bg-black/20">
        <div class="flex justify-between items-center">
          <span class="text-[10px] font-black tracking-widest text-cyan-400 uppercase italic">Anti-Spam Whitelist</span>
          <span class="text-[9px] font-mono text-gray-500">{whitelistPhones.length} SĐT</span>
        </div>

        <!-- Input form -->
        <div class="flex gap-2">
          <input 
            type="text" 
            bind:value={newPhone} 
            placeholder="Nhập số điện thoại test..."
            class="flex-1 bg-black/50 border border-white/10 rounded-lg px-2.5 py-1.5 text-[10px] font-mono text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500/50 transition-colors"
            disabled={phoneLoading}
            onkeydown={(e) => e.key === 'Enter' && addPhone()}
          />
          <button 
            onclick={addPhone}
            disabled={phoneLoading}
            class="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-[9px] font-black tracking-widest transition-all cursor-pointer flex items-center justify-center min-w-[50px]"
          >
            {#if phoneLoading}
              <div class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            {:else}
              Thêm
            {/if}
          </button>
        </div>

        <!-- Whitelisted phones list -->
        <div class="space-y-1.5 max-h-[250px] overflow-y-auto scrollbar-mission">
          {#each whitelistPhones as phone}
            <div class="flex justify-between items-center p-2 rounded bg-black/40 border border-white/5 group hover:border-cyan-500/20 transition-all duration-300">
              <div class="flex items-center gap-1.5">
                <span class="w-1 h-1 rounded-full bg-emerald-500 shadow-[0_0_6px_rgba(16,185,129,0.5)]"></span>
                <span class="text-[10px] font-mono font-bold text-gray-300">{phone}</span>
              </div>
              <button 
                onclick={() => removePhone(phone)}
                class="text-gray-600 hover:text-rose-400 transition-colors opacity-0 group-hover:opacity-100 cursor-pointer"
                title="Xóa khỏi Whitelist"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
              </button>
            </div>
          {:else}
            <div class="text-center py-6 opacity-30 italic text-[9px]">Chưa có SĐT whitelist nào.</div>
          {/each}
        </div>
      </div>
    </aside>
  </main>

  <!-- Detail Modal -->
  {#if detailLog}
    <div 
      class="absolute inset-0 flex items-center justify-center p-6 bg-black/80 backdrop-blur-md"
      style="z-index: {Z_INDEX_ADMIN.MODAL};"
      transition:fade
    >
      <div class="w-full max-w-2xl bg-[#0a0c10] border border-cyan-500/30 rounded-2xl shadow-2xl overflow-hidden flex flex-col" transition:scale={{ start: 0.95 }}>
        <div class="p-6 border-b border-white/5 flex justify-between items-center bg-cyan-500/[0.02]">
           <div class="flex items-center gap-3"><Fingerprint size={20} class="text-cyan-400" /><div><h3 class="text-sm font-black text-white tracking-widest">Forensic Analysis</h3></div></div>
           <button onclick={() => detailLog = null} class="p-2 hover:bg-white/5 rounded-full"><X size={20} /></button>
        </div>
        <div class="p-6 space-y-6 overflow-y-auto">
           <div class="grid grid-cols-2 gap-4">
             <div class="p-4 bg-white/[0.01] border border-white/5 rounded-xl"><span class="text-[8px] text-gray-500 font-black ">Identity</span><p class="text-xs font-bold text-cyan-400 mt-1">{detailLog.actor}</p></div>
             <div class="p-4 bg-white/[0.01] border border-white/5 rounded-xl"><span class="text-[8px] text-gray-500 font-black ">IP</span><p class="text-xs font-bold text-cyan-400 mt-1">{detailLog.ip}</p></div>
           </div>
           <div class="space-y-2">
             <span class="text-[8px] text-gray-500 font-black ">Payload JSON</span>
             <div class="p-4 bg-black rounded-xl border border-white/5 font-mono text-[9px] text-emerald-400/80 overflow-x-auto"><pre>{JSON.stringify(detailLog, null, 2)}</pre></div>
           </div>
        </div>
        <div class="p-6 border-t border-white/5 flex gap-3">
           <button class="flex-1 py-3 bg-rose-600 text-white text-[10px] font-black tracking-widest rounded-xl">Exile Target</button>
           <button onclick={() => detailLog = null} class="flex-1 py-3 bg-white/5 border border-white/10 text-white text-[10px] font-black rounded-xl">Close</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  @keyframes scanline { from { transform: translateY(-100%); } to { transform: translateY(100%); } }
  .scrollbar-mission::-webkit-scrollbar { width: 3px; }
  .scrollbar-mission::-webkit-scrollbar-track { background: transparent; }
  .scrollbar-mission::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.05); }
</style>
