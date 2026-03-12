/* ==========================================================================
   CROWNZ19 Product Showcase
   Mouse-follow parallax on scattered products
   ========================================================================== */

(function () {
  'use strict';

  var showcase = document.querySelector('[data-product-showcase]');
  if (!showcase) return;

  var items = showcase.querySelectorAll('[data-showcase-item]');
  if (!items.length) return;

  /* Only enable parallax on desktop */
  var isDesktop = window.matchMedia('(min-width: 769px)');

  function handleMouseMove(e) {
    if (!isDesktop.matches) return;

    var rect = showcase.getBoundingClientRect();
    /* Normalize mouse position to -1 to 1 */
    var mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
    var mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 2;

    items.forEach(function (item) {
      var speed = parseInt(item.getAttribute('data-parallax-speed') || '2', 10);
      if (speed === 0) return;

      var offsetX = mouseX * speed * 8;
      var offsetY = mouseY * speed * 6;

      /* Preserve existing transform and add parallax translate */
      var currentTransform = item.style.transform || '';
      /* Remove any previous parallax translate */
      var baseTransform = currentTransform.replace(/translate3d\([^)]*\)/g, '').trim();

      item.style.transform = 'translate3d(' + offsetX + 'px, ' + offsetY + 'px, 0) ' + baseTransform;
    });
  }

  function handleMouseLeave() {
    items.forEach(function (item) {
      var currentTransform = item.style.transform || '';
      var baseTransform = currentTransform.replace(/translate3d\([^)]*\)/g, '').trim();
      item.style.transform = 'translate3d(0, 0, 0) ' + baseTransform;
    });
  }

  showcase.addEventListener('mousemove', handleMouseMove);
  showcase.addEventListener('mouseleave', handleMouseLeave);

  /* Staggered reveal animation */
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var allItems = entry.target.querySelectorAll('[data-showcase-item]');
            allItems.forEach(function (item, i) {
              item.style.transitionDelay = (i * 80) + 'ms';
              item.classList.add('is-visible');
            });
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1 }
    );

    observer.observe(showcase);
  }
})();
