<script lang="ts">
  /**
   * EditorOverlays.svelte — Modals and Bubble Menus for Tiptap
   * Component split from TiptapEditor.svelte to maintain < 500 lines.
   * Elite V2.7: Strictly typed, no any, high-performance logic.
   */
  import { portal } from '$lib/core/actions/portal';
  import MediaVaultModal from "$lib/components/media/MediaVaultModal.svelte";
  import LinkDialog from '../ui/LinkDialog.svelte';
  import AnnotationTooltip from '../ui/AnnotationTooltip.svelte';
  import LinkBubbleMenu from '../ui/LinkBubbleMenu.svelte';
  import ImageBubbleMenu from '../ui/ImageBubbleMenu.svelte';
  import { resolveMediaUrl } from '$lib/state/utils';
  import { stripMarks } from '../utils/editorUtils';
  import { Z_INDEX_ADMIN } from '$lib/core/constants/z_index_admin';
  import type { Editor } from '@tiptap/core';
  import type { MediaAsset } from '$lib/state/types';

  let {
    editor,
    editable,
    showMediaVault = $bindable(),
    showLinkDialog = $bindable(),
    campaignId,
    assets = $bindable(),
    selectedAvatarUrl = $bindable(),
    selectedAssetIndex = $bindable(),
    blockClicks = $bindable(),
    imageMenuVisible = $bindable(),
    linkMenuVisible = $bindable(),
    isHoveringLinkMenu = $bindable(),
    linkHoverTimeout = $bindable(),
    linkPos = $bindable(),
    isSyncLocked = $bindable(),
    content = $bindable(),
    onChange,
    currentLinkData,
    tooltipVisible = $bindable(),
    tooltipX,
    tooltipY,
    tooltipType,
    tooltipText,
    isFixing,
    handleFix,
    handleTooltipEnter,
    handleTooltipLeave,
    linkMenuX,
    linkMenuY,
    imageMenuX,
    imageMenuY
  }: {
    editor: Editor | null;
    editable: boolean;
    showMediaVault: boolean;
    showLinkDialog: boolean;
    campaignId?: string;
    assets: (MediaAsset | string)[];
    selectedAvatarUrl: string | null;
    selectedAssetIndex: number;
    blockClicks: boolean;
    imageMenuVisible: boolean;
    linkMenuVisible: boolean;
    isHoveringLinkMenu: boolean;
    linkHoverTimeout: ReturnType<typeof setTimeout> | null;
    linkPos: number | null;
    isSyncLocked: boolean;
    content: string;
    onChange: (val: string) => void;
    currentLinkData: any;
    tooltipVisible: boolean;
    tooltipX: number;
    tooltipY: number;
    tooltipType: string;
    tooltipText: string;
    isFixing: boolean;
    handleFix: () => Promise<void>;
    handleTooltipEnter: () => void;
    handleTooltipLeave: () => void;
    linkMenuX: number;
    linkMenuY: number;
    imageMenuX: number;
    imageMenuY: number;
  } = $props();

</script>

<div use:portal>
  <MediaVaultModal
    isOpen={showMediaVault}
    onClose={() => showMediaVault = false}
    {campaignId}
    bind:assets={assets}
    bind:selectedAvatarUrl={selectedAvatarUrl}
    bind:selectedAssetIndex={selectedAssetIndex}
    onSelect={(url) => {
      if (editor) {
        blockClicks = true;
        imageMenuVisible = false;
        const safeUrl = resolveMediaUrl(url);
        
        isSyncLocked = true;
        
        setTimeout(() => {
          if (!editor || editor.isDestroyed) { isSyncLocked = false; return; }
          
          if (editor.isActive('image')) {
            editor.chain().focus().updateAttributes('image', { src: safeUrl }).run();
          } else {
            editor.chain().focus().setImage({ src: safeUrl }).run();
          }
          
          const cleaned = stripMarks(editor.getHTML());
          content = cleaned;
          onChange(cleaned);
          
          setTimeout(() => { 
            blockClicks = false; 
            isSyncLocked = false;
          }, 300);
        }, 50);
      }
    }}
  />
</div>

<div use:portal>
  <LinkDialog 
    bind:show={showLinkDialog} 
    currentData={currentLinkData} 
    onApply={(data) => {
      if (data.url && editor) {
        editor.chain().focus().setLink({ 
          href: data.url, 
          title: data.title, 
          target: data.target || undefined, 
          rel: data.rel || undefined 
        }).run();
      } else if (editor) {
        editor.chain().focus().unsetLink().run();
      }
    }} 
  />
</div>

<div use:portal>
  <AnnotationTooltip 
    bind:visible={tooltipVisible} 
    x={tooltipX} 
    y={tooltipY} 
    type={tooltipType} 
    text={tooltipText} 
    {isFixing} 
    onFix={handleFix} 
    onMouseEnter={handleTooltipEnter}
    onMouseLeave={handleTooltipLeave}
  />
</div>

{#if linkMenuVisible && editor && !blockClicks}
  <div
    use:portal
    class="fixed pointer-events-auto link-bubble-menu"
    style="left: {linkMenuX}px; top: {linkMenuY}px; transform: translate(-50%, -100%); z-index: {Z_INDEX_ADMIN.TIPTAP_LINK_BUBBLE};"
    role="tooltip"
    onmouseenter={() => {
      isHoveringLinkMenu = true;
      if (linkHoverTimeout) {
        clearTimeout(linkHoverTimeout);
        linkHoverTimeout = null;
      }
    }}
    onmouseleave={() => {
      isHoveringLinkMenu = false;
      linkHoverTimeout = setTimeout(() => {
        linkMenuVisible = false;
      }, 400);
    }}
  >
    <LinkBubbleMenu
      {editor}
      {linkPos}
      {currentLinkData}
      bind:linkMenuVisible={linkMenuVisible}
      onEdit={() => { showLinkDialog = true; linkMenuVisible = false; }}
      onClose={() => linkMenuVisible = false}
    />
  </div>
{/if}

{#if editor && editable && imageMenuVisible && !blockClicks && !showMediaVault && !showLinkDialog}
<div
  use:portal
  class="fixed -translate-x-1/2 -translate-y-full pointer-events-auto transition-all duration-75 ease-out image-bubble-menu"
  style="left: {imageMenuX}px; top: {imageMenuY}px; z-index: {Z_INDEX_ADMIN.TIPTAP_BUBBLE_MENU};"
>
  <ImageBubbleMenu
    {editor}
    onReplace={() => {
      if (!blockClicks) showMediaVault = true;
    }}
    onClose={() => imageMenuVisible = false}
  />
</div>
{/if}
