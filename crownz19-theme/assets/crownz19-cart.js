/* ==========================================================================
   CROWNZ19 Cart Drawer
   Open/close, quantity changes, remove items, AJAX updates
   ========================================================================== */

(function () {
  'use strict';

  var drawer = document.querySelector('[data-cart-drawer]');
  if (!drawer) return;

  var overlay = drawer.querySelector('[data-cart-drawer-overlay]');
  var closeBtn = drawer.querySelector('[data-cart-drawer-close]');
  var body = drawer.querySelector('[data-cart-drawer-body]');
  var countEl = drawer.querySelector('[data-cart-drawer-count]');
  var totalEl = drawer.querySelector('[data-cart-drawer-total]');
  var checkoutBtn = drawer.querySelector('[data-cart-checkout]');

  /* ------------------------------------------------------------------
     Open / Close
     ------------------------------------------------------------------ */
  function openDrawer() {
    drawer.classList.add('is-open');
    drawer.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    drawer.classList.remove('is-open');
    drawer.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }

  document.addEventListener('cart:toggle', function () {
    if (drawer.classList.contains('is-open')) {
      closeDrawer();
    } else {
      refreshCart().then(openDrawer);
    }
  });

  if (overlay) overlay.addEventListener('click', closeDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer.classList.contains('is-open')) {
      closeDrawer();
    }
  });

  /* ------------------------------------------------------------------
     Checkout redirect
     ------------------------------------------------------------------ */
  if (checkoutBtn) {
    checkoutBtn.addEventListener('click', function () {
      window.location.href = '/checkout';
    });
  }

  /* ------------------------------------------------------------------
     AJAX Cart API helpers
     ------------------------------------------------------------------ */
  function cartRequest(url, data) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }).then(function (r) { return r.json(); });
  }

  function refreshCart() {
    return fetch('/cart.js')
      .then(function (r) { return r.json(); })
      .then(function (cart) {
        renderCart(cart);
        updateGlobalCount(cart.item_count);
        return cart;
      });
  }

  function updateGlobalCount(count) {
    if (countEl) countEl.textContent = count;
    /* Also update header cart count */
    document.querySelectorAll('[data-cart-count]').forEach(function (el) {
      el.textContent = count;
      el.style.display = count > 0 ? '' : 'none';
    });
    document.dispatchEvent(new CustomEvent('cart:updated', { detail: { count: count } }));
  }

  /* ------------------------------------------------------------------
     Render cart HTML from JSON
     ------------------------------------------------------------------ */
  function renderCart(cart) {
    if (!body) return;

    if (cart.item_count === 0) {
      body.innerHTML = '<div class="cart-drawer__empty" data-cart-drawer-empty>' +
        '<p>Your cart is empty</p>' +
        '<a href="/collections/all" class="btn btn--primary">Continue Shopping</a></div>';

      var footer = drawer.querySelector('[data-cart-drawer-footer]');
      if (footer) footer.style.display = 'none';
      return;
    }

    var itemsHtml = '<div class="cart-drawer__items" data-cart-drawer-items>';
    cart.items.forEach(function (item, i) {
      var imgSrc = item.image ? item.image.replace(/(\.\w+)$/, '_120x$1') : '';
      var variantHtml = item.variant_title
        ? '<p class="cart-drawer__item-variant">' + item.variant_title + '</p>'
        : '';

      itemsHtml += '<div class="cart-drawer__item" data-cart-item data-line="' + (i + 1) + '">' +
        '<a href="' + item.url + '" class="cart-drawer__item-image">' +
        (imgSrc ? '<img src="' + imgSrc + '" alt="" width="80" height="80" loading="lazy">' : '') +
        '</a>' +
        '<div class="cart-drawer__item-info">' +
        '<a href="' + item.url + '" class="cart-drawer__item-title">' + item.product_title + '</a>' +
        variantHtml +
        '<p class="cart-drawer__item-price">' + formatMoney(item.final_line_price) + '</p>' +
        '<div class="cart-drawer__item-actions">' +
        '<div class="cart-drawer__item-qty">' +
        '<button class="cart-drawer__qty-btn" data-cart-qty-minus aria-label="Decrease">\u2212</button>' +
        '<span class="cart-drawer__qty-value" data-cart-qty-value>' + item.quantity + '</span>' +
        '<button class="cart-drawer__qty-btn" data-cart-qty-plus aria-label="Increase">+</button>' +
        '</div>' +
        '<button class="cart-drawer__item-remove" data-cart-remove aria-label="Remove">Remove</button>' +
        '</div></div></div>';
    });
    itemsHtml += '</div>';
    body.innerHTML = itemsHtml;

    /* Update footer */
    if (totalEl) totalEl.textContent = formatMoney(cart.total_price);
    var footer = drawer.querySelector('[data-cart-drawer-footer]');
    if (footer) footer.style.display = '';

    bindItemEvents();
  }

  function formatMoney(cents) {
    if (window.CROWNZ19 && window.CROWNZ19.formatMoney) {
      return CROWNZ19.formatMoney(cents);
    }
    return '$' + (cents / 100).toFixed(2);
  }

  /* ------------------------------------------------------------------
     Bind quantity/remove events on cart items
     ------------------------------------------------------------------ */
  function bindItemEvents() {
    body.querySelectorAll('[data-cart-item]').forEach(function (item) {
      var line = parseInt(item.getAttribute('data-line'), 10);

      var minusBtn = item.querySelector('[data-cart-qty-minus]');
      var plusBtn = item.querySelector('[data-cart-qty-plus]');
      var removeBtn = item.querySelector('[data-cart-remove]');
      var qtyValue = item.querySelector('[data-cart-qty-value]');

      if (minusBtn) {
        minusBtn.addEventListener('click', function () {
          var qty = parseInt(qtyValue.textContent, 10);
          if (qty <= 1) {
            changeQuantity(line, 0);
          } else {
            changeQuantity(line, qty - 1);
          }
        });
      }

      if (plusBtn) {
        plusBtn.addEventListener('click', function () {
          var qty = parseInt(qtyValue.textContent, 10);
          changeQuantity(line, qty + 1);
        });
      }

      if (removeBtn) {
        removeBtn.addEventListener('click', function () {
          changeQuantity(line, 0);
        });
      }
    });
  }

  function changeQuantity(line, quantity) {
    cartRequest('/cart/change.js', { line: line, quantity: quantity })
      .then(function (cart) {
        renderCart(cart);
        updateGlobalCount(cart.item_count);
      });
  }

  /* Initial bind for server-rendered items */
  bindItemEvents();
})();
