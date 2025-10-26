// Управление сайдбаром
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const headerNav = document.querySelector('.header-nav');

    let isCollapsed = false;
    let pendingRaf = null;

    function measureNavFit() {
        if (!headerNav || !menuToggle) {
            return;
        }

        const header = document.querySelector('.header');
        const headerLeft = document.querySelector('.header-left');

        if (!header || !headerLeft) {
            return;
        }

        // Подготавливаем навигацию к измерению, делаем её невидимой, но сохраняем размеры
        headerNav.style.display = 'flex';
        headerNav.style.visibility = 'hidden';
        headerNav.style.position = 'absolute';
        headerNav.style.pointerEvents = 'none';

        const headerWidth = header.clientWidth;
        const headerLeftWidth = headerLeft.offsetWidth;
        const navWidth = headerNav.scrollWidth;
        const navRect = headerNav.getBoundingClientRect();
        const computedStyles = window.getComputedStyle(headerNav);
        const lineHeight = parseFloat(computedStyles.lineHeight) || navRect.height;

        // Учитываем небольшой запас в 16px (паддинги и возможные пробелы)
        const availableWidth = headerWidth - headerLeftWidth - 16;
        const shouldCollapse = navWidth > availableWidth || navRect.height > lineHeight + 4;

        // Возвращаем исходные стили после измерения
        headerNav.style.visibility = '';
        headerNav.style.position = '';
        headerNav.style.pointerEvents = '';

        if (shouldCollapse) {
            if (!isCollapsed) {
                header.classList.add('nav-collapsed');
                headerNav.style.display = 'none';
                menuToggle.style.display = 'flex';
                isCollapsed = true;
            }
        } else {
            if (isCollapsed) {
                header.classList.remove('nav-collapsed');
            }
            headerNav.style.display = 'flex';
            menuToggle.style.display = 'none';
            isCollapsed = false;
        }
    }

    function checkNavFit() {
        if (pendingRaf) {
            cancelAnimationFrame(pendingRaf);
        }
        pendingRaf = requestAnimationFrame(() => {
            pendingRaf = null;
            measureNavFit();
        });
    }

    // Инициализация: считаем, что навигация видима по умолчанию
    if (menuToggle) {
        menuToggle.style.display = 'none';
    }
    if (headerNav) {
        headerNav.style.display = 'flex';
    }

    setTimeout(checkNavFit, 100);

    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(checkNavFit, 150);
    });

    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            menuToggle.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    }

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

    const sidebarLinks = sidebar.querySelectorAll('a');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            closeSidebar();
        });
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && sidebar.classList.contains('active')) {
            closeSidebar();
        }
    });
});

