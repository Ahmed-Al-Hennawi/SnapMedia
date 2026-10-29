# AdSense readiness and inactive placements

The visible advertisement spaces are **placeholders only**. They have no links, scripts, tracking, publisher ID, or ad requests. Each space can be turned off independently in `web/ads-config.js`. The file also reserves fields for a future publisher ID and slot IDs, but filling them in does **not** activate ads.

## Policy blocker

Google's [Publisher Policies](https://support.google.com/adsense/answer/10502938?hl=en) give as an example of disallowed content “pages that assist or enable users to download streaming videos if prohibited by the content provider.” [YouTube's terms](https://uk.youtube.com/t/terms) restrict downloading and automated access except in specified circumstances. The current SnapMedia downloader has not been approved by YouTube or the other platforms. A user permission statement alone does not give the site operator platform permission. **Do not enable AdSense on this downloader on the strength of these placeholders.** Obtain specialist legal and policy review and any necessary platform authorisations first. A separate site with original educational content and no prohibited download function may be a more realistic monetisation option.

## What to do if eligibility is established later

1. Choose the final domain and verify ownership in AdSense. Hostinger is the intended domain provider; the web host and its privacy/logging settings still need confirmation.
2. Have the site and each intended ad placement reviewed against the current Google Publisher Policies and platform terms. Keep ads away from download buttons and navigation, and avoid ad units on pages with little original content.
3. For UK/EEA/Swiss users, select a [Google-certified CMP with IAB TCF support](https://support.google.com/adsense/answer/13554116?hl=en-GB) as required by Google's then-current rules. The site's simple privacy-choice panel is **not** such a CMP. Implement Consent Mode v2 as appropriate, with denied defaults before any tags and consent-aware loading; test with Tag Assistant. Re-prompt users when introducing actual advertising providers. Do not treat previously saved placeholder preferences as ad consent.
4. Use the exact publisher ID, ad slot IDs, and `ads.txt` line supplied by your approved AdSense account. See `docs/ads.txt.example` for format only. Publish the real `ads.txt` at the domain root and verify it returns HTTP 200. There is deliberately no live `/ads.txt` template with a fake ID.
5. Update the Privacy and Cookie Policies with the actual vendors, storage, purposes, legal bases, transfers, and retention periods before loading any ad script. Test consent withdrawal and mobile layouts.
6. Only then add and review a separate consent-aware ad loader. None is included in this version because an inactive placeholder must not turn into a live ad through a configuration typo.

Google [does not guarantee site approval](https://support.google.com/adsense/answer/10502938?hl=en), and these preparations do not imply that SnapMedia qualifies.
