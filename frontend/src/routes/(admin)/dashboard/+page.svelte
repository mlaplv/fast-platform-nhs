<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import ReviewGates from '$lib/components/admin/management/ReviewGates.svelte';
    import { fade } from 'svelte/transition';

    let campaigns = $state([]);
    let loading = $state(true);
    // Track all open SSE connections so we close them on page unmount
    const openStreams: EventSource[] = [];

    onMount(async () => {
        await loadCampaigns();
    });

    onDestroy(() => {
        // LIFECYCLE FIX: Close every SSE opened by this page
        openStreams.forEach(es => es.close());
        openStreams.length = 0;
    });

    async function loadCampaigns() {
        try {
            const res = await fetch(`/api/v1/content/campaigns`);
            campaigns = await res.json();
            
            // Start SSE ONLY for campaigns actively processing
            campaigns.forEach(c => {
                if (c.status === 'PROCESSING') {
                    startStreaming(c.id);
                }
            });
        } catch (e) {
            console.error('Failed to load campaigns:', e);
        } finally {
            loading = false;
        }
    }

    function startStreaming(id: string) {
        const eventSource = new EventSource(`/api/v1/content/campaigns/${id}/stream`);
        // LIFECYCLE FIX: Register so onDestroy can close it
        openStreams.push(eventSource);
        
        eventSource.addEventListener('progress', (event) => {
            const update = JSON.parse(event.data);
            const index = campaigns.findIndex(c => c.id === id);
            if (index !== -1) {
                campaigns[index] = { ...campaigns[index], ...update };
            }
        });

        // V65.0: SSE POISON PILL - Đóng stream ngay lập tức để bảo vệ RAM
        eventSource.addEventListener('terminate', () => {
            console.log(`[SSE] Poison pill received for ${id}. Disconnecting...`);
            eventSource.close();
            const i = openStreams.indexOf(eventSource);
            if (i !== -1) openStreams.splice(i, 1);
        });

        eventSource.onerror = (e) => {
            console.error(`SSE Error for ${id}:`, e);
            eventSource.close();
            const i = openStreams.indexOf(eventSource);
            if (i !== -1) openStreams.splice(i, 1);
        };
    }
</script>

<div class="dashboard p-8 min-h-screen bg-[#010101] text-white">
    <header class="mb-10 flex justify-between items-end">
        <div>
            <h1 class="text-4xl font-extrabold tracking-tighter bg-gradient-to-r from-white to-gray-500 bg-clip-text text-transparent">
                CONTENT FACTORY
            </h1>
            <p class="text-gray-500 mt-2 font-medium">Hệ thống điều phối 6 bước sáng tạo nội dung tự động</p>
        </div>
        <div class="bg-blue-600/10 px-4 py-2 rounded-full border border-blue-500/20 flex items-center gap-2">
            <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <span class="text-[10px] font-bold text-blue-400 uppercase tracking-widest">Live Engine Active</span>
        </div>
    </header>

    {#if loading}
        <div class="relative w-20 h-20 flex items-center justify-center">
            <div class="absolute inset-0 border-4 border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
            <img 
              src="/hamster-icon.png" 
              alt="Hamster" 
              class="w-12 h-12 object-contain animate-pulse rounded-full"
              style="filter: drop-shadow(0 0 15px rgba(59, 130, 246, 0.5)); clip-path: circle(50%)"
            />
        </div>
    {:else}
        <div class="grid gap-6">
            {#each campaigns as _, i (campaigns[i].id)}
                <div class="campaign-card bg-gray-900/40 border border-white/5 rounded-2xl p-6 hover:border-white/10 transition-all duration-500 group" in:fade>
                    <div class="flex justify-between items-start mb-6">
                        <div>
                            <div class="flex items-center gap-3">
                                <h3 class="text-lg font-bold text-gray-200">{campaigns[i].topic_data?.title || 'Đang phân tích chủ đề...'}</h3>
                                <span class="px-2 py-1 rounded-md bg-black/40 border border-white/5 text-[9px] font-mono text-gray-500">ID: {campaigns[i].id.slice(0,8)}</span>
                            </div>
                            <p class="text-sm text-gray-500 mt-1 line-clamp-1 italic">"{campaigns[i].source_input}"</p>
                        </div>
                        <div class="text-right text-[10px] font-bold uppercase tracking-widest text-gray-600 group-hover:text-blue-400 transition-colors">
                            {campaigns[i].status}
                        </div>
                    </div>

                    <ReviewGates bind:campaign={campaigns[i]} />
                </div>
            {:else}
                <div class="text-center py-20 bg-gray-900/20 rounded-3xl border border-dashed border-white/5">
                    <p class="text-gray-600 font-medium">Chưa có chiến dịch nào được khởi tạo.</p>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .campaign-card {
        background: radial-gradient(circle at top left, rgba(255,255,255,0.02), transparent);
    }
</style>
