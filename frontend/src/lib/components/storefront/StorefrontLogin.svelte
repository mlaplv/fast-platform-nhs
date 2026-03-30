<script lang="ts">
  import { fade, fly } from "svelte/transition";
  import LucideShieldCheck from "lucide-svelte/icons/shield-check";
  import LucideLock from "lucide-svelte/icons/lock";
  import LucideMail from "lucide-svelte/icons/mail";
  import LucideArrowRight from "lucide-svelte/icons/arrow-right";
  import LucidePhone from "lucide-svelte/icons/phone";
  import LucideGithub from "lucide-svelte/icons/github";
  import LucideScanFace from "lucide-svelte/icons/scan-face";
  import LucideEye from "lucide-svelte/icons/eye";
  import LucideEyeOff from "lucide-svelte/icons/eye-off";
  import { apiClient } from "$lib/utils/apiClient";
  import { fallbackSha256 } from "$lib/utils/cryptoFallback";

  import LoginForm from "./LoginForm.svelte";

  let isLoading = $state(false);
  let error = $state("");
  let showPage = $state(false);
  let tab = $state("EMAIL"); // EMAIL | PHONE | SOCIAL
  let phone = $state("");

  $effect(() => {
    showPage = true;
  });

  async function hashPassword(pw: string): Promise<string> {
    if (!crypto.subtle) {
      console.warn("Môi trường không bảo mật. Sử dụng SHA-256 dự phòng.");
      return fallbackSha256(pw);
    }

    const encoder = new TextEncoder();
    const data = encoder.encode(pw);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function handleLogin(
    email: string,
    password: string,
    rememberMe: boolean,
  ) {
    isLoading = true;
    error = "";

    try {
      const hashedPassword = await hashPassword(password);

      const { access_token } = await apiClient.post<{ access_token: string }>(
        "/api/v1/auth/login",
        {
          identifier: email,
          password: hashedPassword,
        },
      );

      if (!access_token) {
        throw new Error("Đăng nhập thất bại");
      }

      // THIẾT QUÂN LUẬT: Phân tách thời lượng phiên bản Storefront
      if (rememberMe) {
        document.cookie = `user_token=${access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Strict`;
        localStorage.setItem("user_token", access_token);
      } else {
        document.cookie = `user_token=${access_token}; path=/; SameSite=Strict`;
        sessionStorage.setItem("user_token", access_token);
      }

      sessionStorage.setItem("xohi_just_logged_in", "true");
      window.location.href = "/";
    } catch (e: unknown) {
      const err = e as Error;
      error = err.message || "Login failed. Please verify your credentials.";
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>Đăng nhập | SmartShop Premium</title>
</svelte:head>

<div
  class="min-h-screen bg-[#F5F5F7] flex flex-col items-center justify-center p-6 font-sans"
>
  {#if showPage}
    <div class="w-full max-w-md" in:fly={{ y: 20, duration: 800 }}>
      <div class="text-center mb-12">
        <div
          class="inline-flex items-center justify-center w-14 h-14 bg-white rounded-2xl shadow-sm mb-6"
        >
          <div
            class="w-8 h-8 bg-black rounded-lg flex items-center justify-center"
          >
            <span class="text-white font-black text-xl italic">S</span>
          </div>
        </div>
        <h1 class="text-3xl font-bold text-black tracking-tight mb-2">
          Trải nghiệm mua sắm mới
        </h1>
        <p class="text-gray-500 text-sm font-medium">
          Đăng nhập để tận hưởng đặc quyền riêng của bạn
        </p>
      </div>

      <div
        class="bg-white rounded-[32px] p-10 shadow-[0_20px_50px_rgba(0,0,0,0.05)] border border-gray-100"
      >
        <!-- TABS -->
        <div class="flex border-b border-gray-100 mb-8">
          <button
            class="flex-1 pb-4 text-xs font-bold tracking-widest uppercase transition-all {tab ===
            'EMAIL'
              ? 'text-black border-b-2 border-black'
              : 'text-gray-400 border-b-2 border-transparent hover:text-gray-600'}"
            onclick={() => (tab = "EMAIL")}
          >
            Email
          </button>
          <button
            class="flex-1 pb-4 text-xs font-bold tracking-widest uppercase transition-all {tab ===
            'PHONE'
              ? 'text-black border-b-2 border-black'
              : 'text-gray-400 border-b-2 border-transparent hover:text-gray-600'}"
            onclick={() => (tab = "PHONE")}
          >
            SĐT / OTP
          </button>
          <button
            class="flex-1 pb-4 text-xs font-bold tracking-widest uppercase transition-all {tab ===
            'SOCIAL'
              ? 'text-black border-b-2 border-black'
              : 'text-gray-400 border-b-2 border-transparent hover:text-gray-600'}"
            onclick={() => (tab = "SOCIAL")}
          >
            Mạng xã hội
          </button>
        </div>

        {#if tab === "EMAIL"}
          <LoginForm onLogin={handleLogin} {isLoading} {error} />
        {:else if tab === "PHONE"}
          <div class="space-y-5" in:fade>
            <div class="space-y-1.5">
              <label
                for="phone"
                class="text-[11px] font-bold text-gray-400 uppercase tracking-widest ml-1"
                >Số điện thoại</label
              >
              <div class="relative group">
                <span
                  class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-300 group-focus-within:text-black transition-colors"
                >
                  <LucidePhone size={18} />
                </span>
                <input
                  id="phone"
                  bind:value={phone}
                  type="tel"
                  class="w-full bg-gray-50 border border-transparent rounded-2xl py-3.5 pl-12 pr-4 text-sm focus:bg-white focus:border-black/5 focus:ring-4 focus:ring-black/5 transition-all outline-none"
                  placeholder="+84 ••• ••• •••"
                />
              </div>
            </div>
            <button
              class="w-full bg-black text-white font-bold py-4 rounded-2xl hover:bg-gray-900 transition-all flex items-center justify-center gap-2"
            >
              Gửi mã OTP
            </button>
          </div>
        {:else if tab === "SOCIAL"}
          <div class="space-y-3" in:fade>
            <button
              class="w-full bg-[#f2f2f5] hover:bg-[#eaeaee] text-black font-bold py-3.5 rounded-2xl flex items-center justify-center gap-3 transition-all"
            >
              <svg
                class="w-5 h-5"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              <span class="text-sm">Đăng nhập với Google</span>
            </button>
            <button
              class="w-full bg-[#1877F2] hover:bg-[#166fe5] text-white font-bold py-3.5 rounded-2xl flex items-center justify-center gap-3 transition-all"
            >
              <span class="text-sm">Tiếp tục qua Facebook</span>
            </button>
            <button
              class="w-full bg-[#0068FF] hover:bg-[#005cdc] text-white font-bold py-3.5 rounded-2xl flex items-center justify-center gap-3 transition-all"
            >
              <span class="text-sm">Xác thực bằng Zalo</span>
            </button>
            <div class="py-2 flex items-center gap-4 text-gray-300">
              <div class="h-[1px] flex-1 bg-gray-100"></div>
              <span class="text-[10px] uppercase font-bold tracking-widest"
                >Hoặc nhanh hơn</span
              >
              <div class="h-[1px] flex-1 bg-gray-100"></div>
            </div>
            <button
              class="w-full bg-white border border-gray-200 hover:border-black text-black font-bold py-3.5 rounded-2xl flex items-center justify-center gap-3 transition-all"
            >
              <LucideScanFace size={20} />
              <span class="text-sm">Mở khóa vân tay</span>
            </button>
          </div>
        {/if}
      </div>

      <div class="mt-10 text-center">
        <p class="text-sm text-gray-500">
          Chưa có tài khoản? <a
            href="/register"
            class="text-black font-black hover:underline underline-offset-4"
            >Đăng ký thành viên mới</a
          >
        </p>
      </div>

      <div class="mt-20 flex justify-center gap-8">
        <p class="text-[10px] text-gray-400 uppercase tracking-[0.2em]">
          &copy; 2026 SmartShop Premium
        </p>
        <a
          href="/support"
          class="text-[10px] text-gray-400 uppercase tracking-[0.2em] hover:text-black"
          >Hỗ trợ</a
        >
        <a
          href="/privacy"
          class="text-[10px] text-gray-400 uppercase tracking-[0.2em] hover:text-black"
          >Bảo mật</a
        >
      </div>
    </div>
  {/if}
</div>

<style>
  :global(body) {
    background-color: #f5f5f7;
    -webkit-font-smoothing: antialiased;
  }

  input:-webkit-autofill,
  input:-webkit-autofill:hover,
  input:-webkit-autofill:focus,
  input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 1000px #f9f9fb inset !important;
    -webkit-text-fill-color: black !important;
    transition: background-color 5000s ease-in-out 0s;
    caret-color: black;
  }
</style>
