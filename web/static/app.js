// CrossFit Hub Web Admin

// Конфигурация
const API_URL = '/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let trainersList = [];
let currentWeekOffset = 0;  // 0 = текущая неделя, -1 = прошлая, +1 = следующая

// Утилиты
function showError(message) {
    alert('Ошибка: ' + message);
}

function showSuccess(message) {
    alert('Успешно: ' + message);
}

// Цвета для разных типов тренировок
function getWorkoutColor(workoutName) {
    const colors = {
        'CrossFit': '#8B1538',  // Темно-красный
        'CrossFit Beginners': '#5C6BC0',  // Синий
        'Weightlifting': '#388E3C',  // Зеленый
        'Thai Boxing': '#F57C00',  // Оранжевый
        'Yoga': '#8E24AA',  // Фиолетовый
        'Stretching': '#1565C0',  // Ярко-синий
        'CrossFit Football': '#C62828',  // Красный
    };
    
    return colors[workoutName] || '#757575';  // Серый по умолчанию
}

function formatDateTime(datetime) {
    const date = new Date(datetime);
    return date.toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// API запросы
async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        // Токен недействителен
        logout();
        return;
    }
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({detail: 'Unknown error'}));
        throw new Error(error.detail || 'Request failed');
    }
    
    // Если это DELETE запрос с 204, не пытаемся парсить JSON
    if (response.status === 204) {
        return null;
    }
    
    return await response.json();
}

// Авторизация
async function login(loginIdentifier, secretCode) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                login: String(loginIdentifier).trim(),
                secret_code: secretCode
            })
        });
        
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        updateUserInfo();
        return true;
    } catch (error) {
        showError(error.message);
        return false;
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    showLoginPage();
}

function updateUserInfo() {
    if (!currentUser) return;
    const roleLabels = { 'admin': 'Администратор', 'trainer': 'Тренер', 'athlete': 'Атлет' };
    const roleClasses = { 'admin': 'role-admin', 'trainer': 'role-trainer', 'athlete': 'role-athlete' };
    const label = roleLabels[currentUser.role] || currentUser.role;
    const cls = roleClasses[currentUser.role] || '';
    const el = document.getElementById('userName');
    if (el) {
        el.innerHTML = `<span class="user-name">${currentUser.full_name}</span><span class="role-badge ${cls}">${label}</span>`;
    }
}

// Тренировки
async function loadWorkouts(dateFrom, dateTo) {
    try {
        const params = new URLSearchParams();
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);
        
        const workouts = await apiRequest(`/workouts?${params}`);
        displayWorkouts(workouts);
    } catch (error) {
        showError('Не удалось загрузить тренировки: ' + error.message);
    }
}

function displayWorkouts(workouts) {
    const tbody = document.getElementById('workoutsTableBody');
    tbody.innerHTML = '';
    
    if (workouts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Тренировок не найдено</td></tr>';
        return;
    }
    
    workouts.forEach(workout => {
        const tr = document.createElement('tr');
        
        const occupancy = workout.current_participants / workout.max_participants;
        let badge = 'badge-success';
        if (occupancy >= 0.8) badge = 'badge-danger';
        else if (occupancy >= 0.5) badge = 'badge-warning';
        
        tr.innerHTML = `
            <td>${formatDateTime(workout.datetime)}</td>
            <td><strong>${workout.name}</strong></td>
            <td>${workout.duration} мин</td>
            <td>${workout.trainer_name || '<span style="color:#999;">— нет —</span>'}</td>
            <td>
                <span class="badge ${badge}">
                    ${workout.current_participants}/${workout.max_participants}
                </span>
            </td>
            <td>
                <div class="actions">
                    <button class="btn btn-sm btn-primary" onclick="viewWorkout(${workout.id})">👁️</button>
                    <button class="btn btn-sm btn-secondary" onclick="editWorkout(${workout.id})">✏️</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteWorkout(${workout.id})">🗑️</button>
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

async function createWorkout(workoutData) {
    try {
        await apiRequest('/workouts/', {
            method: 'POST',
            body: JSON.stringify(workoutData)
        });
        
        showSuccess('Тренировка создана!');
        closeModal('createWorkoutModal');
        loadTodayWorkouts();
        loadWeekWorkouts();
    } catch (error) {
        showError('Не удалось создать тренировку: ' + error.message);
    }
}

async function updateWorkout(workoutId, workoutData) {
    try {
        await apiRequest(`/workouts/${workoutId}`, {
            method: 'PUT',
            body: JSON.stringify(workoutData)
        });
        
        showSuccess('Тренировка обновлена!');
        closeModal('editWorkoutModal');
        loadTodayWorkouts();
        loadWeekWorkouts();
    } catch (error) {
        showError('Не удалось обновить тренировку: ' + error.message);
    }
}

async function deleteWorkout(workoutId) {
    if (!confirm('Вы уверены, что хотите удалить эту тренировку?')) {
        return;
    }
    
    try {
        await apiRequest(`/workouts/${workoutId}`, {
            method: 'DELETE'
        });
        
        showSuccess('Тренировка удалена!');
        closeModal('viewWorkoutModal');
        loadTodayWorkouts();
        loadWeekWorkouts();
    } catch (error) {
        showError('Не удалось удалить тренировку: ' + error.message);
    }
}

async function viewWorkout(workoutId) {
    try {
        const [workout, participants] = await Promise.all([
            apiRequest(`/workouts/${workoutId}`),
            apiRequest(`/workouts/${workoutId}/participants`)
        ]);
        
        // Показываем модальное окно с информацией
        const modal = document.getElementById('viewWorkoutModal');
        const content = document.getElementById('viewWorkoutContent');
        
        const occupancy = workout.current_participants / workout.max_participants;
        let statusColor = '#4CAF50';
        let statusText = 'Есть места';
        let statusEmoji = '🟢';
        
        if (occupancy >= 1.0) {
            statusColor = '#f44336';
            statusText = 'Занято';
            statusEmoji = '🔴';
        } else if (occupancy >= 0.8) {
            statusColor = '#ff9800';
            statusText = 'Мало мест';
            statusEmoji = '🟡';
        }
        
        const workoutDateTime = new Date(workout.datetime);
        const timeStr = workoutDateTime.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        const dateStr = workoutDateTime.toLocaleDateString('ru-RU', { 
            weekday: 'long', 
            day: 'numeric', 
            month: 'long' 
        });
        
        content.innerHTML = `
            <div style="border-left: 4px solid ${statusColor}; padding-left: 20px; margin-bottom: 20px;">
                <h2 style="margin: 0 0 10px 0; color: ${statusColor};">${statusEmoji} ${workout.name}</h2>
                <div style="font-size: 16px; color: #666;">
                    📅 ${dateStr}<br>
                    🕐 ${timeStr}<br>
                    ⏱ ${workout.duration} минут<br>
                    👤 Тренер: <strong>${workout.trainer_name || 'не назначен'}</strong>
                </div>
            </div>
            
            ${workout.description ? `
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <strong>📝 Описание:</strong><br>
                    ${workout.description}
                </div>
            ` : ''}
            
            <div style="background: linear-gradient(135deg, ${statusColor}, ${statusColor}dd); color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                <div style="font-size: 14px; opacity: 0.9; margin-bottom: 5px;">Участники</div>
                <div style="font-size: 32px; font-weight: bold;">${workout.current_participants}/${workout.max_participants}</div>
                <div style="font-size: 14px; opacity: 0.9;">${statusText}</div>
            </div>
            
            <h3 style="margin: 20px 0 15px 0;">👥 Список участников:</h3>
            ${participants.participants.length > 0 ? `
                <ul class="participants-list" style="max-height: 300px; overflow-y: auto;">
                    ${participants.participants.map((p, index) => `
                        <li style="padding: 12px; border-radius: 6px; margin-bottom: 8px; background: ${index % 2 === 0 ? '#f9f9f9' : 'white'};">
                            <div>
                                <span class="participant-name" style="font-size: 16px;">${index + 1}. ${p.full_name}</span><br>
                                ${p.username ? `<span class="participant-username" style="font-size: 13px; color: #888;">@${p.username}</span>` : ''}
                            </div>
                        </li>
                    `).join('')}
                </ul>
            ` : '<div style="text-align: center; padding: 40px; color: #999;">📋 Пока никто не записался</div>'}
            
            <div style="margin-top: 20px; padding-top: 20px; border-top: 2px solid #eee; display: flex; gap: 10px;">
                ${currentUser.role === 'admin' ? `
                    <button class="btn btn-secondary" onclick="closeModal('viewWorkoutModal'); editWorkout(${workout.id})">✏️ Редактировать</button>
                    <button class="btn btn-danger" onclick="closeModal('viewWorkoutModal'); deleteWorkout(${workout.id})">🗑️ Удалить</button>
                ` : ''}
                <button class="btn btn-primary" style="margin-left: auto;" onclick="closeModal('viewWorkoutModal')">Закрыть</button>
            </div>
        `;
        
        openModal('viewWorkoutModal');
    } catch (error) {
        showError('Не удалось загрузить информацию о тренировке: ' + error.message);
    }
}

async function editWorkout(workoutId) {
    try {
        const workout = await apiRequest(`/workouts/${workoutId}`);
        
        // Заполняем форму редактирования
        const form = document.getElementById('editWorkoutForm');
        form.elements['workout_id'].value = workout.id;
        form.elements['name'].value = workout.name;
        form.elements['description'].value = workout.description || '';
        
        // Конвертируем datetime в нужный формат для input datetime-local
        form.elements['datetime'].value = workout.datetime.slice(0, 16);
        
        form.elements['duration'].value = workout.duration;
        form.elements['max_participants'].value = workout.max_participants;

        // Устанавливаем тренера в dropdown
        const editTrainerSelect = document.getElementById('editTrainerSelect');
        if (editTrainerSelect) {
            editTrainerSelect.value = workout.trainer_id || '';
        }

        openModal('editWorkoutModal');
    } catch (error) {
        showError('Не удалось загрузить тренировку: ' + error.message);
    }
}

async function bulkCreateSchedule(weeks) {
    if (!confirm(`Создать расписание на ${weeks} недель?`)) {
        return;
    }
    
    try {
        const result = await apiRequest('/workouts/bulk-create', {
            method: 'POST',
            body: JSON.stringify({ weeks: parseInt(weeks) })
        });
        
        console.log('📅 Результат создания расписания:', result);
        console.log('📊 Создано по датам:', result.created_by_date);
        console.log('🔍 Debug:', result.debug);
        
        let message = `Создано ${result.created} тренировок (пропущено ${result.skipped})`;
        if (result.debug) {
            message += `\n\nОтладка:\n`;
            message += `Сегодня: ${result.debug.today} (день недели: ${result.debug.today_weekday})\n`;
            message += `Начало: ${result.debug.start_date} (день недели: ${result.debug.start_weekday})`;
        }
        
        showSuccess(message);
        loadTodayWorkouts();
        loadWeekWorkouts();
    } catch (error) {
        showError('Не удалось создать расписание: ' + error.message);
    }
}

async function deleteWorkoutsByRange() {
    const dateFrom = document.getElementById('deleteRangeFrom').value;
    const dateTo = document.getElementById('deleteRangeTo').value;
    
    if (!dateFrom || !dateTo) {
        showError('Выберите даты ОТ и ДО');
        return;
    }
    
    if (dateFrom > dateTo) {
        showError('Дата ОТ должна быть раньше или равна дате ДО');
        return;
    }
    
    if (!confirm(`⚠️ Удалить тренировки с ${dateFrom} по ${dateTo}?\n\nЭто действие необратимо!`)) {
        return;
    }
    
    const btn = document.getElementById('btnDeleteRange');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Удаление...';
    
    try {
        const result = await apiRequest('/workouts/delete-by-range', {
            method: 'POST',
            body: JSON.stringify({
                date_from: dateFrom,
                date_to: dateTo
            })
        });
        
        showSuccess(`✅ ${result.message}`);
        
        // Очищаем поля
        document.getElementById('deleteRangeFrom').value = '';
        document.getElementById('deleteRangeTo').value = '';
        
        // Обновляем все виды
        loadTodayWorkouts();
        loadWeekWorkouts();
    } catch (error) {
        showError('Ошибка удаления: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

async function clearAllWorkouts() {
    // Двойное подтверждение для критической операции
    if (!confirm('⚠️ ВНИМАНИЕ! Это удалит ВСЕ тренировки и записи!\n\nПродолжить?')) {
        return;
    }
    
    if (!confirm('Вы действительно уверены? Это действие необратимо!')) {
        return;
    }
    
    const btn = document.getElementById('btnClearAll');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Удаление...';
    
    try {
        const result = await apiRequest('/workouts/clear-all', {
            method: 'POST'
        });
        
        showSuccess(`✅ Удалено: ${result.deleted_workouts} тренировок и ${result.deleted_bookings} записей`);
        
        // Обновляем все виды
        loadTodayWorkouts();
        loadWeekWorkouts();
    } catch (error) {
        showError('Ошибка очистки: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// Пользователи
async function loadUsers() {
    if (currentUser.role !== 'admin') {
        return;
    }
    
    try {
        const users = await apiRequest('/users/');
        displayUsers(users);
        
        const stats = await apiRequest('/users/stats/summary');
        displayUserStats(stats);
    } catch (error) {
        showError('Не удалось загрузить пользователей: ' + error.message);
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';
    
    users.forEach(user => {
        const tr = document.createElement('tr');
        
        const roleEmoji = {
            'athlete': '🏋️',
            'trainer': '🤸‍♀️',
            'admin': '👑'
        }[user.role] || '👤';
        
        const staff = user.role === 'trainer' || user.role === 'admin';
        const pwdHint = user.has_web_password ? ' (есть)' : '';
        tr.innerHTML = `
            <td>${user.id}</td>
            <td><strong>${user.full_name}</strong></td>
            <td>${user.username ? '@' + user.username : '-'}</td>
            <td>${roleEmoji} ${user.role}</td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="actions">
                    ${staff ? `<button type="button" class="btn btn-sm btn-secondary" title="Индивидуальный пароль веб-панели" onclick="setUserWebPassword(${user.id})">🔑 Пароль${pwdHint}</button>` : ''}
                    <button class="btn btn-sm btn-secondary" onclick="changeUserRole(${user.id}, '${user.role}')">Изменить роль</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id}, '${user.full_name.replace(/'/g, "\\'")}')">Удалить</button>
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
}

function displayUserStats(stats) {
    const container = document.getElementById('userStats');
    container.innerHTML = `
        <div class="stat-card">
            <h3>${stats.total}</h3>
            <p>Всего пользователей</p>
        </div>
        <div class="stat-card success">
            <h3>${stats.by_role.athlete || 0}</h3>
            <p>Атлетов</p>
        </div>
        <div class="stat-card warning">
            <h3>${stats.by_role.trainer || 0}</h3>
            <p>Тренеров</p>
        </div>
    `;
}

let _changeRoleUserId = null;
let _changeRoleCurrentRole = null;

function changeUserRole(userId, currentRole) {
    _changeRoleUserId = userId;
    _changeRoleCurrentRole = currentRole;
    const select = document.getElementById('roleSelect');
    select.value = currentRole;
    openModal('changeRoleModal');
}

async function confirmRoleChange() {
    const newRole = document.getElementById('roleSelect').value;
    if (!newRole || newRole === _changeRoleCurrentRole) {
        closeModal('changeRoleModal');
        return;
    }
    try {
        await apiRequest(`/users/${_changeRoleUserId}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role: newRole })
        });
        closeModal('changeRoleModal');
        showSuccess('Роль пользователя изменена!');
        loadUsers();
    } catch (error) {
        showError('Не удалось изменить роль: ' + error.message);
    }
}
window.confirmRoleChange = confirmRoleChange;

async function setUserWebPassword(userId) {
    const pw = prompt('Новый пароль для входа в веб-панель (минимум 4 символа):');
    if (pw === null) return;
    if (String(pw).length < 4) {
        showError('Пароль не короче 4 символов');
        return;
    }
    try {
        await apiRequest(`/users/${userId}/password`, {
            method: 'PATCH',
            body: JSON.stringify({ password: String(pw) })
        });
        showSuccess('Пароль сохранён');
        loadUsers();
    } catch (error) {
        showError(error.message);
    }
}

async function deleteUser(userId, userName) {
    if (!confirm(`Удалить пользователя "${userName}"?\n\nЭто действие необратимо:\n— записи на тренировки будут удалены\n— тренировки, где он тренер, станут без тренера`)) {
        return;
    }
    try {
        await apiRequest(`/users/${userId}`, { method: 'DELETE' });
        showSuccess(`Пользователь "${userName}" удалён`);
        loadUsers();
    } catch (error) {
        showError('Не удалось удалить пользователя: ' + error.message);
    }
}

// Модальные окна
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Вкладки
function switchTab(tabName) {
    // Скрываем все вкладки
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Показываем нужную вкладку
    document.getElementById(tabName).classList.add('active');
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
    
    // Загружаем данные
    if (tabName === 'today') {
        loadTodayWorkouts();
    } else if (tabName === 'week') {
        loadWeekWorkouts();
    } else if (tabName === 'users') {
        loadUsers();
    } else if (tabName === 'template') {
        loadTemplate();
    } else if (tabName === 'scheduleImage') {
        loadScheduleImage();
    } else if (tabName === 'gymSettings') {
        loadGymSettings();
    }
}

async function loadGymSettings() {
    const el = document.getElementById('gymSettingsBody');
    if (!el) return;
    el.innerHTML = '<div class="loading">Загрузка...</div>';
    try {
        const s = await apiRequest('/settings');
        el.innerHTML = `
            <div class="form-group">
                <label>Максимум записей атлета в один календарный день</label>
                <input type="number" class="form-control" id="maxBookingsPerDay" min="1" max="20"
                    value="${s.max_bookings_per_day}">
                <p class="hint" style="margin-top:8px;font-size:0.9em;color:#666;">
                    Действует для бота при записи атлетов. От 1 до 20.
                </p>
            </div>
            <button type="button" class="btn btn-primary" onclick="saveGymSettings()">Сохранить</button>
        `;
    } catch (e) {
        el.innerHTML = `<div class="alert alert-error">Ошибка: ${e.message}</div>`;
    }
}

async function saveGymSettings() {
    const raw = document.getElementById('maxBookingsPerDay');
    if (!raw) return;
    const maxBookingsPerDay = parseInt(raw.value, 10);
    if (Number.isNaN(maxBookingsPerDay) || maxBookingsPerDay < 1 || maxBookingsPerDay > 20) {
        showError('Введите число от 1 до 20');
        return;
    }
    try {
        await apiRequest('/settings', {
            method: 'PATCH',
            body: JSON.stringify({ max_bookings_per_day: maxBookingsPerDay })
        });
        showSuccess('Настройки сохранены');
        loadGymSettings();
    } catch (e) {
        showError(e.message);
    }
}

// ─── Шаблон расписания ────────────────────────────────────────────────────────

const DAY_NAMES = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];

async function loadTemplate() {
    const container = document.getElementById('templateTable');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    try {
        const slots = await apiRequest('/schedule-template/');
        displayTemplate(slots);
    } catch (e) {
        container.innerHTML = `<div class="alert alert-error">Ошибка: ${e.message}</div>`;
    }
}

function displayTemplate(slots) {
    const container = document.getElementById('templateTable');
    if (!slots.length) {
        container.innerHTML = '<div style="padding:20px;color:#999;">Шаблон пуст. Добавьте слоты или загрузите из файла.</div>';
        return;
    }

    // Группируем по дням
    const byDay = {};
    slots.forEach(s => {
        if (!byDay[s.day_of_week]) byDay[s.day_of_week] = [];
        byDay[s.day_of_week].push(s);
    });

    let html = '';
    for (let day = 0; day <= 6; day++) {
        const daySlots = byDay[day] || [];
        if (!daySlots.length) continue;
        html += `<div style="margin-bottom:20px;">
            <h3 style="margin-bottom:8px; color:#555;">${DAY_NAMES[day]}</h3>
            <table style="width:100%; border-collapse:collapse; font-size:14px;">
                <thead>
                    <tr style="background:#f0f0f0;">
                        <th style="padding:8px; text-align:left; border:1px solid #ddd;">Время</th>
                        <th style="padding:8px; text-align:left; border:1px solid #ddd;">Название</th>
                        <th style="padding:8px; text-align:center; border:1px solid #ddd;">Мин</th>
                        <th style="padding:8px; text-align:center; border:1px solid #ddd;">Макс</th>
                        <th style="padding:8px; text-align:center; border:1px solid #ddd;"></th>
                    </tr>
                </thead>
                <tbody>
                    ${daySlots.map(s => `
                    <tr id="slot-row-${s.id}">
                        <td style="padding:8px; border:1px solid #ddd;">${s.time}</td>
                        <td style="padding:8px; border:1px solid #ddd;">${s.name}</td>
                        <td style="padding:8px; border:1px solid #ddd; text-align:center;">${s.duration}</td>
                        <td style="padding:8px; border:1px solid #ddd; text-align:center;">${s.max_participants}</td>
                        <td style="padding:8px; border:1px solid #ddd; text-align:center; white-space:nowrap;">
                            <button class="btn btn-secondary btn-sm" onclick="editTemplateSlot(${s.id}, '${s.time}', '${s.name.replace(/'/g, "\\'")}', ${s.duration}, ${s.max_participants}, ${s.day_of_week})">✏️</button>
                            <button class="btn btn-danger btn-sm" onclick="deleteTemplateSlot(${s.id})">🗑️</button>
                        </td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>`;
    }
    container.innerHTML = html;
}

function openAddSlotForm() {
    document.getElementById('addSlotForm').style.display = 'block';
}

async function saveNewSlot() {
    const day = parseInt(document.getElementById('slotDay').value);
    const time = document.getElementById('slotTime').value.trim();
    const name = document.getElementById('slotName').value.trim();
    const duration = parseInt(document.getElementById('slotDuration').value);
    const max = parseInt(document.getElementById('slotMax').value);

    if (!time || !name) { showError('Заполните время и название'); return; }
    if (!/^\d{2}:\d{2}$/.test(time)) { showError('Время должно быть в формате ЧЧ:ММ'); return; }

    try {
        await apiRequest('/schedule-template/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({day_of_week: day, time, name, duration, max_participants: max}),
        });
        document.getElementById('addSlotForm').style.display = 'none';
        showSuccess('Слот добавлен');
        loadTemplate();
    } catch (e) {
        showError(e.message);
    }
}

function editTemplateSlot(slotId, time, name, duration, maxParticipants, dayOfWeek) {
    const row = document.getElementById(`slot-row-${slotId}`);
    if (!row) return;
    row.innerHTML = `
        <td style="padding:8px; border:1px solid #ddd;">
            <input type="text" id="edit-time-${slotId}" value="${time}" style="width:60px; padding:4px;" pattern="\\d{2}:\\d{2}">
        </td>
        <td style="padding:8px; border:1px solid #ddd;">
            <input type="text" id="edit-name-${slotId}" value="${name}" style="width:100%; padding:4px;">
        </td>
        <td style="padding:8px; border:1px solid #ddd; text-align:center;">
            <input type="number" id="edit-dur-${slotId}" value="${duration}" style="width:60px; padding:4px;" min="10" max="300">
        </td>
        <td style="padding:8px; border:1px solid #ddd; text-align:center;">
            <input type="number" id="edit-max-${slotId}" value="${maxParticipants}" style="width:60px; padding:4px;" min="1" max="200">
        </td>
        <td style="padding:8px; border:1px solid #ddd; text-align:center; white-space:nowrap;">
            <button class="btn btn-success btn-sm" onclick="updateTemplateSlot(${slotId})">💾</button>
            <button class="btn btn-secondary btn-sm" onclick="loadTemplate()">✖</button>
        </td>
    `;
}

async function updateTemplateSlot(slotId) {
    const time = document.getElementById(`edit-time-${slotId}`).value.trim();
    const name = document.getElementById(`edit-name-${slotId}`).value.trim();
    const duration = parseInt(document.getElementById(`edit-dur-${slotId}`).value);
    const maxParticipants = parseInt(document.getElementById(`edit-max-${slotId}`).value);

    if (!time || !name) { showError('Заполните время и название'); return; }
    if (!/^\d{2}:\d{2}$/.test(time)) { showError('Время должно быть в формате ЧЧ:ММ'); return; }

    try {
        await apiRequest(`/schedule-template/${slotId}`, {
            method: 'PUT',
            body: JSON.stringify({ time, name, duration, max_participants: maxParticipants }),
        });
        showSuccess('Слот обновлён');
        loadTemplate();
    } catch (e) {
        showError(e.message);
    }
}

async function deleteTemplateSlot(slotId) {
    if (!confirm('Удалить этот слот из шаблона?')) return;
    try {
        await apiRequest(`/schedule-template/${slotId}`, {method: 'DELETE'});
        showSuccess('Слот удалён');
        loadTemplate();
    } catch (e) {
        showError(e.message);
    }
}

async function seedTemplateFromFile() {
    if (!confirm('Загрузить шаблон из create_weekly_schedule.py? Действие пропускается, если шаблон уже заполнен.')) return;
    try {
        const result = await apiRequest('/schedule-template/seed-from-file', {method: 'POST'});
        showSuccess(result.message || `Создано ${result.created} слотов`);
        loadTemplate();
    } catch (e) {
        showError(e.message);
    }
}

async function seedTemplateFromFileForce() {
    if (!confirm('Очистить весь шаблон и загрузить заново из create_weekly_schedule.py?\nЭто действие необратимо.')) return;
    try {
        const result = await apiRequest('/schedule-template/seed-from-file?force=true', {method: 'POST'});
        showSuccess(`Шаблон перезаписан. Создано ${result.created} слотов`);
        loadTemplate();
    } catch (e) {
        showError(e.message);
    }
}

// ─── Картинка расписания ─────────────────────────────────────────────────────

async function loadScheduleImage() {
    const statusEl = document.getElementById('scheduleImageStatus');
    const previewEl = document.getElementById('scheduleImagePreview');
    const deleteBtn = document.getElementById('deleteScheduleImageBtn');
    try {
        const data = await apiRequest('/schedule-image/status');
        if (data.exists) {
            statusEl.innerHTML = `<div class="alert alert-success">✅ Изображение загружено: <b>${data.filename}</b></div>`;
            previewEl.innerHTML = `<img src="/api/schedule-image/file" alt="Расписание"
                style="max-width:100%;max-height:500px;border-radius:8px;border:1px solid #ddd;">`;
            deleteBtn.style.display = 'inline-block';
        } else {
            statusEl.innerHTML = `<div class="alert alert-warning">⚠️ Изображение не загружено</div>`;
            previewEl.innerHTML = '';
            deleteBtn.style.display = 'none';
        }
    } catch (e) {
        statusEl.innerHTML = `<div class="alert alert-error">Ошибка: ${e.message}</div>`;
    }
}

async function uploadScheduleImage() {
    const fileInput = document.getElementById('scheduleImageFile');
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_URL}/schedule-image/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData,
        });
        if (!response.ok) {
            const err = await response.json().catch(() => ({detail: 'Ошибка загрузки'}));
            throw new Error(err.detail);
        }
        showSuccess('Изображение успешно загружено');
        fileInput.value = '';
        loadScheduleImage();
    } catch (e) {
        showError(e.message);
    }
}

async function deleteScheduleImage() {
    if (!confirm('Удалить изображение расписания?')) return;
    try {
        await apiRequest('/schedule-image/', {method: 'DELETE'});
        showSuccess('Изображение удалено');
        loadScheduleImage();
    } catch (e) {
        showError(e.message);
    }
}

// ─── Список тренеров (для dropdown) ─────────────────────────────────────────

async function loadTrainers() {
    if (currentUser.role !== 'admin') return;
    try {
        const trainers = await apiRequest('/users/?role=trainer');
        const admins = await apiRequest('/users/?role=admin');
        trainersList = [...admins, ...trainers];
        populateTrainerSelects();
    } catch (e) {
        console.warn('Не удалось загрузить список тренеров:', e.message);
    }
}

function populateTrainerSelects() {
    const selects = document.querySelectorAll('#createTrainerSelect, #editTrainerSelect');
    selects.forEach(sel => {
        const currentValue = sel.value;
        sel.innerHTML = '<option value="">— Без тренера —</option>';
        trainersList.forEach(t => {
            const roleLabel = t.role === 'admin' ? ' (админ)' : '';
            sel.innerHTML += `<option value="${t.id}">${t.full_name}${roleLabel}</option>`;
        });
        sel.value = currentValue;
    });
}

// Загрузка тренировок на сегодня
async function loadTodayWorkouts() {
    const container = document.getElementById('todayWorkouts');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    const today = formatDateLocal(new Date());
    
    console.log('📅 Загрузка сегодняшних тренировок:', today);
    
    try {
        const workouts = await apiRequest(`/workouts/?date_from=${today}&date_to=${today}`);
        console.log('📊 Получено тренировок на сегодня:', workouts.length);
        displayTodayWorkouts(workouts);
    } catch (error) {
        container.innerHTML = `<div class="alert alert-error">Ошибка загрузки: ${error.message}</div>`;
        console.error('Load today workouts error:', error);
    }
}

function displayTodayWorkouts(workouts) {
    const container = document.getElementById('todayWorkouts');
    
    // Обновляем заголовок с датой
    const today = new Date();
    const weekdays = ['Воскресенье', 'Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота'];
    document.getElementById('todayDate').textContent = 
        `Сегодня - ${weekdays[today.getDay()]}, ${today.toLocaleDateString('ru-RU')}`;
    
    if (workouts.length === 0) {
        container.innerHTML = '<div class="no-workouts">📅 На сегодня тренировок нет</div>';
        return;
    }
    
    container.innerHTML = workouts.map(workout => {
        const occupancy = workout.current_participants / workout.max_participants;
        let statusClass = 'available';
        let statusEmoji = '🟢';
        
        if (occupancy >= 1.0) {
            statusClass = 'full';
            statusEmoji = '🔴';
        } else if (occupancy >= 0.8) {
            statusClass = 'warning';
            statusEmoji = '🟡';
        }
        
        const time = new Date(workout.datetime).toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        const workoutColor = getWorkoutColor(workout.name);
        
        return `
            <div class="workout-card" onclick="viewWorkout(${workout.id})" style="border-left: 6px solid ${workoutColor};">
                <div class="workout-card-status ${statusClass}"></div>
                <div class="workout-card-time">${time}</div>
                <div class="workout-card-name" style="color: ${workoutColor};">${workout.name}</div>
                <div class="workout-card-trainer">${workout.trainer_name ? '👤 ' + workout.trainer_name : '<span style="color:#999;">— без тренера —</span>'}</div>
                <div class="workout-card-stats">
                    <div class="workout-card-participants">
                        ${statusEmoji} ${workout.current_participants}/${workout.max_participants}
                    </div>
                    <div class="workout-card-duration">
                        ⏱ ${workout.duration} мин
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Хелпер для форматирования даты в YYYY-MM-DD без UTC-сдвига
function formatDateLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// ─── Навигация по неделям ─────────────────────────────────────────────────────

function getWeekMonday(offset) {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    const monday = new Date(today);
    monday.setDate(today.getDate() - daysFromMonday + (offset * 7));
    monday.setHours(0, 0, 0, 0);
    return monday;
}

function navigateWeek(direction) {
    if (direction === 0) {
        currentWeekOffset = 0;
    } else {
        currentWeekOffset += direction;
    }
    loadWeekWorkouts();
}

function updateWeekLabel(monday, sunday) {
    const label = document.getElementById('weekRangeLabel');
    if (!label) return;
    const fmt = d => `${d.getDate()}.${String(d.getMonth() + 1).padStart(2, '0')}`;
    const monthNames = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'];
    const text = `${fmt(monday)} — ${fmt(sunday)} ${monthNames[sunday.getMonth()]} ${sunday.getFullYear()}`;
    label.textContent = currentWeekOffset === 0 ? `📍 ${text}` : text;
    label.style.color = currentWeekOffset === 0 ? '' : '#1976d2';
}

// Загрузка тренировок на неделю
async function loadWeekWorkouts() {
    const container = document.getElementById('weekWorkouts');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    const monday = getWeekMonday(currentWeekOffset);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    
    const dateFrom = formatDateLocal(monday);
    const dateTo = formatDateLocal(sunday);
    
    updateWeekLabel(monday, sunday);
    
    try {
        const workouts = await apiRequest(`/workouts/?date_from=${dateFrom}&date_to=${dateTo}`);
        displayWeekWorkouts(workouts, monday);
    } catch (error) {
        container.innerHTML = `<div class="alert alert-error">Ошибка загрузки: ${error.message}</div>`;
    }
}

function displayWeekWorkouts(workouts, mondayOverride) {
    const container = document.getElementById('weekWorkouts');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const monday = mondayOverride || getWeekMonday(currentWeekOffset);
    
    // Группируем тренировки по дням
    const workoutsByDate = {};
    workouts.forEach(workout => {
        const date = workout.datetime.split('T')[0];
        if (!workoutsByDate[date]) {
            workoutsByDate[date] = [];
        }
        workoutsByDate[date].push(workout);
    });
    
    // Создаём 7 дней (с понедельника по воскресенье)
    const days = [];
    for (let i = 0; i < 7; i++) {
        const date = new Date(monday);
        date.setDate(monday.getDate() + i);
        days.push(date);
    }
    
    console.log('📆 Отображаемые дни:');
    days.forEach((d, i) => {
        console.log(`  ${i}: ${formatDateLocal(d)} (${['Вс','Пн','Вт','Ср','Чт','Пт','Сб'][d.getDay()]})`);
    });
    
    const weekdays = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    
    container.innerHTML = days.map(date => {
        const dateStr = formatDateLocal(date);
        const dayWorkouts = workoutsByDate[dateStr] || [];
        const isToday = date.toDateString() === today.toDateString();
        
        return `
            <div class="day-column ${isToday ? 'today' : ''}">
                <div class="day-column-header">
                    <div class="day-column-weekday">${weekdays[date.getDay()]}</div>
                    <div class="day-column-date">${date.getDate()}.${String(date.getMonth() + 1).padStart(2, '0')}</div>
                </div>
                <div class="day-column-workouts">
                    ${dayWorkouts.length > 0 ? dayWorkouts.map(workout => {
                        const occupancy = workout.current_participants / workout.max_participants;
                        let statusClass = 'available';
                        
                        if (occupancy >= 1.0) {
                            statusClass = 'full';
                        } else if (occupancy >= 0.8) {
                            statusClass = 'warning';
                        }
                        
                        const time = new Date(workout.datetime).toLocaleTimeString('ru-RU', { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                        });
                        
                        const workoutColor = getWorkoutColor(workout.name);
                        
                        return `
                            <div class="mini-workout-card ${statusClass}" onclick="viewWorkout(${workout.id})" style="border-left-color: ${workoutColor};">
                                <div class="mini-workout-time" style="color: ${workoutColor};">${time}</div>
                                <div class="mini-workout-name">${workout.name}</div>
                                <div class="mini-workout-trainer">${workout.trainer_name ? '👤 ' + workout.trainer_name : '<span style="color:#999;">без тренера</span>'}</div>
                                <div class="mini-workout-info">
                                    <span>${workout.current_participants}/${workout.max_participants}</span>
                                    <span>${workout.duration}м</span>
                                </div>
                            </div>
                        `;
                    }).join('') : '<div class="no-workouts">Нет тренировок</div>'}
                </div>
            </div>
        `;
    }).join('');
}

// Отображение страниц
function showLoginPage() {
    document.body.innerHTML = `
        <div class="login-container">
            <div class="login-card">
                <h1>🏋️ TNT Admin panel</h1>
                <form id="loginForm">
                    <div class="form-group">
                        <label>Логин (Telegram ID или username)</label>
                        <input type="text" class="form-control" id="loginIdentifier" required
                            autocomplete="username" inputmode="text">
                    </div>
                    <div class="form-group">
                        <label>Пароль</label>
                        <input type="password" class="form-control" id="secretCode" required
                            autocomplete="current-password">
                    </div>
                    <button type="submit" class="btn btn-primary">Войти</button>
                </form>
            </div>
        </div>
    `;
    
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const loginIdentifier = document.getElementById('loginIdentifier').value;
        const secretCode = document.getElementById('secretCode').value;
        
        const success = await login(loginIdentifier, secretCode);
        if (success) {
            location.reload();
        }
    });
}

function showMainPage() {
    // Загружаем главную страницу через fetch
    window.location.href = '/';
}

// Экспорт функций в глобальную область видимости
window.loadTodayWorkouts = loadTodayWorkouts;
window.loadWeekWorkouts = loadWeekWorkouts;
window.viewWorkout = viewWorkout;
window.editWorkout = editWorkout;
window.deleteWorkout = deleteWorkout;
window.createWorkout = createWorkout;
window.updateWorkout = updateWorkout;
window.bulkCreateSchedule = bulkCreateSchedule;
window.deleteWorkoutsByRange = deleteWorkoutsByRange;
window.clearAllWorkouts = clearAllWorkouts;
window.changeUserRole = changeUserRole;
window.setUserWebPassword = setUserWebPassword;
window.deleteUser = deleteUser;
window.openModal = openModal;
window.closeModal = closeModal;
window.switchTab = switchTab;
window.logout = logout;
window.updateUserInfo = updateUserInfo;
window.loadTrainers = loadTrainers;
window.openAddSlotForm = openAddSlotForm;
window.saveNewSlot = saveNewSlot;
window.editTemplateSlot = editTemplateSlot;
window.updateTemplateSlot = updateTemplateSlot;
window.deleteTemplateSlot = deleteTemplateSlot;
window.seedTemplateFromFile = seedTemplateFromFile;
window.seedTemplateFromFileForce = seedTemplateFromFileForce;
window.uploadScheduleImage = uploadScheduleImage;
window.deleteScheduleImage = deleteScheduleImage;
window.navigateWeek = navigateWeek;
window.loadGymSettings = loadGymSettings;
window.saveGymSettings = saveGymSettings;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Проверяем авторизацию
    if (!authToken) {
        showLoginPage();
        return;
    }
    
    // Восстанавливаем данные пользователя
    currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    if (!currentUser) {
        showLoginPage();
        return;
    }

    updateUserInfo();

    // Загружаем список тренеров для dropdown (только для admin)
    loadTrainers();

    // Скрываем элементы управления для тренеров (только admin видит полный интерфейс)
    if (currentUser.role !== 'admin') {
        // Кнопки "Создать тренировку" в шапках вкладок
        document.querySelectorAll('[onclick="openModal(\'createWorkoutModal\')"]').forEach(el => el.style.display = 'none');
        // Вкладка "Управление расписанием" (bulk create, delete)
        const scheduleTab = document.getElementById('scheduleTab');
        if (scheduleTab) scheduleTab.style.display = 'none';
        // Вкладка "Пользователи"
        const usersTab = document.getElementById('usersTab');
        if (usersTab) usersTab.style.display = 'none';
        // Вкладка "Шаблон расписания"
        const templateTab = document.getElementById('templateTab');
        if (templateTab) templateTab.style.display = 'none';
        // Вкладка "Картинка расписания"
        const scheduleImageTab = document.getElementById('scheduleImageTab');
        if (scheduleImageTab) scheduleImageTab.style.display = 'none';
        const gymSettingsTab = document.getElementById('gymSettingsTab');
        if (gymSettingsTab) gymSettingsTab.style.display = 'none';
    }

    // Обработчики форм
    const createForm = document.getElementById('createWorkoutForm');
    if (createForm) {
        createForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const rawTrainerId = formData.get('trainer_id');
            const workoutData = {
                name: formData.get('name'),
                description: formData.get('description'),
                datetime: formData.get('datetime'),
                duration: parseInt(formData.get('duration')),
                max_participants: parseInt(formData.get('max_participants')),
                trainer_id: rawTrainerId ? parseInt(rawTrainerId) : null
            };
            createWorkout(workoutData);
        });
    }
    
    const editForm = document.getElementById('editWorkoutForm');
    if (editForm) {
        editForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const workoutId = formData.get('workout_id');
            const rawTrainerId = formData.get('trainer_id');
            const workoutData = {
                name: formData.get('name'),
                description: formData.get('description'),
                datetime: formData.get('datetime'),
                duration: parseInt(formData.get('duration')),
                max_participants: parseInt(formData.get('max_participants')),
                trainer_id: rawTrainerId ? parseInt(rawTrainerId) : null
            };
            updateWorkout(workoutId, workoutData);
        });
    }
    
    // Загружаем первую вкладку
    switchTab('today');
});

