/* ──────────────────────────────────────────────────────────────────────────
   LucidBit — shared client-side behavior
   Loaded by every page. Behavior is opt-in via data attributes so each page
   keeps its exact current behavior:

     <body data-reveal-threshold="0.12">   → enable reveal-on-scroll observer
     <body data-reveal-threshold="0.08">   → (detail pages use a lower value)
     <body>  (no attr)                     → observer is not attached at all

     <div class="..." data-tilt data-tilt-strength="4">
       Strength defaults to 4 if omitted. Works on child <img> or <video>.

   Nav-scroll effect and Kit newsletter form handler attach automatically if
   the matching element ids exist on the page.
   ──────────────────────────────────────────────────────────────────────── */
(function () {
  'use strict';

  /* ── Nav scroll shade ── */
  var nav = document.getElementById('main-nav');
  if (nav) {
    window.addEventListener('scroll', function () {
      nav.classList.toggle('scrolled', window.scrollY > 24);
    }, { passive: true });
  }

  /* ── Reveal on scroll (opt-in per page via body data attribute) ── */
  var revealAttr = document.body.getAttribute('data-reveal-threshold');
  if (revealAttr !== null && 'IntersectionObserver' in window) {
    var threshold = parseFloat(revealAttr);
    if (isNaN(threshold)) threshold = 0.1;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          io.unobserve(e.target);
        }
      });
    }, { threshold: threshold });
    document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });
  }

  /* ── Subtle tilt on [data-tilt] wrappers ──
     Target preference: first visible <img>/<video> child; falls back to the
     wrapper itself when no media child exists (so placeholder divs still
     track the mouse exactly like an image/video would). Re-resolves on
     every move so DOM swaps — e.g. a video element being removed on error
     in favor of a fallback div — don't leave tilt pointing at a detached
     node. */
  function resolveTiltTarget(wrap) {
    var candidates = wrap.querySelectorAll('img, video');
    for (var i = 0; i < candidates.length; i++) {
      var el = candidates[i];
      if (!el.isConnected) continue;
      var cs = window.getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      return el;
    }
    return wrap;
  }
  document.querySelectorAll('[data-tilt]').forEach(function (wrap) {
    var strength = parseFloat(wrap.getAttribute('data-tilt-strength'));
    if (isNaN(strength)) strength = 4;
    wrap.addEventListener('mousemove', function (e) {
      var target = resolveTiltTarget(wrap);
      var r = wrap.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width  - 0.5;
      var y = (e.clientY - r.top)  / r.height - 0.5;
      target.style.transform =
        'perspective(900px) rotateX(' + (-y * strength) + 'deg) rotateY(' + (x * strength) + 'deg) scale(1.025)';
      target.style.transition = 'transform 0.1s ease';
    });
    wrap.addEventListener('mouseleave', function () {
      var target = resolveTiltTarget(wrap);
      target.style.transform = 'perspective(900px) rotateX(0deg) rotateY(0deg) scale(1)';
      target.style.transition = 'transform 0.6s ease';
    });
  });

  /* ── Nav dropdown (Apps menu) ──
     Hover-open is handled in CSS (:hover / :focus-within). This adds
     click/keyboard toggle for the trigger, outside-click to close, and
     Escape to dismiss — so the menu works on mobile and with keyboards. */
  document.querySelectorAll('.nav-dropdown').forEach(function (dd) {
    var trigger = dd.querySelector('.nav-dropdown-trigger');
    if (!trigger) return;
    trigger.addEventListener('click', function (e) {
      e.preventDefault();
      var isOpen = dd.classList.toggle('open');
      trigger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    });
    dd.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        dd.classList.remove('open');
        trigger.setAttribute('aria-expanded', 'false');
        trigger.focus();
      }
    });
  });
  document.addEventListener('click', function (e) {
    document.querySelectorAll('.nav-dropdown.open').forEach(function (dd) {
      if (!dd.contains(e.target)) {
        dd.classList.remove('open');
        var t = dd.querySelector('.nav-dropdown-trigger');
        if (t) t.setAttribute('aria-expanded', 'false');
      }
    });
  });

  /* ── Kit newsletter form handler ── */
  var form = document.getElementById('kit-form');
  if (form) {
    form.addEventListener('submit', function () {
      setTimeout(function () {
        form.style.display = 'none';
        var thanks = document.getElementById('kit-thanks');
        if (thanks) thanks.style.display = 'block';
      }, 400);
    });
  }

  /* ── Card mouse-tracker helper (kept on window for any inline handlers) ── */
  window.trackMouse = function (e, card) {
    var r = card.getBoundingClientRect();
    card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    card.style.setProperty('--my', (e.clientY - r.top) + 'px');
  };
})();
