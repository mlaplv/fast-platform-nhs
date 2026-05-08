<script lang="ts">
  import { scale } from 'svelte/transition';
  import RotateCcw from "@lucide/svelte/icons/rotate-ccw";
  import Trash2 from "@lucide/svelte/icons/trash-2";
    import type { MediaAsset } from '$lib/state/types';
    import { mediaStore } from '$lib/state/media.svelte';
    import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';

    interface Props {
        asset: MediaAsset;
        onRestore: (id: string) => void;
        onDelete: (id: string) => void;
    }

    let { asset, onRestore, onDelete } = $props<Props>();
</script>

<div class="absolute inset-0 bg-[#0c0e14]/60 backdrop-blur-md opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center gap-4" style="z-index: {Z_INDEX_ADMIN.TOOLBAR_SUB};">
    <button
        onclick={(e) => { e.stopPropagation(); onRestore(asset.id); }}
        class="w-12 h-12 rounded-full bg-green-500/20 border border-green-500/50 text-green-400 flex items-center justify-center hover:bg-green-500 hover:text-white transition-all shadow-lg active:scale-90"
        title="Khôi phục"
    >
        <RotateCcw size={20} />
    </button>
    <button
        onclick={(e) => { e.stopPropagation(); onDelete(asset.id); }}
        class="w-12 h-12 rounded-full bg-red-500/20 border border-red-500/50 text-red-400 flex items-center justify-center hover:bg-red-500 hover:text-white transition-all shadow-lg active:scale-90"
        title="Xoá vĩnh viễn"
    >
        <Trash2 size={20} />
    </button>
</div>
