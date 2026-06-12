<script lang="ts">
    import { onMount } from 'svelte';
    import { fade } from 'svelte/transition';
    import Network from '@lucide/svelte/icons/network';
    import GitBranch from '@lucide/svelte/icons/git-branch';
    import Sparkles from '@lucide/svelte/icons/sparkles';
    import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
    import ChevronRight from '@lucide/svelte/icons/chevron-right';
    import RefreshCw from '@lucide/svelte/icons/refresh-cw';
    import Bot from '@lucide/svelte/icons/bot';
    import { useNanobot } from '$lib/state/nanobot.svelte';

    const nanobot = useNanobot();

    // Props
    type Props = {};

    // State
    let loading = $state(true);
    let refreshing = $state(false);
    let meta = $state<{
        total_nodes: number;
        total_edges: number;
        pillars: number;
        unclassified: number;
        ai_suggested: number;
        generated_at: string;
    } | null>(null);
    let error = $state<string | null>(null);

    onMount(async () => {
        await loadStats();
    });

    async function loadStats() {
        try {
            const res = await fetch('/api/v1/seo/graph');
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const aiSuggested = (data.links ?? []).filter((l: any) => !l.is_confirmed).length;
            meta = { ...data.meta, ai_suggested: aiSuggested };
        } catch (e) {
            error = 'Không thể tải dữ liệu SEO Graph.';
        } finally {
            loading = false;
        }
    }

    async function handleRefresh() {
        refreshing = true;
        await loadStats();
        refreshing = false;
    }

    function openGraph() {
        nanobot.openWidget('SEO_GRAPH');
    }

    // Computed
    const clusterCount = $derived(
        meta ? meta.total_nodes - meta.pillars - meta.unclassified : 0
    );
    const healthScore = $derived(
        meta && meta.total_nodes > 0
            ? Math.round(((meta.total_nodes - meta.unclassified) / meta.total_nodes) * 100)
            : 0
    );
</script>

<div
    class="relative group overflow-hidden bg-[#0a0a0a]/80 backdrop-blur-3xl border border-white/5 rounded-[2.5rem] p-8 transition-all duration-700 hover:border-violet-500/30"
    in:fade={{ duration: 900, delay: 300 }}
>
    <!-- Background Aura — violet for SEO/graph theme -->
    <div class="absolute -bottom-20 -right-20 w-72 h-72 bg-violet-500/8 blur-[100px] rounded-full group-hover:bg-violet-500/15 transition-all duration-1000"></div>
    <div class="absolute -top-10 left-20 w-48 h-48 bg-indigo-500/5 blur-[80px] rounded-full group-hover:bg-indigo-500/12 transition-all duration-1000"></div>

    <!-- Scanline effect -->
    <div class="universal-scanline pointer-events-none"></div>

    <div class="relative z-10">
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
            <div class="flex items-center gap-4">
                <div class="p-3 bg-white/5 rounded-2xl border border-white/10 group-hover:border-violet-500/50 transition-colors relative">
                    <Network size={24} class="text-white group-hover:text-violet-400 transition-colors" />
                    <!-- Pulse dot nếu có unclassified -->
                    {#if meta && meta.unclassified > 0}
                        <span class="absolute -top-1 -right-1 flex h-3 w-3">
                            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                            <span class="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                        </span>
                    {/if}
                </div>
                <div>
                    <h2 class="text-xl font-black tracking-tighter text-white italic">SEO Pillar Network</h2>
                    <p class="text-[10px] font-mono text-gray-500 tracking-[0.3em]">AI-POWERED INTERNAL LINKING</p>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <!-- Refresh button -->
                <button
                    onclick={handleRefresh}
                    disabled={refreshing}
                    class="p-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all disabled:opacity-40"
                    title="Làm mới dữ liệu"
                >
                    <RefreshCw size={14} class="text-gray-400 {refreshing ? 'animate-spin' : ''}" />
                </button>
                <!-- Open Graph button -->
                <button
                    onclick={openGraph}
                    class="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-violet-500/10 border border-white/10 hover:border-violet-500/30 rounded-xl transition-all group/btn"
                >
                    <span class="text-[10px] font-black tracking-widest text-gray-400 group-hover/btn:text-violet-300">Graph Hub</span>
                    <ChevronRight size={14} class="text-gray-600 group-hover/btn:text-violet-400 group-hover/btn:translate-x-0.5 transition-all" />
                </button>
            </div>
        </div>

        {#if loading}
            <!-- Skeleton -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 opacity-20">
                {#each Array(4) as _}
                    <div class="h-20 bg-white/5 rounded-3xl animate-pulse"></div>
                {/each}
            </div>
        {:else if error}
            <div class="flex items-center gap-3 p-4 bg-red-500/5 border border-red-500/10 rounded-2xl">
                <AlertTriangle size={16} class="text-red-400 shrink-0" />
                <p class="text-xs text-red-300">{error}</p>
            </div>
        {:else if meta}
            <!-- Stats Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <!-- Pillars -->
                <div class="relative p-5 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-violet-500/5 hover:border-violet-500/20 transition-all group/card">
                    <div class="flex justify-between items-start mb-3">
                        <div class="p-1.5 bg-violet-500/10 rounded-xl">
                            <Network size={12} class="text-violet-400" />
                        </div>
                        <span class="text-[8px] font-mono text-gray-600 tracking-widest uppercase">Pillars</span>
                    </div>
                    <div class="text-3xl font-black text-white tracking-tighter mb-1">{meta.pillars}</div>
                    <div class="text-[10px] font-mono text-gray-500 tracking-widest">Trang trụ cột</div>
                </div>

                <!-- Clusters -->
                <div class="relative p-5 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-indigo-500/5 hover:border-indigo-500/20 transition-all">
                    <div class="flex justify-between items-start mb-3">
                        <div class="p-1.5 bg-indigo-500/10 rounded-xl">
                            <GitBranch size={12} class="text-indigo-400" />
                        </div>
                        <span class="text-[8px] font-mono text-gray-600 tracking-widest uppercase">Clusters</span>
                    </div>
                    <div class="text-3xl font-black text-indigo-300 tracking-tighter mb-1">{clusterCount}</div>
                    <div class="text-[10px] font-mono text-gray-500 tracking-widest">Liên kết nội trang</div>
                </div>

                <!-- AI Suggested -->
                <div class="relative p-5 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-orange-500/5 hover:border-orange-500/20 transition-all">
                    <div class="flex justify-between items-start mb-3">
                        <div class="p-1.5 bg-orange-500/10 rounded-xl">
                            <Bot size={12} class="text-orange-400" />
                        </div>
                        <span class="text-[8px] font-mono text-gray-600 tracking-widest uppercase">AI Suggest</span>
                    </div>
                    <div class="text-3xl font-black tracking-tighter mb-1 {meta.ai_suggested > 0 ? 'text-orange-400' : 'text-white'}">{meta.ai_suggested}</div>
                    <div class="text-[10px] font-mono text-gray-500 tracking-widest">Chờ duyệt</div>
                </div>

                <!-- Unclassified -->
                <div class="relative p-5 rounded-3xl bg-white/[0.02] border border-white/5 transition-all {meta.unclassified > 0 ? 'hover:bg-amber-500/5 hover:border-amber-500/20 border-amber-500/10' : ''}">
                    <div class="flex justify-between items-start mb-3">
                        <div class="p-1.5 {meta.unclassified > 0 ? 'bg-amber-500/10' : 'bg-white/5'} rounded-xl">
                            <AlertTriangle size={12} class="{meta.unclassified > 0 ? 'text-amber-400' : 'text-gray-600'}" />
                        </div>
                        <span class="text-[8px] font-mono text-gray-600 tracking-widest uppercase">Unclassified</span>
                    </div>
                    <div class="text-3xl font-black tracking-tighter mb-1 {meta.unclassified > 0 ? 'text-amber-400' : 'text-white'}">{meta.unclassified}</div>
                    <div class="text-[10px] font-mono text-gray-500 tracking-widest">Cần phân loại</div>
                </div>
            </div>

            <!-- Network Health Bar -->
            <div class="p-5 bg-white/[0.02] border border-white/5 rounded-2xl">
                <div class="flex justify-between items-center mb-3">
                    <div class="flex items-center gap-2">
                        <Sparkles size={12} class="text-violet-400" />
                        <span class="text-[10px] font-mono text-gray-500 tracking-widest uppercase">Network Health</span>
                    </div>
                    <span class="text-sm font-black {healthScore >= 80 ? 'text-emerald-400' : healthScore >= 50 ? 'text-amber-400' : 'text-red-400'}">
                        {healthScore}%
                    </span>
                </div>
                <div class="relative h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div
                        class="h-full rounded-full transition-all duration-700 {healthScore >= 80 ? 'bg-gradient-to-r from-violet-500 to-indigo-400' : healthScore >= 50 ? 'bg-gradient-to-r from-amber-500 to-orange-400' : 'bg-red-500'}"
                        style="width: {healthScore}%"
                    ></div>
                </div>
                <div class="flex justify-between items-center mt-2 text-[9px] font-mono text-gray-600">
                    <span>{meta.total_nodes} nodes · {meta.total_edges} edges</span>
                    {#if meta.unclassified > 0}
                        <button onclick={openGraph} class="text-amber-500 hover:text-amber-400 transition-colors flex items-center gap-1">
                            <AlertTriangle size={10} />
                            Phân loại {meta.unclassified} node →
                        </button>
                    {:else}
                        <span class="text-emerald-500/60">Mạng lưới đang hoạt động tốt</span>
                    {/if}
                </div>
            </div>
        {:else}
            <!-- Empty state — prompt to start -->
            <div class="text-center py-8">
                <div class="inline-flex p-4 bg-violet-500/10 rounded-3xl mb-4">
                    <Network size={32} class="text-violet-400" />
                </div>
                <p class="text-sm text-gray-500 mb-2">SEO Graph chưa có dữ liệu</p>
                <p class="text-[10px] text-gray-600 max-w-xs mx-auto leading-relaxed">
                    Đăng ký bài viết/sản phẩm vào graph và đặt Pillar Pages để bắt đầu xây dựng mạng lưới nội trang.
                </p>
                <button
                    onclick={openGraph}
                    class="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-violet-500 hover:bg-violet-400 text-white text-xs font-black rounded-2xl transition-all hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] active:scale-95"
                >
                    <Network size={14} />
                    Mở SEO Graph
                </button>
            </div>
        {/if}
    </div>
</div>
