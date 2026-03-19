<script lang="ts">
  import ContentReviewCard from "../ui/ContentReviewCard.svelte";
  import type { CampaignData } from "$lib/state/types";

  let { data } = $props<{ data: Partial<CampaignData> }>();

  // Svelte 5 Safety: 'data' from UniversalModal is a read-only $derived object. 
  // We MUST clone it safely and GUARANTEE no properties are undefined
  // Svelte 5 strict mode will crash silently if a mandatory prop is passed as undefined!
  function createSafeData(source: Partial<CampaignData>): Partial<CampaignData> {
    return {
      campaign_id: source?.campaign_id || source?.id || "",
      step: source?.step ?? 1,
      status: source?.status || "IDLE",
      progress_msg: source?.progress_msg || "",
      keywords: source?.keywords || {},
      assets: source?.assets || [],
      reserve_assets: source?.reserve_assets || [],
      outline: source?.outline || {},
      draft_content: source?.draft_content || "",
      final_html: source?.final_html || "",
      selectedAvatarUrl: source?.selectedAvatarUrl || null,
      selectedAssetIndex: source?.selectedAssetIndex || 0,
      creation_config: source?.creation_config || {},
      analysis_cache: source?.analysis_cache || {},
      analysis_metrics: source?.analysis_metrics || {},
      ...source
    };
  }

  let safelyMutableData = $state(createSafeData(data));
  
  // CNS V75.6: Session-based Awareness Set
  // We track every URL/ID ever seen in this session to distinguish 
  // between "New AI Discovery" and "Old Stale Pulse (after deletion)".
  let historicalSeen = $state(new Set<string>());

  $effect(() => {
    // CNS V75.3: Robust Pulse Sync Engine (Dual Property Support)
    const sourceId = data?.campaign_id || data?.id || "";
    
    if (data && sourceId) {
      if (sourceId !== safelyMutableData.campaign_id) {
        safelyMutableData = createSafeData(data);
        historicalSeen.clear(); // Reset awareness for new campaign
      } else {
        // Phase 1: Update Awareness Set from local state
        // This ensures the UI "remembers" what the user just deleted.
        safelyMutableData.assets?.forEach((a: any) => {
          const url = typeof a === 'string' ? a : (a.file_path || a.url);
          if (url) historicalSeen.add(url);
        });
        safelyMutableData.reserve_assets?.forEach((url: any) => {
          const u = typeof url === 'string' ? url : (url.file_path || url.url);
          if (u) historicalSeen.add(u);
        });

        // Deep reactive sync for progress-related fields
        const nextStep = data.current_step ?? data.step;
        if (nextStep !== undefined && nextStep !== safelyMutableData.step) {
          safelyMutableData.step = nextStep;
        }
        
        if (data.status !== undefined && data.status !== safelyMutableData.status) {
          safelyMutableData.status = data.status;
        }
        if (data.progress_msg !== undefined && data.progress_msg !== safelyMutableData.progress_msg) {
          safelyMutableData.progress_msg = data.progress_msg;
        }
        
        // Sync streaming content only if not locally editing
        if (!safelyMutableData.isEditing) {
          if (data.draft_content && data.draft_content !== safelyMutableData.draft_content) {
            safelyMutableData.draft_content = data.draft_content;
          }
          if (data.final_html && data.final_html !== safelyMutableData.final_html) {
            safelyMutableData.final_html = data.final_html;
          }
          if (data.outline && JSON.stringify(data.outline) !== JSON.stringify(safelyMutableData.outline)) {
            safelyMutableData.outline = data.outline;
          }
        }
        
        // CNS V75.7: Intelligent Merging with Awareness
        // We only ADD items that have NEVER been seen in this session.
        // This effectively ignores "Undelete" pulses while allowing "New AI" assets.
        if (data.assets && Array.isArray(data.assets)) {
           const newAssets = data.assets.filter(a => !historicalSeen.has(a.file_path || a.url));
           if (newAssets.length > 0) {
             safelyMutableData.assets = [...safelyMutableData.assets, ...newAssets];
             newAssets.forEach(a => historicalSeen.add(a.file_path || a.url));
           }
        }
        
        if (data.reserve_assets && Array.isArray(data.reserve_assets)) {
          const newReserves = data.reserve_assets.filter(url => !historicalSeen.has(url));
          if (newReserves.length > 0) {
            safelyMutableData.reserve_assets = [...safelyMutableData.reserve_assets, ...newReserves];
            newReserves.forEach(url => historicalSeen.add(url));
          }
        }

        // Phase 73.11: Sync Analysis Cache & Metrics (Always sync as they are server-driven)
        if (data.analysis_cache && JSON.stringify(data.analysis_cache) !== JSON.stringify(safelyMutableData.analysis_cache)) {
          safelyMutableData.analysis_cache = data.analysis_cache;
        }
        if (data.analysis_metrics && JSON.stringify(data.analysis_metrics) !== JSON.stringify(safelyMutableData.analysis_metrics)) {
          safelyMutableData.analysis_metrics = data.analysis_metrics;
        }
      }
    }
  });
</script>

  <div class="w-full h-full relative z-10 pointer-events-auto">
    <ContentReviewCard
      campaign_id={safelyMutableData.campaign_id || safelyMutableData.id || "temp-dev"}
      bind:keywords={safelyMutableData.keywords}
      bind:assets={safelyMutableData.assets}
      bind:reserve_assets={safelyMutableData.reserve_assets}
      bind:outline={safelyMutableData.outline}
      bind:draft_content={safelyMutableData.draft_content}
      bind:step={safelyMutableData.step}
      bind:status={safelyMutableData.status}
      bind:progress_msg={safelyMutableData.progress_msg}
      bind:finalHtml={safelyMutableData.final_html}
      bind:selectedAvatarUrl={safelyMutableData.selectedAvatarUrl}
      bind:selectedAssetIndex={safelyMutableData.selectedAssetIndex}
      bind:creation_config={safelyMutableData.creation_config}
      bind:analysis_cache={safelyMutableData.analysis_cache}
      bind:analysis_metrics={safelyMutableData.analysis_metrics}
    />
  </div>
