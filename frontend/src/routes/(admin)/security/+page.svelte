<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, slide } from 'svelte/transition';
    import XohiLogo from '$lib/components/admin/XohiLogo.svelte';

    let logs = $state([]);
    let stats = $state({
        total_mutations_last_1000: 0,
        suspicious_events: 0,
        status: 'SECURE',
        active_guards: [],
        emergency_lockdown: false
    });
    let blacklist = $state([]);
    let drafts = $state([]);
    let loading = $state(true);
    let analyzing = $state(null); // ID of log being analyzed
    let analysisResult = $state(null);
    let viewSuspiciousOnly = $state(false);

    onMount(async () => {
        await refreshData();
        const interval = setInterval(refreshData, 30000); // Poll every 30s
        return () => clearInterval(interval);
    });

    async function refreshData() {
        try {
            const [logsRes, statsRes, blRes, draftRes] = await Promise.all([
                fetch(`/api/v1/security/audit-logs?limit=50&suspicious_only=${viewSuspiciousOnly}`),
                fetch(`/api/v1/security/stats`),
                fetch(`/api/v1/ads-protection/blacklist`),
                fetch(`/api/v1/security/drafts`)
            ]);
            logs = await logsRes.json();
            stats = await statsRes.json();
            blacklist = await blRes.json();
            drafts = await draftRes.json();
        } catch (e) {
            console.error('Security Monitor Error:', e);
        } finally {
            loading = false;
        }
    }

    async function handleDraft(id: string, action: 'approve' | 'reject') {
        try {
            const res = await fetch(`/api/v1/security/drafts/${id}/${action}`, { method: 'POST' });
            const data = await res.json();
            if (res.ok) {
                alert(data.message);
                await refreshData();
            } else {
                alert('Lỗi: ' + data.detail);
            }
        } catch (e) {
            alert('Lỗi kết nối server');
        }
    }

    async function analyzeWithAI(log: any) {
        analyzing = log.timestamp || log.id;
        analysisResult = null;
        try {
            const res = await fetch(`/api/v1/security/analyze-threat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(log)
            });
            analysisResult = await res.json();
        } catch (e) {
            console.error('AI Analysis failed:', e);
        } finally {
            analyzing = null;
        }
    }

    async function unblockIP(ip: string) {
        if (!confirm(`Gỡ chặn IP ${ip}?`)) return;
        try {
            await fetch(`/api/v1/ads-protection/blacklist/${ip}`, { method: 'DELETE' });
            await refreshData();
        } catch (e) {
            alert('Lỗi gỡ chặn IP');
        }
    }

    function getRiskColor(level: string) {
        switch (level) {
            case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/20';
            case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
            case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
            default: return 'text-blue-500 bg-blue-500/10 border-blue-500/20';
        }
    }
</script>

<div class="security-dashboard p-8 min-h-screen bg-[#020202] text-white font-sans">
    <header class="mb-10 flex justify-between items-start">
        <div>
            <div class="flex items-center gap-3 mb-2">
                <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-600/20">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04kM12 21a9.003 9.003 0 008.367-5.657l-1.907-1.017a7 7 0 11-12.92 0l-1.907 1.017A9.003 9.003 0 0012 21z"></path></svg>
                </div>
                <h1 class="text-3xl font-black tracking-tighter uppercase italic">Security Operations Center</h1>
            </div>
            <p class="text-gray-500 font-medium">Hệ thống giám sát và phản ứng tự động Elite V2.2</p>
        </div>
        
        <div class="flex gap-4">
            <div class="stat-card bg-gray-900/40 border border-white/5 rounded-xl px-4 py-2">
                <span class="text-[10px] text-gray-500 uppercase font-bold tracking-widest block">Trạng thái</span>
                <span class="text-sm font-bold {stats.status === 'SECURE' ? 'text-green-400' : 'text-red-400'}">{stats.status}</span>
            </div>
            {#if stats.emergency_lockdown}
                <div class="stat-card bg-red-600/20 border border-red-500/50 rounded-xl px-4 py-2 animate-pulse shadow-[0_0_20px_rgba(220,38,38,0.2)]">
                    <span class="text-[10px] text-red-400 uppercase font-black tracking-widest block">Thiết quân luật</span>
                    <span class="text-sm font-black text-red-500">READ-ONLY ACTIVE</span>
                </div>
            {/if}
            <div class="stat-card bg-gray-900/40 border border-white/5 rounded-xl px-4 py-2">
                <span class="text-[10px] text-gray-500 uppercase font-bold tracking-widest block">Cảnh báo (1k)</span>
                <span class="text-sm font-bold text-orange-400">{stats.suspicious_events}</span>
            </div>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Log Table -->
        <div class="lg:col-span-2 space-y-6">
            <div class="flex justify-between items-center">
                <h2 class="text-xl font-bold flex items-center gap-2">
                    <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    Audit Trail (Forensic)
                </h2>
                <button 
                    onclick={() => { viewSuspiciousOnly = !viewSuspiciousOnly; refreshData(); }}
                    class="px-4 py-1.5 rounded-full text-xs font-bold transition-all {viewSuspiciousOnly ? 'bg-red-600 text-white shadow-lg shadow-red-600/20' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}"
                >
                    {viewSuspiciousOnly ? 'Hiển thị tất cả' : 'Chỉ xem rủi ro'}
                </button>
            </div>

            <div class="bg-gray-900/20 rounded-2xl border border-white/5 overflow-hidden">
                <div class="max-h-[70vh] overflow-y-auto custom-scrollbar">
                    <table class="w-full text-left border-collapse">
                        <thead class="sticky top-0 bg-gray-950/80 backdrop-blur-md z-10">
                            <tr class="text-[10px] uppercase tracking-widest text-gray-500 border-b border-white/5">
                                <th class="px-6 py-4">Thời gian</th>
                                <th class="px-6 py-4">Action</th>
                                <th class="px-6 py-4">IP / Actor</th>
                                <th class="px-6 py-4">Status</th>
                                <th class="px-6 py-4 text-right">Ops</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-white/5">
                            {#each logs as log (log.timestamp || Math.random())}
                                <tr class="hover:bg-white/[0.02] transition-colors group">
                                    <td class="px-6 py-4 font-mono text-[11px] text-gray-500">
                                        {new Date(log.timestamp).toLocaleTimeString()}
                                    </td>
                                    <td class="px-6 py-4">
                                        <div class="flex flex-col">
                                            <span class="text-xs font-bold {log.suspicious ? 'text-red-400' : 'text-gray-200'}">{log.action}</span>
                                            {#if log.risk_reason}
                                                <span class="text-[10px] text-red-500 italic">{log.risk_reason}</span>
                                            {/if}
                                        </div>
                                    </td>
                                    <td class="px-6 py-4">
                                        <div class="flex flex-col">
                                            <span class="text-xs font-mono text-gray-400">{log.ip}</span>
                                            <span class="text-[10px] text-gray-600">ID: {log.actor}</span>
                                        </div>
                                    </td>
                                    <td class="px-6 py-4">
                                        <span class="text-[10px] font-bold px-2 py-0.5 rounded border {log.status < 400 ? 'border-green-500/20 text-green-500' : 'border-red-500/20 text-red-500'}">
                                            {log.status}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 text-right">
                                        <button 
                                            onclick={() => analyzeWithAI(log)}
                                            class="p-2 rounded-lg bg-white/5 hover:bg-blue-600/20 hover:text-blue-400 transition-all opacity-0 group-hover:opacity-100"
                                            title="AI Forensic"
                                        >
                                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path></svg>
                                        </button>
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Sidebar: Blacklist & AI Analysis -->
        <div class="space-y-8">
            <!-- AI Analysis Results -->
            {#if analyzing || analysisResult}
                <div class="ai-box bg-blue-600/5 border border-blue-500/20 rounded-2xl p-6 shadow-2xl shadow-blue-900/10" transition:slide>
                    <div class="flex items-center gap-3 mb-4">
                        <XohiLogo variant="simple" size={24} />
                        <h3 class="text-sm font-black uppercase tracking-tighter text-blue-400">AI Forensic Report</h3>
                    </div>
                    
                    {#if analyzing}
                        <div class="flex items-center gap-3 py-10 justify-center">
                            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.2s]"></div>
                            <div class="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:0.4s]"></div>
                        </div>
                    {:else if analysisResult}
                        <div class="space-y-4" in:fade>
                            <div class="flex justify-between items-center">
                                <span class="px-3 py-1 rounded-full text-[10px] font-black border {getRiskColor(analysisResult.risk_level)}">
                                    {analysisResult.risk_level}
                                </span>
                                <span class="text-[10px] font-bold {analysisResult.is_attack ? 'text-red-500' : 'text-green-500'}">
                                    {analysisResult.is_attack ? 'XÁC NHẬN TẤN CÔNG' : 'HÀNH VI HỢP LỆ'}
                                </span>
                            </div>
                            <p class="text-xs text-gray-300 leading-relaxed italic">"{analysisResult.reason}"</p>
                            <div class="pt-4 border-t border-white/5">
                                <span class="text-[10px] text-gray-500 uppercase font-bold block mb-1">Khuyến nghị</span>
                                <p class="text-xs font-bold text-blue-400">{analysisResult.recommended_action}</p>
                            </div>
                        </div>
                    {/if}
                </div>
            {/if}

            <!-- Pending Approvals (Martial Law) -->
            <div class="draft-box bg-orange-600/5 border border-orange-500/20 rounded-2xl p-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-sm font-black uppercase tracking-tighter text-orange-500 italic">Hàng chờ Phê duyệt (4-Eyes)</h3>
                    <span class="text-[10px] font-mono text-gray-600">{drafts.length} Req</span>
                </div>

                <div class="space-y-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                    {#each drafts as draft}
                        <div class="p-4 rounded-xl bg-black/40 border border-white/5 space-y-3" transition:slide>
                            <div class="flex justify-between items-start">
                                <div>
                                    <span class="text-[10px] font-black text-orange-400 uppercase tracking-tighter block">{draft.action}</span>
                                    <span class="text-[9px] text-gray-500 font-mono">By: {draft.proposed_by.slice(0,8)}...</span>
                                </div>
                                <span class="text-[9px] text-gray-600 italic">Target: {draft.target_model}</span>
                            </div>
                            
                            <div class="flex gap-2">
                                <button 
                                    onclick={() => handleDraft(draft.id, 'approve')}
                                    class="flex-1 py-1.5 rounded bg-green-600/20 text-green-500 text-[10px] font-bold hover:bg-green-600 hover:text-white transition-all uppercase tracking-widest"
                                >
                                    Phê duyệt
                                </button>
                                <button 
                                    onclick={() => handleDraft(draft.id, 'reject')}
                                    class="flex-1 py-1.5 rounded bg-red-600/20 text-red-500 text-[10px] font-bold hover:bg-red-600 hover:text-white transition-all uppercase tracking-widest"
                                >
                                    Từ chối
                                </button>
                            </div>
                        </div>
                    {:else}
                        <div class="text-center py-10 opacity-30 italic text-xs">Không có yêu cầu chờ duyệt.</div>
                    {/each}
                </div>
            </div>

            <!-- Active Blacklist -->
            <div class="blacklist-box bg-gray-900/40 border border-white/5 rounded-2xl p-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-sm font-black uppercase tracking-tighter text-red-500">Global Blacklist</h3>
                    <span class="text-[10px] font-mono text-gray-600">{blacklist.length} IPs</span>
                </div>
                
                <div class="space-y-3 max-h-[400px] overflow-y-auto custom-scrollbar">
                    {#each blacklist as item}
                        <div class="flex justify-between items-center p-3 rounded-xl bg-black/40 border border-white/5 group">
                            <div class="flex flex-col">
                                <span class="text-xs font-mono font-bold text-gray-300">{item.ip}</span>
                                <span class="text-[9px] text-gray-600 truncate max-w-[150px]">{item.reason}</span>
                            </div>
                            <button 
                                onclick={() => unblockIP(item.ip)}
                                class="text-gray-600 hover:text-green-400 transition-colors opacity-0 group-hover:opacity-100"
                                title="Unblock"
                            >
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04kM12 21a9.003 9.003 0 008.367-5.657l-1.907-1.017a7 7 0 11-12.92 0l-1.907 1.017A9.003 9.003 0 0012 21z"></path></svg>
                            </button>
                        </div>
                    {:else}
                        <div class="text-center py-10 opacity-30 italic text-xs">Chưa có IP nào bị chặn.</div>
                    {/each}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
    
    .security-dashboard {
        background: radial-gradient(circle at top right, rgba(37, 99, 235, 0.05), transparent 40%),
                    radial-gradient(circle at bottom left, rgba(220, 38, 38, 0.02), transparent 40%);
    }
</style>
