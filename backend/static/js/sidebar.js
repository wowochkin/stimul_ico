// Управление сайдбаром
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    // Открытие сайдбара
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            menuToggle.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

    // Закрытие сайдбара
    function closeSidebar() {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
        menuToggle.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (menuClose) {
        menuClose.addEventListener('click', closeSidebar);
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Закрытие сайдбара при клике на ссылку (только на мобильных)
    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });

    // Закрытие сайдбара при изменении размера окна
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });

    // Закрытие сайдбара клавишей Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
});

