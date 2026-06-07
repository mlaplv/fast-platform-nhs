<script lang="ts">
  let {
    headlines = [],
    descriptions = [],
    adGroupKeywords = []
  } = $props<{
    headlines?: string[];
    descriptions?: string[];
    adGroupKeywords?: string[];
  }>();

  // Derived state for Ad Strength calculations
  let headlinesFilled = $derived(headlines ? headlines.filter(h => h && h.trim()).length : 0);
  let descsFilled = $derived(descriptions ? descriptions.filter(d => d && d.trim()).length : 0);
  
  let keywordMatches = $derived(
    (adGroupKeywords && headlines)
      ? adGroupKeywords.filter(kw => 
          headlines.some(h => h && h.toLowerCase().includes(kw.toLowerCase()))
        )
      : []
  );

  let uniqueHeadlinesCount = $derived(
    headlines
      ? new Set(headlines.filter(h => h && h.trim()).map(h => h.trim().toLowerCase())).size
      : 0
  );

  let uniqueDescsCount = $derived(
    descriptions
      ? new Set(descriptions.filter(d => d && d.trim()).map(d => d.trim().toLowerCase())).size
      : 0
  );

  let adStrengthScore = $derived.by(() => {
    let score = 0;
    // 40 points for headlines count (up to 15)
    score += Math.min(40, (headlinesFilled / 15) * 40);
    // 20 points for descriptions count (up to 4)
    score += Math.min(20, (descsFilled / 4) * 20);
    // 20 points for keyword matching
    if (adGroupKeywords && adGroupKeywords.length > 0) {
      score += Math.min(20, (keywordMatches.length / Math.min(3, adGroupKeywords.length)) * 20);
    } else {
      score += 20; // default points if no keywords defined in group
    }
    // 20 points for uniqueness
    if (headlinesFilled > 0) {
      score += Math.min(10, (uniqueHeadlinesCount / headlinesFilled) * 10);
    }
    if (descsFilled > 0) {
      score += Math.min(10, (uniqueDescsCount / descsFilled) * 10);
    }
    return Math.round(score);
  });

  let adStrengthLabel = $derived.by(() => {
    const score = adStrengthScore;
    if (score < 40) return 'POOR';
    if (score < 65) return 'AVERAGE';
    if (score < 85) return 'GOOD';
    return 'EXCELLENT';
  });
</script>

<div class="bg-white/[0.02] border border-white/10 p-6 rounded-none relative overflow-hidden">
  <h5 class="text-xs font-black text-white tracking-widest font-mono uppercase mb-4 text-left">Độ mạnh quảng cáo</h5>
  
  <!-- Score & Label -->
  <div class="flex items-end justify-between mb-4">
    <span class="text-[9px] text-slate-500 font-mono font-black">CHỈ SỐ SỨC MẠNH</span>
    <div class="text-right">
      <span class="text-2xl font-black font-mono tracking-tighter {adStrengthLabel === 'EXCELLENT' ? 'text-emerald-400' : adStrengthLabel === 'GOOD' ? 'text-cyan-400' : adStrengthLabel === 'AVERAGE' ? 'text-yellow-500' : 'text-red-500'}">
        {adStrengthLabel === 'EXCELLENT' ? 'RẤT TỐT' : adStrengthLabel === 'GOOD' ? 'TỐT' : adStrengthLabel === 'AVERAGE' ? 'TRUNG BÌNH' : 'KÉM'}
      </span>
      <span class="text-xs text-slate-500 font-mono block">({adStrengthScore}/100)</span>
    </div>
  </div>

  <!-- Progress Bar -->
  <div class="w-full h-2 bg-white/5 mb-6 rounded-none overflow-hidden flex">
    <div 
      class="h-full transition-all duration-500 {adStrengthLabel === 'EXCELLENT' ? 'bg-emerald-500' : adStrengthLabel === 'GOOD' ? 'bg-cyan-400' : adStrengthLabel === 'AVERAGE' ? 'bg-yellow-500' : 'bg-red-500'}"
      style="width: {adStrengthScore}%"
    ></div>
  </div>

  <!-- Checklist Criteria -->
  <div class="space-y-3 font-mono text-[10px] text-slate-400">
    <div class="flex items-center justify-between pb-2 border-b border-white/5">
      <span>1. Thêm nhiều dòng tiêu đề hơn</span>
      <span class="font-bold {headlinesFilled >= 12 ? 'text-emerald-400' : 'text-slate-600'}">
        {headlinesFilled >= 12 ? '✓ ĐẠT' : '✗ CHƯA ĐẠT'} ({headlinesFilled}/15)
      </span>
    </div>
    <div class="flex items-center justify-between pb-2 border-b border-white/5">
      <span>2. Bao phủ từ khóa mục tiêu</span>
      <span class="font-bold {keywordMatches.length >= Math.min(3, adGroupKeywords.length) ? 'text-emerald-400' : 'text-slate-600'}">
        {keywordMatches.length >= Math.min(3, adGroupKeywords.length) ? '✓ ĐẠT' : '✗ CHƯA ĐẠT'} ({keywordMatches.length}/{adGroupKeywords.length})
      </span>
    </div>
    <div class="flex items-center justify-between pb-2 border-b border-white/5">
      <span>3. Tiêu đề độc đáo, đa dạng</span>
      <span class="font-bold {uniqueHeadlinesCount >= Math.max(5, Math.round(headlinesFilled * 0.7)) ? 'text-emerald-400' : 'text-slate-600'}">
        {uniqueHeadlinesCount >= Math.max(5, Math.round(headlinesFilled * 0.7)) ? '✓ ĐẠT' : '✗ CHƯA ĐẠT'} ({uniqueHeadlinesCount}/{headlinesFilled})
      </span>
    </div>
    <div class="flex items-center justify-between pb-2 border-b border-white/5">
      <span>4. Mô tả độc đáo, khác biệt</span>
      <span class="font-bold {uniqueDescsCount >= Math.max(2, descsFilled) ? 'text-emerald-400' : 'text-slate-600'}">
        {uniqueDescsCount >= Math.max(2, descsFilled) ? '✓ ĐẠT' : '✗ CHƯA ĐẠT'} ({uniqueDescsCount}/{descsFilled})
      </span>
    </div>
    <div class="flex items-center justify-between pb-2 border-b border-white/5">
      <span>5. Cấu hình Sitelinks liên kết</span>
      <span class="font-bold text-emerald-400">✓ KHUYẾN NGHỊ</span>
    </div>
  </div>
</div>
