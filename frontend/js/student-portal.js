const apiBase = (() => {
    const configuredBase = window.PORTFOLIA_API_BASE
        || document.querySelector('meta[name="portfolia-api-base"]')?.content.trim();
    if (configuredBase) return configuredBase.replace(/\/+$/, '');

    const hostname = window.location.hostname;
    const local = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname) || hostname.endsWith('.localhost');
    const apiOrigin = local ? `${window.location.protocol}//${hostname}:8000` : window.location.origin;
    return `${apiOrigin}/api/v1`;
})();

localStorage.removeItem('portfolia_access_token');

const portalState = {
    profile: null,
    projects: [],
    activities: [],
    activeAttempt: null,
    attemptTimer: null,
    activeTeamId: null,
};

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (character) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    })[character]);
}

function showMessage(target, text, isError = false) {
    if (!target) return;
    target.textContent = text;
    target.classList.toggle('is-error', isError);
    target.classList.toggle('is-success', !isError);
}

function formMessage(form, text, isError = false) {
    showMessage(form.querySelector('[data-message]'), text, isError);
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
        const error = new Error('Unable to reach the API. Check that the backend is running and try again.');
        error.status = 0;
        throw error;
    }

    if (response.status === 204) return null;
    const contentType = response.headers.get('content-type') || '';
    const data = contentType.includes('application/json') ? await response.json() : null;
    if (!response.ok) {
        const error = new Error(data?.detail || data?.message || `Request failed (${response.status})`);
        error.status = response.status;
        throw error;
    }
    return data;
}

function handlePageError(error, target) {
    if (error.status === 401) {
        window.location.href = '../login.html';
        return;
    }
    if (target) target.innerHTML = `<p class="error-state">${escapeHtml(error.message)}</p>`;
}

function formObject(form) {
    return Object.fromEntries(new FormData(form).entries());
}

function csvValues(value) {
    return String(value || '').split(',').map((item) => item.trim()).filter(Boolean);
}

function navigate(view) {
    document.querySelectorAll('.portal-view').forEach((section) => {
        section.classList.toggle('is-active', section.id === `view-${view}`);
    });
    document.querySelectorAll('.portal-nav [data-view]').forEach((link) => {
        link.classList.toggle('is-active', link.dataset.view === view);
    });
    document.querySelector('.portal-sidebar')?.classList.remove('is-open');
    const loaders = {
        dashboard: loadDashboard,
        details: loadDetails,
        learning: loadLearning,
        assessments: loadAssessments,
        portfolio: loadPortfolio,
        workspace: loadWorkspace,
        opportunities: loadOpportunities,
        support: loadSupport,
        settings: loadSettings,
    };
    if (loaders[view]) loaders[view]();
}

async function loadDashboard() {
    const metrics = document.getElementById('dashboard-metrics');
    try {
        const [profile, summary] = await Promise.all([
            apiRequest('/students/me'),
            apiRequest('/students/dashboard'),
        ]);
        portalState.profile = profile;
        document.getElementById('username').textContent = profile.full_name;
        document.getElementById('topbar-port-id').textContent = profile.port_id || 'Port ID pending';
        const photo = document.getElementById('profile-photo');
        if (profile.profile_photo_url) {
            photo.src = profile.profile_photo_url;
            photo.hidden = false;
        } else {
            photo.hidden = true;
        }
        metrics.innerHTML = `
            <article class="board-panel"><span class="metric-label">Profile completion</span><strong class="metric-value">${summary.profile_completion_percent}%</strong><progress max="100" value="${summary.profile_completion_percent}"></progress></article>
            <article class="board-panel"><span class="metric-label">Learning records</span><strong class="metric-value">${summary.total_learning_activities}</strong><span>${summary.total_learning_hours} learning hours</span></article>
            <article class="board-panel"><span class="metric-label">Today's learning</span><strong class="metric-value">${summary.daily_learning_activities}</strong><span>Activities dated today</span></article>
            <article class="board-panel"><span class="metric-label">Assessment attempts</span><strong class="metric-value">${summary.skill_assessment_attempts}</strong><span>${summary.latest_assessment_score === null ? 'No scored attempt yet' : `Latest score: ${summary.latest_assessment_score}`}</span></article>
            <article class="board-panel"><span class="metric-label">Portfolio projects</span><strong class="metric-value">${summary.portfolio_project_count}</strong><span>Projects in your portfolio</span></article>
            <article class="board-panel"><span class="metric-label">Workspace teams</span><strong class="metric-value">${summary.active_teams}</strong><span>${summary.team_invitations} pending invitations</span></article>
        `;
        renderDashboardSkills(summary.skills || []);
        renderDashboardActivity(summary.recent_activity || []);
        renderDashboardOpportunities(summary.latest_opportunities || []);
    } catch (error) {
        handlePageError(error, metrics);
    }
}

function renderDashboardSkills(skills) {
    const root = document.getElementById('dashboard-skills');
    root.innerHTML = skills.length
        ? `<ul class="data-list">${skills.map((skill) => `<li><strong>${escapeHtml(skill.name)}</strong><span>${escapeHtml(skill.category)}${skill.proficiency ? ` · ${escapeHtml(skill.proficiency)}` : ''}</span></li>`).join('')}</ul>`
        : '<p class="empty-state">Add skills to see your skills overview.</p>';
}

function renderDashboardActivity(items) {
    const root = document.getElementById('dashboard-activity');
    root.innerHTML = items.length
        ? `<ul class="data-list">${items.map((item) => `<li><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.type)} · ${escapeHtml(new Date(item.occurred_at).toLocaleDateString())}</span></li>`).join('')}</ul>`
        : '<p class="empty-state">Your recent learning and project activity will appear here.</p>';
}

function renderDashboardOpportunities(items) {
    const root = document.getElementById('dashboard-opportunities');
    root.innerHTML = items.length
        ? `<ul class="data-list">${items.map((item) => `<li><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.organization)} · ${escapeHtml(item.category)}</span></li>`).join('')}</ul>`
        : '<p class="empty-state">No opportunities are currently published.</p>';
}

async function loadDetails() {
    const form = document.getElementById('student-profile-form');
    const skillsRoot = document.getElementById('skills-list');
    try {
        const [profile, skills, certifications, achievements] = await Promise.all([
            apiRequest('/students/me'),
            apiRequest('/students/skills'),
            apiRequest('/portfolios/certifications'),
            apiRequest('/portfolios/achievements'),
        ]);
        portalState.profile = profile;
        document.getElementById('student-email').value = profile.email;
        document.getElementById('topbar-port-id').textContent = profile.port_id || 'Port ID pending';
        for (const [name, value] of Object.entries(profile)) {
            const field = form.elements.namedItem(name);
            if (field && value !== null && value !== undefined) {
                field.value = name === 'date_of_birth' ? String(value).slice(0, 10) : value;
            }
        }
        renderSkills(skills, skillsRoot);
        const credentials = document.getElementById('profile-credentials');
        credentials.innerHTML = certifications.length + achievements.length
            ? `<ul class="data-list">${certifications.map((item) => `<li><strong>${escapeHtml(item.name)}</strong><span>Certification${item.issuer ? ` · ${escapeHtml(item.issuer)}` : ''}</span></li>`).concat(achievements.map((item) => `<li><strong>${escapeHtml(item.title)}</strong><span>Achievement${item.awarded_by ? ` · ${escapeHtml(item.awarded_by)}` : ''}</span></li>`)).join('')}</ul>`
            : '<p class="empty-state">No certifications or achievements recorded yet.</p>';
    } catch (error) {
        handlePageError(error, skillsRoot);
    }
}

function renderSkills(skills, root) {
    root.innerHTML = skills.length
        ? `<ul class="data-list">${skills.map((skill) => `<li><div><strong>${escapeHtml(skill.name)}</strong><span>${escapeHtml(skill.category)}${skill.proficiency ? ` · ${escapeHtml(skill.proficiency)}` : ''}${skill.evidence_url ? ` · <a href="${escapeHtml(skill.evidence_url)}" target="_blank" rel="noopener noreferrer">Evidence</a>` : ''}</span></div><button class="small-button danger-button" data-delete-skill="${escapeHtml(skill.id)}">Remove</button></li>`).join('')}</ul>`
        : '<p class="empty-state">No skills added yet.</p>';
}

async function saveProfile(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = formObject(form);
    for (const field of ['date_of_birth', 'graduation_year']) {
        if (!values[field]) values[field] = null;
    }
    if (values.graduation_year) values.graduation_year = Number(values.graduation_year);
    for (const field of ['profile_photo_url', 'linkedin_url', 'github_url', 'personal_website']) {
        if (!values[field]) values[field] = null;
    }
    try {
        await apiRequest('/students/me', { method: 'PUT', body: JSON.stringify(values) });
        formMessage(form, 'Profile saved successfully.');
        await Promise.all([loadDetails(), loadDashboard()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addSkill(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.evidence_url) payload.evidence_url = null;
    try {
        await apiRequest('/students/skills', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        formMessage(form, 'Skill added.');
        await Promise.all([loadDetails(), loadDashboard()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function loadLearning() {
    const history = document.getElementById('learning-history');
    try {
        const [activities, paths, milestones, resources, progress, timeline] = await Promise.all([
            apiRequest('/students/learning-activities'),
            apiRequest('/learning/paths'),
            apiRequest('/learning/milestones'),
            apiRequest('/learning/resources'),
            apiRequest('/learning/progress'),
            apiRequest('/learning/timeline'),
        ]);
        portalState.activities = activities;
        renderLearningHistory(activities, history);
        renderLearningPaths(paths);
        renderMilestones(milestones);
        renderLearningResources(resources);
        renderLearningProgress(progress);
        renderLearningTimeline(timeline);
    } catch (error) {
        handlePageError(error, history);
    }
}

function renderLearningHistory(activities, root) {
    root.innerHTML = activities.length
        ? `<ul class="data-list">${activities.map((item) => `<li><div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.topic || item.category)} · ${escapeHtml(item.status)} · ${item.duration_hours}h · ${escapeHtml(new Date(item.completed_at).toLocaleString())}</span>${item.description ? `<p>${escapeHtml(item.description)}</p>` : ''}</div><button class="small-button" data-edit-learning="${item.id}">Edit</button></li>`).join('')}</ul>`
        : '<p class="empty-state">No daily learning records yet. Add your first activity.</p>';
}

function renderLearningPaths(paths) {
    const root = document.getElementById('learning-paths');
    root.innerHTML = paths.length
        ? `<ul class="data-list">${paths.map((path) => `<li><strong>${escapeHtml(path.title)}</strong><span>${escapeHtml(path.skill_name || 'General')} · ${path.target_date ? escapeHtml(path.target_date) : 'No target date'}</span><p>${escapeHtml(path.description || '')}</p></li>`).join('')}</ul>`
        : '<p class="empty-state">No learning paths created yet.</p>';
}

function renderMilestones(rows) {
    const root = document.getElementById('learning-milestones');
    root.innerHTML = rows.length
        ? `<ul class="data-list">${rows.map((item) => `<li><div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.status)}${item.target_date ? ` · ${escapeHtml(item.target_date)}` : ''}</span></div><button class="small-button" data-toggle-milestone="${escapeHtml(item.id)}">${item.status === 'completed' ? 'Reopen' : 'Complete'}</button></li>`).join('')}</ul>`
        : '<p class="empty-state">No milestones yet.</p>';
}

function renderLearningResources(rows) {
    const root = document.getElementById('learning-resources');
    root.innerHTML = rows.length
        ? `<ul class="data-list">${rows.map((item) => `<li><strong><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a></strong><span>${escapeHtml(item.category)}</span></li>`).join('')}</ul>`
        : '<p class="empty-state">No learning resources saved yet.</p>';
}

function renderLearningProgress(data) {
    const entries = Object.entries(data.by_skill || {});
    const root = document.getElementById('learning-progress');
    root.innerHTML = entries.length
        ? entries.map(([skill, item]) => `<div class="progress-row"><div><strong>${escapeHtml(skill)}</strong><span>${item.completed}/${item.activities} completed · ${item.hours}h</span></div><progress max="100" value="${item.progress_percent}"></progress><span>${item.progress_percent}%</span></div>`).join('')
        : '<p class="empty-state">Progress by skill will be calculated from your learning records.</p>';
}

function renderLearningTimeline(rows) {
    const root = document.getElementById('learning-history');
    if (!rows.length) return;
    const timeline = `<h3>Learning timeline</h3><ul class="timeline">${rows.map((item) => `<li><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.type)} · ${escapeHtml(item.skill || 'General')} · ${escapeHtml(item.status)} · ${escapeHtml(new Date(item.occurred_at).toLocaleDateString())}</span></li>`).join('')}</ul>`;
    root.insertAdjacentHTML('beforeend', timeline);
}

async function submitLearning(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = formObject(form);
    const id = values.id;
    delete values.id;
    values.duration_hours = Number(values.duration_hours || 0);
    values.confidence = values.confidence ? Number(values.confidence) : null;
    values.completed_at = values.completed_at ? new Date(values.completed_at).toISOString() : null;
    for (const field of ['resource_url', 'evidence_url']) {
        if (!values[field]) values[field] = null;
    }
    try {
        await apiRequest(id ? `/students/learning-activities/${id}` : '/students/learning-activities', {
            method: id ? 'PUT' : 'POST',
            body: JSON.stringify(values),
        });
        form.reset();
        form.elements.namedItem('id').value = '';
        formMessage(form, id ? 'Learning record updated.' : 'Learning record saved.');
        await Promise.all([loadLearning(), loadDashboard()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addLearningPath(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.target_date) payload.target_date = null;
    try {
        await apiRequest('/learning/paths', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        formMessage(form, 'Learning path created.');
        await loadLearning();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addMilestone(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.target_date) payload.target_date = null;
    try {
        await apiRequest('/learning/milestones', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        formMessage(form, 'Milestone added.');
        await loadLearning();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addResource(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
        await apiRequest('/learning/resources', { method: 'POST', body: JSON.stringify(formObject(form)) });
        form.reset();
        formMessage(form, 'Resource saved.');
        await loadLearning();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function loadAssessments() {
    const catalogue = document.getElementById('assessment-catalogue');
    try {
        const [assessments, attempts] = await Promise.all([
            apiRequest('/assessments'),
            apiRequest('/assessments/attempts'),
        ]);
        catalogue.innerHTML = assessments.length
            ? `<ul class="data-list">${assessments.map((item) => `<li><div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.category)} · ${item.question_count} question(s) · ${item.duration_minutes} min</span><p>${escapeHtml(item.description)}</p></div><button class="small-button" data-start-assessment="${escapeHtml(item.id)}">Start</button></li>`).join('')}</ul>`
            : '<p class="empty-state">No assessments are available.</p>';
        const history = document.getElementById('assessment-history');
        history.innerHTML = attempts.length
            ? `<ul class="data-list">${attempts.map((item) => `<li><div><strong>${escapeHtml(item.assessment_title || 'Assessment')}</strong><span>${item.score === null ? 'In progress' : `${item.score}/${item.max_score} · ${item.max_score ? Math.round(item.score * 100 / item.max_score) : 0}%`} · ${escapeHtml(new Date(item.started_at).toLocaleString())}</span>${item.topic_scores ? `<small>${escapeHtml(Object.entries(item.topic_scores).map(([topic, score]) => `${topic}: ${score.score}/${score.max_score}`).join(' · '))}</small>` : ''}</div></li>`).join('')}</ul>`
            : '<p class="empty-state">Your assessment attempts and results will appear here.</p>';
    } catch (error) {
        handlePageError(error, catalogue);
    }
}

async function startAssessment(id) {
    const root = document.getElementById('assessment-current');
    try {
        const attempt = await apiRequest(`/assessments/${id}/attempts`, { method: 'POST' });
        portalState.activeAttempt = attempt;
        let remainingSeconds = attempt.duration_minutes * 60;
        root.innerHTML = `
            <article class="board-panel assessment-panel">
                <h2>${escapeHtml(attempt.title)}</h2>
                <p id="assessment-countdown">${attempt.duration_minutes ? `Time allowed: ${attempt.duration_minutes} minutes` : 'Untimed assessment'}</p>
                <form id="assessment-attempt-form" data-attempt-id="${escapeHtml(attempt.attempt_id)}">
                    ${attempt.questions.map((question, index) => `
                        <fieldset class="question-card">
                            <legend>${index + 1}. ${escapeHtml(question.prompt)}</legend>
                            ${question.options.map((option) => `
                                <label class="choice-label">
                                    <input type="${question.question_type === 'multiple_select' ? 'checkbox' : 'radio'}"
                                        name="q-${escapeHtml(question.id)}"
                                        value="${escapeHtml(option)}" />
                                    ${escapeHtml(option)}
                                </label>
                            `).join('')}
                        </fieldset>
                    `).join('')}
                    <button type="submit">Submit answers</button>
                    <button type="button" class="button-link secondary" id="cancel-assessment">Cancel</button>
                    <p class="form-note" data-message role="status"></p>
                </form>
            </article>
        `;
        if (portalState.attemptTimer) clearInterval(portalState.attemptTimer);
        if (attempt.duration_minutes) {
            portalState.attemptTimer = window.setInterval(() => {
                remainingSeconds -= 1;
                const timer = document.getElementById('assessment-countdown');
                if (timer) timer.textContent = `Time remaining: ${Math.floor(remainingSeconds / 60)}:${String(remainingSeconds % 60).padStart(2, '0')}`;
                if (remainingSeconds <= 0) {
                    clearInterval(portalState.attemptTimer);
                    document.getElementById('assessment-attempt-form')?.requestSubmit();
                }
            }, 1000);
        }
        root.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
        handlePageError(error, root);
    }
}

async function submitAssessment(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const answers = {};
    for (const question of portalState.activeAttempt.questions) {
        const selected = [...form.querySelectorAll(`[name="q-${CSS.escape(question.id)}"]:checked`)].map((input) => input.value);
        answers[question.id] = question.question_type === 'multiple_select' ? selected : selected[0] ?? '';
    }
    try {
        const result = await apiRequest(`/assessments/attempts/${form.dataset.attemptId}/submit`, {
            method: 'POST',
            body: JSON.stringify({ answers }),
        });
        clearInterval(portalState.attemptTimer);
        form.closest('.assessment-panel').innerHTML = `<h2>Assessment result</h2><p class="result-score">${result.score}/${result.max_score}</p><p>${result.max_score ? Math.round(result.score * 100 / result.max_score) : 0}% correct</p><p>${escapeHtml(Object.entries(result.topic_scores || {}).map(([topic, score]) => `${topic}: ${score.score}/${score.max_score}`).join(' · '))}</p><p>Review the topics with lower scores to focus your practice.</p>`;
        portalState.activeAttempt = null;
        await Promise.all([loadAssessments(), loadDashboard()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function loadPortfolio() {
    const root = document.getElementById('portfolio-projects');
    try {
        const [projects, certifications, achievements, experience, contributions, profile] = await Promise.all([
            apiRequest('/portfolios/projects'),
            apiRequest('/portfolios/certifications'),
            apiRequest('/portfolios/achievements'),
            apiRequest('/portfolios/experience'),
            apiRequest('/portfolios/contributions'),
            apiRequest('/students/me'),
        ]);
        portalState.projects = projects;
        root.innerHTML = projects.length
            ? `<ul class="data-list">${projects.map((item) => `<li><div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.status)} · ${item.is_public ? 'Public' : 'Private'} · ${item.technologies.map(escapeHtml).join(', ')}</span><p>${escapeHtml(item.description || '')}</p>${item.verified_at ? '<small>Institutionally verified</small>' : ''}</div><button class="small-button" data-edit-project="${escapeHtml(item.id)}">Edit</button></li>`).join('')}</ul>`
            : '<p class="empty-state">No portfolio projects yet.</p>';
        document.getElementById('certifications-list').innerHTML = certifications.length
            ? `<ul class="data-list">${certifications.map((item) => `<li><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.issuer || 'Issuer not specified')}</span></li>`).join('')}</ul>`
            : '<p class="empty-state">No certifications recorded.</p>';
        document.getElementById('achievements-list').innerHTML = achievements.length
            ? `<ul class="data-list">${achievements.map((item) => `<li><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.awarded_by || 'Awarding body not specified')}</span></li>`).join('')}</ul>`
            : '<p class="empty-state">No achievements recorded.</p>';
        document.getElementById('work-experience-list').innerHTML = experience.length
            ? `<ul class="data-list">${experience.map((item) => `<li><strong>${escapeHtml(item.role)} · ${escapeHtml(item.organization)}</strong><span>${escapeHtml(item.start_date || '')}${item.end_date ? ` – ${escapeHtml(item.end_date)}` : ''}</span><p>${escapeHtml(item.description || '')}</p></li>`).join('')}</ul>`
            : '<p class="empty-state">No work experience recorded.</p>';
        document.getElementById('portfolio-contributions').innerHTML = contributions.length
            ? `<ul class="data-list">${contributions.map((item) => `<li><strong>${escapeHtml(item.description)}</strong><span>${escapeHtml(new Date(item.created_at).toLocaleDateString())}${item.evidence_url ? ` · <a href="${escapeHtml(item.evidence_url)}" target="_blank" rel="noopener noreferrer">Evidence</a>` : ''}</span></li>`).join('')}</ul>`
            : '<p class="empty-state">Team contributions you record will appear here.</p>';
        const linkRoot = document.getElementById('public-portfolio-link');
        linkRoot.innerHTML = profile.port_id && profile.profile_visibility === 'public'
            ? `<a href="public-portfolio.html?port_id=${encodeURIComponent(profile.port_id)}">View public portfolio</a>`
            : '<span class="muted-text">Set profile visibility to public to share your portfolio.</span>';
    } catch (error) {
        handlePageError(error, root);
    }
}

function fillProjectForm(projectId) {
    const project = portalState.projects.find((item) => item.id === projectId);
    const form = document.getElementById('project-form');
    if (!project || !form) return;
    form.elements.namedItem('id').value = project.id;
    for (const key of ['title', 'description', 'problem_statement', 'objective', 'student_role', 'duration', 'status', 'github_url', 'live_url']) {
        form.elements.namedItem(key).value = project[key] || '';
    }
    for (const key of ['technologies', 'team_members', 'evidence_urls']) {
        form.elements.namedItem(key).value = (project[key] || []).join(', ');
    }
    form.elements.namedItem('is_public').checked = project.is_public;
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function saveProject(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = formObject(form);
    const id = values.id;
    const payload = {
        title: values.title,
        description: values.description || null,
        problem_statement: values.problem_statement || null,
        objective: values.objective || null,
        technologies: csvValues(values.technologies),
        student_role: values.student_role || null,
        team_members: csvValues(values.team_members),
        duration: values.duration || null,
        status: values.status,
        github_url: values.github_url || null,
        live_url: values.live_url || null,
        evidence_urls: csvValues(values.evidence_urls),
        key_learnings: values.key_learnings || null,
        is_public: form.elements.namedItem('is_public').checked,
    };
    try {
        await apiRequest(id ? `/portfolios/projects/${id}` : '/portfolios/projects', {
            method: id ? 'PUT' : 'POST',
            body: JSON.stringify(payload),
        });
        form.reset();
        form.elements.namedItem('id').value = '';
        formMessage(form, id ? 'Project updated.' : 'Project added to your portfolio.');
        await Promise.all([loadPortfolio(), loadDashboard()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addCertification(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.credential_url) payload.credential_url = null;
    if (!payload.issued_at) payload.issued_at = null;
    try {
        await apiRequest('/portfolios/certifications', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        formMessage(form, 'Certification added.');
        await loadPortfolio();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addAchievement(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.achieved_at) payload.achieved_at = null;
    try {
        await apiRequest('/portfolios/achievements', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        formMessage(form, 'Achievement added.');
        await loadPortfolio();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function addWorkExperience(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.start_date) payload.start_date = null;
    if (!payload.end_date) payload.end_date = null;
    try {
        await apiRequest('/portfolios/experience', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        formMessage(form, 'Work experience added.');
        await loadPortfolio();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function loadWorkspace(queryString = '') {
    const discovery = document.getElementById('team-discovery');
    try {
        const [teams, mine, invitations] = await Promise.all([
            apiRequest(`/teams${queryString}`),
            apiRequest('/teams/mine'),
            apiRequest('/teams/invitations'),
        ]);
        discovery.innerHTML = teams.length
            ? teams.map((team) => `<article class="mini-card"><h3>${escapeHtml(team.name)}</h3><p>${escapeHtml(team.project_name)} · ${escapeHtml(team.category || 'General')}</p><p>${escapeHtml(team.description || '')}</p><p>Skills: ${escapeHtml((team.required_skills || []).join(', ') || 'Not specified')} · ${team.open_positions} open position(s)</p></article>`).join('')
            : '<p class="empty-state">No open teams match your search.</p>';
        const myRoot = document.getElementById('my-teams');
        myRoot.innerHTML = mine.length
            ? mine.map((team) => `<article class="mini-card"><h3>${escapeHtml(team.name)}</h3><p>${escapeHtml(team.project_name)} · ${escapeHtml(team.status)}</p><button class="small-button" data-open-team="${escapeHtml(team.id)}">Open workspace</button></article>`).join('')
            : '<p class="empty-state">You are not part of a team yet. Create one or accept an invitation.</p>';
        const inviteRoot = document.getElementById('team-invitations');
        inviteRoot.innerHTML = invitations.length
            ? `<ul class="data-list">${invitations.map((item) => `<li><div><strong>${escapeHtml(item.team_name || 'Team invitation')}</strong><span>${escapeHtml(item.status)}</span></div>${item.status === 'pending' ? `<button class="small-button" data-accept-invitation="${escapeHtml(item.id)}">Accept</button>` : ''}</li>`).join('')}</ul>`
            : '<p class="empty-state">No team invitations.</p>';
    } catch (error) {
        handlePageError(error, discovery);
    }
}

async function createTeam(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = formObject(form);
    const payload = {
        ...values,
        required_skills: csvValues(values.required_skills),
        team_size: Number(values.team_size),
        open_positions: Number(values.open_positions),
    };
    try {
        await apiRequest('/teams', { method: 'POST', body: JSON.stringify(payload) });
        form.reset();
        form.elements.namedItem('team_size').value = '4';
        form.elements.namedItem('open_positions').value = '1';
        formMessage(form, 'Team and workspace project created.');
        await Promise.all([loadWorkspace(), loadDashboard()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function openTeam(teamId) {
    portalState.activeTeamId = teamId;
    const root = document.getElementById('team-work-area');
    root.innerHTML = '<article class="mini-card"><p>Loading workspace…</p></article>';
    try {
        const [tasks, contributions] = await Promise.all([
            apiRequest(`/teams/${teamId}/tasks`),
            apiRequest(`/teams/${teamId}/contributions`),
        ]);
        root.innerHTML = `
            <article class="mini-card">
                <h3>Project tasks</h3>
                <form id="team-task-form" class="inline-form"><input name="title" placeholder="Task title" required /><input name="description" placeholder="Details" /><button>Add task</button></form>
                <div>${tasks.length ? `<ul class="data-list">${tasks.map((task) => `<li><div><strong>${escapeHtml(task.title)}</strong><span>${escapeHtml(task.status)}${task.due_date ? ` · due ${escapeHtml(task.due_date)}` : ''}</span></div>${task.status !== 'done' ? `<button class="small-button" data-complete-task="${escapeHtml(task.id)}">Mark done</button>` : ''}</li>`).join('')}</ul>` : '<p class="empty-state">No project tasks yet.</p>'}</div>
            </article>
            <article class="mini-card">
                <h3>Record contribution</h3>
                <form id="contribution-form" class="inline-form"><input name="description" placeholder="What did you contribute?" required /><input name="evidence_url" type="url" placeholder="Evidence URL (optional)" /><button>Save contribution</button></form>
                <div>${contributions.length ? `<ul class="data-list">${contributions.map((item) => `<li><strong>${escapeHtml(item.description)}</strong><span>${escapeHtml(new Date(item.created_at).toLocaleDateString())}</span></li>`).join('')}</ul>` : '<p class="empty-state">No contributions recorded.</p>'}</div>
            </article>
            <article class="mini-card">
                <h3>Invite a collaborator</h3>
                <form id="team-invite-form" class="inline-form"><input name="email" type="email" placeholder="Student email" required /><button>Send invitation</button></form>
            </article>`;
    } catch (error) {
        handlePageError(error, root);
    }
}

async function submitTeamTask(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
        await apiRequest(`/teams/${portalState.activeTeamId}/tasks`, {
            method: 'POST',
            body: JSON.stringify(formObject(form)),
        });
        await openTeam(portalState.activeTeamId);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function submitContribution(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = formObject(form);
    if (!payload.evidence_url) payload.evidence_url = null;
    try {
        await apiRequest(`/teams/${portalState.activeTeamId}/contributions`, { method: 'POST', body: JSON.stringify(payload) });
        await openTeam(portalState.activeTeamId);
        await loadDashboard();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function sendTeamInvitation(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
        await apiRequest(`/teams/${portalState.activeTeamId}/invitations`, {
            method: 'POST',
            body: JSON.stringify(formObject(form)),
        });
        form.reset();
        formMessage(form, 'Invitation sent.');
        await loadWorkspace();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function loadOpportunities(query = '') {
    const root = document.getElementById('opportunity-list');
    try {
        const [opportunities, applications, saved] = await Promise.all([
            apiRequest(`/opportunities${query}`),
            apiRequest('/opportunities/applications'),
            apiRequest('/opportunities/saved'),
        ]);
        root.innerHTML = opportunities.length
            ? opportunities.map((item) => `<article class="mini-card"><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.organization)} · ${escapeHtml(item.category)}</p><p>${escapeHtml(item.description)}</p><p><strong>Skills:</strong> ${escapeHtml((item.required_skills || []).join(', ') || 'Not specified')}</p><p><strong>Eligibility:</strong> ${escapeHtml(item.eligibility || 'Not specified')}<br /><strong>Location:</strong> ${escapeHtml(item.location || 'Not specified')} · ${escapeHtml(item.work_mode || 'Work mode not specified')}<br /><strong>Compensation:</strong> ${escapeHtml(item.compensation || 'Not disclosed')}<br /><strong>Deadline:</strong> ${escapeHtml(item.deadline || 'Not specified')}</p>${item.contact_information ? `<p><strong>Contact:</strong> ${escapeHtml(item.contact_information)}</p>` : ''}<div class="card-actions">${item.application_url ? `<a href="${escapeHtml(item.application_url)}" target="_blank" rel="noopener noreferrer">Application details</a>` : ''}<button class="small-button" data-save-opportunity="${escapeHtml(item.id)}">Save</button><button class="small-button" data-apply-opportunity="${escapeHtml(item.id)}">Track application</button></div></article>`).join('')
            : '<p class="empty-state">No opportunities match your search.</p>';
        document.getElementById('opportunity-applications').innerHTML = applications.length
            ? `<ul class="data-list">${applications.map((item) => `<li><div><strong>${escapeHtml(item.opportunity?.title || 'Opportunity')}</strong><span>${escapeHtml(item.application.status)} · ${escapeHtml(new Date(item.application.created_at).toLocaleDateString())}</span></div></li>`).join('')}</ul>`
            : '<p class="empty-state">You have not tracked any applications.</p>';
        document.getElementById('saved-opportunities').innerHTML = saved.length
            ? `<ul class="data-list">${saved.map((item) => `<li><strong>${escapeHtml(item.opportunity?.title || 'Opportunity')}</strong><span>${escapeHtml(item.opportunity?.organization || '')}</span></li>`).join('')}</ul>`
            : '<p class="empty-state">No saved opportunities.</p>';
    } catch (error) {
        handlePageError(error, root);
    }
}

async function searchOpportunities(event) {
    event.preventDefault();
    const values = formObject(event.currentTarget);
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(values)) if (value) params.set(key, value);
    await loadOpportunities(params.size ? `?${params}` : '');
}

async function loadSupport() {
    const root = document.getElementById('support-tickets');
    try {
        const tickets = await apiRequest('/support/tickets');
        root.innerHTML = tickets.length
            ? `<ul class="data-list">${tickets.map((ticket) => `<li><div><strong>${escapeHtml(ticket.subject)}</strong><span>${escapeHtml(ticket.category)} · ${escapeHtml(ticket.status)}</span></div><button class="small-button" data-open-ticket="${escapeHtml(ticket.id)}">View</button></li>`).join('')}</ul>`
            : '<p class="empty-state">No support tickets. Use the form to contact support.</p>';
    } catch (error) {
        handlePageError(error, root);
    }
}

async function createTicket(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
        await apiRequest('/support/tickets', { method: 'POST', body: JSON.stringify(formObject(form)) });
        form.reset();
        formMessage(form, 'Support ticket submitted.');
        await loadSupport();
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function openTicket(ticketId) {
    const root = document.getElementById('ticket-detail');
    try {
        const data = await apiRequest(`/support/tickets/${ticketId}`);
        root.innerHTML = `<article class="mini-card"><h3>${escapeHtml(data.ticket.subject)} · ${escapeHtml(data.ticket.status)}</h3><ul class="data-list">${data.messages.map((message) => `<li><p>${escapeHtml(message.message)}</p><span>${escapeHtml(new Date(message.created_at).toLocaleString())}</span></li>`).join('')}</ul>${data.ticket.status !== 'closed' ? `<form id="ticket-message-form" class="inline-form"><textarea name="message" required placeholder="Add a reply"></textarea><button>Reply</button></form>` : '<p class="muted-text">This ticket is closed.</p>'}</article>`;
        root.dataset.ticketId = ticketId;
    } catch (error) {
        handlePageError(error, root);
    }
}

async function replyToTicket(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const root = document.getElementById('ticket-detail');
    try {
        await apiRequest(`/support/tickets/${root.dataset.ticketId}/messages`, { method: 'POST', body: JSON.stringify(formObject(form)) });
        await openTicket(root.dataset.ticketId);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function loadSettings() {
    const root = document.getElementById('sessions-list');
    try {
        const [settings, sessions, notifications] = await Promise.all([
            apiRequest('/students/settings'),
            apiRequest('/students/sessions'),
            apiRequest('/students/notifications'),
        ]);
        const form = document.getElementById('settings-form');
        form.elements.namedItem('profile_visibility').value = settings.profile_visibility;
        for (const name of ['email_opportunities', 'email_learning']) {
            form.elements.namedItem(name).checked = Boolean(settings.email_preferences?.[name]);
        }
        for (const name of ['notify_team', 'notify_support']) {
            form.elements.namedItem(name).checked = Boolean(settings.notification_settings?.[name]);
        }
        for (const name of ['privacy_show_skills', 'privacy_show_projects']) {
            form.elements.namedItem(name).checked = Boolean(settings.privacy_settings?.[name]);
        }
        root.innerHTML = sessions.length
            ? `<ul class="data-list">${sessions.map((session) => `<li><div><strong>Signed in ${escapeHtml(new Date(session.created_at).toLocaleString())}</strong><span>${escapeHtml(session.user_agent || 'Browser session')} · Expires ${escapeHtml(new Date(session.expires_at).toLocaleString())}</span></div><button class="small-button danger-button" data-revoke-session="${escapeHtml(session.id)}">Revoke</button></li>`).join('')}</ul>`
            : '<p class="empty-state">No active sessions.</p>';
        const notificationsRoot = document.getElementById('notifications-list');
        notificationsRoot.innerHTML = notifications.length
            ? `<ul class="data-list">${notifications.map((item) => `<li><div><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.message)} · ${escapeHtml(new Date(item.created_at).toLocaleString())}</span></div>${item.is_read ? '<span>Read</span>' : `<button class="small-button" data-read-notification="${escapeHtml(item.id)}">Mark read</button>`}</li>`).join('')}</ul>`
            : '<p class="empty-state">No notifications.</p>';
        const deactivation = document.getElementById('deactivation-button');
        if (settings.deactivation_requested) {
            deactivation.disabled = true;
            deactivation.textContent = 'Request pending';
        }
    } catch (error) {
        handlePageError(error, root);
    }
}

async function saveSettings(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = {
        profile_visibility: form.elements.namedItem('profile_visibility').value,
        email_preferences: {
            email_opportunities: form.elements.namedItem('email_opportunities').checked,
            email_learning: form.elements.namedItem('email_learning').checked,
        },
        notification_settings: {
            notify_team: form.elements.namedItem('notify_team').checked,
            notify_support: form.elements.namedItem('notify_support').checked,
        },
        privacy_settings: {
            privacy_show_skills: form.elements.namedItem('privacy_show_skills').checked,
            privacy_show_projects: form.elements.namedItem('privacy_show_projects').checked,
        },
    };
    try {
        await apiRequest('/students/settings', { method: 'PUT', body: JSON.stringify(payload) });
        formMessage(form, 'Preferences saved.');
        await Promise.all([loadDetails(), loadPortfolio()]);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function changePassword(event) {
    event.preventDefault();
    const form = event.currentTarget;
    try {
        await apiRequest('/students/password', { method: 'PUT', body: JSON.stringify(formObject(form)) });
        formMessage(form, 'Password changed. Please sign in again.');
        window.setTimeout(() => {
            window.location.href = '../login.html';
        }, 1000);
    } catch (error) {
        formMessage(form, error.message, true);
    }
}

async function logout() {
    try {
        await apiRequest('/auth/logout', { method: 'POST' });
    } finally {
        window.location.href = '../login.html';
    }
}

function bindForm(id, handler) {
    const form = document.getElementById(id);
    if (form) form.addEventListener('submit', handler);
}

async function loadPublicPortfolio() {
    const root = document.getElementById('public-portfolio');
    const portId = new URLSearchParams(window.location.search).get('port_id');
    if (!portId) {
        root.innerHTML = '<p class="error-state">A portfolio ID is required.</p>';
        return;
    }
    try {
        const data = await apiRequest(`/portfolios/public/${encodeURIComponent(portId)}`);
        document.getElementById('public-name').textContent = data.full_name;
        document.getElementById('public-port-id').textContent = data.port_id;
        document.getElementById('public-bio').textContent = data.bio || '';
        root.innerHTML = `
            <section class="board-panel"><h2>Skills</h2>${data.skills.length ? `<ul class="data-list">${data.skills.map((skill) => `<li><strong>${escapeHtml(skill.name)}</strong><span>${escapeHtml(skill.category)}${skill.proficiency ? ` · ${escapeHtml(skill.proficiency)}` : ''}</span></li>`).join('')}</ul>` : '<p class="empty-state">No public skills listed.</p>'}</section>
            <section class="board-panel"><h2>Public projects</h2>${data.projects.length ? `<ul class="data-list">${data.projects.map((project) => `<li><strong>${escapeHtml(project.title)}</strong><p>${escapeHtml(project.description || '')}</p><span>${escapeHtml((project.technologies || []).join(', '))}</span>${project.github_url ? `<p><a href="${escapeHtml(project.github_url)}" rel="noopener noreferrer">GitHub</a></p>` : ''}${project.live_url ? `<p><a href="${escapeHtml(project.live_url)}" rel="noopener noreferrer">Live project</a></p>` : ''}</li>`).join('')}</ul>` : '<p class="empty-state">No public projects have been shared.</p>'}</section>`;
    } catch (error) {
        handlePageError(error, root);
    }
}

window.addEventListener('DOMContentLoaded', async () => {
    if (document.getElementById('public-portfolio')) {
        await loadPublicPortfolio();
        return;
    }

    try {
        await apiRequest('/auth/me');
    } catch (error) {
        handlePageError(error, document.getElementById('dashboard-metrics'));
        return;
    }

    document.querySelectorAll('.portal-nav [data-view]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            navigate(link.dataset.view);
        });
    });
    document.querySelectorAll('[data-navigate]').forEach((button) => {
        button.addEventListener('click', () => navigate(button.dataset.navigate));
    });
    document.getElementById('menu-toggle').addEventListener('click', () => {
        document.querySelector('.portal-sidebar').classList.toggle('is-open');
    });
    document.getElementById('logout-button').addEventListener('click', logout);

    bindForm('student-profile-form', saveProfile);
    bindForm('skill-form', addSkill);
    bindForm('learning-form', submitLearning);
    bindForm('path-form', addLearningPath);
    bindForm('milestone-form', addMilestone);
    bindForm('resource-form', addResource);
    bindForm('project-form', saveProject);
    bindForm('certification-form', addCertification);
    bindForm('achievement-form', addAchievement);
    bindForm('work-experience-form', addWorkExperience);
    bindForm('team-form', createTeam);
    bindForm('team-search-form', async (event) => {
        event.preventDefault();
        const values = formObject(event.currentTarget);
        const params = new URLSearchParams();
        if (values.q) params.set('q', values.q);
        if (values.skill) params.set('skill', values.skill);
        await loadWorkspace(params.size ? `?${params}` : '');
    });
    bindForm('opportunity-search-form', searchOpportunities);
    bindForm('ticket-form', createTicket);
    bindForm('settings-form', saveSettings);
    bindForm('password-form', changePassword);

    document.getElementById('team-work-area').addEventListener('submit', (event) => {
        if (event.target.id === 'team-task-form') submitTeamTask(event);
        if (event.target.id === 'contribution-form') submitContribution(event);
        if (event.target.id === 'team-invite-form') sendTeamInvitation(event);
    });
    document.getElementById('assessment-current').addEventListener('submit', (event) => {
        if (event.target.id === 'assessment-attempt-form') submitAssessment(event);
    });

    document.getElementById('deactivation-button').addEventListener('click', async (event) => {
        const button = event.currentTarget;
        try {
            await apiRequest('/students/settings', { method: 'PUT', body: JSON.stringify({ deactivation_requested: true }) });
            showMessage(button.nextElementSibling, 'Deactivation request submitted for review.');
            button.disabled = true;
        } catch (error) {
            showMessage(button.nextElementSibling, error.message, true);
        }
    });

    document.body.addEventListener('click', async (event) => {
        const target = event.target.closest('button');
        if (!target) return;
        if (target.dataset.startAssessment) await startAssessment(target.dataset.startAssessment);
        if (target.id === 'cancel-assessment') {
            clearInterval(portalState.attemptTimer);
            document.getElementById('assessment-current').replaceChildren();
            portalState.activeAttempt = null;
        }
        if (target.dataset.editProject) fillProjectForm(target.dataset.editProject);
        if (target.dataset.deleteSkill) {
            try {
                await apiRequest(`/students/skills/${target.dataset.deleteSkill}`, { method: 'DELETE' });
                await Promise.all([loadDetails(), loadDashboard()]);
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.editLearning) {
            const item = portalState.activities.find((activity) => activity.id === Number(target.dataset.editLearning));
            const form = document.getElementById('learning-form');
            if (item && form) {
                for (const key of ['title', 'category', 'topic', 'description', 'what_i_practised', 'resource_url', 'evidence_url', 'confidence', 'status', 'duration_hours']) {
                    form.elements.namedItem(key).value = item[key] ?? '';
                }
                form.elements.namedItem('id').value = item.id;
                const date = new Date(item.completed_at);
                form.elements.namedItem('completed_at').value = new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
                form.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
        if (target.dataset.toggleMilestone) {
            try {
                await apiRequest(`/learning/milestones/${target.dataset.toggleMilestone}`, { method: 'PATCH' });
                await loadLearning();
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.openTeam) await openTeam(target.dataset.openTeam);
        if (target.dataset.acceptInvitation) {
            try {
                await apiRequest(`/teams/invitations/${target.dataset.acceptInvitation}/accept`, { method: 'POST' });
                await Promise.all([loadWorkspace(), loadDashboard()]);
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.completeTask) {
            try {
                await apiRequest(`/teams/${portalState.activeTeamId}/tasks/${target.dataset.completeTask}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ status: 'done' }),
                });
                await openTeam(portalState.activeTeamId);
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.saveOpportunity) {
            try {
                await apiRequest(`/opportunities/${target.dataset.saveOpportunity}/save`, { method: 'POST' });
                await loadOpportunities();
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.applyOpportunity) {
            try {
                await apiRequest(`/opportunities/${target.dataset.applyOpportunity}/apply`, { method: 'POST' });
                await loadOpportunities();
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.openTicket) await openTicket(target.dataset.openTicket);
        if (target.dataset.revokeSession) {
            try {
                await apiRequest(`/students/sessions/${target.dataset.revokeSession}`, { method: 'DELETE' });
                await loadSettings();
            } catch (error) {
                window.alert(error.message);
            }
        }
        if (target.dataset.readNotification) {
            try {
                await apiRequest(`/students/notifications/${target.dataset.readNotification}/read`, { method: 'PATCH' });
                await loadSettings();
            } catch (error) {
                window.alert(error.message);
            }
        }
    });

    document.getElementById('assessment-current').addEventListener('click', (event) => {
        if (event.target.id === 'cancel-assessment') {
            clearInterval(portalState.attemptTimer);
            document.getElementById('assessment-current').replaceChildren();
            portalState.activeAttempt = null;
        }
    });
    document.getElementById('support-tickets').addEventListener('click', async (event) => {
        const button = event.target.closest('[data-open-ticket]');
        if (button) await openTicket(button.dataset.openTicket);
    });
    document.getElementById('ticket-detail').addEventListener('submit', replyToTicket);

    const initialView = window.location.hash.slice(1);
    if (initialView && document.getElementById(`view-${initialView}`)) {
        navigate(initialView);
    } else {
        await loadDashboard();
    }
});
