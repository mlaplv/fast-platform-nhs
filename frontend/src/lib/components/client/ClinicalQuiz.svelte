<script lang="ts">
  import { fade, fly, scale } from "svelte/transition";
  import { quintOut } from "svelte/easing";
  import { getShopStore } from "$lib/state/commerce/shop.svelte.ts";
  import type { QuizQuestion, Product, ProductMetadata } from "$lib/types";
  import QuizIcon from "./QuizIcon.svelte";
  import DiagnosticScanner from "./slug/DiagnosticScanner.svelte";
  import "./slug/LiquidEffects.css";
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";
  import Plus from "@lucide/svelte/icons/plus";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import PlusCircle from "@lucide/svelte/icons/plus-circle";
  import Target from "@lucide/svelte/icons/target";
  import RefreshCcw from "@lucide/svelte/icons/refresh-ccw";
  import GripVertical from "@lucide/svelte/icons/grip-vertical";
  import ArrowLeft from "@lucide/svelte/icons/arrow-left";

  let {
    product,
    metadata: propMetadata,
    questions: propQuestions,
  } = $props<{
    product: Product;
    metadata: ProductMetadata;
    questions: QuizQuestion[];
  }>();

  const shopStore = getShopStore();

  const QUIZ_FALLBACKS = {
    result_headline:
      'Phác đồ điều trị <br/><span class="text-luxury-copper">độc quyền.</span>',
    result_subheadline:
      '⚠️ Cảnh báo từ AI: Hiện trạng sắc tố của Quý khách cần can thiệp ngay với ít nhất <span class="text-luxury-gold font-semibold">{quantity} đơn vị</span> để đạt liệu trình phục hồi tối đa.',
    result_cta: "Kích hoạt liệu trình ngay",
    restart_label: "Thiết lập lại dữ liệu",
    loading_label: "Đang truy xuất cơ sở dữ liệu lâm sàng...",
  };

  interface VNDivision {
    name: string;
    code?: string;
    id?: string;
  }

  const selectedAreaLabel = $derived(
    answers.find((ans) => ans.q.includes("giải cứu"))?.a || "",
  );

  const levelOptions = $derived.by(() => {
    const area = selectedAreaLabel.toLowerCase();
    if (area.includes("bikini"))
      return [
        { label: "Sắc tố chưa đồng nhất", value: "light", icon: "Moon" },
        { label: "Khu vực kém mịn màng", value: "medium", icon: "CloudMoon" },
        { label: "Điểm sắc tố li ti", value: "heavy", icon: "Activity" },
        {
          label: "Dày sừng vùng nhạy cảm",
          value: "chronic",
          icon: "ShieldAlert",
        },
      ];
    if (area.includes("nách"))
      return [
        { label: "Kích ứng sắc tố nhẹ", value: "light", icon: "Moon" },
        {
          label: "Tối màu do ma sát / hóa chất",
          value: "medium",
          icon: "CloudMoon",
        },
        { label: "Tập trung melanin sâu", value: "heavy", icon: "Activity" },
        {
          label: "Dày sừng do tổn thương bề mặt",
          value: "chronic",
          icon: "ShieldAlert",
        },
      ];
    if (area.includes("nhũ hoa"))
      return [
        { label: "Sắc tố chưa rạng rỡ", value: "light", icon: "Moon" },
        { label: "Vùng da kém mịn màng", value: "medium", icon: "CloudMoon" },
        { label: "Khu vực tập trung sắc tố", value: "heavy", icon: "Activity" },
        {
          label: "Mất độ hồng mọng tự nhiên",
          value: "chronic",
          icon: "ShieldAlert",
        },
      ];
    return [
      { label: "Sắc tố bề mặt nhẹ", value: "light", icon: "Moon" },
      { label: "Vùng da kém rạng rỡ", value: "medium", icon: "CloudMoon" },
      { label: "Khu vực tối màu rõ rệt", value: "heavy", icon: "Activity" },
      {
        label: "Dày sừng & Sắc tố thâm niên",
        value: "chronic",
        icon: "ShieldAlert",
      },
    ];
  });

  const metadata = $derived(propMetadata || product?.metadata || {});
  const questions = $derived(
    propQuestions ||
      (metadata.quiz_questions as QuizQuestion[])?.map((q, i) => {
        if (q.id === "level" || q.title?.includes("sắc tố thực tế")) {
          return { ...q, options: levelOptions };
        }
        return {
          ...q,
          id: q.id || `q_auto_${i}_${Date.now()}`,
        };
      }) || [
        {
          id: "area",
          title: "Vùng cần giải cứu sắc tố?",
          options: [
            { label: "Vùng nách", value: "armpit", icon: "Wind" },
            { label: "Vùng bikini", value: "bikini", icon: "Shield" },
            { label: "Vùng nhũ hoa", value: "sun", icon: "Sun" },
            { label: "Khác / Đùi trong", value: "other", icon: "Layers" },
          ],
        },
        {
          id: "level",
          title: "Hiện trạng sắc tố thực tế?",
          options: levelOptions,
        },
        {
          id: "goal",
          title: "Mục tiêu mong muốn nhất?",
          options: [
            { label: "Trắng sáng rạng rỡ", value: "whitening", icon: "Zap" },
            {
              label: "Phục hồi gốc da",
              value: "recovery",
              icon: "ShieldCheck",
            },
            {
              label: "Dứt điểm vùng tối màu",
              value: "permanent",
              icon: "Target",
            },
            {
              label: "Dịu nhẹ cho da nhạy cảm",
              value: "sensitive",
              icon: "Heart",
            },
          ],
        },
      ],
  );

  const labels = $derived({
    result_headline:
      (metadata.quiz_result_headline as string) ||
      QUIZ_FALLBACKS.result_headline,
    result_subheadline:
      (metadata.quiz_result_subheadline as string) ||
      QUIZ_FALLBACKS.result_subheadline,
    result_cta:
      (metadata.quiz_result_cta as string) || QUIZ_FALLBACKS.result_cta,
    restart_label:
      (metadata.quiz_restart_label as string) || QUIZ_FALLBACKS.restart_label,
    loading_label:
      (metadata.quiz_loading_label as string) || QUIZ_FALLBACKS.loading_label,
  });

  const isEditable = $derived(
    liveEditStore.isEditMode && liveEditStore.isAdmin,
  );

  let currentStep = $state(0);
  let answers = $state<Array<{ q: string; a: string }>>([]);
  let progress = $derived(
    questions.length > 0 ? (currentStep / questions.length) * 100 : 0,
  );

  let quizContainer = $state<HTMLElement | null>(null);
  let draggingIdx = $state<number | null>(null);

  // Elite V2.2: Absolute Direct Editing Logic
  function addQuestion() {
    const newQuestion = {
      id: `q_${Date.now()}`,
      title: "Câu hỏi mới?",
      subtitle: "Mô tả ngắn để khách hàng hiểu ngữ cảnh...",
      options: [
        {
          label: "Lựa chọn 1",
          value: `v1_${Date.now()}`,
          score: 0,
          icon: "Circle",
        },
        {
          label: "Lựa chọn 2",
          value: `v2_${Date.now()}`,
          score: 0,
          icon: "Circle",
        },
        {
          label: "Lựa chọn 3",
          value: `v3_${Date.now()}`,
          score: 0,
          icon: "Circle",
        },
      ],
    };
    const newQuestions = [newQuestion, ...questions];
    liveEditStore.updateField("metadata.quiz_questions", newQuestions);
  }

  function handleDragStart(idx: number) {
    draggingIdx = idx;
  }

  function handleDragOver(e: DragEvent, idx: number) {
    e.preventDefault();
  }

  function handleDrop(targetIdx: number) {
    if (draggingIdx === null || draggingIdx === targetIdx) return;
    const newQuestions = JSON.parse(JSON.stringify(questions));
    const [movedItem] = newQuestions.splice(draggingIdx, 1);
    newQuestions.splice(targetIdx, 0, movedItem);
    liveEditStore.updateField("metadata.quiz_questions", newQuestions);
    draggingIdx = null;
  }

  function removeQuestion(idx: number) {
    const newQuestions = questions.filter((_, i) => i !== idx);
    liveEditStore.updateField("metadata.quiz_questions", newQuestions);
  }

  function addOption(qIdx: number) {
    const newQuestions = JSON.parse(JSON.stringify(questions));
    newQuestions[qIdx].options.push({
      label: "Lựa chọn mới",
      value: `v_${Date.now()}`,
      score: 0,
      icon: "Circle",
    });
    liveEditStore.updateField("metadata.quiz_questions", newQuestions);
  }

  function removeOption(qIdx: number, oIdx: number) {
    const newQuestions = $state.snapshot(questions);
    newQuestions[qIdx].options.splice(oIdx, 1);
    liveEditStore.updateField("metadata.quiz_questions", newQuestions);
  }

  function nextStep(value: string, label: string) {
    answers.push({ q: questions[currentStep].title, a: label });
    if (currentStep < questions.length - 1) {
      currentStep++;
    } else {
      currentStep++;
      // Trigger AI Agentic Analysis
      shopStore.analyzeDiagnostics(answers);
    }
  }

  function prevStep() {
    if (currentStep > 0) {
      currentStep--;
      answers.pop();
    }
  }

  function restart() {
    currentStep = 0;
    answers = [];
    shopStore.diagnosticResult = null;
    shopStore.setQuantity(1);
  }

  function toSentenceCase(str: string) {
    if (!str) return "";
    const cleanStr = str.replace(/<[^>]*>/g, "").trim();
    if (!cleanStr) return str;
    return cleanStr.charAt(0).toUpperCase() + cleanStr.slice(1).toLowerCase();
  }

  function formatRecommendation(
    text: string,
    theme: "desktop" | "mobile",
  ): string {
    if (!text) return "";
    const cleaned = text.trim();

    const stepMatches = [
      ...cleaned.matchAll(
        /(\d+)\.\s*([^:]+):\s*(.+?)(?=\s*\d+\.\s*|\s*\*\*|\Z)/gs,
      ),
    ];
    const phaseMatches = [
      ...cleaned.matchAll(/\*\*([^*]+?):\*\*\s*(.+?)(?=\s*\*\*|\Z)/gs),
    ];

    let html = "";

    if (stepMatches.length > 0) {
      html += `<div class="recommendation-steps-container space-y-3 mb-5 text-left">`;
      stepMatches.forEach((m) => {
        const num = m[1];
        const title = m[2].trim();
        const desc = m[3].trim();

        const accentColor =
          theme === "desktop" ? "var(--luxury-gold)" : "#FFB7C5";
        const badgeBg =
          theme === "desktop"
            ? "rgba(193, 143, 126, 0.08)"
            : "rgba(255, 183, 197, 0.08)";
        const badgeBorder =
          theme === "desktop"
            ? "rgba(193, 143, 126, 0.2)"
            : "rgba(255, 183, 197, 0.2)";

        html += `
          <div class="step-card p-4 rounded-[1.5rem] bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all duration-300 shadow-[inset_0_1px_1px_rgba(255,255,255,0.02)]">
            <div class="flex items-center gap-3 mb-2">
              <div class="step-badge w-8 h-8 rounded-full flex items-center justify-center text-xs font-black shrink-0" 
                   style="background: ${badgeBg}; border: 1px solid ${badgeBorder}; color: ${accentColor}; box-shadow: 0 0 10px rgba(193,143,126,0.1)">
                ${num}
              </div>
              <h5 class="text-xs font-black tracking-widest first-letter:uppercase" style="color: ${accentColor}; margin: 0;">${title}</h5>
            </div>
            <p class="text-white/85 text-xs md:text-sm leading-relaxed">${desc}</p>
          </div>
        `;
      });
      html += `</div>`;
    }

    if (phaseMatches.length > 0) {
      html += `<div class="recommendation-phases-container grid grid-cols-1 gap-3 pt-4 border-t border-white/5 text-left">`;
      phaseMatches.forEach((m) => {
        const title = m[1].trim();
        const desc = m[2].trim();

        let phaseBg = "rgba(239, 68, 68, 0.03)";
        let phaseBorder = "rgba(239, 68, 68, 0.15)";
        let phaseText = "text-red-400";

        if (title.toLowerCase().includes("duy trì")) {
          phaseBg = "rgba(52, 211, 153, 0.03)";
          phaseBorder = "rgba(52, 211, 153, 0.15)";
          phaseText = "text-emerald-400";
        } else if (title.toLowerCase().includes("tấn công")) {
          phaseBg =
            theme === "desktop"
              ? "rgba(193, 143, 126, 0.03)"
              : "rgba(255, 183, 197, 0.03)";
          phaseBorder =
            theme === "desktop"
              ? "rgba(193, 143, 126, 0.15)"
              : "rgba(255, 183, 197, 0.15)";
          phaseText =
            theme === "desktop" ? "text-luxury-copper" : "text-pink-300";
        }

        html += `
          <div class="phase-card p-4 rounded-[1.5rem] border transition-all duration-300" 
               style="background: ${phaseBg}; border-color: ${phaseBorder};">
            <div class="flex items-center gap-2 mb-2">
              <div class="w-1.5 h-1.5 rounded-full bg-current ${phaseText} animate-pulse"></div>
              <h5 class="text-xs font-black tracking-[0.2em] first-letter:uppercase ${phaseText}">${title}</h5>
            </div>
            <p class="text-white/85 text-xs md:text-sm leading-relaxed">${desc}</p>
          </div>
        `;
      });
      html += `</div>`;
    }

    if (stepMatches.length === 0 && phaseMatches.length === 0) {
      let fallback = cleaned
        .replace(
          /\*\*([^*]+?):\*\*/g,
          '<strong class="text-emerald-400 font-bold">$1:</strong>',
        )
        .replace(
          /\*\*([^*]+?)\*\*/g,
          '<strong class="text-emerald-400 font-bold">$1</strong>',
        );
      return `<p class="text-white/80 text-xs md:text-sm leading-relaxed">${fallback}</p>`;
    }

    return html;
  }
</script>

<!-- SVG Filter for Liquid/Gooey Effect -->
<svg
  class="invisible absolute"
  width="0"
  height="0"
  xmlns="http://www.w3.org/2000/svg"
  version="1.1"
>
  <defs>
    <filter id="liquid-goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
      <feColorMatrix
        in="blur"
        mode="matrix"
        values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9"
        result="goo"
      />
      <feComposite in="SourceGraphic" in2="goo" operator="atop" />
    </filter>
  </defs>
</svg>

<div
  bind:this={quizContainer}
  class="clinical-quiz {!shopStore.diagnosticResult
    ? 'glass-liquid border-white/5'
    : ''} {shopStore.diagnosticResult
    ? 'p-0 md:p-0 lg:p-12 max-w-6xl'
    : 'p-6 md:p-8 lg:p-12 max-w-6xl'} rounded-[3.5rem] relative overflow-hidden mx-auto shadow-2xl min-h-[500px]"
>
  <!-- Subdued Neural Orbs -->
  <div
    class="neural-orb -top-20 -right-20 opacity-20"
    style:background="radial-gradient(circle, var(--luxury-copper) 0%,
    transparent 70%)"
    style:transform="scale(1.5)"
  ></div>
  <div
    class="neural-orb -bottom-40 -left-20 opacity-10"
    style:background="radial-gradient(circle, var(--luxury-gold) 0%, transparent
    70%)"
  ></div>

  <!-- Neural Progress Track (Elite V2.2) -->
  <div class="absolute top-0 left-0 right-0 h-1 bg-white/5 overflow-hidden">
    <div
      class="h-full bg-gradient-to-r from-luxury-copper via-luxury-gold to-luxury-peach transition-all duration-1000 ease-[cubic-bezier(0.23,1,0.32,1)] shadow-[0_0_20px_rgba(193,143,126,0.5)] relative"
      style:width="{progress}%"
    >
      <!-- Leading Edge Scan Glow -->
      <div
        class="absolute right-0 top-1/2 -translate-y-1/2 w-4 h-full bg-white blur-[4px] opacity-80"
      ></div>
      <div
        class="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-full bg-white shadow-[0_0_15px_#fff]"
      ></div>
    </div>
  </div>

  {#if isEditable}
    <div class="edit-mode-container relative z-surface animate-reveal py-4">
      <div
        class="flex items-center justify-between mb-10 border-b border-white/5 pb-6"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-2 h-2 rounded-full bg-luxury-copper animate-pulse shadow-[0_0_10px_var(--luxury-copper)]"
          ></div>
          <h3 class="text-sm font-semibold text-white tracking-[0.4em]">
            Quiz direct engine // V2.2
          </h3>
        </div>
        <button
          onclick={addQuestion}
          class="flex items-center gap-2 px-6 py-3 bg-luxury-copper hover:bg-luxury-gold text-white text-[10px] font-semibold rounded-full shadow-xl active:scale-95 transition-all"
        >
          <Plus size={14} /> Thêm câu hỏi mới
        </button>
      </div>

      <div
        class="space-y-12 max-h-[70vh] overflow-y-auto px-4 pb-40 custom-scrollbar relative z-10 touch-pan-y"
        onwheel={(e) => e.stopPropagation()}
        ontouchmove={(e) => e.stopPropagation()}
      >
        {#each questions as question, qIdx (question.id)}
          <div
            class="edit-question-card bg-white/[0.02] border border-white/5 rounded-[2.5rem] p-8 relative group/q h-fit transition-all duration-300 {draggingIdx ===
            qIdx
              ? 'opacity-20 scale-95 border-blue-500/50'
              : ''}"
            draggable="true"
            ondragstart={() => handleDragStart(qIdx)}
            ondragover={(e) => handleDragOver(e, qIdx)}
            ondrop={() => handleDrop(qIdx)}
            ondragend={() => (draggingIdx = null)}
          >
            <div
              class="absolute left-4 top-1/2 -translate-y-1/2 opacity-0 group-hover/q:opacity-100 transition-opacity cursor-grab active:cursor-grabbing p-2 text-white/10 hover:text-blue-400"
            >
              <GripVertical size={20} />
            </div>

            <button
              onclick={() => removeQuestion(qIdx)}
              class="absolute -top-3 -right-3 w-8 h-8 bg-red-500/10 hover:bg-red-500 text-red-500 rounded-full flex items-center justify-center opacity-0 group-hover/q:opacity-100 transition-all border border-red-500/20"
            >
              <Trash2 size={12} />
            </button>

            <div class="flex gap-6">
              <div
                class="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center text-white/20 font-semibold italic shrink-0"
              >
                {qIdx + 1}
              </div>
              <div class="flex-1 space-y-6 text-left">
                <div class="space-y-2">
                  <label
                    class="text-[8px] font-semibold text-white/20 tracking-widest pl-1"
                    >Question title</label
                  >
                  <input
                    bind:value={question.title}
                    class="w-full bg-transparent border-b border-white/10 focus:border-luxury-copper py-1 text-2xl font-medium text-white outline-none transition-all"
                    oninput={() =>
                      liveEditStore.updateField(
                        `metadata.quiz_questions.${qIdx}.title`,
                        question.title,
                      )}
                  />
                </div>
                <div class="space-y-2">
                  <label
                    class="text-[8px] font-semibold text-white/20 tracking-widest pl-1"
                    >Context / Subtitle</label
                  >
                  <input
                    bind:value={question.subtitle}
                    class="w-full bg-transparent border-b border-white/5 focus:border-luxury-copper/40 py-1 text-sm text-white/50 outline-none transition-all"
                    oninput={() =>
                      liveEditStore.updateField(
                        `metadata.quiz_questions.${qIdx}.subtitle`,
                        question.subtitle,
                      )}
                  />
                </div>

                <div class="space-y-4 pt-4">
                  <div class="flex items-center justify-between">
                    <span
                      class="text-[8px] font-semibold text-luxury-copper/60 tracking-widest"
                      >Options configuration</span
                    >
                    <button
                      onclick={() => addOption(qIdx)}
                      class="text-[8px] font-semibold text-white/20 hover:text-luxury-gold tracking-widest flex items-center gap-1"
                    >
                      <PlusCircle size={10} /> Add option
                    </button>
                  </div>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {#each question.options as option, oIdx}
                      <div
                        class="flex items-center gap-3 p-3 bg-white/[0.03] border border-white/5 rounded-xl group/opt"
                      >
                        <input
                          bind:value={option.label}
                          class="flex-1 bg-transparent text-xs font-medium text-white outline-none"
                          oninput={() =>
                            liveEditStore.updateField(
                              `metadata.quiz_questions.${qIdx}.options.${oIdx}.label`,
                              option.label,
                            )}
                        />
                        <div
                          class="flex items-center gap-1 bg-white/5 px-2 py-1 rounded-lg border border-white/5"
                        >
                          <Target size={10} class="text-white/20" />
                          <input
                            type="number"
                            bind:value={option.score}
                            class="w-6 bg-transparent text-[10px] font-semibold text-luxury-copper text-center outline-none"
                            oninput={() =>
                              liveEditStore.updateField(
                                `metadata.quiz_questions.${qIdx}.options.${oIdx}.score`,
                                option.score,
                              )}
                          />
                        </div>
                        <button
                          onclick={() => removeOption(qIdx, oIdx)}
                          class="text-red-500/20 hover:text-red-400 opacity-0 group-hover/opt:opacity-100 transition-opacity"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    {/each}
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {:else if questions.length > 0}
    {#if currentStep < questions.length}
      <div
        id="s{currentStep + 1}"
        class="step-container relative z-surface"
        in:fly={{ y: 30, duration: 800, easing: quintOut }}
      >
        <!-- Step Header with Back Button -->
        <div class="flex items-center gap-6 mb-8 md:mb-12 animate-fade-in">
          {#if currentStep > 0}
            <button
              onclick={prevStep}
              class="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-luxury-copper hover:bg-luxury-copper/10 hover:border-luxury-copper/30 transition-all active:scale-90 group/back"
              aria-label="Quay lại"
            >
              <ArrowLeft
                size={20}
                class="group-hover/back:-translate-x-1 transition-transform"
              />
            </button>
          {/if}
          <div class="flex flex-col">
            <span
              class="text-[10px] font-black text-white/20 tracking-[0.4em] font-mono"
              >Ai sequence phase</span
            >
            <div class="flex items-center gap-2 mt-1">
              <span
                class="text-xs font-black text-luxury-copper italic tracking-widest"
                >Bước {currentStep + 1} // {questions.length}</span
              >
              <div class="h-px w-12 bg-white/5"></div>
              <span class="text-[9px] font-bold text-white/10 tracking-widest"
                >{Math.round(((currentStep + 1) / questions.length) * 100)}%
                hoàn thành</span
              >
            </div>
          </div>
        </div>

        <div class="mb-8 md:mb-10 text-left">
          <h3
            class="text-xl md:text-2xl font-black text-white mb-3 tracking-[-0.01em] leading-tight font-sans bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-white/90"
            style:text-transform="none"
          >
            {@html toSentenceCase(questions[currentStep].title)}
          </h3>
          <p class="text-luxury-peach/40 font-medium text-lg leading-relaxed">
            {questions[currentStep].subtitle}
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          {#each questions[currentStep].options as option, idx}
            <button
              onclick={() => nextStep(option.value, option.label)}
              onkeydown={(e) =>
                e.key === "Enter" && nextStep(option.value, option.label)}
              aria-label="Select {option.label}"
              class="group p-6 text-left glass-liquid border-white/5 rounded-[2rem] hover:border-luxury-copper/30 transition-all duration-500 flex items-center gap-6 relative overflow-hidden liquid-bubble"
              in:fly={{
                x: 15,
                duration: 800,
                delay: idx * 50,
                easing: quintOut,
              }}
            >
              <div
                class="w-16 h-16 bg-white/5 rounded-[1.5rem] flex items-center justify-center group-hover:scale-105 transition-all duration-500 border border-white/5 relative z-surface"
              >
                <QuizIcon icon={option.icon} />
              </div>
              <div class="flex-1 relative z-surface">
                <span
                  class="block text-xl font-medium text-white/90 group-hover:text-luxury-gold transition-colors tracking-tight"
                  style:text-transform="none"
                  >{@html toSentenceCase(option.label)}</span
                >
              </div>

              <div
                class="w-10 h-10 rounded-full border border-white/5 group-hover:border-luxury-gold/50 group-hover:bg-luxury-gold/20 flex items-center justify-center transition-all duration-500 relative z-surface"
              >
                <svg
                  class="w-5 h-5 text-white scale-0 group-hover:scale-100 transition-all duration-300"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="4"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
            </button>
          {/each}
        </div>
      </div>
    {:else if shopStore.isAnalyzing}
      <DiagnosticScanner
        status="Hệ thống AI đang giải mã hắc tố và thiết kế phác đồ..."
      />
    {:else if shopStore.diagnosticResult}
      <div
        class="result-container text-center py-0 md:py-0 lg:py-10 relative z-surface"
        in:fade={{ duration: 1000 }}
      >
        <div class="mb-0 md:mb-0 lg:mb-12 text-left relative overflow-hidden">
          <div
            class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 pb-6"
          >
            <div>
              <h3
                class="text-3xl md:text-[2.25rem] lg:text-5xl font-semibold text-white tracking-tighter mb-2 whitespace-nowrap pt-2 uppercase"
              >
                PHÁC ĐỒ ĐIỀU TRỊ
              </h3>
              <p
                class="text-luxury-copper/60 font-semibold text-[10px] tracking-[0.4em]"
              >
                Kiến tạo bởi Trí tuệ Nhân tạo osmo 2026
              </p>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right hidden md:block">
                <div
                  class="text-[10px] font-semibold text-white/30 tracking-widest"
                >
                  Hiệu lực
                </div>
                <div
                  class="text-emerald-400 font-medium text-sm tracking-tighter"
                >
                  Chứng thực an toàn
                </div>
              </div>
              <div
                class="w-16 h-16 rounded-3xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center"
              >
                <svg
                  class="w-8 h-8 text-emerald-400"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"
                  />
                </svg>
              </div>
            </div>
          </div>

          <div class="space-y-6">
            <div>
              <h4
                class="text-xs font-semibold text-luxury-copper/60 mb-2 tracking-[0.3em]"
              >
                Phân tích chuyên sâu
              </h4>
              <p
                class="text-white text-[16px] md:text-[18px] lg:text-[22px] font-medium leading-tight tracking-tight"
              >
                {@html shopStore.diagnosticResult.analysis}
              </p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6">
              <div>
                <h4
                  class="text-[10px] font-semibold text-white/30 mb-3 tracking-[0.3em]"
                >
                  Tổng quan
                </h4>
                <p class="text-white/50 text-sm leading-relaxed">
                  {shopStore.diagnosticResult.reasoning}
                </p>
              </div>
              <div>
                <div class="flex items-center gap-3 mb-3">
                  <h4
                    class="text-[10px] font-semibold text-emerald-400/60 tracking-[0.3em]"
                  >
                    Liệu trình tối ưu
                  </h4>
                </div>
                <div
                  class="text-emerald-500/80 text-sm font-medium leading-relaxed"
                >
                  {@html formatRecommendation(
                    shopStore.diagnosticResult.recommendation,
                    "desktop",
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          class="flex flex-col gap-4 max-w-sm mx-auto mt-8 md:mt-10 lg:mt-12"
        >
          <button
            onclick={() => {
              const recommendedQty = shopStore.diagnosticResult?.quantity || 1;
              const variant = shopStore.product?.variants?.find(
                (v) => (v.attributes?.combo_qty || 1) === recommendedQty,
              );
              if (variant) {
                shopStore.selectVariant(variant);
              }
              document
                .getElementById("offers")
                ?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            class="group relative w-full py-5 md:py-6 bg-luxury-copper text-white rounded-[2rem] font-semibold text-2xl md:text-2xl lg:text-3xl shadow-[0_20px_50px_rgba(193,143,126,0.4)] overflow-hidden active:scale-[0.98] transition-all duration-500"
          >
            <span class="relative z-surface">Xem liệu trình</span>
            <div
              class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"
            ></div>
          </button>

          <!-- Security & Privacy Disclaimer integrated inside clinical results card -->
          <p
            class="text-[9px] font-medium text-white/35 tracking-[0.05em] leading-relaxed whitespace-nowrap mx-auto text-center mt-2 animate-fade-in"
          >
            AI có thể mắc sai sót. Vì vậy, hãy xác minh thông tin này với bác
            sĩ.
          </p>

          <button
            onclick={restart}
            class="text-[10px] font-semibold text-white/10 hover:text-luxury-copper/50 transition-colors tracking-[0.4em] py-2"
          >
            Làm lại chẩn đoán
          </button>
        </div>
      </div>
    {/if}
  {:else}
    <div class="py-24 text-center relative z-surface" in:fade>
      <div class="mb-10 relative">
        <div
          class="absolute inset-0 bg-luxury-copper/10 blur-[60px] rounded-full animate-pulse"
        ></div>
        <div
          class="w-24 h-24 bg-white/5 rounded-full border border-luxury-copper/20 flex items-center justify-center backdrop-blur-3xl mx-auto relative group"
        >
          <div
            class="absolute inset-0 border border-luxury-copper/20 rounded-full animate-ping opacity-20"
          ></div>
          <svg
            class="w-12 h-12 text-luxury-copper/40 animate-spin-slow"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M12 4V2m0 20v-2m8-8h2M2 12h2m13.657-6.343l1.414-1.414M4.929 19.071l1.414-1.414m12.728 0l1.414 1.414M4.929 4.929l1.414 1.414"
            />
          </svg>
        </div>
      </div>
      <h4
        class="text-xl font-semibold text-white mb-2 tracking-[0.2em] italic opacity-80"
      >
        Đang quét sinh học
      </h4>
      <p
        class="text-luxury-copper/30 font-medium tracking-[0.4em] text-[10px] animate-pulse"
      >
        Khởi tạo trí tuệ osmo 2026...
      </p>
    </div>
  {/if}
</div>

<style>
  :global(.clinical-quiz) {
    transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
    background: rgba(255, 255, 255, 0.015) !important;
    backdrop-filter: blur(40px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(40px) saturate(180%) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
  }
  .z-surface {
    z-index: var(--z-content);
  }

  /* Premium Custom Scrollbar - Elite V2.2 */
  .custom-scrollbar {
    overscroll-behavior: contain;
  }

  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(193, 143, 126, 0.2);
    border-radius: 10px;
    border: 2px solid transparent;
    background-clip: content-box;
    transition: all 0.3s ease;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(193, 143, 126, 0.5);
    background-clip: content-box;
  }

  /* Premium Option Styling - Elite V2.2 */
  :global(.clinical-quiz .liquid-bubble) {
    transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1) !important;
    background: rgba(255, 255, 255, 0.01) !important;
    border: 1px solid rgba(255, 255, 255, 0.03) !important;
  }

  :global(.clinical-quiz .liquid-bubble:hover) {
    border-color: rgba(255, 183, 197, 0.25) !important;
    background: rgba(255, 183, 197, 0.02) !important;
    box-shadow:
      0 30px 60px rgba(0, 0, 0, 0.6),
      inset 0 0 20px rgba(255, 183, 197, 0.05) !important;
    transform: translateY(-2px);
  }

  :global(.clinical-quiz .liquid-bubble:active) {
    transform: translateY(0) scale(0.98);
  }
</style>
