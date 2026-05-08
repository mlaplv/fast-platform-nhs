<script lang="ts">
    import Zap from "@lucide/svelte/icons/zap";
  import { formatCurrency } from '$lib/utils/format';

  interface Props {
    isFlashSaleActive: boolean;
    displayDiscountPercent: number;
    displaySalePrice: number;
    displayOriginalPrice: number;
    timeLeft: { hours: number; minutes: number; seconds: number };
  }

  let { 
    isFlashSaleActive, displayDiscountPercent, displaySalePrice, 
    displayOriginalPrice, timeLeft 
  }: Props = $props();
</script>

{#if isFlashSaleActive}
  <section class="flash-sale-banner">
    <div class="fs-left">
      <div class="flex items-center gap-1.5">
        <div class="discount-percent">-{displayDiscountPercent}%</div>
        <div class="freeship-fomo">
          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          FREE SHIP
        </div>
      </div>
      <div class="price-container">
        <span class="price-label">Từ</span>
        <span class="price-value">{formatCurrency(displaySalePrice)}</span>
      </div>
      <div class="original-price">{formatCurrency(displayOriginalPrice)}</div>
    </div>
    
    <div class="fs-right">
      <div class="fs-title"><Zap size={18} fill="white" /><span>Flash Sale</span></div>
      <div class="fs-countdown">
        <span>Kết thúc sau</span>
        <div class="time-box font-mono tabular-nums">
          <span>{timeLeft.hours.toString().padStart(2, '0')}</span>
          <span class="separator">:</span>
          <span>{timeLeft.minutes.toString().padStart(2, '0')}</span>
          <span class="separator">:</span>
          <span>{timeLeft.seconds.toString().padStart(2, '0')}</span>
        </div>
      </div>
    </div>
  </section>
{/if}

<style>
  .flash-sale-banner { 
    background: linear-gradient(90deg, #ee4d2d, #ff7337); color: white; display: flex; padding: 6px 12px; justify-content: space-between; align-items: center; position: relative; overflow: hidden;
    box-shadow: 0 4px 15px rgba(238, 77, 45, 0.2);
  }
  .fs-left { flex: 1; z-index: 1; }
  .discount-percent { background: white; color: #ee4d2d; border: 1px solid white; width: max-content; padding: 0 4px; font-size: 11px; font-weight: 900; border-radius: 2px; }
  .freeship-fomo { background: #E3B5A4; color: white; font-size: 10px; font-weight: 900; padding: 0 4px; border-radius: 2px; display: flex; align-items: center; gap: 2px; height: 16px; }
  .price-container { display: flex; align-items: center; gap: 4px; margin-top: 2px; }
  .price-label { font-size: 13px; color: white; opacity: 0.9; }
  .price-value { font-size: 20px; font-weight: 900; letter-spacing: -0.5px; }
  .original-price { font-size: 11px; text-decoration: line-through; color: rgba(255,255,255,0.7); }
  .fs-right { text-align: right; z-index: 1; display: flex; flex-direction: column; align-items: flex-end; }
  .fs-title { display: flex; align-items: center; gap: 4px; font-weight: 900; font-size: 16px; text-transform: uppercase; font-style: italic; }
  .fs-countdown { font-size: 11px; display: flex; align-items: center; gap: 4px; font-weight: 700; }
  .time-box { display: flex; gap: 2px; align-items: center; }
  .time-box span { background: rgba(0,0,0,0.3); color: white; padding: 2px 6px; border-radius: 4px; font-weight: 1000; border: 1px solid rgba(255,255,255,0.2); min-width: 28px; text-align: center; font-size: 13px; }
  .time-box .separator { background: none; border: none; padding: 0; min-width: 4px; opacity: 0.8; text-align: center; font-weight: 1000; }
</style>
