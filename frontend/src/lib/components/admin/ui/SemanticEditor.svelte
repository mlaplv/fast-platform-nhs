<script lang="ts">
  /**
   * SemanticEditor.svelte — Lightweight SGE Semantic HTML Composer
   * Input: bind:value (raw HTML string: <h2>...</h2><ul class="product-highlights"><li>...</li></ul>)
   * Output: auto-composed HTML from structured title + bullets UI
   */
  import { onMount } from "svelte";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";

  interface Props {
    value?: string;
  }

  // ✅ NO default in $bindable() — Svelte 5 rule: initialize in onMount instead
  let { value = $bindable() }: Props = $props();

  // Parse HTML → structured state
  function parseHtml(html: string): { title: string; bullets: string[] } {
    if (!html) return { title: "", bullets: ["", ""] };
    const h2 = html.match(/<h2[^>]*>(.*?)<\/h2>/i)?.[1]?.trim() ?? "";
    const liMatches = [...html.matchAll(/<li[^>]*>(.*?)<\/li>/gi)];
    const bullets = liMatches.map((m) => m[1].trim());
    return { title: h2, bullets: bullets.length ? bullets : ["", ""] };
  }

  // Compose HTML ← structured state
  function composeHtml(title: string, bullets: string[]): string {
    const h2 = title ? `<h2>${title}</h2>` : "";
    const filled = bullets.filter((b) => b.trim());
    if (!h2 && filled.length === 0) return "";
    const lis = filled.map((b) => `\n  <li>${b}</li>`).join("");
    return `${h2}\n<ul class="product-highlights">${lis}\n</ul>`;
  }

  let title = $state("");
  let bullets = $state<string[]>(["", ""]);
  let ready = $state(false);
  let lastExternal = "";

  // ✅ Safe init in onMount — avoids $bindable("") crash when parent passes undefined
  onMount(() => {
    const safeVal = value ?? "";
    const p = parseHtml(safeVal);
    title = p.title;
    bullets = [...p.bullets];
    lastExternal = safeVal;
    ready = true;
  });

  // One-way sync: when value changes externally (XOHI AUTO), re-parse
  $effect(() => {
    if (!ready) return;
    const current = value ?? "";
    if (current !== lastExternal && current !== composeHtml(title, bullets)) {
      const p = parseHtml(current);
      title = p.title;
      bullets = [...p.bullets];
      lastExternal = current;
    }
  });

  // Compose output on every internal change
  $effect(() => {
    if (!ready) return;
    const composed = composeHtml(title, bullets);
    if (composed !== (value ?? "")) {
      value = composed;
      lastExternal = composed;
    }
  });

  function addBullet() {
    bullets = [...bullets, ""];
  }

  function removeBullet(i: number) {
    if (bullets.length <= 1) return;
    bullets = bullets.filter((_, idx) => idx !== i);
  }

  function updateBullet(i: number, val: string) {
    bullets = bullets.map((b, idx) => (idx === i ? val : b));
  }
</script>

<div class="flex flex-col gap-2">
  <!-- H2 Title -->
  <div class="flex items-center gap-2">
    <span class="text-[9px] font-black text-emerald-400/60 tracking-widest shrink-0 w-8 text-center">H2</span>
    <input
      type="text"
      bind:value={title}
      placeholder="Tên sản phẩm (tiêu đề SGE)..."
      class="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-[12px] text-white/80 font-bold placeholder-white/20 outline-none focus:border-emerald-500/40 transition-colors"
    />
  </div>

  <!-- Bullet List -->
  <div class="flex flex-col gap-1.5 pl-10">
    {#each bullets as bullet, i}
      <div class="flex items-center gap-2 group">
        <span class="text-emerald-400 text-[16px] leading-none shrink-0">•</span>
        <input
          type="text"
          value={bullet}
          oninput={(e) => updateBullet(i, (e.currentTarget as HTMLInputElement).value)}
          placeholder="Công dụng / công nghệ nổi bật..."
          class="flex-1 bg-black/30 border border-white/5 rounded-lg px-3 py-1.5 text-[12px] text-white/70 placeholder-white/15 outline-none focus:border-emerald-500/30 transition-colors"
        />
        <button
          type="button"
          onclick={() => removeBullet(i)}
          disabled={bullets.length <= 1}
          class="opacity-0 group-hover:opacity-100 text-white/20 hover:text-red-400 transition-all disabled:pointer-events-none"
        >
          <Trash2 size={12} />
        </button>
      </div>
    {/each}

    <button
      type="button"
      onclick={addBullet}
      class="flex items-center gap-1.5 text-[10px] text-white/25 hover:text-emerald-400 transition-colors mt-1 w-fit"
    >
      <Plus size={12} />
      Thêm bullet
    </button>
  </div>
</div>
