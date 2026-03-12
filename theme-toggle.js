/* ZIION Theme Toggle — Dark / Light Mode */
(function() {
  // Apply saved theme immediately
  var saved = localStorage.getItem('ziion-theme');
  if (saved === 'light') {
    document.documentElement.classList.add('light-mode');
    if (document.body) document.body.classList.add('light-mode');
  }

  function init() {
    // Apply theme to body
    var theme = localStorage.getItem('ziion-theme');
    if (theme === 'light') {
      document.body.classList.add('light-mode');
    }

    // Find toggle button
    var toggle = document.getElementById('themeToggle');
    if (!toggle) return;

    updateIcon(theme === 'light');
    fixInlineSvgStrokes(theme === 'light');

    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      var isLight = document.body.classList.toggle('light-mode');
      document.documentElement.classList.toggle('light-mode', isLight);
      localStorage.setItem('ziion-theme', isLight ? 'light' : 'dark');
      updateIcon(isLight);
      fixInlineSvgStrokes(isLight);
    });

    function fixInlineSvgStrokes(isLight) {
      document.querySelectorAll('svg [stroke="white"], svg [stroke="#fff"], svg [stroke="#ffffff"]').forEach(function(el) {
        el.setAttribute('stroke', isLight ? '#7a7a7a' : 'white');
      });
      document.querySelectorAll('svg [fill="white"], svg [fill="#fff"], svg [fill="#ffffff"]').forEach(function(el) {
        if (!el.closest('#themeToggle')) {
          el.setAttribute('fill', isLight ? '#7a7a7a' : 'white');
        }
      });
      document.querySelectorAll('.thread-avatar[style]').forEach(function(el) {
        if (isLight) {
          el.style.background = 'linear-gradient(135deg, #d4d4d4, #e8e8e8)';
        } else {
          el.style.background = 'linear-gradient(135deg, #4D4D4D, #322D2A)';
        }
      });
    }

    function updateIcon(isLight) {
      if (isLight) {
        toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
        toggle.title = 'Switch to dark mode';
      } else {
        toggle.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
        toggle.title = 'Switch to light mode';
      }
    }
  }

  // Run init: if DOM already loaded, run now; otherwise wait
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
