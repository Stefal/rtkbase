(() => {
  'use strict';
  const key = 'rtkbase-theme';
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  const valid = value => ['light', 'dark', 'system'].includes(value);
  let preference = 'system';
  try { const saved = localStorage.getItem(key); if (valid(saved)) preference = saved; } catch (_) {}
  function apply() {
    const theme = preference === 'system' ? (media.matches ? 'dark' : 'light') : preference;
    document.documentElement.dataset.theme = theme;
    window.dispatchEvent(new Event('rtkbase-theme-change'));
  }
  apply();
  media.addEventListener('change', () => { if (preference === 'system') apply(); });
  window.addEventListener('storage', event => {
    if (event.key === key) { preference = valid(event.newValue) ? event.newValue : 'system'; apply(); }
  });
  document.addEventListener('DOMContentLoaded', () => {
    const select = document.getElementById('interface-theme');
    if (!select) return;
    select.value = preference;
    select.addEventListener('change', () => {
      if (!valid(select.value)) return;
      preference = select.value;
      try { localStorage.setItem(key, preference); } catch (_) {}
      apply();
    });
    window.addEventListener('storage', () => { select.value = preference; });
  });
})();
