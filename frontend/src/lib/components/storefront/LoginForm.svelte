<script lang="ts">
  import { fade } from "svelte/transition";
  import LucideLock from "@lucide/svelte/icons/lock";
  import LucideMail from "@lucide/svelte/icons/mail";
  import LucideArrowRight from "@lucide/svelte/icons/arrow-right";
  import LucideEye from "@lucide/svelte/icons/eye";
  import LucideEyeOff from "@lucide/svelte/icons/eye-off";
  import LucideFingerprint from "@lucide/svelte/icons/fingerprint";

  let { onLogin, isLoading, error } = $props<{
    onLogin: (email: string, password: string, rememberMe: boolean) => void;
    isLoading: boolean;
    error: string;
  }>();

  let email = $state("");
  let password = $state("");
  let showPassword = $state(false);
  let rememberMe = $state(false);

  function handleSubmit(e: Event) {
    e.preventDefault();
    onLogin(email, password, rememberMe);
  }
</script>

<form onsubmit={handleSubmit} class="space-y-5" in:fade>
  {#if error}
    <div
      in:fade
      class="p-3 bg-red-50 border border-red-100 rounded-xl text-red-600 text-xs text-center font-medium"
    >
      {error}
    </div>
  {/if}

  <div class="space-y-1.5">
    <label
      for="email"
      class="text-[11px] font-bold text-gray-400 tracking-widest ml-1"
      >Tài khoản Email</label
    >
    <div class="relative group">
      <span
        class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300 group-focus-within:text-black transition-colors"
      >
        <LucideMail size={18} />
      </span>
      <input
        bind:value={email}
        type="email"
        id="email"
        required
        class="w-full bg-gray-50 border border-transparent rounded-2xl py-3.5 pl-12 pr-4 text-sm focus:bg-white focus:border-black/5 focus:ring-4 focus:ring-black/5 transition-all outline-none"
        placeholder="your@email.com"
      />
    </div>
  </div>

  <div class="space-y-1.5">
    <label
      for="password"
      class="text-[11px] font-bold text-gray-400 tracking-widest ml-1"
      >Mật khẩu bảo mật</label
    >
    <div class="relative group">
      <span
        class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300 group-focus-within:text-black transition-colors"
      >
        <LucideLock size={18} />
      </span>
      <input
        bind:value={password}
        type={showPassword ? "text" : "password"}
        id="password"
        required
        class="w-full bg-gray-50 border border-transparent rounded-2xl py-3.5 pl-12 pr-12 text-sm focus:bg-white focus:border-black/5 focus:ring-4 focus:ring-black/5 transition-all outline-none"
        placeholder="••••••••"
      />
      <button
        type="button"
        onclick={() => (showPassword = !showPassword)}
        class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-300 hover:text-black transition-colors"
      >
        {#if showPassword}
          <LucideEyeOff size={18} />
        {:else}
          <LucideEye size={18} />
        {/if}
      </button>
    </div>
  </div>

  <div class="flex items-center gap-2 mt-2">
    <button
      type="button"
      class="w-4 h-4 rounded border border-gray-300 flex items-center justify-center transition-colors {rememberMe
        ? 'bg-black border-black'
        : 'bg-transparent'}"
      onclick={() => (rememberMe = !rememberMe)}
    >
      {#if rememberMe}
        <svg
          class="w-3 h-3 text-white"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="3"
          ><path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M5 13l4 4L19 7"
          /></svg
        >
      {/if}
    </button>
    <button
      type="button"
      class="text-[11px] text-gray-500 font-bold tracking-widest cursor-pointer hover:text-black"
      onclick={() => (rememberMe = !rememberMe)}
    >
      Lưu phiên mua sắm (7 ngày)
    </button>
  </div>

  <div class="flex items-center gap-3 mt-4">
    <button
      type="submit"
      disabled={isLoading}
      class="flex-1 bg-black text-white font-bold py-4 rounded-2xl hover:bg-gray-900 active:scale-[0.98] transition-all flex items-center justify-center gap-2 shadow-xl shadow-black/10"
    >
      {#if isLoading}
        <div
          class="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"
        ></div>
      {:else}
        <span>Tiếp tục</span>
        <LucideArrowRight size={18} />
      {/if}
    </button>

    <button
      type="button"
      class="w-14 h-14 border border-gray-100 rounded-2xl flex items-center justify-center text-gray-400 hover:text-black hover:border-black/20 hover:bg-gray-50 transition-all active:scale-[0.95] shrink-0 group"
      title="Mở khóa bằng vân tay"
    >
      <LucideFingerprint size={32} class="transition-transform group-hover:scale-110" />
    </button>
  </div>
</form>
