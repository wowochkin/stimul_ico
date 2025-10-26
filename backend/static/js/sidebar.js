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
        
        // Сначала скрываем навигацию и смотрим размер header без неё
        headerNav.style.display = 'none';
        const headerHeightWithoutNav = header.getBoundingClientRect().height;
        
        // Получаем размеры элементов header-left
        const headerLeftRect = headerLeft.getBoundingClientRect();
        
        // Теперь показываем навигацию
        headerNav.style.display = 'flex';
        
        // Небольшая задержка для корректного измерения после показа
        requestAnimationFrame(() => {
            const headerRect = header.getBoundingClientRect();
            const navRect = headerNav.getBoundingClientRect();
            
            // Проверяем, перенеслась ли навигация на новую строку по координатам
            const isNavOnNewLine = Math.abs(navRect.top - headerLeftRect.top) > 15;
            
            // Проверяем, увеличилась ли высота header
            const isHeaderMultiLine = headerRect.height > headerHeightWithoutNav + 15;
            
            // Также проверяем ширину - сумма заголовка и навигации не должна превышать header
            const totalWidth = headerLeftRect.width + navRect.width + 48; // 48px padding header
            const isWidthExceeded = totalWidth > headerRect.width;
            
            const isOverflowing = isHeaderMultiLine || isNavOnNewLine || isWidthExceeded;
            
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

