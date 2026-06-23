<script lang="ts">
  import { authStore } from "$lib/state/authStore.svelte";
  import { getClientUi } from "$lib/state/commerce/ui.svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { fade, fly } from "svelte/transition";
  import { untrack } from "svelte";
  import MemberCard from "./MemberCard.svelte";
  import SkinProfile from "./SkinProfile.svelte";
  import Avatar from "./Avatar.svelte";
  import { Z_INDEX_CLIENT } from "$lib/core/constants/zIndex";
  import User from "@lucide/svelte/icons/user";
  import Mail from "@lucide/svelte/icons/mail";
  import Phone from "@lucide/svelte/icons/phone";
  import Calendar from "@lucide/svelte/icons/calendar";
  import Heart from "@lucide/svelte/icons/heart";
  import Fingerprint from "@lucide/svelte/icons/fingerprint";
  import Sparkles from "@lucide/svelte/icons/sparkles";

  const ui = getClientUi();

  // Profile States
  let name = $state(authStore.user?.name || "");
  let email = $state(authStore.user?.email || "");
  let username = $state(authStore.user?.username || "");
  let isEditingEmail = $state(false);
  let gender = $state(authStore.user?.gender || "OTHER");
  let dob = $state(
    authStore.user?.dob ? new Date(authStore.user.dob) : new Date(),
  );

  let birthDay = $state(dob.getDate());
  let birthMonth = $state(dob.getMonth() + 1);
  let birthYear = $state(dob.getFullYear());
  let phone = $state(authStore.user?.phone || "");

  // Skin Profile States (Nested in extra_metadata)
  let skinData = $state(
    authStore.user?.extra_metadata?.skin_profile || {
      skinType: "",
      concerns: [],
      sensitivity: 5,
    },
  );

  let isSaving = $state(false);
  let activeTab = $state("basic"); // basic | beauty

  // Elite V3.2: Unified Reactivity Engine
  $effect(() => {
    if (authStore.user) {
      const user = authStore.user;
      untrack(() => {
        name = user.name || "";
        email = user.email || "";
        username = user.username || "";
        gender = user.gender || "OTHER";
        phone = user.phone || "";

        if (user.dob) {
          const d = new Date(user.dob);
          birthDay = d.getDate();
          birthMonth = d.getMonth() + 1;
          birthYear = d.getFullYear();
        }

        if (user.extra_metadata?.skin_profile) {
          skinData = { ...user.extra_metadata.skin_profile };
        }
      });
    }
  });

  function generateCardNumber(id: string = "") {
    if (!id) return "";
    const cleanId = id.replace(/-/g, "").toUpperCase();
    return `${cleanId.substring(0, 4)} ${cleanId.substring(4, 8)} ${cleanId.substring(8, 12)} ${cleanId.substring(12, 16)}`.toUpperCase();
  }

  const days = Array.from({ length: 31 }, (_, i) => i + 1);
  const months = Array.from({ length: 12 }, (_, i) => i + 1);
  const years = Array.from(
    { length: 80 },
    (_, i) => new Date().getFullYear() - 10 - i,
  );

  async function handleSave() {
    // 🛡️ Client-side Validation
    if (!name.trim()) {
      ui.showToast("Quý khách vui lòng điền họ và tên ạ.", "warning");
      return;
    }
    if (!username.trim() || username.length < 3) {
      ui.showToast("Tên đăng nhập cần có tối thiểu 3 ký tự.", "warning");
      return;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email.trim() || !emailRegex.test(email)) {
      ui.showToast(
        "Quý khách vui lòng kiểm tra lại định dạng địa chỉ email.",
        "warning",
      );
      return;
    }

    isSaving = true;
    try {
      const updatedDob = new Date(
        birthYear,
        birthMonth - 1,
        birthDay,
      ).toISOString();
      const cardNumber =
        authStore.user?.extra_metadata?.cardNumber ||
        generateCardNumber(authStore.user?.id);

      await apiClient.patch<{ ok: boolean }>("/api/v1/client/user/profile", {
        name,
        gender,
        username,
        email,
        phone,
        dob: updatedDob,
        extra_metadata: {
          ...authStore.user?.extra_metadata,
          skin_profile: skinData,
          cardNumber,
        },
      });

      await authStore.sync();
      isEditingEmail = false;
      ui.showToast("Thông tin của Quý khách đã được ghi nhận! ✨", "success");
    } catch (e: unknown) {
      const error = e as { status?: number; message?: string };
      if (error && typeof error === "object" && "status" in error) {
        if (
          error.status === 409 ||
          error.status === 400 ||
          (error.message && error.message.includes("tồn tại"))
        ) {
          console.warn(
            "⚠️ [Beauty Profile] Validation/Conflict:",
            error.message,
          );
          ui.showToast(error.message || "Dữ liệu không hợp lệ", "warning");
        } else {
          console.error("❌ [Beauty Profile] Lỗi hệ thống khi cập nhật:", e);
          ui.showToast(
            error.message || "Có lỗi xảy ra, mong Quý khách thứ lỗi.",
            "error",
          );
        }
      } else {
        ui.showToast("Có lỗi xảy ra, mong Quý khách thứ lỗi.", "error");
      }
    } finally {
      isSaving = false;
    }
  }

  function maskEmail(val: string) {
    if (!val) return "Chưa cập nhật";
    const [user, domain] = val.split("@");
    return `${user.substring(0, 3)}***@${domain}`;
  }
</script>

<div class="max-w-4xl mx-auto space-y-12 pb-20 px-4 md:px-6">
  <!-- Elite Header Section: Card & Identity -->
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
    <div class="lg:col-span-7 space-y-4">
      <MemberCard />
      <div class="flex justify-center md:justify-start px-2">
        <a
          href="/user/loyalty"
          class="flex items-center gap-2 px-4 py-2 bg-luxury-copper/5 border border-luxury-copper/20 rounded-full group active:scale-95 transition-all"
        >
          <Sparkles class="w-3.5 h-3.5 text-luxury-copper animate-pulse" />
          <span class="text-[9px] font-black text-luxury-copper tracking-[2px]"
            >Xem quyền lợi thành viên →</span
          >
        </a>
      </div>
    </div>

    <div
      class="lg:col-span-5 flex flex-col items-center lg:items-end justify-center space-y-4 px-4"
    >
      <div class="relative">
        <Avatar
          src={authStore.user?.avatar_url}
          name={authStore.user?.name}
          size="lg"
          editable={true}
        />
        <div
          class="absolute -bottom-1 -right-1 bg-white p-1.5 rounded-full shadow-sm border border-stone-100"
        >
          <Sparkles class="w-3.5 h-3.5 text-luxury-copper" />
        </div>
      </div>
      <div class="text-center lg:text-right">
        <h2 class="text-2xl font-serif italic text-stone-800 leading-tight">
          {authStore.user?.name || "Quý khách"}
        </h2>
        <p class="text-[10px] tracking-[3px] text-stone-400 mt-1 font-bold">
          Thành viên
        </p>
      </div>
    </div>
  </div>

  <!-- Navigation Tabs: Modern Pill Style -->
  <div class="flex justify-center md:justify-start">
    <div
      class="inline-flex p-1 bg-stone-50 rounded-full border border-stone-100"
    >
      <button
        onclick={() => (activeTab = "basic")}
        class="px-6 md:px-10 py-2.5 rounded-full text-[11px] tracking-widest font-bold transition-all duration-500 flex items-center gap-2
        {activeTab === 'basic'
          ? 'bg-white text-stone-800 shadow-sm ring-1 ring-stone-200/50'
          : 'text-stone-400 hover:text-stone-600'}"
      >
        <User class="w-3.5 h-3.5" />
        Thông tin
      </button>
      <button
        onclick={() => (activeTab = "beauty")}
        class="px-6 md:px-10 py-2.5 rounded-full text-[11px] tracking-widest font-bold transition-all duration-500 flex items-center gap-2
        {activeTab === 'beauty'
          ? 'bg-white text-stone-800 shadow-sm ring-1 ring-stone-200/50'
          : 'text-stone-400 hover:text-stone-600'}"
      >
        <Heart class="w-3.5 h-3.5" />
        Vẻ đẹp
      </button>
    </div>
  </div>

  <!-- Form Content -->
  <div class="relative">
    {#if activeTab === "basic"}
      <div
        class="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10"
        in:fade={{ duration: 400 }}
      >
        <!-- Identity Group -->
        <div class="space-y-10">
          <div class="flex items-center gap-3 border-b border-stone-100 pb-2">
            <Fingerprint class="w-4 h-4 text-luxury-copper" />
            <h3 class="text-[12px] tracking-[2px] font-bold text-stone-800">
              Định danh tài khoản
            </h3>
          </div>

          <div class="space-y-8">
            <div class="space-y-1.5 group">
              <label
                for="username"
                class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors"
                >Tên đăng nhập</label
              >
              <input
                id="username"
                type="text"
                bind:value={username}
                placeholder="Thiết lập tên đăng nhập..."
                class="w-full h-12 bg-transparent border-b border-stone-200 outline-none focus:border-luxury-copper transition-all text-stone-800 font-medium placeholder:text-stone-200 placeholder:italic"
              />
            </div>

            <div class="space-y-1.5 group">
              <label
                for="fullname"
                class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors"
                >Họ và tên</label
              >
              <input
                id="fullname"
                type="text"
                bind:value={name}
                placeholder="Nhập họ tên đầy đủ..."
                class="w-full h-12 bg-transparent border-b border-stone-200 outline-none focus:border-luxury-copper transition-all text-stone-800 font-medium placeholder:text-stone-200"
              />
            </div>

            <div class="space-y-1.5 group">
              <label
                class="text-[10px] tracking-widest text-stone-400 font-bold mb-2 block"
                >Giới tính</label
              >
              <div class="flex items-center gap-6 h-12">
                {#each [["Nam", "MALE"], ["Nữ", "FEMALE"], ["Khác", "OTHER"]] as [label, val]}
                    <label
                      for="gender-{val}"
                      class="flex items-center gap-2.5 cursor-pointer group/radio py-2"
                    >
                      <div
                        class="w-5 h-5 rounded-full border border-stone-300 flex items-center justify-center transition-all group-hover/radio:border-luxury-copper {gender ===
                        val
                          ? 'border-luxury-copper bg-luxury-copper/5'
                          : ''}"
                      >
                        {#if gender === val}
                          <div
                            class="w-2 h-2 bg-luxury-copper rounded-full"
                            in:fade
                          ></div>
                        {/if}
                      </div>
                      <input
                        id="gender-{val}"
                        type="radio"
                        bind:group={gender}
                        value={val}
                        class="hidden"
                      />
                    <span
                      class="text-[13px] text-stone-600 group-hover/radio:text-stone-800 transition-colors"
                      >{label}</span
                    >
                  </label>
                {/each}
              </div>
            </div>
          </div>
        </div>

        <!-- Contact & Birthday Group -->
        <div class="space-y-10">
          <div class="flex items-center gap-3 border-b border-stone-100 pb-2">
            <Mail class="w-4 h-4 text-luxury-copper" />
            <h3 class="text-[12px] tracking-[2px] font-bold text-stone-800">
              Liên hệ & Cá nhân
            </h3>
          </div>

          <div class="space-y-8">
            <div class="space-y-1.5 group">
              <label
                for="email"
                class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors"
                >Địa chỉ Email</label
              >
              <div
                class="w-full h-12 border-b border-stone-200 flex items-center justify-between"
              >
                {#if isEditingEmail}
                  <input
                    id="email"
                    type="email"
                    bind:value={email}
                    class="w-full h-full outline-none bg-transparent text-stone-800 font-medium"
                    onblur={() => {
                      if (!email) isEditingEmail = false;
                    }}
                    autoFocus
                  />
                {:else}
                  <span class="text-stone-800 font-medium"
                    >{maskEmail(email)}</span
                  >
                  <button
                    type="button"
                    onclick={() => (isEditingEmail = true)}
                    class="text-[9px] text-luxury-copper hover:underline font-black tracking-widest"
                  >
                    Thay đổi
                  </button>
                {/if}
              </div>
            </div>

            <div class="space-y-1.5 group">
              <label
                for="phone"
                class="text-[10px] tracking-widest text-stone-400 font-bold group-focus-within:text-luxury-copper transition-colors"
                >Số điện thoại</label
              >
              <div class="relative">
                <input
                  id="phone"
                  type="tel"
                  bind:value={phone}
                  placeholder="0xx xxxx xxx"
                  class="w-full h-12 bg-transparent border-b border-stone-200 outline-none focus:border-luxury-copper transition-all text-stone-800 font-medium placeholder:text-stone-200"
                />
                <Phone
                  class="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-stone-200"
                />
              </div>
            </div>

            <div class="space-y-3">
              <div class="flex items-center gap-2">
                <Calendar class="w-3.5 h-3.5 text-luxury-copper" />
                <label
                  for="birth-day"
                  class="text-[10px] tracking-widest text-stone-400 font-bold"
                  >Ngày sinh của bạn</label
                >
              </div>
              <div class="flex gap-4">
                <div class="flex-1 border-b border-stone-200">
                  <select
                    id="birth-day"
                    bind:value={birthDay}
                    class="w-full h-12 bg-transparent outline-none text-[13px] text-stone-800 cursor-pointer appearance-none"
                  >
                    {#each days as d}<option value={d}
                        >{d < 10 ? "0" + d : d}</option
                      >{/each}
                  </select>
                </div>
                <div class="flex-1 border-b border-stone-200">
                  <select
                    id="birth-month"
                    bind:value={birthMonth}
                    class="w-full h-12 bg-transparent outline-none text-[13px] text-stone-800 cursor-pointer appearance-none"
                  >
                    {#each months as m}<option value={m}>Tháng {m}</option
                      >{/each}
                  </select>
                </div>
                <div class="flex-1 border-b border-stone-200">
                  <select
                    id="birth-year"
                    bind:value={birthYear}
                    class="w-full h-12 bg-transparent outline-none text-[13px] text-stone-800 cursor-pointer appearance-none"
                  >
                    {#each years as y}<option value={y}>{y}</option>{/each}
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    {:else}
      <div in:fade={{ duration: 400 }}>
        <SkinProfile bind:data={skinData} />
      </div>
    {/if}
  </div>

  <!-- Footer Action: Elegant Floating Effect -->
  <div class="pt-10 flex flex-col items-center space-y-4">
    <button
      onclick={handleSave}
      disabled={isSaving}
      class="group relative px-16 py-4 bg-stone-800 text-white overflow-hidden transition-all duration-700 hover:shadow-[0_20px_40px_rgba(0,0,0,0.2)] disabled:opacity-50"
    >
      <div
        class="absolute inset-0 bg-luxury-copper translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-700 ease-out"
      ></div>
      <span class="relative z-10 text-[11px] tracking-[5px] font-black">
        {isSaving ? "Đang lưu hồ sơ..." : "Lưu thay đổi"}
      </span>
    </button>
    <p class="text-[9px] text-stone-300 tracking-widest">
      Mọi thông tin được bảo mật bởi {ui.settings?.basic_info?.site_name || 'osmo.vn'}
    </p>
  </div>
</div>

<style>
  :global(.luxury-copper) {
    color: #c5a059;
  }
  :global(.bg-luxury-copper) {
    background-color: #c5a059;
  }
  :global(.border-luxury-copper) {
    border-color: #c5a059;
  }
</style>
