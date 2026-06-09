// ============================================================
// Market-Place / MPSU ads for tehpodskazka.vercel.app
// Articles only: horizontal after 1st, 5th, and 9th paragraphs, corner sticker
(function () {
  var MPSU_SCRIPT_SRC = 'https://statika.mpsuadv.ru/scripts/11320.js';

  function isArticlePage() {
    if (!document.body) return false;
    if (document.body.classList.contains('home')) return false;
    if (document.body.classList.contains('category')) return false;
    if (document.body.classList.contains('archive')) return false;
    return !!document.querySelector('article, .article-body');
  }

  function getArticleRoot() {
    return document.querySelector('article') || document.querySelector('.article-body');
  }

  function loadMpsuScript() {
    var existingScript = document.querySelector('script[src="' + MPSU_SCRIPT_SRC + '"]');
    if (existingScript) return;
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
    var root = getArticleRoot();
    if (!root) return;
    var paragraphs = root.querySelectorAll('p');
    var target = paragraphs[paragraphNumber - 1];
    if (!target || !target.parentNode) return;
    var block = createWidget(widgetId);
    if (!block) return;
    target.parentNode.insertBefore(block, target.nextSibling);
    startWidget(widgetId);
  }

  function appendFloating(widgetId) {
    var block = createWidget(widgetId);
    if (!block) return;
    document.body.appendChild(block);
    startWidget(widgetId);
  }

  function initMpsuAds() {
    if (!isArticlePage()) return;
    loadMpsuScript();
    // Rotator Static ZBT tehpodskazka.vercel.app horizontal 1 ?38993
    insertAfterParagraph(38993, 1);
    // Rotator Static ZBT tehpodskazka.vercel.app horizontal 2 ?38994
    insertAfterParagraph(38994, 5);
    // Rotator Static ZBT tehpodskazka.vercel.app horizontal 3 ?40462
    insertAfterParagraph(40462, 9);
    // Rotator Recom V tehpodskazka.vercel.app corner sticker ?40392
    appendFloating(40392);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMpsuAds);
  } else {
    initMpsuAds();
  }
})();

// Yandex.Metrika — counter 108292530
(function(){
  var s = document.createElement('script');
  s.src = 'https://mc.yandex.ru/metrika/tag.js';
  s.async = true;
  s.onload = function(){
    ym(108292530, 'init', {
      clickmap: true,
      trackLinks: true,
      accurateTrackBounce: true,
      webvisor: true
    });
  };
  document.head.appendChild(s);
})();

