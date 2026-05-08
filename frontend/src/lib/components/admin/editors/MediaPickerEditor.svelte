<script lang="ts">
  import FileManager from "$lib/components/media/FileManager.svelte";
  import type { MediaAsset } from "$lib/state/types";
  import { resolveMediaUrl } from "$lib/state/utils";
  import Check from "@lucide/svelte/icons/check";
  import X from "@lucide/svelte/icons/x";
  import { liveEditStore } from "$lib/state/commerce/liveEdit.svelte";

  import type { Product } from '$lib/types';

  let { path, type, onSave, onClose } = $props<{
    path: string;
    type: 'image' | 'video';
    onSave: (val: string) => void;
    onClose: () => void;
  }>();

  const getValue = (p: string) => {
    if (!liveEditStore.dirtyProduct) return "";
    const keys = p.split(".");
    let current: any = liveEditStore.dirtyProduct as Product;
    for (const key of keys) {
        if (!current) return "";
        current = (current as any)[key];
    }
    return current || "";
  };

  let selectedUrl = $state(getValue(path));

  function handleConfirm(assets: MediaAsset[]) {
    if (assets.length > 0) {
      const asset = assets[0];
      onSave(asset.file_path || asset.url);
    }
  }

  function handleClose() {
    onClose();
  }
</script>

<div class="h-full w-full bg-[#0a0c10]">
  <FileManager 
    mode="pick" 
    onPickConfirm={handleConfirm}
    onPickClose={handleClose}
    standalone={true}
  />
</div>

<style lang="postcss">
</style>
