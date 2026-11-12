const adminApiBase = (() => {
    const configuredBase = window.PORTFOLIA_API_BASE
        || document.querySelector('meta[name="portfolia-api-base"]')?.content.trim();
    if (configuredBase) return configuredBase.replace(/\/+$/, '');

    const hostname = window.location.hostname;
    const local = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname) || hostname.endsWith('.localhost');
    const apiOrigin = local ? `${window.location.protocol}//${hostname}:8000` : window.location.origin;
    return `${apiOrigin}/api/v1`;
})();

const studentRecordConfigs = {
    skills: {
        label: 'Skills',
        fields: [
            { name: 'name', label: 'Skill name', required: true },
            { name: 'category', label: 'Category', value: 'technical' },
            { name: 'proficiency', label: 'Proficiency' },
            { name: 'evidence_url', label: 'Evidence URL', type: 'url' },
        ],
        columns: ['name', 'category', 'proficiency', 'evidence_url'],
    },
    'learning-activities': {
        label: 'Learning activities',
        fields: [
            { name: 'title', label: 'Title', required: true },
            { name: 'category', label: 'Category', value: 'general' },
            { name: 'topic', label: 'Topic' },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'what_i_practised', label: 'What they practised', type: 'textarea' },
            { name: 'resource_url', label: 'Resource URL', type: 'url' },
            { name: 'evidence_url', label: 'Evidence URL', type: 'url' },
            { name: 'confidence', label: 'Confidence (1–5)', type: 'number', min: 1, max: 5 },
            { name: 'status', label: 'Status', type: 'select', options: ['planned', 'in_progress', 'completed'], value: 'completed' },
            { name: 'duration_hours', label: 'Duration (hours)', type: 'number', min: 0, value: 0 },
            { name: 'completed_at', label: 'Completed at', type: 'datetime-local' },
        ],
        columns: ['title', 'topic', 'status', 'duration_hours'],
    },
    'learning-paths': {
        label: 'Learning paths',
        fields: [
            { name: 'title', label: 'Title', required: true },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'skill_name', label: 'Skill' },
            { name: 'status', label: 'Status', type: 'select', options: ['active', 'paused', 'completed'], value: 'active' },
            { name: 'target_date', label: 'Target date', type: 'date' },
        ],
        columns: ['title', 'skill_name', 'status', 'target_date'],
    },
    milestones: {
        label: 'Learning milestones',
        fields: [
            { name: 'title', label: 'Title', required: true },
            { name: 'skill_name', label: 'Skill' },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'target_date', label: 'Target date', type: 'date' },
            { name: 'status', label: 'Status', type: 'select', options: ['planned', 'in_progress', 'completed'], value: 'planned' },
        ],
        columns: ['title', 'skill_name', 'status', 'target_date'],
    },
    resources: {
        label: 'Learning resources',
        fields: [
            { name: 'title', label: 'Title', required: true },
            { name: 'url', label: 'Resource URL', type: 'url', required: true },
            { name: 'category', label: 'Category', value: 'general' },
            { name: 'description', label: 'Description', type: 'textarea' },
        ],
        columns: ['title', 'category', 'url'],
    },
    projects: {
        label: 'Portfolio projects',
        fields: [
            { name: 'title', label: 'Title', required: true },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'problem_statement', label: 'Problem statement', type: 'textarea' },
            { name: 'objective', label: 'Objective', type: 'textarea' },
            { name: 'technologies', label: 'Technologies (comma separated)', type: 'array' },
            { name: 'student_role', label: 'Student role' },
            { name: 'team_members', label: 'Team members (comma separated)', type: 'array' },
            { name: 'duration', label: 'Duration' },
            { name: 'status', label: 'Status', type: 'select', options: ['planned', 'in_progress', 'completed'], value: 'in_progress' },
            { name: 'github_url', label: 'GitHub URL', type: 'url' },
            { name: 'live_url', label: 'Live URL', type: 'url' },
            { name: 'evidence_urls', label: 'Evidence URLs (comma separated)', type: 'array' },
            { name: 'key_learnings', label: 'Key learnings', type: 'textarea' },
            { name: 'is_public', label: 'Public portfolio item', type: 'checkbox' },
        ],
        columns: ['title', 'status', 'student_role', 'is_public'],
    },
    certifications: {
        label: 'Certifications',
        fields: [
            { name: 'name', label: 'Certification', required: true },
            { name: 'issuer', label: 'Issuer' },
            { name: 'credential_url', label: 'Credential URL', type: 'url' },
            { name: 'issued_at', label: 'Issued at', type: 'date' },
        ],
        columns: ['name', 'issuer', 'issued_at', 'credential_url'],
    },
    achievements: {
        label: 'Achievements',
        fields: [
            { name: 'title', label: 'Title', required: true },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'awarded_by', label: 'Awarded by' },
            { name: 'achieved_at', label: 'Achieved at', type: 'date' },
        ],
        columns: ['title', 'awarded_by', 'achieved_at'],
    },
    'work-experiences': {
        label: 'Work experience',
        fields: [
            { name: 'organization', label: 'Organization', required: true },
            { name: 'role', label: 'Role', required: true },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'start_date', label: 'Start date', type: 'date' },
            { name: 'end_date', label: 'End date', type: 'date' },
        ],
        columns: ['organization', 'role', 'start_date', 'end_date'],
    },
    teams: {
        label: 'Teams',
        fields: [
            { name: 'name', label: 'Team name', required: true },
            { name: 'project_name', label: 'Project name', required: true },
            { name: 'description', label: 'Description', type: 'textarea' },
            { name: 'category', label: 'Category' },
            { name: 'required_skills', label: 'Required skills (comma separated)', type: 'array' },
            { name: 'team_size', label: 'Team size', type: 'number', min: 2, max: 100, value: 4 },
            { name: 'open_positions', label: 'Open positions', type: 'number', min: 0, max: 99, value: 1 },
            { name: 'duration', label: 'Duration' },
            { name: 'objectives', label: 'Objectives', type: 'textarea' },
        ],
        columns: ['name', 'project_name', 'status', 'open_positions'],
    },
};

const readOnlyStudentRecords = {
    assessment_attempts: { label: 'Assessment attempts', columns: ['assessment_title', 'score', 'max_score', 'started_at', 'completed_at'], activity: 'assessment-attempts', actions: ['delete'] },
    opportunity_applications: { label: 'Opportunity applications', columns: ['opportunity_title', 'status', 'created_at'], activity: 'applications', actions: ['status', 'delete'], statuses: ['submitted', 'reviewing', 'interview', 'accepted', 'rejected'], create: true, fields: [{ name: 'opportunity_id', label: 'Opportunity ID', required: true }] },
    saved_opportunities: { label: 'Saved opportunities', columns: ['opportunity_title', 'created_at'], activity: 'saved-opportunities', actions: ['delete'], create: true, fields: [{ name: 'opportunity_id', label: 'Opportunity ID', required: true }] },
    support_tickets: { label: 'Support tickets', columns: ['subject', 'category', 'status', 'message_count', 'updated_at'], activity: 'support-tickets', actions: ['status', 'support'], statuses: ['open', 'in_progress', 'closed'] },
    notifications: { label: 'Notifications', columns: ['title', 'message', 'is_read', 'created_at'], activity: 'notifications', actions: ['edit', 'delete'], create: true, fields: [{ name: 'title', label: 'Title', required: true }, { name: 'message', label: 'Message', type: 'textarea', required: true }, { name: 'is_read', label: 'Read', type: 'checkbox' }] },
    sessions: { label: 'Login sessions', columns: ['created_at', 'expires_at', 'revoked_at', 'user_agent'], activity: 'sessions', actions: ['delete'] },
    team_memberships: { label: 'Team memberships', columns: ['team_name', 'role', 'joined_at'], activity: 'team-memberships', actions: ['edit', 'delete'], create: true, fields: [{ name: 'team_id', label: 'Team', type: 'team-select', required: true }, { name: 'role', label: 'Role', required: true }] },
    team_invitations: { label: 'Team invitations', columns: ['team_name', 'invitee_email', 'status', 'created_at'], activity: 'team-invitations', actions: ['status', 'delete'], statuses: ['pending', 'accepted', 'declined', 'cancelled'], create: true, fields: [{ name: 'team_id', label: 'Team', type: 'team-select', required: true }, { name: 'invitee_id', label: 'Invitee student ID', required: true }] },
    project_tasks: { label: 'Project tasks', columns: ['title', 'team_name', 'status', 'assignee_email', 'due_date'], activity: 'project-tasks', actions: ['edit', 'delete'], create: true, fields: [{ name: 'team_id', label: 'Team', type: 'team-select', required: true }, { name: 'title', label: 'Title', required: true }, { name: 'description', label: 'Description', type: 'textarea' }, { name: 'assignee_id', label: 'Assignee student ID' }, { name: 'status', label: 'Status', type: 'select', options: ['todo', 'in_progress', 'done'], value: 'todo' }, { name: 'due_date', label: 'Due date', type: 'date' }] },
    project_contributions: { label: 'Project contributions', columns: ['description', 'team_name', 'evidence_url', 'created_at'], activity: 'project-contributions', actions: ['edit', 'delete'], create: true, fields: [{ name: 'team_id', label: 'Team', type: 'team-select', required: true }, { name: 'description', label: 'Description', type: 'textarea', required: true }, { name: 'evidence_url', label: 'Evidence URL', type: 'url' }] },
    support_messages: { label: 'Support messages', columns: ['ticket_id', 'sender_id', 'message', 'created_at'] },
    team_records: { label: 'Team participation details', columns: ['name', 'project_name', 'status', 'owner_id'] },
    settings: { label: 'Account settings', columns: ['email_preferences', 'notification_settings', 'privacy_settings', 'profile_visibility', 'deactivation_requested'], activity: 'settings', actions: ['edit', 'delete'], fields: [{ name: 'email_preferences', label: 'Email preferences (JSON)', type: 'json' }, { name: 'notification_settings', label: 'Notification settings (JSON)', type: 'json' }, { name: 'privacy_settings', label: 'Privacy settings (JSON)', type: 'json' }, { name: 'profile_visibility', label: 'Profile visibility', type: 'select', options: ['private', 'public'] }, { name: 'deactivation_requested', label: 'Deactivation requested', type: 'checkbox' }] },
};

const assessmentQuestionCount = 30;

function renderAssessmentQuestionEditor(questions = [], locked = false) {
    const root = document.getElementById('admin-assessment-questions');
    root.innerHTML = Array.from({ length: assessmentQuestionCount }, (_, index) => {
        const question = questions[index] || {};
        const options = question.options || ['', '', '', ''];
        const optionInputs = options.map((option, optionIndex) => `
            <label>Option ${optionIndex + 1}
                <input data-assessment-option="${optionIndex}" value="${escapeHtml(option)}" required maxlength="1000" ${locked ? 'disabled' : ''} />
            </label>
        `).join('');
        return `
            <fieldset class="admin-assessment-question">
                <legend>Question ${index + 1}</legend>
                <label>Question text<textarea data-assessment-prompt required minlength="5" maxlength="5000" ${locked ? 'disabled' : ''}>${escapeHtml(question.prompt || '')}</textarea></label>
                <label>Topic<input data-assessment-topic value="${escapeHtml(question.topic || '')}" required minlength="2" maxlength="120" ${locked ? 'disabled' : ''} /></label>
                <div class="assessment-option-grid">${optionInputs}</div>
                <label>Correct option
                    <select data-assessment-correct ${locked ? 'disabled' : ''}>
                        ${[0, 1, 2, 3].map((optionIndex) => `<option value="${optionIndex}" ${Number(question.correct_option_index || 0) === optionIndex ? 'selected' : ''}>Option ${optionIndex + 1}</option>`).join('')}
                    </select>
                </label>
            </fieldset>
        `;
    }).join('');
}

function resetAssessmentForm() {
    const form = document.getElementById('admin-assessment-form');
    form.reset();
    form.elements.id.value = '';
    form.elements.duration_minutes.value = '30';
    form.elements.is_active.checked = true;
    document.getElementById('admin-assessment-submit').textContent = 'Create test';
    document.getElementById('admin-assessment-cancel').hidden = true;
    form.dataset.questionsLocked = 'false';
    form.querySelector('[data-message]').textContent = '';
    renderAssessmentQuestionEditor();
}

async function loadAdminAssessments() {
    const root = document.getElementById('admin-assessments');
    try {
        const assessments = await adminRequest('/admin/assessments');
        root.innerHTML = assessments.length
            ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Test</th><th>Questions</th><th>Duration</th><th>Attempts</th><th>Status</th><th>Actions</th></tr></thead><tbody>${assessments.map((item) => `
                <tr>
                    <td><strong>${escapeHtml(item.title)}</strong><br /><span>${escapeHtml(item.category)}</span></td>
                    <td>${item.question_count}/30</td><td>${item.duration_minutes} min</td><td>${item.attempt_count}</td>
                    <td>${item.is_active ? 'Available' : 'Inactive'}</td>
                    <td>
                        <button class="small-button" data-assessment-edit="${escapeHtml(item.id)}">Edit</button>
                        <button class="small-button" data-assessment-active="${escapeHtml(item.id)}" data-next="${!item.is_active}">${item.is_active ? 'Deactivate' : 'Activate'}</button>
                        <button class="small-button danger-button" data-assessment-delete="${escapeHtml(item.id)}" ${item.attempt_count ? 'disabled title="Tests with attempts cannot be deleted"' : ''}>Delete</button>
                    </td>
                </tr>`).join('')}</tbody></table></div>`
            : '<p class="empty-state">No skill tests have been created yet.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

async function editAdminAssessment(assessmentId) {
    const form = document.getElementById('admin-assessment-form');
    try {
        const assessments = await adminRequest('/admin/assessments');
        const assessment = assessments.find((item) => item.id === assessmentId);
        if (!assessment) throw new Error('Test not found.');
        form.elements.id.value = assessment.id;
        form.elements.title.value = assessment.title;
        form.elements.category.value = assessment.category;
        form.elements.description.value = assessment.description || '';
        form.elements.duration_minutes.value = assessment.duration_minutes;
        form.elements.is_active.checked = assessment.is_active;
        const locked = assessment.attempt_count > 0 || assessment.question_count !== assessmentQuestionCount;
        renderAssessmentQuestionEditor(assessment.questions, locked);
        form.querySelector('[data-message]').textContent = assessment.attempt_count > 0
            ? 'Students have started this test. Its questions are locked; you can update its details or deactivate it.'
            : locked
                ? 'This legacy test does not have 30 questions. You can update its details or deactivate it; create a new test to publish a 30-question MCQ.'
                : '';
        document.getElementById('admin-assessment-submit').textContent = 'Save test';
        document.getElementById('admin-assessment-cancel').hidden = false;
        form.dataset.questionsLocked = String(locked);
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        alertAdmin(error.message, true);
    }
}

async function submitAdminAssessment(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const id = form.elements.id.value;
    const payload = {
        title: form.elements.title.value.trim(),
        category: form.elements.category.value.trim(),
        description: form.elements.description.value.trim() || null,
        duration_minutes: Number(form.elements.duration_minutes.value),
        is_active: form.elements.is_active.checked,
    };
    if (!id || form.dataset.questionsLocked !== 'true') {
        const questionCards = [...form.querySelectorAll('.admin-assessment-question')];
        payload.questions = questionCards.map((card) => ({
            prompt: card.querySelector('[data-assessment-prompt]').value.trim(),
            topic: card.querySelector('[data-assessment-topic]').value.trim(),
            options: [...card.querySelectorAll('[data-assessment-option]')].map((input) => input.value.trim()),
            correct_option_index: Number(card.querySelector('[data-assessment-correct]').value),
        }));
    }
    try {
        await adminRequest(id ? `/admin/assessments/${id}` : '/admin/assessments', {
            method: id ? 'PATCH' : 'POST',
            body: JSON.stringify(payload),
        });
        alertAdmin(id ? 'Skill test updated.' : '30-question skill test created.');
        resetAssessmentForm();
        await Promise.all([loadAdminAssessments(), loadAdminActivity()]);
    } catch (error) {
        form.querySelector('[data-message]').textContent = error.message;
        form.querySelector('[data-message]').className = 'form-note is-error';
    }
}

const studentProfileFields = [
    { name: 'phone', label: 'Phone' },
    { name: 'date_of_birth', label: 'Date of birth', type: 'date' },
    { name: 'gender', label: 'Gender' },
    { name: 'address', label: 'Address', type: 'textarea' },
    { name: 'college_name', label: 'College' },
    { name: 'university', label: 'University' },
    { name: 'degree', label: 'Degree' },
    { name: 'course', label: 'Course' },
    { name: 'department', label: 'Department' },
    { name: 'current_year', label: 'Current year' },
    { name: 'graduation_year', label: 'Graduation year', type: 'number' },
    { name: 'career_interests', label: 'Career interests', type: 'textarea' },
    { name: 'career_objective', label: 'Career objective', type: 'textarea' },
    { name: 'interested_industries', label: 'Interested industries', type: 'textarea' },
    { name: 'preferred_job_roles', label: 'Preferred job roles', type: 'textarea' },
    { name: 'career_goals', label: 'Career goals', type: 'textarea' },
    { name: 'technical_skills', label: 'Technical skills', type: 'textarea' },
    { name: 'non_technical_skills', label: 'Non-technical skills', type: 'textarea' },
    { name: 'languages', label: 'Languages', type: 'textarea' },
    { name: 'linkedin_url', label: 'LinkedIn URL', type: 'url' },
    { name: 'github_url', label: 'GitHub URL', type: 'url' },
    { name: 'personal_website', label: 'Personal website', type: 'url' },
    { name: 'profile_photo_url', label: 'Profile photo URL', type: 'url' },
    { name: 'profile_visibility', label: 'Profile visibility', type: 'select', options: ['private', 'public'], value: 'private' },
    { name: 'bio', label: 'Bio', type: 'textarea' },
];

let activeAdminStudent = null;
let activeAdminRecord = null;
let studentSearchQuery = '';
let studentOffset = 0;
const studentPageSize = 25;

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (character) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    })[character]);
}

function setAdminMessage(target, message, isError = false) {
    if (!target) return;
    target.textContent = message;
    target.classList.toggle('is-error', isError);
    target.classList.toggle('is-success', !isError);
}

async function adminRequest(path, options = {}) {
    let response;
    try {
        response = await fetch(`${adminApiBase}${path}`, {
            ...options,
            credentials: 'include',
            headers: {
                ...(options.body ? { 'Content-Type': 'application/json' } : {}),
                ...(options.headers || {}),
            },
        });
    } catch {
        throw new Error('Unable to reach the API. Check that the backend is running.');
    }
    if (response.status === 204) return null;
    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : null;
    if (!response.ok) {
        const detail = data?.detail;
        const message = Array.isArray(detail)
            ? detail.map((issue) => `${(issue.loc || []).filter((part) => part !== 'body').join('.')}: ${issue.msg}`).join('; ')
            : typeof detail === 'string'
                ? detail
                : detail
                    ? JSON.stringify(detail)
                    : `Request failed (${response.status})`;
        const error = new Error(message);
        error.status = response.status;
        throw error;
    }
    return data;
}

function alertAdmin(message, isError = false) {
    const root = document.getElementById('admin-alert');
    root.textContent = message;
    root.className = message ? (isError ? 'admin-alert is-error' : 'admin-alert is-success') : '';
}

async function checkAdminAccess() {
    try {
        const profile = await adminRequest('/auth/me');
        await adminRequest('/admin/dashboard');
        document.getElementById('admin-gate').hidden = true;
        document.getElementById('admin-console').hidden = false;
        document.getElementById('admin-name').textContent = profile.full_name;
        await loadAdminDashboard();
    } catch (error) {
        if (error.status !== 401 && error.status !== 403) {
            const note = document.querySelector('#admin-register-form [data-message]');
            setAdminMessage(note, error.message, true);
        }
    }
}

async function registerAdmin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
        await adminRequest('/auth/register-admin', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        await checkAdminAccess();
    } catch (error) {
        setAdminMessage(form.querySelector('[data-message]'), error.message, true);
    }
}

async function loadAdminDashboard() {
    const root = document.getElementById('admin-metrics');
    try {
        const data = await adminRequest('/admin/dashboard');
        root.innerHTML = `
            <article class="board-panel"><span class="metric-label">Total users</span><strong class="metric-value">${data.users_total}</strong><span>${data.users_active} active</span></article>
            <article class="board-panel"><span class="metric-label">Students</span><strong class="metric-value">${data.students_total}</strong><span>Registered accounts</span></article>
            <article class="board-panel"><span class="metric-label">Organizations</span><strong class="metric-value">${data.companies_total + data.institutions_total + data.investors_total}</strong><span>${data.pending_verification} pending verification</span></article>
            <article class="board-panel"><span class="metric-label">Opportunities</span><strong class="metric-value">${data.opportunities_active}</strong><span>${data.applications_total} tracked applications</span></article>
            <article class="board-panel"><span class="metric-label">Support queue</span><strong class="metric-value">${data.support_open}</strong><span>Open or in progress</span></article>
            <article class="board-panel"><span class="metric-label">Student work</span><strong class="metric-value">${data.projects_total}</strong><span>${data.teams_total} teams · ${data.learning_records_total} learning records</span></article>
            <article class="board-panel"><span class="metric-label">Assessment attempts</span><strong class="metric-value">${data.assessment_attempts_total}</strong><span>Saved attempts</span></article>
        `;
        const usersRoot = document.getElementById('admin-recent-users');
        usersRoot.innerHTML = data.recent_users.length
            ? `<ul class="data-list">${data.recent_users.map((user) => `<li><div><strong>${escapeHtml(user.full_name)}</strong><span>${escapeHtml(user.email)} · ${escapeHtml(user.user_type)} · ${escapeHtml(new Date(user.created_at).toLocaleDateString())}</span></div></li>`).join('')}</ul>`
            : '<p class="empty-state">No accounts have been registered.</p>';
        const activityRoot = document.getElementById('admin-recent-activity');
        activityRoot.innerHTML = data.recent_activity.length
            ? `<ul class="data-list">${data.recent_activity.map((item) => `<li><div><strong>${escapeHtml(item.action)}</strong><span>${escapeHtml(item.actor)} · ${escapeHtml(new Date(item.created_at).toLocaleString())}</span></div></li>`).join('')}</ul>`
            : '<p class="empty-state">Admin actions will appear here when recorded.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

function queryFromForm(form) {
    const values = Object.fromEntries(new FormData(form).entries());
    const params = new URLSearchParams();
    Object.entries(values).forEach(([key, value]) => {
        if (value) params.set(key, value);
    });
    return params.size ? `?${params}` : '';
}

async function loadAdminUsers(query = '') {
    const root = document.getElementById('admin-users');
    try {
        const data = await adminRequest(`/admin/users${query}`);
        root.innerHTML = data.items.length
            ? `<p>${data.total} account(s)</p><div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>User</th><th>Type</th><th>Port ID</th><th>Account</th><th>Verification</th><th>Actions</th></tr></thead><tbody>${data.items.map((user) => `<tr><td><strong>${escapeHtml(user.full_name)}</strong><br /><span>${escapeHtml(user.email)}</span>${user.college_name ? `<br /><span>${escapeHtml(user.college_name)}</span>` : ''}</td><td>${escapeHtml(user.user_type)}</td><td>${escapeHtml(user.port_id || '—')}</td><td>${user.is_active ? 'Active' : 'Inactive'}</td><td>${user.is_verified ? 'Verified' : 'Unverified'}</td><td><button class="small-button" data-user-verify="${escapeHtml(user.id)}" data-next="${!user.is_verified}">${user.is_verified ? 'Unverify' : 'Verify'}</button><button class="small-button danger-button" data-user-active="${escapeHtml(user.id)}" data-next="${!user.is_active}">${user.is_active ? 'Deactivate' : 'Activate'}</button></td></tr>`).join('')}</tbody></table></div>`
            : '<p class="empty-state">No users match these filters.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

async function loadAdminOrganizations() {
    const root = document.getElementById('admin-organizations');
    try {
        const organizations = await adminRequest('/admin/organizations');
        root.innerHTML = organizations.length
            ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Organization</th><th>Type</th><th>Contact</th><th>Status</th><th></th></tr></thead><tbody>${organizations.map((org) => `<tr><td>${escapeHtml(org.name)}</td><td>${escapeHtml(org.user_type)}</td><td>${escapeHtml(org.email)}</td><td>${org.is_verified ? 'Verified' : 'Pending verification'} · ${org.is_active ? 'Active' : 'Inactive'}</td><td><button class="small-button" data-user-verify="${escapeHtml(org.user_id)}" data-next="${!org.is_verified}">${org.is_verified ? 'Revoke verification' : 'Verify organization'}</button></td></tr>`).join('')}</tbody></table></div>`
            : '<p class="empty-state">No organization profiles are available yet.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

async function loadAdminOpportunities(query = '') {
    const root = document.getElementById('admin-opportunities');
    try {
        const items = await adminRequest(`/admin/opportunities${query}`);
        root.innerHTML = items.length
            ? items.map((item) => `<article class="mini-card"><div class="panel-heading"><h2>${escapeHtml(item.title)}</h2><span class="status-chip ${item.is_active ? 'status-active' : 'status-inactive'}">${item.is_active ? 'Published' : 'Hidden'}</span></div><p>${escapeHtml(item.organization)} · ${escapeHtml(item.category)} · Published by ${escapeHtml(item.publisher_email || 'Unknown')}</p><p>${escapeHtml(item.description)}</p><p>Deadline: ${escapeHtml(item.deadline || 'Not specified')} · Required skills: ${escapeHtml((item.required_skills || []).join(', ') || 'Not specified')}</p><p><small>Opportunity ID: <code>${escapeHtml(item.id)}</code></small></p><button class="small-button ${item.is_active ? 'danger-button' : ''}" data-opportunity-id="${escapeHtml(item.id)}" data-next="${!item.is_active}">${item.is_active ? 'Unpublish' : 'Publish'}</button></article>`).join('')
            : '<p class="empty-state">No published opportunities found.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

async function loadAdminTickets(query = '') {
    const root = document.getElementById('admin-tickets');
    try {
        const tickets = await adminRequest(`/admin/support/tickets${query}`);
        root.innerHTML = tickets.length
            ? `<ul class="data-list">${tickets.map((ticket) => `<li><div><strong>${escapeHtml(ticket.subject)}</strong><span>${escapeHtml(ticket.user_email)} · ${escapeHtml(ticket.category)} · ${escapeHtml(ticket.status)} · ${ticket.message_count} message(s)</span></div><button class="small-button" data-admin-ticket="${escapeHtml(ticket.id)}">Review</button></li>`).join('')}</ul>`
            : '<p class="empty-state">No tickets match these filters.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

async function loadAdminTicket(ticketId) {
    const root = document.getElementById('admin-ticket-detail');
    try {
        const data = await adminRequest(`/admin/support/tickets/${ticketId}`);
        root.dataset.ticketId = ticketId;
        root.innerHTML = `<h2>${escapeHtml(data.ticket.subject)}</h2><p>${escapeHtml(data.ticket.user_email)} · ${escapeHtml(data.ticket.category)} · ${escapeHtml(data.ticket.status)}</p><div class="admin-ticket-messages">${data.messages.map((message) => `<article class="ticket-message"><strong>${escapeHtml(message.sender_name || 'User')}</strong><span>${escapeHtml(new Date(message.created_at).toLocaleString())}</span><p>${escapeHtml(message.message)}</p></article>`).join('')}</div>${data.ticket.status !== 'closed' ? `<form id="admin-ticket-reply" class="compact-form"><label>Reply<textarea name="message" rows="4" required maxlength="10000"></textarea></label><button>Send response</button></form>` : '<p class="empty-state">This ticket is closed.</p>'}<form id="admin-ticket-status" class="inline-form"><label>Ticket status<select name="status"><option ${data.ticket.status === 'open' ? 'selected' : ''}>open</option><option ${data.ticket.status === 'in_progress' ? 'selected' : ''}>in_progress</option><option ${data.ticket.status === 'closed' ? 'selected' : ''}>closed</option></select></label><button>Update status</button></form>`;
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

async function loadAdminActivity() {
    const root = document.getElementById('admin-activity');
    try {
        const data = await adminRequest('/admin/activity?limit=100');
        root.innerHTML = data.items.length
            ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Details</th></tr></thead><tbody>${data.items.map((item) => `<tr><td>${escapeHtml(new Date(item.created_at).toLocaleString())}</td><td>${escapeHtml(item.actor)}</td><td>${escapeHtml(item.action)}</td><td><code>${escapeHtml(item.details || '')}</code></td></tr>`).join('')}</tbody></table></div>`
            : '<p class="empty-state">No admin audit events recorded yet.</p>';
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

function readableFieldName(field) {
    return field.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function displayStudentValue(value) {
    if (value === null || value === undefined || value === '') return '—';
    if (Array.isArray(value)) return value.join(', ') || '—';
    if (typeof value === 'object') return JSON.stringify(value);
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    return String(value);
}

function studentFormField(field, value = undefined, requiredOverride = undefined) {
    const type = field.type || 'text';
    let fieldValue = value ?? field.value ?? '';
    if (type === 'json' && fieldValue && typeof fieldValue === 'object') fieldValue = JSON.stringify(fieldValue, null, 2);
    const required = requiredOverride ?? field.required ?? false;
    const attrs = [
        `name="${escapeHtml(field.name)}"`,
        !['textarea', 'json', 'select', 'team-select', 'checkbox'].includes(type) ? `type="${type === 'array' ? 'text' : type}"` : '',
        field.required || requiredOverride ? 'required' : '',
        field.min !== undefined ? `min="${field.min}"` : '',
        field.max !== undefined ? `max="${field.max}"` : '',
        field.minlength !== undefined ? `minlength="${field.minlength}"` : '',
        field.maxlength !== undefined ? `maxlength="${field.maxlength}"` : '',
        'autocomplete="off"',
    ].filter(Boolean).join(' ');
    let control;
    if (type === 'textarea' || type === 'json') {
        control = `<textarea ${attrs} rows="3">${escapeHtml(fieldValue)}</textarea>`;
    } else if (type === 'select' || type === 'team-select') {
        const options = type === 'team-select'
            ? (activeAdminStudent?.records.team_records || []).map((team) => ({ value: team.id, label: `${team.name} · ${team.project_name}` }))
            : (field.options || []).map((option) => ({ value: option, label: readableFieldName(option) }));
        control = `<select ${attrs}><option value="">Select…</option>${options.map((option) => `<option value="${escapeHtml(option.value)}" ${String(fieldValue) === String(option.value) ? 'selected' : ''}>${escapeHtml(option.label)}</option>`).join('')}</select>`;
    } else if (type === 'checkbox') {
        control = `<input ${attrs} type="checkbox" ${fieldValue ? 'checked' : ''} />`;
    } else {
        let inputValue = fieldValue;
        if (type === 'array' && Array.isArray(fieldValue)) inputValue = fieldValue.join(', ');
        if (type === 'datetime-local' && fieldValue) inputValue = new Date(fieldValue).toISOString().slice(0, 16);
        control = `<input ${attrs} value="${escapeHtml(inputValue)}" />`;
    }
    return `<label class="${type === 'checkbox' ? 'admin-checkbox-field' : ''}">${escapeHtml(field.label)}${control}</label>`;
}

function collectStudentForm(form, fields) {
    const values = new FormData(form);
    const payload = {};
    for (const field of fields) {
        const element = form.elements.namedItem(field.name);
        if (field.type === 'checkbox') {
            payload[field.name] = Boolean(element.checked);
            continue;
        }
        const raw = values.get(field.name);
        if (field.type === 'array') {
            payload[field.name] = String(raw || '').split(',').map((item) => item.trim()).filter(Boolean);
        } else if (field.type === 'json') {
            if (raw === '') {
                payload[field.name] = {};
            } else {
                const parsed = JSON.parse(String(raw));
                if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
                    throw new Error(`${field.label} must be a JSON object.`);
                }
                payload[field.name] = parsed;
            }
        } else if (field.type === 'number') {
            payload[field.name] = raw === '' ? null : Number(raw);
        } else if (field.type === 'datetime-local') {
            payload[field.name] = raw ? new Date(raw).toISOString() : null;
        } else {
            payload[field.name] = raw === '' ? null : raw;
        }
    }
    return payload;
}

async function loadAdminStudents(query = studentSearchQuery, offset = 0) {
    studentSearchQuery = query;
    studentOffset = offset;
    const root = document.getElementById('admin-students');
    root.innerHTML = '<p>Loading students…</p>';
    try {
        const params = new URLSearchParams(query.replace(/^\?/, ''));
        params.set('offset', String(offset));
        params.set('limit', String(studentPageSize));
        const data = await adminRequest(`/admin/students?${params}`);
        const first = data.total ? offset + 1 : 0;
        const last = Math.min(offset + data.items.length, data.total);
        root.innerHTML = `<p>${data.total} student account(s)</p>${data.items.length
            ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr><th>Student</th><th>Port ID</th><th>College</th><th>Status</th><th></th></tr></thead><tbody>${data.items.map((student) => `<tr><td><strong>${escapeHtml(student.full_name)}</strong><br /><span>${escapeHtml(student.email)}</span></td><td>${escapeHtml(student.port_id || '—')}</td><td>${escapeHtml(student.college_name || '—')}</td><td>${student.is_active ? 'Active' : 'Inactive'} · ${student.is_verified ? 'Verified' : 'Unverified'}</td><td><button type="button" class="small-button" data-student-open="${escapeHtml(student.id)}">Manage student</button></td></tr>`).join('')}</tbody></table></div>`
            : '<p class="empty-state">No students match this search.</p>'}<div class="admin-pagination"><span>Showing ${first}–${last} of ${data.total}</span><div><button type="button" class="small-button" data-student-page="${Math.max(0, offset - studentPageSize)}" ${offset === 0 ? 'disabled' : ''}>Previous</button><button type="button" class="small-button" data-student-page="${offset + studentPageSize}" ${offset + data.items.length >= data.total ? 'disabled' : ''}>Next</button></div></div>`;
    } catch (error) {
        root.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
    }
}

function renderStudentRecords(detail) {
    const root = document.getElementById('admin-student-records');
    const groups = Object.entries(studentRecordConfigs).map(([resource, config]) => {
        const items = detail.records[resource] || [];
        return `<section class="admin-record-group"><div class="panel-heading"><h3>${escapeHtml(config.label)} <span class="record-count">${items.length}</span></h3><button type="button" class="small-button" data-record-add="${resource}">Add</button></div>${items.length
            ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${config.columns.map((field) => `<th>${escapeHtml(readableFieldName(field))}</th>`).join('')}<th>Actions</th></tr></thead><tbody>${items.map((item) => `<tr>${config.columns.map((field) => `<td>${escapeHtml(displayStudentValue(item[field]))}</td>`).join('')}<td><button type="button" class="small-button" data-record-edit="${resource}" data-record-id="${escapeHtml(item.id)}">Edit</button><button type="button" class="small-button danger-button" data-record-delete="${resource}" data-record-id="${escapeHtml(item.id)}">Delete</button></td></tr>`).join('')}</tbody></table></div>`
            : '<p class="empty-state">No records yet.</p>'}</section>`;
    });
    for (const [key, config] of Object.entries(readOnlyStudentRecords)) {
        const data = detail.records[key] || [];
        const rows = Array.isArray(data) ? data : (data ? [data] : []);
        const toolbar = config.create
            ? `<button type="button" class="small-button" data-activity-add="${key}">Add</button>`
            : key === 'settings'
                ? '<button type="button" class="small-button" data-activity-edit="settings">Edit settings</button>'
                : '';
        const body = rows.length
            ? `<div class="admin-table-wrap"><table class="admin-table"><thead><tr>${config.columns.map((field) => `<th>${escapeHtml(readableFieldName(field))}</th>`).join('')}${config.actions ? '<th>Actions</th>' : ''}</tr></thead><tbody>${rows.map((item) => {
                const controls = [];
                if (config.actions?.includes('edit')) controls.push(`<button type="button" class="small-button" data-activity-edit="${key}" data-activity-id="${escapeHtml(item.id || activeAdminStudent.student.id)}">Edit</button>`);
                if (config.actions?.includes('status')) {
                    controls.push(`<select aria-label="${escapeHtml(config.label)} status" data-activity-status-value="${key}" data-activity-id="${escapeHtml(item.id)}">${config.statuses.map((option) => `<option value="${escapeHtml(option)}" ${item.status === option ? 'selected' : ''}>${escapeHtml(readableFieldName(option))}</option>`).join('')}</select><button type="button" class="small-button" data-activity-status="${key}" data-activity-id="${escapeHtml(item.id)}">Save status</button>`);
                }
                if (config.actions?.includes('delete')) controls.push(`<button type="button" class="small-button danger-button" data-activity-delete="${key}" data-activity-id="${escapeHtml(item.id)}">${key === 'sessions' ? 'Revoke' : 'Delete'}</button>`);
                if (config.actions?.includes('support')) controls.push(`<button type="button" class="small-button" data-support-review="${escapeHtml(item.id)}">Review & reply</button>`);
                return `<tr>${config.columns.map((field) => `<td>${escapeHtml(displayStudentValue(item[field]))}</td>`).join('')}${config.actions ? `<td class="admin-row-actions">${controls.join('')}</td>` : ''}</tr>`;
            }).join('')}</tbody></table></div>`
            : `<p class="empty-state">${key === 'settings' ? 'Settings not initialized yet.' : 'No records.'}</p>`;
        groups.push(`<section class="admin-record-group"><div class="panel-heading"><h3>${escapeHtml(config.label)} <span class="record-count">${rows.length}</span></h3>${toolbar}</div>${body}</section>`);
    }
    root.innerHTML = groups.join('');
}

function renderStudentDetail(detail) {
    activeAdminStudent = detail;
    const { student, profile } = detail;
    document.getElementById('admin-student-detail').hidden = false;
    document.getElementById('admin-student-title').textContent = student.full_name;
    document.getElementById('admin-student-summary').textContent =
        `${student.email} · ${student.port_id || 'No Port ID'} · ${student.is_active ? 'Active' : 'Inactive'} · ${student.is_verified ? 'Verified' : 'Unverified'}`;
    const accountFields = [
        ['Email', student.email],
        ['Student ID', student.id],
        ['Account created', student.created_at],
        ['Account status', student.is_active ? 'Active' : 'Inactive'],
        ['Verification', student.is_verified ? 'Verified' : 'Unverified'],
    ];
    const profileFields = studentProfileFields.map((field) => [field.label, profile?.[field.name]]);
    document.getElementById('admin-student-profile').innerHTML = [...accountFields, ...profileFields]
        .map(([label, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(displayStudentValue(value))}</strong></article>`)
        .join('');
    renderStudentRecords(detail);
}

async function openAdminStudent(studentId) {
    const root = document.getElementById('admin-student-detail');
    root.hidden = false;
    root.scrollIntoView({ behavior: 'smooth', block: 'start' });
    document.getElementById('admin-student-title').textContent = 'Loading student…';
    try {
        const detail = await adminRequest(`/admin/students/${studentId}`);
        renderStudentDetail(detail);
    } catch (error) {
        root.hidden = false;
        document.getElementById('admin-student-title').textContent = 'Unable to load student';
        document.getElementById('admin-student-summary').textContent = error.message;
    }
}

function openStudentAccountDialog(mode) {
    const form = document.getElementById('admin-student-form');
    const title = document.getElementById('admin-student-form-title');
    const fields = document.getElementById('admin-student-form-fields');
    form.reset();
    form.dataset.mode = mode;
    const student = activeAdminStudent?.student;
    const profile = activeAdminStudent?.profile || {};
    const accountFields = [
        { name: 'full_name', label: 'Full name', required: true, minlength: 2, maxlength: 255 },
        { name: 'email', label: 'Email', type: 'email', required: true, maxlength: 255 },
        { name: 'password', label: mode === 'create' ? 'Temporary password (12+ characters)' : 'New password (leave blank to keep current)', type: 'password', required: mode === 'create', minlength: mode === 'create' ? 12 : undefined, maxlength: 128 },
    ];
    const values = {
        full_name: student?.full_name || '',
        email: student?.email || '',
        is_active: student?.is_active ?? true,
        is_verified: student?.is_verified ?? false,
        ...profile,
    };
    if (mode === 'edit') {
        accountFields.push(
            { name: 'is_active', label: 'Account active', type: 'checkbox' },
            { name: 'is_verified', label: 'Account verified', type: 'checkbox' },
            ...studentProfileFields,
        );
    }
    fields.innerHTML = accountFields.map((field) => studentFormField(field, values[field.name], field.required)).join('');
    title.textContent = mode === 'create' ? 'Create student account' : `Edit ${student.full_name}`;
    form.querySelector('[data-message]').textContent = '';
    document.getElementById('admin-student-dialog').showModal();
}

function openStudentRecordDialog(resource, record = null) {
    const config = studentRecordConfigs[resource];
    activeAdminRecord = { resource, id: record?.id || null };
    const form = document.getElementById('admin-record-form');
    form.reset();
    form.dataset.resource = resource;
    form.dataset.kind = 'record';
    document.getElementById('admin-record-form-title').textContent = `${record ? 'Edit' : 'Add'} ${config.label.toLowerCase()}`;
    document.getElementById('admin-record-form-fields').innerHTML = config.fields
        .map((field) => studentFormField(field, record?.[field.name]))
        .join('');
    form.querySelector('[data-message]').textContent = '';
    document.getElementById('admin-record-dialog').showModal();
}

function openStudentActivityDialog(resource, record = null) {
    const config = readOnlyStudentRecords[resource];
    activeAdminRecord = {
        resource,
        id: resource === 'settings' ? activeAdminStudent.student.id : (record?.id || null),
        activityType: config.activity,
    };
    const form = document.getElementById('admin-record-form');
    form.reset();
    form.dataset.resource = resource;
    form.dataset.kind = 'activity';
    const values = resource === 'settings'
        ? {
            email_preferences: record?.email_preferences || {},
            notification_settings: record?.notification_settings || {},
            privacy_settings: record?.privacy_settings || {},
            profile_visibility: record?.profile_visibility || activeAdminStudent.profile?.profile_visibility || 'private',
            deactivation_requested: record?.deactivation_requested || false,
        }
        : (record || {});
    document.getElementById('admin-record-form-title').textContent = `${record ? 'Edit' : 'Add'} ${config.label.toLowerCase()}`;
    document.getElementById('admin-record-form-fields').innerHTML = config.fields
        .map((field) => studentFormField(field, values[field.name]))
        .join('');
    form.querySelector('[data-message]').textContent = '';
    document.getElementById('admin-record-dialog').showModal();
}

async function submitStudentAccount(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const mode = form.dataset.mode;
    const baseFields = [
        { name: 'full_name' },
        { name: 'email' },
        { name: 'password' },
    ];
    const profilePayload = mode === 'edit'
        ? collectStudentForm(form, studentProfileFields)
        : {};
    const values = collectStudentForm(form, baseFields);
    const payload = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== null && value !== ''));
    if (mode === 'edit') {
        payload.is_active = form.elements.namedItem('is_active').checked;
        payload.is_verified = form.elements.namedItem('is_verified').checked;
        Object.assign(payload, profilePayload);
    }
    try {
        const path = mode === 'create'
            ? '/admin/students'
            : `/admin/students/${activeAdminStudent.student.id}`;
        const detail = await adminRequest(path, {
            method: mode === 'create' ? 'POST' : 'PATCH',
            body: JSON.stringify(payload),
        });
        document.getElementById('admin-student-dialog').close();
        await Promise.all([loadAdminStudents(), loadAdminActivity(), loadAdminDashboard()]);
        if (mode === 'edit') renderStudentDetail(detail);
        else await openAdminStudent(detail.student.id);
        alertAdmin(mode === 'create' ? 'Student account created.' : 'Student profile updated.');
    } catch (error) {
        setAdminMessage(form.querySelector('[data-message]'), error.message, true);
    }
}

async function submitStudentRecord(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const resource = form.dataset.resource;
    const isActivity = form.dataset.kind === 'activity';
    const config = isActivity ? readOnlyStudentRecords[resource] : studentRecordConfigs[resource];
    let payload;
    try {
        payload = collectStudentForm(form, config.fields);
    } catch (error) {
        setAdminMessage(form.querySelector('[data-message]'), error.message, true);
        return;
    }
    try {
        const studentId = activeAdminStudent.student.id;
        const editing = activeAdminRecord.id !== null;
        const path = isActivity
            ? `/admin/students/${studentId}/activities/${config.activity}${editing && config.activity !== 'settings' ? `/${activeAdminRecord.id}` : editing ? `/${studentId}` : ''}`
            : `/admin/students/${studentId}/records/${resource}${editing ? `/${activeAdminRecord.id}` : ''}`;
        await adminRequest(path, {
            method: editing ? 'PATCH' : 'POST',
            body: JSON.stringify(payload),
        });
        document.getElementById('admin-record-dialog').close();
        renderStudentDetail(await adminRequest(`/admin/students/${studentId}`));
        await Promise.all([loadAdminActivity(), loadAdminDashboard()]);
        alertAdmin(`${config.label} ${editing ? 'updated' : 'added'}.`);
    } catch (error) {
        setAdminMessage(form.querySelector('[data-message]'), error.message, true);
    }
}

async function updateStudentActivity(resource, recordId, values) {
    const config = readOnlyStudentRecords[resource];
    const studentId = activeAdminStudent.student.id;
    try {
        await adminRequest(
            `/admin/students/${studentId}/activities/${config.activity}/${recordId}`,
            { method: 'PATCH', body: JSON.stringify(values) },
        );
        renderStudentDetail(await adminRequest(`/admin/students/${studentId}`));
        await Promise.all([loadAdminActivity(), loadAdminDashboard()]);
        alertAdmin(`${config.label} updated.`);
    } catch (error) {
        alertAdmin(error.message, true);
    }
}

async function deleteStudentActivity(resource, recordId) {
    const config = readOnlyStudentRecords[resource];
    const studentId = activeAdminStudent.student.id;
    const label = resource === 'sessions' ? 'revoke this login session' : `delete this ${config.label.toLowerCase()} record`;
    if (!window.confirm(`Are you sure you want to ${label}?`)) return;
    const id = resource === 'settings' ? studentId : recordId;
    try {
        await adminRequest(
            `/admin/students/${studentId}/activities/${config.activity}/${id}`,
            { method: 'DELETE' },
        );
        renderStudentDetail(await adminRequest(`/admin/students/${studentId}`));
        await Promise.all([loadAdminActivity(), loadAdminDashboard()]);
        alertAdmin(resource === 'sessions' ? 'Student login session revoked.' : `${config.label} deleted.`);
    } catch (error) {
        alertAdmin(error.message, true);
    }
}

function openStudentSupportTicket(ticketId) {
    activateAdminView('support');
    loadAdminTicket(ticketId);
}

function activateAdminView(view) {
    document.querySelectorAll('.admin-view').forEach((section) => section.classList.toggle('is-active', section.id === `admin-view-${view}`));
    document.querySelectorAll('[data-admin-view]').forEach((link) => link.classList.toggle('is-active', link.dataset.adminView === view));
    document.querySelector('.admin-shell .portal-sidebar')?.classList.remove('is-open');
    const load = {
        overview: loadAdminDashboard,
        'skill-tests': loadAdminAssessments,
        students: () => loadAdminStudents(),
        users: () => loadAdminUsers(),
        organizations: loadAdminOrganizations,
        opportunities: () => loadAdminOpportunities(),
        support: () => loadAdminTickets(),
        activity: loadAdminActivity,
    }[view];
    if (load) load();
}

async function updateAdminUser(userId, field, value) {
    try {
        await adminRequest(`/admin/users/${userId}`, {
            method: 'PATCH',
            body: JSON.stringify({ [field]: value }),
        });
        alertAdmin('User record updated.');
        await Promise.all([loadAdminUsers(), loadAdminOrganizations(), loadAdminDashboard(), loadAdminActivity()]);
    } catch (error) {
        alertAdmin(error.message, true);
    }
}

async function logoutAdmin() {
    try {
        await adminRequest('/auth/logout', { method: 'POST' });
    } finally {
        window.location.href = '../login.html';
    }
}

window.addEventListener('DOMContentLoaded', () => {
    renderAssessmentQuestionEditor();
    document.getElementById('admin-assessment-form').addEventListener('submit', submitAdminAssessment);
    document.getElementById('admin-assessment-cancel').addEventListener('click', resetAssessmentForm);
    document.getElementById('admin-register-form').addEventListener('submit', registerAdmin);
    document.querySelectorAll('[data-admin-view]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            activateAdminView(link.dataset.adminView);
        });
    });
    document.getElementById('admin-menu-toggle').addEventListener('click', () => {
        document.querySelector('.admin-shell .portal-sidebar').classList.toggle('is-open');
    });
    document.getElementById('admin-logout').addEventListener('click', logoutAdmin);
    document.getElementById('admin-user-search').addEventListener('submit', (event) => {
        event.preventDefault();
        loadAdminUsers(queryFromForm(event.currentTarget));
    });
    document.getElementById('admin-student-search').addEventListener('submit', (event) => {
        event.preventDefault();
        loadAdminStudents(queryFromForm(event.currentTarget), 0);
    });
    document.getElementById('admin-student-create').addEventListener('click', () => openStudentAccountDialog('create'));
    document.getElementById('admin-student-edit').addEventListener('click', () => openStudentAccountDialog('edit'));
    document.getElementById('admin-student-form').addEventListener('submit', submitStudentAccount);
    document.getElementById('admin-record-form').addEventListener('submit', submitStudentRecord);
    document.querySelectorAll('[data-dialog-close]').forEach((button) => {
        button.addEventListener('click', () => button.closest('dialog').close());
    });
    document.getElementById('admin-student-delete').addEventListener('click', async () => {
        if (!activeAdminStudent) return;
        const { id, full_name: fullName } = activeAdminStudent.student;
        if (!window.confirm(`Permanently delete ${fullName} and all student-owned profile, learning, portfolio, team, support, and account data? This cannot be undone.`)) return;
        try {
            await adminRequest(`/admin/students/${id}`, { method: 'DELETE' });
            document.getElementById('admin-student-detail').hidden = true;
            activeAdminStudent = null;
            await Promise.all([loadAdminStudents(), loadAdminActivity(), loadAdminDashboard()]);
            alertAdmin(`${fullName} and their student-owned records were deleted.`);
        } catch (error) {
            alertAdmin(error.message, true);
        }
    });
    document.getElementById('admin-opportunity-search').addEventListener('submit', (event) => {
        event.preventDefault();
        loadAdminOpportunities(queryFromForm(event.currentTarget));
    });
    document.getElementById('admin-ticket-search').addEventListener('submit', (event) => {
        event.preventDefault();
        loadAdminTickets(queryFromForm(event.currentTarget));
    });
    document.body.addEventListener('click', async (event) => {
        const button = event.target.closest('button');
        if (!button) return;
        if (button.dataset.studentPage !== undefined) {
            await loadAdminStudents(studentSearchQuery, Number(button.dataset.studentPage));
        }
        if (button.dataset.assessmentEdit) await editAdminAssessment(button.dataset.assessmentEdit);
        if (button.dataset.assessmentActive) {
            try {
                await adminRequest(`/admin/assessments/${button.dataset.assessmentActive}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ is_active: button.dataset.next === 'true' }),
                });
                alertAdmin('Skill test availability updated.');
                await Promise.all([loadAdminAssessments(), loadAdminActivity()]);
            } catch (error) {
                alertAdmin(error.message, true);
            }
        }
        if (button.dataset.assessmentDelete) {
            if (!window.confirm('Delete this skill test?')) return;
            try {
                await adminRequest(`/admin/assessments/${button.dataset.assessmentDelete}`, { method: 'DELETE' });
                alertAdmin('Skill test deleted.');
                await Promise.all([loadAdminAssessments(), loadAdminActivity()]);
            } catch (error) {
                alertAdmin(error.message, true);
            }
        }
        if (button.dataset.studentOpen) await openAdminStudent(button.dataset.studentOpen);
        if (button.dataset.recordAdd) openStudentRecordDialog(button.dataset.recordAdd);
        if (button.dataset.activityAdd) openStudentActivityDialog(button.dataset.activityAdd);
        if (button.dataset.recordEdit) {
            const record = activeAdminStudent?.records[button.dataset.recordEdit]?.find(
                (item) => String(item.id) === button.dataset.recordId,
            );
            if (record) openStudentRecordDialog(button.dataset.recordEdit, record);
        }
        if (button.dataset.activityEdit !== undefined) {
            const resource = button.dataset.activityEdit;
            const rows = activeAdminStudent.records[resource];
            const record = resource === 'settings'
                ? rows
                : rows?.find((item) => String(item.id) === button.dataset.activityId);
            openStudentActivityDialog(resource, record);
        }
        if (button.dataset.activityStatus) {
            const resource = button.dataset.activityStatus;
            const control = button.parentElement.querySelector(
                `[data-activity-status-value="${resource}"][data-activity-id="${button.dataset.activityId}"]`,
            );
            if (control) await updateStudentActivity(resource, button.dataset.activityId, { status: control.value });
        }
        if (button.dataset.activityDelete) {
            await deleteStudentActivity(button.dataset.activityDelete, button.dataset.activityId);
        }
        if (button.dataset.supportReview) openStudentSupportTicket(button.dataset.supportReview);
        if (button.dataset.recordDelete) {
            const config = studentRecordConfigs[button.dataset.recordDelete];
            if (!window.confirm(`Delete this ${config.label.toLowerCase()} record?`)) return;
            try {
                await adminRequest(
                    `/admin/students/${activeAdminStudent.student.id}/records/${button.dataset.recordDelete}/${button.dataset.recordId}`,
                    { method: 'DELETE' },
                );
                activeAdminStudent = await adminRequest(`/admin/students/${activeAdminStudent.student.id}`);
                renderStudentDetail(activeAdminStudent);
                await Promise.all([loadAdminActivity(), loadAdminDashboard()]);
                alertAdmin(`${config.label} record deleted.`);
            } catch (error) {
                alertAdmin(error.message, true);
            }
        }
        if (button.dataset.userVerify) await updateAdminUser(button.dataset.userVerify, 'is_verified', button.dataset.next === 'true');
        if (button.dataset.userActive) await updateAdminUser(button.dataset.userActive, 'is_active', button.dataset.next === 'true');
        if (button.dataset.opportunityId) {
            try {
                await adminRequest(`/admin/opportunities/${button.dataset.opportunityId}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ is_active: button.dataset.next === 'true' }),
                });
                alertAdmin('Opportunity moderation saved.');
                await Promise.all([loadAdminOpportunities(), loadAdminActivity(), loadAdminDashboard()]);
            } catch (error) {
                alertAdmin(error.message, true);
            }
        }
        if (button.dataset.adminTicket) await loadAdminTicket(button.dataset.adminTicket);
    });
    document.getElementById('admin-ticket-detail').addEventListener('submit', async (event) => {
        event.preventDefault();
        const form = event.target;
        const ticketId = event.currentTarget.dataset.ticketId;
        try {
            if (form.id === 'admin-ticket-reply') {
                await adminRequest(`/admin/support/tickets/${ticketId}/responses`, {
                    method: 'POST',
                    body: JSON.stringify(Object.fromEntries(new FormData(form).entries())),
                });
                alertAdmin('Support response sent.');
            } else if (form.id === 'admin-ticket-status') {
                await adminRequest(`/admin/support/tickets/${ticketId}`, {
                    method: 'PATCH',
                    body: JSON.stringify(Object.fromEntries(new FormData(form).entries())),
                });
                alertAdmin('Ticket status updated.');
            }
            await Promise.all([loadAdminTicket(ticketId), loadAdminTickets(), loadAdminActivity()]);
        } catch (error) {
            alertAdmin(error.message, true);
        }
    });
    checkAdminAccess();
});
