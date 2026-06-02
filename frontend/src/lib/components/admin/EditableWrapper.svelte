<script lang="ts">
  import { lightLiveEdit } from "$lib/state/commerce/liveEditState.svelte";

  interface Props {
    path: string;
    type?: 'text' | 'html' | 'image' | 'video' | 'quiz' | 'metrics';
    label?: string;
    value?: string; 
    class?: string;
    as?: 'div' | 'span';
    children?: import('svelte').Snippet;
  }

  let { path, type = 'text', label = 'SỬA NỘI DUNG', value, as = 'div', children, ...props }: Props = $props();

  const isEditMode = $derived(lightLiveEdit.isEditMode);

  // Elite V2.2: Pure lightweight extraction logic using zero-dependency store
  const product = $derived(lightLiveEdit.dirtyProduct);
  const currentValue = $derived.by(() => {
    if (!product) return value || "";
    try {
      const normalizedPath = path.replace(/\[(\d+)\]/g, '.$1');
      const keys = normalizedPath.split(".");
      let current: any = product;
      for (const key of keys) {
        if (current === null || current === undefined || typeof current !== 'object') return value || "";
        current = current[key];
      }
      return current ?? value ?? "";
    } catch {
      return value || "";
    }
  });

  const isDisabled = $derived(String(currentValue).startsWith('[OFF]'));
  const shouldRender = $derived(!isDisabled || isEditMode);
</script>

{#if shouldRender}
  {#if !isEditMode}
    <!-- ZERO-HYDRATION: When not in active Edit Mode, render absolute raw children. Zero bundles, zero styles. -->
    {@render children?.()}
  {:else}
    <!-- LAZY-LOADED ACTIVE EDITOR: Fetched dynamically only when edit mode is toggled, completely shielding regular users from admin assets -->
    <!-- svelte-ignore state_referenced_locally -->
    {#await import('./EditableWrapperActive.svelte') then { default: EditableWrapperActive }}
      <EditableWrapperActive
        {path}
        {type}
        {label}
        value={value}
        {as}
        class={props.class}
      >
        {@render children?.()}
      </EditableWrapperActive>
    {/await}
  {/if}
{/if}
