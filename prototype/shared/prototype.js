/* =====================================================================
 * WayTum Prototype — Shared JavaScript
 * Navigation · typing sim · auto-advance · keyboard shortcuts
 * ===================================================================== */
(function () {
  'use strict';

  const SCREEN_ORDER = [
    '01-landing.html',
    '02-vision.html',
    '03-blockers.html',
    '04-ground.html',
    '05-commitment.html',
    '06-swarm.html',
    '07-reveal.html',
    '08-course.html',
    '09-course-stepin.html',
    '10-review.html',
    '11-submitted.html',
    '12-event.html',
    '13-event-stepin.html',
    '14-person.html',
    '15-person-stepin.html',
    '16-scholarship.html',
    '17-opportunity-detail.html',
    '18-profile.html',
    '19-vision-refresh.html'
  ];

  let autoAdvanceTimer = null;
  const DEFAULT_AUTO_MS = 4500;

  // ---- Navigation ----
  function currentIndex() {
    const path = window.location.pathname.split('/').pop();
    const idx = SCREEN_ORDER.indexOf(path);
    return idx === -1 ? 0 : idx;
  }

  function navTo(url) {
    if (!url) return;
    clearTimeout(autoAdvanceTimer);
    document.body.classList.add('exiting');
    setTimeout(() => { window.location.href = url; }, 120);
  }

  function navNext() {
    const idx = currentIndex();
    if (idx < SCREEN_ORDER.length - 1) navTo(SCREEN_ORDER[idx + 1]);
  }
  function navPrev() {
    const idx = currentIndex();
    if (idx > 0) navTo(SCREEN_ORDER[idx - 1]);
  }
  function navRestart() { navTo(SCREEN_ORDER[0]); }

  // Auto-advance is DISABLED by design — the user drives the flow.
  // scheduleAdvance() is a no-op kept for backward compatibility.
  function scheduleAdvance() { /* no-op — manual navigation only */ }
  function cancelAdvance() { clearTimeout(autoAdvanceTimer); }

  // ---- Typing simulation ----
  function typeInto(target, text, opts) {
    opts = opts || {};
    const baseMs = opts.speed || 45;
    return new Promise((resolve) => {
      const el = typeof target === 'string' ? document.querySelector(target) : target;
      if (!el) { resolve(); return; }
      let i = 0;
      // Preserve cursor
      const useCursor = opts.cursor !== false;
      if (el.tagName === 'INPUT') {
        el.value = '';
        el.focus();
        function step() {
          if (i >= text.length) return resolve();
          const ch = text[i++];
          el.value += ch;
          const pause = (ch === '.' || ch === ',' || ch === '\n') ? 180 : 0;
          setTimeout(step, baseMs + Math.random() * 30 + pause);
        }
        step();
      } else {
        el.innerHTML = useCursor ? '<span class="typed"></span><span class="cursor"></span>' : '';
        const typed = el.querySelector('.typed') || el;
        function step() {
          if (i >= text.length) {
            if (useCursor) {
              const c = el.querySelector('.cursor');
              if (c) setTimeout(() => c.remove(), 400);
            }
            return resolve();
          }
          const ch = text[i++];
          typed.textContent += ch;
          const pause = (ch === '.' || ch === ',' || ch === '\n') ? 180 : 0;
          setTimeout(step, baseMs + Math.random() * 30 + pause);
        }
        step();
      }
    });
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // ---- Timer (mm:ss) ----
  function startTimer(el, startSec) {
    if (!el) return null;
    let s = startSec || 0;
    function fmt(s) {
      const m = Math.floor(s / 60); const r = s % 60;
      return m + ':' + String(r).padStart(2, '0');
    }
    el.textContent = fmt(s);
    const h = setInterval(() => { s++; el.textContent = fmt(s); }, 1000);
    return h;
  }

  // ---- Demo controls (restart + keyboard hint) ----
  function mountDemoControls() {
    const bar = document.createElement('div');
    bar.className = 'demo-controls';
    bar.innerHTML = [
      '<span>◀ ▶ keys · </span>',
      '<button data-nav="prev">Prev</button>',
      '<span class="sep">·</span>',
      '<button data-nav="next">Next</button>',
      '<span class="sep">·</span>',
      '<button data-nav="restart">Restart</button>'
    ].join('');
    document.body.appendChild(bar);
  }

  function bindKeys() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight') {
        cancelAdvance();
        // Per-screen override: set window.WP_RIGHT = 'xx.html' to skip step-ins
        if (window.WP_RIGHT) navTo(window.WP_RIGHT);
        else navNext();
      }
      else if (e.key === 'ArrowLeft') {
        cancelAdvance();
        if (window.WP_LEFT) navTo(window.WP_LEFT);
        else navPrev();
      }
      else if (e.key === 'r' || e.key === 'R') navRestart();
    });
  }

  function bindDelegation() {
    document.addEventListener('click', (e) => {
      const a = e.target.closest('[data-nav]');
      if (!a) return;
      const to = a.dataset.nav;
      cancelAdvance();
      e.preventDefault();
      if (to === 'next') navNext();
      else if (to === 'prev') navPrev();
      else if (to === 'restart') navRestart();
      else navTo(to);
    });
  }

  // Build a canonical status bar (9:41 · icons)
  function buildStatusBar(opts) {
    opts = opts || {};
    const dark = !!opts.dark;
    const html = [
      '<div class="status-bar' + (dark ? ' dark' : '') + '">',
        '<span class="time">9:41</span>',
        '<span class="icons">',
          '<svg width="18" height="10" viewBox="0 0 18 10" fill="currentColor"><circle cx="3" cy="5" r="2"/><circle cx="9" cy="5" r="2"/><circle cx="15" cy="5" r="2"/></svg>',
          '<svg width="16" height="11" viewBox="0 0 16 11" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8 8 L8 3 A5 5 0 0 0 3 8 Z" fill="currentColor"/><path d="M8 8 L8 1 A7 7 0 0 0 1 8" /></svg>',
          '<svg width="22" height="10" viewBox="0 0 22 10" fill="none" stroke="currentColor" stroke-width="1"><rect x="0.5" y="0.5" width="18" height="9" rx="2"/><rect x="2" y="2" width="15" height="6" rx="1" fill="currentColor"/><rect x="19.5" y="3.5" width="1.5" height="3" rx="0.5" fill="currentColor"/></svg>',
        '</span>',
      '</div>'
    ].join('');
    return html;
  }

  // Expose API
  window.WP = {
    navTo, navNext, navPrev, navRestart,
    scheduleAdvance, cancelAdvance,
    typeInto, sleep, startTimer,
    buildStatusBar, SCREEN_ORDER
  };

  // Boot
  document.addEventListener('DOMContentLoaded', () => {
    bindKeys();
    bindDelegation();
    mountDemoControls();
  });
})();
