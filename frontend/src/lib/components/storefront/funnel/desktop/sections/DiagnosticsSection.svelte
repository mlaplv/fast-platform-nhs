<script lang="ts">
  import ClinicalQuiz from "$lib/components/client/ClinicalQuiz.svelte";
  import type { QuizQuestion, ProductMetadata, Product } from "$lib/types";
  import { SHOP_CONFIG } from "$lib/constants/shop";
  import { getShopStore } from "$lib/state/commerce/shop.svelte";
  import EditableWrapper from "$lib/components/admin/EditableWrapper.svelte";
  import "./DiagnosticsSection.css";
  import "./LiquidEffects.css";

  import { lightLiveEdit } from "$lib/state/commerce/liveEditState.svelte";

  let { product: propProduct } = $props<{ product?: Product }>();
  const shopStore = getShopStore();

  const product = $derived(
    lightLiveEdit.isEditMode && lightLiveEdit.dirtyProduct
      ? lightLiveEdit.dirtyProduct
      : propProduct || shopStore.product,
  );
  const metadata = $derived(product?.metadata || {});
  const questions = $derived(metadata?.quiz_questions || []);

  const labels = $derived({
    disclaimer:
      metadata.diagnostics_disclaimer ||
      `AI có thể mắc sai sót. Vì vậy, hãy xác minh thông tin này với bác sĩ`,
  });

  const showHeadline = $derived(
    lightLiveEdit.isEditMode ||
    !product?.metadata?.diagnostics_headline ||
    !product.metadata.diagnostics_headline.startsWith('[OFF]')
  );
  const showSubtitle = $derived(
    lightLiveEdit.isEditMode ||
    !product?.metadata?.diagnostics_subtitle ||
    !product.metadata.diagnostics_subtitle.startsWith('[OFF]')
  );
</script>

<section
  id="diagnostics-section"
  aria-labelledby="personalized-care"
  class="diagnostics-container diagnostic-premium-flow relative overflow-x-hidden"
>
  <div
    class="container mx-auto px-4 md:px-6 max-w-6xl text-center relative z-surface"
  >
    {#if showHeadline}
      <h3
        id="personalized-care"
        class="elite-session-headline mb-4 text-center diagnostics-headline"
      >
        <span>
          <EditableWrapper
            path="metadata.diagnostics_headline"
            type="text"
            label="Sửa tiêu đề chẩn đoán"
            class="inline"
            as="span"
          >
            {@html product?.metadata?.diagnostics_headline ||
              "CHẨN ĐOÁN PHỤC HỒI SẮC TỐ GỐC"}
          </EditableWrapper>
        </span>
      </h3>
    {/if}
    {#if showSubtitle}
      <p class="section-description text-white/40 text-base md:text-lg max-w-3xl mx-auto leading-relaxed mb-10 text-center font-normal mt-4">
        <EditableWrapper
          path="metadata.diagnostics_subtitle"
          type="text"
          label="Sửa mô tả phụ chẩn đoán"
          class="inline"
          as="span"
        >
          {product?.metadata?.diagnostics_subtitle ||
            "Thấu hiểu làn da toàn diện với phác đồ quét và phân tích sạm nám bằng công nghệ AI thế hệ mới"}
        </EditableWrapper>
      </p>
    {/if}

    <div class="quiz-wrapper relative">
      <ClinicalQuiz {product} {questions} {metadata} />
    </div>

  </div>
  <!-- Dynamic Line Wave Divider -->
  <div class="wave-container">
    <svg
      viewBox="0 0 1440 320"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient
          id="wave-gradient-diag"
          x1="0%"
          y1="0%"
          x2="100%"
          y2="0%"
        >
          <stop offset="0%" stop-color="#C18F7E" stop-opacity="0" />
          <stop offset="50%" stop-color="#E8D5B0" stop-opacity="0.8" />
          <stop offset="100%" stop-color="#C18F7E" stop-opacity="0" />
        </linearGradient>
      </defs>
      <path
        class="wave-line opacity-30"
        d="M0,180 Q180,160 360,180 T720,180 T1080,180 T1440,180"
      />
      <path
        class="wave-line"
        d="M0,200 C150,190 200,100 300,200 C450,210 500,120 600,200 C750,190 800,100 900,200 C1050,210 1100,120 1200,200 C1350,190 1400,100 1440,200"
      />
      <path
        class="wave-line secondary"
        d="M0,210 C200,200 300,180 400,210 C500,220 600,190 700,210 C800,230 900,180 1000,210 C1100,240 1200,190 1440,210"
      />
    </svg>
  </div>
</section>

<style>
  .z-surface {
    z-index: var(--z-surface);
  }

  .diagnostics-headline {
    font-size: clamp(1.8rem, 4vw, 2.6rem) !important;
  }

  .diagnostics-headline :global(span) {
    display: block;
    margin-bottom: 0.15rem;
  }

</style>
