<script lang="ts">
  import { slide } from 'svelte/transition';
  import Info from "@lucide/svelte/icons/info";
  import AlertTriangle from "@lucide/svelte/icons/alert-triangle";
  import RefreshCw from "@lucide/svelte/icons/refresh-cw";
  import { apiClient } from "$lib/utils/apiClient";

  let {
    selectedCampaign = null
  } = $props<{
    selectedCampaign: any;
  }>();

  let showPMaxTooltip = $state(false);
  let newPMaxName = $state('');
  let pmaxBudget = $state(150000);
  let upgradingToPMax = $state(false);
  let upgradeError = $state<string | null>(null);
  let upgradeSuccessMessage = $state<string | null>(null);

  // AI Max Human Edit States
  let pmaxAssetsLoaded = $state(false);
  let loadingPMaxAssets = $state(false);
  let pmaxHeadlines = $state<string[]>([]);
  let pmaxDescriptions = $state<string[]>([]);
  let pmaxSearchThemes = $state<string[]>([]);
  let pmaxLandingPageUrl = $state('');
  let pmaxMarketingImages = $state<string[]>([]);
  let pmaxSquareImages = $state<string[]>([]);
  let pmaxLogoImages = $state<string[]>([]);
  let validationError = $state<string | null>(null);
  let userConfirmedReview = $state(false);

  // Auto-reset review state when campaign changes
  $effect(() => {
    if (selectedCampaign) {
      pmaxAssetsLoaded = false;
      userConfirmedReview = false;
      upgradeSuccessMessage = null;
      upgradeError = null;
      validationError = null;
      pmaxMarketingImages = [];
      pmaxSquareImages = [];
      pmaxLogoImages = [];
    }
  });

  async function loadAIProposedAssets() {
    if (!selectedCampaign?.resource_name) return;
    const campId = selectedCampaign.resource_name.split('/').pop();
    loadingPMaxAssets = true;
    upgradeError = null;
    upgradeSuccessMessage = null;
    validationError = null;
    try {
      const res = await apiClient.get<any>(`/api/v1/ads-protection/campaigns/${campId}/preview-aimax-assets`);
      if (res) {
        pmaxHeadlines = res.headlines || [];
        pmaxDescriptions = res.descriptions || [];
        pmaxSearchThemes = res.search_themes || [];
        pmaxLandingPageUrl = res.landing_page_url || '';
        pmaxMarketingImages = res.marketing_images || [];
        pmaxSquareImages = res.square_marketing_images || [];
        pmaxLogoImages = res.logo_images || [];
        pmaxAssetsLoaded = true;
      }
    } catch (err: any) {
      upgradeError = err?.message || "Lỗi khi tải nội dung đề xuất từ AI.";
    } finally {
      loadingPMaxAssets = false;
    }
  }

  async function upgradeToPMax() {
    if (!selectedCampaign?.resource_name) return;
    const campId = selectedCampaign.resource_name.split('/').pop();
    upgradingToPMax = true;
    upgradeError = null;
    upgradeSuccessMessage = null;
    try {
      const payload: any = {
        dsa_campaign_id: campId,
        daily_budget_vnd: pmaxBudget,
        name: newPMaxName || `${selectedCampaign.name} - AI Max (PMax)`
      };
      
      payload.assets = {
        headlines: pmaxHeadlines.filter(h => h.trim() !== ''),
        descriptions: pmaxDescriptions.filter(d => d.trim() !== ''),
        search_themes: pmaxSearchThemes.filter(t => t.trim() !== ''),
        landing_page_url: pmaxLandingPageUrl,
        marketing_images: pmaxMarketingImages.filter(img => img.trim() !== ''),
        square_marketing_images: pmaxSquareImages.filter(img => img.trim() !== ''),
        logo_images: pmaxLogoImages.filter(img => img.trim() !== '')
      };

      const res = await apiClient.post<any>(`/api/v1/ads-protection/campaigns/${campId}/upgrade-to-aimax`, payload);
      if (res && res.success) {
        upgradeSuccessMessage = res.message;
      } else {
        upgradeError = res?.message || "Lỗi nâng cấp chiến dịch không xác định.";
      }
    } catch (err: any) {
      upgradeError = err?.message || "Lỗi kết nối khi nâng cấp chiến dịch.";
    } finally {
      upgradingToPMax = false;
    }
  }

  function validateAndUpgrade() {
    validationError = null;
    if (!pmaxAssetsLoaded) { validationError = "Vui lòng xem và biên tập nội dung AI đề xuất trước."; return; }
    if (!userConfirmedReview) { validationError = "Bạn phải tích chọn xác nhận đã phê duyệt nội dung."; return; }

    const activeHeadlines = pmaxHeadlines.filter(h => h.trim() !== '');
    const activeDescriptions = pmaxDescriptions.filter(d => d.trim() !== '');
    const activeMarketing = pmaxMarketingImages.filter(img => img.trim() !== '');
    const activeSquare = pmaxSquareImages.filter(img => img.trim() !== '');
    const activeLogos = pmaxLogoImages.filter(img => img.trim() !== '');
    
    if (activeHeadlines.length < 3) { validationError = "Cần tối thiểu 3 tiêu đề (headlines)."; return; }
    if (activeHeadlines.length > 15) { validationError = "Tối đa 15 tiêu đề."; return; }
    if (activeDescriptions.length < 2) { validationError = "Cần tối thiểu 2 mô tả (descriptions)."; return; }
    if (activeDescriptions.length > 5) { validationError = "Tối đa 5 mô tả."; return; }
    
    for (let h of activeHeadlines) {
      if (h.length > 30) { validationError = `Tiêu đề "${h}" vượt quá giới hạn 30 ký tự (hiện tại: ${h.length}).`; return; }
    }
    for (let d of activeDescriptions) {
      if (d.length > 90) { validationError = `Mô tả "${d}" vượt quá giới hạn 90 ký tự (hiện tại: ${d.length}).`; return; }
    }
    if (!pmaxLandingPageUrl || !pmaxLandingPageUrl.startsWith('http')) { validationError = "Đường dẫn trang đích không hợp lệ."; return; }
    if (activeMarketing.length < 1) { validationError = "Cần tối thiểu 1 hình ảnh ngang (Landscape Marketing Image) chuẩn 1.91:1."; return; }
    if (activeSquare.length < 1) { validationError = "Cần tối thiểu 1 hình ảnh vuông (Square Marketing Image) chuẩn 1:1."; return; }
    if (activeLogos.length < 1) { validationError = "Cần tối thiểu 1 biểu trưng vuông (Logo Image) chuẩn 1:1."; return; }
    upgradeToPMax();
  }

  let uploadingImage = $state(false);
  let targetUploadIndex = $state<number | null>(null);

  async function uploadImage(e: Event, type: 'marketing' | 'square' | 'logo') {
    const target = e.target as HTMLInputElement;
    if (!target.files?.[0]) return;
    uploadingImage = true;
    try {
      const fd = new FormData();
      fd.append('data', target.files[0]);
      const res = await apiClient.upload<{ data: { file_path: string } }>('/api/v1/media', fd);
      if (res?.data?.file_path) {
        const path = res.data.file_path;
        const idx = targetUploadIndex;
        if (type === 'marketing') {
          if (idx !== null) pmaxMarketingImages[idx] = path;
          else pmaxMarketingImages = [...pmaxMarketingImages, path];
        } else if (type === 'square') {
          if (idx !== null) pmaxSquareImages[idx] = path;
          else pmaxSquareImages = [...pmaxSquareImages, path];
        } else {
          if (idx !== null) pmaxLogoImages[idx] = path;
          else pmaxLogoImages = [...pmaxLogoImages, path];
        }
      }
    } catch (err: any) {
      validationError = "Lỗi tải ảnh: " + (err?.message || "");
    } finally {
      uploadingImage = false;
      targetUploadIndex = null;
      target.value = '';
    }
  }

  function triggerUpload(type: 'marketing' | 'square' | 'logo', idx?: number) {
    targetUploadIndex = idx !== undefined ? idx : null;
    document.getElementById(`upload-${type}`)?.click();
  }
</script>

<svelte:window onclick={() => showPMaxTooltip = false} />

<div class="bg-black/60 border border-purple-500/30 p-5 font-mono text-left relative overflow-visible">
  <div class="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-purple-500 to-rose-500"></div>
  <div class="flex justify-between items-center mb-3">
    <div class="flex items-center gap-2">
      <span class="text-lg">🚀</span>
      <span class="font-black text-white text-xs tracking-wider uppercase">NÂNG CẤP CHIẾN DỊCH LÊN AI MAX (PMAX)</span>
      <div class="relative inline-flex items-center">
        <button type="button" class="cursor-pointer inline-flex items-center focus:outline-none" onclick={(e) => { e.stopPropagation(); showPMaxTooltip = !showPMaxTooltip; }}>
          <Info size={12} class="text-purple-400 hover:text-purple-300 transition-colors" />
        </button>
        {#if showPMaxTooltip}
          <div class="absolute top-full left-0 mt-2 w-72 bg-slate-950 border border-purple-500/30 p-3 rounded shadow-2xl z-50 text-[9px] text-slate-300 leading-normal whitespace-normal">
            <span class="text-purple-400 font-bold block mb-1.5 uppercase border-b border-purple-500/20 pb-1">Quy trình nâng cấp tự động (5 Bước):</span>
            <ul class="space-y-1.5 list-none pl-0">
              <li><strong class="text-white">1. Tạm dừng DSA cũ:</strong> Tránh thầu chéo, dồn ngân sách sang chiến dịch mới.</li>
              <li><strong class="text-white">2. Tạo Ngân sách mới:</strong> Thiết lập ngân sách độc lập cho AI Max.</li>
              <li><strong class="text-white">3. Tạo Chiến dịch PMax:</strong> Tự động cấu hình tuân thủ chính sách quảng cáo chính trị EU & tắt quy định Brand Guidelines (cho phép đẩy lên mà chưa bắt buộc logo/tên DN).</li>
              <li><strong class="text-white">4. Sinh Asset Group:</strong> Tạo 5 headlines & 5 descriptions bằng AI đã rà quét lọc bỏ hoạt chất nhạy cảm y tế.</li>
              <li><strong class="text-white">5. Đẩy Search Themes:</strong> Đẩy thẳng 10 tín hiệu chủ đề tìm kiếm lên Google Ads để định hướng thuật toán.</li>
            </ul>
          </div>
        {/if}
      </div>
    </div>
    <span class="px-2 py-0.5 border border-purple-500/20 bg-purple-500/10 text-[8px] font-black text-purple-300">
      GOOGLE ADS V24 COMPLIANT
    </span>
  </div>

  <p class="text-[9px] text-slate-400 mb-4 leading-relaxed">
    Tự động dừng chiến dịch DSA hiện tại, sinh Asset Group chất lượng cao (5 tiêu đề, 5 mô tả đạt chuẩn ký tự, loại bỏ hoạt chất nhạy cảm y tế) và đẩy 10 Search Themes ngữ cảnh lên Google Ads.
  </p>

  {#if selectedCampaign}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
      <div>
        <span class="block text-[8px] text-slate-500 font-black tracking-widest uppercase mb-1">TÊN CHIẾN DỊCH AI MAX MỚI</span>
        <input 
          type="text" 
          placeholder="{selectedCampaign.name} - AI Max (PMax)"
          bind:value={newPMaxName} 
          class="w-full bg-black/80 border border-white/10 p-2 text-xs text-white outline-none focus:border-purple-400/50" 
        />
      </div>
      <div>
        <span class="block text-[8px] text-slate-500 font-black tracking-widest uppercase mb-1">NGÂN SÁCH MỖI NGÀY (VNĐ)</span>
        <input 
          type="number" 
          bind:value={pmaxBudget} 
          class="w-full bg-black/80 border border-white/10 p-2 text-xs text-white outline-none focus:border-purple-400/50" 
        />
      </div>
    </div>

    {#if !pmaxAssetsLoaded}
      <button 
        type="button"
        class="w-full py-2.5 bg-purple-900/30 border border-purple-500/30 hover:bg-purple-800/40 text-purple-300 text-[10px] font-black tracking-widest transition-all flex items-center justify-center gap-2 mb-4"
        onclick={loadAIProposedAssets}
        disabled={loadingPMaxAssets}
      >
        {#if loadingPMaxAssets}
          <RefreshCw size={12} class="animate-spin text-purple-400" />
          <span>ĐANG PHÂN TÍCH VÀ SOẠN THẢO BẰNG AI...</span>
        {:else}
          <span>BƯỚC 1: XEM & BIÊN TẬP NỘI DUNG DO AI SOẠN THẢO (BẮT BUỘC)</span>
        {/if}
      </button>
    {:else}
      <div class="border border-purple-500/20 bg-purple-950/5 p-4 mb-4 space-y-4 text-left animate-fade-in">
        <span class="block text-[9px] text-purple-400 font-black tracking-widest uppercase border-b border-purple-500/20 pb-1.5">BIÊN TẬP NỘI DUNG CHIẾN DỊCH (HUMAN-IN-THE-LOOP)</span>
        
        <!-- Headlines Editor -->
        <div class="space-y-2">
          <div class="flex justify-between items-center">
            <span class="block text-[8px] text-slate-400 font-bold uppercase tracking-wider">Tiêu đề (Headlines) - Cần 3 đến 15:</span>
            <button 
              type="button" 
              class="text-[8px] text-purple-400 hover:text-purple-300 font-bold"
              onclick={() => { if (pmaxHeadlines.length < 15) pmaxHeadlines = [...pmaxHeadlines, ''] }}
            >
              + THÊM TIÊU ĐỀ
            </button>
          </div>
          <div class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {#each pmaxHeadlines as headline, idx}
              <div class="flex gap-2 items-center">
                <span class="text-[8px] text-slate-500 w-4">{idx + 1}.</span>
                <input 
                  type="text" 
                  bind:value={pmaxHeadlines[idx]} 
                  placeholder="Nhập tiêu đề (tối đa 30 ký tự)..."
                  class="flex-1 bg-black/80 border border-white/10 p-1.5 text-xs text-white outline-none focus:border-purple-400/50" 
                />
                <span class="text-[8px] shrink-0 {headline.length > 30 ? 'text-rose-500 font-black' : 'text-slate-500'}">
                  {headline.length}/30
                </span>
                <button 
                  type="button" 
                  class="text-rose-450 hover:text-rose-300 text-[10px]"
                  onclick={() => { pmaxHeadlines = pmaxHeadlines.filter((_, i) => i !== idx) }}
                >
                  ×
                </button>
              </div>
            {/each}
          </div>
        </div>

        <!-- Descriptions Editor -->
        <div class="space-y-2">
          <div class="flex justify-between items-center">
            <span class="block text-[8px] text-slate-400 font-bold uppercase tracking-wider">Mô tả (Descriptions) - Cần 2 đến 5:</span>
            <button 
              type="button" 
              class="text-[8px] text-purple-400 hover:text-purple-300 font-bold"
              onclick={() => { if (pmaxDescriptions.length < 5) pmaxDescriptions = [...pmaxDescriptions, ''] }}
            >
              + THÊM MÔ TẢ
            </button>
          </div>
          <div class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {#each pmaxDescriptions as desc, idx}
              <div class="flex gap-2 items-center">
                <span class="text-[8px] text-slate-500 w-4">{idx + 1}.</span>
                <input 
                  type="text" 
                  bind:value={pmaxDescriptions[idx]} 
                  placeholder="Nhập mô tả (tối đa 90 ký tự)..."
                  class="flex-1 bg-black/80 border border-white/10 p-1.5 text-xs text-white outline-none focus:border-purple-400/50" 
                />
                <span class="text-[8px] shrink-0 {desc.length > 90 ? 'text-rose-500 font-black' : 'text-slate-500'}">
                  {desc.length}/90
                </span>
                <button 
                  type="button" 
                  class="text-rose-450 hover:text-rose-300 text-[10px]"
                  onclick={() => { pmaxDescriptions = pmaxDescriptions.filter((_, i) => i !== idx) }}
                >
                  ×
                </button>
              </div>
            {/each}
          </div>
        </div>

        <!-- Search Themes Editor -->
        <div class="space-y-2">
          <div class="flex justify-between items-center">
            <span class="block text-[8px] text-slate-400 font-bold uppercase tracking-wider">Chủ đề Tìm kiếm (Search Themes) - Tối đa 10:</span>
            <button 
              type="button" 
              class="text-[8px] text-purple-400 hover:text-purple-300 font-bold"
              onclick={() => { if (pmaxSearchThemes.length < 10) pmaxSearchThemes = [...pmaxSearchThemes, ''] }}
            >
              + THÊM CHỦ ĐỀ
            </button>
          </div>
          <div class="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {#each pmaxSearchThemes as theme, idx}
              <div class="flex gap-2 items-center">
                <span class="text-[8px] text-slate-500 w-4">{idx + 1}.</span>
                <input 
                  type="text" 
                  bind:value={pmaxSearchThemes[idx]} 
                  placeholder="Nhập từ khóa chủ đề tìm kiếm..."
                  class="flex-1 bg-black/80 border border-white/10 p-1.5 text-xs text-white outline-none focus:border-purple-400/50" 
                />
                <button 
                  type="button" 
                  class="text-rose-450 hover:text-rose-300 text-[10px]"
                  onclick={() => { pmaxSearchThemes = pmaxSearchThemes.filter((_, i) => i !== idx) }}
                >
                  ×
                </button>
              </div>
            {/each}
          </div>
        </div>

        <!-- Image Assets Editor -->
        <input type="file" id="upload-marketing" accept="image/*" class="hidden" onchange={(e) => uploadImage(e, 'marketing')} />
        <input type="file" id="upload-square" accept="image/*" class="hidden" onchange={(e) => uploadImage(e, 'square')} />
        <input type="file" id="upload-logo" accept="image/*" class="hidden" onchange={(e) => uploadImage(e, 'logo')} />

        <div class="space-y-3 border-t border-purple-500/20 pt-3 text-[8px]">
          <div class="flex justify-between items-center">
            <span class="block text-purple-400 font-bold uppercase tracking-wider">Hình ảnh Chiến dịch (PMax Image Assets):</span>
            {#if uploadingImage}
              <span class="text-purple-300 animate-pulse font-bold text-[8px]">ĐANG TẢI ẢNH LÊN...</span>
            {/if}
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
            <!-- Landscape -->
            <div class="space-y-1.5 border border-white/5 p-1.5 bg-black/40">
              <div class="flex justify-between items-center border-b border-white/10 pb-1 mb-1 font-bold">
                <span>ẢNH NGANG (1.91:1)</span>
                <div class="flex gap-1.5">
                  <button type="button" class="text-purple-400 hover:text-purple-300" onclick={() => pmaxMarketingImages = [...pmaxMarketingImages, '']}>+ URL</button>
                  <button type="button" class="text-purple-400 hover:text-purple-300 border-l border-white/10 pl-1.5" onclick={() => triggerUpload('marketing')}>+ TẢI LÊN</button>
                </div>
              </div>
              {#each pmaxMarketingImages as img, idx}
                <div class="flex gap-1.5 items-center">
                  <input type="text" bind:value={pmaxMarketingImages[idx]} placeholder="URL..." class="flex-1 bg-black/80 border border-white/10 p-1 text-[9px] text-white outline-none focus:border-purple-400/50" />
                  <button type="button" class="text-purple-400 text-[8px] hover:text-purple-300" onclick={() => triggerUpload('marketing', idx)} title="Tải ảnh khác thay thế">THAY</button>
                  <button type="button" class="text-rose-450 hover:text-rose-300 text-[10px]" onclick={() => pmaxMarketingImages = pmaxMarketingImages.filter((_, i) => i !== idx)}>×</button>
                </div>
                {#if img && (img.startsWith('http') || img.startsWith('/'))}
                  <div class="relative aspect-[1.91/1] w-full border border-white/10 overflow-hidden bg-slate-950"><img src={img} alt="" class="w-full h-full object-cover" /></div>
                {/if}
              {/each}
            </div>
            <!-- Square -->
            <div class="space-y-1.5 border border-white/5 p-1.5 bg-black/40">
              <div class="flex justify-between items-center border-b border-white/10 pb-1 mb-1 font-bold">
                <span>ẢNH VUÔNG (1:1)</span>
                <div class="flex gap-1.5">
                  <button type="button" class="text-purple-400 hover:text-purple-300" onclick={() => pmaxSquareImages = [...pmaxSquareImages, '']}>+ URL</button>
                  <button type="button" class="text-purple-400 hover:text-purple-300 border-l border-white/10 pl-1.5" onclick={() => triggerUpload('square')}>+ TẢI LÊN</button>
                </div>
              </div>
              {#each pmaxSquareImages as img, idx}
                <div class="flex gap-1.5 items-center">
                  <input type="text" bind:value={pmaxSquareImages[idx]} placeholder="URL..." class="flex-1 bg-black/80 border border-white/10 p-1 text-[9px] text-white outline-none focus:border-purple-400/50" />
                  <button type="button" class="text-purple-400 text-[8px] hover:text-purple-300" onclick={() => triggerUpload('square', idx)} title="Tải ảnh khác thay thế">THAY</button>
                  <button type="button" class="text-rose-450 hover:text-rose-300 text-[10px]" onclick={() => pmaxSquareImages = pmaxSquareImages.filter((_, i) => i !== idx)}>×</button>
                </div>
                {#if img && (img.startsWith('http') || img.startsWith('/'))}
                  <div class="relative aspect-square w-full border border-white/10 overflow-hidden bg-slate-950"><img src={img} alt="" class="w-full h-full object-cover" /></div>
                {/if}
              {/each}
            </div>
            <!-- Logo -->
            <div class="space-y-1.5 border border-white/5 p-1.5 bg-black/40">
              <div class="flex justify-between items-center border-b border-white/10 pb-1 mb-1 font-bold">
                <span>LOGO THƯƠNG HIỆU</span>
                <div class="flex gap-1.5">
                  <button type="button" class="text-purple-400 hover:text-purple-300" onclick={() => pmaxLogoImages = [...pmaxLogoImages, '']}>+ URL</button>
                  <button type="button" class="text-purple-400 hover:text-purple-300 border-l border-white/10 pl-1.5" onclick={() => triggerUpload('logo')}>+ TẢI LÊN</button>
                </div>
              </div>
              {#each pmaxLogoImages as img, idx}
                <div class="flex gap-1.5 items-center">
                  <input type="text" bind:value={pmaxLogoImages[idx]} placeholder="URL..." class="flex-1 bg-black/80 border border-white/10 p-1 text-[9px] text-white outline-none focus:border-purple-400/50" />
                  <button type="button" class="text-purple-400 text-[8px] hover:text-purple-300" onclick={() => triggerUpload('logo', idx)} title="Tải ảnh khác thay thế">THAY</button>
                  <button type="button" class="text-rose-450 hover:text-rose-300 text-[10px]" onclick={() => pmaxLogoImages = pmaxLogoImages.filter((_, i) => i !== idx)}>×</button>
                </div>
                {#if img && (img.startsWith('http') || img.startsWith('/'))}
                  <div class="relative aspect-square w-12 h-12 mx-auto border border-white/10 overflow-hidden bg-slate-950"><img src={img} alt="" class="w-full h-full object-cover" /></div>
                {/if}
              {/each}
            </div>
          </div>
        </div>

        <!-- Landing Page URL Editor -->
        <div class="space-y-2">
          <span class="block text-[8px] text-slate-400 font-bold uppercase tracking-wider">ĐƯỜNG DẪN TRANG ĐÍCH:</span>
          <input type="text" bind:value={pmaxLandingPageUrl} placeholder="Nhập link trang đích..." class="w-full bg-black/80 border border-white/10 p-1.5 text-xs text-white outline-none focus:border-purple-400/50" />
        </div>

        <!-- Reset Trigger -->
        <div class="text-right"><button type="button" class="text-[8px] text-slate-400 hover:text-white underline" onclick={loadAIProposedAssets}>Đặt lại từ AI đề xuất</button></div>
      </div>
    {/if}

    <!-- Error & Success Messages -->
    {#if validationError}<div class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[9px] font-bold mb-4">❌ {validationError}</div>{/if}
    {#if upgradeError}<div class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-[9px] font-bold mb-4">❌ {upgradeError}</div>{/if}
    {#if upgradeSuccessMessage}
      {#if upgradeSuccessMessage.toLowerCase().includes('thất bại')}
        <div class="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[9px] font-bold mb-4">⚠️ {upgradeSuccessMessage}</div>
      {:else}
        <div class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-bold mb-4">✅ {upgradeSuccessMessage}</div>
      {/if}
    {/if}

    <!-- Danger Alert and Chốt Chặn Checkbox -->
    <div class="p-4 bg-amber-500/5 border border-amber-500/20 mb-4 space-y-3">
      <div class="text-amber-400 text-[8.5px] leading-relaxed font-bold flex items-start gap-2">
        <AlertTriangle size={14} class="shrink-0 text-amber-500 animate-pulse mt-0.5" />
        <span>CẢNH BÁO CHỐT CHẶN: Giao phó 100% cho AI rất nguy hiểm, tăng rủi ro bị khóa tài khoản quảng cáo. Bạn bắt buộc phải Xem & Biên tập các Tiêu đề, Mô tả bằng tay trước khi nâng cấp.</span>
      </div>
      {#if pmaxAssetsLoaded}
        <label class="flex items-center gap-2.5 p-2 bg-amber-500/10 text-amber-300 text-[9px] cursor-pointer select-none font-black uppercase hover:bg-amber-500/20 transition-all border border-amber-500/30">
          <input type="checkbox" bind:checked={userConfirmedReview} class="rounded border-amber-500 text-amber-600 focus:ring-amber-500 focus:ring-offset-black bg-black w-3.5 h-3.5" />
          <span>TÔI XÁC NHẬN ĐÃ PHÊ DUYỆT CÁC TIÊU ĐỀ, MÔ TẢ VÀ ĐƯỜNG DẪN TRANG ĐÍCH</span>
        </label>
      {/if}
    </div>

    <!-- Main Action Button -->
    {#if pmaxAssetsLoaded}
      <button class="w-full py-2.5 bg-gradient-to-r from-purple-600 to-rose-600 hover:from-purple-500 hover:to-rose-500 text-white text-[10px] font-black tracking-widest transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed disabled:from-stone-800 disabled:to-stone-800" onclick={validateAndUpgrade} disabled={upgradingToPMax || !userConfirmedReview}>
        {#if upgradingToPMax}
          <RefreshCw size={12} class="animate-spin" />
          <span>ĐANG NÂNG CẤP CHIẾN DỊCH...</span>
        {:else}
          <span>XÁC NHẬN NỘI DUNG VÀ ĐĂNG LÊN GOOGLE ADS MỚI</span>
        {/if}
      </button>
    {/if}
  {:else}
    <div class="text-[9px] text-amber-400/70 bg-amber-500/5 border border-amber-500/10 p-3 italic">⚠️ Vui lòng chọn chiến dịch DSA để thực hiện di cư nâng cấp.</div>
  {/if}
</div>
