# Step 5: Real-world Preview & Certification Dashboard

Transform Step 5 from an active checking phase into a "Preview & Certification" dashboard. This step will lock the scores achieved in Step 4 and display them as badges alongside realistic previews of how the content will appear on the web.

## User Review Required

> [!IMPORTANT]
> This plan changes the logic for Step 5. [PlagiarismCop](file:///home/lv/Desktop/fast-platform-core/backend/services/xohi/creative_studio/operatives/plagiarism_cop.py#80-424) will no longer be executed automatically when transitioning from Step 4 to Step 5. Uniqueness must be checked during Step 4. Step 5 becomes a pure presentation layer. Is this acceptable?

## Proposed Changes

### Backend — Orchestrator & Engine

#### [MODIFY] [orchestrator.py](file:///home/lv/Desktop/fast-platform-core/backend/services/xohi/creative_studio/orchestrator.py)
- Re-map the Step 5 operative in `registry.register` or remove the automated trigger. Currently, `registry.register(5, self.cop)` binds PlagiarismCop to Step 5. We need to detach this so transitioning to Step 5 doesn't trigger a new analysis.

#### [MODIFY] [engine.py](file:///home/lv/Desktop/fast-platform-core/backend/services/xohi/creative_studio/handlers/engine.py)
- Update [_execute_step](file:///home/lv/Desktop/fast-platform-core/backend/services/xohi/creative_studio/handlers/engine.py#32-157) to handle Step 5 organically. If Step 5 is just a presentation step, the engine might not need to execute an operative, but simply mark the step as complete and emit the `CONTENT_STEP_COMPLETED` event to hydrate the UI.

---

### Frontend — Component Orchestration

#### [NEW] [ValidationPreviewStep.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/ui/content-factory/ValidationPreviewStep.svelte)
Create a new dedicated component for Step 5 to replace the current reuse of `DraftStep`.
- **Layout**: Split-view architecture (65% left, 35% right).
- **Left Panel (Article Preview)**: Re-render the `draft_content` as a mock news article. Use a clean, typography-focused design resembling VNExpress. Add a toggle for Desktop/Mobile view.
- **Right Panel (Certification Dashboard)**:
  - **Trust Badges**: Display the hydrated `copyrightScore`, `seoScore`, and `aiScore` as large, prominent, locked badges indicating verification.
  - **SERP Simulator**: Google Search result preview (Title, URL, Meta Description).
  - **SGE Simulator**: Google AI Overview simulation (Summary box with citations).
  - **Social Preview**: Open Graph card simulation (Image + Title + Description).

#### [MODIFY] [ContentReviewCard.svelte](file:///home/lv/Desktop/fast-platform-core/frontend/src/lib/components/admin/ui/ContentReviewCard.svelte)
- Import `ValidationPreviewStep`.
- Update the `viewingStep === 5` block to render `ValidationPreviewStep` instead of `DraftStep`.
- Pass necessary props: `draft_content`, `assets`, `keywords`, `analysis_metrics`, `analysis_cache`, `copyrightScore`, `seoScore`, `aiScore`.

## Verification Plan

### Manual Verification
- Complete Step 4, ensuring at least one analysis is run.
- Click "Duyệt" to move to Step 5.
- Verify that the API does not re-trigger a long-running analysis task.
- Verify the UI switches to the split-view dashboard.
- Check that the badges correctly display the scores from Step 4.
- Toggle the mobile/desktop view in the preview panel and verify layout responsiveness.
- Review the SERP, SGE, and Social simulators for formatting accuracy.
