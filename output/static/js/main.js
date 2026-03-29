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
});
