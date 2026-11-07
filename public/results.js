const API_BASE = window.location.origin;

let autoRefresh = true;
let refreshInterval = 4000; // 4s keeps updates live without overloading SQLite
let timerId = null;
let currentTheme = 'dark'; // default theme
let isAuthenticated = false;
let currentUserRole = null;

// Vote rate tracking
let voteHistory = []; // Array of timestamps of votes
let vpsUpdateInterval = null;

// Performance tracking
let performanceMetrics = {
    apiResponseTimes: [],
    failedRequests: 0,
    lastSyncTime: null,
    lastSyncSuccess: true,
    startTime: Date.now(),
    sessionStartTime: null
};
let perfUpdateInterval = null;
let heartbeatIntervalId = null;
let connectedDevicesIntervalId = null;

const resultsContainer = document.getElementById('results-container');
const toggleAutoBtn = document.getElementById('toggle-auto');
const refreshBtn = document.getElementById('refresh');
const downloadCsvBtn = document.getElementById('download-csv');
const toggleThemeBtn = document.getElementById('toggle-theme');
const fullscreenBtn = document.getElementById('fullscreen');
const totalVotesDisplay = document.getElementById('total-votes-display');
const authOverlay = document.getElementById('auth-overlay');
const resultsContent = document.getElementById('results-content');
const logoutBtn = document.getElementById('logout');
const vpsCounter = document.getElementById('vps-counter');
const peakVps = document.getElementById('peak-vps');
const avgVps = document.getElementById('avg-vps');

// Performance DOM elements
const apiResponseTimeEl = document.getElementById('api-response-time');
const lastSyncTimeEl = document.getElementById('last-sync-time');
const uptimeDisplayEl = document.getElementById('uptime-display');
const memoryUsageEl = document.getElementById('memory-usage');
const failedRequestsEl = document.getElementById('failed-requests');

// Token Stats Elements
const totalTokensEl = document.getElementById('total-tokens');
const spentTokensEl = document.getElementById('spent-tokens');
const remainingTokensEl = document.getElementById('remaining-tokens');

const serverStatusEl = document.getElementById('server-status');
const serverStatusBadge = document.getElementById('server-status-badge');
const apiStatusBadge = document.getElementById('api-status-badge');
const syncStatusBadge = document.getElementById('sync-status-badge');
const memoryStatusBadge = document.getElementById('memory-status-badge');
const errorStatusBadge = document.getElementById('error-status-badge');
const connectedDevicesSection = document.getElementById('connected-devices-section');
const connectedDevicesBody = document.getElementById('connected-devices-body');
const devicesTotalEl = document.getElementById('devices-total');
const devicesOnlineEl = document.getElementById('devices-online');
const devicesIdleEl = document.getElementById('devices-idle');
const devicesOfflineEl = document.getElementById('devices-offline');
const requestMetricsSection = document.getElementById('request-metrics-section');
const requestMetricsBody = document.getElementById('request-metrics-body');
const metricsTotalIpsEl = document.getElementById('metrics-total-ips');
const metricsTopCountEl = document.getElementById('metrics-top-count');
const metricsTopErrorsEl = document.getElementById('metrics-top-errors');
const serverStatusIndicator = document.getElementById('server-status-indicator');
const electionStatusEl = document.getElementById('election-current-status');
const winnerDeclarationInput = document.getElementById('winner-declaration-input');
const winnerDeclarationDisplay = document.getElementById('winner-display-admin');
const electionAdminMessage = document.getElementById('election-admin-message');
const closeElectionBtn = document.getElementById('close-election-btn');
const reopenElectionBtn = document.getElementById('reopen-election-btn');
const adminKillSwitchBtn = document.getElementById('admin-killswitch-btn');
const restoreLatestBtn = document.getElementById('restore-latest-btn');
const saveWinnerBtn = document.getElementById('save-winner-btn');
const adminSidebar = document.getElementById('admin-sidebar');
const adminSidebarOverlay = document.getElementById('admin-sidebar-overlay');
const adminSidebarToggleBtn = document.getElementById('admin-sidebar-toggle');
const adminSidebarCloseBtn = document.getElementById('admin-sidebar-close');
const timelineToggleBtn = document.getElementById('timeline-toggle-btn');
const timelineYearPicker = document.getElementById('timeline-year-picker');
const timelineYearSelect = document.getElementById('timeline-year-select');
const timelineLoadBtn = document.getElementById('timeline-load-btn');
const timelineContent = document.getElementById('timeline-content');

let lastCandidates = [];
let lastTotalVotes = 0;
let timelineYearsLoaded = false;

function setAdminSidebarOpen(isOpen) {
    document.body.classList.toggle('sidebar-open', Boolean(isOpen));
}

function initializeAdminSidebar() {
    if (!adminSidebar) return;

    if (adminSidebarToggleBtn) {
        adminSidebarToggleBtn.addEventListener('click', () => {
            const willOpen = !document.body.classList.contains('sidebar-open');
            setAdminSidebarOpen(willOpen);
        });
    }

    if (adminSidebarCloseBtn) {
        adminSidebarCloseBtn.addEventListener('click', () => setAdminSidebarOpen(false));
    }

    if (adminSidebarOverlay) {
        adminSidebarOverlay.addEventListener('click', () => setAdminSidebarOpen(false));
    }

    document.querySelectorAll('.admin-sidebar-link').forEach((linkBtn) => {
        linkBtn.addEventListener('click', () => {
            const targetId = linkBtn.getAttribute('data-target-id');
            const target = targetId ? document.getElementById(targetId) : null;
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            setAdminSidebarOpen(false);
        });
    });
}

function formatTimelineDate(value) {
    if (!value) return 'N/A';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function renderTimelineYearData(data) {
    if (!timelineContent) return;

    const leaders = data.leaders || {};
    const president = leaders.president;
    const vice = leaders.vice_president;
    const contestants = Array.isArray(data.contestants) ? data.contestants : [];
    const winnerText = (data.election && data.election.winnerDeclaration) || 'No winner declaration recorded.';

    const contestantsRows = contestants.map((candidate, index) => `
        <tr>
            <td>${index + 1}</td>
            <td>${candidate.name || ''}</td>
            <td>${candidate.position || ''}</td>
            <td>${candidate.votes || 0}</td>
            <td>${candidate.slogan || '-'}</td>
            <td>${candidate.studentId || '-'}</td>
            <td>${formatTimelineDate(candidate.registrationDate)}</td>
        </tr>
    `).join('');

    timelineContent.innerHTML = `
        <div class="timeline-summary-grid">
            <div class="timeline-card">
                <div class="timeline-card-title">President Leader</div>
                <div class="timeline-card-value">${president ? `${president.name} (${president.votes} votes)` : 'No data'}</div>
            </div>
            <div class="timeline-card">
                <div class="timeline-card-title">Vice President Leader</div>
                <div class="timeline-card-value">${vice ? `${vice.name} (${vice.votes} votes)` : 'No data'}</div>
            </div>
            <div class="timeline-card">
                <div class="timeline-card-title">Winner Declaration</div>
                <div class="timeline-card-value">${winnerText}</div>
            </div>
            <div class="timeline-card">
                <div class="timeline-card-title">Archived At</div>
                <div class="timeline-card-value">${formatTimelineDate(data.archivedAt)}</div>
            </div>
        </div>
        <div class="timeline-contestants">
            <table class="timeline-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th>Position</th>
                        <th>Votes</th>
                        <th>Slogan</th>
                        <th>Student ID</th>
                        <th>Registered</th>
                    </tr>
                </thead>
                <tbody>
                    ${contestantsRows || '<tr><td colspan="7">No contestants found for this year.</td></tr>'}
                </tbody>
            </table>
        </div>
    `;
}

async function loadLeadershipTimelineYear(year) {
    if (!timelineContent || !year) return;
    timelineContent.textContent = 'Loading timeline...';

    try {
        const res = await fetch(`${API_BASE}/api/leadership-timeline/${year}`);
        const data = await res.json();
        if (!res.ok) {
            timelineContent.textContent = data.error || 'No timeline data found for this year.';
            return;
        }
        renderTimelineYearData(data);
    } catch (error) {
        timelineContent.textContent = 'Failed to load timeline data.';
    }
}

async function refreshTimelineYears(autoLoadLatest = false) {
    if (!timelineYearSelect) return;

    try {
        const res = await fetch(`${API_BASE}/api/leadership-timeline/years`);
        const data = await res.json();
        const years = Array.isArray(data.years) ? data.years : [];

        const currentValue = timelineYearSelect.value;
        timelineYearSelect.innerHTML = '<option value="">Select year</option>';
        years.forEach((year) => {
            const option = document.createElement('option');
            option.value = String(year);
            option.textContent = String(year);
            timelineYearSelect.appendChild(option);
        });

        if (years.length === 0) {
            timelineContent.textContent = 'No leadership timeline data yet. Close and refresh an election to archive it.';
            return;
        }

        if (currentValue && years.includes(Number(currentValue))) {
            timelineYearSelect.value = currentValue;
        } else if (autoLoadLatest) {
            timelineYearSelect.value = String(years[0]);
            await loadLeadershipTimelineYear(years[0]);
        }
    } catch (error) {
        timelineContent.textContent = 'Failed to fetch timeline years.';
    }
}

function initializeLeadershipTimeline() {
    if (!timelineToggleBtn || !timelineYearPicker) return;

    timelineToggleBtn.addEventListener('click', async () => {
        const willOpen = !timelineYearPicker.classList.contains('open');
        timelineYearPicker.classList.toggle('open', willOpen);
        if (willOpen && !timelineYearsLoaded) {
            await refreshTimelineYears(false);
            timelineYearsLoaded = true;
        }
    });

    if (timelineLoadBtn) {
        timelineLoadBtn.addEventListener('click', () => {
            const year = Number(timelineYearSelect ? timelineYearSelect.value : '');
            if (!year) {
                timelineContent.textContent = 'Please select a year first.';
                return;
            }
            loadLeadershipTimelineYear(year);
        });
    }

    if (timelineYearSelect) {
        timelineYearSelect.addEventListener('change', () => {
            const year = Number(timelineYearSelect.value);
            if (year) {
                loadLeadershipTimelineYear(year);
            }
        });
    }
}

// ===== PERFORMANCE TRACKING FUNCTIONS =====
function trackApiCall(startTime) {
    const responseTime = Date.now() - startTime;
    performanceMetrics.apiResponseTimes.push(responseTime);
    // Keep only last 60 measurements
    if (performanceMetrics.apiResponseTimes.length > 60) {
        performanceMetrics.apiResponseTimes.shift();
    }
    return responseTime;
}

function updatePerformanceDisplay() {
    // API Response Time
    if (performanceMetrics.apiResponseTimes.length > 0) {
        const avgResponseTime = performanceMetrics.apiResponseTimes.reduce((a, b) => a + b, 0) / performanceMetrics.apiResponseTimes.length;
        const lastResponseTime = performanceMetrics.apiResponseTimes[performanceMetrics.apiResponseTimes.length - 1];

        if (apiResponseTimeEl) {
            apiResponseTimeEl.textContent = `${lastResponseTime}ms`;
        }

        // Update API status badge
        if (apiStatusBadge) {
            if (lastResponseTime > 1000) {
                apiStatusBadge.className = 'perf-status critical';
                apiStatusBadge.textContent = 'Slow';
            } else if (lastResponseTime > 500) {
                apiStatusBadge.className = 'perf-status warning';
                apiStatusBadge.textContent = 'Fair';
            } else {
                apiStatusBadge.className = 'perf-status healthy';
                apiStatusBadge.textContent = 'Good';
            }
        }
    }

    // Last Sync Time
    if (performanceMetrics.lastSyncTime) {
        const syncAge = Date.now() - performanceMetrics.lastSyncTime;
        const seconds = Math.floor(syncAge / 1000);

        if (lastSyncTimeEl) {
            lastSyncTimeEl.textContent = `${seconds}s ago`;
        }

        if (syncStatusBadge) {
            if (seconds > 10) {
                syncStatusBadge.className = 'perf-status warning';
                syncStatusBadge.textContent = 'Delayed';
            } else {
                syncStatusBadge.className = 'perf-status healthy';
                syncStatusBadge.textContent = 'Synced';
            }
        }
    }

    // Uptime
    if (performanceMetrics.sessionStartTime) {
        const uptime = Date.now() - performanceMetrics.sessionStartTime;
        const minutes = Math.floor(uptime / 60000);
        const hours = Math.floor(minutes / 60);

        if (uptimeDisplayEl) {
            if (hours > 0) {
                uptimeDisplayEl.textContent = `${hours}h ${minutes % 60}m`;
            } else {
                uptimeDisplayEl.textContent = `${minutes}m`;
            }
        }
    }

    // Memory Usage (simulate with API response time and request count)
    const estimatedMemory = (performanceMetrics.apiResponseTimes.length * 0.5 + performanceMetrics.failedRequests * 2).toFixed(1);
    if (memoryUsageEl) {
        memoryUsageEl.textContent = `${estimatedMemory}MB`;
    }

    if (memoryStatusBadge) {
        const memValue = parseFloat(estimatedMemory);
        if (memValue > 100) {
            memoryStatusBadge.className = 'perf-status critical';
            memoryStatusBadge.textContent = 'High';
        } else if (memValue > 50) {
            memoryStatusBadge.className = 'perf-status warning';
            memoryStatusBadge.textContent = 'Moderate';
        } else {
            memoryStatusBadge.className = 'perf-status healthy';
            memoryStatusBadge.textContent = 'Normal';
        }
    }

    // Failed Requests
    if (failedRequestsEl) {
        failedRequestsEl.textContent = performanceMetrics.failedRequests;
    }

    if (errorStatusBadge) {
        if (performanceMetrics.failedRequests > 5) {
            errorStatusBadge.className = 'perf-status critical';
            errorStatusBadge.textContent = 'Critical';
        } else if (performanceMetrics.failedRequests > 0) {
            errorStatusBadge.className = 'perf-status warning';
            errorStatusBadge.textContent = 'Warnings';
        } else {
            errorStatusBadge.className = 'perf-status healthy';
            errorStatusBadge.textContent = 'None';
        }
    }
}

// ===== AUTHENTICATION FUNCTIONS =====
function setupAuthListeners() {
    // Unified form submission
    const loginForm = document.getElementById('unified-login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleUnifiedLogin);
    }

    // Logout button
    logoutBtn.addEventListener('click', logout);

    // Initial field visibility
    toggleLoginFields();
}

function toggleLoginFields() {
    const role = document.getElementById('login-role').value;
    const usernameGroup = document.getElementById('username-group');
    const passwordGroup = document.getElementById('password-group');

    if (role === 'public') {
        usernameGroup.style.display = 'none';
        passwordGroup.style.display = 'none';
    } else {
        usernameGroup.style.display = 'block';
        passwordGroup.style.display = 'block';
    }
}

async function handleUnifiedLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const role = document.getElementById('login-role').value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        const data = await response.json();

        if (data.success) {
            authenticate(data.user, data.role);
        } else {
            showAuthError(data.message || 'wrong username or password');
        }
    } catch (error) {
        console.error('Login error:', error);
        showAuthError('Server error, please try again.');
    }
}

function authenticate(userIdentifier, role) {
    isAuthenticated = true;
    currentUserRole = role;
    sessionStorage.setItem('authUser', userIdentifier);
    sessionStorage.setItem('authRole', role);

    if (userIdentifier === 'HAJISUDI') {
        // Special case: Redirect HAJISUDI strictly to print tokens
        window.location.href = 'print_tokens.html';
        return;
    }

    if (role === 'public') {
        // Automatically redirect Public role to the public dashboard
        window.location.href = 'public_results.html';
        return;
    }

    authOverlay.style.display = 'none';
    resultsContent.classList.add('authenticated');
    console.log(`Authenticated as: ${userIdentifier} (${role})`);

    // Apply role permissions
    applyRolePermissions(role);

    // Initialize the page after successful login
    initializeResultsPage();
}

function logout() {
    isAuthenticated = false;
    currentUserRole = null;
    sessionStorage.removeItem('authUser');
    sessionStorage.removeItem('authRole');
    authOverlay.style.display = 'flex';
    resultsContent.classList.remove('authenticated');

    // Clear form
    const loginForm = document.getElementById('unified-login-form');
    if (loginForm) {
        loginForm.reset();
        // Reset visibility
        toggleLoginFields();
    }

    hideAuthError();

    // Stop auto-refresh on logout
    stopAutoRefresh();
    autoRefresh = false;
    toggleAutoBtn.textContent = 'Paused';
    setAdminSidebarOpen(false);

    // Clear vote rate tracking
    if (vpsUpdateInterval) {
        clearInterval(vpsUpdateInterval);
        vpsUpdateInterval = null;
    }
    voteHistory = [];
    lastTotalVotes = 0;

    // Clear performance tracking
    if (perfUpdateInterval) {
        clearInterval(perfUpdateInterval);
        perfUpdateInterval = null;
    }
    if (heartbeatIntervalId) {
        clearInterval(heartbeatIntervalId);
        heartbeatIntervalId = null;
    }
    if (connectedDevicesIntervalId) {
        clearInterval(connectedDevicesIntervalId);
        connectedDevicesIntervalId = null;
    }
    performanceMetrics = {
        apiResponseTimes: [],
        failedRequests: 0,
        lastSyncTime: null,
        lastSyncSuccess: true,
        startTime: Date.now(),
        sessionStartTime: null
    };
}

function showAuthError(message) {
    const errorEl = document.getElementById('auth-error');
    errorEl.textContent = message;
    errorEl.classList.add('show');
}

function hideAuthError() {
    const errorEl = document.getElementById('auth-error');
    errorEl.classList.remove('show');
}

function checkAuthStatus() {
    const authUser = sessionStorage.getItem('authUser');
    const authRole = sessionStorage.getItem('authRole');
    if (authUser) {
        if (authUser === 'HAJISUDI') {
            // Already logged in as HAJISUDI, strictly redirect to print tokens
            window.location.href = 'print_tokens.html';
            return;
        }
        if (authRole === 'public') {
            // Already logged in as public, redirect
            window.location.href = 'public_results.html';
            return;
        }
        isAuthenticated = true;
        currentUserRole = authRole;
        authOverlay.style.display = 'none';
        resultsContent.classList.add('authenticated');
        // Apply role permissions on page load if authenticated
        applyRolePermissions(authRole);
    }
}

function applyRolePermissions(role) {
    const developerSidebarSection = document.getElementById('developer-sidebar-section');
    const statsContainer = document.getElementById('stats-container');
    const tokenStatsContainer = document.getElementById('token-stats-container');
    const tokensListSection = document.getElementById('tokens-list-section');
    const systemPerfSection = document.getElementById('system-performance-section');
    const tokensGrid = document.getElementById('tokens-grid');

        if (role === 'developer') {
            if (developerSidebarSection) developerSidebarSection.style.display = 'block';
            if (connectedDevicesSection) connectedDevicesSection.style.display = 'block';
            if (requestMetricsSection) requestMetricsSection.style.display = 'block';
        if (statsContainer) statsContainer.style.display = 'grid';
        if (tokenStatsContainer) tokenStatsContainer.style.display = 'grid';
        if (tokensListSection) tokensListSection.style.display = 'block';
        if (systemPerfSection) systemPerfSection.style.display = 'block';
        if (tokensGrid) tokensGrid.style.display = 'grid';
        } else if (role === 'teacher') {
            if (developerSidebarSection) developerSidebarSection.style.display = 'none';
            if (connectedDevicesSection) connectedDevicesSection.style.display = 'none';
            if (requestMetricsSection) requestMetricsSection.style.display = 'none';
        if (statsContainer) statsContainer.style.display = 'none';
        if (tokenStatsContainer) tokenStatsContainer.style.display = 'none';
        if (tokensListSection) tokensListSection.style.display = 'none';
        if (systemPerfSection) systemPerfSection.style.display = 'none';
        } else {
            if (developerSidebarSection) developerSidebarSection.style.display = 'none';
            if (connectedDevicesSection) connectedDevicesSection.style.display = 'none';
            if (requestMetricsSection) requestMetricsSection.style.display = 'none';
        if (statsContainer) statsContainer.style.display = 'none';
        if (tokenStatsContainer) tokenStatsContainer.style.display = 'none';
        if (tokensListSection) tokensListSection.style.display = 'none';
        if (systemPerfSection) systemPerfSection.style.display = 'none';
    }
}

function updateElectionUI(state = {}) {
    const isOpen = Boolean(state.isOpen);
    const declaration = (state.winnerDeclaration || '').trim();
    const closedAt = state.closedAt ? ` (Closed at: ${new Date(state.closedAt).toLocaleString()})` : '';

    if (electionStatusEl) {
        electionStatusEl.textContent = isOpen
            ? 'Election status: OPEN'
            : `Election status: CLOSED${closedAt}`;
        electionStatusEl.style.color = isOpen ? '#22c55e' : '#ef4444';
    }

    if (winnerDeclarationDisplay) {
        winnerDeclarationDisplay.textContent = declaration || 'No winner declaration yet.';
    }
}

function showElectionMessage(message, isError = false) {
    if (!electionAdminMessage) return;
    electionAdminMessage.textContent = message;
    electionAdminMessage.style.color = isError ? '#ef4444' : '#22c55e';
}

async function closeElection() {
    const adminKey = prompt('Enter admin key to close election:');
    if (!adminKey) return;

    try {
        const res = await fetch(`${API_BASE}/api/election/close`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adminKey })
        });
        const data = await res.json();

        if (!res.ok) {
            showElectionMessage(data.error || 'Failed to close election.', true);
            return;
        }

        updateElectionUI(data.state || {});
        showElectionMessage('Election temporarily closed. Contestants and results are preserved.');
        await refreshTimelineYears(true);
    } catch (error) {
        showElectionMessage('Failed to close election.', true);
    }
}

async function reopenElectionAndRefreshSystem() {
    const dangerConfirmed = confirm('This will permanently clear all current candidates and vote records. Continue?');
    if (!dangerConfirmed) return;

    const adminKey = prompt('Enter admin key for DANGER reset (new round):');
    if (!adminKey) return;

    try {
        const res = await fetch(`${API_BASE}/api/election/reopen-reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adminKey })
        });
        const data = await res.json();

        if (!res.ok) {
            showElectionMessage(data.error || 'Failed to run danger reset.', true);
            return;
        }

        updateElectionUI(data.state || {});
        if (winnerDeclarationInput) {
            winnerDeclarationInput.value = '';
        }
        showElectionMessage('Danger reset complete. New round started.');
        await fetchAndRender(true);
        if (currentUserRole === 'developer') {
            await fetchTokenStats();
        }
        await refreshTimelineYears(true);
    } catch (error) {
        showElectionMessage('Failed to run danger reset.', true);
    }
}

async function reopenElectionOnly() {
    const adminKey = prompt('Enter admin key to resume voting without reset:');
    if (!adminKey) return;

    try {
        const res = await fetch(`${API_BASE}/api/election/reopen`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adminKey })
        });
        const data = await res.json();

        if (!res.ok) {
            showElectionMessage(data.error || 'Failed to resume voting.', true);
            return;
        }

        updateElectionUI(data.state || {});
        showElectionMessage('Voting resumed. Existing data was preserved.');
        await fetchAndRender(true);
        if (currentUserRole === 'developer') {
            await fetchTokenStats();
        }
    } catch (error) {
        showElectionMessage('Failed to resume voting.', true);
    }
}

async function restoreLatestArchivedData() {
    const adminKey = prompt('Enter admin key to restore latest archived data:');
    if (!adminKey) return;

    try {
        const res = await fetch(`${API_BASE}/api/election/restore-latest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adminKey })
        });
        const data = await res.json();

        if (!res.ok) {
            showElectionMessage(data.error || 'Failed to restore archived data.', true);
            return;
        }

        updateElectionUI(data.state || {});
        const restoredCount = data.restored && data.restored.contestantsRestored ? data.restored.contestantsRestored : 0;
        const restoredYear = data.restored && data.restored.year ? data.restored.year : '';
        showElectionMessage(`Recovered ${restoredCount} candidate records from archive ${restoredYear}.`);
        await fetchAndRender(true);
        if (currentUserRole === 'developer') {
            await fetchTokenStats();
        }
        await refreshTimelineYears(true);
    } catch (error) {
        showElectionMessage('Failed to restore archived data.', true);
    }
}

async function saveWinnerDeclaration() {
    const declaration = winnerDeclarationInput ? winnerDeclarationInput.value.trim() : '';
    if (!declaration) {
        showElectionMessage('Please choose a pre-made declaration statement first.', true);
        return;
    }

    const adminKey = prompt('Enter admin key to save winner declaration:');
    if (!adminKey) return;

    try {
        const res = await fetch(`${API_BASE}/api/election/winner`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ adminKey, declaration })
        });
        const data = await res.json();

        if (!res.ok) {
            showElectionMessage(data.error || 'Failed to save winner declaration.', true);
            return;
        }

        updateElectionUI(data.state || {});
        showElectionMessage('Winner declaration saved.');
    } catch (error) {
        showElectionMessage('Failed to save winner declaration.', true);
    }
}

// Start
document.addEventListener('DOMContentLoaded', () => {
    // Check if already authenticated
    checkAuthStatus();

    if (!isAuthenticated) {
        // Show auth modal
        setupAuthListeners();
        return;
    }

    // Otherwise, initialize results page
    initializeResultsPage();
});

function initializeResultsPage() {
    performanceMetrics.sessionStartTime = Date.now();

    initTheme();
    initializeAdminSidebar();
    initializeLeadershipTimeline();
    attachControls();
    fetchAndRender();
    startAutoRefresh();
    startClientHeartbeat();

    if (currentUserRole === 'developer') {
        fetchConnectedDevices();
        connectedDevicesIntervalId = setInterval(fetchConnectedDevices, 8000);
    }

    // Start vote rate tracking updates
    vpsUpdateInterval = setInterval(updateVoteRateDisplay, 1000); // Update every second

    // Start performance updates
    perfUpdateInterval = setInterval(updatePerformanceDisplay, 1000); // Update every second

    // keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && document.body.classList.contains('sidebar-open')) {
            setAdminSidebarOpen(false);
            return;
        }
        if (e.key === ' ') { // space toggles auto
            e.preventDefault();
            toggleAuto();
        }
        if (e.key.toLowerCase() === 'f') {
            toggleFullscreen();
        }
        if (e.key.toLowerCase() === 't') {
            toggleTheme();
        }
    });
}

function attachControls() {
    toggleAutoBtn.addEventListener('click', () => {
        toggleAuto();
        setAdminSidebarOpen(false);
        showToast(autoRefresh ? 'Auto-refresh Resumed' : 'Auto-refresh Paused', 'info');
    });

    refreshBtn.addEventListener('click', () => {
        setAdminSidebarOpen(false);
        refreshBtn.classList.add('refresh-spin');
        fetchAndRender(true).then(() => {
            setTimeout(() => refreshBtn.classList.remove('refresh-spin'), 1000);
            showToast('Data refreshed successfully', 'success');
        });
    });

    downloadCsvBtn.addEventListener('click', () => {
        setAdminSidebarOpen(false);
        downloadCSV();
        showToast('CSV Export started', 'success');
    });

    toggleThemeBtn.addEventListener('click', () => {
        setAdminSidebarOpen(false);
        toggleTheme();
        showToast(`Switched to ${currentTheme} theme`, 'info');
    });

    fullscreenBtn.addEventListener('click', () => {
        setAdminSidebarOpen(false);
        toggleFullscreen();
    });

    // Attach logout listener here as well to ensure it's always active when authenticated
    if (logoutBtn) {
        // Remove existing listener to avoid duplicates if possible, or just add (browsers handle duplicates well if same function)
        logoutBtn.removeEventListener('click', logout);
        logoutBtn.addEventListener('click', logout);
    }

    if (closeElectionBtn) {
        closeElectionBtn.addEventListener('click', closeElection);
    }
    if (reopenElectionBtn) {
        reopenElectionBtn.addEventListener('click', reopenElectionAndRefreshSystem);
    }
    if (adminKillSwitchBtn) {
        adminKillSwitchBtn.addEventListener('click', () => {
            setAdminSidebarOpen(false);
            reopenElectionOnly();
        });
    }
    if (restoreLatestBtn) {
        restoreLatestBtn.addEventListener('click', () => {
            setAdminSidebarOpen(false);
            restoreLatestArchivedData();
        });
    }
    if (saveWinnerBtn) {
        saveWinnerBtn.addEventListener('click', saveWinnerDeclaration);
    }
}

function startAutoRefresh() {
    stopAutoRefresh();
    if (autoRefresh) {
        timerId = setInterval(fetchAndRender, refreshInterval);
        toggleAutoBtn.textContent = 'Pause';
    } else {
        toggleAutoBtn.textContent = 'Resume';
    }
}

function stopAutoRefresh() {
    if (timerId) {
        clearInterval(timerId);
        timerId = null;
    }
}

function startClientHeartbeat() {
    stopClientHeartbeat();
    sendHeartbeat();
    heartbeatIntervalId = setInterval(sendHeartbeat, 25000);
}

function stopClientHeartbeat() {
    if (heartbeatIntervalId) {
        clearInterval(heartbeatIntervalId);
        heartbeatIntervalId = null;
    }
}

function toggleAuto() {
    autoRefresh = !autoRefresh;
    startAutoRefresh();
}

async function sendHeartbeat() {
    if (!isAuthenticated) return;
    const user = sessionStorage.getItem('authUser') || 'Anonymous';
    const role = currentUserRole || sessionStorage.getItem('authRole') || 'unknown';
    try {
        await fetch(`${API_BASE}/api/heartbeat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user,
                role,
                path: window.location.pathname
            })
        });
    } catch (err) {
        // Keep silent to avoid noisy UI while still allowing best-effort tracking.
    }
}

function formatAgo(seconds) {
    if (seconds < 60) return `${seconds}s ago`;
    const mins = Math.floor(seconds / 60);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    return `${hrs}h ${mins % 60}m ago`;
}

function renderConnectedDevices(payload) {
    if (!connectedDevicesBody) return;

    const summary = payload && payload.summary ? payload.summary : { total: 0, online: 0, idle: 0, offline: 0 };
    const devices = payload && Array.isArray(payload.devices) ? payload.devices : [];

    if (devicesTotalEl) devicesTotalEl.textContent = summary.total || 0;
    if (devicesOnlineEl) devicesOnlineEl.textContent = summary.online || 0;
    if (devicesIdleEl) devicesIdleEl.textContent = summary.idle || 0;
    if (devicesOfflineEl) devicesOfflineEl.textContent = summary.offline || 0;

    if (devices.length === 0) {
        connectedDevicesBody.innerHTML = '<tr><td colspan="7">No connected devices detected yet.</td></tr>';
        return;
    }

    connectedDevicesBody.innerHTML = devices.map((device) => {
        const status = (device.status || 'offline').toLowerCase();
        const statusColor = status === 'online' ? '#22c55e' : (status === 'idle' ? '#f59e0b' : '#ef4444');
        return `
            <tr>
                <td>${device.ip || '-'}</td>
                <td>${device.username || 'Anonymous'}</td>
                <td>${device.role || 'unknown'}</td>
                <td><span style="color:${statusColor};font-weight:700;text-transform:uppercase;">${status}</span></td>
                <td>${formatAgo(Number(device.ageSeconds || 0))}</td>
                <td>${Number(device.requestCount || 0)}</td>
                <td>${device.lastPath || '-'}</td>
            </tr>
        `;
    }).join('');
}

function renderRequestMetrics(payload) {
    if (!requestMetricsBody) return;

    const requests = payload && Array.isArray(payload.requests) ? payload.requests : [];
    const topRequest = requests.length ? Number(requests[0].count || 0) : 0;
    const topErrors = requests.reduce((maxValue, item) => Math.max(maxValue, Number(item.errors || 0)), 0);

    if (metricsTotalIpsEl) metricsTotalIpsEl.textContent = payload && payload.totalIps ? payload.totalIps : 0;
    if (metricsTopCountEl) metricsTopCountEl.textContent = topRequest;
    if (metricsTopErrorsEl) metricsTopErrorsEl.textContent = topErrors;

    if (requests.length === 0) {
        requestMetricsBody.innerHTML = '<tr><td colspan="7">No request metrics collected yet.</td></tr>';
        return;
    }

    requestMetricsBody.innerHTML = requests.slice(0, 10).map((item) => `
        <tr>
            <td>${item.ip || '-'}</td>
            <td>${Number(item.count || 0)}</td>
            <td>${Number(item.apiCount || 0)}</td>
            <td>${Number(item.errors || 0)}</td>
            <td>${Number(item.lastStatus || 0)}</td>
            <td>${item.lastPath || '-'}</td>
            <td>${item.lastSeen ? new Date(item.lastSeen).toLocaleTimeString() : '-'}</td>
        </tr>
    `).join('');
}

async function fetchConnectedDevices() {
    if (currentUserRole !== 'developer') return;
    try {
        const headers = {
            'X-Auth-Role': 'developer'
        };
        const [devicesRes, metricsRes] = await Promise.all([
            fetch(`${API_BASE}/api/connected-devices`, { headers }),
            fetch(`${API_BASE}/api/request-metrics`, { headers })
        ]);
        const [devicesData, metricsData] = await Promise.all([
            devicesRes.json(),
            metricsRes.json()
        ]);

        if (devicesRes.ok) {
            renderConnectedDevices(devicesData);
        }
        if (metricsRes.ok) {
            renderRequestMetrics(metricsData);
        }
    } catch (err) {
        if (connectedDevicesBody) {
            connectedDevicesBody.innerHTML = '<tr><td colspan="7">Failed to load connected devices.</td></tr>';
        }
        if (requestMetricsBody) {
            requestMetricsBody.innerHTML = '<tr><td colspan="7">Failed to load request metrics.</td></tr>';
        }
    }
}

async function fetchAndRender(animate = false) {
    try {
        const apiStartTime = Date.now();
        const res = await fetch(`${API_BASE}/api/results`);
        const data = await res.json();

        // Track API performance
        const responseTime = trackApiCall(apiStartTime);
        performanceMetrics.lastSyncTime = Date.now();
        performanceMetrics.lastSyncSuccess = true;

        // Update server status
        if (serverStatusIndicator) {
            serverStatusIndicator.className = 'uptime-indicator online';
        }
        if (serverStatusEl) {
            serverStatusEl.textContent = 'Online';
        }
        if (serverStatusBadge) {
            serverStatusBadge.className = 'perf-status healthy';
            serverStatusBadge.textContent = 'Healthy';
        }

        renderResults(data, animate);
        updateElectionUI(data.election || {});
        if (winnerDeclarationInput && document.activeElement !== winnerDeclarationInput) {
            winnerDeclarationInput.value = (data.election?.winnerDeclaration || '').trim();
        }

        // Track vote changes for rate calculation
        const totalVotes = (data.president?.totalVotes || 0) + (data.vice_president?.totalVotes || 0);
        if (totalVotes > lastTotalVotes) {
            const voteDiff = totalVotes - lastTotalVotes;
            // Add timestamps for each new vote
            const now = Date.now();
            for (let i = 0; i < voteDiff; i++) {
                voteHistory.push(now);
            }
            lastTotalVotes = totalVotes;
        }

        // Fetch and update token stats for developers only
        if (currentUserRole === 'developer') {
            fetchTokenStats();
        }

    } catch (err) {
        console.error('Failed to fetch results', err);
        performanceMetrics.failedRequests++;
        performanceMetrics.lastSyncSuccess = false;

        // Update server status on error
        if (serverStatusIndicator) {
            serverStatusIndicator.className = 'uptime-indicator offline';
        }
        if (serverStatusEl) {
            serverStatusEl.textContent = 'Offline';
        }
        if (serverStatusBadge) {
            serverStatusBadge.className = 'perf-status critical';
            serverStatusBadge.textContent = 'Error';
        }
    }
}

async function fetchTokenStats() {
    try {
        const res = await fetch(`${API_BASE}/api/tokens`);
        const data = await res.json();

        if (data) {
            // Update stats
            if (totalTokensEl) totalTokensEl.textContent = data.total;
            if (spentTokensEl) spentTokensEl.textContent = data.spent;
            if (remainingTokensEl) remainingTokensEl.textContent = data.remaining;

            // Render token grid
            renderTokenGrid(data.tokens);
        }
    } catch (err) {
        console.error('Failed to fetch token stats', err);
    }
}

function renderTokenGrid(tokens) {
    const grid = document.getElementById('tokens-grid');
    if (!grid) return;

    grid.innerHTML = '';

    if (!tokens || tokens.length === 0) {
        grid.innerHTML = '<div style="text-align: center; color: var(--text-secondary); padding: 20px; grid-column: 1 / -1;">No tokens found.</div>';
        return;
    }

    tokens.forEach(tokenObj => {
        const el = document.createElement('div');
        el.className = `token-item ${tokenObj.isSpent ? 'token-used' : 'token-active'}`;
        el.textContent = tokenObj.token;
        el.title = tokenObj.isSpent ? `Used (Voted for: ${tokenObj.votedPositions.join(', ')})` : 'Active';
        grid.appendChild(el);
    });
}

function updateVoteRateDisplay() {
    const now = Date.now();
    const oneMinuteAgo = now - (60 * 1000); // 60 seconds
    const tenSecondsAgo = now - (10 * 1000); // 10 seconds

    // Remove old votes from history (older than 1 minute)
    voteHistory = voteHistory.filter(timestamp => timestamp > oneMinuteAgo);

    // Calculate current rate (votes in last 10 seconds)
    const recentVotes = voteHistory.filter(timestamp => timestamp > tenSecondsAgo);
    const currentVps = recentVotes.length > 0 ? (recentVotes.length / 10).toFixed(2) : '0.0';

    // Calculate peak and average rates
    let peakRate = 0;
    let totalRate = 0;

    if (voteHistory.length > 0) {
        // Split into 1-second intervals and find peak
        const intervals = {};
        voteHistory.forEach(timestamp => {
            const second = Math.floor((timestamp - oneMinuteAgo) / 1000);
            intervals[second] = (intervals[second] || 0) + 1;
        });

        peakRate = Math.max(...Object.values(intervals));
        totalRate = voteHistory.length / Math.min(60, Math.max(1, (now - Math.min(...voteHistory)) / 1000));
    }

    // Update display
    if (vpsCounter) vpsCounter.textContent = currentVps;
    if (peakVps) peakVps.textContent = peakRate.toFixed(1);
    if (avgVps) avgVps.textContent = totalRate.toFixed(2);
}

function renderResults(data, animate = false) {
    resultsContainer.innerHTML = '';

    const presidentData = data.president || { candidates: [], totalVotes: 0 };
    const vicePresidentData = data.vice_president || { candidates: [], totalVotes: 0 };

    // Update data for CSV Export
    lastCandidates = [...presidentData.candidates, ...vicePresidentData.candidates];
    lastTotalVotes = presidentData.totalVotes + vicePresidentData.totalVotes;

    // President Results
    const presSection = document.createElement('div');
    presSection.innerHTML = '<h3 style="margin-top: 20px; margin-bottom: 15px; color: var(--text-primary); border-bottom: 2px solid var(--border-color); padding-bottom: 10px;">President Results</h3>';
    renderCandidateResults(presSection, presidentData.candidates, presidentData.totalVotes, animate);
    resultsContainer.appendChild(presSection);

    // Vice President Results
    const viceSection = document.createElement('div');
    viceSection.innerHTML = '<h3 style="margin-top: 30px; margin-bottom: 15px; color: var(--text-primary); border-bottom: 2px solid var(--border-color); padding-bottom: 10px;">Vice President Results</h3>';
    renderCandidateResults(viceSection, vicePresidentData.candidates, vicePresidentData.totalVotes, animate);
    resultsContainer.appendChild(viceSection);

    // Update total display
    const totalVotes = presidentData.totalVotes + vicePresidentData.totalVotes;
    totalVotesDisplay.textContent = `Total Votes Cast: ${totalVotes}`;
}

function renderCandidateResults(container, candidates, totalVotes, animate = false) {
    if (!candidates || candidates.length === 0) {
        const p = document.createElement('p');
        p.style.textAlign = 'center';
        p.style.color = 'rgba(255,255,255,0.6)';
        p.textContent = 'No candidates registered yet.';
        container.appendChild(p);
        return;
    }

    candidates.forEach((candidate, idx) => {
        const percent = totalVotes > 0 ? ((candidate.votes / totalVotes) * 100).toFixed(1) : 0;
        const rank = idx + 1;
        const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `${rank}.`;

        const item = document.createElement('div');
        item.className = 'result-item';
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.justifyContent = 'space-between';

        const left = document.createElement('div');
        left.style.display = 'flex';
        left.style.alignItems = 'center';
        left.style.gap = '18px';

        const rankDiv = document.createElement('div');
        rankDiv.className = 'result-rank';
        rankDiv.style.minWidth = '60px';
        rankDiv.style.fontSize = '1.6rem';
        rankDiv.textContent = medal;

        const img = document.createElement('img');
        img.src = candidate.image || '';
        img.alt = candidate.name;
        img.style.width = '72px';
        img.style.height = '72px';
        img.style.borderRadius = '50%';
        img.style.objectFit = 'cover';
        img.onerror = function () { this.style.display = 'none'; };

        const info = document.createElement('div');
        const name = document.createElement('div');
        name.className = 'result-name';
        name.textContent = candidate.name;

        const position = document.createElement('div');
        position.className = 'result-position';
        position.style.color = 'rgba(255,255,255,0.7)';
        position.textContent = candidate.position;

        info.appendChild(name);
        info.appendChild(position);

        left.appendChild(rankDiv);
        left.appendChild(img);
        left.appendChild(info);

        const right = document.createElement('div');
        right.style.textAlign = 'right';

        const votes = document.createElement('div');
        votes.className = 'result-votes';
        votes.textContent = candidate.votes;

        const pct = document.createElement('div');
        pct.className = 'result-percentage';
        pct.textContent = percent + '%';

        // progress bar
        const barContainer = document.createElement('div');
        barContainer.className = 'result-bar-container';
        barContainer.style.marginTop = '10px';
        barContainer.style.width = '260px';
        barContainer.style.marginLeft = 'auto';

        const bar = document.createElement('div');
        bar.className = 'result-bar';
        bar.style.width = percent + '%';
        bar.style.height = '12px';

        barContainer.appendChild(bar);

        right.appendChild(votes);
        right.appendChild(pct);
        right.appendChild(barContainer);

        item.appendChild(left);
        item.appendChild(right);

        container.appendChild(item);
    });

    // Store last data for CSV - REMOVED (Moved to renderResults)
}

function toggleFullscreen() {
    const el = document.documentElement;
    if (!document.fullscreenElement) {
        if (el.requestFullscreen) el.requestFullscreen();
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
    }
}

function initTheme() {
    const saved = localStorage.getItem('resultsTheme') || 'dark';
    currentTheme = saved;
    applyTheme(currentTheme);
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('resultsTheme', currentTheme);
    applyTheme(currentTheme);
}

function applyTheme(theme) {
    document.body.classList.remove('dark-theme', 'light-theme');
    document.body.classList.add(`${theme}-theme`);

    // Update button emoji
    toggleThemeBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function downloadCSV() {
    if (!lastCandidates || lastCandidates.length === 0) {
        alert('No results to download yet.');
        return;
    }

    // Create CSV header
    const headers = ['Rank', 'Candidate Name', 'Position', 'Votes', 'Percentage'];
    const rows = [];
    rows.push(headers.join(','));

    // Add data rows
    lastCandidates.forEach((candidate, idx) => {
        const rank = idx + 1;
        const percentage = lastTotalVotes > 0 ? ((candidate.votes / lastTotalVotes) * 100).toFixed(2) : 0;
        const row = [
            rank,
            `"${candidate.name.replace(/"/g, '""')}"`, // Escape quotes
            `"${candidate.position.replace(/"/g, '""')}"`,
            candidate.votes,
            percentage
        ];
        rows.push(row.join(','));
    });

    // Add total votes row
    rows.push('');
    rows.push(`Total Votes,${lastTotalVotes}`);

    // Create blob and download
    const csvContent = '\uFEFF' + rows.join('\n'); // Add BOM for Excel
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    const now = new Date();
    const timestamp = now.toISOString().split('T')[0]; // YYYY-MM-DD
    link.setAttribute('href', url);
    link.setAttribute('download', `feza-vote-results-${timestamp}.csv`);
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Toast Notification
function showToast(message, type = 'success', duration = 3000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Icon based on type
    let icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'info') icon = 'ℹ️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;

    container.appendChild(toast);

    // Auto remove
    setTimeout(() => {
        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentElement) toast.parentElement.removeChild(toast);
        }, 300);
    }, duration);
}

// Stop auto-refresh when user leaves page
window.addEventListener('blur', () => {
    if (autoRefresh) stopAutoRefresh();
});

window.addEventListener('focus', () => {
    if (autoRefresh) startAutoRefresh();
});
