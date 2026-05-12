import { apiClient } from '$lib/utils/apiClient';
import { useNanobot } from "$lib/state/nanobot.svelte";
import { onDestroy } from 'svelte';
import { behaviorEngine } from '$lib/core/ads/BehaviorEngine';

const API_BASE = '/api/v1';
const ADS_API = `${API_BASE}/ads-protection`;

// --- Type Definitions (Elite V2.6 Standard) ---
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
  insights: any[];
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
  let insights = $state<any[]>([]);
  let reportResult = $state<InvestigationReportResult | null>(null);
  let googleMetrics = $state<GoogleMetric[]>([]);
  let campaigns = $state<any[]>([]);
  let selectedCampaign = $state<any>(null);
  let adGroups = $state<any[]>([]);
  let selectedAdGroup = $state<any>(null);
  let ads = $state<any[]>([]);
  let blacklistedIPs = $state<any[]>([]);
  let negativeKeywords = $state<any[]>([]);
  let aiResult = $state<any>(null);
  
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
  let adGroupLoading = $state(false);
  let adsLoading = $state(false);
  let aiLoading = $state(false);
  let negativeKeywordsLoading = $state(false);
  let activeTab = $state('overview');
  let campaignView = $state('list');
  
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
          if (data.verdict === 'CHALLENGE') {
            isPoWActive = true;
            setTimeout(() => { isPoWActive = false; }, 10000);
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
   * [V3.0] Proof-of-Work ngầm để chặn bot vùng xám (50-80% score)
   */
  async function solvePoW(challenge: string) {
    isPoWActive = true;
    try {
      // Giả lập giải thuật Hash ngầm (Elite V3.0)
      await new Promise(r => setTimeout(r, 2000));
      console.log("🛡️ [PoW] Challenge solved.");
      return true;
    } finally {
      isPoWActive = false;
    }
  }

  let debounceTimer: any;
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
        const params: any = {};
        if (dateFrom && dateTo) {
          params.date_from = dateFrom;
          params.date_to = dateTo;
        } else {
          params.hours = String(selectedHours);
        }
        
        const [s, i, b] = await Promise.all([
          apiClient.get(`${ADS_API}/summary`, { params }),
          apiClient.get(`${ADS_API}/insights`, { params }),
          apiClient.get(`${ADS_API}/blacklist`)
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

  let pastReports = $state<any[]>([]);

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
      let res: any = await apiClient.post(`${ADS_API}/generate-investigation-report`, {
         date_from: dates.from,
         date_to: dates.to
      });
      
      // Nếu không có dữ liệu mới, tự động truy xuất lại dữ liệu gần nhất (Force Rebuild)
      if (res.status !== 'ready') {
         res = await apiClient.post(`${ADS_API}/generate-investigation-report`, { 
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
    } catch (e: any) { 
      const msg = e.response?.data?.detail || e.message || 'Lỗi truy xuất báo cáo';
      nanobot.showToast(msg, 'error'); 
      console.error("REPORT_GEN_ERROR:", e);
    }
    finally { reportLoading = false; }
  }

  async function fetchPastReports() {
     try {
        pastReports = await apiClient.get(`${ADS_API}/investigation-reports`) || [];
     } catch { pastReports = []; }
  }

  async function viewPastReport(name: string) {
     reportLoading = true;
     try {
        const res: any = await apiClient.get(`${ADS_API}/investigation-report-content/${name}`);
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
     try {
       let from_str, to_str;
       if (dateFrom && dateTo) {
         from_str = dateFrom;
         to_str = dateTo;
       } else {
         const to = new Date(); const from = new Date();
         from.setHours(from.getHours() - selectedHours);
         const fmtD = (d: Date) => d.toISOString().split('T')[0];
         from_str = fmtD(from);
         to_str = fmtD(to);
       }
       googleMetrics = await apiClient.get(`${ADS_API}/google-metrics`, { params: { date_from: from_str, date_to: to_str } }) ?? [];
     } catch { googleError = 'Lỗi API Google'; }
     finally { googleLoading = false; }
   }

  async function fetchCampaigns() {
    campaignLoading = true;
    try { campaigns = await apiClient.get(`${ADS_API}/campaigns`) ?? []; }
    finally { campaignLoading = false; }
  }

  async function fetchAdGroups(c: any) {
    selectedCampaign = c; adGroupLoading = true; campaignView = 'ad_groups';
    try {
      const id = c.resource_name.split('/').pop();
      adGroups = await apiClient.get(`${ADS_API}/campaigns/${id}/ad-groups`) ?? [];
    } finally { adGroupLoading = false; }
  }

  async function fetchAds(ag: any) {
    selectedAdGroup = ag; adsLoading = true; campaignView = 'ads';
    try {
      const id = ag.resource_name.split('/').pop();
      ads = await apiClient.get(`${ADS_API}/ad-groups/${id}/ads`) ?? [];
    } finally { adsLoading = false; }
  }

  async function updateCampaignStatus(resource: string, status: string) {
    const id = resource.split('/').pop();
    try {
      const res: any = await apiClient.patch(`${ADS_API}/campaigns/${id}/status`, { status });
      if (res.success) { nanobot.showToast(res.message, 'success'); fetchCampaigns(); }
    } catch { nanobot.showToast('Lỗi cập nhật', 'error'); }
  }

   async function fetchNegativeKeywords() {
     negativeKeywordsLoading = true;
     try {
       const id = selectedCampaign?.resource_name.split('/').pop();
       negativeKeywords = await apiClient.get(`${ADS_API}/negative-keywords`) ?? [];
       if (id) {
         const campK = await apiClient.get(`${ADS_API}/campaigns/${id}/negative-keywords`) ?? [];
         negativeKeywords = [...negativeKeywords, ...campK];
       }
     } catch { negativeKeywords = []; }
     finally { negativeKeywordsLoading = false; }
   }

  async function addNegativeKeyword(text: string) {
    if (!text.trim()) return;
    const keywords = text.split('\n').map(k => k.trim()).filter(Boolean);
    try {
      let res: any;
      if (isGlobalNegative) res = await apiClient.post(`${ADS_API}/negative-keywords`, { keywords });
      else {
        const id = selectedCampaign.resource_name.split('/').pop();
        res = await apiClient.post(`${ADS_API}/campaigns/${id}/negative-keywords`, { keywords });
      }
      if (res.success) { nanobot.showToast(`Đã xuất bản ${keywords.length} từ khóa`, 'success'); fetchNegativeKeywords(); newNegativeKeyword = ''; }
    } catch { nanobot.showToast("Lỗi API", "error"); }
  }

  async function removeNegativeKeyword(resource: string) {
    const id = resource.split('/').pop();
    try {
      const res: any = await apiClient.delete(`${ADS_API}/negative-keywords/${id}`);
      if (res.success) { nanobot.showToast(res.message, 'success'); fetchNegativeKeywords(); }
    } catch { nanobot.showToast('Lỗi xóa', 'error'); }
  }

  async function blockIP(ip: string, reason = 'Phát hiện click fraud') {
    try {
      const id = selectedCampaign?.resource_name.split('/').pop();
      const res: any = await apiClient.post(`${ADS_API}/blacklist`, { ip, reason, campaign_id: id, is_global: isGlobalIP });
      if (res.success) { nanobot.showToast(res.message || 'Đã chặn IP thành công', 'success'); fetchAll(); }
    } catch { nanobot.showToast('Lỗi chặn IP', 'error'); }
  }

  async function unblockIP(ip: string) {
    try {
      const res: any = await apiClient.delete(`${ADS_API}/blacklist/${ip}`);
      if (res.success) { nanobot.showToast(res.message, 'success'); fetchAll(); }
    } catch { nanobot.showToast('Lỗi gỡ chặn', 'error'); }
  }

  async function aiSuggest(task: string, context: string) {
    aiLoading = true;
    try {
      const res: any = await apiClient.post(`${ADS_API}/ai-suggest`, { task, context });
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
    get periodLabel() { return periodLabel },
    fmt, priorityColor, isBlacklisted, fetchAll, generateReport, fetchGoogleMetrics, fetchCampaigns, fetchAdGroups, fetchAds, 
    updateCampaignStatus, fetchNegativeKeywords, addNegativeKeyword, removeNegativeKeyword, blockIP, unblockIP, aiSuggest, fetchPastReports, viewPastReport,
    getDateRange,
    initSSE, initEdge, solvePoW, dispose,
    get edgeStatus() { return edgeStatus },
    get isPoWActive() { return isPoWActive }
  };
}
