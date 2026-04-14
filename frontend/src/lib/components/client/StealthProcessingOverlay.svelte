<script lang="ts">
  import { Z_INDEX_CLIENT } from '$lib/core/constants/zIndex.ts';

  let { isSubmitting, submissionStep, processingSteps } = $props<{
    isSubmitting: boolean;
    submissionStep: number;
    processingSteps: string[];
  }>();
</script>

{#if isSubmitting}
    <div class="processing-overlay" style:z-index={Z_INDEX_CLIENT.OVERLAY}>
        <div class="glass-loader">
            <div class="loader-ripple"></div>
            <div class="loader-content">
                <div class="step-indicator">
                    {#each processingSteps as _, idx}
                        <div class="step-dot" class:dot-active={submissionStep === idx} class:dot-done={submissionStep > idx}></div>
                    {/each}
                </div>
                <h3 class="processing-title">{processingSteps[submissionStep]}</h3>
                <p class="processing-hint">Vui lòng không đóng cửa sổ này...</p>
            </div>
        </div>
    </div>
{/if}
