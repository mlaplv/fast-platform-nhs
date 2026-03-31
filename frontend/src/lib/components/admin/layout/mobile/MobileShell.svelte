<script lang="ts">
  import { nanobot } from "$lib/state/nanobot.svelte";
  import VoiceModal from "../../VoiceModal.svelte";
  import MobileNavDrawer from "./MobileNavDrawer.svelte";
  import MobileInputBar from "./MobileInputBar.svelte";
  import MobileHome from "./MobileHome.svelte";
  import MobileContextSheet from "./MobileContextSheet.svelte";
  import MobileQuickTips from "./MobileQuickTips.svelte";
  import ConfirmationModal from "../../ui/ConfirmationModal.svelte";
  import VaultModal from "../../VaultModal.svelte";

  let { children } = $props();
</script>

<div class="admin-layout fixed inset-0 flex flex-col overflow-hidden bg-[#020202] text-gray-100 font-sans">
  
  <!-- Main Content Area -->
  <main class="relative flex-1 z-10 overflow-hidden flex flex-col w-full h-full">
    <!-- XoHi Conversation Home -->
    <MobileHome />

    <!-- Context Sheet (Slides up over Home when a widget is active) -->
    <MobileContextSheet />
    
    <!-- Render children if any (usually dynamic routing content) -->
    <div class="hidden">
      {@render children?.()}
    </div>
  </main>

  <!-- Navigation Drawer (Hamburger Menu) -->
  <MobileNavDrawer />

  <!-- Progressive Blur / Glassmorphism Deck (Safari Style) -->
  <div 
    class="fixed bottom-0 left-0 right-0 h-32 pointer-events-none z-70"
    style="backdrop-filter: blur(8px); mask-image: linear-gradient(to top, black, transparent);"
  ></div>

  <!-- Voice Input Bar (Bottom fixed) -->
  <MobileInputBar />

  <!-- Quick Tips Overlay (Phase 13) -->
  <MobileQuickTips />

  <!-- Full-screen Voice Interaction Modal -->
  <VoiceModal />

  <!-- Global System Modals -->
  <ConfirmationModal />
  <VaultModal />
</div>
