(function () {
  'use strict';
  const placement = window.SNAP_AD_PLACEMENTS;
  if (!placement?.show) return;
  function space(name, type) {
    const area = document.createElement('aside');
    area.className = `ad-placeholder ad-placeholder-${type}`;
    area.setAttribute('aria-label', 'Inactive advertisement space');
    area.dataset.placement = name;
    const label = document.createElement('span');
    label.textContent = 'ADVERTISEMENT';
    const note = document.createElement('small');
    note.textContent = 'Space reserved for future ads';
    area.append(label, note);
    return area;
  }
  const header = document.querySelector('.site-header');
  const hero = document.querySelector('.hero');
  const legal = document.querySelector('.legal-content');
  if (hero) {
    if (placement.show.header && header) header.after(space('header', 'header'));
    if (placement.show.afterDownloader) hero.after(space('afterDownloader', 'downloader'));
  }
  if (legal && placement.show.legalBottom && ['/terms', '/privacy', '/copyright', '/cookies'].includes(location.pathname)) {
    legal.after(space('legalBottom', 'legal'));
  }
})();
