// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const btn = document.getElementById('menuBtn');
    const nav = document.getElementById('mainNav');
    if (btn && nav) {
        btn.addEventListener('click', function() {
            nav.classList.toggle('open');
        });
    }

    // Sticky TOC active state
    const tocLinks = document.querySelectorAll('.sidebar-toc a');
    if (tocLinks.length) {
        const headings = [];
        tocLinks.forEach(link => {
            const id = link.getAttribute('href').replace('#', '');
            const el = document.getElementById(id);
            if (el) headings.push({ el, link });
        });

        let ticking = false;
        window.addEventListener('scroll', function() {
            if (!ticking) {
                requestAnimationFrame(function() {
                    let current = headings[0];
                    for (const h of headings) {
                        if (h.el.getBoundingClientRect().top <= 100) {
                            current = h;
                        }
                    }
                    tocLinks.forEach(l => l.classList.remove('active'));
                    if (current) current.link.classList.add('active');
                    ticking = false;
                });
                ticking = true;
            }
        });
    }

    // Poll click — "Спасибо за ответ!"
    document.querySelectorAll('.attention-box.attention-info ul li').forEach(function(li) {
        li.addEventListener('click', function() {
            const box = li.closest('.attention-box');
            if (box.classList.contains('voted')) return;
            box.classList.add('voted');
            // Highlight clicked
            li.style.background = '#2563eb';
            li.style.color = '#fff';
            li.style.borderColor = '#2563eb';
            // Add thanks message
            const thanks = document.createElement('p');
            thanks.textContent = '✅ Спасибо за ваш ответ!';
            thanks.style.cssText = 'margin-top:10px;color:#059669;font-weight:600;font-size:0.9em;';
            box.querySelector('div').appendChild(thanks);
        });
    });

    // Checklist — checkbox counter
    document.querySelectorAll('.checklist-block').forEach(function(block) {
        const checks = block.querySelectorAll('input[type="checkbox"]');
        const countEl = block.querySelector('.check-count');
        checks.forEach(function(cb) {
            cb.addEventListener('change', function() {
                const done = block.querySelectorAll('input:checked').length;
                if (countEl) countEl.textContent = done;
                const span = cb.nextElementSibling;
                if (cb.checked) {
                    span.style.textDecoration = 'line-through';
                    span.style.opacity = '0.6';
                } else {
                    span.style.textDecoration = 'none';
                    span.style.opacity = '1';
                }
            });
        });
    });

    // ============================================================
    //  SIDEBAR SEARCH (article pages)
    // ============================================================
    (function() {
        var input = document.getElementById('globalSearchInput');
        var dd = document.getElementById('globalSearchDropdown');
        if (!input || !dd) return;

        var searchData = null;
        var activeIdx = -1;
        var debounceTimer = null;

        function loadIndex(cb) {
            if (searchData) return cb(searchData);
            fetch('/static/js/search-index.json')
                .then(function(r) { return r.arrayBuffer(); })
                .then(function(buf) {
                    var text = new TextDecoder('utf-8').decode(buf);
                    var data = JSON.parse(text);
                    searchData = data.map(function(item) {
                        var title = (item.t || '').normalize('NFC');
                        return {
                            s: item.s,
                            t: title,
                            i: item.i || '📄',
                            tl: title.toLowerCase(),
                            sl: (item.s || '').toLowerCase()
                        };
                    });
                    cb(searchData);
                })
                .catch(function(err) {
                    console.error('Search index error:', err);
                    dd.innerHTML = '<div class="sd-empty">Ошибка загрузки</div>';
                    dd.style.display = 'block';
                });
        }

        function doSearch() {
            var q = input.value.normalize('NFC').toLowerCase().trim();
            if (q.length < 2) { dd.style.display = 'none'; activeIdx = -1; return; }

            loadIndex(function(data) {
                var words = q.split(/\s+/);
                var results = data.filter(function(item) {
                    return words.every(function(w) {
                        return item.tl.indexOf(w) !== -1 || item.sl.indexOf(w) !== -1;
                    });
                }).slice(0, 8);

                if (results.length === 0) {
                    dd.innerHTML = '<div class="sd-empty">🔍 Ничего не найдено</div>';
                } else {
                    dd.innerHTML = results.map(function(item) {
                        return '<a href="/' + item.s + '.html" class="sd-item">' +
                            '<div class="sd-icon">' + item.i + '</div>' +
                            '<div class="sd-title">' + item.t + '</div>' +
                            '</a>';
                    }).join('');
                }
                dd.style.display = 'block';
                activeIdx = -1;
            });
        }

        function updateActive() {
            var items = dd.querySelectorAll('.sd-item');
            items.forEach(function(el, i) {
                el.classList.toggle('sd-active', i === activeIdx);
            });
        }

        input.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(doSearch, 150);
        });

        input.addEventListener('focus', function() {
            if (input.value.trim().length >= 2) doSearch();
        });

        input.addEventListener('keydown', function(e) {
            var items = dd.querySelectorAll('.sd-item');
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeIdx = Math.min(activeIdx + 1, items.length - 1);
                updateActive();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeIdx = Math.max(activeIdx - 1, -1);
                updateActive();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (activeIdx >= 0 && items[activeIdx]) items[activeIdx].click();
                else if (items.length > 0) items[0].click();
            } else if (e.key === 'Escape') {
                dd.style.display = 'none';
                activeIdx = -1;
                input.blur();
            }
        });

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.sidebar-search-box')) {
                dd.style.display = 'none';
                activeIdx = -1;
            }
        });
    })();
});

// Yandex.Metrika
(function(m,e,t,r,i,k,a){
    m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
    m[i].l=1*new Date();
    for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}
    k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
})(window,document,'script','https://mc.yandex.ru/metrika/tag.js?id=108292530','ym');
ym(108292530,'init',{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true});


