/* ==========================================================================
   CROWNZ19 Product Detail
   Variant switching, thumbnail gallery, AJAX add-to-cart
   ========================================================================== */

(function () {
  'use strict';

  var container = document.querySelector('[data-product-detail]');
  if (!container) return;

  var mainImage = container.querySelector('[data-product-main-image]');
  var thumbs = container.querySelectorAll('[data-thumb-index]');
  var optionSelects = container.querySelectorAll('[data-option-index]');
  var variantSelect = container.querySelector('[data-variant-select]');
  var variantIdInput = container.querySelector('[data-variant-id]');
  var addToCartBtn = container.querySelector('[data-add-to-cart]');
  var priceContainer = container.querySelector('[data-product-price]');
  var form = container.querySelector('[data-product-form]');

  /* ------------------------------------------------------------------
     Thumbnail gallery
     ------------------------------------------------------------------ */
  thumbs.forEach(function (thumb) {
    thumb.addEventListener('click', function () {
      var src = this.getAttribute('data-thumb-src');
      if (mainImage && src) {
        mainImage.src = src;
      }
      thumbs.forEach(function (t) { t.classList.remove('is-active'); });
      this.classList.add('is-active');
    });
  });

  /* ------------------------------------------------------------------
     Variant selection
     ------------------------------------------------------------------ */
  function getSelectedOptions() {
    var options = [];
    optionSelects.forEach(function (select) {
      options.push(select.value);
    });
    return options;
  }

  function findVariant(selectedOptions) {
    var variants = variantSelect ? variantSelect.options : [];
    for (var i = 0; i < variants.length; i++) {
      try {
        var variantData = JSON.parse(variants[i].getAttribute('data-variant-json'));
        var match = true;
        for (var j = 0; j < selectedOptions.length; j++) {
          if (variantData['option' + (j + 1)] !== selectedOptions[j]) {
            match = false;
            break;
          }
        }
        if (match) return variantData;
      } catch (e) { /* skip */ }
    }
    return null;
  }

  function updateVariant() {
    var selected = getSelectedOptions();
    var variant = findVariant(selected);
    if (!variant) return;

    /* Update hidden input */
    if (variantIdInput) {
      variantIdInput.value = variant.id;
    }

    /* Update URL */
    if (history.replaceState) {
      var url = window.location.pathname + '?variant=' + variant.id;
      history.replaceState({}, '', url);
    }

    /* Update price */
    if (priceContainer && window.CROWNZ19) {
      var priceHtml = '';
      if (variant.compare_at_price && variant.compare_at_price > variant.price) {
        priceHtml = '<span class="price price--sale">' +
          CROWNZ19.formatMoney(variant.price) +
          '</span> <s class="price price--compare">' +
          CROWNZ19.formatMoney(variant.compare_at_price) + '</s>';
      } else {
        priceHtml = '<span class="price">' + CROWNZ19.formatMoney(variant.price) + '</span>';
      }
      priceContainer.innerHTML = priceHtml;
    }

    /* Update button state */
    if (addToCartBtn) {
      if (variant.available) {
        addToCartBtn.disabled = false;
        addToCartBtn.textContent = 'Add to Cart';
      } else {
        addToCartBtn.disabled = true;
        addToCartBtn.textContent = 'Sold Out';
      }
    }

    /* Update main image if variant has featured image */
    if (variant.featured_image && mainImage) {
      mainImage.src = variant.featured_image.src;
    }
  }

  optionSelects.forEach(function (select) {
    select.addEventListener('change', updateVariant);
  });

  /* ------------------------------------------------------------------
     AJAX Add to Cart
     ------------------------------------------------------------------ */
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var id = variantIdInput ? variantIdInput.value : null;
      var quantityInput = form.querySelector('[data-quantity-input]');
      var quantity = quantityInput ? parseInt(quantityInput.value, 10) : 1;

      if (!id) return;

      addToCartBtn.disabled = true;
      addToCartBtn.textContent = 'Adding...';

      fetch('/cart/add.js', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: parseInt(id, 10), quantity: quantity })
      })
        .then(function (res) { return res.json(); })
        .then(function () {
          addToCartBtn.textContent = 'Added!';
          setTimeout(function () {
            addToCartBtn.disabled = false;
            addToCartBtn.textContent = 'Add to Cart';
          }, 1500);

          /* Update cart count */
          fetch('/cart.js')
            .then(function (r) { return r.json(); })
            .then(function (cart) {
              document.dispatchEvent(new CustomEvent('cart:updated', {
                detail: { count: cart.item_count }
              }));
              document.dispatchEvent(new CustomEvent('cart:toggle'));
            });
        })
        .catch(function () {
          addToCartBtn.disabled = false;
          addToCartBtn.textContent = 'Add to Cart';
        });
    });
  }
})();
