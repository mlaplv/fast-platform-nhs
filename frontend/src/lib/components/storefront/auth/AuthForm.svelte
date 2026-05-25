<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import X from "@lucide/svelte/icons/x";
  import Mail from "@lucide/svelte/icons/mail";
  import ShieldCheck from "@lucide/svelte/icons/shield-check";
  import ArrowRight from "@lucide/svelte/icons/arrow-right";
  import Loader2 from "@lucide/svelte/icons/loader-2";
  import KeyRound from "@lucide/svelte/icons/key-round";
  import UserPlus from "@lucide/svelte/icons/user-plus";
  import Lock from "@lucide/svelte/icons/lock";
  import Eye from "@lucide/svelte/icons/eye";
  import EyeOff from "@lucide/svelte/icons/eye-off";
  import ChevronRight from "@lucide/svelte/icons/chevron-right";
  import { fallbackSha256 } from '$lib/utils/cryptoFallback';
  import { apiClient } from '$lib/utils/apiClient';
  import { fade, fly, scale, slide } from 'svelte/transition';

  interface Props {
    onClose?: () => void;
    rounded?: boolean;
  }

  let { onClose, rounded = true }: Props = $props();
  const r = $derived(rounded ? 'rounded-2xl' : 'rounded-none');

  const ui = getClientUi();
  let step = $state<'input' | 'otp'>('input');
  let identifier = $state('');
  let fullName = $state('');
  let code = $state(['', '', '', '', '', '']);
  let otpToken = $state('');
  let isLoading = $state(false);
  let error = $state<string | null>(null);
  let authMethod = $state<'otp' | 'password'>('otp');
  let password = $state('');
  let showPassword = $state(false);

  let fullCode = $derived(code.join(''));
  let mode = $derived(ui.authModal.mode);

  let requestId = $state<string | null>(null);
  let liveLogs = $state<string[]>([]);
  let pulseSource = $state<EventSource | null>(null);

  async function startPulse(rid: string) {
    if (pulseSource) pulseSource.close();
    liveLogs = ["Đã khởi tạo yêu cầu..."];

    pulseSource = new EventSource(`/api/v1/client/support/pulse/${rid}`);

    pulseSource.addEventListener("OTP_UPDATE", (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      if (data.message) {
        liveLogs = [...liveLogs, data.message];
      }
      if (data.status === 'DONE') {
        setTimeout(() => {
          step = 'otp';
          isLoading = false;
          pulseSource?.close();
        }, 1200);
      } else if (data.status === 'FAILED') {
        console.warn("[Pulse] Task failed:", data.message);
        error = data.message;
        pulseSource?.close();
        isLoading = false;
      }
    });

    pulseSource.onerror = () => {
      pulseSource?.close();
    };
  }

  async function hashPassword(pw: string): Promise<string> {
    if (!crypto.subtle) return fallbackSha256(pw);
    const encoder = new TextEncoder();
    const data = encoder.encode(pw);
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  async function handlePasswordLogin() {
    if (!identifier || !password) return;
    isLoading = true;
    error = null;
    try {
      const hashedPassword = await hashPassword(password);
      const normalizedIdentifier = identifier.trim().toLowerCase();

      const data = await apiClient.post<import('$lib/types').LoginResponse>('/api/v1/auth/login', {
        identifier: normalizedIdentifier,
        password: hashedPassword,
        remember_me: false
      });

      authStore.setSession(data.access_token, {
        id: data.id,
        email: data.email,
        name: data.name,
        role: data.role,
        has_password: data.has_password
      });

      onClose?.();
    } catch (e) {
      error = (e as Error).message || 'Tên đăng nhập hoặc mật khẩu không đúng';
    } finally {
      isLoading = false;
    }
  }

  async function handleRequestOTP() {
    if (!identifier) return;
    if (mode === 'register' && !fullName) {
      error = "Vui lòng nhập họ và tên để đăng ký.";
      return;
    }

    isLoading = true;
    error = null;
    liveLogs = [];
    code = ['', '', '', '', '', ''];

    try {
      const res = await fetch('/api/v1/auth/otp/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: identifier })
      });
      const data = await res.json();
      if (res.ok) {
        otpToken = data.otp_token;
        requestId = data.request_id;
        if (requestId) {
          await startPulse(requestId);
        } else {
          step = 'otp';
        }
      } else {
        error = data.detail || 'Lỗi gửi mã OTP';
        isLoading = false;
      }
    } catch (e) {
      error = 'Không thể kết nối máy chủ';
      isLoading = false;
    }
  }

  async function handleVerifyOTP() {
    if (fullCode.length < 6) return;
    isLoading = true;
    error = null;
    try {
      const res = await fetch('/api/v1/auth/otp/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: identifier,
          code: fullCode,
          otp_token: otpToken,
          name: mode === 'register' ? fullName : undefined
        })
      });
      const data = await res.json();
      if (res.ok) {
        authStore.setSession(data.access_token, {
          id: 'user-id-placeholder',
          email: identifier,
          name: mode === 'register' ? fullName : (identifier.split('@')[0]),
          role: data.role
        });

        onClose?.();
      } else {
        error = data.detail || 'Mã OTP không chính xác';
      }
    } catch (e) {
      error = 'Không thể xác thực';
    } finally {
      isLoading = false;
    }
  }

  function handleKeydown(e: KeyboardEvent, index: number) {
    if (e.key === 'Backspace') {
      if (code[index] === '' && index > 0) {
        document.getElementById(`otp-${index - 1}`)?.focus();
        code[index - 1] = '';
      } else {
        code[index] = '';
      }
      e.preventDefault();
    } else if (e.key === 'Enter' && fullCode.length === 6) {
      handleVerifyOTP();
    }
  }

  function handleSocialLogin(provider: 'google' | 'facebook' | 'zalo') {
    isLoading = true;
    error = null;
    sessionStorage.setItem('returnTo', window.location.pathname + window.location.search);
    sessionStorage.setItem('returnScroll', window.scrollY.toString());
    window.location.href = `/api/v1/auth/oauth/login/${provider}`;
  }

  function handleInput(e: Event, index: number) {
    const target = e.target as HTMLInputElement;
    const val = target.value.replace(/\D/g, '');

    if (val.length > 1) {
      const digits = val.slice(0, 6).split('');
      for (let i = 0; i < 6; i++) {
        code[i] = digits[i] || '';
      }
      target.value = code[index];
      const nextFocus = Math.min(index + val.length, 5);
      document.getElementById(`otp-${nextFocus}`)?.focus();
      if (digits.length === 6) handleVerifyOTP();
    } else {
      code[index] = val;
      target.value = val;
      if (val && index < 5) {
        document.getElementById(`otp-${index + 1}`)?.focus();
      }
    }
  }

  function handlePaste(e: ClipboardEvent) {
    const paste = e.clipboardData?.getData('text')?.trim().replace(/\s/g, '');
    if (paste && /^\d+$/.test(paste)) {
      const digits = paste.slice(0, 6).split('');
      for (let i = 0; i < 6; i++) {
        code[i] = digits[i] || '';
      }
      document.getElementById(`otp-${Math.min(digits.length - 1, 5)}`)?.focus();
      e.preventDefault();
      if (digits.length === 6) handleVerifyOTP();
    }
  }

  $effect(() => {
    liveLogs = [];
  });
</script>

    <div class="px-7 pt-1 pb-2 max-h-[calc(92vh-100px)] overflow-y-auto scrollbar-hide">
    {#if mode === 'profile' && authStore.user}
        <!-- TikTok Style Profile View -->
        <div class="flex flex-col items-center py-6 space-y-6" in:fade>
            <div class="relative group">
                <div class="w-24 h-24 {r} overflow-hidden border-4 border-gray-50 shadow-xl">
                    <img 
                        src={authStore.user.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(authStore.user.name || 'User')}&background=000&color=fff`} 
                        alt={authStore.user.name} 
                        class="w-full h-full object-cover"
                    />
                </div>
                <div class="absolute bottom-0 right-0 p-1.5 bg-black rounded-full border-2 border-white shadow-lg">
                    <UserPlus class="w-3.5 h-3.5 text-white" />
                </div>
            </div>

            <div class="text-center">
                <h3 class="text-xl font-black text-black tracking-tight italic">{authStore.user.name || 'Thành viên mới'}</h3>
                <p class="text-[10px] text-gray-400 font-bold tracking-widest mt-1">{authStore.user.email}</p>
            </div>

            <div class="w-full space-y-3 pt-4">
                <button class="w-full flex items-center justify-between p-4 bg-gray-50/50 hover:bg-gray-100/50 {r} transition-all">
                    <div class="flex items-center gap-3">
                        <ShieldCheck class="w-5 h-5 text-gray-400" />
                        <span class="text-[13px] font-bold text-black italic">Bảo mật tài khoản</span>
                    </div>
                    <ChevronRight class="w-4 h-4 text-gray-300" />
                </button>
                <button class="w-full flex items-center justify-between p-4 bg-gray-50/50 hover:bg-gray-100/50 {r} transition-all" onclick={() => ui.openAddress?.()}>
                    <div class="flex items-center gap-3">
                        <Mail class="w-5 h-5 text-gray-400" />
                        <span class="text-[13px] font-bold text-black italic">Địa chỉ nhận hàng</span>
                    </div>
                    <ChevronRight class="w-4 h-4 text-gray-300" />
                </button>
                <button 
                    class="w-full p-4 bg-red-50/50 text-[#ff3b30] {r} font-black text-[10px] tracking-widest hover:bg-[#ff3b30]/10 transition-all mt-4"
                    onclick={() => { authStore.logout(); onClose?.(); }}
                >
                    Đăng xuất
                </button>
            </div>
        </div>
    {:else if step === 'input'}
    <div class="space-y-3 pt-2">
        {#if mode === 'register'}
        <div class="group">
            <label for="fullName" class="text-[11px] font-black text-gray-400 tracking-widest mb-2 ml-2 block">HỌ VÀ TÊN</label>
            <input
            type="text"
            id="fullName"
            bind:value={fullName}
            placeholder="Nguyễn Văn A"
            class="w-full bg-gray-50/80 border-2 border-transparent p-3 md:p-3.5 {r} text-sm md:text-[14px] font-bold text-black focus:bg-white focus:border-[#C18F7E] transition-all outline-none shadow-sm"
            />
        </div>
        {/if}

        <div class="group">
        <label for="email" class="text-[11px] font-black text-gray-400 tracking-widest mb-2 ml-2 block">ĐỊA CHỈ EMAIL</label>
        <div class="relative">
            <input
            type="email"
            id="email"
            bind:value={identifier}
            placeholder="name@example.com"
            onkeydown={(e) => e.key === 'Enter' && (authMethod === 'otp' ? handleRequestOTP() : handlePasswordLogin())}
            class="w-full bg-gray-50/80 border-2 border-transparent p-3 md:p-3.5 pl-12 md:pl-12 {r} text-sm md:text-[14px] font-bold text-black focus:bg-white focus:border-[#C18F7E] transition-all outline-none shadow-sm"
            />
            <Mail class="absolute left-4 md:left-6 top-1/2 -translate-y-1/2 w-5 h-5 md:w-6 md:h-6 text-gray-300" />
        </div>
        </div>

        {#if authMethod === 'password' && mode === 'login'}
        <div class="group" in:slide>
        <label for="password" class="text-[11px] font-black text-gray-400 tracking-widest mb-2 ml-2 block italic">MẬT KHẨU</label>
        <div class="relative">
            <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            bind:value={password}
            placeholder="••••••••"
            onkeydown={(e) => e.key === 'Enter' && handlePasswordLogin()}
            class="w-full bg-gray-50/80 border-2 border-transparent p-3 md:p-3.5 pl-12 md:pl-12 pr-12 {r} text-sm md:text-[14px] font-bold text-black focus:bg-white focus:border-[#C18F7E] transition-all outline-none shadow-sm"
            />
            <Lock class="absolute left-4 md:left-6 top-1/2 -translate-y-1/2 w-5 h-5 md:w-6 md:h-6 text-gray-300" />
            <button
            type="button"
            onclick={() => showPassword = !showPassword}
            class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-300 hover:text-black transition-colors"
            >
            {#if showPassword}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
            </button>
        </div>
        </div>
        {/if}

        {#if error}
        <div class="text-[#ff3b30] text-[10px] font-black text-center tracking-widest bg-[#ff3b30]/10 p-3 rounded-xl border border-[#ff3b30]/20" in:scale>{error}</div>
        {/if}

        {#if isLoading && liveLogs.length > 0}
        <div class="bg-gray-50/80 {r} p-6 space-y-3" in:fade>
            {#each liveLogs as log, i}
            <div class="flex items-center gap-3" in:fly={{ x: -10, delay: i * 100 }}>
                <div class="w-1.5 h-1.5 rounded-full {i === liveLogs.length - 1 ? 'bg-luxury-copper animate-pulse' : 'bg-gray-300'}"></div>
                <span class="text-[10px] font-bold {i === liveLogs.length - 1 ? 'text-black italic' : 'text-gray-400'} tracking-wider">{log}</span>
            </div>
            {/each}
        </div>
        {/if}

        <div class="flex flex-col gap-2">
            <button
                onclick={authMethod === 'otp' ? handleRequestOTP : handlePasswordLogin}
                disabled={isLoading || !identifier || (authMethod === 'password' && !password)}
                class="w-full bg-[#C18F7E] text-white p-4 md:p-4.5 {r} font-black text-xs md:text-[12px] tracking-[0.2em] italic flex items-center justify-center gap-2 active:scale-95 transition-all disabled:opacity-30 disabled:pointer-events-none shadow-xl shadow-luxury-copper/20 group relative overflow-hidden"
            >
                <!-- Premium Shine Effect -->
                <div class="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none"></div>

                {#if isLoading && liveLogs.length === 0}
                <Loader2 class="w-5 h-5 animate-spin" />
                {:else if isLoading}
                Đang xử lý...
                {:else}
                {mode === 'login' ? 'ĐĂNG NHẬP' : 'ĐĂNG KÝ'} <ArrowRight class="w-5 h-5" />
                {/if}
            </button>

            {#if mode === 'login'}
                <button
                onclick={() => authMethod = authMethod === 'otp' ? 'password' : 'otp'}
                class="w-full text-center text-[10px] italic text-gray-400 hover:text-black transition-colors mt-1 underline underline-offset-4 decoration-gray-100"
                >
                {authMethod === 'otp' ? 'sử dụng mật khẩu' : 'sử dụng mã otp'}
                </button>
            {/if}
        </div>

        <!-- Social Login Divider -->
        <div class="relative py-1">
            <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-gray-100"></div>
            </div>
            <div class="relative flex justify-center text-center">
                <span class="bg-white px-4 text-[10px] font-black text-gray-300 tracking-[0.2em]">
                HOẶC TIẾP TỤC VỚI
                </span>
            </div>
        </div>

        <!-- Social Login Buttons (TikTok Premium Round Style) -->
        <div class="flex justify-center gap-6 pb-2">
            <button
                type="button"
                onclick={() => handleSocialLogin('zalo')}
                disabled={isLoading}
                class="flex items-center justify-center w-14 h-14 {r} bg-white border border-gray-100 hover:bg-gray-50 active:scale-90 transition-all disabled:opacity-30 shadow-sm"
                aria-label="Login with Zalo"
            >
                <svg class="w-8 h-8 animate-in zoom-in duration-300" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <path d="M50,11.8C25.4,11.8,5.5,28.6,5.5,49.2c0,11.9,6.5,22.6,16.5,29.3c-1.3,4.6-4.3,13.2-4.5,13.9c-0.5,1.5,0.7,2.6,2.1,1.8c1.3-0.8,14.6-8.7,20.2-11.8c3.3,0.6,6.7,0.9,10.2,0.9c24.6,0,44.5-16.8,44.5-37.4C94.5,28.6,74.6,11.8,50,11.8z" fill="#0068FF"/>
                <g transform="translate(18, 17) scale(2.7)">
                  <path d="M12.49 10.2722v-.4496h1.3467v6.3218h-.7704a.576.576 0 01-.5763-.5729l-.0006.0005a3.273 3.273 0 01-1.9372.6321c-1.8138 0-3.2844-1.4697-3.2844-3.2823 0-1.8125 1.4706-3.2822 3.2844-3.2822a3.273 3.273 0 011.9372.6321l.0006.0005zM6.9188 7.7896v.205c0 .3823-.051.6944-.2995 1.0605l-.03.0343c-.0542.0615-.1815.206-.2421.2843L2.024 14.8h4.8948v.7682a.5764.5764 0 01-.5767.5761H0v-.3622c0-.4436.1102-.6414.2495-.8476L4.8582 9.23H.1922V7.7896h6.7266zm8.5513 8.3548a.4805.4805 0 01-.4803-.4798v-7.875h1.4416v8.3548H15.47zM20.6934 9.6C22.52 9.6 24 11.0807 24 12.9044c0 1.8252-1.4801 3.306-3.3066 3.306-1.8264 0-3.3066-1.4808-3.3066-3.306 0-1.8237 1.4802-3.3044 3.3066-3.3044zm-10.1412 5.253c1.0675 0 1.9324-.8645 1.9324-1.9312 0-1.065-.865-1.9295-1.9324-1.9295s-1.9324.8644-1.9324 1.9295c0 1.0667.865 1.9312 1.9324 1.9312zm10.1412-.0033c1.0737 0 1.945-.8707 1.945-1.9453 0-1.073-.8713-1.9436-1.945-1.9436-1.0753 0-1.945.8706-1.945 1.9436 0 1.0746.8697 1.9453 1.945 1.9453z" fill="#FFF"/>
                </g>
                </svg>
            </button>
            <button
                type="button"
                onclick={() => handleSocialLogin('google')}
                disabled={isLoading}
                class="flex items-center justify-center w-14 h-14 {r} bg-white border border-gray-100 hover:bg-gray-50 active:scale-90 transition-all disabled:opacity-30 shadow-sm"
                aria-label="Login with Google"
            >
                <svg class="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
            </button>
            <button
                type="button"
                onclick={() => handleSocialLogin('facebook')}
                disabled={isLoading}
                class="flex items-center justify-center w-14 h-14 {r} bg-white border border-gray-100 hover:bg-gray-50 active:scale-90 transition-all disabled:opacity-30 shadow-sm"
                aria-label="Login with Facebook"
            >
                <svg class="w-6 h-6 text-[#1877F2]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
                <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                </svg>
            </button>
        </div>

        <button
        onclick={() => ui.authModal.mode = ui.authModal.mode === 'login' ? 'register' : 'login'}
        class="w-full text-center text-[9px] font-bold text-gray-300 hover:text-black transition-colors tracking-[0.1em] pt-2"
        >
        {mode === 'login' ? 'CHƯA CÓ TÀI KHOẢN? ĐĂNG KÝ' : 'ĐÃ LÀ THÀNH VIÊN? ĐĂNG NHẬP'}
        </button>
    </div>
    {:else}
        <div class="space-y-8 text-center" in:scale>
        <div>
            <p class="text-[11px] font-black text-gray-400 tracking-[0.3em] italic">XÁC THỰC TRUY CẬP</p>
            <p class="text-[13px] text-black font-semibold mt-3">
            Đã gửi mã đến <span class="font-black underline italic decoration-luxury-copper">{identifier}</span>
            </p>
        </div>

        <div class="flex justify-between gap-1.5">
            {#each code as char, i}
            <input
                type="text"
                inputmode="numeric"
                autocomplete={i === 0 ? "one-time-code" : "off"}
                id="otp-{i}"
                value={code[i]}
                oninput={(e) => handleInput(e, i)}
                onkeydown={(e) => handleKeydown(e, i)}
                onpaste={handlePaste}
                class="w-11 h-16 bg-gray-50/80 border-2 {code[i] ? 'border-luxury-copper text-luxury-copper' : 'border-transparent text-black'} text-center text-3xl font-black {r} focus:bg-white focus:border-luxury-copper transition-all outline-none shadow-sm"
            />
            {/each}
        </div>

        {#if error}
            <div class="text-[#ff3b30] text-[10px] font-black text-center tracking-widest bg-[#ff3b30]/10 p-3 rounded-xl border border-[#ff3b30]/20">{error}</div>
        {/if}

        <div class="space-y-4">
            <button
            onclick={handleVerifyOTP}
            disabled={isLoading || fullCode.length < 6}
            class="w-full bg-[#C18F7E] text-white p-5 {r} font-black text-[13px] tracking-[0.3em] italic flex items-center justify-center gap-2 active:scale-95 transition-all disabled:opacity-30 shadow-xl shadow-luxury-copper/20"
            >
            {#if isLoading}
                <Loader2 class="w-5 h-5 animate-spin" />
            {:else}
                XÁC NHẬN ĐĂNG NHẬP
            {/if}
            </button>
            <button
            onclick={() => step = 'input'}
            class="text-[10px] font-bold text-gray-400 hover:text-black transition-colors tracking-[0.2em] italic"
            >
            THAY ĐỔI THÔNG TIN
            </button>
        </div>
        </div>
    {/if}

</div>
