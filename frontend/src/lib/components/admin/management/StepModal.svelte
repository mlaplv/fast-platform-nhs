<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, scale } from 'svelte/transition';

    let { show = $bindable(), campaign, stepId } = $props();

    // R82: Safe initialization for bindable prop
    onMount(() => {
        if (show === undefined) show = false;
    });

    let loading = $state(false);
    let editedData = $state('');

    const stepInfo = $derived({
        1: { title: 'Duyệt Vision (Keywords)', key: 'topic_data' },
        2: { title: 'Duyệt Assets (Images)', key: 'assets_data' },
        3: { title: 'Duyệt Outline', key: 'outline_data' },
        4: { title: 'Duyệt Draft Content', key: 'draft_content' },
        5: { title: 'Xuất bản & Media', key: 'final_html' }
    }[stepId] || { title: 'Review', key: '' });

    onMount(() => {
        const rawData = campaign[stepInfo.key];
        editedData = typeof rawData === 'object' ? JSON.stringify(rawData, null, 2) : rawData;
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

<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" transition:fade>
    <div class="w-full max-w-2xl bg-gray-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden" transition:scale>
        <div class="p-6 border-b border-white/5 flex justify-between items-center bg-gray-800/50">
            <h2 class="text-xl font-bold text-white flex items-center gap-3">
                <span class="text-yellow-500">◈</span> {stepInfo.title}
            </h2>
            <button onclick={() => show = false} class="text-gray-400 hover:text-white">✕</button>
        </div>

        <div class="p-6">
            <div class="mb-4 text-xs text-gray-500 uppercase tracking-widest font-bold">Dữ liệu hiện tại</div>
            <textarea 
                bind:value={editedData}
                class="w-full h-64 bg-black/40 border border-white/10 rounded-xl p-4 text-sm font-mono text-blue-300 focus:border-blue-500/50 outline-none transition-all"
                placeholder="Nhập dữ liệu chỉnh sửa tại đây..."
            ></textarea>

            <div class="mt-4 p-4 bg-blue-500/10 rounded-xl border border-blue-500/20 text-xs text-blue-200 leading-relaxed">
                <strong>LƯU Ý:</strong> Sau khi nhấn Duyệt, hệ thống sẽ tự động kích hoạt Agent cho bước tiếp theo. Quá trình này chạy ngầm và sẽ cập nhật Progress Bar.
            </div>
        </div>

        <div class="p-6 bg-gray-800/30 border-t border-white/5 flex justify-end gap-3">
            <button 
                onclick={() => show = false}
                class="px-5 py-2 rounded-lg text-sm font-bold text-gray-400 hover:bg-white/5 transition-all"
            >
                HỦY
            </button>
            <button 
                onclick={approve}
                disabled={loading}
                class="px-8 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-lg text-sm font-bold shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50"
            >
                {loading ? 'ĐANG GỬI...' : 'DUYỆT & CHẠY TIẾP'}
            </button>
        </div>
    </div>
</div>
