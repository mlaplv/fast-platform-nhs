const CACHE_NAME = "xohi-pwa-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Simple pass-through fetch to fulfill PWA requirements
  event.respondWith(
    fetch(event.request).catch(() => new Response("Offline", { status: 503 })),
  );
});
