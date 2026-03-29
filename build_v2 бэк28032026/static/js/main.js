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
});
