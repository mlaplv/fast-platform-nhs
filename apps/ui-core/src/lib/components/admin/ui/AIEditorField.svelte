<script lang="ts">
  import { onDestroy } from "svelte";

  let { value = $bindable("") } = $props();

  let ghostText = $state("");
  let textareaEl: HTMLTextAreaElement;
  let ghostEl: HTMLDivElement;

  let abortController = $state<AbortController | null>(null);
  let debounceTimeout = $state<ReturnType<typeof setTimeout> | null>(null);

  function syncScroll() {
    if (textareaEl && ghostEl) {
      ghostEl.scrollTop = textareaEl.scrollTop;
      ghostEl.scrollLeft = textareaEl.scrollLeft;
    }
  }

  async function fetchGhostSuggestion(currentText: string) {
    if (!currentText.trim() || currentText.length < 5) {
      ghostText = "";
      return;
    }

    abortController = new AbortController();
    try {
      // Stream directly from intent to match semantic flow
      const res = await fetch("/api/v1/intent/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
           query: `[GHOST_COMPLETION] ${currentText}`,
           modality: "text"
        }),
        signal: abortController.signal,
      });

      if (!res.ok) return; // Silent fail for ghost completion
      
      ghostText = "";
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, chunk } = await reader.read();
          if (done) break;
          
          const textChunk = decoder.decode(chunk, { stream: true });
          const lines = textChunk.split("\n").filter(l => l.startsWith("data: "));
          
          for (const line of lines) {
            try {
              const data = JSON.parse(line.slice(6));
              // Bắt phase 'done' hoặc parse token trực tiếp nếu AI_Worker trả stream
              if (data.status === "done" && data.message) {
                 // Gợi ý luôn là text dài, ta chỉ nối nếu message khớp ngữ cảnh,
                 // do hệ thống intent chưa support pure streaming ghost, ta gán hờ message.
                 // (Tuỳ hệ thống thực thụ sẽ gán data.token)
                 // Tạm thời, giả lập text sinh ra nếu BE có trả.
                 ghostText = data.message;
              } else if (data.token) {
                 ghostText += data.token;
              }
            } catch { /* ignore parse error */ }
          }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") console.error("Ghost Error:", e);
    } finally {
      abortController = null;
    }
  }

  function handleInput() {
    ghostText = "";

    if (abortController) {
      abortController.abort();
      abortController = null;
    }

    if (debounceTimeout) clearTimeout(debounceTimeout);

    // 800ms natural typing pause => Zero latency feel for user typing
    debounceTimeout = setTimeout(() => {
      fetchGhostSuggestion(value);
    }, 800); 
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Tab" && ghostText) {
      e.preventDefault(); // Prevent standard tab behavior
      value += ghostText;
      ghostText = "";
      
      if (abortController) {
        abortController.abort();
        abortController = null;
      }
      if (debounceTimeout) clearTimeout(debounceTimeout);
      
      // Auto follow-up suggestion after accepting
      debounceTimeout = setTimeout(() => fetchGhostSuggestion(value), 500);
    }
  }

  onDestroy(() => {
    if (abortController) abortController.abort();
    if (debounceTimeout) clearTimeout(debounceTimeout);
  });
</script>

<div class="ai-editor-wrapper">
  <!-- Layer 1: Ghost Text (Bottom) -->
  <div class="ghost-layer" bind:this={ghostEl} aria-hidden="true">
    <span class="actual-invisible">{value}</span>
    {#if ghostText}
      <span class="ghost-visible">{ghostText}</span>
    {/if}
  </div>

  <!-- Layer 2: Actual Textarea (Top) -->
  <textarea
    bind:this={textareaEl}
    class="real-textarea custom-scrollbar"
    bind:value
    oninput={handleInput}
    onkeydown={handleKeyDown}
    onscroll={syncScroll}
    placeholder="Nhập nội dung... (Ngừng gõ 1s để được gợi ý, nhấn TAB để điền)"
    spellcheck="false"
  ></textarea>

  <div class="hint">
    {#if ghostText}
      <span class="text-[#39FF14] animate-pulse">Nhấn TAB để nhúng tự động</span>
    {:else if abortController}
      <span class="text-[#00FFFF] animate-pulse">XoHi đang suy nghĩ...</span>
    {/if}
  </div>
</div>

<style>
  .ai-editor-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    min-height: 250px;
    flex-grow: 1; /* Stretch in flex layouts */
    background: rgba(0, 0, 0, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.95rem;
    line-height: 1.6;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .ai-editor-wrapper:focus-within {
    border-color: rgba(0, 255, 255, 0.4);
    box-shadow: 0 0 15px rgba(0, 255, 255, 0.05);
    background: rgba(0, 255, 255, 0.01);
  }

  /* GPU-accelerated scrolling for ghost layer */
  .ghost-layer {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    padding: 1rem;
    pointer-events: none;
    white-space: pre-wrap;
    word-wrap: break-word;
    color: transparent;
    overflow: hidden;
    z-index: 1;
    will-change: scroll-position;
  }

  .ghost-layer .actual-invisible {
    color: transparent; /* Makes the original text transparent so only ghost shows after */
  }

  .ghost-layer .ghost-visible {
    color: #475569;
    background: rgba(255,255,255,0.03);
    border-radius: 4px;
  }

  .real-textarea {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    padding: 1rem;
    background: transparent;
    color: #e2e8f0;
    border: none;
    outline: none;
    resize: none;
    white-space: pre-wrap;
    word-wrap: break-word;
    font-family: inherit;
    font-size: inherit;
    line-height: inherit;
    z-index: 2;
  }

  .real-textarea::placeholder {
    color: rgba(255,255,255,0.2);
    font-style: italic;
  }

  .hint {
    position: absolute;
    bottom: 12px;
    right: 16px;
    font-size: 0.65rem;
    font-family: monospace;
    font-weight: bold;
    text-transform: uppercase;
    z-index: 3;
    pointer-events: none;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 20px;
  }
</style>
