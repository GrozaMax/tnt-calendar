// CrossFit Hub Web Admin

// Конфигурация
const API_URL = '/api';
let authToken = localStorage.getItem('authToken');
let currentUser = null;

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
        'Stretching': '#0097A7',  // Голубой
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
async function login(telegramId, secretCode) {
    try {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                telegram_id: parseInt(telegramId),
                secret_code: secretCode
            })
        });
        
        authToken = data.access_token;
        currentUser = data.user;
        localStorage.setItem('authToken', authToken);
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
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
            <td>${workout.trainer_name}</td>
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
                    👤 Тренер: <strong>${workout.trainer_name}</strong>
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
                ${currentUser.role === 'admin' || (currentUser.role === 'trainer' && workout.trainer_id === currentUser.id) ? `
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
        const dt = new Date(workout.datetime);
        const dateStr = dt.toISOString().slice(0, 16);
        form.elements['datetime'].value = dateStr;
        
        form.elements['duration'].value = workout.duration;
        form.elements['max_participants'].value = workout.max_participants;
        
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
        
        tr.innerHTML = `
            <td>${user.id}</td>
            <td><strong>${user.full_name}</strong></td>
            <td>${user.username ? '@' + user.username : '-'}</td>
            <td>${roleEmoji} ${user.role}</td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="actions">
                    <button class="btn btn-sm btn-secondary" onclick="changeUserRole(${user.id}, '${user.role}')">Изменить роль</button>
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

async function changeUserRole(userId, currentRole) {
    const newRole = prompt(`Изменить роль пользователя.\nТекущая роль: ${currentRole}\n\nВведите новую роль (athlete/trainer/admin):`, currentRole);
    
    if (!newRole || newRole === currentRole) {
        return;
    }
    
    if (!['athlete', 'trainer', 'admin'].includes(newRole)) {
        showError('Неверная роль');
        return;
    }
    
    try {
        await apiRequest(`/users/${userId}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role: newRole })
        });
        
        showSuccess('Роль пользователя изменена!');
        loadUsers();
    } catch (error) {
        showError('Не удалось изменить роль: ' + error.message);
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
    }
}

// Загрузка тренировок на сегодня
async function loadTodayWorkouts() {
    const container = document.getElementById('todayWorkouts');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    const today = new Date().toISOString().split('T')[0];
    
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
                <div class="workout-card-trainer">👤 ${workout.trainer_name}</div>
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

// Загрузка тренировок на неделю
async function loadWeekWorkouts() {
    const container = document.getElementById('weekWorkouts');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    // Вычисляем понедельник текущей недели
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 = воскресенье, 1 = понедельник, ..., 6 = суббота
    const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // Если воскресенье, то 6 дней назад
    
    const monday = new Date(today);
    monday.setDate(today.getDate() - daysFromMonday);
    
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    
    const dateFrom = monday.toISOString().split('T')[0];
    const dateTo = sunday.toISOString().split('T')[0];
    
    console.log('📅 Загрузка недели:');
    console.log('  Сегодня:', today.toISOString().split('T')[0], '(день недели:', today.getDay(), ')');
    console.log('  Понедельник:', dateFrom);
    console.log('  Воскресенье:', dateTo);
    
    try {
        const workouts = await apiRequest(`/workouts/?date_from=${dateFrom}&date_to=${dateTo}`);
        console.log('📊 Получено тренировок:', workouts.length);
        displayWeekWorkouts(workouts);
    } catch (error) {
        container.innerHTML = `<div class="alert alert-error">Ошибка загрузки: ${error.message}</div>`;
        console.error('Load week workouts error:', error);
    }
}

function displayWeekWorkouts(workouts) {
    const container = document.getElementById('weekWorkouts');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Вычисляем понедельник текущей недели
    const dayOfWeek = today.getDay(); // 0 = воскресенье, 1 = понедельник, ..., 6 = суббота
    const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    
    const monday = new Date(today);
    monday.setDate(today.getDate() - daysFromMonday);
    monday.setHours(0, 0, 0, 0);
    
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
    const mondayDateStr = monday.toISOString().split('T')[0];
    for (let i = 0; i < 7; i++) {
        // Используем строковое создание даты для избежания проблем с часовыми поясами
        const [year, month, day] = mondayDateStr.split('-').map(Number);
        const date = new Date(year, month - 1, day + i);
        days.push(date);
    }
    
    console.log('📆 Отображаемые дни:');
    days.forEach((d, i) => {
        console.log(`  ${i}: ${d.toISOString().split('T')[0]} (${['Вс','Пн','Вт','Ср','Чт','Пт','Сб'][d.getDay()]})`);
    });
    
    const weekdays = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    
    container.innerHTML = days.map(date => {
        const dateStr = date.toISOString().split('T')[0];
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
                        <label>Telegram ID</label>
                        <input type="number" class="form-control" id="telegramId" required>
                    </div>
                    <div class="form-group">
                        <label>Секретный код</label>
                        <input type="password" class="form-control" id="secretCode" required value="secret123">
                    </div>
                    <button type="submit" class="btn btn-primary">Войти</button>
                </form>
            </div>
        </div>
    `;
    
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const telegramId = document.getElementById('telegramId').value;
        const secretCode = document.getElementById('secretCode').value;
        
        const success = await login(telegramId, secretCode);
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
window.clearAllWorkouts = clearAllWorkouts;
window.changeUserRole = changeUserRole;
window.openModal = openModal;
window.closeModal = closeModal;
window.switchTab = switchTab;
window.logout = logout;

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
    
    // Обработчики форм
    const createForm = document.getElementById('createWorkoutForm');
    if (createForm) {
        createForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const workoutData = {
                name: formData.get('name'),
                description: formData.get('description'),
                datetime: formData.get('datetime'),
                duration: parseInt(formData.get('duration')),
                max_participants: parseInt(formData.get('max_participants'))
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
            const workoutData = {
                name: formData.get('name'),
                description: formData.get('description'),
                datetime: formData.get('datetime'),
                duration: parseInt(formData.get('duration')),
                max_participants: parseInt(formData.get('max_participants'))
            };
            updateWorkout(workoutId, workoutData);
        });
    }
    
    // Загружаем первую вкладку
    switchTab('today');
});

