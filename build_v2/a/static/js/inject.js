// VideoRoll — ad block after article body
(function(){
  var body = document.querySelector('.article-body');
  if (!body) return;

  var wrap = document.createElement('div');
  wrap.style.cssText = 'text-align:center;margin:16px 0 24px;overflow:hidden;';

  var ad = document.createElement('div');
  ad.id = 'vid_vpaut_div';
  ad.setAttribute('vid_vpaut_pl', '40562');
  ad.style.cssText = 'display:inline-block;width:600px;height:320px;max-width:100%;';

  wrap.appendChild(ad);
  body.parentNode.insertBefore(wrap, body.nextSibling);

  var vs = document.createElement('script');
  vs.src = 'https://videoroll.net/js/vid_vpaut_script.js';
  vs.async = true;
  document.head.appendChild(vs);
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
