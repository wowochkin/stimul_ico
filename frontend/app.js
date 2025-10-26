(function () {
    const TOKEN_STORAGE_KEY = 'stimuliAuthToken';
    const API_BASE_URL = (window.STIMUL_API_BASE_URL || window.location.origin).replace(/\/$/, '');

    const state = {
        token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
        profile: null,
        employees: [],
        requests: [],
        campaigns: [],
        statuses: [],
    };

    const elements = {
        loginSection: document.getElementById('login-section'),
        dashboardSection: document.getElementById('dashboard-section'),
        employeesSection: document.getElementById('employees-section'),
        requestsSection: document.getElementById('requests-section'),
        requestFormSection: document.getElementById('request-form-section'),
        messagesSection: document.getElementById('messages-section'),
        messagesBox: document.getElementById('messages'),
        loginForm: document.getElementById('login-form'),
        logoutButton: document.getElementById('logout-button'),
        currentUser: document.getElementById('current-user'),
        employeeTable: document.getElementById('employees-table'),
        employeeSearch: document.getElementById('employee-search'),
        employeeCategoryFilter: document.getElementById('employee-category-filter'),
        requestTable: document.getElementById('requests-table'),
        reloadRequests: document.getElementById('reload-requests'),
        requestForm: document.getElementById('request-form'),
        requestEmployee: document.getElementById('request-employee'),
        requestCampaign: document.getElementById('request-campaign'),
        dashboardStats: document.getElementById('dashboard-stats'),
    };

    function canManageRequests() {
        if (!state.profile) {
            return false;
        }
        if (state.profile.is_staff) {
            return true;
        }
        return state.profile.groups.includes('Администраторы');
    }

    function requestHeaders(extra = {}) {
        const headers = {
            Accept: 'application/json',
            ...extra,
        };
        if (state.token) {
            headers.Authorization = `Token ${state.token}`;
        }
        return headers;
    }

    async function apiFetch(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
            headers: requestHeaders(options.headers || {}),
        };
        if (config.body && !(config.body instanceof FormData) && !config.headers['Content-Type']) {
            config.headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(url, config);
        if (response.status === 401) {
            handleLogout();
            throw new Error('Требуется повторная авторизация');
        }
        if (!response.ok) {
            let detail = 'Неизвестная ошибка';
            try {
                const payload = await response.json();
                detail = payload.detail || JSON.stringify(payload);
            } catch (error) {
                // ignore JSON parse errors
            }
            throw new Error(detail);
        }
        if (response.status === 204) {
            return null;
        }
        return response.json();
    }

    function showMessage(type, text) {
        if (!text) {
            return;
        }
        elements.messagesSection.hidden = false;
        const node = document.createElement('div');
        node.className = `message ${type}`;
        node.textContent = text;
        elements.messagesBox.prepend(node);
        setTimeout(() => {
            node.remove();
            if (!elements.messagesBox.children.length) {
                elements.messagesSection.hidden = true;
            }
        }, 8000);
    }

    function clearMessages() {
        elements.messagesBox.innerHTML = '';
        elements.messagesSection.hidden = true;
    }

    function updateAuthUI() {
        const isAuthenticated = Boolean(state.profile && state.token);
        elements.loginSection.hidden = isAuthenticated;
        elements.dashboardSection.hidden = !isAuthenticated;
        elements.employeesSection.hidden = !isAuthenticated;
        elements.requestsSection.hidden = !isAuthenticated;
        elements.requestFormSection.hidden = !isAuthenticated;
        elements.messagesSection.hidden = !isAuthenticated || !elements.messagesBox.children.length;
        elements.logoutButton.hidden = !isAuthenticated;
        elements.currentUser.textContent = isAuthenticated ? state.profile.full_name : 'Не авторизованы';
        if (!isAuthenticated) {
            clearMessages();
            elements.employeeTable.innerHTML = '';
            elements.requestTable.innerHTML = '';
            elements.requestForm.reset();
        }
    }

    function persistToken(token) {
        state.token = token;
        if (token) {
            localStorage.setItem(TOKEN_STORAGE_KEY, token);
        } else {
            localStorage.removeItem(TOKEN_STORAGE_KEY);
        }
    }

    function handleLogout() {
        persistToken('');
        state.profile = null;
        state.requests = [];
        state.employees = [];
        state.campaigns = [];
        state.statuses = [];
        updateAuthUI();
    }

    async function handleLogin(event) {
        event.preventDefault();
        const formData = new FormData(elements.loginForm);
        const payload = {
            username: formData.get('username'),
            password: formData.get('password'),
        };

        try {
            const data = await apiFetch('/api/auth/token/', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            persistToken(data.token);
            await bootstrap();
            showMessage('success', 'Авторизация прошла успешно. Данные обновлены.');
        } catch (error) {
            showMessage('error', error.message || 'Не удалось войти.');
        }
    }

    async function fetchProfile() {
        state.profile = await apiFetch('/api/auth/profile/');
        updateAuthUI();
    }

    function renderEmployees() {
        const searchValue = elements.employeeSearch.value.trim().toLowerCase();
        const categoryValue = elements.employeeCategoryFilter.value;

        const filtered = state.employees.filter((employee) => {
            const matchesSearch = !searchValue || `${employee.full_name} ${employee.justification || ''}`.toLowerCase().includes(searchValue);
            const matchesCategory = !categoryValue || employee.category === categoryValue;
            return matchesSearch && matchesCategory;
        });

        elements.employeeTable.innerHTML = '';
        if (!filtered.length) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.textContent = 'Сотрудники не найдены';
            row.appendChild(cell);
            elements.employeeTable.appendChild(row);
            return;
        }

        filtered.forEach((employee) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${employee.full_name}</td>
                <td>${employee.division_name || '—'}</td>
                <td>${employee.position_name || '—'}</td>
                <td>${employee.category_display}</td>
                <td>${formatCurrency(employee.payment)}</td>
            `;
            elements.employeeTable.appendChild(row);
        });
    }

    function formatCurrency(value) {
        const amount = Number(value || 0);
        return amount.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 2 });
    }

    function formatDate(value) {
        if (!value) {
            return '—';
        }
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return date.toLocaleString('ru-RU');
    }

    function renderRequestRow(item) {
        const row = document.createElement('tr');
        const badgeClass = `badge ${item.status}`;
        row.innerHTML = `
            <td>${item.employee_name}</td>
            <td>${formatCurrency(item.amount)}</td>
            <td><span class="${badgeClass}">${item.status_display}</span></td>
            <td>${item.justification || '—'}</td>
            <td>${item.admin_comment || '—'}</td>
            <td>${formatDate(item.created_at)}</td>
        `;

        const actionsCell = document.createElement('td');
        actionsCell.className = 'status-actions';

        if (canManageRequests()) {
            const select = document.createElement('select');
            state.statuses.forEach((status) => {
                const option = document.createElement('option');
                option.value = status.value;
                option.textContent = status.label;
                select.appendChild(option);
            });
            select.value = item.status;

            const applyButton = document.createElement('button');
            applyButton.type = 'button';
            applyButton.textContent = 'Обновить';
            applyButton.addEventListener('click', async () => {
                const adminComment = prompt('Комментарий администратора (можно оставить пустым):', item.admin_comment || '');
                await updateRequest(item.id, {
                    status: select.value,
                    admin_comment: adminComment || '',
                });
            });

            actionsCell.appendChild(select);
            actionsCell.appendChild(applyButton);
        } else if (item.is_editable) {
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.textContent = 'Удалить';
            deleteButton.addEventListener('click', async () => {
                const confirmed = confirm('Удалить заявку?');
                if (!confirmed) {
                    return;
                }
                await deleteRequest(item.id);
            });
            actionsCell.appendChild(deleteButton);
        } else {
            actionsCell.textContent = '—';
        }

        row.appendChild(actionsCell);
        return row;
    }

    function renderRequests() {
        elements.requestTable.innerHTML = '';
        if (!state.requests.length) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 7;
            cell.textContent = 'Заявки не найдены';
            row.appendChild(cell);
            elements.requestTable.appendChild(row);
            return;
        }

        state.requests.forEach((item) => {
            elements.requestTable.appendChild(renderRequestRow(item));
        });
    }

    function renderDashboard() {
        if (!state.profile) {
            elements.dashboardStats.textContent = '';
            return;
        }
        const userRequests = canManageRequests() ? state.requests : state.requests.filter((item) => item.requested_by === state.profile.id);
        const total = userRequests.length;
        const pending = userRequests.filter((item) => item.status === 'pending').length;
        const approved = userRequests.filter((item) => item.status === 'approved').length;
        const rejected = userRequests.filter((item) => item.status === 'rejected').length;

        elements.dashboardStats.innerHTML = `
            <div>Всего заявок: <strong>${total}</strong></div>
            <div>На рассмотрении: <strong>${pending}</strong></div>
            <div>Одобрено: <strong>${approved}</strong></div>
            <div>Отклонено: <strong>${rejected}</strong></div>
        `;
    }

    async function loadEmployees() {
        state.employees = await apiFetch('/api/employees/');
        populateEmployeesSelect();
        renderEmployees();
    }

    function populateEmployeesSelect() {
        elements.requestEmployee.innerHTML = '';
        state.employees.forEach((employee) => {
            const option = document.createElement('option');
            option.value = employee.id;
            option.textContent = employee.full_name;
            elements.requestEmployee.appendChild(option);
        });
    }

    async function loadRequests() {
        state.requests = await apiFetch('/api/requests/');
        renderRequests();
        renderDashboard();
    }

    async function loadCampaigns() {
        state.campaigns = await apiFetch('/api/campaigns/?status=active');
        elements.requestCampaign.innerHTML = '<option value="">Без кампании</option>';
        state.campaigns.forEach((campaign) => {
            const option = document.createElement('option');
            option.value = campaign.id;
            option.textContent = campaign.name;
            elements.requestCampaign.appendChild(option);
        });
    }

    async function loadStatuses() {
        state.statuses = await apiFetch('/api/requests/statuses/');
    }

    async function createRequest(event) {
        event.preventDefault();
        const formData = new FormData(elements.requestForm);
        const campaignValue = formData.get('campaign');
        
        if (!campaignValue) {
            showMessage('error', 'Необходимо выбрать кампанию.');
            return;
        }
        
        const payload = {
            employee: Number(formData.get('employee')),
            amount: Number(formData.get('amount')),
            justification: formData.get('justification'),
            campaign: Number(campaignValue),
        };

        try {
            await apiFetch('/api/requests/', {
                method: 'POST',
                body: JSON.stringify(payload),
            });
            elements.requestForm.reset();
            await loadRequests();
            showMessage('success', 'Заявка отправлена на рассмотрение.');
        } catch (error) {
            showMessage('error', error.message || 'Не удалось создать заявку.');
        }
    }

    async function updateRequest(id, data) {
        try {
            await apiFetch(`/api/requests/${id}/`, {
                method: 'PATCH',
                body: JSON.stringify(data),
            });
            await loadRequests();
            showMessage('success', 'Заявка обновлена.');
        } catch (error) {
            showMessage('error', error.message || 'Не удалось обновить заявку.');
        }
    }

    async function deleteRequest(id) {
        try {
            await apiFetch(`/api/requests/${id}/`, {
                method: 'DELETE',
            });
            await loadRequests();
            showMessage('success', 'Заявка удалена.');
        } catch (error) {
            showMessage('error', error.message || 'Не удалось удалить заявку.');
        }
    }

    async function bootstrap() {
        if (!state.token) {
            handleLogout();
            return;
        }
        try {
            await Promise.all([fetchProfile(), loadStatuses()]);
            await Promise.all([loadEmployees(), loadCampaigns(), loadRequests()]);
            showMessage('success', 'Данные загружены.');
        } catch (error) {
            showMessage('error', error.message);
        }
    }

    function attachEventListeners() {
        elements.loginForm.addEventListener('submit', handleLogin);
        elements.logoutButton.addEventListener('click', () => {
            handleLogout();
            showMessage('success', 'Вы вышли из системы.');
        });
        elements.employeeSearch.addEventListener('input', renderEmployees);
        elements.employeeCategoryFilter.addEventListener('change', renderEmployees);
        elements.reloadRequests.addEventListener('click', () => {
            loadRequests().catch((error) => showMessage('error', error.message));
        });
        elements.requestForm.addEventListener('submit', createRequest);
    }

    attachEventListeners();
    if (state.token) {
        bootstrap();
    } else {
        updateAuthUI();
    }
})();
