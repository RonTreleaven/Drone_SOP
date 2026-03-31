(() => {
  const workflowLinks = [
    { key: 'home', href: 'index.html', label: 'Home' },
    { key: 'tools', href: 'tools.html', label: 'Tools' },
    { key: 'sections', href: 'Sections.html', label: 'SOP Sections' },
    { key: 'flight-log', href: 'flight-log.html', label: 'Flight Log' },
    { key: 'summary', href: 'summary.html', label: 'Summary' },
    { key: 'emergency', href: 'emergencies.html', label: 'Emergency Procedures' }
  ];

  function createSeparator() {
    const sep = document.createElement('span');
    sep.className = 'nav-sep';
    sep.textContent = '|';
    sep.setAttribute('aria-hidden', 'true');
    return sep;
  }

  function createBackLink(fallbackHref) {
    const link = document.createElement('a');
    link.href = '#';
    link.className = 'back-link';
    link.dataset.sharedBack = 'true';
    link.dataset.fallback = fallbackHref || 'index.html';
    link.innerHTML = '<span class="back-icon" aria-hidden="true">&#8592;</span>BACK';
    return link;
  }

  function createNavLink(linkInfo, activeKey) {
    const link = document.createElement('a');
    link.href = linkInfo.href;
    link.textContent = linkInfo.label;
    if (linkInfo.key === activeKey) {
      link.classList.add('active');
      link.setAttribute('aria-current', 'page');
    }
    return link;
  }

  function appendWithSeparators(container, nodes) {
    nodes.forEach((node, index) => {
      if (index > 0) {
        container.appendChild(createSeparator());
      }
      container.appendChild(node);
    });
  }

  function renderWorkflowNav(nav) {
    const activeKey = String(nav.dataset.active || '').toLowerCase();
    const showBack = String(nav.dataset.showBack || 'false').toLowerCase() === 'true';
    const backFallback = nav.dataset.backFallback || 'index.html';
    const primary = document.createElement('div');
    primary.className = 'nav-primary';
    const nodes = [];

    if (showBack) {
      nodes.push(createBackLink(backFallback));
    }

    workflowLinks.forEach(linkInfo => {
      nodes.push(createNavLink(linkInfo, activeKey));
    });

    appendWithSeparators(primary, nodes);
    nav.replaceChildren(primary);
  }

  function renderUtilityNav(nav) {
    const extras = Array.from(nav.querySelectorAll('[data-nav-extra]'));
    const showHome = String(nav.dataset.showHome || 'false').toLowerCase() === 'true';
    const backFallback = nav.dataset.backFallback || 'index.html';

    const primary = document.createElement('div');
    primary.className = 'nav-primary';
    const nodes = [createBackLink(backFallback)];
    if (showHome) {
      nodes.push(createNavLink({ key: 'home', href: 'index.html', label: 'Home' }, ''));
    }
    appendWithSeparators(primary, nodes);

    nav.replaceChildren(primary);

    if (extras.length) {
      const extraWrap = document.createElement('div');
      extraWrap.className = 'nav-extras';
      extras.forEach(node => extraWrap.appendChild(node));
      nav.appendChild(extraWrap);
    }
  }

  function initSharedNavs() {
    document.querySelectorAll('.shared-site-nav').forEach(nav => {
      const variant = String(nav.dataset.navVariant || 'workflow').toLowerCase();
      if (variant === 'utility') {
        renderUtilityNav(nav);
        return;
      }
      renderWorkflowNav(nav);
    });
  }

  document.addEventListener('click', event => {
    const link = event.target.closest('a[data-shared-back="true"]');
    if (!link) return;
    event.preventDefault();
    if (window.history.length > 1) {
      window.history.back();
      return;
    }
    window.location.href = link.dataset.fallback || 'index.html';
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSharedNavs);
  } else {
    initSharedNavs();
  }
})();
