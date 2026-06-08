// Yandex.Metrika — counter 108292530
(function(){
  var s = document.createElement('script');
  s.src = 'https://mc.yandex.ru/metrika/tag.js';
  s.async = true;
  s.onload = function(){
    if (typeof window.ym !== 'function') return;
    window.ym(108292530, 'init', {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: true
    });
  };
  document.head.appendChild(s);
})();



// Market-Place sticker for tehpodskazka.vercel.app
(function () {
  var MPSU_SCRIPT_SRC = 'https://statika.mpsuadv.ru/scripts/11320.js';
  var STICKER_ID = 40392;

  function loadMpsuScript() {
    if (document.querySelector('script[src="' + MPSU_SCRIPT_SRC + '"]')) return;

    var script = document.createElement('script');
    script.async = true;
    script.src = MPSU_SCRIPT_SRC;
    document.head.appendChild(script);
  }

  function initSticker() {
    if (!document.body) return;
    if (document.getElementById('mp_custom_' + STICKER_ID)) return;

    loadMpsuScript();

    var block = document.createElement('div');
    block.id = 'mp_custom_' + STICKER_ID;
    document.body.appendChild(block);

    window.mpsuStart = window.mpsuStart || [];
    window.mpsuStart.push(STICKER_ID);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSticker);
  } else {
    initSticker();
  }
})();
// Market-Place / MPSU ads for tehpodskazka.vercel.app
// Articles only: horizontal after 1st and 5th paragraphs, sidebar vertical
(function () {
  var MPSU_SCRIPT_SRC = 'https://statika.mpsuadv.ru/scripts/11320.js';
  var HORIZONTAL_1_ID = 38993;
  var HORIZONTAL_2_ID = 38994;
  var VERTICAL_ID = 38995;

  function isArticlePage() {
    if (!document.body) return false;

    var bodyClass = document.body.classList;
    if (bodyClass.contains('home') || bodyClass.contains('is-home')) return false;
    if (bodyClass.contains('category') || bodyClass.contains('is-category')) return false;
    if (bodyClass.contains('archive') || bodyClass.contains('is-archive')) return false;

    return !!document.querySelector('article, .article-body');
  }

  function getArticleRoot() {
    return document.querySelector('article') || document.querySelector('.article-body');
  }

  function loadMpsuScript() {
    if (document.querySelector('script[src="' + MPSU_SCRIPT_SRC + '"]')) return;

    var script = document.createElement('script');
    script.async = true;
    script.src = MPSU_SCRIPT_SRC;
    document.head.appendChild(script);
  }

  function startWidget(widgetId) {
    window.mpsuStart = window.mpsuStart || [];
    window.mpsuStart.push(widgetId);
  }

  function createWidget(widgetId) {
    if (document.getElementById('mp_custom_' + widgetId)) return null;

    var block = document.createElement('div');
    block.id = 'mp_custom_' + widgetId;
    return block;
  }

  function insertAfterParagraph(widgetId, paragraphNumber) {
    var article = getArticleRoot();
    var paragraphs = article ? article.querySelectorAll('p') : [];

    if (paragraphs.length < paragraphNumber) return;

    var block = createWidget(widgetId);
    if (!block) return;

    paragraphs[paragraphNumber - 1].insertAdjacentElement('afterend', block);
    startWidget(widgetId);
  }

  function insertSidebarWidget(widgetId) {
    var sidebar = document.querySelector('aside, .sidebar, [class*="sidebar"], [id*="sidebar"]');
    if (!sidebar) return;

    var block = createWidget(widgetId);
    if (!block) return;

    sidebar.appendChild(block);
    startWidget(widgetId);
  }

  function initAds() {
    if (!isArticlePage()) return;

    loadMpsuScript();

    insertAfterParagraph(HORIZONTAL_1_ID, 1);
    insertAfterParagraph(HORIZONTAL_2_ID, 5);
    insertSidebarWidget(VERTICAL_ID);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAds);
  } else {
    initAds();
  }
})();
