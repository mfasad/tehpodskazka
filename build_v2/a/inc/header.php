<style>
    .mobile-only-nav { display: none; }
    @media (max-width: 768px) { .mobile-only-nav { display: block; } }
    </style>
    <header class="site-header">
        <div class="container header-inner">
            <a href="/" class="logo">
                <span class="logo-icon">🔧</span>
                <span>tehpodskazka.vercel.app2</span>
            </a>
            <button class="mobile-menu-btn" aria-label="Меню" id="menuBtn">☰</button>
            <nav class="main-nav" id="mainNav">
                <a href="/category/nastroika-tv/" class="nav-link">📺 Настройка ТВ</a>
<a href="/category/mobilnye-os/" class="nav-link">📱 Мобильные ОС</a>
<a href="/category/windows-i-pk/" class="nav-link">💻 Windows и ПК</a>
<a href="/category/noutbuki-i-zhelezo/" class="nav-link">🖥️ Ноутбуки и Железо</a>
<a href="/category/striming-i-kino/" class="nav-link">🎬 Стриминг и Кино</a>
<a href="/category/svyaz-i-operatory/" class="nav-link">📡 Связь и Операторы</a>
<a href="/category/soft-i-prilozheniya/" class="nav-link mobile-only-nav">📲 Софт и Приложения</a>
<a href="/category/audio-i-gadzhety/" class="nav-link mobile-only-nav">🎧 Аудио и Гаджеты</a>
<a href="/category/akkaunty-i-bezopasnost/" class="nav-link mobile-only-nav">🔒 Аккаунты и Безопасность</a>
<a href="/category/igry-i-razvlecheniya/" class="nav-link mobile-only-nav">🎮 Игры и Развлечения</a>
<a href="/category/drugoe/" class="nav-link mobile-only-nav">📁 Другое</a>
            </nav>
        </div>
    </header>
<script>
(function(){
    var path = location.pathname;
    document.querySelectorAll('.main-nav .nav-link').forEach(function(a) {
        if (path.indexOf(a.getAttribute('href')) === 0) a.classList.add('active');
    });
})();
</script>