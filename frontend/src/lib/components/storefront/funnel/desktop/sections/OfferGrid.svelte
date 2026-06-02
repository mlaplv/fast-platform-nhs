<script lang="ts">
  import { getShopStore } from '$lib/state/commerce/shop.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { getCartStore } from '$lib/state/commerce/cart.svelte';
  import { lightLiveEdit } from '$lib/state/commerce/liveEditState.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import type { Product, ProductVariant, Voucher } from '$lib/types';
  import DesktopProductDetailsModal from './DesktopProductDetailsModal.svelte';
  
  import OfferCard from './OfferCard.svelte';
  import OfferVoucherSheet from './OfferVoucherSheet.svelte';
  import ViralFunnelLanding from './ViralFunnelLanding.svelte';
  import "./OfferGrid.css";
  
  const shopStore = getShopStore();
  const ui = getClientUi();
  const cartStore = getCartStore();

  interface Props {
    onTriggerScan?: () => void;
  }
  let { onTriggerScan }: Props = $props();
  
  const product = $derived(lightLiveEdit.isEditMode && lightLiveEdit.dirtyProduct ? lightLiveEdit.dirtyProduct : shopStore.product);
  const variants = $derived(product?.variants || []);
  const metadata = $derived(product?.metadata || {});

  const h1 = $derived(clean(metadata.offer_headline_1) || "CHẠM NGƯỠNG ĐỈNH CAO CỦA");
  const h2 = $derived(clean(metadata.offer_headline_2) || "SỰ TỰ TIN TUYỆT ĐỐI");
  
  const clean = (s: unknown) => {
    if (!s) return "";
    return String(s)
      .replace(/^(\[OFF\]|\*|\s)+/i, '') // Strips [OFF], *, and leading spaces aggressively
      .trim();
  };

  const mkt = $derived({
    sub: metadata.offer_subheadline || "",
    timer_prefix: clean(metadata.offer_timer_prefix || "Ưu đãi đặc quyền kết thúc sau:"),
    shipping_prefix: clean(metadata.offer_shipping_prefix || "+ VẬN CHUYỂN:"),
    savings_prefix: clean(metadata.offer_savings_prefix || "Tiết kiệm NGAY:"),
    booking_suffix: clean(metadata.offer_booking_suffix || "phụ nữ đã thăng hạng nhan sắc tuần này"),
    trust_verified_by: clean(metadata.offer_trust_verified_by || "TIÊU CHUẨN Y KHOA NHẬT BẢN"),
    compliance_note: clean(metadata.offer_compliance_note || "* Giao hàng bảo mật, <br/> Đóng gói tinh tế như một món quà trang sức."),
    label_activation: metadata.offer_label_activation || "GIAI ĐOẠN ĐÁNH THỨC",
    label_full_treatment: metadata.offer_label_full_treatment || "LIỆU TRÌNH HOÀN MỸ",
    label_expert_choice: metadata.offer_label_expert_choice || "SỰ LỰA CHỌN CỦA PHÁI ĐẸP",
    cta_start: metadata.offer_cta_start || "BẮT ĐẦU TÁI SINH",
    cta_full: metadata.offer_cta_full || "SỞ HỮU SỰ KIÊU SA"
  });

  const mark1 = $derived((metadata.offer_trust_verified_by as string) || "TIÊU CHUẨN Y KHOA NHẬT BẢN");
  const mark2 = $derived((metadata.offer_trust_mark_2 as string) || "HIỆU QUẢ KIỂM CHỨNG");
  const mark3 = $derived((metadata.offer_trust_mark_3 as string) || "DƯỢC MỸ PHẨM CAO CẤP");

  let isDetailsOpen = $state(false);

  const gridClass = $derived(variants.length >= 3 
    ? 'slider-track overflow-x-auto lg:overflow-visible scrollbar-hide snap-x snap-mandatory flex lg:grid lg:grid-cols-3'
    : `grid grid-cols-1 ${variants.length === 2 ? 'md:grid-cols-2' : 'lg:grid-cols-3'}`
  );

  $effect(() => {
    if (cartStore.vouchers && cartStore.vouchers.length > 0) {
      shopStore.setVouchers(cartStore.vouchers);
    }
  });

  let hasInitialized = $state(false);
  $effect(() => {
    if (variants.length > 0 && ui.isDetermined && !hasInitialized) {
      const defaultIdx = (ui.isDesktop && variants.length >= 2) ? 1 : 0;
      
      if (defaultIdx === 1) {
        shopStore.selectVariant(variants[1]);
      } else if (!shopStore.variant) {
        shopStore.selectVariant(variants[0]);
      }
      
      hasInitialized = true;
    }
  });
</script>

<section class="offer-section relative contain-layout">
  <div class="absolute inset-0 bg-radial-at-t from-luxury-sakura/10 to-transparent pointer-events-none"></div>
  <div class="liquid-orb top-[10%] left-[-10%] w-[800px] h-[800px] pointer-events-none" style:background-color="var(--luxury-sakura)" style:opacity="0.1"></div>
  <div class="liquid-orb botto    <div class="container mx-auto px-3 max-w-6xl relative z-surface">
    <div class="text-center">
      <h2 class="elite-session-headline mb-4 text-center offer-grid-headline">
        {#if !(metadata.offer_headline_1 || '').startsWith('[OFF]') || lightLiveEdit.isEditMode}
          <EditableWrapper path="metadata.offer_headline_1" type="text" label="SỬA TIÊU ĐỀ 1" class="inline" as="span">
            {h1}
          </EditableWrapper>
        {/if}

        {#if (!(metadata.offer_headline_1 || '').startsWith('[OFF]') && !(metadata.offer_headline_2 || '').startsWith('[OFF]')) || lightLiveEdit.isEditMode}
          <br class="md:hidden"/>
        {/if}

        {#if !(metadata.offer_headline_2 || '').startsWith('[OFF]') || lightLiveEdit.isEditMode}
          <span class="text-luxury-gold md:ml-3">
             <EditableWrapper path="metadata.offer_headline_2" type="text" label="SỬA TIÊU ĐỀ 2" class="inline" as="span">
               {h2}
             </EditableWrapper>
          </span>
        {/if}
      </h2>

      <div class="flex items-center justify-center gap-4 mt-2 opacity-60 grayscale hover:grayscale-0 transition-all duration-700">
         <EditableWrapper path="metadata.offer_trust_verified_by" type="text" label="SỬA CHỨNG NHẬN 1" class="inline" as="span">
           <span class="text-[8px] tracking-[0.6em] font-medium text-slate-400">{clean(mark1)}</span>
         </EditableWrapper>
         
         {#if (!mark1.startsWith('[OFF]') && !mark2.startsWith('[OFF]')) || lightLiveEdit.isEditMode}
            <div class="h-px w-10 bg-white/5"></div>
         {/if}

         <EditableWrapper path="metadata.offer_trust_mark_2" type="text" label="SỬA CHỨNG NHẬN 2" class="inline" as="span">
           <span class="text-[9px] tracking-[0.3em] font-black text-luxury-sakura">{clean(mark2)}</span>
         </EditableWrapper>
         
         {#if (!mark2.startsWith('[OFF]') && !mark3.startsWith('[OFF]')) || lightLiveEdit.isEditMode}
            <div class="h-px w-10 bg-white/5"></div>
         {/if}

         <EditableWrapper path="metadata.offer_trust_mark_3" type="text" label="SỬA CHỨNG NHẬN 3" class="inline" as="span">
            <span class="text-[8px] tracking-[0.6em] font-medium text-slate-400">{clean(mark3)}</span>
         </EditableWrapper>
      </div>
    </div>

    <div class="max-w-2xl mx-auto mb-8 mt-4 relative z-surface">
      {#if product}
        <ViralFunnelLanding 
          {product} 
          timer_prefix={mkt.timer_prefix}
        />
      {/if}
    </div>

    <div class="package-grid pt-8 {gridClass} gap-6 items-stretch">
      {#each variants as variant, idx (variant.id)}
          <OfferCard 
            {variant} 
            {idx} 
            {product} 
            variantsCount={variants.length}
            {mkt}
            productVouchers={shopStore.productVouchers || []}
            onOpenVouchers={(id) => {
              if (lightLiveEdit.openPopoverId === id) lightLiveEdit.openPopoverId = null;
              else lightLiveEdit.openPopoverId = id;
            }}
            {onTriggerScan}
            onOpenDetails={() => isDetailsOpen = true}
          />
      {/each}
    </div>
  </div>
</section>

<DesktopProductDetailsModal bind:active={isDetailsOpen} {product} />
