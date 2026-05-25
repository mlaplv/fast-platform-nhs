<script lang="ts">
    import { onMount } from 'svelte';
    import { fade, slide } from 'svelte/transition';
    import XohiLogo from '$lib/components/admin/XohiLogo.svelte';

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

    interface AuditLog {
        id?: string;
        timestamp: string;
        action: string;
        actor: string;
        ip: string;
        suspicious: boolean;
        ms: number;
        status?: number;
        risk_reason?: string;
    }

    interface BlacklistIP {
        ip: string;
        reason: string;
    }

    interface SecurityDraft {
        id: string;
        requested_by_email: string;
        action_type: string;
        description: string;
        payload: Record<string, unknown>;
        created_at: string;
        action: string;
        proposed_by: string;
        target_model: string;
    }

    interface AIAnalysis {
        risk_level: string;
        is_attack: boolean;
        reason: string;
        recommended_action: string;
    }

    let logs = $state<AuditLog[]>([]);
    let stats = $state({
        total_mutations_last_1000: 0,
        suspicious_events: 0,
        status: 'SECURE',
        active_guards: [],
        emergency_lockdown: false
    });
    let blacklist = $state<BlacklistIP[]>([]);
    let drafts = $state<SecurityDraft[]>([]);
    let containers = $state<ContainerInfo[]>([]);
    let loading = $state(true);
    let analyzing = $state<string | null>(null); // ID of log being analyzed
    let analysisResult = $state<AIAnalysis | null>(null);
    let viewSuspiciousOnly = $state(false);
    let opLoading = $state<string | null>(null); // Name of container being operated on

    onMount(() => {
        refreshData();
        const interval = setInterval(refreshData, 30000); // Poll every 30s
        return () => clearInterval(interval);
    });

    async function refreshData() {
        try {
            const [logsRes, statsRes, blRes, draftRes, containerRes] = await Promise.all([
                fetch(`/api/v1/security/audit-logs?limit=50&suspicious_only=${viewSuspiciousOnly}`),
                fetch(`/api/v1/security/stats`),
                fetch(`/api/v1/ads-protection/blacklist`),
                fetch(`/api/v1/security/drafts`),
                fetch(`/api/v1/security/containers`)
            ]);
            logs = await logsRes.json();
            stats = await statsRes.json();
            blacklist = await blRes.json();
            drafts = await draftRes.json();
            containers = await containerRes.json();
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

    async function handleContainerAction(containerName: string, action: 'start' | 'stop' | 'restart') {
        const actionLabel = action === 'start' ? 'BẬT (ENABLE)' : action === 'stop' ? 'TẮT (DISABLE)' : 'KHỞI ĐỘNG LẠI (RESTART)';
        if (!confirm(`[SOC WARNING] Xác nhận thực hiện thao tác ${actionLabel} trên container ${containerName}?`)) return;
        
        opLoading = containerName;
        try {
            const res = await fetch(`/api/v1/security/containers/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ container_name: containerName, action })
            });
            const data = await res.json();
            alert(data.message);
            await refreshData();
        } catch (e) {
            alert('Lỗi gửi lệnh điều khiển container');
        } finally {
            opLoading = null;
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
                <h1 class="text-3xl font-black tracking-tighter italic">Security Operations Center</h1>
            </div>
            <p class="text-gray-500 font-medium">Hệ thống giám sát và phản ứng tự động Elite V2.2</p>
        </div>
        
        <div class="flex gap-4">
            <div class="stat-card bg-gray-900/40 border border-white/5 rounded-xl px-4 py-2">
                <span class="text-[10px] text-gray-500 font-bold tracking-widest block">Trạng thái</span>
                <span class="text-sm font-bold {stats.status === 'SECURE' ? 'text-green-400' : 'text-red-400'}">{stats.status}</span>
            </div>
            {#if stats.emergency_lockdown}
                <div class="stat-card bg-red-600/20 border border-red-500/50 rounded-xl px-4 py-2 animate-pulse shadow-[0_0_20px_rgba(220,38,38,0.2)]">
                    <span class="text-[10px] text-red-400 font-black tracking-widest block">Thiết quân luật</span>
                    <span class="text-sm font-black text-red-500">READ-ONLY ACTIVE</span>
                </div>
            {/if}
            <div class="stat-card bg-gray-900/40 border border-white/5 rounded-xl px-4 py-2">
                <span class="text-[10px] text-gray-500 font-bold tracking-widest block">Cảnh báo (1k)</span>
                <span class="text-sm font-bold text-orange-400">{stats.suspicious_events}</span>
            </div>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Main Log Table -->
        <div class="lg:col-span-2 space-y-8">
            <!-- Live Core Infrastructure (SOC Container Monitor) -->
            <div class="mb-8 space-y-4">
                <div class="flex justify-between items-center">
                    <h2 class="text-xl font-bold flex items-center gap-2">
                        <span class="w-2.5 h-2.5 bg-green-500 rounded-full animate-ping"></span>
                        <span class="w-2.5 h-2.5 bg-green-500 rounded-full absolute"></span>
                        Hạ tầng & Container Resources (SOC Live Stats)
                    </h2>
                    <span class="text-xs text-gray-500 font-mono tracking-widest">{containers.length} Node(s) Active</span>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {#each containers as c}
                        <div class="bg-white/[0.02] border border-white/5 rounded-2xl p-5 hover:bg-white/[0.04] transition-all duration-300 relative overflow-hidden group">
                            {#if opLoading === c.name}
                                <div class="absolute inset-0 bg-black/85 backdrop-blur-sm z-20 flex flex-col items-center justify-center gap-3" transition:fade>
                                    <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                    <span class="text-[10px] text-blue-400 font-black tracking-widest uppercase">Đang điều khiển...</span>
                                </div>
                            {/if}

                            <!-- Card Header -->
                            <div class="flex justify-between items-start mb-4">
                                <div class="flex flex-col gap-1">
                                    <div class="flex items-center gap-2">
                                        <span class="w-2 h-2 rounded-full {
                                            c.state === 'running' ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' :
                                            c.state === 'exited' ? 'bg-orange-500 shadow-[0_0_10px_#f97316]' : 'bg-red-500 shadow-[0_0_10px_#ef4444]'
                                        }"></span>
                                        <span class="text-xs font-mono font-black text-gray-200">{c.name}</span>
                                    </div>
                                    <span class="text-[9px] text-gray-500 truncate max-w-[180px]">{c.image}</span>
                                </div>

                                <!-- Professional Operations Control -->
                                <div class="flex items-center gap-1.5 opacity-45 group-hover:opacity-100 transition-opacity">
                                    {#if c.state === 'running'}
                                        <button 
                                            onclick={() => handleContainerAction(c.name, 'restart')}
                                            class="w-6 h-6 rounded bg-blue-500/10 hover:bg-blue-600 hover:text-white text-blue-400 transition-all flex items-center justify-center cursor-pointer"
                                            title="Khởi động lại (Restart)"
                                        >
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H12v4"></path></svg>
                                        </button>
                                        <button 
                                            onclick={() => handleContainerAction(c.name, 'stop')}
                                            class="w-6 h-6 rounded bg-red-500/10 hover:bg-red-600 hover:text-white text-red-400 transition-all flex items-center justify-center cursor-pointer"
                                            title="Tắt (Disable)"
                                        >
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"></path></svg>
                                        </button>
                                    {:else}
                                        <button 
                                            onclick={() => handleContainerAction(c.name, 'start')}
                                            class="w-6 h-6 rounded bg-green-500/10 hover:bg-green-600 hover:text-white text-green-400 transition-all flex items-center justify-center cursor-pointer"
                                            title="Bật (Enable)"
                                        >
                                            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path></svg>
                                        </button>
                                    {/if}
                                </div>
                            </div>

                            <!-- Metrics Grid -->
                            <div class="grid grid-cols-3 gap-2 border-t border-white/5 pt-3">
                                <div class="flex flex-col">
                                    <span class="text-[9px] text-gray-500 font-bold block mb-1">CPU</span>
                                    <span class="text-xs font-bold text-gray-300">{c.cpu}</span>
                                    <div class="w-full bg-white/5 h-1 rounded-full mt-1.5 overflow-hidden">
                                        <div class="bg-blue-500 h-full rounded-full transition-all duration-500" style="width: {c.cpu}"></div>
                                    </div>
                                </div>

                                <div class="flex flex-col col-span-2">
                                    <div class="flex justify-between">
                                        <span class="text-[9px] text-gray-500 font-bold block">RAM (Sức chứa)</span>
                                        <span class="text-[9px] font-mono {
                                            parseFloat(c.mem_perc) > 85 ? 'text-red-400 font-black animate-pulse' :
                                            parseFloat(c.mem_perc) > 70 ? 'text-orange-400 font-bold' : 'text-green-400'
                                        }">{c.mem_perc}</span>
                                    </div>
                                    <span class="text-xs font-bold text-gray-300 mt-1 truncate">{c.mem_usage}</span>
                                    <div class="w-full bg-white/5 h-1 rounded-full mt-1.5 overflow-hidden">
                                        <div class="h-full rounded-full transition-all duration-500 {
                                            parseFloat(c.mem_perc) > 85 ? 'bg-red-500' :
                                            parseFloat(c.mem_perc) > 70 ? 'bg-orange-500' : 'bg-green-500'
                                        }" style="width: {c.mem_perc}"></div>
                                    </div>
                                </div>
                            </div>

                            <!-- ID / Status footer -->
                            <div class="flex justify-between items-center mt-3 pt-2 border-t border-white/5 text-[9px] text-gray-600 font-mono">
                                <span>ID: {c.id ? c.id.slice(0, 12) : 'N/A'}</span>
                                <span class="capitalize">{c.status || 'Offline'}</span>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Audit Trail section -->
            <div class="flex justify-between items-center mt-8">
                <h2 class="text-xl font-bold flex items-center gap-2">
                    <span class="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse"></span>
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
                            <tr class="text-[10px] tracking-widest text-gray-500 border-b border-white/5">
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
                                        <span class="text-[10px] font-bold px-2 py-0.5 rounded border {(log.status ?? 200) < 400 ? 'border-green-500/20 text-green-500' : 'border-red-500/20 text-red-500'}">
                                            {log.status ?? 200}
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
                        <h3 class="text-sm font-black tracking-tighter text-blue-400">AI Forensic Report</h3>
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
                                <span class="text-[10px] text-gray-500 font-bold block mb-1">Khuyến nghị</span>
                                <p class="text-xs font-bold text-blue-400">{analysisResult.recommended_action}</p>
                            </div>
                        </div>
                    {/if}
                </div>
            {/if}

            <!-- Pending Approvals (Martial Law) -->
            <div class="draft-box bg-orange-600/5 border border-orange-500/20 rounded-2xl p-6">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-sm font-black tracking-tighter text-orange-500 italic">Hàng chờ Phê duyệt (4-Eyes)</h3>
                    <span class="text-[10px] font-mono text-gray-600">{drafts.length} Req</span>
                </div>

                <div class="space-y-4 max-h-[300px] overflow-y-auto custom-scrollbar">
                    {#each drafts as draft}
                        <div class="p-4 rounded-xl bg-black/40 border border-white/5 space-y-3" transition:slide>
                            <div class="flex justify-between items-start">
                                <div>
                                    <span class="text-[10px] font-black text-orange-400 tracking-tighter block">{draft.action}</span>
                                    <span class="text-[9px] text-gray-500 font-mono">By: {draft.proposed_by.slice(0,8)}...</span>
                                </div>
                                <span class="text-[9px] text-gray-600 italic">Target: {draft.target_model}</span>
                            </div>
                            
                            <div class="flex gap-2">
                                <button 
                                    onclick={() => handleDraft(draft.id, 'approve')}
                                    class="flex-1 py-1.5 rounded bg-green-600/20 text-green-500 text-[10px] font-bold hover:bg-green-600 hover:text-white transition-all tracking-widest"
                                >
                                    Phê duyệt
                                </button>
                                <button 
                                    onclick={() => handleDraft(draft.id, 'reject')}
                                    class="flex-1 py-1.5 rounded bg-red-600/20 text-red-500 text-[10px] font-bold hover:bg-red-600 hover:text-white transition-all tracking-widest"
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
                    <h3 class="text-sm font-black tracking-tighter text-red-500">Global Blacklist</h3>
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
