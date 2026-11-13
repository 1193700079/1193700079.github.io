(() => {
  'use strict';
  const root = document.documentElement;
  const languageButton = document.querySelector('.language-button');
  const menuButton = document.querySelector('.menu-button');
  const navigation = document.querySelector('.primary-nav');
  const printButton = document.querySelector('.print-button');
  const setLanguage = (language) => {
    root.dataset.language = language;
    root.lang = language === 'zh' ? 'zh-CN' : 'en';
    languageButton.setAttribute('aria-pressed', String(language === 'zh'));
    languageButton.setAttribute('aria-label', language === 'zh' ? 'Switch to English' : '切换为中文');
    try { localStorage.setItem('profile-language', language); } catch (_) { /* Private browsing may disable storage. */ }
  };
  setLanguage(root.dataset.language || 'en');
  languageButton.addEventListener('click', () => setLanguage(root.dataset.language === 'zh' ? 'en' : 'zh'));
  const closeMenu = () => {
    navigation.classList.remove('is-open');
    menuButton.setAttribute('aria-expanded', 'false');
  };
  menuButton.addEventListener('click', () => {
    const open = navigation.classList.toggle('is-open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  navigation.addEventListener('click', (event) => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && navigation.classList.contains('is-open')) { closeMenu(); menuButton.focus(); } });
  document.addEventListener('click', (event) => { if (!event.target.closest('.header-inner')) closeMenu(); });
  if (printButton) printButton.addEventListener('click', () => window.print());
})();
