

// ============================================================
//  HOTFIX: Fix search URL generation
//  Search results incorrectly include category slug in URL:
//    /voennaya-forma/kakie-berety.html
//  Correct format is hash_dirs:
//    /articles/k/ka/kakie-berety.html
//  This observer watches search dropdowns and fixes URLs.
// ============================================================
(function(){
    var dd = document.getElementById('globalSearchDropdown') || document.getElementById('searchDropdown');
    if (!dd) return;
    new MutationObserver(function(){
        var links = dd.querySelectorAll('a[href]');
        for (var i = 0; i < links.length; i++) {
            var a = links[i];
            if (a._urlFixed) continue;
            a._urlFixed = true;
            var href = a.getAttribute('href');
            if (!href) continue;
            if (href.indexOf('/articles/') !== -1) continue;
            var parts = href.split('/');
            var filename = parts[parts.length - 1];
            if (!filename.endsWith('.html')) continue;
            var slug = filename.replace('.html', '').toLowerCase();
            var c1 = slug[0] || '';
            var c2 = slug.substring(0, Math.min(2, slug.length));
            var newUrl = '/articles/' + c1 + '/' + c2 + '/' + filename;
            a.setAttribute('href', newUrl);
            var slugEl = a.querySelector('.sd-slug');
            if (slugEl) slugEl.textContent = newUrl;
        }
    }).observe(dd, {childList: true, subtree: true});
})();
