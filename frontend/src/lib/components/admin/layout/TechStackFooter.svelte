<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();

  let currentTime = $state("");
  let interval: ReturnType<typeof setInterval>;

  // Get versions with fallbacks
  const versions =
    typeof __APP_VERSIONS__ !== "undefined"
      ? __APP_VERSIONS__
      : {
          svelte: "5.x",
          tailwind: "4.x",
          sqlalchemy: "2.x",
          alembic: "1.x",
          litestar: "2.x",
          pydantic_ai: "0.x",
          litellm: "1.x",
          python: "3.x",
          caddy: "2.x",
        };

  function updateTime() {
    const now = new Date();
    currentTime =
      now.toLocaleTimeString("en-GB", { hour12: false }) +
      " " +
      (now.getTimezoneOffset() <= 0 ? "+" : "-") +
      Math.abs(now.getTimezoneOffset() / 60) +
      "GMT";
  }

  onMount(() => {
    updateTime();
    interval = setInterval(updateTime, 1000);
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

<div
  class="absolute z-[200] pointer-events-none opacity-40 hover:opacity-100 transition-opacity mix-blend-screen text-right bottom-0.5 right-6 flex items-center gap-3"
  class:hidden={nanobot.isVuiActive && !nanobot.isTraining}
>
  <!-- Desktop Mode -->
  <div
    class="hidden md:flex items-center gap-2 text-[9px] font-mono text-[#00FFFF] uppercase tracking-widest whitespace-nowrap"
  >
    SV {versions.svelte} // TW {versions.tailwind} // SQLA {versions.sqlalchemy}
    // ALB {versions.alembic} // LITE {versions.litestar} // PAI {versions.pydantic_ai}
  </div>

  <!-- Mobile Mode: Ultra Compact -->
  <div
    class="flex md:hidden items-center gap-1.5 text-[7px] font-mono text-[#00FFFF] uppercase tracking-wider whitespace-nowrap mr-2"
  >
    <span>SV {versions.svelte.split(".").slice(0, 2).join(".")}</span>
    <span class="text-[#00FFFF]/20">/</span>
    <span>LS {versions.litestar.split(".").slice(0, 2).join(".")}</span>
  </div>

  <div class="h-3 w-[1px] bg-white/10 hidden md:block"></div>

  <div
    class="text-[7px] md:text-[9px] font-mono text-gray-500 uppercase tracking-widest whitespace-nowrap"
  >
    <span class="hidden md:inline text-gray-600">SYS_TIME </span>{currentTime}
  </div>
</div>
