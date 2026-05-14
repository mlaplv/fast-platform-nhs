<script lang="ts">
  import { fade, fly, scale } from 'svelte/transition';
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import Lock from "@lucide/svelte/icons/lock";
  import Mail from "@lucide/svelte/icons/mail";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Fingerprint from "@lucide/svelte/icons/fingerprint";
  import Phone from "@lucide/svelte/icons/phone";
  import Chrome from "@lucide/svelte/icons/chrome";
  import Facebook from "@lucide/svelte/icons/facebook";
  import MessageCircle from "@lucide/svelte/icons/message-circle";
  import Eye from "@lucide/svelte/icons/eye";
  import EyeOff from "@lucide/svelte/icons/eye-off";  import { permissionState } from "$lib/state/permissions.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { fallbackSha256 } from "$lib/utils/cryptoFallback";
  // Elite V2.2: Device fingerprinting hook
  const getFp = () => {
    if (typeof window === 'undefined') return '';
    return localStorage.getItem('xohi_device_fingerprint') || '';
  };

  import { goto } from "$app/navigation";
  import XohiLogo from "$lib/components/admin/XohiLogo.svelte";

  type AuthTab = "EMAIL" | "PHONE" | "SOCIAL" | "BIOMETRIC";
  
  let email = $state("");
  let password = $state("");
  let phone = $state("");
  let isLoading = $state(false);
  let error = $state("");
  let showPage = $state(false);
  let showPassword = $state(false);
  let lastTab = $state<AuthTab>("EMAIL");
  let rememberMe = $state(false);

  $effect(() => {
    showPage = true;
  });

  async function hashPassword(pw: string): Promise<string> {
    if (!crypto.subtle) {
      console.warn(
        "[SECURITY] WebCrypto unavailable. Using fallback SHA-256 for local dev.",
      );
      return fallbackSha256(pw);
    }

    const encoder = new TextEncoder();
    const data = encoder.encode(pw);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function handleLogin(e: SubmitEvent) {
    e.preventDefault();
    isLoading = true;
    error = "";
    
    // CNS V82.11: Pure Auth Purge before re-login attempt
    sessionStorage.removeItem("admin_token");

    try {
      const hashedPassword = await hashPassword(password);

      const {
        access_token,
        role,
        name,
        email: userEmail,
      } = await apiClient.post<{
        access_token: string;
        role: string;
        name: string;
        email: string;
      }>("/api/v1/auth/login", {
        identifier: email,
        password: hashedPassword,
        remember_me: rememberMe,
        fingerprint: getFp(),
      });

      if (!access_token) {
        throw new Error("Đăng nhập thất bại");
      }

      // SSOT: Populate global identity state via permissionState (module singleton)
      // Note: nanobot context is not yet initialized on /login page, write directly.
      permissionState.user = userEmail || email;
      permissionState.userName = name || "GHOST_OPERATOR";
      permissionState.roles = [role];

      // THIẾT QUÂN LUẬT: Phân tách thời lượng lưu trú
      if (rememberMe) {
        document.cookie = `admin_token=${access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Strict`;
        localStorage.setItem("admin_token", access_token);
        localStorage.setItem("admin_user_name", name);
        localStorage.setItem("admin_user_email", userEmail || email);
      } else {
        document.cookie = `admin_token=${access_token}; path=/; SameSite=Strict`;
        sessionStorage.setItem("admin_token", access_token);
      }

      permissionState.syncFromToken();

      if (!permissionState.roles.includes("SUPER_ADMIN") && role !== "ADMIN") {
        throw new Error("Bạn không có quyền truy cập vùng này");
      }
      
      // V70.2: Use soft navigation to preserve Audio Context and SSE connections
      sessionStorage.setItem("xohi_just_logged_in", "true");
      await goto("/");
    } catch (e: Error | unknown) {
      error = (e as Error).message || "Failed to login. Please check your credentials.";
    } finally {
      isLoading = false;
    }
  }

  function handleBiometric() {
    error =
      "Biometric hardware connection established. Verification pending...";
    setTimeout(() => {
      error =
        "Biometric simulation: Access Denied. Please use standard credentials.";
    }, 1500);
  }
</script>

<div
  class="min-h-screen bg-[#010101] flex items-center justify-center p-6 font-sans relative overflow-hidden text-white"
>
  <style>
    :global(body) {
      background-color: #010101;
    }
  </style>
  <!-- Cyberpunk grid background -->
  <div
    class="absolute inset-0 z-0 opacity-20 pointer-events-none bg-[linear-gradient(#1a1a1a_1px,transparent_1px),linear-gradient(90deg,#1a1a1a_1px,transparent_1px)] bg-[size:40px_40px]"
  ></div>

  <!-- Dynamic glow orbs -->
  <div class="absolute inset-0 z-0 overflow-hidden pointer-events-none">
    <div
      class="absolute top-[20%] left-[10%] w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] animate-pulse"
    ></div>
    <div
      class="absolute bottom-[20%] right-[10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] animate-pulse [animation-delay:2s]"
    ></div>
  </div>

  {#if showPage}
    <div
      class="w-full max-w-lg relative z-10"
      in:fly={{ y: 40, duration: 1000 }}
    >
      <!-- BRANDING HEADER -->
      <div class="text-center mb-10">
        <div class="relative inline-block mb-4">
          <XohiLogo size="xl" interactive={true} />
        </div>
        <h1
          class="text-4xl font-black mt-6 tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-white to-gray-500"
        >
          XOHI GATEWAY
        </h1>
        <div class="flex items-center justify-center gap-3 mt-2">
          <span class="h-[1px] w-8 bg-cyan-500/50"></span>
          <p
            class="text-[10px] text-cyan-400 font-mono tracking-[0.4em] uppercase"
          >
            Security Level 10
          </p>
          <span class="h-[1px] w-8 bg-cyan-500/50"></span>
        </div>
      </div>

      <!-- LOGIN CARD -->
      <div
        class="bg-[#0a0a0a] md:bg-black/40 md:backdrop-blur-3xl border border-white/5 rounded-[40px] p-2 shadow-[0_0_60px_-15px_rgba(0,0,0,0.8)]"
      >
        <!-- Tab Headers -->
        <div class="flex p-2 bg-white/5 rounded-[32px] mb-6">
          {#each ["EMAIL", "PHONE", "SOCIAL"] as tab}
            <button
              class="flex-1 py-3 rounded-[24px] text-[11px] font-bold tracking-widest transition-all duration-300 {lastTab ===
              tab
                ? 'bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30 shadow-[0_0_20px_rgba(var(--color-neon-cyan-raw),0.15)]'
                : 'text-gray-500 hover:text-white'}"
              onclick={() => (lastTab = tab)}
            >
              {tab}
            </button>
          {/each}
        </div>

        <div class="p-8 pt-2">
          {#if lastTab === "EMAIL"}
            <form onsubmit={handleLogin} class="space-y-6" in:fade>
              {#if error}
                <div
                  in:fly={{ y: -10 }}
                  class="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-400 text-xs text-center font-mono"
                >
                  [SYSTEM ERROR]: {error}
                </div>
              {/if}

              <div class="space-y-2">
                <label
                  for="email"
                  class="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1"
                  >Identity Protocol</label
                >
                <div class="relative group">
                  <div
                    class="absolute inset-0 bg-cyan-500/5 rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"
                  ></div>
                  <span
                    class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-cyan-400 transition-colors z-20"
                  >
                    <Mail size={20} />
                  </span>
                  <input
                    id="email"
                    bind:value={email}
                    type="text"
                    required
                    class="w-full bg-[#0a0a0a] border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm text-white focus:outline-none focus:border-cyan-500/30 transition-all font-mono placeholder:text-gray-800 relative z-10"
                    placeholder="EMAIL OR USERNAME..."
                  />
                </div>
              </div>

              <div class="space-y-2">
                <label
                  for="password"
                  class="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1"
                  >Access Cipher</label
                >
                <div class="relative group">
                  <div
                    class="absolute inset-0 bg-cyan-500/5 rounded-2xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"
                  ></div>
                  <span
                    class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-cyan-400 transition-colors z-20"
                  >
                    <Lock size={20} />
                  </span>
                  <input
                    id="password"
                    bind:value={password}
                    type={showPassword ? "text" : "password"}
                    required
                    class="w-full bg-[#0a0a0a] border border-white/5 rounded-2xl py-4 pl-12 pr-12 text-sm text-white focus:outline-none focus:border-cyan-500/30 transition-all font-mono placeholder:text-gray-800 relative z-10"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onclick={() => (showPassword = !showPassword)}
                    class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-600 hover:text-cyan-400 transition-colors z-20"
                  >
                    {#if showPassword}
                      <EyeOff size={18} />
                    {:else}
                      <Eye size={18} />
                    {/if}
                  </button>
                </div>
              </div>

              <div class="flex items-center gap-2 mt-2">
                <button
                  type="button"
                  class="w-4 h-4 rounded border border-white/20 flex items-center justify-center transition-colors {rememberMe
                    ? 'bg-cyan-500 border-cyan-500'
                    : 'bg-transparent'}"
                  onclick={() => {
                    rememberMe = !rememberMe;
                  }}
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
                  class="text-[10px] text-gray-400 font-bold uppercase tracking-widest cursor-pointer hover:text-white"
                  onclick={() => {
                    rememberMe = !rememberMe;
                  }}
                >
                  Duy trì cảnh giới (7 ngày)
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                class="w-full h-16 bg-gradient-to-r from-cyan-600 via-blue-600 to-blue-700 text-white font-black text-xs uppercase tracking-[0.3em] rounded-2xl hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-3 relative group overflow-hidden shadow-[0_0_30px_-5px_rgba(var(--color-neon-cyan-raw),0.5)] border border-white/10"
                style="background-color: rgb(0, 145, 178);"
              >
                <div
                  class="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
                ></div>
                {#if isLoading}
                  <div
                    class="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"
                  ></div>
                {:else}
                  <span>Establish Connect</span>
                  <ArrowRight
                    size={18}
                    class="group-hover:translate-x-1 transition-transform"
                  />
                {/if}
              </button>
            </form>
          {:else if lastTab === "PHONE"}
            <div class="space-y-6" in:fade>
              <div class="space-y-2">
                <label
                  for="phone"
                  class="text-[10px] font-bold text-gray-500 uppercase tracking-widest ml-1"
                  >Mobile Link</label
                >
                <div class="relative group">
                  <span
                    class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-600 group-focus-within:text-cyan-400 transition-colors z-20"
                  >
                    <Phone size={20} />
                  </span>
                  <input
                    id="phone"
                    bind:value={phone}
                    type="tel"
                    class="w-full bg-[#0a0a0a] border border-white/5 rounded-2xl py-4 pl-12 pr-4 text-sm text-white focus:outline-none focus:border-cyan-500/30 transition-all font-mono placeholder:text-gray-800 relative z-10"
                    placeholder="+84 ••• ••• •••"
                  />
                </div>
              </div>
              <button
                class="w-full h-16 bg-[#111] border border-white/10 text-gray-300 font-bold text-[10px] uppercase tracking-[0.2em] rounded-2xl hover:bg-white hover:text-black transition-all"
              >
                Request Access Code
              </button>
            </div>
          {:else if lastTab === "SOCIAL"}
            <div class="space-y-4" in:fade>
              <button
                class="w-full h-14 bg-white/5 border border-white/5 rounded-2xl flex items-center px-6 gap-4 hover:bg-white/10 transition-all group"
              >
                <Chrome size={20} class="text-red-500" />
                <span
                  class="text-[10px] font-bold tracking-widest uppercase flex-1 text-center"
                  >Continue with Google</span
                >
              </button>
              <button
                class="w-full h-14 bg-white/5 border border-white/5 rounded-2xl flex items-center px-6 gap-4 hover:bg-white/10 transition-all group"
              >
                <Facebook size={20} class="text-blue-500" />
                <span
                  class="text-[10px] font-bold tracking-widest uppercase flex-1 text-center"
                  >Link Facebook ID</span
                >
              </button>
              <button
                class="w-full h-14 bg-white/5 border border-white/5 rounded-2xl flex items-center px-6 gap-4 hover:bg-white/10 transition-all group"
              >
                <MessageCircle size={20} class="text-blue-400" />
                <span
                  class="text-[10px] font-bold tracking-widest uppercase flex-1 text-center"
                  >Authenticate via Zalo</span
                >
              </button>
            </div>
          {/if}

          <!-- Biometric Shortcut -->
          <div
            class="mt-10 pt-8 border-t border-white/5 flex flex-col items-center"
          >
            <p class="text-[9px] text-gray-600 uppercase tracking-[0.3em] mb-6">
              Neural Access Bypass
            </p>
            <button
              onclick={handleBiometric}
              class="group relative w-20 h-20 flex items-center justify-center"
            >
              <div
                class="absolute inset-0 bg-cyan-400/10 rounded-full animate-ping opacity-20"
              ></div>
              <div
                class="absolute inset-0 border border-cyan-400/20 rounded-full group-hover:border-cyan-400/50 transition-colors"
              ></div>
              <Fingerprint
                size={48}
                class="text-gray-400 group-hover:text-cyan-400 transition-all duration-500 transform group-hover:scale-110"
              />
            </button>
          </div>
        </div>
      </div>

      <div class="mt-8 text-center space-y-2">
        <p class="text-[9px] text-gray-700 uppercase tracking-[0.5em]">
          &copy; 2026 XOHI SYSTEMS AGENTIC ENTITY
        </p>
      </div>
    </div>
  {/if}
</div>

<style>
  @keyframes scan {
    0% {
      transform: translateY(0);
    }
    100% {
      transform: translateY(80px);
    }
  }

  :global(body) {
    background-color: #020202;
  }

  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus,
  input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 1000px #0a0a0a inset !important;
    -webkit-text-fill-color: white !important;
    transition: background-color 5000s ease-in-out 0s;
    caret-color: white;
  }
</style>
