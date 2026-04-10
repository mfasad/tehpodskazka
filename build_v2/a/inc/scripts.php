<script>
    (function() {
        const popup = document.getElementById('cookie-consent');
        const btn = document.getElementById('cookie-accept');
        if (popup && btn && !localStorage.getItem('cookie-accepted')) {
            popup.classList.add('visible');
            btn.onclick = () => {
                localStorage.setItem('cookie-accepted', 'true');
                popup.classList.remove('visible');
            };
        }
    })();
    </script>