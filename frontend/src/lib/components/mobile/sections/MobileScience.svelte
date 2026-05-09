<script lang="ts">
    import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Zap from "@lucide/svelte/icons/zap";
  import Droplets from "@lucide/svelte/icons/droplets";
  import HelpCircle from "@lucide/svelte/icons/help-circle";
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import EditableWrapper from '$lib/components/admin/EditableWrapper.svelte';
  import './MobileScience.css';
  import { liveEditStore } from '$lib/state/commerce/liveEdit.svelte';
  import { getShopStore } from '$lib/state/commerce/shop.svelte.ts';

  const shopStore = getShopStore();
  const ui = getClientUi();
  let { product: propProduct } = $props();
  const product = $derived(liveEditStore.isEditMode && liveEditStore.dirtyProduct ? liveEditStore.dirtyProduct : (propProduct || shopStore.product));
  const metadata = $derived(product?.metadata || {});
  
  const claims = $derived([
    metadata.science_claims?.[0] || { label: 'CƠ CHẾ PHÁ VỠ HẮC SẮC TỐ', content: 'Ức chế mạnh mẽ quá trình sản sinh Melanin tối màu nhờ tinh chất Hoa Anh Đào (Sakura) và Vitamin C. Đánh bật các gốc thâm sạm từ sâu bên trong, nâng tone rạng rỡ vùng da xỉn màu.' },
    metadata.science_claims?.[1] || { label: 'AN TOÀN // LÀNH TÍNH CHUẨN NHẬT', content: 'Chiết xuất dược liệu sinh học thân thiện với những vùng da mỏng manh nhất. Cam kết "3 KHÔNG": Không cồn, không Paraben, không hóa chất lột tẩy.' }
  ]);
  const stats = $derived(metadata.science_stats || { value: '3', unit: 'S', label: 'THẨM THẤU TÀNG HÌNH' });

  const tech = $derived([
    {
      icon: ShieldCheck,
      title: typeof claims[0].label === 'string' ? claims[0].label : 'Cơ chế phá vỡ hắc sắc tố',
      desc: typeof claims[0].content === 'string' ? claims[0].content : 'Ức chế Melanin từ tinh chất Sakura.'
    },
    {
      icon: Zap,
      title: `KHÔNG BẾT DÍNH - CHỈ ${stats.value}${stats.unit} CHẠM DA`,
      desc: "Kết cấu serum siêu vi hạt mỏng nhẹ, tan ngay lập tức. Bơm đầy độ ẩm phục hồi sự láng mịn nhưng vẫn đảm bảo bề mặt khô ráo."
    },
    {
      icon: Droplets,
      title: typeof claims[1].label === 'string' ? claims[1].label : 'An toàn chuẩn Nhật',
      desc: typeof claims[1].content === 'string' ? claims[1].content : 'Cam kết 3 KHÔNG: Không cồn, không Paraben, không hóa chất lột tẩy.'
    }
  ]);

  const faqs = $derived([
    {
        q: metadata?.science_faq_1_q || "Bao lâu thì thấy hiệu quả rõ rệt nhất?",
        a: metadata?.science_faq_1_a || "Dạ thường thì sau 2-4 tuần sử dụng đều đặn ngày 2 lần, nàng sẽ thấy da bật tông rõ, sờ vào mịn mướt hẳn luôn. Còn để các vết thâm 'cứng đầu' mờ hẳn thì tầm 6-8 tuần là thời điểm đẹp nhất ạ!"
    },
    {
        q: metadata?.science_faq_2_q || "Ngưng dùng rồi có bị thâm đen trở lại không?",
        a: metadata?.science_faq_2_a || "Nàng yên tâm nhé, ngưng dùng sẽ không bị thâm lại đâu ạ. Miễn là mình vẫn duy trì vệ sinh và các bước dưỡng da cơ bản thì kết quả vẫn sẽ bền đẹp theo thời gian."
    },
    {
        q: metadata?.science_faq_3_q || "Sản phẩm có thực sự làm hồng không?",
        a: metadata?.science_faq_3_a || "Serum tập trung đánh bay sắc tố đen, làm mờ thâm sạm để da sáng hồng tự nhiên, chứ không phải kiểu 'nhuộm màu' đâu ạ."
    },
    {
        q: metadata?.science_faq_4_q || "Vùng nhạy cảm có dùng được không?",
        a: metadata?.science_faq_4_a || "Dạ vô tư luôn nàng ơi! Sản phẩm này sinh ra là để 'chiều lòng' những vùng nhạy cảm nhất. Thành phần cực kỳ lành tính nên rất êm ái cho da."
    }
  ]);

  async function openFaq(index: number) {
    const faq = faqs[index];
    await ui.openConfirm({
      title: faq.q,
      message: faq.a,
      confirmLabel: 'ĐÃ HIỂU',
      cancelLabel: 'ĐÓNG'
    });
  }
</script>

<div class="science-root">
  <div class="science-glow-1"></div>
  <div class="science-glow-2"></div>
  <div class="tech-grid"></div>

  <div class="science-header">
    <h2 class="science-headline">
      <EditableWrapper path="metadata.science_headline" type="text" label="SỬA TIÊU ĐỀ" as="span">
        {metadata.science_headline || 'Tại sao lại hiệu quả vượt trội?'}
      </EditableWrapper>
    </h2>
    
    <p class="science-subheadline">
      <EditableWrapper path="metadata.science_subheadline" type="text" label="SỬA MÔ TẢ PHỤ" as="span">
        {metadata.science_subheadline || `Đột phá công thức hàng đầu từ Nhật Bản.`}
      </EditableWrapper>
    </p>
  </div>

  <div class="science-content-container">
    <div class="science-claims-stack">
      {#each tech as item, i}
        <div class="claim-card" style="--i: {i}">
          <div class="line-wave-container">
            <svg viewBox="0 0 100 20" preserveAspectRatio="none" class="line-wave">
                <path d="M0 10 Q 25 {5 + Math.sin(i) * 5}, 50 10 T 100 10" fill="none" class="wave-path" />
            </svg>
          </div>

          <div class="claim-info">
            <h4 class="claim-title">
              <EditableWrapper path={`metadata.science_claims[${i}].label`} type="text" label="SỬA NHÃN {i+1}" as="span">
                {item.title}
              </EditableWrapper>
            </h4>

            <div class="claim-desc">
              <EditableWrapper path={`metadata.science_claims[${i}].content`} type="text" label="SỬA MÔ TẢ {i+1}">
                {item.desc}
              </EditableWrapper>
            </div>
          </div>
        </div>
      {/each}
    </div>

    <!-- FAQ SECTION (Viral Mobile Grid) -->
    <div class="faq-section-mobile">
      <div class="faq-header-compact">
        <div class="faq-icon-min">
          <HelpCircle class="w-5 h-5 text-luxury-sakura" />
        </div>
        <div class="flex flex-col">
          <span class="faq-title-min">Câu hỏi thường gặp</span>
          <span class="faq-desc-min">Click để xem giải đáp chuyên sâu</span>
        </div>
      </div>

      <div class="faq-grid-mobile">
        {#each faqs as faq, i}
          <button 
            class="faq-btn-item"
            onclick={() => openFaq(i)}
          >
            <span class="faq-q-text">
              <EditableWrapper path={`metadata.science_faq_${i+1}_q`} type="text" label={`SỬA CÂU HỎI ${i+1}`} as="span">
                {faq.q}
              </EditableWrapper>
            </span>
          </button>
        {/each}
      </div>
    </div>
  </div>

  <div class="science-footer">
    <div class="footer-inner">
      <div class="footer-text">
        <span class="footer-top-label">Bảo chứng an toàn</span>
        <span class="footer-main-label">& Chất lượng quốc tế</span>
      </div>
      <div class="footer-badges">
        <div class="footer-badge badge-sakura">
          <ShieldCheck class="w-4 h-4 text-[#FFB7C5]" />
        </div>
        <div class="footer-badge badge-sakura">
          <Zap class="w-4 h-4 text-[#FFB7C5]" />
        </div>
      </div>
    </div>
  </div>
</div>
