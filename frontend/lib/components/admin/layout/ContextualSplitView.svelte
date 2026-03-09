<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    showForm = false,
    mainSlot,
    formSlot,
  }: {
    showForm: boolean;
    mainSlot: Snippet;
    formSlot: Snippet;
  } = $props();
</script>

<div class="canvas-container w-full h-full overflow-hidden flex" class:has-form={showForm}>
  <div class="canvas-main custom-scrollbar">
    {@render mainSlot()}
  </div>
  
  <div class="canvas-form">
    {#if showForm}
      <div class="absolute inset-0 w-full h-full custom-scrollbar form-inner">
        {@render formSlot()}
      </div>
    {/if}
  </div>
</div>

<style>
  .canvas-container {
    background: transparent;
    display: flex;
  }

  /* CPU-bound simple Flex layout requested by user */
  .canvas-main {
    flex: 1;
    height: 100%;
    position: relative;
    transition: width 0.3s ease;
  }
  
  .canvas-form {
    width: 0;
    height: 100%;
    position: relative;
    background: rgba(10, 15, 24, 0.98);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    transition: width 0.3s ease;
    overflow: hidden;
  }

  .canvas-container.has-form .canvas-main {
    width: 40%;
    flex: none;
  }

  .canvas-container.has-form .canvas-form {
    width: 60%;
  }

  @media (max-width: 768px) {
    .canvas-container.has-form .canvas-main {
      display: none;
    }
    .canvas-container.has-form .canvas-form {
      width: 100%;
    }
  }
  .form-inner {
    overflow-y: auto;
    overflow-x: hidden;
  }
  
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
  }
</style>
