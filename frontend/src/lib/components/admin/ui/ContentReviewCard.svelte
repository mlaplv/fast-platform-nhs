<script lang="ts">
  import {
    Check,
    RotateCcw,
    Edit2,
    Save,
    X,
    Sparkles,
    MessageSquare,
    Image as ImageIcon,
    FileText,
    ShieldCheck,
    CheckCircle,
    Maximize2,
    Minimize2,
    Trash2,
    Star,
    Plus,
    BarChart2,
    ShieldAlert,
    Edit3,
    Link as LinkIcon
  } from "lucide-svelte";
  import RichTextEditor from "./RichTextEditor.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { vuiState, vuiController } from "$lib/vui";
  import { fade, slide, scale } from "svelte/transition";
  import { untrack } from "svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import type { EditorAnnotation, ToolbarAction } from "$lib/types";

  let {
    campaign_id,
    step: incomingStep = 1,
    status: incomingStatus = "WAITING_FOR_REVIEW",
    progress_msg: incomingProgressMsg = "",
    title: incomingTitle = "",
    keywords: incomingKeywords = {},
    assets: incomingAssets = [],
    outline: incomingOutline = {},
    draft_content: incomingDraftContent = ""
  } = $props();

  // Unified Local Reactive States (Editable by UI or synced from Props)
  // Matching template expectations: 'keywords', 'assets', 'outline', 'draft_content'
  let step = $state(untrack(() => incomingStep));
  let status = $state(untrack(() => incomingStatus));
  let progress_msg = $state(untrack(() => incomingProgressMsg));
  
  $effect(() => {
    step = incomingStep;
    status = incomingStatus;
    progress_msg = incomingProgressMsg;
  });
  
  // keywords is an object like { title: "...", primary_keyword: "...", secondary_keywords: [...] }
  let keywords = $state(untrack(() => incomingKeywords || {}));
  let assets = $state(untrack(() => incomingAssets || []));
  let outline = $state(untrack(() => incomingOutline || { title: "", sections: [] }));
  let draft_content = $state(untrack(() => incomingDraftContent || ""));
  
  // Secondary State for Editing (Deep Copy)
  let editedKeywords = $state(untrack(() => ({ ...incomingKeywords })));
  let editedOutline = $state(untrack(() => ({ sections: [...(incomingOutline?.sections || [])] })));
  let editedDraft = $state(untrack(() => incomingDraftContent || ""));
  let customImageUrl = $state("");
  let isLoading = $state(false);
  let resultMsg = $state("");
  let selectedAssetIndex = $state(0);
  let selectedAvatarUrl = $state<string | null>(null);
  let isHydrating = $state(false);
  let hasHydrated = $state(false);
  let viewingStep = $state(untrack(() => step));
  let showContext = $state(false);
  let isEditingSidebarKeywords = $state(false);
  let uniqueScore = $state(0);
  let finalHtml = $state("");

  // ── Step 4 Content Studio State ──
  let step4Tab = $state<'editor' | 'copyright' | 'seo'>('editor');
  let copyrightResult = $state<any>(null);
  let isCopyrightLoading = $state(false);
  let seoResult = $state<any>(null);
  let isSeoLoading = $state(false);
  // New: AI Readiness
  let aiReadyResult = $state<any>(null);
  let isAiLoading = $state(false);
  let isPublishing = $state(false);

  // ── Computed Editor Annotations (copyright + seo combined) ──
  let editorAnnotations = $derived<EditorAnnotation[]>([
    // Copyright annotations
    ...((copyrightResult?.flagged_sentences || []).map((s: any) => ({
      text: (typeof s === 'string' ? s : s.text) || '',
      type: (typeof s === 'object' && s.type === 'fixed') ? 'fixed' : 'copyright',
      message: (typeof s === 'object' ? s.reason : '') || 'Cần kiểm tra bản quyền',
      source: (typeof s === 'object' ? s.source_url : '') || '',
      severity: (typeof s === 'object' ? (s.severity || 'medium') : 'medium').toLowerCase()
    }))),
    // SEO structural + AI annotations
    ...((seoResult?.seo_annotations || []).map((a: any) => ({
      text: a.text || '',
      type: a.type || 'seo-info',
      message: a.message || '',
      severity: (a.severity || 'info').toLowerCase()
    }))),
    // AI GEO readiness annotations
    ...((aiReadyResult?.ai_annotations || []).map((a: any) => ({
      text: a.text || '',
      type: a.type || 'geo-info',
      message: a.message || '',
      severity: (a.severity || 'info').toLowerCase()
    })))
  ]);

  const runCopyrightCheck = async () => {
    if (!campaign_id || isCopyrightLoading) return;
    isCopyrightLoading = true;
    copyrightResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/copyright`);
      if (res?.data) copyrightResult = res.data;
    } catch (e) {
      console.error("[ContentReviewCard] Copyright check failed:", e);
    } finally {
      isCopyrightLoading = false;
    }
  };

  const runSeoAnalysis = async () => {
    if (!campaign_id || isSeoLoading) return;
    isSeoLoading = true;
    seoResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/seo`);
      if (res?.data) seoResult = res.data;
    } catch (e) {
      console.error("[ContentReviewCard] SEO analysis failed:", e);
    } finally {
      isSeoLoading = false;
    }
  };

  const runAiAnalysis = async () => {
    if (!campaign_id || isAiLoading) return;
    isAiLoading = true;
    aiReadyResult = null;
    try {
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/ai-inspect`);
      if (res?.data) aiReadyResult = res.data;
    } catch (e) {
      console.error("[ContentReviewCard] AI Inspect failed:", e);
    } finally {
      isAiLoading = false;
    }
  };

  // ── Auto-Fix (Surgical Agent) — Returns new_text, or null on failure
  // The actual replacement is handled inside RichTextEditor via the onfix callback
  const runAutoFix = async (targetSnippet: string, annotationType: string, errorMessage: string): Promise<string | null> => {
    if (!campaign_id) return null;
    try {
      console.log(`[ContentReviewCard Auto-Fix] Requesting fix from AI Engine... Snippet: "${targetSnippet.substring(0, 30)}..."`);
      const res = (await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/analyze/auto-fix`, {
        target_snippet: targetSnippet,
        annotation_type: annotationType,
        error_message: errorMessage,
      })) as any;
      console.log(`[ContentReviewCard Auto-Fix] Raw API Response:`, res);
      
      const payload = res?.status === 'success' ? res.data : null;
      if (payload?.new_text) {
        const new_text = payload.new_text;
        console.log(`[ContentReviewCard Auto-Fix] Received New Text length: ${new_text.length}. Handing off to Editor for ID replacement.`);
        // Return the exact text string to RichTextEditor FIRST.
        // The editor needs the DOM unchanged to find the old tooltip UUID.
        // We delay updating our Svelte state so the `$effect` doesn't wipe out the marks before the editor replaces the text.
        setTimeout(() => {
          console.log(`[ContentReviewCard Auto-Fix] +100ms Timeout elapsed. Updating Svelte UI Local State to "fixed".`);
          const normTarget = targetSnippet.replace(/[\\s\\*\\u200B\\uFEFF]+/g, '').toLowerCase();
          const updateMatches = (text: string) => {
            if (typeof text !== 'string') return false;
            return text.replace(/[\\s\\*\\u200B\\uFEFF]+/g, '').toLowerCase() === normTarget;
          };

          if (seoResult?.seo_annotations) {
            seoResult.seo_annotations = seoResult.seo_annotations.map((a: any) => 
              updateMatches(a.text) ? { ...a, text: new_text, type: 'fixed' } : a
            );
          }
          if (aiReadyResult?.ai_annotations) {
            aiReadyResult.ai_annotations = aiReadyResult.ai_annotations.map((a: any) => 
              updateMatches(a.text) ? { ...a, text: new_text, type: 'fixed' } : a
            );
          }
          if (copyrightResult?.flagged_sentences) {
            copyrightResult.flagged_sentences = copyrightResult.flagged_sentences.map((s: any) => {
              const isMatch = updateMatches(typeof s === 'string' ? s : s.text);
              if (isMatch) {
                return typeof s === 'string' ? { text: new_text, type: 'fixed', message: 'Đã sửa lỗi bản quyền' } : { ...s, text: new_text, type: 'fixed' };
              }
              return s;
            });
          }
        }, 100);
        
        return new_text;
      } else {
        console.warn(`[ContentReviewCard Auto-Fix] API did not return new_text! Payload:`, payload);
        return null;
      }
    } catch (e) {
      console.error('[ContentReviewCard] Auto-Fix failed:', e);
      return null;
    }
    return null;
  };



  // Editor ref (used by Auto-Fix to apply text replacements)
  let editorRef = $state<any>(null);
  
  // Auto-expand context if we are in Step 3/4 and it's the first visit
  $effect(() => {
     if (step >= 3 && !hasHydrated) {
        showContext = true;
     }
  });

  $effect(() => {
    // Only advance viewingStep if it exactly equals step - 1 (meaning step just incremented)
    // This allows users to manually navigate back by setting viewingStep < step via buttons
    if (step > viewingStep + 1) {
      viewingStep = step;
    }
  });

  async function syncAssetChanges() {
    if (!campaign_id) return;
    try {
      await apiClient.put(`/api/v1/content/campaigns/${campaign_id}/metadata`, {
        assets: $state.snapshot(assets),
        avatar: selectedAvatarUrl,
        selected_index: selectedAssetIndex
      });
    } catch (e) {
      console.warn("[ContentReviewCard] Failed to sync asset changes:", e);
    }
  }

  function deleteAsset(index: number, e?: Event) {
    if (e) e.stopPropagation();
    const removedUrl = assets[index];
    assets = assets.filter((_, i) => i !== index);
    if (selectedAssetIndex >= assets.length) {
      selectedAssetIndex = Math.max(0, assets.length - 1);
    }
    if (selectedAvatarUrl === removedUrl) {
      selectedAvatarUrl = assets[0] || null;
    }
    // Phase 85.1: Persist curation immediately
    syncAssetChanges();
  }

  function handleImageError(url: string) {
    const index = assets.indexOf(url);
    if (index !== -1) {
      if (import.meta.env.DEV) console.warn(`[ContentReviewCard] Auto-removing broken image: ${url}`);
      deleteAsset(index);
    }
  }

  async function hydrate() {
    if (!campaign_id || isHydrating || hasHydrated) return;
    isHydrating = true;
    hasHydrated = true; // Mark as "tried" immediately to prevent loop during the async await call
    try {
      if (import.meta.env.DEV) console.log(`[ContentReviewCard] Hydrating slimmed log: ${campaign_id}`);
      const c = await apiClient.get<any>(`/api/v1/content/campaigns/${campaign_id}`);
      if (c) {
        keywords = { ...(c.topic_data || {}) };
        if (!editedKeywords.title) editedKeywords = { ...(c.topic_data || {}) };
        assets = [...(c.assets_data || [])];
        const gold = c.gold_metadata || {};
        if (gold.avatar) {
          selectedAvatarUrl = gold.avatar;
        } else if (!selectedAvatarUrl && assets.length > 0) {
          selectedAvatarUrl = assets[0];
        }

        if (gold.selected_index !== undefined && gold.selected_index < assets.length) {
          selectedAssetIndex = gold.selected_index;
        } else if (selectedAvatarUrl) {
          const idx = assets.indexOf(selectedAvatarUrl);
          if (idx !== -1) selectedAssetIndex = idx;
        }

        outline = { ...(c.outline_data || { sections: [] }) };
        editedOutline = { sections: [...(outline.sections || [])] };
        draft_content = c.draft_content || "";
        uniqueScore = c.unique_score || 0;
        finalHtml = c.final_html || "";
        
        // Convert Step 3 JSON outline into HTML for the RichTextEditor
        if (c.current_step === 3 && !draft_content && outline.sections && outline.sections.length > 0) {
           draft_content = `<h2>${outline.title || "Dàn ý"}</h2>\n` + outline.sections.map((s: any) => `<h3>${s.heading}</h3><p>${s.content}</p>`).join("\n");
        }

        if (!editedDraft) editedDraft = draft_content;
        if (c.current_step > step) step = c.current_step;
      }
    } catch (e) {
      console.error("[ContentReviewCard] Hydration failed:", e);
      // Do NOT reset hasHydrated = false here, to prevent infinite loop on failure (e.g. 429)
    } finally {
      isHydrating = false;
    }
  }

  // UI Derived States — B1 FIX: isEditing is pure $state, not derived from status
  let isEditing = $state(false);
  let isProcessing = $derived(status === "PROCESSING");
  let isReviewing = $derived(status === "WAITING_FOR_REVIEW");

  // Rule R82.22: Smart Sync Effect — Bridging Props and Local State
  $effect(() => {
    // We only read props reactively. 
    // Any assignment to local state MUST be untracked if we also read that state here,
    // otherwise Svelte 5 will throw a maximum update depth exceeded error.
    const newStep = incomingStep;
    const newStatus = incomingStatus;
    const newProgressMsg = incomingProgressMsg;
    const newKeywords = incomingKeywords;
    const newAssets = incomingAssets;
    const newOutline = incomingOutline;
    const newDraftContent = incomingDraftContent;

    untrack(() => {
      // 1. Step Sync (Anti-Regression Logic)
      if (newStep > step) {
        if (import.meta.env.DEV) console.log(`[ContentReviewCard] Prop Step Advance: ${step} -> ${newStep}`);
        step = newStep;
        selectedAssetIndex = 0; // Reset focus on step change
        hasHydrated = false; // Allow hydration for the new step's heavy payloads
      }

      // 2. Status Sync (Elite Transition Logic)
      if (newStatus !== status) {
        if (newStep === step || newStep > step) {
          if (import.meta.env.DEV) console.log(`[ContentReviewCard] Prop Status Sync: ${status} -> ${newStatus}`);
          const oldStatus = status;
          status = newStatus;
          hasHydrated = false; // Trigger re-hydration on any status change (Fix: "Black screen")
          
          if (newDraftContent && newDraftContent !== draft_content) {
            draft_content = newDraftContent;
            if (!editedDraft) editedDraft = newDraftContent;
          }

          if (status === "WAITING_FOR_REVIEW") {
            vuiState.setLiveText(`Bước ${step} hoàn tất.`);
            vuiController.resetToIdle();
            resultMsg = "";
          }
        }
      }

      // 3. Metadata & Asset Sync
      // Only refresh local state if we aren't editing, AND if data is actually present.
      if (!isEditing) {
        if (newKeywords && Object.keys(newKeywords).length > 0) {
          keywords = { ...newKeywords };
          if (newStep > step || !editedKeywords.title) {
            editedKeywords = { ...newKeywords };
          }
        }

        if (newAssets && newAssets.length > 0) {
          assets = [...newAssets];
        }

        if (newOutline && newOutline.sections?.length > 0) {
          outline = { ...newOutline };
          if (newStep > step || !editedOutline.sections || editedOutline.sections.length === 0) {
            editedOutline = { sections: [...newOutline.sections.map(s => ({...s}))] };
          }
        }
      }

      // 4. Progress Message & VUI Phasing
      progress_msg = newProgressMsg;
      if (status === "PROCESSING" && vuiState.phase === "executing") {
        vuiState.setLiveText(progress_msg || "AI đang xử lý...");
      }

      // Sync unique_score, final_html, and draft_content from inbound data props
      const incomingData = nanobot.vuiResponse?.data;
      if (incomingData?.unique_score !== undefined) {
        uniqueScore = incomingData.unique_score;
      }
      if (incomingData?.plagiarism) {
        copyrightResult = incomingData.plagiarism;
      }
      if (incomingData?.final_html) {
        finalHtml = incomingData.final_html;
      }
      if (incomingData?.draft_content && incomingData.draft_content !== draft_content) {
        draft_content = incomingData.draft_content;
        if (!editedDraft) editedDraft = draft_content;
      }

      // 5. Self-Hydration R81.30: Because backend streams Ultra-Slim logs, we must fetch heavy payloads via API.
      const needsKeyword = !keywords.title;
      const needsAssets = step === 2 && (!assets || assets.length === 0);
      const needsOutline = step === 3 && (!outline || !outline.sections || outline.sections.length === 0);
      const needsContent = step === 4 && !draft_content; 
      
      const isCurrentlyProcessing = newStatus === "PROCESSING";

      if (import.meta.env.DEV) {
          console.log(`[ContentReviewCard] Hydration check: step=${step}, status=${newStatus}, isProcessing=${isCurrentlyProcessing}, hasHydrated=${hasHydrated}`);
          console.log(`[ContentReviewCard] Needs: kw=${needsKeyword}, assets=${needsAssets} (len=${assets?.length}), outline=${needsOutline}`);
      }

      if (campaign_id && !isCurrentlyProcessing && (needsKeyword || needsAssets || needsOutline)) {
         // Reset hydration lock if we are missing mandatory step data
         hasHydrated = false;
         if (import.meta.env.DEV) console.log(`[ContentReviewCard] Dropping hasHydrated lock!`);
      }
      
      if (campaign_id && !isCurrentlyProcessing && !hasHydrated) {
        if (import.meta.env.DEV) console.log(`[ContentReviewCard] Executing hydrate()`);
        hydrate();
      }
    });
  });

  async function handleApprove() {
    if (isLoading || status === "PROCESSING") return;
    
    // Rule R81/R82.20: Immediate UI/VUI Lock & Escape from Logs
    isLoading = true;
    status = "PROCESSING";
    vuiController.interruptSpeech();
    vuiState.setIsWaitingForAction(false);
    // If we're inside the log drawer, close it to "escape" to the Orb
    nanobot.closeFullLog();
    
    // Rule R81/R82.20: Capture VUI focus and PREEMPTIVELY show next step processing
    const nextStep = step + 1;
    nanobot.voice.setVoiceResult(
        "Chuyển bước nội dung",
        "Dạ sếp, em đã ghi nhận bản thảo bước " + step + ". Đang khởi tạo bước " + nextStep + " ạ.",
        "CONTENT_CREATE",
        { 
          category: "CONTENT_CREATE",
          campaign_id, 
          step: nextStep, 
          status: "PROCESSING", 
          keywords, // Keep keywords for context
          assets: [], // Clear assets for new hunt
          outline: { title: "", sections: [] }, 
          progress_msg: "Đang yêu cầu duyệt..."
        },
        "voice"
    );

    vuiState.setActive(true);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Đang gửi yêu cầu duyệt...");
    nanobot.startPolling(); 

    try {
      const resp = (await apiClient.post(
        `/api/v1/content/campaigns/${campaign_id}/approve`,
        {
          approved: true,
          step: step,
          edited_data: isEditing ? ((viewingStep === 3 || viewingStep === 4) ? { html: editedDraft } : editedKeywords) : null,
          assets: viewingStep === 2 ? assets : null,
          avatar: selectedAvatarUrl,
          selected_index: selectedAssetIndex
        },
      )) as any;
      resultMsg = resp.message || "Sếp đã duyệt. Đang chuyển pha...";

      // 2. Local State Advance
      if (resp.next_step) {
        step = resp.next_step;
      } else {
        step += 1;
      }
      
      // 3. Sync back to nanobot
      if (nanobot.vuiResponse?.data) {
          nanobot.vuiResponse.data.step = step;
          nanobot.vuiResponse.data.progress_msg = resultMsg;
          nanobot.vuiResponse.data.status = "PROCESSING";
          
          nanobot.vuiResponse.data.assets = [];
          nanobot.vuiResponse.data.outline = { title: "", sections: [] };
          
          assets = []; 
          selectedAssetIndex = 0;
          outline = { title: "", sections: [] };
      }
      
    } catch (e) {
      console.error("[ContentReviewCard] Approve failed:", e);
      resultMsg = "Lỗi kết nối hệ thống...";
      status = "WAITING_FOR_REVIEW";
      if (nanobot.vuiResponse?.data) {
          nanobot.vuiResponse.data.status = "WAITING_FOR_REVIEW";
          nanobot.vuiResponse.data.progress_msg = "Lỗi kết nối. Thử lại nhé sếp!";
      }
    } finally {
      isLoading = false;
      vuiState.setIsWaitingForAction(false);
    }
  }

  async function handlePublish() {
    if (isPublishing) return;
    isPublishing = true;
    try {
      // Step 6: Finalize campaign and "Publish"
      const res = await apiClient.post(`/api/v1/content/campaigns/${campaign_id}/approve`, {
        approved: true,
        step: 6
      });
      if (res) {
        vuiController.addMessage("🚀 BÀI VIẾT ĐÃ ĐƯỢC XUẤT BẢN THÀNH CÔNG!", "success");
        status = "COMPLETED";
      }
    } catch (e) {
      console.error("Publish failed:", e);
      vuiController.addMessage("Lỗi khi xuất bản bài viết.", "error");
    } finally {
      isPublishing = false;
    }
  }

  async function handleRetry() {
    if (isLoading) return; // Still guard against double API calls, but allow PROCESSING interruption
    
    isLoading = true;
    status = "PROCESSING";
    vuiController.interruptSpeech();
    nanobot.closeFullLog();

    // Clear local buffers to provide immediate visual feedback (Fix: "Black screen/Nothing happens")
    draft_content = "";
    assets = [];
    outline = { title: "", sections: [] };
    uniqueScore = 0;
    finalHtml = "";

    // Capture VUI focus for CURRENT step (Rule R81/R82.20)
    nanobot.voice.setVoiceResult(
      "Chạy lại bước",
      "Dạ sếp, em đang chạy lại bước " + step + " cho sếp đây.",
      "CONTENT_CREATE",
      { 
        campaign_id, 
        step, 
        status: "PROCESSING", 
        keywords, 
        assets: [], 
        outline: { title: "", sections: [] },
        progress_msg: "Đang yêu cầu AI thực hiện lại..." 
      },
      "voice"
    );

    vuiState.setActive(true);
    vuiState.setPhase("executing");
    vuiState.setLiveText("Đang yêu cầu AI thực hiện lại...");

    try {
      const resp = (await apiClient.post(
        `/api/v1/content/campaigns/${campaign_id}/retry`,
        {},
      )) as any;
      resultMsg = resp.message || "AI đang thực hiện lại...";
      vuiState.setLiveText(resultMsg);
      
      if (nanobot.vuiResponse?.data) {
          nanobot.vuiResponse.data.status = "PROCESSING";
          nanobot.vuiResponse.data.progress_msg = resultMsg;
      }
      nanobot.startPolling();
    } catch (e) {
      console.error("[ContentReviewCard] Retry failed:", e);
      resultMsg = "Lỗi kết nối hệ thống...";
      status = "WAITING_FOR_REVIEW";
    } finally {
      isLoading = false;
      vuiState.setIsWaitingForAction(false);
    }
  }


  async function handleUpdateMetadata(targetStep?: number) {
    if (!campaign_id || isLoading) return;
    const effectiveStep = targetStep || viewingStep;
    isLoading = true;
    try {
      const payload: any = {
        avatar: selectedAvatarUrl,
        selected_index: selectedAssetIndex
      };
      
      // Backend (orchestrator.py) expects "keywords" for topic_data
      if (effectiveStep === 1) {
        payload.keywords = editedKeywords;
        payload.topic_data = editedKeywords; // Fallback
      }
      if (effectiveStep === 3) {
        payload.outline_data = $state.snapshot(editedOutline);
        payload.draft_content = editedDraft;
      }
      if (effectiveStep === 4) {
        payload.draft_content = editedDraft;
      }
      if (effectiveStep === 2) payload.assets = assets;
      
      await apiClient.put(`/api/v1/content/campaigns/${campaign_id}/metadata`, payload);
      
      // Update local state
      if (effectiveStep === 1) keywords = { ...editedKeywords };
      if (effectiveStep === 3) {
        outline = { sections: [...editedOutline.sections.map(s => ({...s}))] };
        draft_content = editedDraft;
      }
      if (effectiveStep === 4) draft_content = editedDraft;
      
      resultMsg = "Đã lưu thay đổi thành công!";
      isEditing = false;
      setTimeout(() => resultMsg = "", 3000);
    } catch (e) {
      console.error("[ContentReviewCard] Failed to update metadata:", e);
      resultMsg = "Lỗi khi lưu thay đổi...";
    } finally {
      isLoading = false;
    }
  }

  function handleSelectKeyword(kw: string) {
    if (isLoading || viewingStep > 1) return;
    
    // Swap primary and the clicked secondary
    const oldPrimary = keywords.primary_keyword;
    const secondaries = [...(keywords.secondary_keywords || [])];
    const idx = secondaries.indexOf(kw);
    
    if (idx !== -1) {
      secondaries.splice(idx, 1);
      if (oldPrimary) secondaries.push(oldPrimary);
      
      keywords.primary_keyword = kw;
      keywords.secondary_keywords = secondaries;
      
      // Update editedKeywords for sync
      editedKeywords = { ...keywords };
      
      // Voice feedback
      vuiController.speak(`Đã chọn "${kw}" làm từ khóa chính ạ.`);
      
      // Sync to backend
      handleUpdateMetadata(1);
    }
  }

  function toggleEdit() {
    if (isEditing) {
      // Cancel edit: revert to last known good state
      if (viewingStep === 1) editedKeywords = { ...keywords };
      if (viewingStep === 3) editedOutline = { sections: [...(outline.sections || []).map(s => ({...s}))] };
      if (viewingStep === 4) editedDraft = draft_content;
      isEditing = false;
    } else {
      isEditing = true;
    }
  }

  function toggleExpand() {
    nanobot.toggleExpand();
  }

  // Handle Escape key to close expanded view
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape" && nanobot.isExpanded) {
      nanobot.toggleExpand(false);
    }
  }

  // Design 2026: Mouse-tracking Glow (Rule R82.42)
  function handleMouseMove(e: MouseEvent) {
    const target = e.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    target.style.setProperty("--mouse-x", `${x}%`);
    target.style.setProperty("--mouse-y", `${y}%`);
  }
</script>

<svelte:window onkeydown={handleKeyDown} />

<div
  class="content-review-card relative group flex flex-col {nanobot.isExpanded ? 'w-full h-full bg-transparent border-none shadow-none p-0' : 'mt-4 rounded-2xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.3)] overflow-hidden transition-all duration-700 hover:border-blue-500/30 p-5 h-full'}"
  in:fade={{ duration: 400 }}
>
  <!-- Background Glow (only in normal mode) -->
  {#if !nanobot.isExpanded}
    <div
      class="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 blur-[80px] rounded-full pointer-events-none group-hover:bg-blue-500/20 transition-all duration-700"
    ></div>
  {/if}

  <div class="flex items-center justify-between mb-5 relative z-10 {nanobot.isExpanded ? 'mb-8' : ''}">
    <div class="flex items-center gap-3">
      <div
        class="p-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/20 shadow-inner"
      >
        {#if viewingStep === 1} <Sparkles size={16} />
        {:else if viewingStep === 2} <ImageIcon size={16} />
        {:else if viewingStep === 3} <FileText size={16} />
        {:else if viewingStep === 4} <FileText size={16} />
        {:else if viewingStep === 5} <ShieldCheck size={16} />
        {:else} <CheckCircle size={16} />
        {/if}
      </div>
      <div class="flex flex-col">
        <span class="text-[10px] uppercase font-black tracking-[0.2em] text-blue-400/80">
          Phase {viewingStep}
        </span>
        <span class="text-xs font-bold text-white/90">
          {#if viewingStep === 1}Keyword Analysis
          {:else if viewingStep === 2}Asset Hunting
          {:else if viewingStep === 3}Content Outline
          {:else if viewingStep === 4}Drafting
          {:else if viewingStep === 5}Plagiarism Audit
          {:else}Finalization
          {/if}
        </span>
      </div>

      {#if status === "PROCESSING"}
        <div
          class="ml-2 flex items-center gap-1.5 px-2 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-400 animate-pulse"
        >
          <RotateCcw size={10} class="animate-spin" />
          <span class="font-medium">{progress_msg || "AI is working..."}</span>
        </div>
      {/if}
    </div>

    <div class="flex items-center gap-2 relative z-[2000]">
      <button
        onclick={toggleExpand}
        class="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-white/40 hover:text-white border border-white/5 transition-all duration-300"
        title={nanobot.isExpanded ? "Collapse View" : "Expand to Neural Fullview"}
      >
        {#if nanobot.isExpanded}
          <Minimize2 size={16} />
        {:else}
          <Maximize2 size={16} />
        {/if}
      </button>

      {#if step > 1}
      <button
        onclick={() => showContext = !showContext}
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg {showContext ? 'bg-blue-500 text-white' : 'bg-white/5 text-white/40 hover:text-white'} border border-white/5 transition-all duration-300"
        title="Toggle Context Panel (Review previous steps)"
      >
        <MessageSquare size={14} />
        <span class="text-[10px] font-black uppercase tracking-wider">Context</span>
      </button>
      {/if}

    {#if status === "WAITING_FOR_REVIEW" && (viewingStep === 1 || viewingStep === 3 || viewingStep === 4)}
      <button
        onclick={toggleEdit}
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-white/60 hover:text-white border border-white/5 transition-all duration-300"
      >
        {#if isEditing}
          <X size={14} />
          <span class="text-xs font-semibold">Hủy</span>
        {:else}
          <Edit2 size={14} />
          <span class="text-xs font-semibold">Chỉnh sửa</span>
        {/if}
      </button>
      {/if}
    </div>
  </div>

  <!-- Phase Navigation Tabs -->
  {#if step > 1}
  <div class="flex gap-1 mb-6 p-1 bg-black/20 rounded-xl border border-white/5 w-fit relative z-10">
    {#each Array.from({length: Math.min(step, 5)}, (_, i) => i + 1) as s}
      <button
        onclick={() => { viewingStep = s; isEditing = false; }}
        class="px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all
          {viewingStep === s ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'text-white/40 hover:text-white/70 hover:bg-white/5'}"
      >
        Step {s}
      </button>
    {/each}
  </div>
  {/if}

  <div class="flex-1 flex gap-6 min-h-0 overflow-hidden relative z-10">
    <div class="flex-1 space-y-5 flex flex-col min-h-0 overflow-hidden">
      <!-- MAIN WORKSPACE -->
      {#if viewingStep === 1}
      {#if isEditing}
        <div class="space-y-4">
          <div class="group/input">
            <label for="title-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Tiêu đề bài viết</label>
            <div class="relative">
              <MessageSquare size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                id="title-{campaign_id}"
                bind:value={editedKeywords.title}
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
        <div class="group/input">
            <label for="primary-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa chính</label>
            <div class="relative">
              <Sparkles size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-white/20" />
              <input
                id="primary-{campaign_id}"
                bind:value={editedKeywords.primary_keyword}
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </div>
          <!-- B2 FIX: secondary_keywords tag editor -->
          <div class="group/input">
            <label class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Từ khóa phụ</label>
            <div class="flex flex-wrap gap-2 p-3 bg-black/20 border border-white/10 rounded-xl min-h-[44px]">
              {#each (editedKeywords.secondary_keywords || []) as kw, kwIdx}
                <span class="flex items-center gap-1 px-2 py-1 rounded-full bg-white/10 border border-white/10 text-xs text-white/70">
                  {kw}
                  <button
                    type="button"
                    onclick={() => {
                      const arr = [...(editedKeywords.secondary_keywords || [])];
                      arr.splice(kwIdx, 1);
                      editedKeywords.secondary_keywords = arr;
                    }}
                    class="ml-1 text-white/30 hover:text-red-400 transition-colors"
                  >&times;</button>
                </span>
              {/each}
              <input
                placeholder="Thêm từ khóa + Enter"
                class="flex-1 min-w-[120px] bg-transparent text-xs text-white/60 placeholder-white/20 outline-none"
                onkeydown={(e) => {
                  if ((e.key === 'Enter' || e.key === ',') && e.currentTarget.value.trim()) {
                    e.preventDefault();
                    const arr = [...(editedKeywords.secondary_keywords || []), e.currentTarget.value.trim()];
                    editedKeywords.secondary_keywords = arr;
                    e.currentTarget.value = '';
                  }
                }}
              />
            </div>
          </div>
          
          <!-- Meta Description -->
          <div class="group/input">
            <label for="desc-{campaign_id}" class="text-[10px] text-white/40 uppercase font-bold mb-1.5 ml-1 block">Meta Description (SEO)</label>
            <div class="relative">
              <FileText size={14} class="absolute left-3 top-3 text-white/20" />
              <textarea
                id="desc-{campaign_id}"
                bind:value={editedKeywords.description}
                rows="3"
                class="w-full bg-black/20 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-all resize-none"
                placeholder="Nhập mô tả chuẩn SEO..."
              ></textarea>
            </div>
          </div>
        </div>
      {:else}
        <div class="space-y-2">
          <h4 class="text-lg font-bold text-white leading-snug tracking-tight">
            {keywords.title || 'Đang phân tích tiêu đề...'}
          </h4>
          <p class="text-[11px] text-white/40 font-medium uppercase tracking-wider">Style: 
            <span class="text-white/70 italic">{keywords.persona || 'Chuyên gia phân tích'}</span>
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          {#if keywords.primary_keyword}
            <button 
              class="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-[11px] font-bold border border-blue-500/30 hover:bg-blue-500/30 transition-all shadow-lg shadow-blue-500/5 cursor-default"
              title="Từ khóa chính hiện tại"
            >
              {keywords.primary_keyword}
            </button>
          {:else}
            <span class="px-3 py-1 rounded-full bg-white/5 text-white/20 text-[11px] font-medium border border-white/5 animate-pulse">
              Đang chờ từ khóa...
            </span>
          {/if}
          
          {#each (keywords.secondary_keywords || []) as kw}
            <button 
              onclick={() => handleSelectKeyword(kw)}
              class="px-3 py-1 rounded-full bg-white/5 text-white/40 text-[11px] font-medium border border-white/5 hover:border-blue-500/30 hover:text-blue-400/80 transition-all active:scale-95"
              title="Click để chọn làm Từ khóa chính"
            >
              {kw}
            </button>
          {/each}
        </div>

        {#if keywords.description}
          <div class="p-3 rounded-xl bg-white/[0.03] border border-white/5 relative group/desc">
            <div class="flex items-center gap-2 mb-1 text-white/30 group-hover/desc:text-blue-400 transition-colors">
              <FileText size={10} />
              <span class="text-[9px] font-black uppercase tracking-widest">SEO Meta Description</span>
            </div>
            <p class="text-[11px] text-white/60 leading-relaxed italic line-clamp-2">
              "{keywords.description}"
            </p>
          </div>
        {/if}
      {/if}

    <!-- STEP 2: ASSET GALLERY (DESIGN 2026 - NEURAL MATRIX) -->
    {:else if viewingStep === 2}
      <div class="space-y-4 {nanobot.isExpanded ? 'flex-1 overflow-hidden flex flex-col' : 'min-h-[400px]'}">
        <div class="flex items-center justify-between mb-1">
          <div class="flex items-center gap-3">
             <div class="relative w-4 h-4">
                <div class="absolute inset-0 bg-blue-500/40 blur-[4px] rounded-full animate-pulse"></div>
                <div class="absolute inset-1 bg-blue-400 rounded-full shadow-[0_0_8px_rgba(59,130,246,1)]"></div>
             </div>
             <div class="flex flex-col">
                <span class="text-[9px] text-blue-400/60 font-black tracking-[0.4em] leading-none mb-1 uppercase">Neural Asset Repository</span>
                <span class="text-[11px] text-white font-bold opacity-90 tracking-tight leading-none uppercase">SELECT_MODE://ACTIVE</span>
             </div>
          </div>
          <div class="flex items-center gap-2">
            {#if !isProcessing}
              <div class="flex bg-white/5 p-1 rounded-xl border border-white/10 ring-1 ring-black/20 focus-within:ring-blue-500/50 focus-within:border-blue-500/30 transition-all h-8 mr-2">
                <div class="flex items-center justify-center pl-2 text-white/40">
                  <LinkIcon size={12} />
                </div>
                <input 
                  type="url" 
                  placeholder="Dán link ảnh và Enter..." 
                  bind:value={customImageUrl}
                  onkeydown={(e) => {
                    if (e.key === 'Enter' && customImageUrl.trim() && customImageUrl.startsWith('http')) {
                       e.preventDefault();
                       assets = [...assets, customImageUrl.trim()];
                       if (!selectedAvatarUrl) {
                         selectedAvatarUrl = customImageUrl.trim();
                         selectedAssetIndex = assets.length - 1;
                       }
                       customImageUrl = "";
                       syncAssetChanges();
                    }
                  }}
                  class="bg-transparent border-none outline-none text-[10px] text-white placeholder:text-white/30 px-3 w-36 transition-all focus:w-48"
                />
                <button 
                  class="p-1 rounded-lg bg-blue-500 text-white hover:bg-blue-400 disabled:opacity-50 disabled:hover:bg-blue-500 transition-colors"
                  disabled={!customImageUrl.trim() || !customImageUrl.startsWith('http')}
                  onclick={() => {
                    if (customImageUrl.trim() && customImageUrl.startsWith('http')) {
                       assets = [...assets, customImageUrl.trim()];
                       if (!selectedAvatarUrl) {
                         selectedAvatarUrl = customImageUrl.trim();
                         selectedAssetIndex = assets.length - 1;
                       }
                       customImageUrl = "";
                       syncAssetChanges();
                    }
                  }}
                  title="Thêm ảnh"
                >
                  <Plus size={12} />
                </button>
              </div>
            {/if}



            <div class="flex items-center gap-2 px-3 py-1 rounded-full bg-white/[0.03] border border-white/10 backdrop-blur-xl h-8">
               <span class="text-[11px] text-white/50 font-mono">ASSETS: <span class="text-blue-400">{assets.length}</span></span>
            </div>
          </div>
        </div>

        <!-- Design 2026: Premium Bento Matrix Grid -->
        <div class="relative group/matrix {nanobot.isExpanded ? 'flex-1 overflow-hidden flex flex-col' : ''}">
          <!-- Neural Scanline Overlay -->
          <div class="absolute inset-0 pointer-events-none z-10 opacity-[0.02] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_4px,3px_100%]"></div>
          
          <div class="{nanobot.isExpanded ? 'flex-1' : 'max-h-[500px]'} overflow-y-auto pr-2 custom-scrollbar space-y-4 min-h-0">
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {#each (assets || []) as url, i}
                <div 
                  role="button"
                  tabindex="0"
                  onclick={() => {
                    selectedAssetIndex = i;
                    // Rule R82.20: Immediate reaction - speak selection
                    vuiController.speak(`Đã chọn ảnh số ${i+1} ạ.`);
                    syncAssetChanges();
                  }}
                  onkeydown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      selectedAssetIndex = i;
                      vuiController.speak(`Đã chọn ảnh số ${i+1} ạ.`);
                      syncAssetChanges();
                    }
                  }}
                  onmousemove={handleMouseMove}
                  class="group/item relative aspect-[4/3] rounded-2xl overflow-hidden border transition-all duration-500 cursor-pointer
                    {selectedAssetIndex === i ? 'border-blue-500 ring-2 ring-blue-500/30 base-shadow-blue' : 'border-white/5 bg-white/[0.02] hover:border-white/20 hover:scale-[1.02]'}
                    {i % 5 === 0 ? 'lg:col-span-2 lg:row-span-2 aspect-square' : ''}"
                  in:scale={{ duration: 500, delay: i * 40, start: 0.95 }}
                >
                  <!-- Asset Image -->
                  <img 
                    src={url} 
                    alt="Asset {i}" 
                    class="w-full h-full object-cover transition-all duration-1000 group-hover/item:scale-110 {selectedAssetIndex === i ? 'brightness-110' : 'brightness-75 group-hover/item:brightness-100'}"
                    onerror={() => handleImageError(url)}
                  />

                  <!-- Top Actions -->
                  <div class="absolute top-2 right-2 flex flex-col gap-1.5 opacity-0 group-hover/item:opacity-100 transition-opacity z-20">
                    <button 
                      class="p-1.5 rounded-full bg-black/50 hover:bg-red-500/80 text-white/70 hover:text-white backdrop-blur-sm transition-all"
                      onclick={(e) => deleteAsset(i, e)}
                      title="Xóa ảnh"
                    >
                      <Trash2 size={12} />
                    </button>
                    <button 
                      class="p-1.5 rounded-full {selectedAvatarUrl === url ? 'bg-amber-500 text-white' : 'bg-black/50 text-white/70 hover:bg-amber-500/50 hover:text-white'} backdrop-blur-sm transition-all shadow-md"
                      onclick={(e) => {
                         e.stopPropagation();
                         selectedAvatarUrl = url;
                         selectedAssetIndex = i; // Align focus with avatar choice
                         syncAssetChanges();
                      }}
                      title="Chọn làm Ảnh Đại Diện"
                    >
                      <Star size={12} class={selectedAvatarUrl === url ? 'fill-current' : ''} />
                    </button>
                  </div>
                  
                  <!-- Smart Selection Glow -->
                  <div class="absolute inset-0 transition-opacity duration-500 {selectedAssetIndex === i ? 'opacity-100' : 'opacity-0 group-hover/item:opacity-100'} bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none">
                    <div class="absolute bottom-3 left-3 flex items-center gap-2">
                       <div class="p-1.5 rounded-full {selectedAssetIndex === i ? 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]' : 'bg-black/40 backdrop-blur-md'} border border-white/20 transition-all duration-500">
                          <Check size={12} class="text-white" />
                       </div>
                       <span class="text-[9px] font-black text-white uppercase tracking-widest">{selectedAssetIndex === i ? 'Selected' : 'Click to select'}</span>
                    </div>
                  </div>

                  {#if selectedAssetIndex === i}
                    <!-- Reactive Ripple Frame -->
                    <div class="absolute inset-0 border-2 border-blue-400/50 rounded-2xl animate-pulse pointer-events-none"></div>
                  {/if}
                  
                  <!-- Dynamic Mouse Trace -->
                  <div class="absolute inset-0 opacity-0 group-hover/item:opacity-100 transition-opacity duration-300 pointer-events-none bg-[radial-gradient(circle_at_var(--mouse-x,50%)_var(--mouse-y,50%),rgba(59,130,246,0.15)_0%,transparent_50%)]"></div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- B4 FIX: Empty state when AssetHunter found nothing -->
      {#if assets.length === 0 && !isProcessing}
        <div class="flex flex-col items-center justify-center py-12 text-center gap-4" in:fade={{ duration: 300 }}>
          <div class="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
            <ImageIcon size={28} class="text-white/20" />
          </div>
          <div>
            <p class="text-sm font-bold text-white/60">Không tìm thấy ảnh phù hợp</p>
            <p class="text-xs text-white/30 mt-1">Quota Google Search có thể đã hết, hoặc từ khóa quá ít phổ biến.</p>
          </div>
          <button
            onclick={handleRetry}
            class="flex items-center gap-2 px-5 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold transition-all"
          >
            <RotateCcw size={14} />
            Tìm lại ảnh
          </button>
        </div>
      {/if}

    <!-- STEP 3: DOCUMENT EDITOR (Outline) -->
    {:else if viewingStep === 3}
      <div class="space-y-4 flex-1 overflow-hidden flex flex-col">
        <div class="flex items-center gap-3">
           <div class="w-8 h-px bg-gradient-to-r from-transparent to-blue-500/50"></div>
           <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-blue-400">Content Outline</h5>
        </div>
        
        <div class="flex-1 rounded-2xl flex flex-col relative group transition-all overflow-hidden {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-blue-500/30 bg-black/40' : 'bg-transparent'}">
           <RichTextEditor 
             content={isEditing ? editedDraft : draft_content}
             assets={assets}
             onChange={(val) => {
                if (isEditing) editedDraft = val;
                else draft_content = val;
             }}
             editable={isEditing}
             placeholder="Đang tạo dàn ý..."
             fullScreen={nanobot.isExpanded}
             annotations={editorAnnotations}
           />
        </div>
      </div>

    <!-- STEP 4: CONTENT STUDIO (Editor always on, Copyright/SEO in toolbar) -->
    {:else if viewingStep === 4}
      <div class="flex-1 overflow-hidden flex flex-col gap-3">
        <!-- Studio Label -->
        <div class="flex items-center gap-3 shrink-0">
          <div class="w-8 h-px bg-gradient-to-r from-transparent to-purple-500/50"></div>
          <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-purple-400">Content Studio 2026</h5>
          {#if copyrightResult}
            {@const rc = copyrightResult.risk_level === 'LOW' ? 'text-emerald-400' : copyrightResult.risk_level === 'MEDIUM' ? 'text-yellow-400' : 'text-red-400'}
            <span class="text-[9px] font-black uppercase {rc}">
              · Copyright {Math.round(copyrightResult.uniqueness_score * 100)}%
            </span>
          {/if}
          {#if seoResult}
            {@const gc = seoResult.grade === 'A' ? 'text-emerald-400' : seoResult.grade === 'B' ? 'text-blue-400' : seoResult.grade === 'C' ? 'text-yellow-400' : 'text-red-400'}
            <span class="text-[9px] font-black uppercase {gc}">
              · SEO {seoResult.grade} ({seoResult.total_score}/100)
            </span>
          {/if}
        </div>

        <!-- Editor (always visible, Copyright/SEO buttons injected into toolbar) -->
        <div class="flex-1 rounded-2xl flex flex-col relative transition-all overflow-hidden min-h-0 {isEditing ? 'border border-white/10 shadow-2xl ring-2 ring-purple-500/30 bg-black/40' : 'bg-transparent'}">
          <RichTextEditor
            bind:this={editorRef}
            content={isEditing ? editedDraft : draft_content}
            assets={assets}
            onChange={(val) => {
              if (isEditing) editedDraft = val;
              else draft_content = val;
            }}
            editable={isEditing}
            placeholder="AI đang chấp bút bản thảo..."
            fullScreen={nanobot.isExpanded}
            toolbarActions={[
              { label: isCopyrightLoading ? '...' : '🔍 Bản Quyền', loading: isCopyrightLoading, onclick: runCopyrightCheck },
              { label: isSeoLoading ? '...' : '📊 SEO', loading: isSeoLoading, onclick: runSeoAnalysis },
              { label: isAiLoading ? '...' : '✨ AI 2026', loading: isAiLoading, onclick: runAiAnalysis }
            ]}
            annotations={editorAnnotations}
            onfix={runAutoFix}
          />
        </div>

        <!-- Analysis Results (compact, scrollable, below editor) -->
        {#if copyrightResult || isCopyrightLoading || seoResult || isSeoLoading || aiReadyResult || isAiLoading}
          <div class="shrink-0 max-h-52 overflow-y-auto custom-scrollbar flex flex-col gap-2">
            
            <div class="flex items-center gap-2">
                <button 
                  onclick={runCopyrightCheck}
                  disabled={isCopyrightLoading}
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/40 border {copyrightResult ? 'border-green-500/30 text-green-400' : 'border-white/10 text-white/60'} hover:bg-white/5 transition-colors disabled:opacity-50"
                >
                  {#if isCopyrightLoading}
                    <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
                  {:else}
                    <ShieldCheck size={12} />
                  {/if}
                  <span class="text-[10px] uppercase font-bold tracking-wider">Bản quyền</span>
                </button>

                <button 
                  onclick={runSeoAnalysis}
                  disabled={isSeoLoading}
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/40 border {seoResult ? 'border-blue-500/30 text-blue-400' : 'border-white/10 text-white/60'} hover:bg-white/5 transition-colors disabled:opacity-50"
                >
                  {#if isSeoLoading}
                    <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
                  {:else}
                    <BarChart2 size={12} />
                  {/if}
                  <span class="text-[10px] uppercase font-bold tracking-wider">SEO</span>
                </button>

                <button 
                  onclick={runAiAnalysis}
                  disabled={isAiLoading}
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/40 border {aiReadyResult ? 'border-purple-500/30 text-purple-400' : 'border-white/10 text-white/60'} hover:bg-white/5 transition-colors disabled:opacity-50"
                  title="Kiểm tra mức độ thân thiện với LLM/AI Crawlers"
                >
                  {#if isAiLoading}
                    <span class="inline-block w-3 h-3 border-2 border-white/20 border-t-white/80 rounded-full animate-spin"></span>
                  {:else}
                    <Sparkles size={12} />
                  {/if}
                  <span class="text-[10px] uppercase font-bold tracking-wider">AI 2026</span>
                </button>
            </div>

            <!-- Copyright Result -->
            {#if isCopyrightLoading}
              <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-orange-500/5 border border-orange-500/10 text-[9px] text-orange-400/70 animate-pulse">
                <span class="inline-block w-2.5 h-2.5 border border-orange-400/40 border-t-transparent rounded-full animate-spin"></span>
                Google Search → Gemini AI đang phân tích đạo văn...
              </div>
            {:else if copyrightResult}
              {@const pct = Math.round(copyrightResult.uniqueness_score * 100)}
              {@const circ = 2 * Math.PI * 36}
              {@const riskColor = copyrightResult.risk_level === 'LOW' ? '#10b981' : copyrightResult.risk_level === 'MEDIUM' ? '#f59e0b' : '#ef4444'}
              <div class="px-3 py-2 rounded-xl border flex items-center gap-4"
                style="background: {riskColor}08; border-color: {riskColor}20;"
              >
                <!-- Mini circular gauge -->
                <div class="relative w-12 h-12 shrink-0">
                  <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
                    <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
                    <circle cx="24" cy="24" r="19" fill="none" stroke={riskColor}
                      stroke-width="4"
                      stroke-dasharray={2 * Math.PI * 19}
                      stroke-dashoffset={2 * Math.PI * 19 * (1 - copyrightResult.uniqueness_score)}
                      stroke-linecap="round"
                      style="transition:stroke-dashoffset 1s ease"
                    />
                  </svg>
                  <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{riskColor}">{pct}%</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-[9px] font-black uppercase" style="color:{riskColor}">
                      🔍 Bản quyền — {copyrightResult.risk_level === 'LOW' ? 'Rủi ro thấp ✅' : copyrightResult.risk_level === 'MEDIUM' ? 'Cần cải thiện ⚠️' : 'Rủi ro cao 🚨'}
                    </span>
                    <button onclick={runCopyrightCheck} class="text-[8px] text-white/20 hover:text-orange-400 transition-colors">↻</button>
                  </div>
                  <p class="text-[9px] text-white/50 leading-relaxed truncate">{copyrightResult.verdict}</p>
                  {#if copyrightResult.flagged_sentences?.length > 0}
                    <p class="text-[8px] text-orange-400/60 mt-0.5">⚠️ {copyrightResult.flagged_sentences.length} đoạn có rủi ro</p>
                    <div class="mt-1 flex flex-col gap-0.5">
                      {#each copyrightResult.flagged_sentences.slice(0, 3) as sentence}
                        {@const snippetKey = typeof sentence === 'string' ? sentence : (sentence.text || '')}
                        <p class="text-[8px] text-white/30 truncate">• "{snippetKey.slice(0, 50)}..."</p>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
            {/if}

            <!-- SEO Result -->
            {#if isSeoLoading}
              <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-500/5 border border-blue-500/10 text-[9px] text-blue-400/70 animate-pulse">
                <span class="inline-block w-2.5 h-2.5 border border-blue-400/40 border-t-transparent rounded-full animate-spin"></span>
                Gemini AI đang chấm điểm 7 tín hiệu SEO 2026...
              </div>
            {:else if seoResult}
              {@const gradeColor = seoResult.grade === 'A' ? '#10b981' : seoResult.grade === 'B' ? '#3b82f6' : seoResult.grade === 'C' ? '#f59e0b' : '#ef4444'}
              <div class="px-3 py-2 rounded-xl border flex flex-col gap-2"
                style="background: {gradeColor}08; border-color: {gradeColor}20;"
              >
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-lg shrink-0 flex items-center justify-center font-black text-lg" style="background:{gradeColor}15; color:{gradeColor}">{seoResult.grade}</div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="text-[9px] font-black uppercase" style="color:{gradeColor}">📊 SEO Score — {seoResult.total_score}/100</span>
                      <button onclick={runSeoAnalysis} class="text-[8px] text-white/20 hover:text-blue-400 transition-colors">↻</button>
                    </div>
                    <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{seoResult.summary}</p>
                  </div>
                </div>
                <!-- Mini signal bars -->
                {#if seoResult.signals?.length > 0}
                  <div class="grid grid-cols-2 gap-1">
                    {#each seoResult.signals.slice(0, 4) as signal}
                      {@const c = signal.score >= 80 ? '#10b981' : signal.score >= 60 ? '#3b82f6' : signal.score >= 40 ? '#f59e0b' : '#ef4444'}
                      <div class="flex items-center gap-1.5">
                        <span class="text-[7px] text-white/30 uppercase truncate w-16">{signal.label.replace(/_/g,' ')}</span>
                        <div class="flex-1 h-0.5 rounded-full bg-white/5 overflow-hidden">
                          <div class="h-full rounded-full" style="width:{signal.score}%;background:{c}"></div>
                        </div>
                        <span class="text-[7px] font-black" style="color:{c}">{signal.score}</span>
                      </div>
                    {/each}
                  </div>
                {/if}
                {#if seoResult.quick_wins?.length > 0}
                  <p class="text-[8px] text-blue-300/50">⚡ {seoResult.quick_wins[0]}</p>
                {/if}
                {#if seoResult.seo_annotations?.length > 0}
                  <div class="mt-1 flex flex-col gap-0.5">
                    {#each seoResult.seo_annotations.slice(0, 3) as ann}
                      <p class="text-[8px] text-white/30 truncate">• {ann.message.slice(0, 40)}...</p>
                    {/each}
                  </div>
                {/if}
              </div>
            {/if}

            <!-- AI Readiness Result -->
            {#if isAiLoading}
              <div class="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-500/5 border border-purple-500/10 text-[9px] text-purple-400/70 animate-pulse">
                <span class="inline-block w-2.5 h-2.5 border border-purple-400/40 border-t-transparent rounded-full animate-spin"></span>
                Gemini AI đang phân tích mức độ thân thiện với LLM Crawler...
              </div>
            {:else if aiReadyResult}
              {@const aiPct = aiReadyResult.geo_score}
              {@const aiColor = aiPct >= 85 ? '#a855f7' : aiPct >= 65 ? '#d946ef' : '#ef4444'}
              <div class="px-3 py-2 rounded-xl border flex items-center gap-4"
                style="background: {aiColor}08; border-color: {aiColor}20;"
              >
                <!-- Mini circular gauge -->
                <div class="relative w-12 h-12 shrink-0">
                  <svg class="w-full h-full -rotate-90" viewBox="0 0 48 48">
                    <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="4"/>
                    <circle cx="24" cy="24" r="19" fill="none" stroke={aiColor}
                      stroke-width="4"
                      stroke-dasharray={2 * Math.PI * 19}
                      stroke-dashoffset={2 * Math.PI * 19 * (1 - aiPct/100)}
                      stroke-linecap="round"
                      style="transition:stroke-dashoffset 1s ease"
                    />
                  </svg>
                  <span class="absolute inset-0 flex items-center justify-center text-[9px] font-black" style="color:{aiColor}">{aiPct}%</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="text-[9px] font-black uppercase tracking-wider" style="color:{aiColor}">
                      ✨ AI Readiness
                    </span>
                    <button onclick={runAiAnalysis} class="text-[8px] text-white/20 hover:text-purple-400 transition-colors">↻</button>
                  </div>
                  <p class="text-[9px] text-white/50 leading-relaxed line-clamp-2">{aiReadyResult.summary}</p>
                  {#if aiReadyResult.ai_annotations?.length > 0}
                    <div class="mt-1 flex flex-col gap-0.5">
                      {#each aiReadyResult.ai_annotations.slice(0, 3) as ann}
                        <p class="text-[8px] text-white/30 truncate">• {ann.message.slice(0, 40)}...</p>
                      {/each}
                    </div>
                  {/if}
                </div>
              </div>
            {/if}

          </div>
        {/if}

      </div>

    <!-- STEP 5: PLAGIARISM CHECK -->
    {:else if viewingStep === 5}
      <div class="space-y-6 flex flex-col h-full overflow-hidden">
        <div class="flex flex-col items-center justify-center py-4 shrink-0">
          <div class="text-center space-y-1 mb-4">
            <p class="text-[9px] text-purple-400/60 font-black tracking-[0.4em] uppercase">Neural Shield // Uniqueness Scan</p>
            <h5 class="text-[13px] font-black text-white uppercase tracking-[0.15em]">XÁC MINH ĐỘ ĐỘC BẢN</h5>
          </div>

          {#if isProcessing}
            <div class="w-36 h-36 rounded-full border-4 border-white/10 flex items-center justify-center animate-pulse">
              <p class="text-white/40 text-xs text-center font-bold px-4 tracking-widest">ĐANG PHÂN TÍCH<br/>NGỮ NGHĨA...</p>
            </div>
          {:else}
            {@const pct = Math.round(uniqueScore * 100)}
            {@const color = pct >= 85 ? '#10b981' : pct >= 70 ? '#f59e0b' : '#ef4444'}
            {@const label = pct >= 85 ? 'ĐỘC BẢN CAO' : pct >= 70 ? 'CẦN CẢI THIỆN' : 'CẦN VIẾT LẠI'}
            {@const circumference = 2 * Math.PI * 54}
            <div class="relative w-36 h-36">
              <svg class="w-full h-full -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="54" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="8" />
                <circle 
                  cx="60" cy="60" r="54" fill="none" 
                  stroke={color}
                  stroke-width="8"
                  stroke-dasharray={circumference}
                  stroke-dashoffset={circumference * (1 - uniqueScore)}
                  stroke-linecap="round"
                  style="transition: stroke-dashoffset 1s ease-in-out; filter: drop-shadow(0 0 8px {color})"
                />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="text-3xl font-black" style="color: {color}">{pct}%</span>
                <span class="text-[8px] font-black uppercase tracking-widest" style="color: {color}">{label}</span>
              </div>
            </div>
          {/if}
        </div>

        <div class="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-1">
          {#if !isProcessing && copyrightResult}
            <!-- AI Verdict -->
            <div class="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
              <div class="flex items-center gap-2 text-purple-400">
                <Sparkles size={14} />
                <span class="text-[10px] font-black uppercase tracking-wider">Nhận định của XoHi</span>
              </div>
              <p class="text-[12px] text-white/80 leading-relaxed font-bold italic">"{copyrightResult.verdict}"</p>
            </div>

            <!-- Flagged Sentences -->
            {#if copyrightResult.flagged_sentences?.length > 0}
              <div class="space-y-3">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-red-400">
                    <ShieldAlert size={14} />
                    <span class="text-[10px] font-black uppercase tracking-wider">Đoạn văn cần lưu ý</span>
                  </div>
                  <button 
                    onclick={() => { viewingStep = 4; isEditing = true; }}
                    class="text-[9px] font-bold text-blue-400 hover:text-blue-300 transition-colors uppercase flex items-center gap-1"
                  >
                    <Edit3 size={10} /> Sửa Bài Viết
                  </button>
                </div>
                <div class="space-y-2">
                  {#each copyrightResult.flagged_sentences as sentence}
                    <div class="p-3 rounded-xl bg-red-500/5 border border-red-500/10 text-[11px] text-white/70 leading-relaxed">
                      {typeof sentence === 'string' ? sentence : sentence.text}
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            <!-- Similar Sources -->
            {#if copyrightResult.similar_sources?.length > 0}
              <div class="space-y-2">
                <div class="flex items-center gap-2 text-white/30">
                  <LinkIcon size={14} />
                  <span class="text-[10px] font-black uppercase tracking-wider">Nguồn tương đồng (Top Google)</span>
                </div>
                <div class="flex flex-wrap gap-2">
                  {#each copyrightResult.similar_sources as url}
                    <a href={url} target="_blank" class="px-2 py-1 rounded-lg bg-white/5 border border-white/5 text-[9px] text-white/40 hover:text-white transition-all max-w-[200px] truncate">
                      {url}
                    </a>
                  {/each}
                </div>
              </div>
            {/if}
          {:else if !isProcessing}
            <div class="flex flex-col items-center justify-center py-12 gap-3 text-white/20">
              <p class="text-sm italic">"Review the detailed draft below while scan is finalized..."</p>
            </div>
          {/if}

          {#if draft_content}
            <div class="p-4 rounded-xl bg-black/20 border border-white/5 prose prose-invert prose-sm max-w-none text-white/50 text-[12px] leading-relaxed">
              {@html draft_content}
            </div>
          {/if}
        </div>
      </div>

    <!-- STEP 6: FINAL PREVIEW & PUBLISH -->
    {:else if viewingStep === 6}
      <div class="space-y-4 flex-1 overflow-hidden flex flex-col">
        <div class="flex items-center gap-3">
          <div class="w-8 h-px bg-gradient-to-r from-transparent to-green-500/50"></div>
          <h5 class="text-[11px] font-black uppercase tracking-[0.2em] text-green-400">Final Article Preview</h5>
        </div>

        {#if keywords.title}
          <div class="flex items-center gap-3 p-3 rounded-xl bg-black/20 border border-white/5 shrink-0">
            {#if selectedAvatarUrl}
              <img src={selectedAvatarUrl} alt="avatar" class="w-14 h-14 rounded-xl object-cover shrink-0 border border-white/10" />
            {/if}
            <div class="min-w-0">
              <p class="text-sm font-bold text-white leading-snug line-clamp-2">{keywords.title}</p>
              {#if keywords.primary_keyword}
                <span class="mt-1 inline-block px-2 py-0.5 rounded-full bg-green-500/20 text-green-300 text-[10px] font-bold border border-green-500/20">
                  {keywords.primary_keyword}
                </span>
              {/if}
            </div>
          </div>
        {/if}

        <div class="flex-1 overflow-y-auto custom-scrollbar rounded-2xl bg-black/20 border border-white/5 p-4">
            {#if finalHtml}
              <div class="prose prose-invert prose-sm max-w-none text-white/90 text-[13px] leading-relaxed selection:bg-green-500/30">
                {@html finalHtml}
              </div>
            {:else if draft_content}
              <div class="prose prose-invert prose-sm max-w-none text-white/70 text-[13px] leading-relaxed opacity-60">
                {@html draft_content}
              </div>
            {:else}
              <div class="flex flex-col items-center justify-center py-12 gap-3 text-white/20">
                <RotateCcw size={32} class="animate-spin opacity-20" />
                <p class="text-sm">Hệ thống đang đóng gói bản thảo cuối cùng...</p>
              </div>
            {/if}
          </div>

          <!-- Final Metadata/Publish Controls -->
          <div class="grid grid-cols-2 gap-3 shrink-0">
            <div class="p-3 rounded-xl bg-green-500/5 border border-green-500/10 space-y-2">
              <p class="text-[9px] font-black text-green-400 uppercase tracking-widest">Target Slug</p>
              <div class="flex items-center gap-2 group">
                <span class="text-[11px] text-white/40 font-mono tracking-tighter">fast.vn/blog/</span>
                <input 
                  type="text" 
                  bind:value={keywords.slug}
                  placeholder={keywords.title?.toLowerCase().replace(/\s+/g,'-').replace(/[^\w-]/g,'')} 
                  class="bg-transparent border-none p-0 text-[11px] font-bold text-white focus:ring-0 w-full"
                />
              </div>
            </div>
            <div class="p-3 rounded-xl bg-blue-500/5 border border-blue-500/10 space-y-2">
              <p class="text-[9px] font-black text-blue-400 uppercase tracking-widest">Category</p>
              <div class="flex items-center justify-between">
                <input 
                  type="text" 
                  bind:value={keywords.category}
                  class="bg-transparent border-none p-0 text-[11px] font-bold text-white focus:ring-0 w-full"
                />
                <Edit2 size={10} class="text-white/20" />
              </div>
            </div>
          </div>
          
          <!-- Step 6 Meta Description Edit -->
          <div class="p-3 rounded-xl bg-purple-500/5 border border-purple-500/10 space-y-2 shrink-0">
             <div class="flex items-center justify-between">
                <p class="text-[9px] font-black text-purple-400 uppercase tracking-widest">Social Meta Description</p>
                <span class="text-[9px] text-white/20 font-mono">{(keywords.description || '').length}/160</span>
             </div>
             <textarea 
                bind:value={keywords.description}
                rows="2"
                class="w-full bg-transparent border-none p-0 text-[11px] text-white/70 leading-relaxed focus:ring-0 resize-none font-medium italic"
                placeholder="Nhập Meta Description cho bài viết..."
             ></textarea>
          </div>

        </div>
  </div>


    <!-- CONTEXT SIDEBAR -->
    {#if showContext && step > 1}
      <div 
        class="w-[300px] border-l border-white/10 pl-6 flex flex-col gap-6 overflow-y-auto custom-scrollbar shrink-0"
        transition:fade={{ duration: 200 }}
      >
         <!-- CONTEXT: STEP 1 (KEYWORDS) -->
         <div class="space-y-3">
            <div class="flex items-center gap-2 text-blue-400 opacity-60">
               <Sparkles size={12} />
               <span class="text-[9px] font-black uppercase tracking-wider">Context: Phase 1 (Keywords)</span>
            </div>
            
            <div class="bg-black/20 rounded-xl p-3 border border-white/5 space-y-3">
               {#if isEditingSidebarKeywords}
                  <div class="space-y-2">
                     <input 
                        bind:value={editedKeywords.title} 
                        placeholder="Tiêu đề..."
                        class="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-[11px] text-white outline-none focus:border-blue-500/50"
                     />
                     <input 
                        bind:value={editedKeywords.primary_keyword} 
                        placeholder="Từ khóa chính..."
                        class="w-full bg-white/5 border border-white/10 rounded-lg px-2 py-1.5 text-[11px] text-white outline-none focus:border-blue-500/50"
                     />
                     <div class="flex gap-1.5">
                        <button 
                           onclick={async () => {
                              await handleUpdateMetadata(1);
                              isEditingSidebarKeywords = false;
                           }}
                           class="flex-1 py-1 rounded-lg bg-blue-600 text-[9px] font-bold text-white uppercase hover:bg-blue-500"
                        >
                           Lưu
                        </button>
                        <button 
                           onclick={() => {
                              editedKeywords = { ...keywords };
                              isEditingSidebarKeywords = false;
                           }}
                           class="flex-1 py-1 rounded-lg bg-white/5 text-[9px] font-bold text-white/50 uppercase hover:bg-white/10"
                        >
                           Hủy
                        </button>
                     </div>
                  </div>
               {:else}
                  <div>
                     <div class="text-[8px] text-white/30 uppercase font-bold mb-1">Target Title</div>
                     <div class="text-[11px] text-white/80 font-bold leading-tight line-clamp-2">{keywords.title || "---"}</div>
                  </div>
                  
                  <div class="flex flex-wrap gap-1.5">
                     <button 
                        class="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-300 text-[9px] font-bold border border-blue-500/20 cursor-default"
                        title="Primary Keyword"
                     >
                        {keywords.primary_keyword || "---"}
                     </button>
                     {#each (keywords.secondary_keywords || []).slice(0, 5) as kw}
                        <button 
                           onclick={() => handleSelectKeyword(kw)}
                           class="px-2 py-0.5 rounded-full bg-white/5 text-white/40 text-[9px] border border-white/5 hover:border-blue-500/30 hover:text-blue-400/80 transition-all active:scale-95"
                           title="Promote to Primary"
                        >
                           {kw}
                        </button>
                     {/each}
                  </div>
                  
                  <div class="flex gap-1.5 pt-1">
                     <button 
                        onclick={() => {
                           editedKeywords = { ...keywords };
                           isEditingSidebarKeywords = true;
                        }} 
                        class="flex-1 py-1.5 rounded-lg bg-white/5 text-[9px] text-white/50 hover:text-white hover:bg-white/10 transition-all border border-white/5 font-bold uppercase"
                     >
                        Quick Edit
                     </button>
                     <button 
                        onclick={() => { viewingStep = 1; isEditing = true; }} 
                        class="px-3 py-1.5 rounded-lg bg-white/5 text-[9px] text-white/40 hover:text-white transition-all border border-white/5"
                        title="Go to Full Keyword Editor"
                     >
                        <Maximize2 size={10} />
                     </button>
                  </div>
               {/if}
            </div>
         </div>

         <!-- CONTEXT: STEP 2 (ASSETS) - Only show if current step is >= 2 AND we are not already viewing step 2 -->
         {#if step >= 2 && viewingStep !== 2}
          <div class="space-y-3" transition:fade>
            <div class="flex items-center justify-between">
               <div class="flex items-center gap-2 text-blue-400 opacity-60">
                  <ImageIcon size={12} />
                  <span class="text-[9px] font-black uppercase tracking-wider">Context: Phase 2 (Assets)</span>
               </div>
               <span class="text-[9px] text-white/30 font-mono italic">{assets.length} items</span>
            </div>
            <div class="max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
               <div class="grid grid-cols-2 gap-3">
                  {#each (assets || []) as url, i}
                     <div 
                        role="button"
                        tabindex="0"
                        onclick={() => {
                           selectedAssetIndex = i;
                           syncAssetChanges();
                        }}
                        onkeydown={(e) => {
                           if (e.key === 'Enter' || e.key === ' ') {
                              selectedAssetIndex = i;
                              syncAssetChanges();
                           }
                        }}
                        class="aspect-video rounded-xl overflow-hidden border transition-all duration-300 cursor-pointer relative group/ctx
                           {selectedAssetIndex === i ? 'border-blue-500 ring-2 ring-blue-500/20' : 'border-white/10 bg-black/40 hover:border-white/30'}"
                     >
                        <img 
                           src={url} 
                           alt="asset" 
                           class="w-full h-full object-cover {selectedAssetIndex === i ? 'opacity-100 brightness-110' : 'opacity-50 group-hover/ctx:opacity-100'} transition-all" 
                           onerror={() => handleImageError(url)}
                        />
                        
                        <!-- Mini Actions Overlay -->
                        <div class="absolute top-1 right-1 flex flex-col gap-1 opacity-0 group-hover/ctx:opacity-100 transition-opacity z-10">
                           <button 
                              class="p-1 rounded-full bg-black/60 hover:bg-red-500/80 text-white shadow-lg backdrop-blur-md transition-all"
                              onclick={(e) => deleteAsset(i, e)}
                              title="Xóa hình"
                           >
                              <Trash2 size={10} />
                           </button>
                           <button 
                              class="p-1 rounded-full {selectedAvatarUrl === url ? 'bg-amber-500' : 'bg-black/60 hover:bg-amber-500'} text-white shadow-lg backdrop-blur-md transition-all"
                              onclick={(e) => {
                                 e.stopPropagation();
                                 selectedAvatarUrl = url;
                                 selectedAssetIndex = i;
                                 syncAssetChanges();
                              }}
                              title="Chọn làm Ảnh Đại Diện"
                           >
                              <Star size={10} class={selectedAvatarUrl === url ? 'fill-current' : ''} />
                           </button>
                        </div>

                        {#if selectedAssetIndex === i}
                           <div class="absolute bottom-1 right-1 bg-blue-500 rounded-full p-0.5 shadow-lg">
                              <Check size={8} class="text-white" />
                           </div>
                        {/if}
                     </div>
                  {/each}
               </div>
            </div>
            
            <button 
               onclick={() => { viewingStep = 2; isEditing = false; }} 
               class="w-full py-2 rounded-xl bg-white/5 text-[10px] text-white/50 hover:text-white hover:bg-white/10 transition-all border border-white/5 font-extrabold uppercase tracking-tight"
            >
               Mở Kho Ảnh Chi Tiết
            </button>
         </div>
         {/if}

         <!-- CONTEXT: STEP 3 (OUTLINE) - Only show if current step is >= 3 AND we are not already viewing step 3 -->
         {#if step >= 3 && viewingStep !== 3}
         <div class="space-y-3" transition:fade>
            <div class="flex items-center gap-2 text-blue-400 opacity-60">
               <FileText size={12} />
               <span class="text-[9px] font-black uppercase tracking-wider">Context: Phase 3 (Outline)</span>
            </div>
            
            <div class="bg-black/20 rounded-xl p-3 border border-white/5 space-y-2 max-h-[200px] overflow-y-auto custom-scrollbar">
               {#if outline.sections && outline.sections.length > 0}
                  {#each outline.sections as section, i}
                     <div class="flex items-start gap-2 group/outline">
                        <span class="text-[9px] text-white/20 mt-1 font-mono">0{i+1}</span>
                        <div class="flex-1 min-w-0">
                           <div class="text-[10px] text-white/70 font-bold leading-tight group-hover/outline:text-blue-400 transition-colors cursor-default">
                              {section.heading}
                           </div>
                        </div>
                     </div>
                  {/each}
               {:else}
                  <div class="text-[10px] text-white/20 italic">Chưa có dàn ý chi tiết...</div>
               {/if}
               
               <button 
                  onclick={() => { viewingStep = 3; isEditing = false; }} 
                  class="w-full mt-2 py-1.5 rounded-lg bg-white/5 text-[9px] text-white/40 hover:text-white transition-all border border-white/5 uppercase font-bold"
               >
                  Mở Dàn Ý Chi Tiết
               </button>
            </div>
         </div>
         {/if}

          <div class="p-4 rounded-xl bg-blue-500/5 border border-blue-500/10 text-center mb-6">
            <div class="text-[9px] text-blue-400/50 uppercase font-black mb-1">Neural Advice</div>
            <p class="text-[10px] text-white/40 leading-relaxed italic">"Dữ liệu context giúp AI viết đúng trọng tâm từ khóa và phối hợp hình ảnh tốt hơn."</p>
         </div>
      </div>
    {/if}
  </div>

  {#if resultMsg}
    <div
      class="mt-6 flex items-start gap-3 p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-300 transition-all backdrop-blur-md"
      transition:scale={{ start: 0.95, duration: 300 }}
    >
      <div class="mt-0.5 p-1.5 rounded-full bg-blue-500/20 shadow-lg"><Check size={14} strokeWidth={3} /></div>
      <p class="text-[13px] font-bold leading-relaxed">{resultMsg}</p>
    </div>
  {/if}

  <div class="flex gap-4 mt-auto pt-8 shrink-0 relative z-10 border-t border-white/5 {nanobot.isExpanded ? 'pb-4' : ''}">
    <!-- ACTION 1: REGENERATE / RETRY (Always available as a fallback/abort) -->
    <button
      onclick={handleRetry}
      disabled={isLoading}
      class="flex-1 group/btn-retry relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-white/5 hover:bg-white/10 text-white/50 hover:text-white border border-white/10 transition-all font-black text-[10px] uppercase tracking-[0.2em] active:scale-95 {isProcessing ? 'border-amber-500/20 bg-amber-500/5 text-amber-400' : ''}"
      title="Chạy lại hoặc hủy bỏ để làm lại bước này"
    >
      <div class="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/[0.02] to-white/0 opacity-0 group-hover/btn-retry:opacity-100 transition-opacity"></div>
      <RotateCcw size={16} class={isProcessing ? "animate-spin" : ""} />
      <span>{isProcessing ? "Làm Lại" : "Chạy Lại"}</span>
    </button>

    {#if status === "WAITING_FOR_REVIEW"}
      {#if viewingStep < step}
        <!-- VIEWING PREVIOUS STEP -->
        <button
          onclick={isEditing ? handleUpdateMetadata : () => viewingStep = step}
          disabled={isLoading}
          class="flex-1 group/btn-secondary relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-black text-[10px] uppercase tracking-widest transition-all border border-white/10 disabled:opacity-50 active:scale-95"
        >
          {#if isLoading} <RotateCcw size={16} class="animate-spin" />
          {:else if isEditing} <Save size={16} />
            <span>Lưu thay đổi Phase {viewingStep}</span>
          {:else} <RotateCcw size={16} class="rotate-180" />
            <span>Về Phase {step} (Hiện tại)</span>
          {/if}
        </button>
      {:else}
        <!-- CURRENT STEP ACTION -->
        {#if viewingStep === 6 && step === 6}
          <!-- Step 6: Publish Button -->
          <button
            onclick={handlePublish}
            disabled={isLoading}
            class="flex-1 group/btn-publish relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-green-600 hover:bg-green-500 text-white font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_15px_30px_-10px_rgba(22,163,74,0.4)] disabled:opacity-50 active:scale-95"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn-publish:animate-shimmer pointer-events-none"></div>
            {#if isLoading} <RotateCcw size={16} class="animate-spin" />
            {:else} <Check size={16} strokeWidth={3} />
              <span>Xuất Bản</span>
            {/if}
          </button>
        {:else}
          {#if isEditing}
            <button
              onclick={() => handleUpdateMetadata(step)}
              disabled={isLoading}
              class="flex-1 group/btn-save relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-white/10 hover:bg-white/20 text-white font-black text-[10px] uppercase tracking-widest transition-all border border-white/10 disabled:opacity-50 active:scale-95"
            >
              {#if isLoading} <RotateCcw size={16} class="animate-spin" />
              {:else} <Save size={16} />
                <span>Lưu Bản Thảo</span>
              {/if}
            </button>
          {/if}
          
          <button
            onclick={viewingStep === 6 ? handlePublish : handleApprove}
            disabled={isLoading || isPublishing}
            class="flex-1 group/btn-primary relative overflow-hidden flex items-center justify-center gap-2 py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-black text-[10px] uppercase tracking-widest transition-all shadow-[0_15px_30px_-10px_rgba(37,99,235,0.4)] disabled:opacity-50 active:scale-95"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn-primary:animate-shimmer pointer-events-none"></div>
            {#if isLoading || isPublishing} <RotateCcw size={16} class="animate-spin" />
            {:else} 
              <Check size={16} strokeWidth={3} />
              <span>
                {#if viewingStep === 6} Xuất bản ngay
                {:else if isEditing} Duyệt & Lưu
                {:else} Duyệt & Tiếp tục
                {/if}
              </span>
            {/if}
          </button>
        {/if}
      {/if}
    {/if}
  </div>
</div>

<style>
  .content-review-card {
    position: relative;
    isolation: isolate;
  }

  /* 2026 Nano-Scrollbar */
  .custom-scrollbar::-webkit-scrollbar {
    width: 3px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.1);
    border-radius: 20px;
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(59, 130, 246, 0.6);
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);
  }

  /* Shimmer Animation 2026 */
  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  :global(.animate-shimmer) {
    position: relative;
    overflow: hidden;
  }
  :global(.animate-shimmer::after) {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
    animation: shimmer 1.5s infinite linear;
  }

  /* Matrix Layout Flow */
  :global(.grid-flow-dense) {
    grid-auto-flow: dense;
  }

  .base-shadow-blue {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.2);
  }
</style>
