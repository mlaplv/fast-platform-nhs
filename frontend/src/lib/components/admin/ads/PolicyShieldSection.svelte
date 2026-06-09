<script lang="ts">
  import { slide } from 'svelte/transition';
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ShieldAlert from "@lucide/svelte/icons/shield-alert";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import Info from "@lucide/svelte/icons/info";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";

  let {
    view = 'scan',
    selectedAdGroup = null,
    fAd = null,
    competitorUrl = '',
    adGroupKeywords = [],
    policyShieldResults = $bindable(null),
    policyShieldLoading = $bindable(false)
  } = $props<{
    view?: 'scan' | 'history';
    selectedAdGroup?: any;
    fAd?: any;
    competitorUrl?: string;
    adGroupKeywords?: string[];
    policyShieldResults?: any;
    policyShieldLoading?: boolean;
  }>();

  let policyHistory = $state<any[]>([]);
  let loadingHistory = $state(false);
  const nanobot = useNanobot();

  let debounceTimer: any = null;
  function debouncedScan() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      runPolicyShield();
    }, 600);
  }

  async function runPolicyShield() {
    const headlines = fAd?.headlines?.filter(Boolean) || [];
    const descriptions = fAd?.descriptions?.filter(Boolean) || [];
    const keywords = adGroupKeywords || [];
    const landing_page_url = fAd?.final_url || competitorUrl || "";

    if (headlines.length === 0 && descriptions.length === 0 && keywords.length === 0) {
      policyShieldResults = null;
      return;
    }

    policyShieldLoading = true;
    try {
      const res = await apiClient.post<any>("/api/v1/ads-protection/validate-policy-shield", {
        headlines,
        descriptions,
        keywords,
        landing_page_url,
        ad_group_id: selectedAdGroup?.resource_name || null
      });
      if (res) {
        policyShieldResults = res;
        fetchPolicyHistory();
      }
    } catch (err) {
      console.error("Policy shield scan failed:", err);
    } finally {
      policyShieldLoading = false;
    }
  }

  async function fetchPolicyHistory() {
    if (!selectedAdGroup?.resource_name) return;
    const agId = selectedAdGroup.resource_name.split('/').pop();
    loadingHistory = true;
    try {
      const res = await apiClient.get<any[]>(`/api/v1/ads-protection/ad-groups/${agId}/policy-history`);
      if (res) {
        policyHistory = res;
      }
    } catch (err) {
      console.error("Failed to fetch policy history:", err);
    } finally {
      loadingHistory = false;
    }
  }

  async function clearPolicyHistory() {
    if (!selectedAdGroup?.resource_name) return;
    const agId = selectedAdGroup.resource_name.split('/').pop();
    
    // Sử dụng modal xác nhận hệ thống thay vì confirm của trình duyệt
    const confirmed = await nanobot.showConfirm({
      title: "XÁC NHẬN XÓA LỊCH SỬ",
      message: "Sếp có chắc chắn muốn xóa toàn bộ lịch sử quét chính sách cho nhóm quảng cáo này?",
      confirmLabel: "XÓA NGAY",
      cancelLabel: "HỦY BỎ"
    });
    if (!confirmed) return;
    
    try {
      const res = await apiClient.delete<{success: boolean}>(`/api/v1/ads-protection/ad-groups/${agId}/policy-history`);
      if (res && res.success) {
        policyHistory = [];
        nanobot.showToast("Đã xóa lịch sử quét chính sách thành công.", "success");
      }
    } catch (err) {
      console.error("Failed to clear policy history:", err);
      nanobot.showToast("Không thể xóa lịch sử quét chính sách.", "error");
    }
  }

  $effect(() => {
    if (selectedAdGroup) {
      fetchPolicyHistory();
    }
  });

  $effect(() => {
    // Run scan whenever headlines, descriptions, keywords, final_url or competitorUrl change
    const _h = fAd?.headlines;
    const _d = fAd?.descriptions;
    const _k = adGroupKeywords;
    const _u = fAd?.final_url;
    const _cu = competitorUrl;

    debouncedScan();
  });
</script>

{#if view === 'scan'}
  {#if policyShieldResults || policyShieldLoading}
    <div class="border border-purple-500/20 bg-purple-950/10 p-4 font-mono text-[9px] relative overflow-hidden" transition:slide>
      <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-cyan-500 via-purple-500 to-rose-500"></div>
      
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          {#if policyShieldLoading}
            <RefreshCw size={12} class="text-cyan-400 animate-spin" />
            <span class="font-black text-cyan-400 tracking-wider">ĐANG QUÉT CHỐT CHẶN AI...</span>
          {:else}
            <span class="text-lg">🛡️</span>
            <span class="font-black text-white tracking-wider">LÁ CHẮN KIỂM DUYỆT AI (REAL-TIME SCAN)</span>
          {/if}
        </div>
        
        {#if !policyShieldLoading && policyShieldResults}
          <div class="flex items-center gap-1.5 px-2 py-0.5 border text-[8px] font-black tracking-widest
            {policyShieldResults.status === 'SAFE' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 
             policyShieldResults.status === 'WARNING' ? 'bg-amber-500/10 border-amber-500/20 text-amber-400' : 
             'bg-rose-500/10 border-rose-500/20 text-rose-400 animate-pulse'}"
          >
            {policyShieldResults.status === 'SAFE' ? 'AN TOÀN' : 
             policyShieldResults.status === 'WARNING' ? 'CẢNH BÁO' : 'NGUY HIỂM'}
          </div>
        {/if}
      </div>

      {#if !policyShieldLoading && policyShieldResults}
        <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
          <!-- 1. Sensitive Warnings -->
          {#if policyShieldResults.sensitive_warnings && policyShieldResults.sensitive_warnings.length > 0}
            <div class="border border-rose-500/20 bg-rose-500/5 p-2.5 space-y-1 text-left">
              <div class="flex items-center gap-1.5 text-rose-400 font-bold">
                <ShieldAlert size={12} />
                <span>Từ vựng Nhạy cảm ({policyShieldResults.sensitive_warnings.length})</span>
              </div>
              {#each policyShieldResults.sensitive_warnings as w}
                <div class="text-slate-300 pl-4 border-l border-rose-500/20 py-0.5 leading-relaxed text-[8px]">
                  Bị phát hiện từ <strong class="text-rose-300 underline font-black">"{w.matched_term}"</strong> trong <span class="text-slate-400 font-bold">{w.source}</span>.
                  <div class="text-slate-450 font-medium text-[8px] mt-0.5">Khuyên dùng: {w.suggestion}</div>
                </div>
              {/each}
            </div>
          {/if}

          <!-- 2. Landing Page Mismatches -->
          {#if policyShieldResults.landing_page_warnings && policyShieldResults.landing_page_warnings.length > 0}
            <div class="border border-amber-500/20 bg-amber-500/5 p-2.5 space-y-1 text-left">
              <div class="flex items-center gap-1.5 text-amber-400 font-bold">
                <AlertTriangle size={12} />
                <span>Lệch nội dung Trang đích ({policyShieldResults.landing_page_warnings.length})</span>
              </div>
              {#each policyShieldResults.landing_page_warnings as w}
                <div class="text-slate-300 pl-4 border-l border-amber-500/20 py-0.5 leading-relaxed text-[8px]">
                  {w.message}
                  <div class="text-slate-450 font-medium text-[8px] mt-0.5">Khuyên dùng: {w.suggestion}</div>
                </div>
              {/each}
            </div>
          {/if}

          <!-- 3. Low Search Volume Warnings -->
          {#if policyShieldResults.low_volume_warnings && policyShieldResults.low_volume_warnings.length > 0}
            <div class="border border-blue-500/20 bg-blue-500/5 p-2.5 space-y-1 text-left">
              <div class="flex items-center gap-1.5 text-blue-400 font-bold">
                <Info size={12} />
                <span>Nguy cơ Search Volume Thấp ({policyShieldResults.low_volume_warnings.length})</span>
              </div>
              {#each policyShieldResults.low_volume_warnings as w}
                <div class="text-slate-300 pl-4 border-l border-blue-500/20 py-0.5 leading-relaxed text-[8px]">
                  {w.message}
                  <div class="text-slate-450 font-medium text-[8px] mt-0.5">Khuyên dùng: {w.suggestion}</div>
                </div>
              {/each}
            </div>
          {/if}

          <!-- Safe state -->
          {#if (!policyShieldResults.sensitive_warnings || policyShieldResults.sensitive_warnings.length === 0) && 
               (!policyShieldResults.landing_page_warnings || policyShieldResults.landing_page_warnings.length === 0) && 
               (!policyShieldResults.low_volume_warnings || policyShieldResults.low_volume_warnings.length === 0)}
            <div class="flex items-center gap-2 text-emerald-400 py-1 font-bold">
              <ShieldCheck size={14} />
              <span>Chưa phát hiện rủi ro chính sách nào. Chiến dịch an toàn để chạy!</span>
            </div>
          {/if}
        </div>
      {:else if policyShieldLoading}
        <div class="py-4 text-center text-slate-500 italic">Đang quét toàn bộ ad copy và landing page...</div>
      {/if}
    </div>
  {/if}
{:else if view === 'history'}
  <div class="bg-black/40 border border-white/5 p-5 font-mono text-left">
    <div class="flex justify-between items-center mb-3">
      <span class="text-[10px] text-slate-400 font-black tracking-wider uppercase">LỊCH SỬ KIỂM DUYỆT CHÍNH SÁCH</span>
      <div class="flex items-center gap-2">
        <button 
          type="button"
          class="text-[8px] text-purple-400 hover:text-purple-300 underline font-black"
          onclick={fetchPolicyHistory}
        >
          LÀM MỚI
        </button>
        <span class="text-slate-600 text-[8px]">|</span>
        <button 
          type="button"
          class="text-[8px] text-rose-400 hover:text-rose-300 underline font-black"
          onclick={clearPolicyHistory}
        >
          XÓA LỊCH SỬ
        </button>
      </div>
    </div>

    {#if loadingHistory}
      <div class="py-4 text-center text-slate-500 italic text-[9px]">Đang tải lịch sử audit...</div>
    {:else if policyHistory.length > 0}
      <div class="space-y-2 max-h-48 overflow-y-auto pr-1">
        {#each policyHistory as log}
          <div class="border border-white/5 bg-black/40 p-2.5 flex justify-between items-center text-[9px]">
            <div>
              <div class="flex items-center gap-2">
                <span class="font-bold text-white">Điểm: {Math.round(log.score)}%</span>
                <span class="text-slate-500">|</span>
                <span class="text-slate-400">Vi phạm: {log.violations_count}</span>
              </div>
              <div class="text-slate-500 text-[8px] mt-0.5">
                Ngày quét: {log.created_at}
              </div>
            </div>
            <div class="flex gap-1.5 text-[8px]">
              <span class="px-1.5 py-0.5 bg-rose-500/10 text-rose-400 border border-rose-500/10">
                Nhạy cảm: {log.sensitive_count}
              </span>
              <span class="px-1.5 py-0.5 bg-amber-500/10 text-amber-400 border border-amber-500/10">
                Lệch URL: {log.mismatch_count}
              </span>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="text-center text-slate-600 italic py-4 text-[9px]">Chưa có lịch sử audit cho nhóm quảng cáo này.</div>
    {/if}
  </div>
{/if}
