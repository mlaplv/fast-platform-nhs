<script lang="ts">
  import { onMount } from "svelte";
  import { nanobot } from "$lib/state/nanobot.svelte";
  import SupportKnowledgeManagement from "$lib/components/admin/management/SupportKnowledgeManagement.svelte";
  import SupportInbox from "$lib/components/admin/management/SupportInbox.svelte";
  import Database from "lucide-svelte/icons/database";
  import MessageSquare from "lucide-svelte/icons/message-square";

  let activeTab = $state("inbox"); // Default to Inbox to see what Helen is doing

  onMount(() => {
    nanobot.addLog("Accessing Support Center", "SYS", "info");
  });
</script>

<svelte:head>
  <title>CMS - Trung tâm Hỗ trợ Helen AI</title>
</svelte:head>

<div class="h-full w-full flex flex-col p-6 gap-6">
  <!-- Tab Navigation -->
  <div class="flex items-center gap-4 bg-obsidian-900/40 p-1.5 rounded-xl border border-white/5 w-fit self-center">
    <button 
      onclick={() => activeTab = "inbox"}
      class="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all {activeTab === 'inbox' ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20' : 'text-white/40 hover:text-white/70'}"
    >
      <MessageSquare class="w-4 h-4" />
      Hộp thư Helen AI
    </button>
    <button 
      onclick={() => activeTab = "knowledge"}
      class="flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-bold transition-all {activeTab === 'knowledge' ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20' : 'text-white/40 hover:text-white/70'}"
    >
      <Database class="w-4 h-4" />
      Kho tri thức (RAG)
    </button>
  </div>

  <div class="flex-1 overflow-hidden">
    {#if activeTab === "inbox"}
      <div class="h-full">
        <SupportInbox />
      </div>
    {:else}
      <div class="h-full">
        <SupportKnowledgeManagement />
      </div>
    {/if}
  </div>
</div>
