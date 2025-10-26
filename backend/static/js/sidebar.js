// Управление сайдбаром
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const headerNav = document.querySelector('.header-nav');

    // Проверка, умещается ли навигация в одну строку
    function checkNavFit() {
        if (!headerNav || !menuToggle) return;
        
        const header = document.querySelector('.header');
        const headerLeft = document.querySelector('.header-left');
        
        if (!header || !headerLeft) return;
        
        // Временно показываем навигацию для измерения
        headerNav.style.display = 'flex';
        
        // Проверяем, выходит ли навигация за пределы header
        const headerRect = header.getBoundingClientRect();
        const navRect = headerNav.getBoundingClientRect();
        const headerLeftRect = headerLeft.getBoundingClientRect();
        
        // Вычисляем доступное пространство для навигации
        const availableWidth = headerRect.width - headerLeftRect.width - 20; // 20px отступ
        const navWidth = navRect.width;
        
        const isOverflowing = navWidth > availableWidth;
        
        // Если не умещается - скрываем навигацию и показываем кнопку
        if (isOverflowing) {
            headerNav.style.display = 'none';
            menuToggle.style.display = 'flex';
            header.classList.add('nav-collapsed');
        } else {
            headerNav.style.display = 'flex';
            menuToggle.style.display = 'none';
            header.classList.remove('nav-collapsed');
        }
    }

    // Первичная проверка с небольшой задержкой
    setTimeout(checkNavFit, 100);

    // Проверка при изменении размера окна
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(checkNavFit, 250);
    });

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
        if (menuToggle) {
            menuToggle.classList.remove('active');
        }
        document.body.style.overflow = '';
    }

    if (menuClose) {
        menuClose.addEventListener('click', closeSidebar);
    }

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Закрытие сайдбара при клике на ссылку
    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            closeSidebar();
        });
    });

    // Закрытие сайдбара клавишей Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
});

