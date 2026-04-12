<script lang="ts">
  import { authStore } from '$lib/state/authStore.svelte';
  import { getClientUi } from '$lib/state/commerce/ui.svelte';
  import { X, Mail, ShieldCheck, ArrowRight, Loader2, KeyRound, UserPlus } from 'lucide-svelte';
  import { fade, fly, scale } from 'svelte/transition';

  const ui = getClientUi();
  let step = $state<'input' | 'otp'>('input');
  let identifier = $state('');
  let fullName = $state('');
  let code = $state(['', '', '', '', '', '']); 
  let otpToken = $state('');
  let isLoading = $state(false);
  let error = $state<string | null>(null);

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
        console.log("[Pulse] Task completed. Transitioning to OTP step.");
        setTimeout(() => {
          step = 'otp';
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

  async function handleRequestOTP() {
    if (!identifier) return;
    if (mode === 'register' && !fullName) {
      error = "Vui lòng nhập họ và tên để đăng ký.";
      return;
    }
    
    isLoading = true;
    error = null;
    liveLogs = [];
    
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
        
        // Elite V2.2: Context-Anchored Close
        ui.closeModal();
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
    if (e.key >= '0' && e.key <= '9') {
      code[index] = e.key;
      if (index < 5) document.getElementById(`otp-${index + 1}`)?.focus();
      e.preventDefault();
    } else if (e.key === 'Backspace') {
      if (code[index] === '' && index > 0) document.getElementById(`otp-${index - 1}`)?.focus();
      code[index] = '';
    } else if (e.key === 'Enter' && fullCode.length === 6) handleVerifyOTP();
  }

  function handlePaste(e: ClipboardEvent) {
    const paste = e.clipboardData?.getData('text');
    if (paste && paste.length === 6 && /^\d+$/.test(paste)) {
      code = paste.split('');
      document.getElementById(`otp-5`)?.focus();
    }
  }
  $effect(() => {
    console.log("QuickLoginModal: Mounted with mode:", mode);
    liveLogs = []; // Reset on new mount
    return () => console.log("QuickLoginModal: Unmounted");
  });
</script>

<div class="fixed inset-0 z-[100] flex items-center justify-center p-0 md:p-4 bg-black/40 backdrop-blur-[2px]" in:fade>
  <div class="bg-white w-full max-w-sm rounded-none shadow-2xl border border-gray-100 overflow-hidden relative" 
       in:fly={{ y: 20, duration: 400 }}>
    
    <!-- Top accent bar removed -->

    <div class="px-8 py-6 border-b border-gray-50 flex items-center justify-start relative">
      <h2 class="text-xl font-black text-gray-900 tracking-tighter uppercase">
        {mode === 'login' ? 'ĐĂNG NHẬP' : 'GIA NHẬP'}
      </h2>
      <button onclick={() => ui.closeModal()} class="absolute top-4 right-4 p-2 hover:bg-gray-100 transition-colors">
        <X class="w-5 h-5 text-gray-400" />
      </button>
    </div>

    <div class="p-8">
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
                onkeydown={(e) => e.key === 'Enter' && handleRequestOTP()}
                class="w-full bg-gray-50 border-2 border-gray-100 p-4 pl-12 rounded-none text-sm font-bold text-black focus:border-black transition-all outline-none"
              />
              <Mail class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
            </div>
          </div>

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

          <button 
            onclick={handleRequestOTP}
            disabled={isLoading || !identifier}
            class="w-full bg-[#ee4d2d] text-white p-5 rounded-none font-black text-xs tracking-[0.3em] flex items-center justify-center gap-2 hover:bg-black transition-all disabled:opacity-30 disabled:pointer-events-none shadow-lg hover:shadow-none"
          >
            {#if isLoading && liveLogs.length === 0}
              <Loader2 class="w-5 h-5 animate-spin" />
            {:else if isLoading}
              ĐANG XỬ LÝ...
            {:else}
              {mode === 'login' ? 'GỬI MÃ OTP' : 'ĐĂNG KÝ NGAY'} <ArrowRight class="w-5 h-5" />
            {/if}
          </button>

          <button 
            onclick={() => authStore.modalState.mode = authStore.modalState.mode === 'login' ? 'register' : 'login'}
            class="w-full text-center text-[10px] font-black text-gray-400 hover:text-black transition-colors uppercase tracking-widest pt-2"
          >
            {mode === 'login' ? 'BẠN LÀ THÀNH VIÊN MỚI? ĐĂNG KÝ' : 'ĐÃ CÓ TÀI KHOẢN? ĐĂNG NHẬP'}
          </button>
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
                id="otp-{i}"
                maxlength="1"
                bind:value={code[i]}
                onkeydown={(e) => handleKeydown(e, i)}
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

    <div class="p-6 bg-gray-50 border-t-2 border-gray-100 flex items-center justify-center gap-2">
      <ShieldCheck class="w-4 h-4 text-gray-300" />
      <span class="text-[9px] text-gray-400 font-bold uppercase tracking-[0.2em]">Xác thực bảo mật bởi Micsmo</span>
    </div>

  </div>
</div>
