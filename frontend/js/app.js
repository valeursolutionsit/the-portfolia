const apiBase = (() => {
    const configuredBase = window.PORTFOLIA_API_BASE
        || document.querySelector('meta[name="portfolia-api-base"]')?.content.trim();
    if (configuredBase) return configuredBase.replace(/\/+$/, '');

    const hostname = window.location.hostname;
    const isLocalHost = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname) || hostname.endsWith('.localhost');
    const apiOrigin = isLocalHost ? `${window.location.protocol}//${hostname}:8000` : window.location.origin;
    return `${apiOrigin}/api/v1`;
})();

localStorage.removeItem('portfolia_access_token');

function showFormMessage(target, text, isError = false) {
    if (!target) return;
    target.textContent = text;
    target.style.color = isError ? '#b42318' : '#0f766e';
}

async function apiRequest(path, options = {}) {
    let response;
    try {
        response = await fetch(`${apiBase}${path}`, {
            ...options,
            credentials: 'include',
            headers: {
                ...(options.body ? { 'Content-Type': 'application/json' } : {}),
                ...(options.headers || {}),
            },
        });
    } catch {
        throw new Error('Unable to reach the API. Check that the backend is running and try again.');
    }

    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : null;
    if (!response.ok) {
        const error = new Error(data?.detail || data?.message || `Request failed (${response.status})`);
        error.status = response.status;
        throw error;
    }
    return data;
}

async function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const message = form.querySelector('[data-message]');
    const payload = {
        full_name: form.full_name.value.trim(),
        email: form.email.value.trim(),
        password: form.password.value,
        user_type: form.user_type ? form.user_type.value : 'student',
    };

    try {
        await apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
        showFormMessage(message, 'Registration successful. Redirecting…');
        window.location.href = 'students/dashboard.html';
    } catch (error) {
        showFormMessage(message, error.message, true);
    }
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.target;
    const message = form.querySelector('[data-message]');

    try {
        await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                email: form.email.value.trim(),
                password: form.password.value,
            }),
        });
        showFormMessage(message, 'Login successful. Redirecting…');
        const destination = new URLSearchParams(window.location.search).get('next') === 'admin'
            ? 'admin/'
            : 'students/dashboard.html';
        window.location.href = destination;
    } catch (error) {
        showFormMessage(message, error.message, true);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    if (registerForm) registerForm.addEventListener('submit', handleRegister);
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
});
