<script lang="ts">
  import type { RewriteResult } from '$lib/state/types';
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Info from "@lucide/svelte/icons/info";
  import Sparkles from "@lucide/svelte/icons/sparkles";
  import Droplet from "@lucide/svelte/icons/droplet";
  import Star from "@lucide/svelte/icons/star";
  import CheckCircle2 from "@lucide/svelte/icons/check-circle-2";
  import Zap from "@lucide/svelte/icons/zap";
  import { processContentImages } from "$lib/state/utils";

  let { 
    data, 
    compact = false,
    assets = []
  }: { 
    data: RewriteResult | string; 
    compact?: boolean;
    assets?: any[]
  } = $props();

  // Elite V2.2: Zero-Latency reactive parsing using $derived
  const parsedData = $derived.by(() => {
    if (!data) return null;
    if (typeof data === 'string') {
      try {
        return JSON.parse(data) as RewriteResult;
      } catch (e) {
        console.error("InteractiveDashboard: Failed to parse JSON data", e);
        return null;
      }
    }
    return data;
  });

  let activeTab = $state<'ingredients' | 'benefits' | 'routine'>('benefits');
</script>

{#if parsedData}
<div class="interactive-dashboard-wrapper" class:compact>
  <!-- HEADLINE & HERO -->
  <div class="hero-section">
    <div class="hero-badge">
      <Sparkles size={14} />
      <span>SẢN PHẨM ĐỘC QUYỀN</span>
    </div>
    <h1 class="hero-title">{parsedData.hero_headline}</h1>
    <p class="hero-identity">{parsedData.unique_identity}</p>
  </div>

  <!-- SPEC BENTO GRID -->
  <div class="bento-grid">
    {#each parsedData.spec_bento as spec}
      <div class="bento-card">
        <div class="bento-label">{spec.label}</div>
        <div class="bento-value">{spec.value}</div>
      </div>
    {/each}
  </div>

  <!-- INTERACTIVE TABS -->
  <div class="interactive-tabs">
    <div class="tab-headers">
      <button class:active={activeTab === 'benefits'} onclick={() => activeTab = 'benefits'}>
        <Star size={16} /> Hiệu quả
      </button>
      <button class:active={activeTab === 'ingredients'} onclick={() => activeTab = 'ingredients'}>
        <Droplet size={16} /> Thành phần
      </button>
      <button class:active={activeTab === 'routine'} onclick={() => activeTab = 'routine'}>
        <CheckCircle2 size={16} /> Cách dùng
      </button>
    </div>

    <div class="tab-content">
      {#if activeTab === 'benefits'}
        <div class="benefits-list">
          {#each parsedData.benefits as benefit}
            <div class="benefit-item">
              <div class="benefit-icon">
                <Zap size={18} />
              </div>
              <div class="benefit-text">
                <h4>{benefit.title}</h4>
                <p>{benefit.description}</p>
              </div>
            </div>
          {/each}
        </div>
      {:else if activeTab === 'ingredients'}
        <div class="ingredients-list">
          {#each parsedData.golden_ingredients as ing}
            <div class="ingredient-item">
              <div class="ing-title">{ing.title}</div>
              <div class="ing-desc">{ing.description}</div>
            </div>
          {/each}
        </div>
      {:else if activeTab === 'routine'}
        <div class="routine-steps">
          {#each parsedData.routine as step, i}
            <div class="routine-step">
              <div class="step-number">{i + 1}</div>
              <div class="step-text">{step}</div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>

  <!-- SAFETY & COMBINATIONS (ACCORDION) -->
  <div class="extra-info">
    <div class="safety-box">
      <h4><ShieldCheck size={16} /> Lưu ý an toàn</h4>
      <ul>
        {#each parsedData.safety_warnings as warning}
          <li>{warning}</li>
        {/each}
      </ul>
    </div>
    
    {#if parsedData.combinations && parsedData.combinations.length > 0}
      <div class="combo-box">
        <h4><Info size={16} /> Gợi ý kết hợp</h4>
        <ul>
          {#each parsedData.combinations as combo}
            <li>{combo}</li>
          {/each}
        </ul>
      </div>
    {/if}
  </div>

  {#if parsedData.generated_at}
    <div class="dashboard-footer">
      <div class="timestamp-badge">
        <Zap size={10} />
        Báo cáo lập lúc: {parsedData.generated_at}
      </div>
    </div>
  {/if}
</div>
{:else}
  <!-- Fallback for non-JSON content -->
  <div class="raw-content-fallback">
    <!-- eslint-disable-next-line svelte/no-at-html-tags -->
    {@html processContentImages(typeof data === 'string' ? data : '', assets)}
  </div>
{/if}

<style lang="postcss">
  /* PREMIUM VIRAL 2026 STYLES */
  .interactive-dashboard-wrapper {
    font-family: 'Be Vietnam Pro', 'Be Vietnam Pro', -apple-system, sans-serif;
    color: #fff;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 0.5rem;
    animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }

  /* HERO */
  .hero-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 0.75rem;
    padding: 2rem 0;
  }
  .hero-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.65rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    color: #FFB7C5;
    background: rgba(255, 183, 197, 0.1);
    backdrop-filter: blur(10px);
    padding: 0.4rem 1rem;
    border-radius: 100px;
    border: 1px solid rgba(255, 183, 197, 0.2);
    box-shadow: 0 4px 15px rgba(255, 183, 197, 0.1);
  }
  .hero-title {
    font-size: 2.2rem;
    font-weight: 900;
    line-height: 1.1;
    background: linear-gradient(135deg, #ffffff 0%, #E8D5B0 50%, #FFB7C5 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 10px 20px rgba(0,0,0,0.3));
    margin: 0;
    letter-spacing: -0.02em;
  }
  .hero-identity {
    font-size: 1rem;
    line-height: 1.6;
    color: rgba(255,255,255,0.6);
    max-width: 600px;
    margin: 0;
  }

  /* BENTO GRID */
  .bento-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
  }
  .bento-card {
    background: rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
  }
  .bento-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(135deg, rgba(255,183,197,0.1) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.4s ease;
  }
  .bento-card:hover {
    background: rgba(255,255,255,0.07);
    transform: translateY(-4px) scale(1.02);
    border-color: rgba(255, 183, 197, 0.4);
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
  }
  .bento-card:hover::before { opacity: 1; }

  .bento-label {
    font-size: 0.65rem;
    letter-spacing: 0.05em;
    color: rgba(255,255,255,0.4);
    font-weight: 700;
  }
  .bento-value {
    font-size: 1rem;
    font-weight: 700;
    color: #fff;
    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  /* TABS */
  .interactive-tabs {
    background: rgba(255,255,255,0.02);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.08);
    overflow: hidden;
    box-shadow: 0 30px 60px rgba(0,0,0,0.3);
  }
  .tab-headers {
    display: flex;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    background: rgba(0,0,0,0.2);
    padding: 0.5rem;
    gap: 0.5rem;
  }
  .tab-headers button {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    padding: 0.85rem;
    background: transparent;
    border: none;
    color: rgba(255,255,255,0.4);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    border-radius: 14px;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .tab-headers button:hover {
    color: rgba(255,255,255,0.8);
    background: rgba(255,255,255,0.05);
  }
  .tab-headers button.active {
    color: #fff;
    background: linear-gradient(135deg, rgba(255, 183, 197, 0.2) 0%, rgba(232, 213, 176, 0.1) 100%);
    box-shadow: inset 0 0 0 1px rgba(255, 183, 197, 0.3);
  }

  .tab-content {
    padding: 2rem;
    min-height: 300px;
  }

  /* LISTS */
  .benefit-item {
    display: flex;
    gap: 1.25rem;
    margin-bottom: 1.5rem;
    animation: slideIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    opacity: 0;
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
  }
  .benefit-item:nth-child(1) { animation-delay: 0.1s; }
  .benefit-item:nth-child(2) { animation-delay: 0.2s; }
  .benefit-item:nth-child(3) { animation-delay: 0.3s; }

  .benefit-icon {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(255,183,197,0.2) 0%, rgba(232,213,176,0.1) 100%);
    color: #FFB7C5;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 8px 20px rgba(255, 183, 197, 0.15);
  }
  .benefit-text h4 { margin: 0 0 0.4rem 0; font-size: 1rem; color: #fff; font-weight: 700; }
  .benefit-text p { margin: 0; font-size: 0.9rem; color: rgba(255,255,255,0.5); line-height: 1.6; }

  .ingredient-item {
    padding: 1.25rem;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
  }
  .ingredient-item:hover {
    background: rgba(255,255,255,0.05);
    transform: scale(1.01);
  }
  .ing-title { font-weight: 800; color: #E8D5B0; font-size: 1rem; margin-bottom: 0.4rem; letter-spacing: -0.01em; }
  .ing-desc { font-size: 0.9rem; color: rgba(255,255,255,0.6); line-height: 1.6; }

  .routine-step {
    display: flex;
    gap: 1.25rem;
    align-items: flex-start;
    margin-bottom: 1.25rem;
  }
  .step-number {
    width: 28px;
    height: 28px;
    border-radius: 10px;
    background: linear-gradient(135deg, #FFB7C5 0%, #E8D5B0 100%);
    color: #000;
    font-weight: 900;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 4px 10px rgba(255, 183, 197, 0.3);
  }
  .step-text {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.8);
    line-height: 1.6;
    padding-top: 0.15rem;
  }

  /* EXTRA INFO */
  .extra-info {
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }
  .safety-box, .combo-box {
    padding: 1.5rem;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    transition: transform 0.3s ease;
  }
  .safety-box:hover, .combo-box:hover { transform: translateY(-2px); }
  .safety-box { background: rgba(239, 68, 68, 0.03); border-color: rgba(239, 68, 68, 0.15); }
  .combo-box { background: rgba(59, 130, 246, 0.03); border-color: rgba(59, 130, 246, 0.15); }
  .extra-info h4 {
    margin: 0 0 1.25rem 0;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: -0.01em;
  }
  .safety-box h4 { color: #f87171; }
  .combo-box h4 { color: #60a5fa; }
  .extra-info ul {
    margin: 0;
    padding-left: 1.4rem;
    color: rgba(255,255,255,0.6);
    font-size: 0.9rem;
    line-height: 1.7;
  }
  .extra-info li { margin-bottom: 0.6rem; }

  @media (min-width: 768px) {
    .extra-info { grid-template-columns: 1fr 1fr; }
    .hero-title { font-size: 3rem; }
  }

  /* COMPACT MODE FOR ADMIN PREVIEW */
  .interactive-dashboard-wrapper.compact {
    gap: 1rem;
  }
  .interactive-dashboard-wrapper.compact .hero-section { padding: 1rem 0; }
  .interactive-dashboard-wrapper.compact .hero-title { font-size: 1.5rem; }
  .interactive-dashboard-wrapper.compact .tab-content { padding: 1.25rem; }
  .interactive-dashboard-wrapper.compact .bento-grid { grid-template-columns: repeat(2, 1fr); }

  /* FOOTER & TIMESTAMPS */
  .dashboard-footer {
    margin-top: 1rem;
    display: flex;
    justify-content: center;
    padding-bottom: 1rem;
  }
  .timestamp-badge {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.6rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255,255,255,0.3);
    background: rgba(255,255,255,0.03);
    padding: 0.35rem 0.75rem;
    border-radius: 100px;
    border: 1px solid rgba(255,255,255,0.05);
  }
</style>
