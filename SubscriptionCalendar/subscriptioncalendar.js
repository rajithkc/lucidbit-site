(function () {
  'use strict';
  document.querySelectorAll('[data-store-url]').forEach(link => {
    if (!link.dataset.storeUrl) link.addEventListener('click', event => event.preventDefault());
  });
  const nav = document.getElementById('main-nav');
  const hero = document.querySelector('.sc-hero');
  if (nav && hero && 'IntersectionObserver' in window) {
    new IntersectionObserver(entries => nav.classList.toggle('product-mode', !entries[0].isIntersecting), { rootMargin: '-80px 0px 0px 0px' }).observe(hero);
  }
  const gallery = document.querySelector('.sc-gallery');
  const group = document.querySelector('.sc-gallery-group');
  if (gallery && group) {
    const copy = group.cloneNode(true);
    copy.setAttribute('aria-hidden', 'true');
    copy.querySelectorAll('img').forEach(img => {
      img.alt = '';
      img.loading = 'eager';
    });
    group.parentElement.append(copy);
  }
})();
