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
    // Rotator Static ZBT tehpodskazka.vercel.app горизонтальный 3 №40462
    insertAfterParagraph(40462, 9);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMpsuAds);
  } else {
    initMpsuAds();
  }
})();
