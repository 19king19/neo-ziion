/* ==========================================================================
   CROWNZ19 Sphere Grid
   Scroll-triggered stagger reveal + hover glow effects
   ========================================================================== */

(function () {
  'use strict';

  var grid = document.querySelector('[data-sphere-grid]');
  if (!grid) return;

  var spheres = grid.querySelectorAll('[data-sphere-item]');
  if (!spheres.length) return;

  /* ------------------------------------------------------------------
     Stagger Reveal on Scroll
     ------------------------------------------------------------------ */
  if ('IntersectionObserver' in window) {
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var items = entry.target.querySelectorAll('[data-sphere-item]');
            items.forEach(function (item, index) {
              setTimeout(function () {
                item.classList.add('is-visible');
              }, index * 100);
            });
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15 }
    );

    var container = grid.querySelector('[data-sphere-grid-container]');
    if (container) {
      revealObserver.observe(container);
    }
  } else {
    /* Fallback: show all immediately */
    spheres.forEach(function (s) {
      s.classList.add('is-visible');
    });
  }

  /* ------------------------------------------------------------------
     Subtle 3D tilt on hover (desktop only)
     ------------------------------------------------------------------ */
  var isDesktop = window.matchMedia('(min-width: 769px)');

  spheres.forEach(function (sphere) {
    var orb = sphere.querySelector('[data-sphere-orb]');
    if (!orb) return;

    orb.addEventListener('mousemove', function (e) {
      if (!isDesktop.matches) return;

      var rect = orb.getBoundingClientRect();
      var x = (e.clientX - rect.left) / rect.width - 0.5;
      var y = (e.clientY - rect.top) / rect.height - 0.5;

      var rotateX = y * -10;
      var rotateY = x * 10;

      orb.style.transform = 'scale(1.06) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg)';
    });

    orb.addEventListener('mouseleave', function () {
      orb.style.transform = '';
    });
  });
})();
