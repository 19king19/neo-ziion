/* ==========================================================================
   CROWNZ19 Manifest Museum Timeline
   Horizontal scroll driven by vertical scroll + room transitions
   ========================================================================== */

(function () {
  'use strict';

  var section = document.querySelector('[data-manifest-timeline]');
  if (!section) return;

  var track = section.querySelector('[data-manifest-track]');
  var scrollContainer = section.querySelector('[data-manifest-scroll]');
  var eras = section.querySelectorAll('[data-era]');
  var progressBar = section.querySelector('[data-manifest-progress-bar]');
  var dots = section.querySelectorAll('[data-manifest-dot]');

  if (!track || !scrollContainer || !eras.length) return;

  var isMobile = window.matchMedia('(max-width: 768px)');
  var totalEras = eras.length;
  var currentEra = 0;
  var isActive = false;

  /* ------------------------------------------------------------------
     Set scroll container width
     ------------------------------------------------------------------ */
  function setScrollWidth() {
    if (isMobile.matches) {
      scrollContainer.style.width = '';
      return;
    }
    scrollContainer.style.width = (totalEras * 100) + 'vw';
  }

  /* ------------------------------------------------------------------
     Calculate how tall the section needs to be for scroll distance
     ------------------------------------------------------------------ */
  function setSectionHeight() {
    if (isMobile.matches) {
      section.style.height = '';
      return;
    }
    /* Each era gets 100vh of scroll distance */
    var introHeight = section.querySelector('[data-manifest-intro]')
      ? window.innerHeight
      : 0;
    section.style.height = introHeight + (totalEras * window.innerHeight) + 'px';
  }

  /* ------------------------------------------------------------------
     Horizontal scroll from vertical scroll
     ------------------------------------------------------------------ */
  function onScroll() {
    if (isMobile.matches) return;

    var rect = section.getBoundingClientRect();
    var sectionTop = window.pageYOffset + rect.top;
    var intro = section.querySelector('[data-manifest-intro]');
    var introHeight = intro ? window.innerHeight : 0;
    var scrollStart = sectionTop + introHeight;
    var scrollDistance = (totalEras - 1) * window.innerHeight;
    var scrolled = window.pageYOffset - scrollStart;

    /* Check if we're in the scrollable zone */
    if (scrolled < 0 || scrolled > scrollDistance) {
      if (scrolled < 0) {
        scrollContainer.style.transform = 'translateX(0)';
        setActiveEra(0);
        section.classList.remove('is-active');
      }
      if (scrolled > scrollDistance) {
        var maxTranslate = (totalEras - 1) * window.innerWidth;
        scrollContainer.style.transform = 'translateX(-' + maxTranslate + 'px)';
        setActiveEra(totalEras - 1);
      }
      return;
    }

    section.classList.add('is-active');

    /* Map vertical scroll to horizontal translate */
    var progress = scrolled / scrollDistance;
    var translateX = progress * (totalEras - 1) * window.innerWidth;
    scrollContainer.style.transform = 'translateX(-' + translateX + 'px)';

    /* Update active era */
    var eraIndex = Math.round(progress * (totalEras - 1));
    setActiveEra(eraIndex);

    /* Update progress bar */
    if (progressBar) {
      progressBar.style.width = (progress * 100) + '%';
    }
  }

  /* ------------------------------------------------------------------
     Set the active era (content reveal + dot highlight)
     ------------------------------------------------------------------ */
  function setActiveEra(index) {
    if (index === currentEra && eras[index].classList.contains('is-active')) return;
    currentEra = index;

    eras.forEach(function (era, i) {
      if (i === index) {
        era.classList.add('is-active');
      } else {
        era.classList.remove('is-active');
      }
    });

    dots.forEach(function (dot, i) {
      if (i === index) {
        dot.classList.add('is-active');
      } else {
        dot.classList.remove('is-active');
      }
    });
  }

  /* ------------------------------------------------------------------
     Dot click navigation
     ------------------------------------------------------------------ */
  dots.forEach(function (dot, index) {
    dot.addEventListener('click', function () {
      if (isMobile.matches) {
        /* On mobile, scroll to the era element */
        eras[index].scrollIntoView({ behavior: 'smooth' });
        return;
      }

      var intro = section.querySelector('[data-manifest-intro]');
      var introHeight = intro ? window.innerHeight : 0;
      var rect = section.getBoundingClientRect();
      var sectionTop = window.pageYOffset + rect.top;
      var targetScroll = sectionTop + introHeight + (index * window.innerHeight);

      window.scrollTo({
        top: targetScroll,
        behavior: 'smooth'
      });
    });
  });

  /* ------------------------------------------------------------------
     Mobile: use IntersectionObserver for era activation
     ------------------------------------------------------------------ */
  function setupMobileObserver() {
    if (!('IntersectionObserver' in window)) {
      eras.forEach(function (era) { era.classList.add('is-active'); });
      return;
    }

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-active');
        }
      });
    }, { threshold: 0.3 });

    eras.forEach(function (era) { observer.observe(era); });
  }

  /* ------------------------------------------------------------------
     Resize handler
     ------------------------------------------------------------------ */
  function onResize() {
    setScrollWidth();
    setSectionHeight();

    if (isMobile.matches) {
      scrollContainer.style.transform = '';
      section.style.height = '';
      section.classList.remove('is-active');
    } else {
      onScroll();
    }
  }

  /* ------------------------------------------------------------------
     Init
     ------------------------------------------------------------------ */
  setScrollWidth();
  setSectionHeight();

  if (isMobile.matches) {
    setupMobileObserver();
  } else {
    setActiveEra(0);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onResize);

  /* Handle media query changes */
  if (isMobile.addEventListener) {
    isMobile.addEventListener('change', function () {
      if (isMobile.matches) {
        setupMobileObserver();
      }
      onResize();
    });
  }
})();
