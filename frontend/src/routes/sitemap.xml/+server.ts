/**
 * Elite V2.2: Dynamic XML Sitemap — GEO 2026
 *
 * Generates sitemap.xml from backend API data.
 * Scope: Products + Categories + Articles (per Sếp's directive).
 *
 * AI Search engines (Perplexity, ChatGPT, Gemini) crawl sitemaps
 * to discover and index content for citation.
 */
import type { RequestHandler } from './$types';
import { ServerEnv } from '$lib/server/env';

interface SitemapUrl {
    loc: string;
    lastmod?: string;
    changefreq: string;
    priority: string;
}

const SITE_URL = `https://${ServerEnv.APP_DOMAIN}`;

export const GET: RequestHandler = async ({ fetch }) => {
    const apiUrl = ServerEnv.INTERNAL_API_URL;
    const tenantId = ServerEnv.TENANT_ID;
    const headers = { 'x-tenant': tenantId };

    const urls: SitemapUrl[] = [];

    // ── Static Pages ──────────────────────────────────────────────────────
    urls.push({
        loc: `${SITE_URL}/home`,
        changefreq: 'daily',
        priority: '1.0',
    });

    urls.push({
        loc: `${SITE_URL}/products`,
        changefreq: 'daily',
        priority: '0.8',
    });

    // ── Products ──────────────────────────────────────────────────────────
    try {
        const res = await fetch(`${apiUrl}/api/v1/client/products/?limit=500&status=ACTIVE`, {
            headers,
            signal: AbortSignal.timeout(10000),
        });
        if (res.ok) {
            const data = await res.json();
            const products = data.data || [];
            for (const product of products) {
                if (product.slug) {
                    urls.push({
                        loc: `${SITE_URL}/${product.slug}`,
                        lastmod: product.created_at
                            ? new Date(product.created_at).toISOString().split('T')[0]
                            : undefined,
                        changefreq: 'weekly',
                        priority: '0.8',
                    });
                }
            }
        }
    } catch (e) {
        console.error('[SITEMAP] Failed to fetch products:', e);
    }

    // ── Categories ────────────────────────────────────────────────────────
    try {
        const res = await fetch(`${apiUrl}/api/v1/client/home/category/all`, {
            headers,
            signal: AbortSignal.timeout(5000),
        });
        // Fallback: try alternative endpoint
        if (!res.ok) {
            const altRes = await fetch(`${apiUrl}/api/v1/admin/categories`, {
                headers,
                signal: AbortSignal.timeout(5000),
            });
            if (altRes.ok) {
                const data = await altRes.json();
                const categories = data.data || data || [];
                for (const cat of categories) {
                    if (cat.slug) {
                        urls.push({
                            loc: `${SITE_URL}/${cat.slug}/`,
                            changefreq: 'weekly',
                            priority: '0.7',
                        });
                    }
                }
            }
        } else {
            const data = await res.json();
            const categories = data.data || data || [];
            for (const cat of categories) {
                if (cat.slug) {
                    urls.push({
                        loc: `${SITE_URL}/${cat.slug}/`,
                        changefreq: 'weekly',
                        priority: '0.7',
                    });
                }
            }
        }
    } catch (e) {
        console.error('[SITEMAP] Failed to fetch categories:', e);
    }

    // ── Articles ──────────────────────────────────────────────────────────
    try {
        const res = await fetch(`${apiUrl}/api/v1/client/news`, {
            headers,
            signal: AbortSignal.timeout(5000),
        });
        if (res.ok) {
            const data = await res.json();
            const articles = Array.isArray(data) ? data : (data.data || data.items || []);

            // Articles listing page
            if (articles.length > 0) {
                urls.push({
                    loc: `${SITE_URL}/bai-viet`,
                    changefreq: 'weekly',
                    priority: '0.6',
                });
            }

            for (const article of articles) {
                if (article.slug) {
                    urls.push({
                        loc: `${SITE_URL}/${article.slug}`,
                        lastmod: article.created_at
                            ? new Date(article.created_at).toISOString().split('T')[0]
                            : undefined,
                        changefreq: 'monthly',
                        priority: '0.6',
                    });
                }
            }
        }
    } catch (e) {
        console.error('[SITEMAP] Failed to fetch articles:', e);
    }

    // ── Build XML ─────────────────────────────────────────────────────────
    const xml = buildSitemapXml(urls);

    return new Response(xml, {
        headers: {
            'Content-Type': 'application/xml',
            'Cache-Control': 'public, max-age=3600, s-maxage=3600',
        },
    });
};

function buildSitemapXml(urls: SitemapUrl[]): string {
    const urlEntries = urls
        .map((u) => {
            let entry = `  <url>\n    <loc>${escapeXml(u.loc)}</loc>`;
            if (u.lastmod) entry += `\n    <lastmod>${u.lastmod}</lastmod>`;
            entry += `\n    <changefreq>${u.changefreq}</changefreq>`;
            entry += `\n    <priority>${u.priority}</priority>`;
            entry += `\n  </url>`;
            return entry;
        })
        .join('\n');

    return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlEntries}
</urlset>`;
}

function escapeXml(str: string): string {
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}
