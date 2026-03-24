<script lang="ts">
  import { untrack } from "svelte";
  import ContentReviewCard from "../ui/ContentReviewCard.svelte";
  import type { CampaignData, MediaAsset } from "$lib/state/types";
  import { xohiImageStore } from "$lib/state/xohiImage.svelte";

  let { data } = $props<{ data: Partial<CampaignData> }>();

  // Svelte 5 Safety: 'data' from UniversalModal is a read-only $derived object. 
  // We MUST clone it safely and GUARANTEE no properties are undefined
  // Svelte 5 strict mode will crash silently if a mandatory prop is passed as undefined!
  function createSafeData(source: Partial<CampaignData>): Partial<CampaignData> {
    return {
      ...source,
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
      analysis_metrics: source?.analysis_metrics || source?.gold_metadata?.analysis_metrics || {}
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
        xohiImageStore.clearAll(); // CNS V82.10: Hard reset global store to prevent leakage (Hôi nách nam)
      } else {
        // Phase 1: Keep Awareness Set updated for deleted items
        // We track WHAT WAS DELETED locally so we don't re-add it from stale pulses.
        // (This part is fine, but we must be careful not to hide brand new AI assets)

        // Deep reactive sync for progress-related fields
        // CNS V80.3: Monotonic Step Sync (Allow manual backtrack but pulses ONLY advance)
        const nextStep = data.current_step ?? data.step;
        if (nextStep !== undefined && nextStep > safelyMutableData.step) {
          safelyMutableData.step = nextStep;
        }

        if (data.status !== undefined && data.status !== safelyMutableData.status) {
          safelyMutableData.status = data.status;
          if (data.status === "PROCESSING") historicalSeen.clear();
        }
        
        if (data.progress_msg !== undefined) {
          safelyMutableData.progress_msg = data.progress_msg;
        }

        // CNS Phase 16.2: Pulse-driven Keyword & Topic Sync
        const incomingKeywords = data.keywords || data.topic_data;
        if (incomingKeywords && typeof incomingKeywords === 'object' && Object.keys(incomingKeywords).length > 0) {
          // We only sync if changed to avoid unnecessary re-renders of the Step 1 card
          if (JSON.stringify(incomingKeywords) !== JSON.stringify(safelyMutableData.keywords)) {
            safelyMutableData.keywords = { ...incomingKeywords };
          }
        }

        // Sync streaming content only if not locally editing
        if (!safelyMutableData.isEditing) {
          if (data.draft_content) safelyMutableData.draft_content = data.draft_content;
          if (data.final_html) safelyMutableData.final_html = data.final_html;
          const incomingOutline = data.outline || data.outline_data;
          if (incomingOutline) safelyMutableData.outline = incomingOutline;
        }

        // CNS V75.7: Intelligent Merge (Direct Replacement if Pulse is non-empty)
        // If the backend sends a non-empty list, it's the source of truth.
        const incomingAssets = data.assets || data.assets_data;
        if (incomingAssets && Array.isArray(incomingAssets)) {
           const firstId = (a: MediaAsset | string) => typeof a === 'string' ? a : (a.id || a.file_path);
           const currentAssets = untrack(() => safelyMutableData.assets);
           if (incomingAssets.length !== currentAssets.length || (incomingAssets.length > 0 && firstId(incomingAssets[0]) !== firstId(currentAssets[0]))) {
             safelyMutableData.assets = [...incomingAssets];
           }
        }

        const incomingReserves = data.reserve_assets || data.gold_metadata?.reserve_assets;
        if (incomingReserves && Array.isArray(incomingReserves)) {
          const currentReserves = untrack(() => safelyMutableData.reserve_assets);
          if (incomingReserves.length !== currentReserves.length) {
            safelyMutableData.reserve_assets = [...incomingReserves];
          }
        }

        // Phase 73.11: Sync Analysis Cache & Metrics
        if (data.analysis_cache) safelyMutableData.analysis_cache = data.analysis_cache;
        if (data.analysis_metrics) safelyMutableData.analysis_metrics = data.analysis_metrics;
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
