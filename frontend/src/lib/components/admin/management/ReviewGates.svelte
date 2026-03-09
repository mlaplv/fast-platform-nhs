<script lang="ts">
    import { onMount } from 'svelte';
    import StepModal from './StepModal.svelte';

    let { campaign = $bindable() } = $props();

    const STEPS = [
        { id: 1, name: 'Vision', icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0z M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z' },
        { id: 2, name: 'Hunter', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z' },
        { id: 3, name: 'Outline', icon: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
        { id: 4, name: 'Pen', icon: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z' },
        { id: 5, name: 'Audit', icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z' },
        { id: 6, name: 'Format', icon: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1 1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z' }
    ];

    let showModal = $state(false);
    let selectedStep = $state(1);

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
</script>

<div class="review-gates flex items-center gap-4 p-4 bg-gray-900/50 rounded-xl border border-white/10">
    {#each STEPS as step}
        {@const status = getStepStatus(step.id)}
        <button 
            class="step-node flex flex-col items-center gap-2 group relative"
            onclick={() => openReview(step.id)}
            disabled={status === 'pending'}
        >
            <div class="icon-circle w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
                {status === 'completed' ? 'bg-green-500/20 text-green-400 border border-green-500/30' : ''}
                {status === 'waiting' ? 'bg-yellow-500/30 text-yellow-500 border border-yellow-500/50 shadow-[0_0_15px_rgba(234,179,8,0.2)]' : ''}
                {status === 'processing' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50' : ''}
                {status === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/50' : ''}
                {status === 'pending' ? 'bg-gray-800/50 text-gray-600 border border-white/5 opacity-40' : ''}"
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d={step.icon} />
                </svg>
            </div>
            <span class="text-[10px] uppercase tracking-wider font-bold {status !== 'pending' ? 'text-white' : 'text-gray-600'}">
                {step.name}
            </span>

            {#if status === 'waiting'}
                <div class="absolute -top-1 -right-1 w-3 h-3 bg-yellow-500 rounded-full border-2 border-gray-900"></div>
            {/if}
        </button>

        {#if step.id < 6}
            <div class="h-px w-8 bg-white/10 {campaign.current_step > step.id ? 'bg-green-500/30' : ''}"></div>
        {/if}
    {/each}
</div>

{#if showModal}
    <StepModal 
        bind:show={showModal} 
        {campaign} 
        stepId={selectedStep} 
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
</style>
