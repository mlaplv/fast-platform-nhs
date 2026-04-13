<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, fly, scale } from 'svelte/transition';
    import XohiLogo from '$lib/components/admin/XohiLogo.svelte';
    import NeuralPulse from '../widgets/NeuralPulse.svelte';
    
    // Icons
    import Brain from "lucide-svelte/icons/brain";
    import RefreshCw from "lucide-svelte/icons/refresh-cw";
    import Trash2 from "lucide-svelte/icons/trash-2";
    import AlertTriangle from "lucide-svelte/icons/alert-triangle";
    import CheckCircle2 from "lucide-svelte/icons/check-circle-2";
    import Activity from "lucide-svelte/icons/activity";
    import ShieldCheck from "lucide-svelte/icons/shield-check";
    import Database from "lucide-svelte/icons/database";
    import Cpu from "lucide-svelte/icons/cpu";
    import History from "lucide-svelte/icons/history";
    import BookOpen from "lucide-svelte/icons/book-open";
    import Zap from "lucide-svelte/icons/zap";
    import ChevronRight from "lucide-svelte/icons/chevron-right";
    import Info from "lucide-svelte/icons/info";
    import Terminal from "lucide-svelte/icons/terminal";

    let { isWidget = false } = $props();
    import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

    let brainStatus = $state(null);
    let loading = $state(true);
    let syncing = $state(false);
    let message = $state("");
    let manualPage = $state(0);

    // CNS V2.2: Reactive Link to Modal Header Controls
    $effect(() => {
        nanobot.isBrainSyncing = syncing;
    });

    $effect(() => {
        if (nanobot.brainActionTrigger === 'SYNC') {
            triggerSync();
            nanobot.brainActionTrigger = 'NONE';
        } else if (nanobot.brainActionTrigger === 'PURGE') {
            triggerPurge();
            nanobot.brainActionTrigger = 'NONE';
        }
    });

    onMount(async () => {
        await loadBrainStatus();
        const poll = setInterval(loadBrainStatus, 30000); // Polling telemetry every 30s
        return () => clearInterval(poll);
    });

    async function loadBrainStatus() {
        try {
            const res = await fetch('/api/v1/admin/ai/brain/status');
            if (res.ok) {
                const data = await res.json();
                brainStatus = data;
                // Sync with global state for Modal Header & HUD
                nanobot.brainTotalNodes = data.total_nodes;
                nanobot.brainVectorHealth = data.vector_health;
                nanobot.brainDuplicatesCount = (data.duplicates || []).length;
                nanobot.brainCoverage = data.coverage || 0;
                
                // Telemetry Sync
                nanobot.brainUptime = data.uptime || 0;
                nanobot.brainLastSync = data.last_sync || 0;
                nanobot.brainStabilityScore = data.stability_score || 100;
            }
        } catch (e) {
            console.error('Failed to load brain status:', e);
        } finally {
            loading = false;
        }
    }

    async function triggerSync() {
        if (syncing) return;
        nanobot.showConfirm({
            title: "XÁC NHẬN NEURAL SYNC",
            message: "Sếp muốn đồng bộ lại tri thức? Tác vụ này sẽ tốn tài nguyên CPU/RAM trong vài phút để mã hóa lại toàn bộ Database.",
            confirmLabel: "SYNC NOW",
            onConfirm: async () => {
                syncing = true;
                message = "ENCODING NEURAL PATHWAYS...";
                try {
                    const res = await fetch('/api/v1/admin/ai/brain/sync', { method: 'POST' });
                    if (res.ok) {
                        message = "SYNC_COMPLETE: KNOWLEDGE REBASED";
                        await loadBrainStatus();
                        setTimeout(() => message = "", 3000);
                    }
                } catch (e) {
                    message = "ERROR: NEURAL SYNC FAILED.";
                } finally {
                    syncing = false;
                }
            }
        });
    }

    async function triggerPurge() {
        nanobot.showConfirm({
            title: "XÁC NHẬN PURGE",
            message: "Sếp muốn dọn dẹp tri thức rác (Orphaned Embeddings)? Tác vụ này sẽ tối ưu RAM nhưng không thể hoàn tác.",
            confirmLabel: "PURGE NOW",
            onConfirm: async () => {
                message = "PURGING VOLATILE MEMORY...";
                const res = await fetch('/api/v1/admin/ai/brain/purge', { method: 'POST' });
                if (res.ok) {
                    message = "PURGE_SUCCESS: CORTEX OPTIMIZED";
                    await loadBrainStatus();
                    setTimeout(() => message = "", 3000);
                }
            }
        });
    }

    const manual = [
        {
            title: "SYC — Neural Synchronization",
            desc: "Đồng bộ hóa toàn bộ cơ sở dữ liệu (Sản phẩm, Bài viết) vào não bộ AI. Hãy chạy SYC sau khi cập nhật dữ liệu mới để AI luôn thông minh nhất.",
            impact: "Tốn tài nguyên trong lúc chạy, nhưng làm sắc bén tri thức Vector sau đó."
        },
        {
            title: "PURGE — Cortex Optimization",
            desc: "Xóa bỏ các vector 'mồ côi' (orphan) hoặc dữ liệu rác tích tụ lâu ngày. Giúp Helen truy vấn dữ liệu nhanh hơn và giảm tải cơ sở dữ liệu.",
            impact: "Loại bỏ hoàn toàn các 'vết sẹo' tri thức cũ không còn tồn tại."
        },
        {
            title: "AUD — Anti-Duplicate Protocol",
            desc: "Lõi lọc trùng tinh vi. Nếu phát hiện tri thức có độ tương đồng >92%, Helen sẽ 'điểm mặt' ngay tại bảng Audit để Sếp xử lý, tránh lãng phí RAM.",
            impact: "Giảm tỉ lệ Helen tư vấn sai hoặc nhầm tên sản phẩm cho khách."
        },
        {
            title: "CLI — War Room Command",
            desc: "Điều khiển Helen từ Terminal. Chạy lệnh qua Docker để đảm bảo ổn định: 'docker exec -it fast_platform_api python3 backend/scripts/helen_brain.py status' hoặc 'rebuild'.",
            impact: "Tác chiến thần tốc ngay cả khi không có giao diện Web."
        }
    ];

    function formatUptime(sec: number) {
        if (sec < 60) return sec + "s";
        if (sec < 3600) return Math.floor(sec / 60) + "m";
        return Math.floor(sec / 3600) + "h " + Math.floor((sec % 3600) / 60) + "m";
    }

    function formatLastSync(ts: number) {
        if (!ts) return "NEVER";
        const diff = Math.floor((Date.now() / 1000) - ts);
        if (diff < 60) return "JUST NOW";
        return formatUptime(diff) + " AGO";
    }
</script>

<div class="brain-elite-hud {isWidget ? 'h-full' : 'min-h-screen p-8'} bg-[#020202] text-white flex flex-col overflow-hidden relative">
    <!-- Scalar Scanline Overlay -->
    <div class="absolute inset-0 pointer-events-none z-50 opacity-[0.03] scanline-effect"></div>
    <div class="absolute inset-0 pointer-events-none z-50 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-[0.02]"></div>

    {#if loading}
        <div class="flex-1 flex flex-col items-center justify-center space-y-6">
            <div class="relative">
                <div class="absolute inset-0 rounded-full bg-indigo-500/20 blur-3xl animate-pulse"></div>
                <XohiLogo variant="simple" size={100} />
            </div>
            <p class="text-[10px] font-mono tracking-[0.5em] text-indigo-400 animate-pulse uppercase">Initializing Trinity Link...</p>
        </div>
    {:else if brainStatus}
        <div class="flex-1 flex flex-col lg:flex-row overflow-hidden">
            <!-- Left Panel: Telemetry & Core HUD -->
            <aside class="w-full lg:w-[380px] border-r border-white/5 bg-black/40 backdrop-blur-xl flex flex-col p-8 overflow-y-auto scrollbar-tactical">
                <div class="mb-12">
                    <div class="flex items-center gap-3 mb-2">
                        <div class="p-2 glow-indigo rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                            <Brain size={20} class="text-indigo-400" />
                        </div>
                        <div>
                            <h2 class="text-xl font-black italic tracking-tighter text-white">CORTEX CONTROL</h2>
                            <p class="text-[8px] font-mono text-gray-500 tracking-[0.3em] uppercase">TRINITY_SYSTEM_V2.2</p>
                        </div>
                    </div>
                </div>

                <!-- Neural Status Pulse -->
                <div class="py-12 flex flex-col items-center">
                    <NeuralPulse health={brainStatus.vector_health} active={!syncing} />
                    <div class="w-full mt-6 grid grid-cols-2 gap-4">
                        <div class="text-center">
                            <span class="text-[9px] font-mono text-indigo-400 uppercase tracking-[0.4em] mb-1 block">Stability</span>
                            <h3 class="text-2xl font-black italic tracking-tighter text-white">{brainStatus.stability_score}%</h3>
                        </div>
                        <div class="text-center">
                            <span class="text-[9px] font-mono text-vibrant-purple uppercase tracking-[0.4em] mb-1 block">Coverage</span>
                            <h3 class="text-2xl font-black italic tracking-tighter text-white">{nanobot.brainCoverage}%</h3>
                        </div>
                    </div>
                    <div class="mt-4 flex items-center justify-center gap-4 text-[9px] font-mono text-gray-600 uppercase">
                        <div class="flex items-center gap-1.5"><div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> LIVE</div>
                        <div class="flex items-center gap-1.5"><div class="w-1.5 h-1.5 rounded-full bg-indigo-500/40"></div> ENCRYPTED</div>
                    </div>
                </div>

                <!-- Telemetry Stats -->
                <div class="mt-auto space-y-6">
                    <div class="p-5 rounded-2xl bg-white/[0.02] border border-white/5 space-y-4">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <History size={12} class="text-gray-500" />
                                <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Uptime</span>
                            </div>
                            <span class="text-[11px] font-bold font-mono text-white tracking-widest">{formatUptime(nanobot.brainUptime)}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <Zap size={12} class="text-gray-500" />
                                <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Last Sync</span>
                            </div>
                            <span class="text-[11px] font-bold font-mono text-indigo-400 tracking-widest">{formatLastSync(nanobot.brainLastSync)}</span>
                        </div>
                        <div class="flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <Database size={12} class="text-gray-500" />
                                <span class="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Storage</span>
                            </div>
                            <span class="text-[11px] font-bold font-mono text-white tracking-widest">{Math.round(nanobot.brainTotalNodes * 0.42)} KB</span>
                        </div>
                    </div>

                    <button 
                        onclick={() => nanobot.setBrainManualOpen(true)}
                        class="w-full flex items-center justify-between p-5 rounded-2xl bg-indigo-500/5 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/10 transition-all group"
                    >
                        <div class="flex items-center gap-3">
                            <BookOpen size={16} />
                            <span class="text-[11px] font-black uppercase tracking-widest">Tactical Manual</span>
                        </div>
                        <ChevronRight size={14} class="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            </aside>

            <!-- Main Content: Audit Protocol -->
            <main class="flex-1 flex flex-col relative overflow-hidden">
                <!-- Inner Header -->
                <div class="p-8 border-b border-white/5 flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <div class="w-1 h-4 bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.6)]"></div>
                        <h3 class="text-[11px] font-black text-white uppercase tracking-[0.4em]">Audit Protocol — Active Matrix</h3>
                        <div class="flex items-center gap-2 px-3 py-1 bg-white/[0.03] border border-white/5 rounded-full">
                            <div class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
                            <span class="text-[9px] font-mono text-white/50 uppercase tracking-widest leading-none">Threshold: >92%</span>
                        </div>
                    </div>
                    
                    {#if message}
                        <div class="flex items-center gap-2 px-4 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 animate-pulse" in:fade>
                            <Terminal size={10} class="text-indigo-400" />
                            <span class="text-[9px] font-mono font-bold text-indigo-400 uppercase tracking-[0.2em]">{message}</span>
                        </div>
                    {/if}
                </div>

                <!-- Table/Status Area -->
                <div class="flex-1 overflow-auto p-8 scrollbar-tactical">
                    {#if brainStatus.duplicates.length > 0}
                        <div class="audit-elite-table rounded-[2.5rem] bg-gray-900/10 border border-white/5 overflow-hidden">
                            <table class="w-full text-left border-separate border-spacing-0">
                                <thead>
                                    <tr class="bg-white/[0.02]">
                                        <th class="p-6 text-[10px] font-black uppercase text-gray-500 tracking-widest">Classification</th>
                                        <th class="p-6 text-[10px] font-black uppercase text-gray-500 tracking-widest">Subject Context</th>
                                        <th class="p-6 text-[10px] font-black uppercase text-gray-500 tracking-widest">Stability Metric</th>
                                        <th class="p-6 text-[10px] font-black uppercase text-gray-500 tracking-widest text-right">Intervention</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each brainStatus.duplicates as d, i}
                                        <tr 
                                            class="hover:bg-white/[0.03] transition-all group"
                                            in:fly={{ y: 20, delay: i * 50 }}
                                        >
                                            <td class="p-6 border-t border-white/5">
                                                <div class="flex items-center gap-3">
                                                    <div class="p-2 rounded bg-indigo-500/10 text-indigo-400">
                                                        <Activity size={14} />
                                                    </div>
                                                    <span class="text-[10px] font-mono font-bold text-white uppercase tracking-widest">{d.type}</span>
                                                </div>
                                            </td>
                                            <td class="p-6 border-t border-white/5">
                                                <div class="text-sm font-bold text-gray-100 group-hover:text-indigo-300 transition-colors tracking-tight uppercase italic">{d.name}</div>
                                                <div class="text-[9px] text-gray-600 mt-1 font-mono tracking-[0.2em]">PATH://ROOT/NODE_{d.duplicate_id?.slice(0, 8)}</div>
                                            </td>
                                            <td class="p-6 border-t border-white/5">
                                                <div class="flex items-center gap-3">
                                                    <div class="w-px h-6 bg-amber-500/20"></div>
                                                    <div>
                                                        <span class="text-[10px] font-bold text-amber-500 uppercase tracking-widest">Collision Detected</span>
                                                        <p class="text-[9px] text-gray-500 font-mono italic">{d.reason}</p>
                                                    </div>
                                                </div>
                                            </td>
                                            <td class="p-6 border-t border-white/5 text-right">
                                                <button class="px-5 py-2.5 rounded-xl bg-white/5 border border-white/10 text-[9px] font-black uppercase tracking-widest text-gray-500 hover:text-white hover:border-indigo-500/50 hover:bg-indigo-500/10 transition-all active:scale-95">Resolve Hub</button>
                                            </td>
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {:else}
                        <!-- Empty State: Pure Matrix -->
                        <div class="h-full flex flex-col items-center justify-center text-center py-20" in:fade>
                            <div class="relative mb-12">
                                <div class="absolute inset-0 bg-emerald-500/20 blur-[100px] rounded-full animate-pulse"></div>
                                <div class="relative w-32 h-32 rounded-full border border-emerald-500/20 flex items-center justify-center">
                                    <ShieldCheck size={64} class="text-emerald-500/40" />
                                    <!-- Rotating Detail -->
                                    <div class="absolute inset-0 border border-emerald-500/10 border-dashed rounded-full animate-spin-slow"></div>
                                </div>
                            </div>
                            
                            <h4 class="text-3xl font-black italic text-white tracking-widest uppercase mb-4">Neural Harmony Established</h4>
                            <div class="flex items-center gap-4 mb-8">
                                <div class="h-px w-12 bg-white/10"></div>
                                <span class="text-[10px] font-mono text-emerald-400 uppercase tracking-[0.5em]">System Diagnostic: PURE</span>
                                <div class="h-px w-12 bg-white/10"></div>
                            </div>
                            <p class="text-gray-500 text-[11px] font-medium italic uppercase tracking-[0.2em] max-w-sm leading-relaxed">
                                Brain Matrix is in pristine condition. <br/> 
                                zero semantic collisions detected across <span class="text-white">{nanobot.brainTotalNodes} nodes</span>.
                            </p>
                        </div>
                    {/if}
                </div>

                <!-- Bottom Status Bar -->
                <footer class="p-5 border-t border-white/5 bg-black/40 text-[9px] font-mono text-gray-600 flex justify-between items-center">
                    <div class="flex gap-6">
                        <span class="flex items-center gap-2 italic uppercase"><div class="w-1 h-1 bg-emerald-500 rounded-full"></div> Trinity_Bridge: Active</span>
                        <span class="flex items-center gap-2 italic uppercase"><div class="w-1 h-1 bg-indigo-500 rounded-full"></div> Vector_Engine: Trinity_v2.2</span>
                    </div>
                    <div class="uppercase tracking-widest opacity-40">Administrative Clearance Level 1</div>
                </footer>
            </main>
        </div>
    {/if}

    <!-- Tactical Manual Overlay -->
    {#if nanobot.brainManualOpen}
        <div class="absolute inset-0 z-[var(--z-modal-overlay)] bg-black/90 backdrop-blur-3xl flex items-center justify-center p-8" in:fade>
            <div class="max-w-4xl w-full bg-gray-900/40 border border-white/10 rounded-[3rem] overflow-hidden flex flex-col h-[80vh]" in:scale={{ start: 0.95 }}>
                <header class="p-8 border-b border-white/5 flex justify-between items-start">
                    <div>
                        <h2 class="text-3xl font-black italic italic tracking-tighter text-white">TACTICAL MANUAL</h2>
                        <p class="text-[10px] font-mono text-indigo-400 tracking-[0.3em] uppercase mt-1">Operational Guidance v2.2</p>
                    </div>
                    <button 
                        onclick={() => nanobot.setBrainManualOpen(false)}
                        class="p-4 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-all active:scale-90"
                    >
                        <RefreshCw size={20} class="rotate-45" />
                    </button>
                </header>

                <div class="flex-1 overflow-y-auto p-12 space-y-12 scrollbar-tactical">
                    {#each manual as item, i}
                        <section in:fly={{ x: -20, delay: i * 100 }}>
                            <div class="flex items-center gap-4 mb-4">
                                <div class="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center font-mono font-black text-indigo-400">0{i+1}</div>
                                <h3 class="text-xl font-black italic tracking-tighter text-white uppercase">{item.title}</h3>
                            </div>
                            <div class="ml-14 space-y-4">
                                <p class="text-sm text-gray-400 leading-relaxed font-medium">{item.desc}</p>
                                <div class="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex items-start gap-3">
                                    <Info size={14} class="text-indigo-400 mt-0.5" />
                                    <div>
                                        <span class="text-[10px] font-mono text-indigo-400/80 uppercase tracking-widest font-black block mb-1">Operational Impact</span>
                                        <p class="text-[11px] text-gray-500 italic uppercase tracking-wider">{item.impact}</p>
                                    </div>
                                </div>
                            </div>
                        </section>
                    {/each}
                </div>

                <footer class="p-8 border-t border-white/5 flex justify-center">
                    <button 
                        onclick={() => nanobot.setBrainManualOpen(false)}
                        class="px-12 py-4 rounded-full bg-white text-black text-xs font-black uppercase tracking-[0.4em] hover:scale-105 active:scale-95 transition-all"
                    >
                        Acknowledged
                    </button>
                </footer>
            </div>
        </div>
    {/if}
</div>

<style>
    .brain-elite-hud {
        background: radial-gradient(circle at 0% 0%, rgba(79, 70, 229, 0.15), transparent 40%),
                    radial-gradient(circle at 100% 100%, rgba(16, 185, 129, 0.1), transparent 40%);
    }

    .glow-indigo {
        box-shadow: 0 0 20px rgba(79, 70, 229, 0.2);
    }

    .scanline-effect {
        background: linear-gradient(
            to bottom,
            rgba(255,255,255,0) 0%,
            rgba(255,255,255,0.05) 50%,
            rgba(255,255,255,0) 100%
        );
        background-size: 100% 4px;
        animation: scanline 10s linear infinite;
    }

    @keyframes scanline {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }

    .audit-elite-table {
        box-shadow: 0 50px 100px -20px rgba(0, 0, 0, 0.7);
    }

    .animate-spin-slow {
        animation: spin 30s linear infinite;
    }

    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .scrollbar-tactical::-webkit-scrollbar {
        width: 4px;
        height: 4px;
    }
    .scrollbar-tactical::-webkit-scrollbar-track {
        background: transparent;
    }
    .scrollbar-tactical::-webkit-scrollbar-thumb {
        background: rgba(79, 70, 229, 0.2);
        border-radius: 10px;
    }
    .scrollbar-tactical::-webkit-scrollbar-thumb:hover {
        background: rgba(79, 70, 229, 0.4);
    }
</style>
