import { apiClient } from '$lib/utils/apiClient';
import { useNanobot } from "$lib/state/nanobot.svelte";
import { onDestroy } from 'svelte';
import { behaviorEngine } from '$lib/core/ads/BehaviorEngine';

const API_BASE = '/api/v1';
const ADS_API = `${API_BASE}/ads-protection`;

// --- Type Definitions (Elite V2.6 Standard) ---
export interface AdInsight {
  type: string;
  title: string;
  message: string;
  severity: string;
}

export interface GoogleCampaign {
  resource_name: string;
  name: string;
  status: string;
  daily_budget_vnd?: number;
  bidding_strategy?: string;
}

export interface GoogleAdGroup {
  resource_name: string;
  name: string;
  status?: string;
  cpc_bid_vnd?: number;
}

export interface GoogleAd {
  resource_name: string;
  name?: string;
  status?: string;
  final_url?: string;
  headlines?: string[];
  descriptions?: string[];
  display_path1?: string;
  display_path2?: string;
}

export interface BlacklistedIP {
  ip: string;
  reason?: string;
  campaign_id?: string;
  is_global?: boolean;
  created_at?: string;
}

export interface NegativeKeyword {
  resource_name: string;
  text: string;
  campaign_id?: string;
  is_global?: boolean;
}

export interface ReportItem {
  name: string;
  created_at?: string;
}

export interface AdStrengthDetails {
  overall_strength: string;
  headline_count_ok: boolean;
  keyword_coverage_ok: boolean;
  headline_uniqueness_ok: boolean;
  description_uniqueness_ok: boolean;
  has_sitelinks: boolean;
}

export interface AISuggestionResponse {
  success: boolean;
  message?: string;
  headlines?: string[];
  descriptions?: string[];
  display_path1?: string;
  display_path2?: string;
  negative_keywords?: string[];
  ad_strength?: AdStrengthDetails;
}

export interface KeywordSuggestionItem {
  keyword: string;
  intent: 'COMMERCIAL' | 'INFORMATIONAL' | 'NAVIGATIONAL';
  match_type: 'EXACT' | 'PHRASE' | 'BROAD';
  relevance: 'HIGH' | 'MEDIUM' | 'LOW';
  estimated_cpc_vnd?: number;
  estimated_volume?: string;
}

export interface CompetitorHeadlineItem {
  source_domain: string;
  headline: string;
  ad_type: 'HEADLINE' | 'DESCRIPTION';
}

export interface CompetitorAnalysisResponse {
  success: boolean;
  message: string;
  page_title?: string;
  page_summary?: string;
  keyword_suggestions: KeywordSuggestionItem[];
  competitor_headlines: CompetitorHeadlineItem[];
  negative_keyword_suggestions: string[];
  recommended_display_path1?: string;
  recommended_display_path2?: string;
  seo_gaps?: string;
}

export interface GenericSuccessResponse {
  success: boolean;
  message?: string;
}

export interface FraudSummary {
  period_hours: number;
  generated_at: string;
  totals: {
    all_clicks: number;
    fraud: number;
    suspicious: number;
    clean: number;
    fraud_rate_pct: number;
    google_all_clicks: number;
    google_invalid_clicks: number;
  };
  budget: {
    avg_cpc_vnd: number;
    estimated_wasted_vnd: number;
    google_estimated_wasted_vnd: number;
  };
  top_offending_ips: Array<{ ip: string; click_count: number }>;
  hourly_breakdown: Array<{ hour: string; fraud_rate: number; total_clicks: number }>;
  insights: AdInsight[];
}

export interface GoogleMetric {
  campaign_name: string;
  clicks: number;
  invalid_clicks: number;
  invalid_click_rate: number;
  cost_vnd: number;
}

export interface AgenticLog {
  time: string;
  type: 'AGENT' | 'SYSTEM';
  message: string;
  detail?: string;
}

export interface InvestigationReportResult {
  status: 'idle' | 'ready' | 'error' | 'not_found';
  support_message_preview?: string;
  agentic_logs?: AgenticLog[];
  total_fraud_clicks?: number;
  csv_path?: string;
}

export function createAdsState() {
  const nanobot = useNanobot();

  let summary = $state<FraudSummary | null>(null);
  let insights = $state<AdInsight[]>([]);
  let reportResult = $state<InvestigationReportResult | null>(null);
  let googleMetrics = $state<GoogleMetric[]>([]);
  let campaigns = $state<GoogleCampaign[]>([]);
  let selectedCampaign = $state<GoogleCampaign | null>(null);
  let adGroups = $state<GoogleAdGroup[]>([]);
  let selectedAdGroup = $state<GoogleAdGroup | null>(null);
  let selectedAd = $state<GoogleAd | null>(null);
  let ads = $state<GoogleAd[]>([]);
  let blacklistedIPs = $state<BlacklistedIP[]>([]);
  let negativeKeywords = $state<NegativeKeyword[]>([]);
  let aiResult = $state<AISuggestionResponse | null>(null);
  let isEditingAd = $state(false);
  
  // --- Tree View Cache States ---
  let expandedCampaigns = $state<Record<string, boolean>>({});
  let expandedAdGroups = $state<Record<string, boolean>>({});
  let campaignAdGroups = $state<Record<string, GoogleAdGroup[]>>({});
  let adGroupAds = $state<Record<string, GoogleAd[]>>({});
  let loadingCampaigns = $state<Record<string, boolean>>({});
  let loadingAdGroups = $state<Record<string, boolean>>({});
  
  let manualIP = $state('');
  let newNegativeKeyword = $state('');
  let isGlobalNegative = $state(true);
  let isGlobalIP = $state(false);
  let selectedHours = $state<number | string>(24);
  let dateFrom = $state<string | null>(null);
  let dateTo = $state<string | null>(null);
  
  let loading = $state(true);
  let reportLoading = $state(false);
  let googleLoading = $state(false);
  let googleError = $state<string | null>(null);
  let campaignLoading = $state(false);
  let campaignError = $state<string | null>(null);
  let adGroupLoading = $state(false);
  let adsLoading = $state(false);
  let aiLoading = $state(false);
  let negativeKeywordsLoading = $state(false);
  let activeTab = $state('overview');
  let campaignView = $state('list');
  
  // --- Campaign Creation ---
  let fCampaign = $state({
    name: '',
    daily_budget_vnd: 200000,
    bidding_strategy: 'MAXIMIZE_CLICKS',
    target_roas: null
  });
  let campaignSubmitting = $state(false);

  // --- Ad Group & Ad Creation ---
  let fAdGroup = $state({
    name: '',
    cpc_bid_vnd: 5000,
    keywords_raw: '',
    match_type: 'EXACT'
  });
  let adGroupSubmitting = $state(false);

  let fAd = $state({
    final_url: '',
    display_path1: '',
    display_path2: '',
    status: 'PAUSED',
    headlines: Array(15).fill(''),
    descriptions: Array(4).fill('')
  });
  let adSubmitting = $state(false);
  let aiGenerating = $state(false);
  let competitorAnalysis = $state<CompetitorAnalysisResponse | null>(null);
  let competitorAnalyzing = $state(false);
  let competitorUrl = $state('');
  let adGroupKeywords = $state<string[]>([]);

  
  
  // --- V3.0 Fast Path States ---
  let edgeStatus = $state<'idle' | 'initializing' | 'ready' | 'error'>('idle');
  let isPoWActive = $state(false);

  // --- Real-time Sync (SSE) ---
  let sse: EventSource | null = null;

  function initSSE() {
    if (sse) sse.close();
    sse = new EventSource(`${ADS_API}/stream`);
    sse.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === 'NEW_CLICK') {
          // [V3.0] HUD Sync: Toggle PoW Active status if a challenge is issued
          if (data.verdict === 'CHALLENGE' && data.challenge) {
            solvePoW(data.challenge, data.difficulty || 4).then(proof => {
              if (proof) {
                apiClient.post<GenericSuccessResponse>(`${ADS_API}/verify-pow`, {
                  ip: data.ip,
                  challenge: data.challenge,
                  nonce: proof.nonce,
                  hash: proof.hash
                }).then(() => {
                  nanobot.showToast(`🛡️ [Edge] PoW Verified for ${data.ip}`, 'success');
                  debounceFetch();
                });
              }
            });
          }

          if (data.verdict === 'FRAUD') {
            nanobot.showToast(`Phát hiện Click Tặc: ${data.ip} (Score: ${data.score})`, 'warning');
            debounceFetch();
          }
        }
      } catch (err) { console.error('SSE Error:', err); }
    };
  }

  async function initEdge() {
    edgeStatus = 'initializing';
    try {
      await behaviorEngine.init();
      edgeStatus = 'ready';
    } catch {
      edgeStatus = 'error';
    }
  }

  /**
   * [Elite V3.0] Real-world Proof-of-Work (PoW)
   * Ép các IP nghi vấn phải giải toán Hash ngầm (SHA-256)
   * Triệt tiêu tài nguyên của Botnet mà không làm phiền người dùng thật.
   */
  async function solvePoW(challenge: string, difficulty: number = 4) {
    isPoWActive = true;
    try {
      console.log(`🛡️ [PoW] Challenge received: ${challenge} (Difficulty: ${difficulty})`);
      const encoder = new TextEncoder();
      const prefix = '0'.repeat(difficulty);
      let nonce = 0;
      
      const startTime = performance.now();
      
      // Hash puzzle loop
      while (true) {
        const data = encoder.encode(challenge + nonce);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        
        if (hashHex.startsWith(prefix)) {
          const duration = (performance.now() - startTime).toFixed(0);
          console.log(`🛡️ [PoW] Solved in ${duration}ms. Nonce: ${nonce}. Hash: ${hashHex}`);
          return { nonce, hash: hashHex, duration: Number(duration) };
        }
        
        nonce++;
        // Safety break if it takes too long (> 5s)
        if (performance.now() - startTime > 5000) {
          console.warn("🛡️ [PoW] Timeout reached. Sending partial proof.");
          break;
        }
      }
      return null;
    } catch (e) {
      console.error("🛡️ [PoW] Error:", e);
      return null;
    } finally {
      isPoWActive = false;
    }
  }

  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  function debounceFetch() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fetchAll(), 5000);
  }

  function dispose() {
    if (sse) {
      sse.close();
      sse = null;
    }
    clearTimeout(debounceTimer);
  }

  // Period Label Derived
  const periodLabel = $derived.by(() => {
    if (dateFrom && dateTo) {
      const d1 = dateFrom.split('-').reverse().join('/');
      const d2 = dateTo.split('-').reverse().join('/');
      return `${d1} - ${d2}`;
    }
    if (selectedHours === 24) return '24 giờ';
    if (selectedHours === 168) return '7 ngày';
    if (selectedHours === 720) return '30 ngày';
    return `${selectedHours} giờ`;
  });

  // Computed
  const googleTotalInvalid = $derived(googleMetrics.reduce((s, m) => s + (Number(m.invalid_clicks) || 0), 0));
  const googleTotalClicks = $derived(googleMetrics.reduce((s, m) => s + (Number(m.clicks) || 0), 0));
  const googleTotalCost = $derived(googleMetrics.reduce((s, m) => s + (Number(m.cost_vnd) || 0), 0));
  const googleAvgRate = $derived(googleTotalClicks > 0 ? (googleTotalInvalid / googleTotalClicks * 100) : 0);

  // Actions
    async function fetchAll() {
      loading = true;
      try {
        const params: Record<string, string> = {};
        if (dateFrom && dateTo) {
          params.date_from = dateFrom;
          params.date_to = dateTo;
        } else {
          params.hours = String(selectedHours);
        }
        
        const [s, i, b] = await Promise.all([
          apiClient.get<FraudSummary>(`${ADS_API}/summary`, { params }),
          apiClient.get<AdInsight[]>(`${ADS_API}/insights`, { params }),
          apiClient.get<BlacklistedIP[]>(`${ADS_API}/blacklist`)
        ]);
        summary = s; 
        insights = i || []; 
        blacklistedIPs = b || [];
        
        // Luôn đồng bộ dữ liệu Google Ads khi lọc để tránh lệch số liệu giữa các tab
        await fetchGoogleMetrics();
      } catch (e) {
        console.error("Fetch error:", e);
      } finally { loading = false; }
    }

  let pastReports = $state<ReportItem[]>([]);

  function getDateRange() {
    if (dateFrom && dateTo) return { from: dateFrom, to: dateTo };
    const to = new Date(); const from = new Date();
    from.setHours(from.getHours() - Number(selectedHours || 24));
    const f = (d: Date) => d.toISOString().split('T')[0];
    return { from: f(from), to: f(to) };
  }

  async function generateReport() {
    reportLoading = true;
    try {
      const dates = getDateRange();
      let res = await apiClient.post<InvestigationReportResult>(`${ADS_API}/generate-investigation-report`, {
         date_from: dates.from,
         date_to: dates.to
      });
      
      // Nếu không có dữ liệu mới, tự động truy xuất lại dữ liệu gần nhất (Force Rebuild)
      if (res.status !== 'ready') {
         res = await apiClient.post<InvestigationReportResult>(`${ADS_API}/generate-investigation-report`, { 
            date_from: dates.from,
            date_to: dates.to,
            force: true 
         });
      }

      if (res.status === 'ready') {
        reportResult = res;
        nanobot.showToast('Báo cáo pháp y đã sẵn sàng', 'success');
        fetchPastReports(); 
      } else {
        nanobot.showToast('Không có dữ liệu gian lận trong 7 ngày qua', 'info');
      }
    } catch (error: unknown) { 
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const msg = err.response?.data?.detail || err.message || 'Lỗi truy xuất báo cáo';
      nanobot.showToast(msg, 'error'); 
      console.error("REPORT_GEN_ERROR:", error);
    }
    finally { reportLoading = false; }
  }

  async function fetchPastReports() {
     try {
        pastReports = await apiClient.get<ReportItem[]>(`${ADS_API}/investigation-reports`) || [];
     } catch { pastReports = []; }
  }

  async function viewPastReport(name: string) {
     reportLoading = true;
     try {
        const res = await apiClient.get<InvestigationReportResult>(`${ADS_API}/investigation-report-content/${name}`);
        if (res.status === 'ready') {
           reportResult = res;
           nanobot.showToast(`Đã tải hồ sơ: ${name}`, 'success');
        } else {
           nanobot.showToast('Không tìm thấy tệp hồ sơ', 'error');
        }
     } catch { nanobot.showToast('Không thể tải hồ sơ cũ', 'error'); }
     finally { reportLoading = false; }
  }

   async function fetchGoogleMetrics() {
     googleLoading = true;
     googleError = null;
     try {
       let from_str, to_str;
       if (dateFrom && dateTo) {
         from_str = dateFrom;
         to_str = dateTo;
       } else {
         const to = new Date(); const from = new Date();
         from.setHours(from.getHours() - Number(selectedHours));
         const fmtD = (d: Date) => d.toISOString().split('T')[0];
         from_str = fmtD(from);
         to_str = fmtD(to);
       }
       googleMetrics = await apiClient.get<GoogleMetric[]>(`${ADS_API}/google-metrics`, { params: { date_from: from_str, date_to: to_str } }) ?? [];
      } catch (error: unknown) {
        const err = error as { response?: { data?: { detail?: string } }; message?: string };
        googleError = err.response?.data?.detail || err.message || 'Lỗi API Google';
        nanobot.showToast(`Lỗi Google Ads Metrics: ${googleError}`, 'error');
      }
     finally { googleLoading = false; }
   }

  async function fetchCampaigns() {
    campaignLoading = true;
    campaignError = null;
    try {
      campaigns = await apiClient.get<GoogleCampaign[]>(`${ADS_API}/campaigns`) ?? [];
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      campaignError = err.response?.data?.detail || err.message || 'Lỗi tải chiến dịch';
      nanobot.showToast(`Lỗi Google Ads Campaigns: ${campaignError}`, 'error');
      campaigns = [];
    } finally { campaignLoading = false; }
  }

  async function fetchAdGroups(c: GoogleCampaign) {
    selectedCampaign = c; adGroupLoading = true; campaignView = 'ad_groups';
    try {
      const id = c.resource_name.split('/').pop();
      adGroups = await apiClient.get<GoogleAdGroup[]>(`${ADS_API}/campaigns/${id}/ad-groups`) ?? [];
    } finally { adGroupLoading = false; }
  }

  async function fetchAds(ag: GoogleAdGroup) {
    selectedAdGroup = ag; adsLoading = true; campaignView = 'ads';
    adGroupKeywords = [];
    try {
      const id = ag.resource_name.split('/').pop();
      const [adsList, kws] = await Promise.all([
        apiClient.get<GoogleAd[]>(`${ADS_API}/ad-groups/${id}/ads`),
        apiClient.get<string[]>(`${ADS_API}/ad-groups/${id}/keywords`).catch(() => [])
      ]);
      ads = adsList ?? [];
      adGroupKeywords = kws ?? [];
    } finally { adsLoading = false; }
  }

  async function toggleCampaign(c: GoogleCampaign) {
    const resourceName = c.resource_name;
    if (expandedCampaigns[resourceName]) {
      expandedCampaigns[resourceName] = false;
    } else {
      expandedCampaigns[resourceName] = true;
      selectedCampaign = c;
      if (!campaignAdGroups[resourceName]) {
        loadingCampaigns[resourceName] = true;
        try {
          const id = resourceName.split('/').pop();
          const res = await apiClient.get<GoogleAdGroup[]>(`${ADS_API}/campaigns/${id}/ad-groups`);
          campaignAdGroups[resourceName] = res ?? [];
        } catch {
          nanobot.showToast('Lỗi tải nhóm quảng cáo của chiến dịch', 'error');
        } finally {
          loadingCampaigns[resourceName] = false;
        }
      }
    }
  }

  async function toggleAdGroup(ag: GoogleAdGroup) {
    const resourceName = ag.resource_name;
    if (expandedAdGroups[resourceName]) {
      expandedAdGroups[resourceName] = false;
    } else {
      expandedAdGroups[resourceName] = true;
      selectedAdGroup = ag;
      const id = resourceName.split('/').pop();
      
      // Fetch keywords to support Ad Strength calculations
      apiClient.get<string[]>(`${ADS_API}/ad-groups/${id}/keywords`)
        .then((kws: string[] | null) => {
          adGroupKeywords = kws ?? [];
        })
        .catch(() => {});

      if (!adGroupAds[resourceName]) {
        loadingAdGroups[resourceName] = true;
        try {
          const res = await apiClient.get<GoogleAd[]>(`${ADS_API}/ad-groups/${id}/ads`);
          adGroupAds[resourceName] = res ?? [];
        } catch {
          nanobot.showToast('Lỗi tải quảng cáo của nhóm', 'error');
        } finally {
          loadingAdGroups[resourceName] = false;
        }
      }
    }
  }

  function selectAdForEdit(ad: GoogleAd, ag: GoogleAdGroup, c: GoogleCampaign) {
    selectedCampaign = c;
    selectedAdGroup = ag;
    selectedAd = ad;
    isEditingAd = true;
    
    // Fetch keywords for the selected ad group
    const id = ag.resource_name.split('/').pop();
    apiClient.get<string[]>(`${ADS_API}/ad-groups/${id}/keywords`)
      .then((kws: string[] | null) => {
        adGroupKeywords = kws ?? [];
      })
      .catch(() => {});
    
    fAd.final_url = ad.final_url || '';
    fAd.display_path1 = ad.display_path1 || ''; 
    fAd.display_path2 = ad.display_path2 || '';
    fAd.status = ad.status || 'PAUSED';
    fAd.headlines = Array(15).fill('');
    fAd.descriptions = Array(4).fill('');
    
    if (ad.headlines && Array.isArray(ad.headlines)) {
      for (let i = 0; i < Math.min(15, ad.headlines.length); i++) {
        fAd.headlines[i] = ad.headlines[i];
      }
    }
    if (ad.descriptions && Array.isArray(ad.descriptions)) {
      for (let i = 0; i < Math.min(4, ad.descriptions.length); i++) {
        fAd.descriptions[i] = ad.descriptions[i];
      }
    }
    
    campaignView = 'create_ad';
    activeTab = 'campaigns'; 
  }

  async function updateCampaignStatus(resource: string, status: string) {
    const id = resource.split('/').pop();
    if (!id) return;
    try {
      const res = await apiClient.patch<GenericSuccessResponse>(`${ADS_API}/campaigns/${id}/status`, { status });
      if (res.success) { nanobot.showToast(res.message || 'Cập nhật thành công', 'success'); fetchCampaigns(); }
    } catch { nanobot.showToast('Lỗi cập nhật', 'error'); }
  }

  async function submitCampaign() {
    if (!fCampaign.name) {
      nanobot.showToast('Vui lòng nhập tên chiến dịch', 'warning');
      return;
    }
    campaignSubmitting = true;
    try {
      const payload = {
        name: fCampaign.name,
        daily_budget_vnd: Number(fCampaign.daily_budget_vnd),
        bidding_strategy: fCampaign.bidding_strategy,
        target_roas: fCampaign.target_roas ? Number(fCampaign.target_roas) : null
      };
      const res = await apiClient.post<GenericSuccessResponse>(`${ADS_API}/campaigns`, payload);
      if (res.success) {
        nanobot.showToast(res.message || 'Khởi tạo chiến dịch thành công!', 'success');
        campaignView = 'list';
        // Reset form
        fCampaign.name = '';
        fCampaign.daily_budget_vnd = 200000;
        fCampaign.bidding_strategy = 'MAXIMIZE_CLICKS';
        fCampaign.target_roas = null;
        fetchCampaigns();
      } else {
        nanobot.showToast(res.message || 'Lỗi khởi tạo', 'error');
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const errMsg = err.response?.data?.detail || err.message || 'Lỗi kết nối API';
      nanobot.showToast(`Lỗi khởi tạo chiến dịch: ${errMsg}`, 'error');
    } finally {
      campaignSubmitting = false;
    }
  }

  async function submitAdGroup() {
    if (!selectedCampaign) {
      nanobot.showToast('Chưa chọn chiến dịch mục tiêu', 'warning');
      return;
    }
    if (!fAdGroup.name || !fAdGroup.keywords_raw) {
      nanobot.showToast('Vui lòng điền đủ Tên nhóm và Từ khóa', 'warning');
      return;
    }
    adGroupSubmitting = true;
    try {
      const keywords = fAdGroup.keywords_raw
        .split('\n')
        .map(k => k.trim())
        .filter(Boolean);
      
      const payload = {
        campaign_resource_name: selectedCampaign.resource_name,
        name: fAdGroup.name,
        cpc_bid_vnd: Number(fAdGroup.cpc_bid_vnd),
        keywords: keywords,
        match_types: [fAdGroup.match_type]
      };

      const res = await apiClient.post<GenericSuccessResponse>(`${ADS_API}/ad-groups`, payload);
      if (res.success) {
        nanobot.showToast(res.message || 'Tạo Ad Group thành công!', 'success');
        // Reset form
        fAdGroup.name = '';
        fAdGroup.keywords_raw = '';
        fAdGroup.cpc_bid_vnd = 5000;
        // Go back/refresh tree view
        const campRes = selectedCampaign.resource_name;
        expandedCampaigns[campRes] = true;
        const id = campRes.split('/').pop();
        apiClient.get<GoogleAdGroup[]>(`${ADS_API}/campaigns/${id}/ad-groups`).then((freshAg: GoogleAdGroup[] | null) => {
          campaignAdGroups[campRes] = freshAg ?? [];
        });
        campaignView = 'list';
      } else {
        nanobot.showToast(res.message || 'Lỗi tạo Ad Group', 'error');
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const errMsg = err.response?.data?.detail || err.message || 'Lỗi kết nối API';
      nanobot.showToast(`Lỗi tạo Ad Group: ${errMsg}`, 'error');
    } finally {
      adGroupSubmitting = false;
    }
  }

  async function submitAd() {
    if (!selectedAdGroup) {
      nanobot.showToast('Chưa chọn nhóm quảng cáo mục tiêu', 'warning');
      return;
    }
    // Filter out empty headlines and descriptions
    const headlines = fAd.headlines.map(h => h.trim()).filter(Boolean);
    const descriptions = fAd.descriptions.map(d => d.trim()).filter(Boolean);

    if (headlines.length < 3) {
      nanobot.showToast('Cần tối thiểu 3 Tiêu đề', 'warning');
      return;
    }
    if (descriptions.length < 2) {
      nanobot.showToast('Cần tối thiểu 2 Mô tả', 'warning');
      return;
    }
    if (!fAd.final_url) {
      nanobot.showToast('Vui lòng nhập Final URL', 'warning');
      return;
    }

    adSubmitting = true;
    try {
      const payload = {
        ad_group_resource_name: selectedAdGroup.resource_name,
        headlines,
        descriptions,
        final_url: fAd.final_url,
        display_path1: fAd.display_path1 || null,
        display_path2: fAd.display_path2 || null,
        status: fAd.status
      };

      const res = await apiClient.post<GenericSuccessResponse>(`${ADS_API}/ads`, payload);
      if (res.success) {
        nanobot.showToast(res.message || 'Tạo quảng cáo thành công!', 'success');
        
        // If editing, pause the old ad asynchronously to preserve historical data
        if (isEditingAd && selectedAd) {
          apiClient.patch<GenericSuccessResponse>(`${ADS_API}/ads/status`, {
            resource_name: selectedAd.resource_name,
            status: 'PAUSED'
          }).then((patchRes: GenericSuccessResponse | null) => {
            if (patchRes?.success) {
              nanobot.showToast('Đã tự động tạm dừng mẫu quảng cáo cũ để lưu trữ lịch sử.', 'info');
            }
          }).catch((err: unknown) => {
            console.error('Failed to pause old ad:', err);
          });
        }
        // Reset form
        fAd.final_url = '';
        fAd.display_path1 = '';
        fAd.display_path2 = '';
        fAd.status = 'PAUSED';
        fAd.headlines = Array(15).fill('');
        fAd.descriptions = Array(4).fill('');
        // Reset edit state
        isEditingAd = false;
        selectedAd = null;
        aiResult = null;
        // Go back/refresh list
        if (selectedAdGroup) {
          fetchAds(selectedAdGroup.resource_name);
          campaignView = 'ads';
        } else {
          campaignView = 'list';
        }
      } else {
        nanobot.showToast(res.message || 'Lỗi tạo mẫu quảng cáo', 'error');
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const errMsg = err.response?.data?.detail || err.message || 'Lỗi kết nối API';
      nanobot.showToast(`Lỗi tạo quảng cáo: ${errMsg}`, 'error');
    } finally {
      adSubmitting = false;
    }
  }

  async function aiSuggestRSA(url: string) {
    if (!url) {
      nanobot.showToast('Vui lòng nhập Final URL trước khi nhờ Xohi gợi ý', 'warning');
      return;
    }
    aiGenerating = true;
    try {
      const res = await apiClient.post<AISuggestionResponse>(`${ADS_API}/ai-suggest`, {
        task: 'RSA',
        context: url,
        ad_group_resource_name: selectedAdGroup?.resource_name
      });
      if (res.success) {
        nanobot.showToast(res.message || 'Xohi gợi ý thành công!', 'success');
        aiResult = res; // [NEW] Lưu kết quả gợi ý bao gồm độ mạnh quảng cáo
        if (res.headlines && Array.isArray(res.headlines)) {
          for (let i = 0; i < 15; i++) {
            fAd.headlines[i] = res.headlines[i] || '';
          }
        }
        if (res.descriptions && Array.isArray(res.descriptions)) {
          for (let i = 0; i < 4; i++) {
            fAd.descriptions[i] = res.descriptions[i] || '';
          }
        }
        if (res.display_path1) {
          fAd.display_path1 = res.display_path1;
        }
        if (res.display_path2) {
          fAd.display_path2 = res.display_path2;
        }
      } else {
        nanobot.showToast(res.message || 'Lỗi gợi ý AI', 'error');
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const errMsg = err.response?.data?.detail || err.message || 'Lỗi kết nối API';
      nanobot.showToast(`Lỗi gợi ý Xohi: ${errMsg}`, 'error');
    } finally {
      aiGenerating = false;
    }
  }


  async function analyzeCompetitor(url: string) {
    let targetUrl = url?.trim();
    if (!targetUrl) {
      targetUrl = fAd.final_url?.trim();
    }
    if (!targetUrl) {
      nanobot.showToast('Vui lòng nhập URL đối thủ hoặc Final URL để phân tích', 'warning');
      return;
    }
    competitorUrl = targetUrl; // Sync back to UI input field
    competitorAnalyzing = true;
    competitorAnalysis = null;
    try {
      const res = await apiClient.post<CompetitorAnalysisResponse>(`${ADS_API}/ai-competitor-research`, {
        url: targetUrl,
        ad_group_resource_name: selectedAdGroup?.resource_name
      });
      if (res.success) {
        competitorAnalysis = res;
        // Tự động áp dụng display paths nếu chưa có
        if (!fAd.display_path1 && res.recommended_display_path1) {
          fAd.display_path1 = res.recommended_display_path1;
        }
        if (!fAd.display_path2 && res.recommended_display_path2) {
          fAd.display_path2 = res.recommended_display_path2;
        }
        nanobot.showToast('Phân tích hoàn tất!', 'success');
      } else {
        nanobot.showToast(res.message || 'Phân tích thất bại', 'error');
      }
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } }; message?: string };
      const errMsg = err.response?.data?.detail || err.message || 'Lỗi kết nối API';
      nanobot.showToast(`Lỗi phân tích: ${errMsg}`, 'error');
    } finally {
      competitorAnalyzing = false;
    }
  }

  function importKeyword(kw: string) {
    // Thêm từ khóa vào headlines nếu còn chỗ trống
    const emptyIdx = fAd.headlines.findIndex(h => !h.trim());
    if (emptyIdx !== -1) {
      fAd.headlines[emptyIdx] = kw;
      fAd.headlines = [...fAd.headlines]; // Kích hoạt tính phản ứng Svelte 5
      nanobot.showToast(`Đã thêm "${kw}" vào tiêu đề #${emptyIdx + 1}`, 'success');
    } else {
      nanobot.showToast('Tất cả 15 tiêu đề đã đầy', 'warning');
    }
  }


   async function fetchNegativeKeywords() {
     negativeKeywordsLoading = true;
     try {
       const id = selectedCampaign?.resource_name.split('/').pop();
       negativeKeywords = await apiClient.get<NegativeKeyword[]>(`${ADS_API}/negative-keywords`) ?? [];
       if (id) {
         const campK = await apiClient.get<NegativeKeyword[]>(`${ADS_API}/campaigns/${id}/negative-keywords`) ?? [];
         negativeKeywords = [...negativeKeywords, ...campK];
       }
     } catch { negativeKeywords = []; }
     finally { negativeKeywordsLoading = false; }
   }

  async function addNegativeKeyword(text: string) {
    if (!text.trim()) return;
    const keywords = text.split('\n').map(k => k.trim()).filter(Boolean);
    try {
      let res: GenericSuccessResponse;
      if (isGlobalNegative) {
        res = await apiClient.post<GenericSuccessResponse>(`${ADS_API}/negative-keywords`, { keywords });
      } else {
        if (!selectedCampaign) {
          nanobot.showToast('Vui lòng chọn chiến dịch', 'warning');
          return;
        }
        const id = selectedCampaign.resource_name.split('/').pop();
        if (!id) return;
        res = await apiClient.post<GenericSuccessResponse>(`${ADS_API}/campaigns/${id}/negative-keywords`, { keywords });
      }
      if (res.success) { nanobot.showToast(`Đã xuất bản ${keywords.length} từ khóa`, 'success'); fetchNegativeKeywords(); newNegativeKeyword = ''; }
    } catch { nanobot.showToast("Lỗi API", "error"); }
  }

  async function removeNegativeKeyword(resource: string) {
    const id = resource.split('/').pop();
    if (!id) return;
    try {
      const res = await apiClient.delete<GenericSuccessResponse>(`${ADS_API}/negative-keywords/${id}`);
      if (res.success) { nanobot.showToast(res.message || 'Đã xóa thành công', 'success'); fetchNegativeKeywords(); }
    } catch { nanobot.showToast('Lỗi xóa', 'error'); }
  }

  async function blockIP(ip: string, reason = 'Phát hiện click fraud') {
    try {
      const id = selectedCampaign?.resource_name.split('/').pop();
      const res = await apiClient.post<GenericSuccessResponse>(`${ADS_API}/blacklist`, { ip, reason, campaign_id: id, is_global: isGlobalIP });
      if (res.success) { nanobot.showToast(res.message || 'Đã chặn IP thành công', 'success'); fetchAll(); }
    } catch { nanobot.showToast('Lỗi chặn IP', 'error'); }
  }

  async function unblockIP(ip: string) {
    try {
      const res = await apiClient.delete<GenericSuccessResponse>(`${ADS_API}/blacklist/${ip}`);
      if (res.success) { nanobot.showToast(res.message || 'Đã gỡ chặn thành công', 'success'); fetchAll(); }
    } catch { nanobot.showToast('Lỗi gỡ chặn', 'error'); }
  }

  async function aiSuggest(task: string, context: string) {
    aiLoading = true;
    try {
      const res = await apiClient.post<AISuggestionResponse>(`${ADS_API}/ai-suggest`, { task, context });
      if (res.success) {
         aiResult = res;
         if (task === 'NEGATIVE_KEYWORDS' && res.negative_keywords) {
            newNegativeKeyword = res.negative_keywords.join('\n');
         }
         nanobot.showToast(res.message || 'Xohi đã gợi ý xong', 'success');
      } else {
         nanobot.showToast(res.message || 'Lỗi phân tích AI', 'error');
      }
    } catch {
       nanobot.showToast('Lỗi kết nối Trinity Bridge', 'error');
    } finally { aiLoading = false; }
  }

  const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(Math.round(n));
  const priorityColor = (p: string) => p === 'HIGH' ? '#ff3e5e' : p === 'MEDIUM' ? '#fbbf24' : '#10b981';
  const isBlacklisted = (ip: string) => blacklistedIPs.some(i => i.ip === ip);

  return {
    get summary() { return summary }, get insights() { return insights }, get reportResult() { return reportResult },
    get googleMetrics() { return googleMetrics }, get campaigns() { return campaigns }, 
    get selectedCampaign() { return selectedCampaign }, set selectedCampaign(v) { selectedCampaign = v },
    get adGroups() { return adGroups }, 
    get selectedAdGroup() { return selectedAdGroup }, set selectedAdGroup(v) { selectedAdGroup = v },
    get selectedAd() { return selectedAd }, set selectedAd(v) { selectedAd = v },
    get ads() { return ads }, get negativeKeywords() { return negativeKeywords },
    get blacklistedIPs() { return blacklistedIPs },
    get aiResult() { return aiResult },
    get pastReports() { return pastReports },
    get loading() { return loading }, get activeTab() { return activeTab }, set activeTab(v) { activeTab = v },
    get campaignView() { return campaignView }, set campaignView(v) { campaignView = v },
    get isGlobalNegative() { return isGlobalNegative }, set isGlobalNegative(v) { isGlobalNegative = v },
    get newNegativeKeyword() { return newNegativeKeyword }, set newNegativeKeyword(v) { newNegativeKeyword = v },
    get isGlobalIP() { return isGlobalIP }, set isGlobalIP(v) { isGlobalIP = v },
    get manualIP() { return manualIP }, set manualIP(v) { manualIP = v },
    get selectedHours() { return selectedHours }, set selectedHours(v) { selectedHours = v },
    get dateFrom() { return dateFrom }, set dateFrom(v) { dateFrom = v },
    get dateTo() { return dateTo }, set dateTo(v) { dateTo = v },
    get reportLoading() { return reportLoading }, get googleLoading() { return googleLoading }, get aiLoading() { return aiLoading },
    get negativeKeywordsLoading() { return negativeKeywordsLoading },
    get googleTotalCost() { return googleTotalCost }, 
    get googleAvgRate() { return googleAvgRate },
    get googleTotalClicks() { return googleTotalClicks },
    get googleTotalInvalid() { return googleTotalInvalid },
    get googleError() { return googleError },
    get campaignError() { return campaignError },
    get periodLabel() { return periodLabel },
    get fCampaign() { return fCampaign }, set fCampaign(v) { fCampaign = v },
    get campaignSubmitting() { return campaignSubmitting },
    get fAdGroup() { return fAdGroup }, set fAdGroup(v) { fAdGroup = v },
    get adGroupSubmitting() { return adGroupSubmitting },
    get fAd() { return fAd }, set fAd(v) { fAd = v },
    get adSubmitting() { return adSubmitting },
    get aiGenerating() { return aiGenerating },
    get isEditingAd() { return isEditingAd }, set isEditingAd(v) { isEditingAd = v },
    get expandedCampaigns() { return expandedCampaigns }, set expandedCampaigns(v) { expandedCampaigns = v },
    get expandedAdGroups() { return expandedAdGroups }, set expandedAdGroups(v) { expandedAdGroups = v },
    get campaignAdGroups() { return campaignAdGroups }, set campaignAdGroups(v) { campaignAdGroups = v },
    get adGroupAds() { return adGroupAds }, set adGroupAds(v) { adGroupAds = v },
    get loadingCampaigns() { return loadingCampaigns },
    get loadingAdGroups() { return loadingAdGroups },
    get competitorAnalysis() { return competitorAnalysis }, set competitorAnalysis(v) { competitorAnalysis = v },
    get competitorAnalyzing() { return competitorAnalyzing },
    get competitorUrl() { return competitorUrl }, set competitorUrl(v) { competitorUrl = v },
    get adGroupKeywords() { return adGroupKeywords }, set adGroupKeywords(v) { adGroupKeywords = v },
    fmt, priorityColor, isBlacklisted, fetchAll, generateReport, fetchGoogleMetrics, fetchCampaigns, fetchAdGroups, fetchAds, 
    updateCampaignStatus, submitCampaign, submitAdGroup, submitAd, aiSuggestRSA, analyzeCompetitor, importKeyword, fetchNegativeKeywords, addNegativeKeyword, removeNegativeKeyword, blockIP, unblockIP, aiSuggest, fetchPastReports, viewPastReport,
    getDateRange,
    initSSE, initEdge, solvePoW, dispose,
    get edgeStatus() { return edgeStatus },
    get isPoWActive() { return isPoWActive },
    toggleCampaign, toggleAdGroup, selectAdForEdit
  };
}
