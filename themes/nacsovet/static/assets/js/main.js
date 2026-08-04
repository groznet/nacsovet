// Глобальный обработчик кликов (Делегирование событий)
document.addEventListener('click', (e) => {
    
    // ==========================================
    // 1. МОБИЛЬНОЕ МЕНЮ (Header Burger)
    // ==========================================
    const mobileMenu = document.getElementById('mobileMenu');
    
    if (mobileMenu) {
        if (e.target.closest('#mobileMenuBtn')) {
            mobileMenu.classList.toggle('hidden');
            return;
        }

        if (e.target.closest('#mobileMenu a')) {
            mobileMenu.classList.add('hidden');
            return;
        }

        if (!mobileMenu.classList.contains('hidden') && 
            !e.target.closest('#mobileMenu') && 
            !e.target.closest('#mobileMenuBtn')) {
            mobileMenu.classList.add('hidden');
        }
    }

    // ==========================================
    // 2. ПЛАВНЫЙ СКРОЛЛ ПО ЯКОРЯМ
    // ==========================================
    const anchor = e.target.closest('a[href^="#"]');
    if (anchor) {
        const targetId = anchor.getAttribute('href');
        if (targetId !== "#" && targetId !== "" && targetId !== "/" && targetId.startsWith("#")) {
            e.preventDefault();
            document.querySelector(targetId)?.scrollIntoView({ behavior: 'smooth' });
        }
    }
});