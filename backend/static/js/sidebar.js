// Управление сайдбаром
document.addEventListener('DOMContentLoaded', function() {
    const header = document.querySelector('.header');
    const headerLeft = document.querySelector('.header-left');
    const headerContent = document.querySelector('.header-content');
    const headerNav = document.querySelector('.header-nav');
    const logoutForm = document.querySelector('.header-content .logout-form');

    const menuToggle = document.getElementById('menu-toggle');
    const menuClose = document.getElementById('menu-close');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    let pendingRaf = null;

    function prepareForMeasurement() {
        header.classList.remove('nav-collapsed');
        if (headerNav) {
            headerNav.style.display = 'flex';
        }
        if (logoutForm) {
            logoutForm.style.display = 'inline';
        }
        if (menuToggle) {
            menuToggle.style.display = 'none';
        }
    }

    function applyCollapsedState() {
        header.classList.add('nav-collapsed');
        if (headerNav) {
            headerNav.style.display = 'none';
        }
        if (logoutForm) {
            logoutForm.style.display = 'none';
        }
        if (menuToggle) {
            menuToggle.style.display = 'flex';
        }
    }

    function measureNavFit() {
        if (!header || !headerLeft || !headerContent || !headerNav || !menuToggle) {
            return;
        }

        prepareForMeasurement();

        // Даём браузеру время на рендер
        requestAnimationFrame(() => {
            const headerRect = header.getBoundingClientRect();
            const headerLeftRect = headerLeft.getBoundingClientRect();
            const navRect = headerNav.getBoundingClientRect();

            // Проверяем, умещается ли навигация в одну строку с заголовком
            const isOnSameLine = Math.abs(navRect.top - headerLeftRect.top) < 10;
            
            // Проверяем, не выходит ли за границы
            const fitsInWidth = (headerLeftRect.width + navRect.width + 40) <= headerRect.width;

            const shouldShowNav = isOnSameLine && fitsInWidth;

            if (!shouldShowNav) {
                applyCollapsedState();
            }
        });
    }

    function checkNavFit() {
        if (pendingRaf) {
            cancelAnimationFrame(pendingRaf);
        }
        pendingRaf = requestAnimationFrame(() => {
            pendingRaf = null;
            measureNavFit();
            if (header) {
                header.classList.remove('nav-initializing');
            }
        });
    }

    if (header) {
        header.classList.add('nav-initializing');
    }

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

