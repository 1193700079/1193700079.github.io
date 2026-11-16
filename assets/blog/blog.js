(() => {
  'use strict';
  const menu = document.querySelector('.menu-button');
  const navigation = document.querySelector('.primary-nav');
  const setMenu = (open) => {
    if (!menu || !navigation) return;
    menu.setAttribute('aria-expanded', String(open));
    navigation.classList.toggle('is-open', open);
  };
  menu?.addEventListener('click', () => setMenu(menu.getAttribute('aria-expanded') !== 'true'));
  navigation?.addEventListener('click', (event) => { if (event.target.closest('a')) setMenu(false); });
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.site-header')) setMenu(false);
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && menu?.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      menu.focus();
    }
  });
  const mobile = window.matchMedia('(max-width: 760px)');
  mobile.addEventListener('change', () => { if (!mobile.matches) setMenu(false); });

  try {
    if (!sessionStorage.getItem('blog-visited')) {
      document.body.classList.add('first-visit');
      sessionStorage.setItem('blog-visited', '1');
    }
  } catch (_) { /* Storage is optional. */ }

  const search = document.querySelector('#post-search');
  if (search) {
    const posts = [...document.querySelectorAll('[data-post]')];
    const filters = [...document.querySelectorAll('[data-filter]')];
    const count = document.querySelector('[data-result-count]');
    const empty = document.querySelector('.search-empty');
    const end = document.querySelector('[data-list-end]');
    let selected = 'all';
    const filterPosts = () => {
      const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const post of posts) {
        const match = (selected === 'all' || post.dataset.category === selected)
          && terms.every((term) => post.dataset.search.includes(term));
        post.hidden = !match;
        if (match) visible += 1;
      }
      count.textContent = visible === posts.length ? `共 ${visible} 篇` : `找到 ${visible} 篇 / 共 ${posts.length} 篇`;
      empty.hidden = visible !== 0;
      end.hidden = visible !== posts.length;
    };
    for (const button of filters) button.addEventListener('click', () => {
      selected = button.dataset.filter;
      for (const candidate of filters) {
        const active = candidate === button;
        candidate.classList.toggle('is-active', active);
        candidate.setAttribute('aria-pressed', String(active));
      }
      filterPosts();
    });
    search.addEventListener('input', filterPosts);
    document.querySelector('[data-reset-search]')?.addEventListener('click', () => {
      search.value = '';
      selected = 'all';
      for (const button of filters) {
        const active = button.dataset.filter === 'all';
        button.classList.toggle('is-active', active);
        button.setAttribute('aria-pressed', String(active));
      }
      filterPosts();
      search.focus();
    });
    document.addEventListener('keydown', (event) => {
      const editable = event.target.closest('input,textarea,select,[contenteditable="true"]');
      if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !editable) {
        event.preventDefault();
        search.focus();
      }
    });
  }

  const status = document.createElement('span');
  status.className = 'sr-only';
  status.setAttribute('role', 'status');
  document.body.append(status);
  const copyText = async (text, button, original) => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.cssText = 'position:fixed;top:0;left:-9999px;';
        textarea.setAttribute('aria-label', '待复制的内容');
        document.body.append(textarea);
        textarea.select();
        let copied;
        try { copied = document.execCommand('copy'); } finally { textarea.remove(); button.focus(); }
        if (!copied) throw new Error('Copy not available');
      }
      button.textContent = '已复制 ✓';
      status.textContent = '已复制到剪贴板';
    } catch (_) {
      button.textContent = '复制失败，请手动复制';
      status.textContent = '无法访问剪贴板，请选择内容后手动复制';
    }
    window.setTimeout(() => { button.textContent = original; }, 2200);
  };
  for (const figure of document.querySelectorAll('.article-entry figure.highlight')) {
    const code = figure.querySelector('.code pre');
    if (!code) continue;
    const toolbar = document.createElement('div');
    toolbar.className = 'code-toolbar';
    const language = document.createElement('span');
    language.textContent = [...figure.classList].find((name) => name !== 'highlight')?.toUpperCase() || 'CODE';
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = '复制代码';
    button.setAttribute('aria-label', `复制 ${language.textContent} 代码`);
    button.addEventListener('click', () => copyText(code.innerText, button, '复制代码'));
    toolbar.append(language, button);
    const scroller = document.createElement('div');
    scroller.className = 'code-scroll';
    scroller.tabIndex = 0;
    scroller.setAttribute('role', 'region');
    scroller.setAttribute('aria-label', `${language.textContent} 代码，内容超宽时可横向滚动`);
    while (figure.firstChild) scroller.append(figure.firstChild);
    figure.append(toolbar, scroller);
  }
  document.querySelector('[data-copy-link]')?.addEventListener('click', (event) => {
    const canonical = document.querySelector('link[rel="canonical"]')?.href || location.href.split('#')[0];
    copyText(canonical, event.currentTarget, '复制文章链接 ↗');
  });

  const toc = document.querySelector('.article-toc');
  if (toc) {
    if (mobile.matches) toc.open = false;
    const links = [...toc.querySelectorAll('a')];
    const headings = links.map((link) => document.getElementById(decodeURIComponent(link.hash.slice(1)))).filter(Boolean);
    let scheduled = false;
    const updateCurrent = () => {
      scheduled = false;
      let current = headings[0];
      for (const heading of headings) {
        if (heading.getBoundingClientRect().top <= 145) current = heading;
      }
      for (const link of links) {
        const active = decodeURIComponent(link.hash.slice(1)) === current?.id;
        link.classList.toggle('is-current', active);
        if (active) link.setAttribute('aria-current', 'location'); else link.removeAttribute('aria-current');
      }
    };
    window.addEventListener('scroll', () => {
      if (!scheduled) { scheduled = true; requestAnimationFrame(updateCurrent); }
    }, { passive: true });
    toc.addEventListener('click', (event) => { if (mobile.matches && event.target.closest('a')) toc.open = false; });
    updateCurrent();
  }
})();
