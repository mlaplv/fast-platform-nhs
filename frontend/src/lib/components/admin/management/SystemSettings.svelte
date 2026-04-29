<script lang="ts">
  import { onMount } from "svelte";
  import { apiClient } from "$lib/utils/apiClient";
  import { useNanobot } from "$lib/state/nanobot.svelte";
  const nanobot = useNanobot();
  import type { BaseWidgetProps } from "$lib/types";

  import Save from "lucide-svelte/icons/save";
  import RefreshCw from "lucide-svelte/icons/refresh-cw";
  import Globe from "lucide-svelte/icons/globe";
  import Phone from "lucide-svelte/icons/phone";
  import Share2 from "lucide-svelte/icons/share-2";
  import Search from "lucide-svelte/icons/search";
  import MapPin from "lucide-svelte/icons/map-pin";
  import Tool from "lucide-svelte/icons/wrench";
  import Plus from "lucide-svelte/icons/plus";
  import TrendingUp from "lucide-svelte/icons/trending-up";
  import Trash2 from "lucide-svelte/icons/trash-2";
  import Upload from "lucide-svelte/icons/upload";
  import Sparkles from "lucide-svelte/icons/sparkles";
  import ShieldCheck from "lucide-svelte/icons/shield-check";
  import Coins from "lucide-svelte/icons/coins";
  import MediaVaultModal from "../../media/MediaVaultModal.svelte";
  import type { MediaAsset } from "$lib/state/types";

  let { data = {} } = $props<BaseWidgetProps>();

  interface BasicInfo {
    site_name: string;
    description: string;
    logo_desktop: string | null;
    logo_mobile: string | null;
    favicon: string | null;
  }

  interface ContactInfo {
    company_name: string;
    tax_id: string;
    business_license: string;
    phone: string;
    hotline: string;
    email: string;
    address: string;
    working_hours: string;
  }

  interface SocialMediaItem {
    platform: string;
    url: string;
    icon_url: string | null;
  }

  interface SeoAnalytics {
    meta_title: string;
    meta_description: string;
    meta_keywords: string;
    google_analytics_id: string;
    facebook_pixel_id: string;
  }

  interface GoogleMaps {
    map_iframe: string;
    api_key: string;
  }

  interface MaintenanceMode {
    is_enabled: boolean;
    message: string;
  }

  interface SupportBotSettings {
    helen_enabled: boolean;
    offline_message: string;
    zalo_integration_enabled: boolean;
    messenger_integration_enabled: boolean;
  }

  interface ConversionSettings {
    fomo_enabled: boolean;
  }

  interface CurrencySettings {
    symbol: string;
    position: "prefix" | "suffix";
    decimal_separator: string;
    thousand_separator: string;
    show_symbol: boolean;
  }

  interface EntropySettings {
    enabled: boolean;
    tone_override: string | null;
    structure_override: string | null;
    schema_drop_probability: number;
    lexical_sanitizer_enabled: boolean;
  }

  interface SystemSettings {
    basic_info: BasicInfo;
    contact_info: ContactInfo;
    social_media: SocialMediaItem[];
    seo_analytics: SeoAnalytics;
    google_maps: GoogleMaps;
    maintenance: MaintenanceMode;
    support_bot: SupportBotSettings;
    conversions: ConversionSettings;
    currency: CurrencySettings;
    entropy: EntropySettings;
  }

  let settings = $state<SystemSettings>({
    basic_info: { site_name: "", description: "", logo_desktop: null, logo_mobile: null, favicon: null },
    contact_info: { company_name: "", tax_id: "", business_license: "", phone: "", hotline: "", email: "", address: "", working_hours: "" },
    social_media: [],
    seo_analytics: { meta_title: "", meta_description: "", meta_keywords: "", google_analytics_id: "", facebook_pixel_id: "" },
    google_maps: { map_iframe: "", api_key: "" },
    maintenance: { is_enabled: false, message: "" },
    support_bot: { 
      helen_enabled: true, 
      offline_message: "",
      zalo_integration_enabled: true,
      messenger_integration_enabled: true
    },
    conversions: {
      fomo_enabled: true
    },
    currency: {
      symbol: "₫",
      position: "suffix",
      decimal_separator: ".",
      thousand_separator: ".",
      show_symbol: true
    },
    entropy: {
      enabled: true,
      tone_override: null,
      structure_override: null,
      schema_drop_probability: 0.2,
      lexical_sanitizer_enabled: true
    }
  });

  let activeTab = $state("basic");
  let isLoading = $state(true);
  let isSaving = $state(false);

  // Media Picker State
  let showMediaModal = $state(false);
  let currentPickField = $state<string | null>(null);
  let currentPickType = $state<'basic' | 'social'>('basic');
  let currentSocialIndex = $state<number | null>(null);

  type TabId = "basic" | "contact" | "currency" | "social" | "seo" | "maps" | "maintenance" | "helen" | "conversion" | "entropy";

  interface TabDefinition {
    id: TabId;
    label: string;
    icon: typeof Globe;
  }

  const tabs: TabDefinition[] = [
    { id: "basic", label: "Thông tin cơ bản", icon: Globe },
    { id: "contact", label: "Liên hệ", icon: Phone },
    { id: "currency", label: "Tiền tệ", icon: Coins },
    { id: "social", label: "Mạng xã hội", icon: Share2 },
    { id: "seo", label: "SEO & Analytics", icon: Search },
    { id: "maps", label: "Google Maps", icon: MapPin },
    { id: "maintenance", label: "Bảo trì", icon: Tool },
    { id: "helen", label: "Helen AI", icon: Sparkles },
    { id: "conversion", label: "Chuyển đổi", icon: TrendingUp },
    { id: "entropy", label: "SGE Shield", icon: ShieldCheck }
  ];

  onMount(async () => {
    try {
      const res = await apiClient.get<{ settings: SystemSettings }>("/api/v1/settings/general");
      if (res?.settings) {
        settings = res.settings;
      }
    } catch (e) {
      nanobot.showToast("Failed to fetch settings.", "error");
    } finally {
      isLoading = false;
    }
  });

  async function saveSettings() {
    isSaving = true;
    try {
      await apiClient.post("/api/v1/settings/general", settings);
      nanobot.showToast("Cấu hình hệ thống đã được lưu.", "success");
    } catch (e) {
      nanobot.showToast("Không thể lưu cấu hình.", "error");
    } finally {
      isSaving = false;
    }
  }

  function addSocial() {
    settings.social_media = [...settings.social_media, { platform: "", url: "", icon_url: null }];
  }

  function removeSocial(index: number) {
    settings.social_media = settings.social_media.filter((_, i) => i !== index);
  }

  function handleUpload(field: keyof BasicInfo) {
    currentPickField = field;
    currentPickType = 'basic';
    showMediaModal = true;
  }

  function handleSocialUpload(index: number) {
    currentSocialIndex = index;
    currentPickType = 'social';
    showMediaModal = true;
  }

  function handleMediaSelect(url: string) {
    if (currentPickType === 'basic' && currentPickField) {
      // @ts-ignore - dynamic key access
      settings.basic_info[currentPickField] = url;
    } else if (currentPickType === 'social' && currentSocialIndex !== null) {
      settings.social_media[currentSocialIndex].icon_url = url;
    }
    showMediaModal = false;
    currentPickField = null;
    currentSocialIndex = null;
  }

  const brandAssets = [
    { label: 'Logo Desktop', field: 'logo_desktop' as keyof BasicInfo, icon: Globe },
    { label: 'Logo Mobile', field: 'logo_mobile' as keyof BasicInfo, icon: Share2 },
    { label: 'Favicon / Icon', field: 'favicon' as keyof BasicInfo, icon: Globe }
  ];

</script>

<div class="w-full h-full flex flex-col bg-[#020202] text-zinc-100 selection:bg-cyan-500/30 font-sans">
  {#if isLoading}
    <div class="flex-1 flex flex-col items-center justify-center gap-8">
      <div class="relative">
        <div class="w-24 h-24 border-2 border-cyan-500/5 border-t-cyan-400 rounded-full animate-spin"></div>
      </div>
      <h2 class="text-xs font-mono text-cyan-400 uppercase tracking-[0.6em] animate-pulse">
        Accessing System Core
      </h2>
    </div>
  {:else}
    <header class="h-auto min-h-[3.5rem] lg:h-16 px-4 sm:px-6 lg:px-8 border-b border-white/5 flex flex-col lg:flex-row items-center justify-between bg-zinc-950/40 backdrop-blur-xl gap-4 py-2 lg:py-0 z-50 sticky top-0">
      <div class="flex items-center gap-4">
        <div class="flex flex-col lg:flex-row lg:items-center gap-2 lg:gap-4">
          <h1 class="text-lg lg:text-xl font-black italic tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 to-zinc-500">
            SYSTEM CONFIGURATION
          </h1>
          <div class="flex items-center gap-2 px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded-md">
            <div class="w-1 h-1 rounded-full bg-cyan-500 animate-pulse"></div>
            <span class="text-[8px] font-mono text-cyan-500 uppercase tracking-widest">Core Access Granted</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <button
          onclick={saveSettings}
          disabled={isSaving}
          class="group relative h-9 lg:h-10 px-6 bg-cyan-600 hover:bg-cyan-500 text-black font-bold rounded-lg shadow-[0_0_15px_rgba(8,145,178,0.3)] transition-all disabled:opacity-50 flex items-center gap-2"
        >
          {#if isSaving}
            <RefreshCw size={14} class="animate-spin" />
          {:else}
            <Save size={14} class="group-hover:scale-110 transition-transform" />
          {/if}
          <span class="text-[10px] uppercase tracking-[0.15em] font-black">
            {isSaving ? "Saving..." : "Save Config"}
          </span>
        </button>
      </div>
    </header>

    <main class="flex-1 flex flex-col lg:flex-row min-h-0">
      <!-- Sidebar Tabs -->
      <aside class="w-full lg:w-64 border-b lg:border-b-0 lg:border-r border-white/5 bg-zinc-950/20 overflow-y-auto custom-scrollbar flex flex-col p-4 gap-2">
        {#each tabs as tab}
          <button
            onclick={() => activeTab = tab.id}
            class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-left group
              {activeTab === tab.id ? 'bg-cyan-500/10 border border-cyan-500/20 text-cyan-400' : 'hover:bg-white/5 border border-transparent text-zinc-500 hover:text-zinc-300'}"
          >
            <tab.icon size={18} class={activeTab === tab.id ? 'text-cyan-400' : 'group-hover:text-zinc-300'} />
            <span class="text-xs font-bold uppercase tracking-wider">{tab.label}</span>
          </button>
        {/each}
      </aside>

      <!-- Content Area -->
      <section class="flex-1 overflow-y-auto custom-scrollbar bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.03),transparent_70%)] p-4 sm:p-6 lg:p-8">
        <div class="max-w-4xl mx-auto">
          
          {#if activeTab === 'basic'}
            <div class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <section class="space-y-4">
                <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Globe size={16} /> Thông tin cơ bản
                </h3>
                <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                  <div class="space-y-1">
                    <label for="site_name" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Tên Website</label>
                    <input id="site_name" bind:value={settings.basic_info.site_name} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="e.g. SmartShop" />
                  </div>
                  <div class="space-y-1">
                    <label for="site_desc" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Mô tả hệ thống</label>
                    <textarea id="site_desc" bind:value={settings.basic_info.description} rows="3" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors resize-none" placeholder="Mô tả ngắn về website..."></textarea>
                  </div>
                </div>
              </section>

              <section class="space-y-4">
                <h3 class="text-xs font-bold text-zinc-400 uppercase tracking-widest">Brand Assets</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {#each brandAssets as item}
                    <div class="bg-zinc-950/40 border border-white/5 rounded-2xl p-6 flex flex-col items-center gap-4 group/asset">
                      <div class="w-16 h-16 rounded-xl bg-black border border-white/5 flex items-center justify-center relative overflow-hidden group-hover/asset:border-cyan-500/30 transition-colors">
                        {#if settings.basic_info[item.field]}
                          <img src={settings.basic_info[item.field]} alt={item.label} class="w-full h-full object-contain p-2" />
                        {:else}
                          <item.icon size={24} class="text-zinc-700 group-hover/asset:text-cyan-500/50 transition-colors" />
                        {/if}
                      </div>
                      <div class="text-center">
                        <p class="text-[10px] font-black uppercase tracking-tighter mb-2">{item.label}</p>
                        <button 
                          onclick={() => handleUpload(item.field)}
                          aria-label={`Upload ${item.label}`}
                          class="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-mono uppercase tracking-widest transition-all flex items-center gap-2 mx-auto"
                        >
                          <Upload size={10} /> Sync Asset
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              </section>
            </div>

          {:else if activeTab === 'contact'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Phone size={16} /> Thông tin liên hệ
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                <div class="space-y-1 md:col-span-2">
                  <label for="company_name" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Tên Công Ty</label>
                  <input id="company_name" bind:value={settings.contact_info.company_name} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="Công ty TNHH SmartShop" />
                </div>
                <div class="space-y-1">
                  <label for="tax_id" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Mã số thuế</label>
                  <input id="tax_id" bind:value={settings.contact_info.tax_id} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="e.g. 0101234567" />
                </div>
                <div class="space-y-1">
                  <label for="business_license" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Giấy phép kinh doanh</label>
                  <input id="business_license" bind:value={settings.contact_info.business_license} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="Số GPKD, ngày cấp..." />
                </div>
                <div class="space-y-1">
                  <label for="phone" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Điện thoại</label>
                  <input id="phone" bind:value={settings.contact_info.phone} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="0901 234 567" />
                </div>
                <div class="space-y-1">
                  <label for="hotline" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Hotline</label>
                  <input id="hotline" bind:value={settings.contact_info.hotline} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="1800 XXXX" />
                </div>
                <div class="space-y-1">
                  <label for="email" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Email</label>
                  <input id="email" bind:value={settings.contact_info.email} type="email" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="admin@example.com" />
                </div>
                <div class="space-y-1">
                  <label for="hours" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Giờ làm việc</label>
                  <input id="hours" bind:value={settings.contact_info.working_hours} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="8:00 - 22:00" />
                </div>
                <div class="space-y-1 md:col-span-2">
                  <label for="address" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Địa chỉ</label>
                  <input id="address" bind:value={settings.contact_info.address} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="Số 1, Đường ABC, Quận XYZ..." />
                </div>
              </div>
            </div>

          {:else if activeTab === 'currency'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Coins size={16} /> Cấu hình Tiền tệ
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                <div class="space-y-1">
                  <label for="currency_symbol" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Ký hiệu tiền tệ</label>
                  <input id="currency_symbol" bind:value={settings.currency.symbol} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="e.g. ₫, $, €" />
                </div>
                <div class="space-y-1">
                  <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Vị trí hiển thị</label>
                  <select bind:value={settings.currency.position} class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors">
                    <option value="prefix">Trước giá trị (e.g. ₫378.000)</option>
                    <option value="suffix">Sau giá trị (e.g. 378.000₫)</option>
                  </select>
                </div>
                <div class="space-y-1">
                  <label for="thousand_sep" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Phân cách hàng nghìn</label>
                  <input id="thousand_sep" bind:value={settings.currency.thousand_separator} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="e.g. . or ," />
                </div>
                <div class="space-y-1">
                  <label for="decimal_sep" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Phân cách thập phân</label>
                  <input id="decimal_sep" bind:value={settings.currency.decimal_separator} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="e.g. , or ." />
                </div>
                <div class="flex items-center justify-between md:col-span-2 p-4 bg-black/20 rounded-xl border border-white/5">
                  <div>
                    <h4 class="text-xs font-bold text-white uppercase tracking-wider">Hiển thị ký hiệu</h4>
                    <p class="text-[9px] text-zinc-500 font-mono">Bật/tắt hiển thị ký hiệu tiền tệ trên toàn hệ thống</p>
                  </div>
                  <button 
                    onclick={() => settings.currency.show_symbol = !settings.currency.show_symbol}
                    class="relative w-10 h-5 rounded-full transition-colors duration-300 {settings.currency.show_symbol ? 'bg-cyan-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300 {settings.currency.show_symbol ? 'translate-x-5' : 'translate-x-0'}"></div>
                  </button>
                </div>
              </div>

              <div class="bg-cyan-500/5 border border-cyan-500/20 rounded-2xl p-6">
                <h4 class="text-[10px] font-black text-cyan-400 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                  <Sparkles size={14} /> Xem trước hiển thị
                </h4>
                <div class="flex items-center justify-center py-8">
                  <div class="text-4xl font-black italic tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white to-zinc-500">
                    {#if settings.currency.position === 'prefix'}
                      {settings.currency.show_symbol ? settings.currency.symbol : ''}378{settings.currency.thousand_separator}000
                    {:else}
                      378{settings.currency.thousand_separator}000{settings.currency.show_symbol ? settings.currency.symbol : ''}
                    {/if}
                  </div>
                </div>
              </div>
            </div>

          {:else if activeTab === 'social'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Share2 size={16} /> Mạng xã hội
                </h3>
                <button 
                  onclick={addSocial}
                  class="px-4 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-600/30 rounded-lg text-xs font-black text-cyan-400 uppercase tracking-widest transition-all flex items-center gap-2"
                >
                  <Plus size={14} /> Add Channel
                </button>
              </div>

              {#if settings.social_media.length === 0}
                <div class="bg-zinc-950/40 border border-dashed border-white/10 rounded-2xl p-12 text-center">
                  <Share2 size={32} class="text-zinc-800 mx-auto mb-4" />
                  <p class="text-zinc-600 text-sm font-mono uppercase tracking-widest">No social channels configured</p>
                </div>
              {/if}

              <div class="grid grid-cols-1 gap-4">
                {#each settings.social_media as item, i}
                  <div class="bg-zinc-950/40 border border-white/5 rounded-2xl p-4 flex items-center gap-4 animate-in slide-in-from-left-2 duration-200">
                    <button 
                      onclick={() => handleSocialUpload(i)}
                      aria-label="Upload Social Icon"
                      class="w-12 h-12 rounded-lg bg-black border border-white/5 flex items-center justify-center group/socialico relative overflow-hidden"
                    >
                      {#if item.icon_url}
                        <img src={item.icon_url} alt="Icon" class="w-full h-full object-contain p-1" />
                      {:else}
                        <Upload size={16} class="text-zinc-700 group-hover/socialico:text-cyan-500 transition-colors" />
                      {/if}
                    </button>
                    <div class="flex-1 grid grid-cols-2 gap-4">
                      <input bind:value={item.platform} type="text" autocomplete="off" aria-label="Platform Name" class="bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-xs focus:border-cyan-500/50 outline-none" placeholder="Tên (e.g. Facebook)" />
                      <input bind:value={item.url} type="text" autocomplete="off" aria-label="Platform URL" class="bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-xs focus:border-cyan-500/50 outline-none" placeholder="Link liên kết" />
                    </div>
                    <button 
                      onclick={() => removeSocial(i)}
                      aria-label="Remove Social Channel"
                      class="p-2 text-zinc-600 hover:text-red-400 transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                {/each}
              </div>
            </div>

          {:else if activeTab === 'seo'}
            <div class="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <section class="space-y-4">
                <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Search size={16} /> SEO Optimization
                </h3>
                <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                  <div class="space-y-1">
                    <label for="seo_title" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Meta Title (Default)</label>
                    <input id="seo_title" bind:value={settings.seo_analytics.meta_title} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="Tiêu đề trang mẫu..." />
                  </div>
                  <div class="space-y-1">
                    <label for="seo_keys" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Meta Keywords</label>
                    <input id="seo_keys" bind:value={settings.seo_analytics.meta_keywords} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="AI, mua sắm, thời trang..." />
                  </div>
                  <div class="space-y-1">
                    <label for="seo_desc" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Meta Description</label>
                    <textarea id="seo_desc" bind:value={settings.seo_analytics.meta_description} rows="3" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors resize-none" placeholder="Mô tả chuẩn SEO..."></textarea>
                  </div>
                </div>
              </section>

              <section class="space-y-4">
                <h3 class="text-sm font-black text-emerald-400 uppercase tracking-[0.2em] flex items-center gap-2">
                  <Search size={16} /> Analytics & Tracking
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                  <div class="space-y-1">
                    <label for="ga_id" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Google Analytics ID</label>
                    <input id="ga_id" bind:value={settings.seo_analytics.google_analytics_id} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-emerald-500/50 outline-none transition-colors" placeholder="G-XXXXXXXX" />
                  </div>
                  <div class="space-y-1">
                    <label for="fb_id" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Facebook Pixel ID</label>
                    <input id="fb_id" bind:value={settings.seo_analytics.facebook_pixel_id} type="text" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-emerald-500/50 outline-none transition-colors" placeholder="XXXXXXXXXX" />
                  </div>
                </div>
              </section>
            </div>

          {:else if activeTab === 'maps'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <MapPin size={16} /> Google Maps Config
              </h3>
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-6">
                <div class="space-y-1">
                  <label for="map_iframe" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Embed Iframe Code</label>
                  <textarea id="map_iframe" bind:value={settings.google_maps.map_iframe} rows="4" autocomplete="off" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm font-mono focus:border-cyan-500/50 outline-none transition-colors resize-none" placeholder="<iframe src='...' ...></iframe>"></textarea>
                  <p class="text-[9px] text-zinc-600 mt-1 italic">Dán mã nhúng iframe từ Google Maps vào đây.</p>
                </div>
                <div class="space-y-1">
                  <label for="map_key" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Maps API Key (Optional)</label>
                  <input id="map_key" bind:value={settings.google_maps.api_key} type="password" autocomplete="new-password" spellcheck="false" class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors" placeholder="AIza..." />
                </div>
              </div>

              {#if settings.google_maps.map_iframe}
                <div class="bg-black border border-white/5 rounded-2xl overflow-hidden h-64 relative grayscale hover:grayscale-0 transition-all duration-700">
                  <div class="absolute inset-0 pointer-events-none bg-gradient-to-t from-black to-transparent opacity-40"></div>
                  {@html settings.google_maps.map_iframe.replace(/width="[^"]*"/, 'width="100%"').replace(/height="[^"]*"/, 'height="100%"')}
                </div>
              {/if}
            </div>

          {:else if activeTab === 'maintenance'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-amber-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Tool size={16} /> Maintenance Mode
              </h3>
              
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-8 items-center">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h4 class="text-base font-black text-white uppercase italic tracking-tighter">Emergency Shutdown</h4>
                    <p class="text-[10px] text-zinc-500 font-mono tracking-widest mt-1">IF ACTIVE, VISITORS WILL SEE THE MAINTENANCE PAGE</p>
                  </div>
                  
                  <button 
                    onclick={() => settings.maintenance.is_enabled = !settings.maintenance.is_enabled}
                    aria-label="Toggle Maintenance Mode"
                    class="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none 
                      {settings.maintenance.is_enabled ? 'bg-red-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300
                      {settings.maintenance.is_enabled ? 'translate-x-7' : 'translate-x-0'}">
                    </div>
                  </button>
                </div>

                <div class="space-y-1">
                  <label for="maint_msg" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Lý do bảo trì / Thông điệp</label>
                  <textarea 
                    id="maint_msg"
                    bind:value={settings.maintenance.message} 
                    rows="4" 
                    disabled={!settings.maintenance.is_enabled}
                    autocomplete="off"
                    class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-amber-500/50 outline-none transition-colors resize-none disabled:opacity-40" 
                    placeholder="Thông báo cho khách hàng..."
                  ></textarea>
                </div>
                
                {#if settings.maintenance.is_enabled}
                  <div class="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-4 animate-pulse">
                    <div class="w-2 h-2 rounded-full bg-red-500"></div>
                    <span class="text-[10px] font-black text-red-500 uppercase tracking-[0.2em]">System Isolated: Maintenance Protocol Active</span>
                  </div>
                {/if}
              </div>
            </div>
          {:else if activeTab === 'helen'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-cyan-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <Sparkles size={16} /> Helen AI Configuration
              </h3>
              
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-8 items-center">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h4 class="text-base font-black text-white uppercase italic tracking-tighter">Helen AI Control</h4>
                    <p class="text-[10px] text-zinc-500 font-mono tracking-widest mt-1">ENABLE OR DISABLE THE AI SUPPORT BOT GLOBALLY</p>
                  </div>
                  
                  <button 
                    onclick={() => settings.support_bot.helen_enabled = !settings.support_bot.helen_enabled}
                    aria-label="Toggle Helen AI"
                    class="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none 
                      {settings.support_bot.helen_enabled ? 'bg-cyan-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300
                      {settings.support_bot.helen_enabled ? 'translate-x-7' : 'translate-x-0'}">
                    </div>
                  </button>
                </div>

                <div class="space-y-1">
                  <label for="helen_offline_msg" class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Thông báo khi Helen OFF</label>
                  <textarea 
                    id="helen_offline_msg"
                    bind:value={settings.support_bot.offline_message} 
                    rows="4" 
                    autocomplete="off"
                    class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:border-cyan-500/50 outline-none transition-colors resize-none" 
                    placeholder="Dược sĩ tư vấn sẽ hỗ trợ sếp ngay ạ..."
                  ></textarea>
                </div>
                
                {#if settings.support_bot.helen_enabled}
                  <div class="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl flex items-center gap-4">
                    <div class="w-2 h-2 rounded-full bg-cyan-500 animate-ping"></div>
                    <span class="text-[10px] font-black text-cyan-400 uppercase tracking-[0.2em]">Helen AI is Online & Active</span>
                  </div>
                {:else}
                  <div class="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center gap-4">
                    <div class="w-2 h-2 rounded-full bg-amber-500"></div>
                    <span class="text-[10px] font-black text-amber-500 uppercase tracking-[0.2em]">Manual Support Mode Active</span>
                  </div>
                {/if}

                <div class="w-full h-px bg-white/5 my-4"></div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <!-- Zalo Integration -->
                  <div class="bg-black/40 border border-white/5 rounded-xl p-5 flex flex-col gap-4">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                          <span class="text-blue-400 font-black text-xs">Z</span>
                        </div>
                        <div>
                          <h4 class="text-xs font-bold text-white uppercase tracking-wider">Zalo OA</h4>
                          <p class="text-[9px] text-zinc-500 font-mono">PUSH NOTIFICATIONS</p>
                        </div>
                      </div>
                      <button 
                        onclick={() => settings.support_bot.zalo_integration_enabled = !settings.support_bot.zalo_integration_enabled}
                        class="relative w-10 h-5 rounded-full transition-colors duration-300 {settings.support_bot.zalo_integration_enabled ? 'bg-blue-500' : 'bg-zinc-800'}"
                      >
                        <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300 {settings.support_bot.zalo_integration_enabled ? 'translate-x-5' : 'translate-x-0'}"></div>
                      </button>
                    </div>
                    <p class="text-[10px] text-zinc-400 leading-relaxed italic">Gửi link Zalo và đẩy thông báo cho Admin khi có khách cần hỗ trợ gấp thưa Sếp.</p>
                  </div>

                  <!-- Messenger Integration -->
                  <div class="bg-black/40 border border-white/5 rounded-xl p-5 flex flex-col gap-4">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                          <span class="text-purple-400 font-black text-xs">M</span>
                        </div>
                        <div>
                          <h4 class="text-xs font-bold text-white uppercase tracking-wider">Messenger</h4>
                          <p class="text-[9px] text-zinc-500 font-mono">FB INTEGRATION</p>
                        </div>
                      </div>
                      <button 
                        onclick={() => settings.support_bot.messenger_integration_enabled = !settings.support_bot.messenger_integration_enabled}
                        class="relative w-10 h-5 rounded-full transition-colors duration-300 {settings.support_bot.messenger_integration_enabled ? 'bg-purple-500' : 'bg-zinc-800'}"
                      >
                        <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300 {settings.support_bot.messenger_integration_enabled ? 'translate-x-5' : 'translate-x-0'}"></div>
                      </button>
                    </div>
                    <p class="text-[10px] text-zinc-400 leading-relaxed italic">Điều hướng khách hàng sang kênh Facebook Messenger khi cần tư vấn chuyên sâu.</p>
                  </div>
                </div>
              </div>
            </div>
          {:else if activeTab === 'conversion'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-rose-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <TrendingUp size={16} /> Viral Marketing & Conversion
              </h3>
              
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-8 items-center">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h4 class="text-base font-black text-white uppercase italic tracking-tighter">Neural Activity Bar (FOMO)</h4>
                    <p class="text-[10px] text-zinc-500 font-mono tracking-widest mt-1">REAL-TIME SOCIAL PROOF NOTIFICATIONS</p>
                  </div>
                  
                  <button 
                    onclick={() => settings.conversions.fomo_enabled = !settings.conversions.fomo_enabled}
                    aria-label="Toggle FOMO"
                    class="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none 
                      {settings.conversions.fomo_enabled ? 'bg-rose-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300
                      {settings.conversions.fomo_enabled ? 'translate-x-7' : 'translate-x-0'}">
                    </div>
                  </button>
                </div>

                <div class="p-6 bg-black/40 border border-white/5 rounded-xl space-y-4">
                  <div class="flex items-start gap-4">
                    <div class="w-10 h-10 rounded-full bg-rose-500/10 flex items-center justify-center flex-shrink-0">
                      <Sparkles size={18} class="text-rose-400" />
                    </div>
                    <div>
                      <h5 class="text-xs font-bold text-white uppercase tracking-wider mb-1">Cơ chế hoạt động thần kinh 2026</h5>
                      <p class="text-[10px] text-zinc-400 leading-relaxed">
                        Tự động hiển thị các thông báo mua hàng, số lượng tồn kho và lượt xem thực tế theo phong cách tối giản. 
                        Nâng cao uy tín thương hiệu và kích thích quyết định mua hàng tức thì của khách hàng.
                      </p>
                    </div>
                  </div>
                </div>

                {#if settings.conversions.fomo_enabled}
                  <div class="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-4">
                    <div class="w-2 h-2 rounded-full bg-rose-500 animate-ping"></div>
                    <span class="text-[10px] font-black text-rose-400 uppercase tracking-[0.2em]">FOMO Engine is Active & Accelerating Conversions</span>
                  </div>
                {:else}
                  <div class="p-4 bg-zinc-800/20 border border-white/5 rounded-xl flex items-center gap-4 opacity-50">
                    <div class="w-2 h-2 rounded-full bg-zinc-600"></div>
                    <span class="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em]">Conversion Boosters Disabled</span>
                  </div>
                {/if}
              </div>
            </div>
          {:else if activeTab === 'entropy'}
            <div class="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <h3 class="text-sm font-black text-indigo-400 uppercase tracking-[0.2em] flex items-center gap-2">
                <ShieldCheck size={16} /> AI Footprint Entropy (SGE Shield)
              </h3>
              
              <div class="grid grid-cols-1 gap-6 bg-zinc-950/40 border border-white/5 rounded-2xl p-8 items-center">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h4 class="text-base font-black text-white uppercase italic tracking-tighter">SGE Shield V1.0</h4>
                    <p class="text-[10px] text-zinc-500 font-mono tracking-widest mt-1">PROTECT AGAINST GOOGLE AI OVERVIEWS PURGE</p>
                  </div>
                  
                  <button 
                    onclick={() => settings.entropy.enabled = !settings.entropy.enabled}
                    aria-label="Toggle Entropy"
                    class="relative w-14 h-7 rounded-full transition-colors duration-300 focus:outline-none 
                      {settings.entropy.enabled ? 'bg-indigo-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-lg transition-transform duration-300
                      {settings.entropy.enabled ? 'translate-x-7' : 'translate-x-0'}">
                    </div>
                  </button>
                </div>

                <div class="p-4 bg-indigo-500/10 border border-indigo-500/20 rounded-xl mb-4">
                  <p class="text-[11px] text-zinc-300 leading-relaxed font-mono">
                    <span class="text-indigo-400 font-bold">INFO:</span> Cơ chế tiêm "Độ nhiễu của con người" vào AI Content. Mặc định tự động Random giọng văn (Tone), cấu trúc (Structure) và Schema.
                  </p>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div class="space-y-1">
                    <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Giọng văn (Tone) mặc định</label>
                    <select bind:value={settings.entropy.tone_override} disabled={!settings.entropy.enabled} class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-sm focus:border-indigo-500/50 outline-none transition-colors disabled:opacity-40">
                      <option value={null}>🎲 Auto Random (Khuyên dùng)</option>
                      <option value="dermatologist">👨‍⚕️ Bác sĩ da liễu</option>
                      <option value="pharmacist">👩‍🔬 Dược sĩ tận tâm</option>
                      <option value="health_blogger">✨ Beauty Blogger</option>
                      <option value="science_writer">🔬 Nhà khoa học</option>
                      <option value="mom_expert">👩‍👧 Mẹ Việt Nam chia sẻ</option>
                      <option value="customer_advocate">🛍️ Khách hàng trải nghiệm</option>
                      <option value="wellness_coach">🏃 Coach sức khỏe</option>
                      <option value="traditional_medicine">🌿 Bác sĩ Y học cổ truyền</option>
                    </select>
                  </div>
                  
                  <div class="space-y-1">
                    <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Cấu trúc (Structure) mặc định</label>
                    <select bind:value={settings.entropy.structure_override} disabled={!settings.entropy.enabled} class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-sm focus:border-indigo-500/50 outline-none transition-colors disabled:opacity-40">
                      <option value={null}>🎲 Auto Random (Khuyên dùng)</option>
                      <option value="hook_first">🎣 Mở đầu gây tò mò</option>
                      <option value="problem_solution">🎯 Vấn đề → Giải pháp</option>
                      <option value="story_driven">📖 Kể chuyện trải nghiệm</option>
                      <option value="listicle">🔢 Danh sách đánh số</option>
                      <option value="comparison">⚖️ So sánh trước/sau</option>
                      <option value="question_answer">❓ Hỏi đáp xen kẽ</option>
                    </select>
                  </div>
                </div>

                <div class="space-y-1 mt-4">
                  <label class="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Tỉ lệ Drop Optional Schema Keys (0 - 1.0)</label>
                  <input bind:value={settings.entropy.schema_drop_probability} type="number" step="0.1" min="0" max="1" disabled={!settings.entropy.enabled} class="w-full bg-black/50 border border-white/10 rounded-lg px-4 py-2 text-sm focus:border-indigo-500/50 outline-none transition-colors disabled:opacity-40" />
                  <p class="text-[9px] text-zinc-600 mt-1 italic">Mặc định: 0.2 (20%). Google thường soi các keys Schema quá hoàn hảo.</p>
                </div>

                <div class="flex items-center justify-between mt-4 p-4 bg-black/40 border border-white/5 rounded-xl">
                  <div>
                    <h4 class="text-xs font-bold text-white uppercase tracking-wider">Bộ lọc Lexical Sanitizer</h4>
                    <p class="text-[9px] text-zinc-500 font-mono">Tự động xóa/thay thế các từ "rập khuôn AI" (Tóm lại, Không ngoa khi nói...)</p>
                  </div>
                  <button 
                    onclick={() => settings.entropy.lexical_sanitizer_enabled = !settings.entropy.lexical_sanitizer_enabled}
                    disabled={!settings.entropy.enabled}
                    class="relative w-10 h-5 rounded-full transition-colors duration-300 disabled:opacity-40 {settings.entropy.lexical_sanitizer_enabled ? 'bg-indigo-500' : 'bg-zinc-800'}"
                  >
                    <div class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-300 {settings.entropy.lexical_sanitizer_enabled ? 'translate-x-5' : 'translate-x-0'}"></div>
                  </button>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </section>
    </main>
  {/if}
</div>

<MediaVaultModal
  isOpen={showMediaModal}
  onClose={() => showMediaModal = false}
  onSelect={handleMediaSelect}
/>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 10px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  /* Prevent browser autofill from turning background white */
  input:-webkit-autofill,
  input:-webkit-autofill:hover, 
  input:-webkit-autofill:focus, 
  input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 30px #0a0a0a inset !important;
    -webkit-text-fill-color: #f4f4f5 !important;
    transition: background-color 5000s ease-in-out 0s;
  }

  /* Fix OmniCommand looking "white" due to backdrop-filter on light backgrounds */
  :global(.omni-waterdrop) :global(.flex-1.rounded-full) {
    background: rgba(0, 0, 0, 0.8) !important;
    border-color: rgba(0, 255, 255, 0.1) !important;
  }
</style>
