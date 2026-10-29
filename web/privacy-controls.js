(function () {
  'use strict';
  const key = 'snapmedia_privacy_v1';
  const version = 1;
  const footer = document.querySelector('.footer-links');
  if (!footer) return;

  function readChoice() {
    try {
      const value = JSON.parse(localStorage.getItem(key) || 'null');
      return value && value.version === version ? value : null;
    } catch (_) {
      return null;
    }
  }
  function saveChoice(analytics, advertising) {
    const choice = { version, analytics, advertising, savedAt: new Date().toISOString() };
    try { localStorage.setItem(key, JSON.stringify(choice)); } catch (_) { /* Browsing still works. */ }
    banner.hidden = true;
    if (dialog.open) dialog.close();
  }

  const privacyLink = document.createElement('button');
  privacyLink.type = 'button';
  privacyLink.className = 'privacy-footer-link';
  privacyLink.lang = 'en';
  privacyLink.textContent = 'Privacy choices';
  footer.append(privacyLink);

  const banner = document.createElement('section');
  banner.className = 'privacy-banner';
  banner.lang = 'en';
  banner.dir = 'ltr';
  banner.setAttribute('aria-label', 'Privacy choices');
  banner.hidden = true;
  banner.innerHTML = '<strong>Your privacy choices</strong><p>SnapMedia remembers your language and privacy choice. Analytics and advertising are currently off. We will ask again before adding any new provider.</p><div class="privacy-actions"><button type="button" data-privacy="reject">Reject optional</button><button type="button" data-privacy="accept">Accept optional</button><button type="button" data-privacy="manage">Manage</button></div><a href="/cookies">Read the Cookie Policy</a>';
  document.body.append(banner);

  const dialog = document.createElement('dialog');
  dialog.className = 'privacy-dialog';
  dialog.lang = 'en';
  dialog.dir = 'ltr';
  dialog.setAttribute('aria-label', 'Manage privacy choices');
  dialog.innerHTML = '<div class="privacy-dialog-inner"><h2>Manage privacy choices</h2><p>Language and privacy-choice storage support the interface. No analytics or advertising scripts are active. These optional choices do not enable them; we will ask again if providers are added.</p><label><input type="checkbox" checked disabled> Essential interface storage</label><label><input type="checkbox" id="privacy-analytics"> Analytics, if introduced later</label><label><input type="checkbox" id="privacy-advertising"> Advertising, if introduced later</label><div class="privacy-actions"><button type="button" data-privacy="save">Save choices</button><button type="button" data-privacy="close">Close</button></div><a href="/cookies">Read the Cookie Policy</a></div>';
  document.body.append(dialog);

  function openDialog() {
    const current = readChoice();
    dialog.querySelector('#privacy-analytics').checked = Boolean(current?.analytics);
    dialog.querySelector('#privacy-advertising').checked = Boolean(current?.advertising);
    dialog.showModal();
  }
  privacyLink.addEventListener('click', openDialog);
  banner.addEventListener('click', event => {
    const action = event.target.closest('[data-privacy]')?.dataset.privacy;
    if (action === 'reject') saveChoice(false, false);
    if (action === 'accept') saveChoice(true, true);
    if (action === 'manage') openDialog();
  });
  dialog.addEventListener('click', event => {
    const action = event.target.closest('[data-privacy]')?.dataset.privacy;
    if (action === 'save') saveChoice(dialog.querySelector('#privacy-analytics').checked, dialog.querySelector('#privacy-advertising').checked);
    if (action === 'close') dialog.close();
  });
  if (!readChoice()) banner.hidden = false;
})();
