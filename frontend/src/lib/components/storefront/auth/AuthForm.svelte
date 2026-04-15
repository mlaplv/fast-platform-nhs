<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { X, Mail, ShieldCheck, ArrowRight, Loader2, KeyRound, UserPlus, Lock, Eye, EyeOff } from 'lucide-svelte';
  import { fallbackSha256 } from '$lib/utils/cryptoFallback';
  import { apiClient } from '$lib/utils/apiClient';
  import { fade, fly, scale, slide } from 'svelte/transition';

  let { onClose } = $props();

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
      console.log("[Pulse] Received OTP_UPDATE event:", e.data);
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

      const data = await apiClient.post<any>('/api/v1/auth/login', {
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
    } catch (e: any) {
      error = e.message || 'Tên đăng nhập hoặc mật khẩu không đúng';
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

<div class="p-8 max-h-[calc(90vh-140px)] overflow-y-auto scrollbar-hide">
    {#if step === 'input'}
    <div class="space-y-6">
        {#if mode === 'register'}
        <div class="group">
            <label for="fullName" class="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2 block">HỌ VÀ TÊN</label>
            <input
            type="text"
            id="fullName"
            bind:value={fullName}
            placeholder="Nguyễn Văn A"
            class="w-full bg-gray-50 border-2 border-gray-100 p-4 rounded-none text-sm font-bold text-black focus:border-black transition-all outline-none"
            />
        </div>
        {/if}

        <div class="group">
        <label for="email" class="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2 block">ĐỊA CHỈ EMAIL</label>
        <div class="relative">
            <input
            type="email"
            id="email"
            bind:value={identifier}
            placeholder="name@example.com"
            onkeydown={(e) => e.key === 'Enter' && (authMethod === 'otp' ? handleRequestOTP() : handlePasswordLogin())}
            class="w-full bg-gray-50 border-2 border-gray-100 p-4 pl-12 rounded-none text-sm font-bold text-black focus:border-black transition-all outline-none"
            />
            <Mail class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
        </div>
        </div>

        {#if authMethod === 'password' && mode === 'login'}
        <div class="group" in:slide>
        <label for="password" class="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2 block">MẬT KHẨU</label>
        <div class="relative">
            <input
            type={showPassword ? 'text' : 'password'}
            id="password"
            bind:value={password}
            placeholder="••••••••"
            onkeydown={(e) => e.key === 'Enter' && handlePasswordLogin()}
            class="w-full bg-gray-50 border-2 border-gray-100 p-4 pl-12 pr-12 rounded-none text-sm font-bold text-black focus:border-black transition-all outline-none"
            />
            <Lock class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
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
        <div class="text-[#ee4d2d] text-[11px] font-black text-center uppercase tracking-widest bg-[#ee4d2d]/10 p-3 border border-[#ee4d2d]/20" in:scale>{error}</div>
        {/if}

        {#if isLoading && liveLogs.length > 0}
        <div class="bg-gray-50 border-x-2 border-gray-100 p-6 space-y-3" in:fade>
            {#each liveLogs as log, i}
            <div class="flex items-center gap-3" in:fly={{ x: -10, delay: i * 100 }}>
                <div class="w-1.5 h-1.5 rounded-full {i === liveLogs.length - 1 ? 'bg-[#ee4d2d] animate-pulse' : 'bg-gray-300'}"></div>
                <span class="text-[10px] font-bold {i === liveLogs.length - 1 ? 'text-black' : 'text-gray-400'} uppercase tracking-wider">{log}</span>
            </div>
            {/each}
        </div>
        {/if}

        <div class="flex flex-col">
        <button
            onclick={authMethod === 'otp' ? handleRequestOTP : handlePasswordLogin}
            disabled={isLoading || !identifier || (authMethod === 'password' && !password)}
            class="w-full bg-[#ee4d2d] text-white p-5 rounded-none font-black text-xs tracking-[0.3em] flex items-center justify-center gap-2 hover:bg-black transition-all disabled:opacity-30 disabled:pointer-events-none shadow-lg hover:shadow-none"
        >
            {#if isLoading && liveLogs.length === 0}
            <Loader2 class="w-5 h-5 animate-spin" />
            {:else if isLoading}
            ĐANG XỬ LÝ...
            {:else}
            {authMethod === 'otp' ? (mode === 'login' ? 'GỬI MÃ OTP' : 'ĐĂNG KÝ NGAY') : 'ĐĂNG NHẬP'} <ArrowRight class="w-5 h-5" />
            {/if}
        </button>

        {#if mode === 'login'}
            <button
            onclick={() => authMethod = authMethod === 'otp' ? 'password' : 'otp'}
            class="w-fit text-left text-[10px] italic text-stone-400 hover:text-luxury-copper transition-colors mt-0 ml-1"
            >
            {authMethod === 'otp' ? 'hoặc đăng nhập bằng mật khẩu' : 'hoặc sử dụng mã otp'}
            </button>
        {/if}
        </div>

        <button
        onclick={() => ui.authModal.mode = ui.authModal.mode === 'login' ? 'register' : 'login'}
        class="w-full text-center text-[10px] font-black text-gray-400 hover:text-black transition-colors uppercase tracking-widest pt-2"
        >
        {mode === 'login' ? 'BẠN LÀ THÀNH VIÊN MỚI? ĐĂNG KÝ' : 'ĐÃ CÓ TÀI KHOẢN? ĐĂNG NHẬP'}
        </button>

        <!-- Social Login Divider -->
        <div class="relative py-4 mt-2">
        <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-100"></div>
        </div>
        <div class="relative flex justify-center text-center">
            <span class="bg-white px-3 text-[9px] font-bold text-gray-400 uppercase tracking-widest">
            HOẶC TIẾP TỤC VỚI
            </span>
        </div>
        </div>

        <!-- Social Login Buttons -->
        <div class="grid grid-cols-3 gap-3">
        <button
            type="button"
            onclick={() => handleSocialLogin('google')}
            disabled={isLoading}
            class="flex items-center justify-center p-3 border-2 border-gray-100 hover:border-black hover:bg-black hover:text-white transition-all disabled:opacity-30 disabled:pointer-events-none group"
            aria-label="Login with Google"
        >
            <svg class="w-5 h-5 group-hover:grayscale group-hover:brightness-0 group-hover:invert transition-all" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
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
            class="flex items-center justify-center p-3 border-2 border-gray-100 hover:border-[#1877F2] hover:bg-[#1877F2] transition-all disabled:opacity-30 disabled:pointer-events-none group"
            aria-label="Login with Facebook"
        >
            <svg class="w-5 h-5 text-[#1877F2] group-hover:text-white transition-colors" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
            </svg>
        </button>
        <button
            type="button"
            onclick={() => handleSocialLogin('zalo')}
            disabled={isLoading}
            class="flex items-center justify-center p-3 border-2 border-gray-100 hover:border-[#0068FF] hover:bg-[#0068FF] transition-all disabled:opacity-30 disabled:pointer-events-none group"
            aria-label="Login with Zalo"
        >
            <svg class="w-7 h-5 group-hover:brightness-0 group-hover:invert transition-all" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <path d="M50,11.8C25.4,11.8,5.5,28.6,5.5,49.2c0,11.9,6.5,22.6,16.5,29.3c-1.3,4.6-4.3,13.2-4.5,13.9 c-0.5,1.5,0.7,2.6,2.1,1.8c1.3-0.8,14.6-8.7,20.2-11.8c3.3,0.6,6.7,0.9,10.2,0.9c24.6,0,44.5-16.8,44.5-37.4C94.5,28.6,74.6,11.8,50,11.8z" fill="#0068FF"/>
            <path d="M43.7,60.6h-9.9v-2.3l8.7-10.7h-8.7v-2.3h9.9v2.3l-8.7,10.7h8.7V60.6z M57.2,60.6H54c-1.1,0-2.1-0.9-2.1-2.1V47.5 c0-1.1,0.9-2.1,2.1-2.1h3.2c1.1,0,2.1,0.9,2.1,2.1v11C59.2,59.7,58.3,60.6,57.2,60.6z M55.6,47.5h-3.2v11h3.2V47.5z M69.7,46.5 c4.6,0,8.3,3.7,8.3,8.3c0,4.6-3.7,8.3-8.3,8.3h-4.3v-16.6H69.7z M69.7,60.6c3.4,0,6.1-2.7,6.1-6.1s-2.7-6.1-6.1-6.1h-2v12.2H69.7z M31.3,46.5c4.6,0,8.3,3.7,8.3,8.3c0,4.6-3.7,8.3-8.3,8.3h-4.3v-16.6H31.3z M31.3,60.6c3.4,0,6.1-2.7,6.1-6.1 s-2.7-6.1-6.1-6.1h-2v12.2H31.3z" fill="#FFF"/>
            </svg>
        </button>
        </div>
    </div>
    {:else}
        <div class="space-y-8 text-center">
        <div>
            <p class="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em]">XÁC THỰC TRUY CẬP</p>
            <p class="text-xs text-gray-400 mt-2">
            Đã gửi đến <span class="text-black font-black">{identifier}</span>
            </p>
        </div>

        <div class="flex justify-between gap-1">
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
                class="w-11 h-16 bg-gray-50 border-2 {code[i] ? 'border-black text-black' : 'border-gray-100 text-black'} text-center text-3xl font-black rounded-none focus:border-black transition-all outline-none"
            />
            {/each}
        </div>

        {#if error}
            <div class="text-[#ee4d2d] text-[11px] font-black text-center uppercase tracking-widest bg-[#ee4d2d]/10 p-3 border border-[#ee4d2d]/20">{error}</div>
        {/if}

        <div class="space-y-4">
            <button
            onclick={handleVerifyOTP}
            disabled={isLoading || fullCode.length < 6}
            class="w-full bg-gradient-to-r from-luxury-copper to-luxury-peach text-white p-5 rounded-none font-black text-xs tracking-[0.3em] flex items-center justify-center gap-2 hover:opacity-90 transition-all disabled:opacity-30 shadow-lg shadow-luxury-copper/20"
            >
            {#if isLoading}
                <Loader2 class="w-5 h-5 animate-spin" />
            {:else}
                XÁC NHẬN MẬT MÃ
            {/if}
            </button>
            <button
            onclick={() => step = 'input'}
            class="text-[10px] font-black text-gray-400 hover:text-black transition-colors uppercase tracking-widest"
            >
            THAY ĐỔI THÔNG TIN
            </button>
        </div>
        </div>
    {/if}
</div>
