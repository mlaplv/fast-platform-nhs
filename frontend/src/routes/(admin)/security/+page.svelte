<script lang="ts">
  import { onMount } from "svelte";
  import SecuritySOC from "$lib/components/admin/management/SecuritySOC.svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  onMount(() => {
    nanobot.addLog("Accessing Security Operations Center", "SYS", "info");
  });
</script>

<svelte:head>
  <title>TRINITY SOC - Trung tâm Giám sát An ninh</title>
</svelte:head>

<div class="h-full w-full bg-[#020408] overflow-hidden">
  <SecuritySOC />
</div>

<style>
  div {
    display: flex;
    flex-direction: column;
  }
</style>
