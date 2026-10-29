# SnapMedia launch and growth guide

The current site is a single-process Flask service. Its visible design and download flow are unchanged by the optimization work. This guide covers the settings that need a real public host or account.

## Launch checklist

1. Choose one HTTPS domain (including whether to use `www`). Redirect the other host and HTTP to that address at your reverse proxy.
2. Set `SNAPMEDIA_SITE_URL` to the chosen origin, for example `https://your-domain.example`. Do not include a path or trailing slash. This drives canonical links, Open Graph URLs, `robots.txt`, and `sitemap.xml` without trusting a visitor's Host header. Check all three public pages after deployment.
3. Put Gunicorn behind a trusted HTTPS reverse proxy. Set `SNAPMEDIA_TRUSTED_PROXY_COUNT` to the **exact** number of proxies that set `X-Forwarded-For` and `X-Forwarded-Proto`; leave it at `0` otherwise. A wrong value can let clients spoof their IP for rate limits. Configure HTTPS, redirects and HSTS at the proxy after HTTPS works.
4. Keep one Gunicorn worker process until job state and files are moved out of process. Use writable temporary storage with room for source and converted copies; three 300 MB jobs can temporarily use considerably more than 900 MB. Monitor disk usage, CPU, memory, queue saturation, error rates and FFmpeg failures. Keep access logs free of query strings containing user media links if possible.
5. At the proxy or CDN, restrict outbound server network access and add distributed rate limits. App URL checks cannot fully prevent server-side request forgery if a supported platform redirects an extractor to a private address. Permit required platform and media CDN traffic, then test each provider. Do not cache `/api/` responses; the app marks them `no-store`. Static assets may be cached for one hour and HTML for five minutes; purge stale CDN assets when deploying a release.
6. Review the Terms and Privacy wording against the actual hosting provider, jurisdiction, logging, retention and any future advertising. The current legal text explicitly identifies itself as a draft. Add required operator details and get legal review before treating it as final.
7. Recheck a current public media URL from each platform after deployment. External platforms can change formats, access rules or anti-bot behavior at any time. The `/api/health` route checks local tools, not external platform availability.

## Search setup

The public URLs are `/`, `/terms`, and `/privacy`. `/index.html`, `/terms.html`, and `/privacy.html` redirect to these routes. The server emits self-referencing canonicals and a `WebSite` site-name JSON-LD block on the home page when `SNAPMEDIA_SITE_URL` is set. The sitemap contains only those three public URLs. The robots file excludes `/api/` and points to the sitemap. No `noindex` is set on the public pages.

After the real site is live:

1. Open `https://your-domain.example/robots.txt` and `https://your-domain.example/sitemap.xml`. Confirm the listed URLs use your chosen HTTPS host and that each page returns HTTP 200. Inspect a public page's source to confirm its canonical matches its final URL.
2. In [Google Search Console](https://search.google.com/search-console/about), add a **Domain** property for the domain and verify ownership using the DNS TXT record Google supplies. If DNS access is unavailable, use a URL-prefix property and one of its offered verification methods. Submit `https://your-domain.example/sitemap.xml` in **Sitemaps**. Use **URL Inspection** for the home page, then monitor **Pages**, **Performance**, and **Core Web Vitals**. Google says a sitemap helps discovery but does not guarantee indexing or rankings.
3. In [Bing Webmaster Tools](https://www.bing.com/webmasters/), import the verified Search Console property, or add and verify the site manually. Submit the same sitemap under **Sitemaps** if it was not imported. Use **URL Inspection** and **Site Explorer** to track crawl and indexing errors.
4. IndexNow is optional for a small site with three mostly stable URLs. If future content changes frequently, register an IndexNow key and submit changed URLs according to its protocol. It is not a replacement for Google Search Console or the sitemap.

The language selector changes content at the same URL in the browser. There are no separate crawlable language URLs, so do not add `hreflang` until real localized page URLs exist. Search engines may choose their own title or snippet even when metadata is supplied. The `WebSite` block expresses the preferred site name; it does not promise a rich result.

## Search topics and content plan

| Page | Main topic | Related searches to serve naturally |
| --- | --- | --- |
| `/` | Save permitted public videos as MP4 or MP3 | public video downloader, TikTok video download, Instagram Reel download, YouTube Shorts download, Facebook video download, MP4 video, MP3 audio |
| `/terms` | SnapMedia usage terms | permitted downloads, copyright responsibilities, supported content |
| `/privacy` | SnapMedia privacy practices | temporary download retention, link processing, language preference |

The homepage title and description describe the actual tool and formats. Existing FAQ and step text explain limits and permitted use without keyword stuffing. The legal pages have distinct titles and descriptions and include English content directly in HTML for crawlers and no-JavaScript visitors.

Potential future content, if you decide to add pages: original platform-specific tutorials, supported formats and quality limits, troubleshooting for inaccessible public links, and a plain-language guide to permission and copyright. Link these from the homepage and related guides. Share genuinely useful guides with relevant communities or creators for earned links; do not buy links or produce mass-generated near-duplicate pages. Compare Search Console queries, impressions, clicks, average position, and indexing trends monthly, then improve pages whose intent or information is weak.

## Performance and capacity

The logo now uses a lossless WebP copy in browsers that support it, with the original PNG retained as a fallback and social preview. The WebP file is 666,870 bytes versus 1,146,260 bytes for PNG (42% fewer bytes); decoded RGB pixels were compared and matched exactly. The about image is lazy loaded and has fixed intrinsic dimensions. CSS and JavaScript are deferred or loaded normally as before. Static responses have one-hour cache headers; HTML has five-minute cache headers and ETags. Cleanup no longer scans download folders on every request. API responses remain uncached.

The expensive operations are third-party extraction, media transfer and H.264/AAC conversion. A single process allows at most three concurrent jobs and limits each visitor to 12 information checks and 6 download starts per minute. These limits protect the current small deployment; they do not establish a daily visitor capacity. For materially larger traffic, use a durable shared queue, dedicated download/transcode workers, shared object storage with expiring links, distributed rate limiting, CDN delivery for static files, and hosting-level outbound network policy. Measure CPU seconds, bandwidth and disk per job before sizing workers or promising throughput. A separate static frontend is possible later but does not remove the media processing cost.

Run PageSpeed Insights on the live HTTPS site for mobile and desktop, then inspect real-user Core Web Vitals in Search Console. The useful targets are LCP at or below 2.5 seconds, INP at or below 200 ms, and CLS at or below 0.1 at the 75th percentile. Local file sizes and tests are not a substitute for field measurements.

## Security and future advertising

The application validates allowed HTTPS platform hosts, limits request size and expensive actions, uses random job IDs, serves downloads with `no-store`, and sends CSP, frame, content-type, referrer and permissions headers. There is no database, so SQL injection is not applicable. Existing UI code uses DOM text nodes for media titles. The content security policy permits the existing Google Fonts and remote media thumbnails. Keep FFmpeg, Node, Python packages and operating system packages updated, and rerun `pip-audit --local` in the deployed environment after installation. Use hosting logs and alerts for 429/5xx responses, queue saturation, storage exhaustion and repeated extractor failures. Temporary files need no backup; back up source code and deployment configuration.

No advertising or tracking code was added. AdSense approval depends on Google's current policies, original useful content and a live site review. Before applying, ensure the legal and privacy pages reflect the real deployment, consider whether additional original content is needed, and plan consent controls where required. If ads are added later, reserve space for units so they do not shift the layout and load scripts only after the required privacy choices. The current design intentionally contains no ad slots.

## Sources

- [Google: build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google: canonical URL guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google: site name structured data](https://developers.google.com/search/docs/appearance/site-names)
- [Google: Search Console guide](https://developers.google.com/search/docs/monitor-debug/search-console-start)
- [Google: Core Web Vitals](https://developers.google.com/search/docs/appearance/core-web-vitals)
- [Bing: add and verify a site](https://www2.bing.com/webmasters/help/add-and-verify-site-12184f8b)
- [Bing: submit sitemaps](https://www2.bing.com/webmasters/help/sitemaps-3b5cf6ed)
- [Google: AdSense eligibility](https://support.google.com/adsense/answer/9724/eligibility-requirements-for-adsense)
