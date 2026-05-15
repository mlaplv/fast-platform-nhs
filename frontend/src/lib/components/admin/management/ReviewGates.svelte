<script lang="ts">
    import { onMount, type Snippet } from 'svelte';
    import StepModal from './StepModal.svelte';
    import MediaVaultModal from '$lib/components/media/MediaVaultModal.svelte';

    let { campaign = $bindable() } = $props();

    onMount(() => {
        if (campaign === undefined) campaign = {};
    });

    const STEPS = [
        { id: 1, name: 'Vision', icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z' },
        { id: 2, name: 'Hunter', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
        { id: 3, name: 'Outline', icon: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
        { id: 4, name: 'Pen', icon: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z' },
        { id: 5, name: 'Audit', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
        { id: 6, name: 'Format', icon: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1 1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z' }
    ];

    let showModal = $state(false);
    let showMediaModal = $state(false);
    let selectedStep = $state(1);
    
    // Media Intelligence states
    let assets = $state<string[]>([]);
    let reserve_assets = $state<string[]>([]);
    let selectedAvatarUrl = $state<string | null>(null);
    let selectedAssetIndex = $state(0);

    function getStepStatus(stepId: number) {
        if (campaign.current_step > stepId) return 'completed';
        if (campaign.current_step === stepId) {
            if (campaign.status === 'WAITING_FOR_REVIEW') return 'waiting';
            if (campaign.status === 'PROCESSING') return 'processing';
            if (campaign.status === 'ERROR') return 'error';
        }
        return 'pending';
    }

    function openReview(stepId: number) {
        selectedStep = stepId;
        showModal = true;
    }

    // Status mapping for high-trust HUD aesthetics
    const statusConfig = {
        completed: {
            bg: 'bg-emerald-500/10',
            text: 'text-emerald-400',
            border: 'border-emerald-500/30',
            aura: 'shadow-[0_0_15px_rgba(16,185,129,0.15)]',
            icon: 'M5 13l4 4L19 7'
        },
        waiting: {
            bg: 'bg-amber-500/20',
            text: 'text-amber-400',
            border: 'border-amber-500/50',
            aura: 'shadow-[0_0_20px_rgba(245,158,11,0.25)]',
            pulse: 'animate-pulse'
        },
        processing: {
            bg: 'bg-cyan-500/10',
            text: 'text-cyan-400',
            border: 'border-cyan-500/40',
            aura: 'shadow-[0_0_15px_rgba(6,182,212,0.2)]',
            spin: 'animate-spin-slow'
        },
        error: {
            bg: 'bg-rose-500/20',
            text: 'text-rose-400',
            border: 'border-rose-500/50',
            aura: 'shadow-[0_0_20px_rgba(244,63,94,0.3)]',
            glitch: 'animate-hud-flicker'
        },
        pending: {
            bg: 'bg-white/5',
            text: 'text-white/20',
            border: 'border-white/5',
            aura: ''
        }
    };
</script>

<div class="review-gates-container relative group">
    <!-- HUD Metadata Labels -->
    <div class="absolute -top-6 left-2 flex items-center gap-4 px-2 py-0.5">
        <div class="flex items-center gap-2">
            <span class="w-1 h-1 bg-cyan-500 animate-pulse"></span>
            <span class="text-[9px] font-black tracking-[0.2em] text-cyan-500/60 font-mono">
                System // Review_Gates_V2.2
            </span>
        </div>
        <div class="h-px w-8 bg-white/10"></div>
        <div class="text-[9px] font-bold tracking-[0.1em] text-white/30 font-mono italic">
            Secure_Channel_Active [AES-256]
        </div>
    </div>

    <!-- Main Liquid Glass UI -->
    <div class="review-gates relative flex items-center gap-2 p-3 bg-[#0a0a0b]/80 backdrop-blur-3xl rounded-[2rem] border border-white/10 shadow-2xl overflow-hidden transition-all duration-700 hover:border-white/20">
        <!-- Inner Ambient Glow -->
        <div class="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
        
        {#each STEPS as step, i}
            {@const status = getStepStatus(step.id)}
            {@const config = statusConfig[status]}
            
            <button 
                class="step-node flex flex-col items-center gap-1.5 px-4 py-2 rounded-[1.5rem] transition-all duration-500 relative z-10
                    {status !== 'pending' ? 'hover:bg-white/5 cursor-pointer' : 'cursor-not-allowed'}"
                onclick={() => status !== 'pending' && openReview(step.id)}
                disabled={status === 'pending'}
            >
                <div class="relative">
                    <!-- Status Ring (for processing) -->
                    {#if status === 'processing'}
                        <div class="absolute -inset-1 rounded-full border border-cyan-500/30 border-t-cyan-400 animate-spin"></div>
                    {/if}

                    <div class="icon-circle w-11 h-11 rounded-full flex items-center justify-center transition-all duration-500
                        {config.bg} {config.text} border {config.border} {config.aura} 
                        {status === 'waiting' ? config.pulse : ''}
                        {status === 'error' ? config.glitch : ''}"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 transition-transform duration-500 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d={status === 'completed' ? config.icon : step.icon} />
                        </svg>
                    </div>

                    <!-- Waiting Indicator (Ping) -->
                    {#if status === 'waiting'}
                        <div class="absolute -top-1 -right-1 flex">
                            <div class="absolute inset-0 bg-amber-400 rounded-full animate-ping opacity-75"></div>
                            <div class="relative w-3 h-3 bg-amber-500 rounded-full border-2 border-[#0a0a0b]"></div>
                        </div>
                    {/if}
                </div>

                <span class="text-[9px] tracking-[0.15em] font-black transition-colors duration-500
                    {status !== 'pending' ? 'text-white/80' : 'text-white/10'}">
                    {step.name}
                </span>

                <!-- Tooltip Logic could go here -->
            </button>

            <!-- Energy Conduit (Connector) -->
            {#if i < STEPS.length - 1}
                <div class="relative flex-1 min-w-[20px] h-[2px]">
                    <div class="absolute inset-0 bg-white/5 rounded-full overflow-hidden">
                        {#if campaign.current_step > step.id}
                            <div class="h-full bg-gradient-to-r from-emerald-500/50 to-emerald-400 glow-conduit"></div>
                            <!-- Moving Pulse -->
                            <div class="absolute top-0 left-0 h-full w-1/2 bg-white/20 animate-data-stream"></div>
                        {:else if campaign.current_step === step.id && campaign.status === 'PROCESSING'}
                            <div class="h-full bg-cyan-500/20"></div>
                            <div class="absolute top-0 left-0 h-full w-4 bg-cyan-400 blur-[2px] animate-data-stream-slow"></div>
                        {/if}
                    </div>
                </div>
            {/if}
        {/each}

        <!-- Tactical Divider -->
        <div class="h-8 w-px bg-white/10 mx-3 self-center"></div>

        <!-- Media Intelligence Core -->
        <button
            class="media-core-btn flex flex-col items-center gap-1.5 px-5 py-2 rounded-[1.5rem] bg-blue-500/5 hover:bg-blue-500/10 border border-blue-500/20 hover:border-blue-500/40 transition-all duration-500 group/media"
            onclick={() => showMediaModal = true}
        >
            <div class="w-11 h-11 rounded-full flex items-center justify-center bg-blue-500/20 text-blue-400 border border-blue-500/30 group-hover/media:shadow-[0_0_20px_rgba(59,130,246,0.3)] transition-all">
                <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 transition-transform duration-500 group-hover/media:rotate-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
            </div>
            <span class="text-[9px] tracking-[0.15em] font-black text-blue-400/60 group-hover/media:text-blue-400">Library</span>
        </button>
    </div>
</div>

{#if showModal}
    <StepModal 
        bind:show={showModal} 
        {campaign} 
        stepId={selectedStep} 
    />
{/if}

{#if showMediaModal}
    <MediaVaultModal
        isOpen={showMediaModal}
        bind:assets
        bind:reserve_assets
        bind:selectedAvatarUrl
        bind:selectedAssetIndex
        onClose={() => showMediaModal = false}
    />
{/if}

<style>
    .animate-spin-slow {
        animation: spin 3s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }

    .glow-conduit {
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
    }

    .animate-data-stream {
        animation: data-stream 1.5s linear infinite;
    }

    .animate-data-stream-slow {
        animation: data-stream 3s linear infinite;
    }

    @keyframes data-stream {
        0% { transform: translateX(-100%); opacity: 0; }
        50% { opacity: 1; }
        100% { transform: translateX(200%); opacity: 0; }
    }

    @keyframes hud-flicker {
        0%, 100% { opacity: 1; filter: brightness(1); }
        50% { opacity: 0.8; filter: brightness(1.2); }
        52% { opacity: 1; filter: brightness(1.5); }
    }
</style>

