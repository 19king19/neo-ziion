/* ==========================================================================
   CROWNZ19 Main JS
   Global utilities, scroll reveal, overlay management
   ========================================================================== */

(function () {
  'use strict';

  /* ------------------------------------------------------------------
     Scroll Reveal (IntersectionObserver)
     ------------------------------------------------------------------ */
  const revealElements = document.querySelectorAll('.reveal');

  if (revealElements.length && 'IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('reveal--visible');
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    revealElements.forEach(function (el) {
      revealObserver.observe(el);
    });
  }

  /* ------------------------------------------------------------------
     Overlay
     ------------------------------------------------------------------ */
  const overlay = document.querySelector('[data-overlay]');

  function showOverlay() {
    if (overlay) {
      overlay.classList.add('is-active');
      document.body.style.overflow = 'hidden';
    }
  }

  function hideOverlay() {
    if (overlay) {
      overlay.classList.remove('is-active');
      document.body.style.overflow = '';
    }
  }

  if (overlay) {
    overlay.addEventListener('click', function () {
      hideOverlay();
      document.dispatchEvent(new CustomEvent('overlay:clicked'));
      /* Close mobile nav if open */
      document.body.classList.remove('mobile-nav-open');
      var mobileNav = document.querySelector('[data-mobile-nav]');
      if (mobileNav) mobileNav.setAttribute('aria-hidden', 'true');
      var toggle = document.querySelector('[data-menu-toggle]');
      if (toggle) toggle.setAttribute('aria-expanded', 'false');
    });
  }

  document.addEventListener('overlay:show', showOverlay);
  document.addEventListener('overlay:hide', hideOverlay);

  /* ------------------------------------------------------------------
     Money Formatting
     ------------------------------------------------------------------ */
  window.CROWNZ19 = window.CROWNZ19 || {};

  window.CROWNZ19.formatMoney = function (cents, format) {
    if (typeof cents === 'string') cents = cents.replace('.', '');
    var value = '';
    var placeholderRegex = /\{\{\s*(\w+)\s*\}\}/;
    format = format || window.CROWNZ19.money_format || '${{amount}}';

    function formatWithDelimiters(number, precision, thousands, decimal) {
      precision = precision == null ? 2 : precision;
      thousands = thousands || ',';
      decimal = decimal || '.';

      if (isNaN(number) || number == null) return '0';

      number = (number / 100.0).toFixed(precision);
      var parts = number.split('.');
      var dollars = parts[0].replace(/(\d)(?=(\d\d\d)+(?!\d))/g, '$1' + thousands);
      var pennies = parts[1] ? decimal + parts[1] : '';

      return dollars + pennies;
    }

    switch (format.match(placeholderRegex)[1]) {
      case 'amount':
        value = formatWithDelimiters(cents, 2);
        break;
      case 'amount_no_decimals':
        value = formatWithDelimiters(cents, 0);
        break;
      case 'amount_with_comma_separator':
        value = formatWithDelimiters(cents, 2, '.', ',');
        break;
      case 'amount_no_decimals_with_comma_separator':
        value = formatWithDelimiters(cents, 0, '.', ',');
        break;
    }

    return format.replace(placeholderRegex, value);
  };

  /* ------------------------------------------------------------------
     Smooth scroll for anchor links
     ------------------------------------------------------------------ */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      var targetId = this.getAttribute('href');
      if (targetId === '#') return;
      var target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  /* ------------------------------------------------------------------
     Update cart count on page load (from Shopify cart object)
     ------------------------------------------------------------------ */
  function updateCartCount(count) {
    document.querySelectorAll('[data-cart-count]').forEach(function (el) {
      el.textContent = count;
      el.setAttribute('data-cart-count', count);
    });
  }

  /* Listen for cart updates from other scripts */
  document.addEventListener('cart:updated', function (e) {
    if (e.detail && e.detail.item_count !== undefined) {
      updateCartCount(e.detail.item_count);
    }
  });
})();
