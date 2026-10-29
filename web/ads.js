/* Google Ad Manager adapter. Default: no actual ads / no generated revenue.
 * Rewarded ads require clear, affirmative user opt-in. The click happens in
 * app.js before this module is asked to request and show the rewarded ad.
 * These client events are NOT secure server-side reward verification. */
window.SNAP_ADS = (() => {
  const cfg = window.SNAP_CONFIG?.ads || {};
  const live = Boolean(cfg.enabled && cfg.rewardedAdUnit);
  let scriptPromise;
  const load = () => {
    if (!live) return Promise.resolve(false);
    if (!scriptPromise) {
      scriptPromise = new Promise((resolve) => {
        window.googletag = window.googletag || { cmd: [] };
        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://securepubads.g.doubleclick.net/tag/js/gpt.js';
        script.onload = () => resolve(true);
        script.onerror = () => resolve(false);
        document.head.appendChild(script);
      });
    }
    return scriptPromise;
  };
  async function watchRewardedAd() {
    if (!live || !(await load())) return 'unavailable';
    return new Promise((resolve) => {
      let finished = false;
      let slot = null;
      let timer;
      let listeners = [];
      const finish = (result) => {
        if (finished) return;
        finished = true;
        clearTimeout(timer);
        try {
          for (const [name, callback] of listeners) googletag.pubads().removeEventListener(name,callback);
          if (slot) googletag.destroySlots([slot]);
        } catch (_) {}
        resolve(result);
      };
      window.googletag.cmd.push(() => {
        if (finished) return;
        try {
          const g = window.googletag;
          slot = g.defineOutOfPageSlot(cfg.rewardedAdUnit, g.enums.OutOfPageFormat.REWARDED);
          if (!slot) {finish('unavailable');return;}
          slot.addService(g.pubads());
          const listen = (name, fn) => {g.pubads().addEventListener(name,fn);listeners.push([name,fn]);};
          listen('rewardedSlotReady', event => {
            if (event.slot === slot) {
              clearTimeout(timer);
              timer = setTimeout(() => finish('declined'), 180000);
              // User already opted in by choosing "Watch ad & download".
              const shown = event.makeRewardedVisible();
              if (!shown) finish('unavailable');
            }
          });
          listen('rewardedSlotGranted', event => {if(event.slot === slot) finish('granted');});
          listen('rewardedSlotClosed', event => {if(event.slot === slot) finish('declined');});
          listen('slotRenderEnded', event => {if(event.slot === slot && event.isEmpty) finish('unavailable');});
          g.enableServices();
          g.display(slot);
          timer = setTimeout(() => finish('unavailable'), 12000); // No fill/blocked. Never fake ad completion.
        } catch (_) {finish('unavailable');}
      });
    });
  }
  async function setupBanner() {
    if (!live || !cfg.bannerAdUnit || !(await load())) return;
    window.googletag.cmd.push(() => {
      try {
        const container = document.getElementById('banner-ad');
        if (!container) return;
        const g = window.googletag;
        const mapping = g.sizeMapping().addSize([760,0],[[728,90]]).addSize([0,0],[[320,50]]).build();
        const slot = g.defineSlot(cfg.bannerAdUnit,[[728,90],[320,50]],'banner-ad');
        if (!slot) return;
        slot.defineSizeMapping(mapping).addService(g.pubads());
        container.replaceChildren();
        container.style.border='none';
        g.enableServices();
        g.display('banner-ad');
      } catch (_) {}
    });
  }
  return {live,watchRewardedAd,setupBanner};
})();
