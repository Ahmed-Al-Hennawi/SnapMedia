# SnapMedia production audit

Reviewed 29 October 2026 against branch baseline `7d05c27`. This records what the source code does and which deployment facts still need confirmation. It is a technical assessment, not a legal opinion or a claim of compliance.

## Current architecture and data flow

- Flask serves the site, legal pages, API, robots file, and sitemap. yt-dlp extracts metadata and downloads the source to `instance/downloads/<job-id>/`. FFmpeg creates MP3 or playable H.264/AAC MP4 output. The app serves the resulting file from its own server and normally deletes it after about one hour. Downloads are **not** sent directly from the source platform to the visitor.
- Job state, rate limits, and files are local to one process. There is no account system or database. The browser stores the chosen language in `localStorage` and may fetch Google Fonts and source-platform thumbnail images. Hostinger is intended for the domain. The web host, proxy, and access logs are outside the repository and have not been identified or inspected.
- The source permits four platform host families. Its direct URL check does not constrain redirects or every media request made by yt-dlp. The current code does not request platform credentials or implement a DRM bypass.

## Highest-priority decisions before launch

| Priority | Finding | Safe next action |
| --- | --- | --- |
| Critical | Google's publisher policy explicitly includes pages that help download streaming videos when the provider prohibits that activity among examples it will not monetize. YouTube's terms restrict downloads and automated access unless an exception applies. Meta describes automated collection without permission as a terms violation; the exact application of each platform's current UK terms and SnapMedia's methods needs specialist review. A permission statement on SnapMedia does not grant platform permission. | Keep AdSense disabled. Seek specialist review or written platform permissions before trying to monetize the downloader. A separate original-content site with no prohibited download function may be a more suitable monetization route. |
| High | yt-dlp may follow provider redirects or media URLs beyond the hostname initially checked by SnapMedia. This leaves a server-side request forgery (SSRF) exposure until outbound network policy and redirect validation are proven. | Restrict outbound destinations at the hosting layer and test provider traffic; a complete code-side fix would touch the protected download path and needs a separate decision. |
| High | The current privacy draft lacks a complete verified operator, hosting, log-retention, transfer, and complaint description. | Confirm the hosting provider, jurisdiction, log settings, and operator details; have the published policies reviewed before launch. |
| High | The in-memory job store and local files cannot safely serve multiple independent workers; a process restart loses active jobs. Conversion can use substantial CPU, disk, and bandwidth. | Keep one worker, monitor capacity, and load-test before making visitor-volume claims. A shared queue and storage would be a future architecture project. |
| Medium | Current SEO routes and metadata depend on `SNAPMEDIA_SITE_URL`, which has not yet been chosen. | Set the final HTTPS origin before publishing; verify canonical URLs, robots file, sitemap, and search-console ownership. |
| Medium | There is no production host or Google publisher account in this repository, so live logs, headers at the proxy, cookie behavior of third parties, AdSense eligibility, and real traffic capacity are unverified. | Audit the deployed host and provider settings when chosen. |

## Security observations

The app has a direct HTTPS platform-host allowlist, short JSON body limit, request limits, random job IDs, content security policy and other response headers, and subprocess calls that pass argument arrays rather than a shell command. It returns generic extractor errors to visitors. These are useful controls, but they do not prove the service is secure. In particular, the initial URL allowlist does not control every downstream yt-dlp request; rate limits are per process; and an unguessable job URL functions as a temporary bearer link. There is no authenticated state-changing form, so conventional account CSRF is not the main concern; unauthenticated abuse and resource exhaustion are.

## Traffic and performance limits

The process permits at most three active download jobs, with each job potentially doing network transfer and CPU-heavy conversion. No production workload or host size has been measured, so there is no justified visitor-capacity claim. For planning only, 1,000, 10,000, and 100,000 daily visits average roughly 0.7, 6.9, and 69 visits per minute over a full day; actual peaks and downloads per visitor can be much higher. The single-process design might handle the smallest case with sufficient hardware and light use, but even that needs load testing. The larger cases call for a queue, dedicated workers, shared job state and file storage, distributed rate limits, and measured bandwidth/CPU budgets. Page caching and image optimization help browsing performance but do not remove conversion cost. Test the live site’s mobile Core Web Vitals and accessibility after choosing a host.

The existing test suite passed at audit start: **27 tests**. A local `pip-audit --local` check completed against the public vulnerability database and reported **no known vulnerabilities in the installed environment** on 29 October 2026. This is not a guarantee about future advisories or a different deployment; rerun it in CI and on the production environment.

## Privacy and consent notes

SnapMedia processes submitted URLs, metadata, output choices, IP addresses for in-process rate limiting, temporary media files, and support email requests if a visitor contacts the operator. Google Fonts and remote thumbnails may disclose visitor network details to third parties. The existing code does not load analytics or AdSense scripts. A consent preference saved now cannot be treated as informed consent to future, unspecified advertising vendors or purposes. Any eventual Google ad integration for UK/EEA/Swiss visitors needs the then-current Google-certified CMP/TCF requirements and a fresh review of the actual deployment.

## Official references

- [YouTube Terms of Service](https://uk.youtube.com/t/terms)
- [TikTok EEA/UK Terms of Service](https://www.tiktok.com/legal/page/eea/terms-of-service/en) (linked for operator review; direct page access was blocked during this audit)
- [Meta on unauthorized automated collection](https://about.fb.com/news/2021/04/how-we-combat-scraping/)
- [Google Publisher Policies](https://support.google.com/adsense/answer/10502938?hl=en)
- [Google consent-management requirements](https://support.google.com/adsense/answer/13554020?hl=en)
- [ICO cookie and storage guidance](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-the-use-of-storage-and-access-technologies/how-do-we-manage-consent-in-practice)
- [ICO privacy-information checklist](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/what-privacy-information-should-we-provide/)
- [UK government copyright guidance](https://www.gov.uk/using-somebody-elses-intellectual-property/copyright)
