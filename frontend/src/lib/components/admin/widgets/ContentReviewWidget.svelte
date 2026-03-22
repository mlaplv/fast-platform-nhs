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
      keywords: source?.keywords || source?.topic_data || {},
      assets: source?.assets || source?.assets_data || [],
      reserve_assets: source?.reserve_assets || source?.gold_metadata?.reserve_assets || [],
      outline: source?.outline || source?.outline_data || {},
      draft_content: source?.draft_content || "",
      final_html: source?.final_html || "",
      selectedAvatarUrl: source?.selectedAvatarUrl || source?.gold_metadata?.selectedAvatarUrl || null,
      selectedAssetIndex: source?.selectedAssetIndex || 0,
      creation_config: source?.creation_config || source?.gold_metadata?.creation_config || {},
      analysis_cache: source?.analysis_cache || source?.gold_metadata?.analysis_cache || {},
      analysis_metrics: source?.analysis_metrics || source?.gold_metadata?.analysis_metrics || {},
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
        safelyMutableData.assets?.forEach((a: MediaAsset | string) => {
          const url = typeof a === 'string' ? a : (a.file_path || a.url);
          if (url) historicalSeen.add(url);
        });
        safelyMutableData.reserve_assets?.forEach((url: MediaAsset | string) => {
          const u = typeof url === 'string' ? url : (url.file_path || url.url);
          if (u) historicalSeen.add(u);
        });

        // Deep reactive sync for progress-related fields
        const nextStep = data.current_step ?? data.step;
        if (nextStep !== undefined && nextStep !== safelyMutableData.step) {
          safelyMutableData.step = nextStep;
        }

        if (data.status !== undefined && data.status !== safelyMutableData.status) {
          // Phase 75.9: Clear awareness set on new processing (Retry / New Step)
          if (data.status === "PROCESSING" && safelyMutableData.status !== "PROCESSING") {
            historicalSeen.clear();
          }
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
          const incomingOutline = data.outline || data.outline_data;
          if (incomingOutline && JSON.stringify(incomingOutline) !== JSON.stringify(safelyMutableData.outline)) {
            safelyMutableData.outline = incomingOutline;
          }
        }

        // CNS V75.7: Intelligent Merging with Awareness
        // We only ADD items that have NEVER been seen in this session.
        // This effectively ignores "Undelete" pulses while allowing "New AI" assets.
        const incomingAssets = data.assets || data.assets_data;
        if (incomingAssets && Array.isArray(incomingAssets)) {
           const newAssets = incomingAssets.filter(a => {
             const url = typeof a === 'string' ? a : (a.file_path || a.url);
             return url && !historicalSeen.has(url);
           });
           if (newAssets.length > 0) {
             safelyMutableData.assets = [...safelyMutableData.assets, ...newAssets];
             newAssets.forEach(a => {
               const url = typeof a === 'string' ? a : (a.file_path || a.url);
               if (url) historicalSeen.add(url);
             });
           }
        }

        const incomingReserves = data.reserve_assets || data.gold_metadata?.reserve_assets;
        if (incomingReserves && Array.isArray(incomingReserves)) {
          const newReserves = incomingReserves.filter(url => {
            const u = typeof url === 'string' ? url : (url.file_path || url.url);
            return u && !historicalSeen.has(u);
          });
          if (newReserves.length > 0) {
            safelyMutableData.reserve_assets = [...safelyMutableData.reserve_assets, ...newReserves];
            newReserves.forEach(url => {
              const u = typeof url === 'string' ? url : (url.file_path || url.url);
              if (u) historicalSeen.add(u);
            });
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
