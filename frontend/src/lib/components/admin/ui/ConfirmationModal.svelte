<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import { Z_INDEX } from "$lib/core/constants/zIndex";
  import type { FormField } from "$lib/state/types";
  import Check from "lucide-svelte/icons/check";
  import MissionControlShell from "./MissionControlShell.svelte";
  import AlertTriangle from "lucide-svelte/icons/alert-triangle";

  const dialog = $derived(nanobot.confirmDialog);
  let promptValue = $state("");
  let formValues = $state<Record<string, string>>({});
  let submitted = $state(false);

  // Initialize form values when dialog opens
  $effect(() => {
    if (dialog) {
      submitted = false;
      if (dialog.fields && dialog.fields.length > 0) {
        const init: Record<string, string> = {};
        for (const f of dialog.fields) {
          init[f.key] = f.defaultValue || "";
        }
        formValues = init;
      } else if (dialog.isPrompt && typeof dialog.defaultValue !== "undefined") {
        promptValue = dialog.defaultValue;
      } else {
        promptValue = "";
        formValues = {};
      }
    }
  });

  function isFormValid(): boolean {
    if (!dialog?.fields) return true;
    for (const f of dialog.fields) {
      if (f.required && !formValues[f.key]?.trim()) return false;
    }
    return true;
  }

  function handleConfirm(e?: Event) {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!dialog) return;

    submitted = true;

    if (dialog.fields && dialog.fields.length > 0) {
      if (!isFormValid()) return;
      dialog.onConfirm(formValues);
    } else {
      dialog.onConfirm(promptValue);
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    e.stopPropagation();
    if (e.key === "Enter" && (dialog?.isPrompt || dialog?.fields)) {
      e.preventDefault();
      handleConfirm(e);
    }
  }

  function handleCancel(e: Event) {
    e.preventDefault();
    e.stopPropagation();
    dialog?.onCancel?.();
  }

  function isFieldInvalid(field: FormField): boolean {
    return submitted && !!field.required && !formValues[field.key]?.trim();
  }
</script>

{#if dialog}
  <MissionControlShell
    title={dialog.title || "SYSTEM_CONFIRMATION"}
    isOpen={!!dialog}
    onClose={() => dialog.onCancel?.()}
    headerIcon={AlertTriangle}
    maxWidth={dialog.fields && dialog.fields.length > 0 ? "max-w-xl" : "max-w-lg"}
    height="h-auto"
    zIndex={Z_INDEX.MODAL_CONFIRM}
    backdropClass="bg-[#050505]/95 md:bg-black/40 md:backdrop-blur-sm"
  >
    <div class="px-8 py-6 relative">
      <!-- Message -->
      <p class="text-gray-300 text-sm leading-relaxed font-light tracking-wide mb-6 text-center">
        {dialog.message}
      </p>

      <!-- Multi-field form -->
      {#if dialog.fields && dialog.fields.length > 0}
        <div class="space-y-4">
          {#each dialog.fields as field}
            <div class="space-y-1.5">
              <label
                for="field-{field.key}"
                class="block text-[10px] font-mono font-bold uppercase tracking-[.2em]
                  {isFieldInvalid(field) ? 'text-red-400' : 'text-gray-400'}"
              >
                {field.label}
                {#if field.required}<span class="text-red-400/80">*</span>{/if}
              </label>

              {#if field.type === "select"}
                <select
                  id="field-{field.key}"
                  bind:value={formValues[field.key]}
                  class="w-full bg-black/60 border rounded-lg px-4 py-2.5 text-sm font-mono text-white
                    outline-none transition-all appearance-none cursor-pointer
                    {isFieldInvalid(field)
                      ? 'border-red-500/50 focus:border-red-400/80'
                      : 'border-white/10 focus:border-cyan-500/50 hover:border-white/20'}"
                >
                  {#each field.options || [] as opt}
                    <option value={opt.value} class="bg-gray-900">{opt.label}</option>
                  {/each}
                </select>

              {:else if field.type === "textarea"}
                <textarea
                  id="field-{field.key}"
                  bind:value={formValues[field.key]}
                  placeholder={field.placeholder}
                  rows="2"
                  class="w-full bg-black/60 border rounded-lg px-4 py-2.5 text-sm font-mono text-white
                    outline-none transition-all resize-none
                    {isFieldInvalid(field)
                      ? 'border-red-500/50 focus:border-red-400/80'
                      : 'border-white/10 focus:border-cyan-500/50 hover:border-white/20'}"
                ></textarea>

              {:else}
                <input
                  id="field-{field.key}"
                  type={field.type}
                  bind:value={formValues[field.key]}
                  placeholder={field.placeholder}
                  onkeydown={handleKeydown}
                  class="w-full bg-black/60 border rounded-lg px-4 py-2.5 text-sm font-mono text-white
                    outline-none transition-all
                    {isFieldInvalid(field)
                      ? 'border-red-500/50 focus:border-red-400/80'
                      : 'border-white/10 focus:border-cyan-500/50 hover:border-white/20'}"
                />
              {/if}

              {#if isFieldInvalid(field)}
                <p class="text-[9px] font-mono text-red-400/80 tracking-wider">
                  Trường này bắt buộc
                </p>
              {/if}
            </div>
          {/each}
        </div>

      <!-- Single prompt input (legacy) -->
      {:else if dialog.isPrompt}
        <input
          type="text"
          bind:value={promptValue}
          onkeydown={handleKeydown}
          placeholder={dialog.promptPlaceholder || "ENTER_DATA..."}
          class="w-full bg-black/50 border border-white/10 focus:border-cyan-500/50 text-white
            font-mono text-sm px-4 py-3 rounded-lg outline-none transition-colors
            shadow-inner text-center tracking-wider max-w-[80%] mx-auto block"
        />
      {/if}
    </div>

    <!-- Action buttons -->
    <div class="flex border-t border-cyan-500/10">
      <button
        onclick={handleCancel}
        class="flex-1 py-5 text-[11px] font-mono font-bold tracking-[.4em] uppercase
          text-gray-500 hover:text-white border-r border-cyan-500/10
          bg-white/[0.01] hover:bg-white/[0.03] transition-all"
      >
        {dialog.cancelLabel || "HỦY"}
      </button>
      <button
        onclick={handleConfirm}
        class="flex-1 py-5 text-[11px] font-mono font-bold tracking-[.4em] uppercase
          text-cyan-400 bg-cyan-500/5 hover:bg-cyan-500 hover:text-black
          transition-all group overflow-hidden relative"
      >
        <div
          class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent
            translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"
        ></div>
        <span class="flex items-center justify-center gap-3 relative z-10">
          <Check size={18} />
          {dialog.confirmLabel || "XÁC NHẬN"}
        </span>
      </button>
    </div>
  </MissionControlShell>
{/if}


