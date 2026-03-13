/* ══════════════════════════════════════════
   ZIION Mobile Navigation System
   ══════════════════════════════════════════ */
(function() {
  'use strict';

  // Detect current page
  var path = window.location.pathname.split('/').pop() || 'index.html';

  // Nav items config
  var navItems = [
    { id: 'dashboard', label: 'Home', href: 'cosmos-grid.html', pages: ['cosmos-grid.html','dashboard.html','index.html',''], icon: '<svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>' },
    { id: 'library', label: 'Library', href: 'library.html', pages: ['library.html'], icon: '<svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>' },
    { id: 'threads', label: 'Threads', href: 'threads.html', pages: ['threads.html'], icon: '<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' },
    { id: 'world', label: 'World', href: 'world.html', pages: ['world.html'], icon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>' },
    { id: 'more', label: 'More', href: '#menu', pages: [], icon: '<svg viewBox="0 0 24 24"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>' }
  ];

  // All menu links (for slide-out panel)
  var menuLinks = [
    { label: 'Dashboard', href: 'cosmos-grid.html', icon: '<svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>' },
    { label: 'Library', href: 'library.html', icon: '<svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>' },
    { label: 'Threads', href: 'threads.html', icon: '<svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>' },
    { label: 'Connections', href: 'directory.html', icon: '<svg viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
    { label: 'Assets', href: 'assets.html', icon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>' },
    { label: 'World', href: 'world.html', icon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>' },
    { label: 'Pulse', href: 'pulse.html', icon: '<svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>' },
    { divider: true },
    { label: 'Book 19Keys', href: 'book-19keys.html', icon: '<svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>' },
    { label: 'Messages', href: 'messages.html', icon: '<svg viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>' },
    { label: 'Settings', href: '#', icon: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.32 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' }
  ];

  // Build bottom nav HTML
  var navHtml = '<nav class="mobile-nav"><div class="mobile-nav-inner">';
  navItems.forEach(function(item) {
    var isActive = item.pages.indexOf(path) !== -1;
    var cls = 'mobile-nav-item' + (isActive ? ' active' : '');
    var href = item.href === '#menu' ? '#' : item.href;
    var onclick = item.href === '#menu' ? ' onclick="window._ziionToggleMenu(event)"' : '';
    navHtml += '<a class="' + cls + '" href="' + href + '"' + onclick + '>' + item.icon + '<span>' + item.label + '</span></a>';
  });
  navHtml += '</div></nav>';

  // Build menu overlay + panel
  var menuHtml = '<div class="mobile-menu-overlay" onclick="window._ziionToggleMenu(event)">';
  menuHtml += '<div class="mobile-menu-panel" onclick="event.stopPropagation()">';
  menuHtml += '<div class="mobile-menu-logo"><span>Z I I O N</span><button class="mobile-menu-close" onclick="window._ziionToggleMenu(event)">&times;</button></div>';

  menuLinks.forEach(function(item) {
    if (item.divider) {
      menuHtml += '<div class="mobile-menu-divider"></div>';
    } else {
      var isActive = item.href === path;
      var cls = 'mobile-menu-link' + (isActive ? ' active' : '');
      menuHtml += '<a class="' + cls + '" href="' + item.href + '">' + item.icon + item.label + '</a>';
    }
  });

  menuHtml += '</div></div>';

  // Inject into DOM
  document.body.insertAdjacentHTML('beforeend', navHtml + menuHtml);

  // Toggle menu function
  var overlay = document.querySelector('.mobile-menu-overlay');
  var panel = document.querySelector('.mobile-menu-panel');

  window._ziionToggleMenu = function(e) {
    if (e) e.preventDefault();
    var isOpen = panel.classList.contains('open');
    if (isOpen) {
      panel.classList.remove('open');
      overlay.classList.remove('open');
      setTimeout(function() { overlay.style.display = 'none'; }, 300);
    } else {
      overlay.style.display = 'block';
      // Force reflow
      overlay.offsetHeight;
      overlay.classList.add('open');
      panel.classList.add('open');
    }
  };
})();
