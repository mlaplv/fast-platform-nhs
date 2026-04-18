<script lang="ts">
  import { fomoStore } from '$lib/state/commerce/fomo.svelte';
  import { fly, fade } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { ShoppingBag, Users, Zap } from 'lucide-svelte';
  import { onDestroy } from 'svelte';

  onDestroy(() => {
    fomoStore.dispose();
  });
</script>

{#if fomoStore.isActivityVisible && fomoStore.currentActivity}
  <div 
    class="neural-activity-root fixed z-[var(--z-fomo, 9999)] pointer-events-none"
    in:fly={{ x: -20, duration: 800, easing: cubicOut }}
    out:fade={{ duration: 400 }}
  >
    <div class="neural-bar-v2">
      <!-- Neural Aura Glow -->
      <div class="neural-glow"></div>
      
      <div class="neural-inner">
        <!-- Live Status Pulse -->
        <div class="neural-status">
          <div class="status-dot"></div>
        </div>

        <!-- Activity Icon -->
        <div class="neural-icon-wrap">
          {#if fomoStore.currentActivity.type === 'ORDER'}
            <ShoppingBag class="w-2.5 h-2.5 text-[#C18F7E]" />
          {:else if fomoStore.currentActivity.type === 'VISITORS'}
            <Users class="w-2.5 h-2.5 text-emerald-400" />
          {:else}
            <Zap class="w-2.5 h-2.5 text-purple-400" />
          {/if}
        </div>

        <!-- Single Line Content -->
        <div class="neural-text-line">
          {#if fomoStore.currentActivity.type === 'ORDER'}
            <span class="user-name">{fomoStore.currentActivity.name}</span>
            <span class="action-text">{fomoStore.currentActivity.action}</span>
          {:else}
            <span class="action-text">{fomoStore.currentActivity.msg}</span>
          {/if}
          
          <span class="time-tag">• vừa xong</span>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .neural-activity-root {
    bottom: 24px;
    left: 20px;
  }

  .neural-bar-v2 {
    position: relative;
    padding: 1px;
    border-radius: 100px;
    background: linear-gradient(135deg, rgba(193, 143, 126, 0.3), rgba(255, 255, 255, 0.05));
    overflow: hidden;
  }

  .neural-inner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px 6px 10px;
    background: rgba(10, 10, 11, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 100px;
    border: 0.5px solid rgba(255, 255, 255, 0.08);
  }

  .neural-status {
    position: relative;
    width: 6px;
    height: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .status-dot {
    width: 4px;
    height: 4px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10b981;
    animation: pulse-dot 2s infinite;
  }

  @keyframes pulse-dot {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 15px #10b981; }
    100% { transform: scale(0.95); opacity: 0.8; }
  }

  .neural-icon-wrap {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 50%;
    border: 0.5px solid rgba(255, 255, 255, 0.1);
  }

  .neural-text-line {
    display: flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
  }

  .user-name {
    font-size: 11px;
    font-weight: 800;
    color: #C18F7E;
    letter-spacing: -0.01em;
  }

  .action-text {
    font-size: 11px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
    letter-spacing: -0.01em;
  }

  .time-tag {
    font-size: 9px;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.3);
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }

  .neural-glow {
    position: absolute;
    inset: -10px;
    background: radial-gradient(circle at 20% 50%, rgba(193, 143, 126, 0.15), transparent 60%);
    pointer-events: none;
    animation: glow-move 4s infinite alternate;
  }

  @keyframes glow-move {
    from { opacity: 0.3; transform: translateX(-10%); }
    to { opacity: 0.6; transform: translateX(10%); }
  }

  @media (max-width: 768px) {
    .neural-activity-root {
      left: 10px;
      right: auto;
      bottom: 82px; /* Dâng cao để né Bottom Nav */
    }
  }
</style>
