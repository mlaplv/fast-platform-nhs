<script lang="ts">
  import { fade } from "svelte/transition";
  import { untrack } from "svelte";
  import Copy from "@lucide/svelte/icons/copy";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import ChevronDown from "@lucide/svelte/icons/chevron-down";
  import type { VideoScript } from "$lib/types";
  import { useNanobot } from "$lib/state/nanobot.svelte";

  const nanobot = useNanobot();

  interface Props {
    activeScript: VideoScript | null;
    triggerAutoSave: () => void;
  }
  let { activeScript, triggerAutoSave }: Props = $props();

  // State
  let imageRefs = $state<{ label: string; url: string }[]>([
    { label: "Mặt trước", url: "" },
    { label: "Mặt sau", url: "" },
  ]);
  let animationStyle = $state("360_spin");
  let endingStyle = $state("logo_reveal");
  let backgroundStyle = $state("dark_gradient");
  let productFeatures = $state<string[]>(["", "", ""]);
  let ctaText = $state("Mua ngay tại osmo.vn");
  let brandTagline = $state("");
  let beforeDesc = $state("Da xỉn màu, thiếu sức sống");
  let afterDesc = $state("Da sáng mịn, căng bóng tự nhiên");

  let activeDropdown = $state<string | null>(null);
  let currentScriptId = $state<string | null>(null);

  // Sync / Load logic
  $effect(() => {
    if (activeScript && activeScript.id !== currentScriptId) {
      currentScriptId = activeScript.id;
      const settings = activeScript.structured_script?.animation_settings as
        | Record<string, any>
        | undefined;

      // Extraction helper for tagline
      const getFallbackTagline = (): string => {
        const compAnalysis =
          activeScript.structured_script?.competitor_analysis;
        if (compAnalysis && compAnalysis.core_message) {
          return compAnalysis.core_message;
        }
        const headlines = activeScript.structured_script
          ?.landing_page_headlines as any[] | undefined;
        if (headlines && headlines.length > 0) {
          return headlines[0].subheadline || headlines[0].headline || "";
        }
        return activeScript.product_name
          ? `Thương hiệu uy tín cho ${activeScript.product_name}`
          : "Vẻ đẹp từ thiên nhiên";
      };

      // Extraction helper for features
      const getFallbackFeatures = (): string[] => {
        const compAnalysis =
          activeScript.structured_script?.competitor_analysis;
        let feats: string[] = [];
        if (compAnalysis && Array.isArray(compAnalysis.our_strengths)) {
          feats = compAnalysis.our_strengths.filter(Boolean);
        }
        if (feats.length === 0) {
          const headlines = activeScript.structured_script
            ?.landing_page_headlines as any[] | undefined;
          if (headlines && headlines.length > 0) {
            feats = headlines.map((h) => h.headline).filter(Boolean);
          }
        }
        const finalFeats = feats.slice(0, 3);
        while (finalFeats.length < 3) {
          finalFeats.push("");
        }
        return finalFeats;
      };

      if (settings) {
        imageRefs = settings.imageRefs
          ? JSON.parse(JSON.stringify(settings.imageRefs))
          : [
              { label: "Mặt trước", url: "" },
              { label: "Mặt sau", url: "" },
            ];
        animationStyle = settings.animationStyle || "360_spin";
        endingStyle = settings.endingStyle || "logo_reveal";
        backgroundStyle = settings.backgroundStyle || "dark_gradient";
        ctaText = settings.ctaText || "Mua ngay tại osmo.vn";
        beforeDesc = settings.beforeDesc || "Da xỉn màu, thiếu sức sống";
        afterDesc = settings.afterDesc || "Da sáng mịn, căng bóng tự nhiên";

        // Tagline fallback if empty
        brandTagline = settings.brandTagline || getFallbackTagline();

        // Features fallback if empty or all elements are empty
        const sFeatures = settings.productFeatures
          ? [...settings.productFeatures]
          : ["", "", ""];
        if (sFeatures.every((f) => !f.trim())) {
          productFeatures = getFallbackFeatures();
        } else {
          productFeatures = sFeatures;
        }
      } else {
        imageRefs = [
          { label: "Mặt trước", url: "" },
          { label: "Mặt sau", url: "" },
        ];
        animationStyle = "360_spin";
        endingStyle = "logo_reveal";
        backgroundStyle = "dark_gradient";
        productFeatures = getFallbackFeatures();
        ctaText = "Mua ngay tại osmo.vn";
        brandTagline = getFallbackTagline();
        beforeDesc = "Da xỉn màu, thiếu sức sống";
        afterDesc = "Da sáng mịn, căng bóng tự nhiên";
      }
    }
  });

  // Auto-save logic
  $effect(() => {
    const stateObj = {
      imageRefs: $state.snapshot(imageRefs),
      animationStyle,
      endingStyle,
      backgroundStyle,
      productFeatures: $state.snapshot(productFeatures),
      ctaText,
      brandTagline,
      beforeDesc,
      afterDesc,
    };

    untrack(() => {
      if (activeScript && activeScript.id === currentScriptId) {
        const currentSettingsStr = JSON.stringify(
          activeScript.structured_script?.animation_settings || {},
        );
        const newSettingsStr = JSON.stringify(stateObj);
        if (currentSettingsStr !== newSettingsStr) {
          activeScript.structured_script.animation_settings = stateObj;
          triggerAutoSave();
        }
      }
    });
  });

  function toggleDd(name: string, e: Event) {
    e.stopPropagation();
    activeDropdown = activeDropdown === name ? null : name;
  }

  const ANIM_STYLES: Record<string, string> = {
    "360_spin": "360° Product Spin",
    before_after: "Before → After",
    ingredient_explode: "Ingredient Explode",
    unboxing: "Unboxing Reveal",
    floating: "Floating Product",
    zoom_detail: "Zoom to Detail",
  };
  const END_STYLES: Record<string, string> = {
    logo_reveal: "Logo Reveal + Tagline",
    feature_cards: "Feature Cards Cascade",
    ba_recap: "Before-After Recap + CTA",
    split_info: "Split Info Panel",
  };
  const BG_STYLES: Record<string, string> = {
    dark_gradient: "Gradient tối cao cấp",
    studio_white: "Studio trắng tinh",
    marble_reflect: "Đá cẩm thạch phản chiếu",
    nature_bokeh: "Thiên nhiên bokeh",
  };
  const BG_PROMPT: Record<string, string> = {
    dark_gradient: "dark minimalist gradient background with subtle depth",
    studio_white: "clean white studio infinity curve background",
    marble_reflect: "polished black marble reflective surface",
    nature_bokeh: "soft natural bokeh background with botanical elements",
  };

  function addImageRef() {
    imageRefs = [...imageRefs, { label: "", url: "" }];
  }
  function removeImageRef(i: number) {
    imageRefs = imageRefs.filter((_, idx) => idx !== i);
  }
  function addFeature() {
    productFeatures = [...productFeatures, ""];
  }
  function removeFeature(i: number) {
    productFeatures = productFeatures.filter((_, idx) => idx !== i);
  }

  let prodName = $derived(
    activeScript?.product_name || activeScript?.title || "sản phẩm",
  );
  let aspectRatio = $derived(
    activeScript?.structured_script?.aspect_ratio || "9:16",
  );
  let brandName = $derived("Miccosmo / osmo.vn");
  let websiteUrl = $derived("osmo.vn");

  let imageRefBlock = $derived(() => {
    const lines = imageRefs
      .filter((r) => r.url.trim())
      .map((r) => `• ${r.label}: ${r.url}`);
    if (!lines.length) return "";
    return `REFERENCE IMAGES (Attach these images in order when submitting to AI):\n${lines.join("\n")}\nCRITICAL: Strictly maintain the exact product design, logo, text, packaging colors and proportions as shown in reference images. Do NOT fabricate, alter or hallucinate any branding elements.`;
  });

  let featuresListPrompt = $derived(() => {
    return productFeatures
      .filter((f) => f.trim())
      .map((f, i) => `• Card ${i + 1}: "✦ ${f}" — slides in, holds 0.8s`)
      .join("\n");
  });

  let outroBlock = $derived(() => {
    const feats = productFeatures.filter((f) => f.trim());
    const fl = feats.map((f, i) => `  — "${f}"`).join("\n");
    if (endingStyle === "logo_reveal")
      return `ENDING SEQUENCE (Final 3-4 seconds):\nThe product gently settles into final position at center frame. Smooth fade-to-dark transition. The brand logo "${brandName}" elegantly fades in at center with a soft luminous glow animation — clean, minimal, white on dark. Below the logo, the tagline "${brandTagline || "Vẻ đẹp từ bên trong"}" appears with a subtle letter-by-letter reveal animation. Soft ambient light pulse behind the logo. The website URL "${websiteUrl}" fades in below in small, elegant typography. Premium, cinematic, luxury brand ending. Hold for 2 seconds.`;
    if (endingStyle === "feature_cards")
      return `ENDING SEQUENCE (Final 4-6 seconds):\nThe product remains in center frame with soft focus background. Elegant floating text cards appear one-by-one beside the product with smooth slide-in animation from right:\n${featuresListPrompt()}\nEach card has a subtle frosted glass effect with clean sans-serif typography. After all features display, they fade out and the brand logo "${brandName}" with tagline "${brandTagline || "Vẻ đẹp từ bên trong"}" fades in at center. Website "${websiteUrl}" appears below. Premium commercial typography. Hold final frame for 2 seconds.`;
    if (endingStyle === "ba_recap")
      return `ENDING SEQUENCE (Final 4-5 seconds):\nQuick flashback montage: brief 0.5s flash of the "before" state, then smooth cross-dissolve to the "after" result with the product front-and-center. The product glows with a warm, inviting halo. Clean text overlay appears: "${ctaText}" in bold, high-contrast typography with a subtle pulsing animation. Below: brand logo "${brandName}" and "${websiteUrl}". Confident, persuasive, conversion-optimized ending. Hold for 2 seconds.`;
    return `ENDING SEQUENCE (Final 4-6 seconds):\nThe frame divides into a premium split layout:\nLEFT SIDE (60%): The product in hero pose — slight rotation, dramatic lighting, floating with subtle particle effects.\nRIGHT SIDE (40%): Clean dark panel with stacked product information:\n  — Product name: "${prodName}"\n${fl}\n  — Brand logo "${brandName}"\n  — Website: "${websiteUrl}"\n  — CTA: "${ctaText}" with subtle glow border\nAll text appears with smooth staggered fade-in animation. Premium editorial layout. Hold for 3 seconds.`;
  });

  let generatedPrompt = $derived(() => {
    const bg = BG_PROMPT[backgroundStyle] || BG_PROMPT["dark_gradient"];
    const iRef = imageRefBlock();
    const outro = outroBlock();
    const neg = `Negative: motion blur, warping, morphing, distorted text, inconsistent physics, jitter, unnatural lighting, plastic texture, oversaturation, low quality.`;
    if (animationStyle === "360_spin")
      return `A smooth cinematic 360-degree orbit rotation of "${prodName}" product. The product sits centered on a ${bg} surface.\n${iRef}\nSlow, continuous rotation revealing all sides — front label, side profile, back ingredient list, and returning to front. Professional studio lighting with sharp rim lights accentuating the product silhouette, subtle reflections on the surface. Shallow depth of field, 85mm lens aesthetic. Hyper-realistic, 8K resolution, commercial grade. Fluid, steady motion.\n\n${outro}\n\n${neg}`;
    if (animationStyle === "before_after")
      return `Split-screen cinematic transition for "${prodName}".\nLEFT SIDE: ${beforeDesc} — dull, tired skin texture under cold flat lighting.\nRIGHT SIDE: ${afterDesc} — glowing, hydrated, healthy skin with warm radiant lighting.\n${iRef}\nSmooth seamless wipe transition from left to right, revealing the transformation. The product appears floating center-frame at the exact transition moment with a subtle glow aura. Soft natural morning sunlight, cinematic close-up, 4K, hyper-realistic.\n\n${outro}\n\n${neg}`;
    if (animationStyle === "ingredient_explode")
      return `Professional commercial shot of "${prodName}" product standing stationary in center frame.\n${iRef}\nSudden high-speed cinematic explosion of key ingredients bursting outward from behind the product — fresh botanical petals, water droplets, vitamin capsules, natural extract particles — slow-motion physics with gravity-defying trajectories. Floating particles catching light, dramatic depth of field. Premium studio lighting, 4K, sharp product details remain perfectly still while ingredients orbit around it.\n\n${outro}\n\n${neg}`;
    if (animationStyle === "unboxing")
      return `Cinematic luxury unboxing reveal of "${prodName}".\n${iRef}\nCamera starts with a top-down close-up of a premium packaging box. The lid lifts slowly with satisfying motion revealing tissue paper layers. Smooth dolly-in as the product emerges — volumetric light rays streaming from inside the box. The product floats upward into center frame with a subtle rotation. ${bg}. High-end skincare aesthetic, 8K, hyper-realistic, anamorphic lens flare.\n\n${outro}\n\n${neg}`;
    if (animationStyle === "floating")
      return `Gravity-defying floating product shot of "${prodName}".\n${iRef}\nThe product levitates in center frame with gentle, slow bobbing motion. Soft particle effects — water droplets, light orbs, botanical elements — orbit around the product in slow motion. Dramatic volumetric rim lighting from behind creating a glowing silhouette effect. Background: ${bg}. Extreme shallow depth of field, 85mm macro lens, 8K cinematic. Smooth, dreamlike motion.\n\n${outro}\n\n${neg}`;
    return `Extreme macro dolly-in shot of "${prodName}" surface texture and details.\n${iRef}\nCamera begins with a medium product shot showing full packaging, then performs a smooth, continuous slow zoom-in revealing micro-textures — embossed logo, label typography, ingredient text, cap threading, surface finish quality. Rack focus transition from body to cap detail. Professional studio lighting, 8K. Slow, controlled motion.\n\n${outro}\n\n${neg}`;
  });

  let generatedRequirements = $derived(() => {
    const imgs = imageRefs
      .filter((r) => r.url.trim())
      .map((r) => `   • ${r.label}: ${r.url}`)
      .join("\n");
    const feats = productFeatures
      .filter((f) => f.trim())
      .map((f) => `   • ${f}`)
      .join("\n");
    return `YÊU CẦU GỬI CHO AI VIDEO:\n\n1. ĐÍNH KÈM ẢNH: Upload các ảnh sản phẩm bên dưới vào cùng lượt gửi:\n${imgs || "   (Chưa có ảnh)"}\n\n2. CHẾ ĐỘ: Chọn "Image-to-Video" (Ảnh thành Video)\n\n3. CÀI ĐẶT KHUYẾN NGHỊ:\n   • Reference Strength: HIGH (80-90%)\n   • Thời lượng: 5-10 giây / clip\n   • Chất lượng: 4K hoặc cao nhất\n   • Tỷ lệ khung hình: ${aspectRatio}\n\n4. TÍNH NĂNG SẢN PHẨM HIỂN THỊ Ở ENDING:\n${feats || "   (Chưa nhập)"}\n   • CTA: ${ctaText}\n   • Tagline: ${brandTagline || "(Chưa nhập)"}\n\n5. QUY TẮC BẮT BUỘC:\n   • KHÔNG tự ý thay đổi logo, nhãn mác, text trên sản phẩm\n   • KHÔNG thêm đồ họa tự chế, mã QR không có trong brief\n   • Ending PHẢI hiển thị đầy đủ tính năng + logo + CTA\n   • Nếu bị méo text/logo → tăng Reference Strength\n\n6. NEGATIVE PROMPT:\n   "motion blur, warping, morphing, distorted text, inconsistent physics, jitter, unnatural lighting, plastic texture, oversaturation, low quality, pixelated text"`;
  });

  function copyText(text: string, label: string) {
    navigator.clipboard.writeText(text);
    nanobot.showToast(`Đã sao chép ${label}!`, "success");
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="space-y-5 pb-6"
  onclick={() => {
    activeDropdown = null;
  }}
>
  <!-- Image References -->
  <div class="space-y-2">
    <span
      class="text-[9px] font-mono text-emerald-400 tracking-wider font-bold uppercase block"
      >ẢNH THAM CHIẾU SẢN PHẨM</span
    >
    {#each imageRefs as ref, idx}
      <div class="flex gap-2 items-center">
        <input
          type="text"
          bind:value={imageRefs[idx].label}
          placeholder="Góc chụp..."
          class="w-24 bg-[#111] border border-gray-800 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-emerald-500/40 shrink-0"
        />
        <input
          type="text"
          bind:value={imageRefs[idx].url}
          placeholder="Dán URL ảnh..."
          class="flex-1 bg-[#111] border border-gray-800 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-emerald-500/40 font-mono"
        />
        {#if imageRefs.length > 1}
          <button
            type="button"
            onclick={() => removeImageRef(idx)}
            class="p-1 text-gray-600 hover:text-red-400 transition-colors"
            ><Trash2 class="w-3 h-3" /></button
          >
        {/if}
      </div>
    {/each}
    <button
      type="button"
      onclick={addImageRef}
      class="flex items-center gap-1 text-[10px] text-emerald-400 hover:text-emerald-300 font-mono transition-colors"
    >
      <Plus class="w-3 h-3" /> Thêm góc chụp
    </button>
  </div>

  <!-- Product Features -->
  <div class="space-y-2">
    <span
      class="text-[9px] font-mono text-amber-400 tracking-wider font-bold uppercase block"
      >TÍNH NĂNG NỔI BẬT SẢN PHẨM</span
    >
    {#each productFeatures as _, idx}
      <div class="flex gap-2 items-center">
        <span
          class="text-[10px] font-mono text-amber-400/60 font-bold w-5 text-right"
          >#{idx + 1}</span
        >
        <input
          type="text"
          bind:value={productFeatures[idx]}
          placeholder="VD: Collagen 10.000mg..."
          class="flex-1 bg-[#111] border border-gray-800 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-amber-500/40"
        />
        {#if productFeatures.length > 1}
          <button
            type="button"
            onclick={() => removeFeature(idx)}
            class="p-1 text-gray-600 hover:text-red-400 transition-colors"
            ><Trash2 class="w-3 h-3" /></button
          >
        {/if}
      </div>
    {/each}
    <button
      type="button"
      onclick={addFeature}
      class="flex items-center gap-1 text-[10px] text-amber-400 hover:text-amber-300 font-mono transition-colors"
    >
      <Plus class="w-3 h-3" /> Thêm tính năng
    </button>
  </div>

  <!-- CTA & Tagline -->
  <div class="grid grid-cols-2 gap-3">
    <div class="space-y-1">
      <span class="text-[9px] font-mono text-gray-500 uppercase font-bold"
        >CTA (Kêu gọi hành động)</span
      >
      <input
        type="text"
        bind:value={ctaText}
        placeholder="Mua ngay tại osmo.vn"
        class="w-full bg-[#111] border border-gray-800 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-cyan-500/40"
      />
    </div>
    <div class="space-y-1">
      <span class="text-[9px] font-mono text-gray-500 uppercase font-bold"
        >Brand Tagline</span
      >
      <input
        type="text"
        bind:value={brandTagline}
        placeholder="Vẻ đẹp từ bên trong"
        class="w-full bg-[#111] border border-gray-800 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-cyan-500/40"
      />
    </div>
  </div>

  <!-- Dropdowns Row -->
  <div class="grid grid-cols-3 gap-3">
    <!-- Animation Style -->
    <div class="space-y-1">
      <span class="text-[9px] font-mono text-cyan-400 uppercase font-bold"
        >Kiểu Animation</span
      >
      <div class="relative">
        <button
          type="button"
          onclick={(e) => toggleDd("anim", e)}
          class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none"
        >
          <span class="truncate">{ANIM_STYLES[animationStyle]}</span>
          <ChevronDown
            class="w-3 h-3 text-gray-500 {activeDropdown === 'anim'
              ? 'rotate-180 text-cyan-400'
              : ''}"
          />
        </button>
        {#if activeDropdown === "anim"}
          <div
            transition:fade={{ duration: 100 }}
            class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 py-1"
          >
            {#each Object.entries(ANIM_STYLES) as [key, label]}
              <button
                type="button"
                onclick={() => {
                  animationStyle = key;
                  activeDropdown = null;
                }}
                class="w-full text-left px-3 py-1.5 text-[10px] transition-colors {animationStyle ===
                key
                  ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >{label}</button
              >
            {/each}
          </div>
        {/if}
      </div>
    </div>
    <!-- Ending Style -->
    <div class="space-y-1">
      <span class="text-[9px] font-mono text-purple-400 uppercase font-bold"
        >Kiểu kết thúc</span
      >
      <div class="relative">
        <button
          type="button"
          onclick={(e) => toggleDd("end", e)}
          class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none"
        >
          <span class="truncate">{END_STYLES[endingStyle]}</span>
          <ChevronDown
            class="w-3 h-3 text-gray-500 {activeDropdown === 'end'
              ? 'rotate-180 text-purple-400'
              : ''}"
          />
        </button>
        {#if activeDropdown === "end"}
          <div
            transition:fade={{ duration: 100 }}
            class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 py-1"
          >
            {#each Object.entries(END_STYLES) as [key, label]}
              <button
                type="button"
                onclick={() => {
                  endingStyle = key;
                  activeDropdown = null;
                }}
                class="w-full text-left px-3 py-1.5 text-[10px] transition-colors {endingStyle ===
                key
                  ? 'bg-purple-950/45 text-purple-400 font-semibold'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >{label}</button
              >
            {/each}
          </div>
        {/if}
      </div>
    </div>
    <!-- Background -->
    <div class="space-y-1">
      <span class="text-[9px] font-mono text-gray-500 uppercase font-bold"
        >Nền video</span
      >
      <div class="relative">
        <button
          type="button"
          onclick={(e) => toggleDd("bg", e)}
          class="w-full bg-[#111115] hover:bg-[#18181f] border border-gray-800 rounded-lg px-2.5 py-1.5 text-[10px] text-gray-300 flex items-center justify-between transition-all focus:outline-none"
        >
          <span class="truncate">{BG_STYLES[backgroundStyle]}</span>
          <ChevronDown
            class="w-3 h-3 text-gray-500 {activeDropdown === 'bg'
              ? 'rotate-180 text-cyan-400'
              : ''}"
          />
        </button>
        {#if activeDropdown === "bg"}
          <div
            transition:fade={{ duration: 100 }}
            class="absolute z-50 left-0 right-0 mt-1 bg-[#09090c]/98 backdrop-blur-md border border-gray-800/90 rounded-lg shadow-xl shadow-black/80 py-1"
          >
            {#each Object.entries(BG_STYLES) as [key, label]}
              <button
                type="button"
                onclick={() => {
                  backgroundStyle = key;
                  activeDropdown = null;
                }}
                class="w-full text-left px-3 py-1.5 text-[10px] transition-colors {backgroundStyle ===
                key
                  ? 'bg-cyan-950/45 text-cyan-400 font-semibold'
                  : 'text-gray-400 hover:bg-white/5 hover:text-white'}"
                >{label}</button
              >
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Before/After fields (conditional) -->
  {#if animationStyle === "before_after"}
    <div class="grid grid-cols-2 gap-3" transition:fade={{ duration: 150 }}>
      <div class="space-y-1">
        <span class="text-[9px] font-mono text-red-400 uppercase font-bold"
          >Mô tả TRƯỚC khi dùng</span
        >
        <textarea
          bind:value={beforeDesc}
          rows="2"
          class="w-full bg-[#111] border border-red-500/20 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-red-500/40 resize-none"
        ></textarea>
      </div>
      <div class="space-y-1">
        <span class="text-[9px] font-mono text-green-400 uppercase font-bold"
          >Mô tả SAU khi dùng</span
        >
        <textarea
          bind:value={afterDesc}
          rows="2"
          class="w-full bg-[#111] border border-green-500/20 rounded px-2 py-1.5 text-[10px] text-gray-300 focus:outline-none focus:border-green-500/40 resize-none"
        ></textarea>
      </div>
    </div>
  {/if}

  <!-- Output: Generated Prompt -->
  <div
    class="bg-emerald-950/10 border border-emerald-500/20 rounded-xl p-4 space-y-3"
  >
    <div
      class="flex items-center justify-between border-b border-emerald-500/20 pb-2"
    >
      <span class="text-[10px] font-mono font-bold text-emerald-400 uppercase"
        >Prompt Animation Video</span
      >
      <button
        onclick={() => copyText(generatedPrompt(), "Prompt Animation")}
        class="flex items-center gap-1 px-2 py-1 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded text-[10px] font-mono transition-all"
      >
        <Copy class="w-3.5 h-3.5" /> Copy Prompt
      </button>
    </div>
    <pre
      class="text-[11px] text-emerald-200 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/40 border border-emerald-500/10 p-3 rounded-lg max-h-56 overflow-y-auto custom-scrollbar">{generatedPrompt()}</pre>
  </div>

  <!-- Output: Generated Requirements -->
  <div
    class="bg-amber-950/10 border border-amber-500/20 rounded-xl p-4 space-y-3"
  >
    <div
      class="flex items-center justify-between border-b border-amber-500/20 pb-2"
    >
      <span class="text-[10px] font-mono font-bold text-amber-400 uppercase"
        >Yêu cầu gửi kèm</span
      >
      <button
        onclick={() => copyText(generatedRequirements(), "Yêu cầu")}
        class="flex items-center gap-1 px-2 py-1 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 rounded text-[10px] font-mono transition-all"
      >
        <Copy class="w-3.5 h-3.5" /> Copy Yêu cầu
      </button>
    </div>
    <pre
      class="text-[11px] text-amber-200 leading-relaxed font-mono whitespace-pre-wrap select-all bg-black/40 border border-amber-500/10 p-3 rounded-lg max-h-56 overflow-y-auto custom-scrollbar">{generatedRequirements()}</pre>
  </div>
</div>
