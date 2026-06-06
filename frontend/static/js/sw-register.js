if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    try {
      const registration = await navigator.serviceWorker.register("/sw.js");
      console.log("SW registered with scope:", registration.scope);
    } catch (err) {
      if (err.name === 'SecurityError' || err.message.includes('SSL certificate')) {
        console.warn(
          "%c[SSL ERROR]%c Service Worker registration failed due to untrusted certificate.\n" +
          "Please run 'bash scripts/setup-ssl.sh' and follow instructions to trust the Root CA.",
          "color: white; background: red; font-weight: bold; padding: 2px 4px; border-radius: 2px;",
          "color: red; font-weight: bold;"
        );
      } else {
        console.warn("SW registration failed: ", err);
      }
    }
  });
}
