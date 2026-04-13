<script lang="ts">
    import type { PageData } from './$types';
    import { fade } from 'svelte/transition';
    import type { Component } from 'svelte';

    /**
     * ELITE V2.2 - MISSION CONTROL HUB
     * Logic: Zero-latency component selection based on verified tenant data.
     * Rule: Static Typing (No 'any'), Rune-based reactivity.
     */
    let { data }: { data: PageData } = $props();

    // ELITE V2.2: Strict Typing for Dynamic Imports
    interface DynamicModuleProps {
        data: PageData;
        isMobile: boolean;
    }
    interface DynamicModule { default: Component<DynamicModuleProps> };

    const loadAdmin = (): Promise<DynamicModule> => import("$lib/components/admin/layout/AdminDashboard.svelte");
    const loadStorefront = (): Promise<DynamicModule> => import("$lib/components/storefront/StorefrontHome.svelte");
</script>

<svelte:head>
    <title>{data.tenant === 'admin' ? 'Xohi Darkboard' : 'SmartShop Storefront'}</title>
</svelte:head>

<div class="page-container h-dvh overflow-x-hidden overflow-y-auto bg-[#010101]">
    {#if data.tenant === 'admin'}
        {#await loadAdmin()}
            <!-- Liquid Loading State (Viral 2026) -->
            <div class="fixed inset-0 flex items-center justify-center bg-[#010101] z-[var(--z-modal-overlay)]">
                <div class="relative flex flex-col items-center gap-4">
                    <div class="w-12 h-12 border-2 border-[#00FFFF]/20 border-t-[#00FFFF] rounded-full animate-spin shadow-[0_0_15px_rgba(0,255,255,0.1)]"></div>
                    <div class="text-[9px] font-mono text-[#00FFFF]/50 tracking-[0.4em] uppercase animate-pulse">Initializing Neural Link...</div>
                </div>
            </div>
        {:then mod}
            <div in:fade={{ duration: 300 }}>
                <mod.default
                    data={data}
                    isMobile={data.isMobile}
                />
            </div>
        {:catch err}
             <div class="fixed inset-0 flex items-center justify-center text-red-500 font-mono text-xs p-4 text-center">
                [SYSTEM FAULT] AI_CORE_LOAD_FAILED<br/>{err.message}
             </div>
        {/await}
    {:else}
        {#await loadStorefront()}
            <!-- Luxury Storefront Loading State (Elite V2.2) -->
            <div class="fixed inset-0 flex items-center justify-center bg-[#020202] z-[var(--z-modal-overlay)]">
                <div class="relative flex flex-col items-center gap-6">
                    <div class="w-16 h-16 border-[1px] border-[#C5A25D]/10 border-t-[#C5A25D] rounded-full animate-spin duration-[2s]"></div>
                    <div class="absolute inset-0 flex items-center justify-center">
                         <div class="w-8 h-8 border-[1px] border-[#C5A25D]/5 border-b-[#C5A25D] rounded-full animate-spin-reverse duration-[3s]"></div>
                    </div>
                    <div class="text-[10px] font-serif italic text-[#C5A25D]/60 tracking-[0.5em] uppercase animate-pulse">Micsmo Elite Experience...</div>
                </div>
            </div>
        {:then mod}
             <div in:fade={{ duration: 300 }} class="flex-1 flex flex-col">
                <mod.default
                    data={data}
                    isMobile={data.isMobile}
                />
            </div>
        {:catch err}
             <div class="fixed inset-0 flex items-center justify-center text-red-500 font-mono text-xs p-4 text-center">
                [SYSTEM FAULT] STOREFRONT_LOAD_FAILED<br/>{err.message}
             </div>
        {/await}
    {/if}
</div>

<style>
    .page-container {
        display: flex;
        flex-direction: column;
    }
    
    @keyframes spin-reverse {
        from { transform: rotate(0deg); }
        to { transform: rotate(-360deg); }
    }
    .animate-spin-reverse {
        animation: spin-reverse 3s linear infinite;
    }

    /* Ensure the inner transition container grows to fill the page container */
    .page-container > div {
        flex: 1;
        display: flex;
        flex-direction: column;
    }
</style>
