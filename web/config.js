// Swap in a real Google Ad Manager rewarded ad unit only after publisher approval.
// Do NOT put API secrets here; this file is public.
window.SNAP_CONFIG = {
  ads: {
    enabled: false,                     // Demo mode by default
    rewardedAdUnit: '',                 // e.g. '/1234567/snapmedia_rewarded'
    bannerAdUnit: '',                   // e.g. '/1234567/snapmedia_banner'
  },
  apiBase: '',                          // Same-origin Python backend
};
