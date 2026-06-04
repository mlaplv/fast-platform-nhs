/**
 * ClickShield.js — Google Ads Click Fraud Defense
 * Triển khai trên landing page osmo.vn qua GTM Custom HTML Tag
 *
 * Luồng:
 *   1. Parse GCLID từ URL → đây là paid click từ Google Ads
 *   2. Thu thập fingerprint (device + behavior) trong 5 giây
 *   3. Gửi lên /api/v1/ads-protection/validate-click
 *   4. Nếu verdict === "FRAUD" → block conversion pixel
 *
 * Chú ý: KHÔNG lưu PII. Chỉ gửi technical signals.
 */

(function (window, document) {
  "use strict";

  // -------------------------------------------------------------------------
  // Config — điều chỉnh theo domain thực tế
  // -------------------------------------------------------------------------
  var CONFIG = {
    apiEndpoint: "https://api.osmo.vn/api/v1/ads-protection/validate-click",
    collectionWindowMs: 5000,   // Thu thập behavior trong 5 giây
    gtmFraudEventName: "click_fraud_detected",
    gtmCleanEventName: "click_validated_clean",
    debug: false,               // Bật true khi dev/staging
  };

  // -------------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------------
  function getParam(name) {
    try {
      return new URLSearchParams(window.location.search).get(name);
    } catch (_) {
      return null;
    }
  }

  function log() {
    if (CONFIG.debug && window.console) {
      console.log.apply(console, ["[ClickShield]"].concat(Array.prototype.slice.call(arguments)));
    }
  }

  // -------------------------------------------------------------------------
  // Fingerprint collector
  // -------------------------------------------------------------------------
  var _state = {
    gclid: getParam("gclid"),
    campaignId: getParam("campaignid"),     // UTM / auto-tagging
    adGroupId: getParam("adgroupid"),
    keyword: getParam("keyword"),
    startTime: Date.now(),
    mouseEvents: 0,
    touchEvents: 0,
    keyEvents: 0,
    maxScrollDepth: 0,
    webdriverDetected: false,
  };

  // Nếu không có GCLID → không phải paid click → exit early
  if (!_state.gclid) {
    log("No GCLID found — not a paid click, skipping.");
    return;
  }

  log("GCLID detected:", _state.gclid, "— starting collection.");

  // -------------------------------------------------------------------------
  // Event listeners — đếm tương tác
  // -------------------------------------------------------------------------
  function _onMouse()  { _state.mouseEvents++; }
  function _onTouch()  { _state.touchEvents++; }
  function _onKey()    { _state.keyEvents++;   }
  function _onScroll() {
    var scrolled   = window.scrollY || document.documentElement.scrollTop;
    var docHeight  = document.documentElement.scrollHeight - window.innerHeight;
    if (docHeight > 0) {
      var depth = Math.round((scrolled / docHeight) * 100);
      if (depth > _state.maxScrollDepth) _state.maxScrollDepth = depth;
    }
  }

  document.addEventListener("mousemove", _onMouse, { passive: true });
  document.addEventListener("touchstart", _onTouch, { passive: true });
  document.addEventListener("keydown", _onKey, { passive: true });
  window.addEventListener("scroll", _onScroll, { passive: true });

  // -------------------------------------------------------------------------
  // Webdriver / headless detection
  // -------------------------------------------------------------------------
  _state.webdriverDetected = (
    navigator.webdriver === true
    || !!window.callPhantom
    || !!window._phantom
    || !!window.__nightmare
    || !!document.__selenium_unwrapped
  );

  // -------------------------------------------------------------------------
  // Build payload & send after collection window
  // -------------------------------------------------------------------------
    // -------------------------------------------------------------------------
    // [V3.0] Conversion Insurance & PoW
    // -------------------------------------------------------------------------
    function detectHighIntent() {
      var patterns = ['checkout', 'pricing', 'cart', 'order', 'booking', 'contact'];
      var url = window.location.href.toLowerCase();
      var referrer = (document.referrer || "").toLowerCase();
      return patterns.some(function(p){ return url.indexOf(p) !== -1 || referrer.indexOf(p) !== -1; });
    }

    async function solvePoW(challenge) {
      log("Solving PoW challenge:", challenge);
      var start = Date.now();
      // Giả lập tính toán Hash (Elite V3.0 Protocol)
      // Trong thực tế sẽ là một vòng lặp tìm nonce cho SHA-256
      var count = 0;
      while (Date.now() - start < 1500) { count++; } 
      return "pow_result_" + challenge + "_" + count;
    }

    async function submitClick(extraData) {
      var payload = {
        gclid:         _state.gclid,
        campaign_id:   _state.campaignId,
        ad_group_id:   _state.adGroupId,
        keyword:       _state.keyword,
        ip_address:    "",
        user_agent:    navigator.userAgent,
        referrer:      document.referrer || null,
        landing_url:   window.location.href,
        session_duration_ms:   Date.now() - _state.startTime,
        scroll_depth_percent:  _state.maxScrollDepth,
        mouse_events_count:    _state.mouseEvents,
        touch_events_count:    _state.touchEvents,
        key_events_count:      _state.keyEvents,
        screen_width:      screen.width,
        screen_height:     screen.height,
        webdriver_detected: _state.webdriverDetected,
        is_high_intent:    detectHighIntent(),
        pow_solution:      extraData ? extraData.solution : null
      };

      try {
        var res = await fetch(CONFIG.apiEndpoint, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify(payload),
          keepalive: true
        });
        var data = await res.json();
        
        log("Server response:", data);

        if (data.verdict === "CHALLENGE" && !payload.pow_solution) {
          log("🛡️ Challenge received. Activating PoW...");
          var solution = await solvePoW(data.challenge_id || "default");
          return submitClick({ solution: solution });
        }

        if (data.verdict === "FRAUD") {
          window.__clickShieldBlocked = true;
          if (window.dataLayer) {
            window.dataLayer.push({
              event: CONFIG.gtmFraudEventName,
              fraud_score: data.fraud_score,
              gclid: _state.gclid
            });
          }
          log("⛔ FRAUD detected — conversion pixel BLOCKED.");
        } else {
          window.__clickShieldBlocked = false;
          if (window.dataLayer) {
            window.dataLayer.push({
              event: CONFIG.gtmCleanEventName,
              fraud_score: data.fraud_score,
              verdict: data.verdict
            });
          }
          log("✅ Click validated clean — verdict:", data.verdict);
        }
      } catch (err) {
        log("API error — failing open:", err);
        window.__clickShieldBlocked = false;
      }
    }

    // Nếu phát hiện High-intent, gửi ngay không cần đợi
    if (detectHighIntent()) {
      log("💎 High-intent detected. Instant submission.");
      submitClick();
    } else {
      setTimeout(submitClick, CONFIG.collectionWindowMs);
    }

}(window, document));

// ============================================================
// GTM CONVERSION TAG GUARD
// Thêm trigger điều kiện vào Google Ads Conversion Tag trong GTM:
//
// Trigger: Custom Event — "click_validated_clean"
//   + Blocking trigger: Custom Event — "click_fraud_detected"
//
// Hoặc dùng Custom JavaScript Variable trong GTM:
//
//   function() {
//     return window.__clickShieldBlocked !== true;
//   }
//
// Set variable này làm trigger điều kiện cho conversion tag.
// ============================================================
