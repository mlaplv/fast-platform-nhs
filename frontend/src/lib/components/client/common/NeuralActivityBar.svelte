<script lang="ts">
  import { fomoStore } from '$lib/state/commerce/fomo.svelte';
  import { fly, fade } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { Users, ShoppingBag, Zap, ShieldCheck } from 'lucide-svelte';
  import { onMount, onDestroy } from 'svelte';

  const iconMap = {
    'VISITORS': Users,
    'ORDER': ShoppingBag,
    'TRENDING': Zap,
    'URGENCY': ShieldCheck
  };

  onMount(() => {
    // Neural Link Active
  });

  onDestroy(() => {
    fomoStore.dispose();
  });
</script>

{#if fomoStore.isActivityVisible && fomoStore.currentActivity}
  <div 
    class="neural-activity-container fixed bottom-6 left-6 z-[1000] pointer-events-none"
    in:fly={{ y: 20, duration: 800, easing: cubicOut }}
    out:fade={{ duration: 400 }}
  >
    <div class="neural-bar group">
      <!-- Liquid Glass Aura -->
      <div class="absolute -inset-2 bg-gradient-to-r from-luxury-sakura/20 via-luxury-gold/20 to-luxury-sakura/20 blur-2xl opacity-50 group-hover:opacity-100 transition-opacity duration-1000"></div>
      
      <div class="relative flex items-center gap-4 px-5 py-3 rounded-full bg-black/60 backdrop-blur-[40px] border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
        
        <!-- Action Icon with Neural Pulse -->
        <div class="relative flex-shrink-0">
          <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-luxury-gold/40 to-white/10 flex items-center justify-center border border-white/5">
            {#if fomoStore.currentActivity.type === 'ORDER'}
              <ShoppingBag class="w-5 h-5 text-luxury-gold" />
            {:else if fomoStore.currentActivity.type === 'VISITORS'}
              <Users class="w-5 h-5 text-emerald-400" />
            {:else}
              <Zap class="w-5 h-5 text-purple-400" />
            {/if}
          </div>
          <div class="absolute -bottom-1 -right-1 w-3 h-3 bg-emerald-500 rounded-full border-2 border-black animate-pulse"></div>
        </div>

        <!-- Text Content -->
        <div class="flex flex-col pr-2">
          <div class="flex items-center gap-2 mb-0.5">
            <span class="text-[9px] font-black text-white/30 uppercase tracking-[0.2em]">Neural_Sync</span>
            {#if fomoStore.currentActivity.type === 'ORDER'}
               <span class="text-[8px] font-mono text-luxury-gold uppercase px-1.5 py-0.5 rounded-full bg-luxury-gold/10 border border-luxury-gold/20">Live Order</span>
            {:else}
               <span class="text-[8px] font-mono text-emerald-400 uppercase px-1.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">Active</span>
            {/if}
          </div>
          
          <p class="text-[13px] text-white/90 font-medium leading-tight">
            {#if fomoStore.currentActivity.type === 'ORDER'}
              <span class="font-bold text-luxury-gold">{fomoStore.currentActivity.name}</span> {fomoStore.currentActivity.action}
            {:else}
              {fomoStore.currentActivity.msg}
            {/if}
          </p>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .neural-activity-container {
    perspective: 1000px;
  }

  .neural-bar {
    transition: transform 0.3s cubic-bezier(0.23, 1, 0.32, 1);
  }

  @media (max-width: 768px) {
    .neural-activity-container {
      left: 1rem;
      right: 1rem;
      bottom: 5rem; /* Avoid dock/tab bar overlay */
    }
    
    .neural-bar > div {
       width: 100%;
       justify-content: flex-start;
    }
  }
</style>
