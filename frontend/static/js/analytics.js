(function(){
  try {
    var orgSetAttr = Element.prototype.setAttribute;
    Element.prototype.setAttribute = function(name, value) {
      if (typeof name === 'string' && name.toLowerCase() === 'attributionsrc') {
        return;
      }
      return orgSetAttr.apply(this, arguments);
    };

    var orgSetAttrNS = Element.prototype.setAttributeNS;
    Element.prototype.setAttributeNS = function(ns, name, value) {
      if (typeof name === 'string' && name.toLowerCase() === 'attributionsrc') {
        return;
      }
      return orgSetAttrNS.apply(this, arguments);
    };

    var orgSetAttrNode = Element.prototype.setAttributeNode;
    Element.prototype.setAttributeNode = function(node) {
      if (node && typeof node.name === 'string' && node.name.toLowerCase() === 'attributionsrc') {
        return node;
      }
      return orgSetAttrNode.apply(this, arguments);
    };

    if (typeof window.fetch === 'function') {
      var orgFetch = window.fetch;
      window.fetch = function(input, init) {
        if (init && typeof init === 'object') {
          try {
            delete init.attributionReporting;
          } catch(e) {}
        }
        return orgFetch.apply(this, arguments);
      };
    }

    if (typeof window.Request === 'function') {
      var orgRequest = window.Request;
      window.Request = function(input, init) {
        if (init && typeof init === 'object') {
          try {
            delete init.attributionReporting;
          } catch(e) {}
        }
        return new orgRequest(input, init);
      };
      window.Request.prototype = orgRequest.prototype;
    }

    var targets = [
      { proto: typeof Request !== 'undefined' && Request.prototype, prop: 'attributionReporting' },
      { proto: typeof HTMLAnchorElement !== 'undefined' && HTMLAnchorElement.prototype, prop: 'attributionSrc' },
      { proto: typeof HTMLImageElement !== 'undefined' && HTMLImageElement.prototype, prop: 'attributionSrc' },
      { proto: typeof HTMLScriptElement !== 'undefined' && HTMLScriptElement.prototype, prop: 'attributionSrc' },
      { proto: typeof HTMLAreaElement !== 'undefined' && HTMLAreaElement.prototype, prop: 'attributionSrc' }
    ];
    targets.forEach(function(t) {
      if (t.proto) {
        try {
          delete t.proto[t.prop];
        } catch(e) {}
        try {
          Object.defineProperty(t.proto, t.prop, {
            configurable: false,
            enumerable: true,
            get: function() { return undefined; },
            set: function() {}
          });
        } catch(e) {}
      }
    });
  } catch (e) {}

  function isAdminZone() {
    try {
      var h = window.location.hostname;
      return h.indexOf('admin.') !== -1 || window.location.search.indexOf('admin') !== -1;
    } catch (e) {}
    return false;
  }

  if (isAdminZone()) {
    try {
      var raw = sessionStorage.getItem('primary_config');
      if (raw) {
        var seo = JSON.parse(raw).seo_analytics;
        if (seo) {
          if (seo.google_analytics_id) {
            window['ga-disable-' + seo.google_analytics_id] = true;
          }
          if (seo.google_tag_manager_id) {
            window['ga-disable-' + seo.google_tag_manager_id] = true;
          }
        }
      }
    } catch (e) {}
    return;
  }

  try {
    var cookieDesc = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie') ||
                     Object.getOwnPropertyDescriptor(HTMLDocument.prototype, 'cookie');
    if (cookieDesc && cookieDesc.set) {
      var rawSet = cookieDesc.set;
      var rawGet = cookieDesc.get;
      Object.defineProperty(document, 'cookie', {
        configurable: true,
        enumerable: true,
        get: function() {
          return rawGet.call(document);
        },
        set: function(val) {
          if (typeof val === 'string') {
            var parts = val.split(';').map(function(s) { return s.trim(); }).filter(Boolean);
            var seen = {};
            var cleaned = [parts[0]];
            for (var i = 1; i < parts.length; i++) {
              var key = parts[i].split('=')[0].toLowerCase();
              if (!seen[key]) {
                seen[key] = true;
                cleaned.push(parts[i]);
              }
            }
            val = cleaned.join('; ');
            var matchGa = parts[0].match(/^\s*(_ga(_[A-Za-z0-9_]+)?)=([^;]+)/);
            if (matchGa) {
              var current = rawGet.call(document) || '';
              if (current.indexOf(matchGa[1] + '=' + matchGa[3]) !== -1) {
                return;
              }
            }
          }
          rawSet.call(document, val);
        }
      });
    }
  } catch(e) {}

  try {
    var origWarn = console.warn;
    console.warn = function() {
      var msg = arguments[0];
      if (typeof msg === 'string' && (
        msg.indexOf('test_cookie') !== -1 ||
        msg.indexOf('doubleclick.net') !== -1 ||
        msg.indexOf('Partitioned') !== -1
      )) {
        return;
      }
      origWarn.apply(console, arguments);
    };
  } catch(e) {}

  var CONFIG_KEY = 'primary_config';

  function isNotEmpty(val) {
    return typeof val === 'string' && val.trim().length > 0 && val !== 'null' && val !== 'undefined' && val !== '0' && !/^[Xx]+$/.test(val.trim());
  }

  function isValidPixelId(val) {
    return isNotEmpty(val) && /^\d{9,16}$/.test(val.trim());
  }

  window.dataLayer = window.dataLayer || [];
  function gtag(){ window.dataLayer.push(arguments); }
  window.gtag = gtag;

  gtag('js', new Date());
  gtag('set', 'cookie_update', false);
  gtag('set', { 'cookie_update': false });
  gtag('set', 'cookie_flags', 'SameSite=None;Secure;Partitioned');

  function initGTM(gtmId) {
    if (!isNotEmpty(gtmId) || window.__gtm_loaded__) return;
    window.__gtm_loaded__ = true;
    window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
    var f = document.getElementsByTagName('script')[0],
        j = document.createElement('script');
    j.async = true;
    j.src = 'https://www.googletagmanager.com/gtm.js?id=' + gtmId;
    f.parentNode.insertBefore(j, f);
  }

  function initGA(gaId) {
    if (!isNotEmpty(gaId) || window.__ga_id__ === gaId) return;
    if (!window.__ga_loaded__) {
      window.__ga_loaded__ = true;
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://www.googletagmanager.com/gtag/js?id=' + gaId;
      document.head.appendChild(s);
    }
    window.__ga_id__ = gaId;
    window.gtag('config', gaId, {
      cookie_update: false,
      cookie_flags: 'SameSite=None;Secure;Partitioned',
      allow_display_features: false
    });
  }

  function initGSC(gscId) {
    if (!isNotEmpty(gscId)) return;
    if (document.querySelector('meta[name="google-site-verification"]')) return;
    var meta = document.createElement('meta');
    meta.name = 'google-site-verification';
    meta.content = gscId;
    document.head.appendChild(meta);
  }

  function initFB(pixelId) {
    if (!isValidPixelId(pixelId) || window.__fb_loaded__) return;
    window.__fb_loaded__ = true;
    (function(f,b,e,v,n,t,s) {
      if(f.fbq)return;n=f.fbq=function(){n.callMethod?
      n.callMethod.apply(n,arguments):n.queue.push(arguments)};
      if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
      n.queue=[];t=b.createElement(e);t.async=!0;
      t.src=v;s=b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t,s)
    })(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    window.fbq('init', pixelId);
    window.fbq('track', 'PageView');
  }

  function loadAnalytics(seo) {
    if (!seo) return;
    var hasGTM = isNotEmpty(seo.google_tag_manager_id);
    initGTM(seo.google_tag_manager_id);
    if (!hasGTM) {
      initGA(seo.google_analytics_id);
    }
    initGSC(seo.google_search_console_id);
    initFB(seo.facebook_pixel_id);
  }

  function syncAndRun() {
    try {
      var localData = sessionStorage.getItem(CONFIG_KEY);
      if (localData) {
        var parsed = JSON.parse(localData);
        loadAnalytics(parsed.seo_analytics);
      }
    } catch (e) {}

    try {
      fetch('/api/v1/client/settings/primary', { cache: 'no-store' })
        .then(function(res) { return res.ok ? res.json() : null; })
        .then(function(data) {
          if (data) {
            try {
              sessionStorage.setItem(CONFIG_KEY, JSON.stringify(data));
            } catch (e) {}
            loadAnalytics(data.seo_analytics);
          }
        })
        .catch(function() {});
    } catch(e) {}
  }

  var isTriggered = false;
  function triggerTrackers() {
    if (isTriggered) return;
    isTriggered = true;
    var events = ['touchstart', 'scroll', 'click', 'mousemove'];
    events.forEach(function(e) {
      window.removeEventListener(e, triggerTrackers, { passive: true });
    });
    syncAndRun();
  }

  function scheduleTrackers() {
    var events = ['touchstart', 'scroll', 'click', 'mousemove'];
    events.forEach(function(e) {
      window.addEventListener(e, triggerTrackers, { passive: true });
    });
    setTimeout(triggerTrackers, 3500);
  }

  if (document.readyState === 'complete') {
    scheduleTrackers();
  } else {
    window.addEventListener('load', scheduleTrackers);
  }
})();
