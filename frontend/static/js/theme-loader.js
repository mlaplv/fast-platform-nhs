(function() {
  try {
    var h = window.location.hostname;
    var isAdmin = h.indexOf('admin.') !== -1 || window.location.search.indexOf('admin') !== -1;
    var lastBg = localStorage.getItem('last_bg_color');
    var isDark = isAdmin || lastBg === '#020202' || lastBg === '#010101';
    if (isDark) {
      document.documentElement.classList.add('admin-theme');
    }
  } catch (e) {}
})();
