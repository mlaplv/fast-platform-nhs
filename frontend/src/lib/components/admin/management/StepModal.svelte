<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, scale } from 'svelte/transition';

    let { show = $bindable(), campaign, stepId } = $props();
    
    let loading = $state(false);
    let editedData = $state('');

    const stepInfo = $derived({
        1: { title: 'Duyệt Vision (Keywords)', key: 'topic_data', color: 'text-cyan-400' },
        2: { title: 'Duyệt Assets (Images)', key: 'assets_data', color: 'text-blue-400' },
        3: { title: 'Duyệt Outline', key: 'outline_data', color: 'text-indigo-400' },
        4: { title: 'Duyệt Draft Content', key: 'draft_content', color: 'text-violet-400' },
        5: { title: 'Duyệt Final Content', key: 'final_content', color: 'text-fuchsia-400' },
        6: { title: 'Xuất bản & Media', key: 'final_html', color: 'text-emerald-400' }
    }[stepId] || { title: 'Review Gate', key: '', color: 'text-white' });

    onMount(() => {
        if (show === undefined) show = false;
        const rawData = campaign[stepInfo.key];
        editedData = typeof rawData === 'object' ? JSON.stringify(rawData, null, 2) : rawData || '';
    });

    async function approve() {
        loading = true;
        try {
            const data = stepInfo.key === 'draft_content' || stepInfo.key === 'final_html' 
                ? editedData 
                : JSON.parse(editedData);

            await fetch(`/api/v1/content/campaigns/${campaign.id}/approve`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ [stepInfo.key]: data })
            });
            show = false;
        } catch (e) {
            alert('Lỗi phê duyệt: ' + e.message);
        } finally {
            loading = false;
        }
    }
</script>

<div class="fixed inset-0 z-[var(--z-modal-overlay)] flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl" transition:fade>
    <div class="w-full max-w-2xl bg-[#0a0a0b]/90 border border-white/10 rounded-[2rem] shadow-[0_0_50px_rgba(0,0,0,0.5)] overflow-hidden relative" transition:scale>
        <!-- Top HUD Accent -->
        <div class="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-[1px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent"></div>

        <div class="p-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
            <h2 class="text-xl font-black text-white flex items-center gap-3 tracking-tight ">
                <span class="w-2 h-2 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.5)]"></span>
                <span class={stepInfo.color}>{stepInfo.title}</span>
            </h2>
            <button onclick={() => show = false} class="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-all">✕</button>
        </div>

        <div class="p-6">
            <div class="mb-4 flex items-baseline justify-between">
                <div class="text-[10px] text-white/30 tracking-[0.2em] font-black font-mono">Input_Dataset_Alpha</div>
                <div class="text-[9px] text-cyan-500/50 font-mono">STATUS: AWAITING_AUTHENTICATION</div>
            </div>
            
            <div class="relative group">
                <div class="absolute -inset-0.5 bg-gradient-to-b from-white/10 to-transparent rounded-xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"></div>
                <textarea 
                    bind:value={editedData}
                    class="w-full h-80 bg-black/60 border border-white/10 rounded-xl p-5 text-sm font-mono text-cyan-300/90 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 outline-none transition-all scrollbar-mission relative z-10"
                    placeholder="Load encryption module..."
                ></textarea>
            </div>

            <div class="mt-4 p-4 bg-cyan-500/[0.03] rounded-2xl border border-cyan-500/10 text-[11px] text-cyan-200/60 leading-relaxed font-medium">
                <span class="text-cyan-400 font-black">SYSTEM_ADVISORY:</span> Sau khi phê duyệt, Engine AI sẽ tiếp tục chu kỳ phân tích tiếp theo. Dữ liệu sẽ được mã hóa và truyền qua Secure Channel.
            </div>
        </div>

        <div class="p-6 bg-white/[0.01] border-t border-white/5 flex justify-end gap-3 items-center">
            <span class="text-[10px] font-mono text-white/20 mr-auto">Bypass_Safety_Check: [OFF]</span>
            
            <button 
                onclick={() => show = false}
                class="px-5 py-2.5 rounded-xl text-xs font-black text-white/40 hover:text-white hover:bg-white/5 transition-all tracking-widest"
            >
                Hủy bỏ
            </button>
            <button 
                onclick={approve}
                disabled={loading}
                class="relative px-8 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-black shadow-[0_0_20px_rgba(6,182,212,0.2)] transition-all disabled:opacity-50 group"
            >
                <div class="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl"></div>
                {loading ? 'AUTHENTICATING...' : 'PHÊ DUYỆT & TIẾP TỤC'}
            </button>
        </div>
    </div>
</div>

