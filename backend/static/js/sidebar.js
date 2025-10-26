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
        
        // Выполняем измерение в два шага через requestAnimationFrame для корректности
        // Шаг 1: скрываем навигацию и измеряем высоту без неё
        headerNav.style.display = 'none';
        
        requestAnimationFrame(() => {
            // Сразу в следующем кадре измеряем высоту без навигации
            const headerHeightWithoutNav = header.getBoundingClientRect().height;
            
            // Показываем навигацию
            headerNav.style.display = 'flex';
            
            // Еще один кадр для корректного измерения с навигацией
            requestAnimationFrame(() => {
                const headerRect = header.getBoundingClientRect();
                
                // Проверяем, увеличилась ли высота header (перенос на новую строку)
                const isHeaderMultiLine = headerRect.height > headerHeightWithoutNav + 15;
                
                // Если не умещается - скрываем навигацию и показываем кнопку
                if (isHeaderMultiLine) {
                    headerNav.style.display = 'none';
                    menuToggle.style.display = 'flex';
                    header.classList.add('nav-collapsed');
                } else {
                    headerNav.style.display = 'flex';
                    menuToggle.style.display = 'none';
                    header.classList.remove('nav-collapsed');
                }
            });
        });
    }

    // При загрузке скрываем всё для предотвращения мигания
    if (menuToggle) {
        menuToggle.style.display = 'none';
    }
    if (headerNav) {
        headerNav.style.display = 'none';
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

