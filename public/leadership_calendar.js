const API_BASE = window.location.origin;
const DEFAULT_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Crect fill='%23e2e8f0' width='160' height='160'/%3E%3Ctext fill='%2394a3b8' font-family='sans-serif' font-size='14' dy='10.5' font-weight='bold' x='50%25' y='50%25' text-anchor='middle'%3ENo Image%3C/text%3E%3C/svg%3E";
const MIN_CALENDAR_YEAR = 2026;

let entries = [];
let selectedYear = '';
const timelineByYear = new Map();
let currentContestants = [];

const historyGrid = document.getElementById('history-grid');
const yearCalendar = document.getElementById('year-calendar');
const contestantsSection = document.getElementById('contestants-section');
const contestantsGrid = document.getElementById('contestants-grid');
const contestantsTitle = document.querySelector('.contestants-title');
const currentContestantsSection = document.getElementById('current-contestants-section');
const currentContestantsGrid = document.getElementById('current-contestants-grid');

const menuToggle = document.getElementById('calendar-menu-toggle');
const sidebar = document.getElementById('calendar-sidebar');
const sidebarOverlay = document.getElementById('calendar-sidebar-overlay');
const sidebarClose = document.getElementById('calendar-sidebar-close');
const logoutBtn = document.getElementById('calendar-logout');

window.fallbackImage = function fallbackImage(img) {
    if (!img) return;
    img.onerror = null;
    img.src = DEFAULT_IMAGE;
};

document.addEventListener('DOMContentLoaded', () => {
    if (!hasAdminSession()) {
        window.location.href = 'results.html';
        return;
    }
    setupSidebar();
    loadHistory();
});

function hasAdminSession() {
    const authUser = sessionStorage.getItem('authUser');
    const authRole = sessionStorage.getItem('authRole');
    return Boolean(authUser) && authRole !== 'public';
}

function setupSidebar() {
    if (!menuToggle || !sidebar || !sidebarOverlay) return;

    menuToggle.addEventListener('click', () => setSidebarOpen(true));
    sidebarOverlay.addEventListener('click', () => setSidebarOpen(false));
    if (sidebarClose) {
        sidebarClose.addEventListener('click', () => setSidebarOpen(false));
    }
    sidebar.querySelectorAll('a').forEach((link) => {
        link.addEventListener('click', () => setSidebarOpen(false));
    });
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            sessionStorage.removeItem('authUser');
            sessionStorage.removeItem('authRole');
            window.location.href = 'results.html';
        });
    }
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            setSidebarOpen(false);
        }
    });
}

function setSidebarOpen(open) {
    sidebar.classList.toggle('open', open);
    sidebarOverlay.classList.toggle('open', open);
    sidebar.setAttribute('aria-hidden', open ? 'false' : 'true');
    document.body.style.overflow = open ? 'hidden' : '';
}

function formatDate(value) {
    if (!value) return 'N/A';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString();
}

function sanitize(value) {
    if (value === undefined || value === null) return '';
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function normalizeEntry(snapshot) {
    const year = Number(snapshot.year);
    const leaders = snapshot.leaders || {};
    const president = leaders.president || null;
    const vice = leaders.vice_president || null;
    const totals = snapshot.totals || {};
    const election = snapshot.election || {};

    return {
        year,
        archivedAt: snapshot.archivedAt,
        winnerDeclaration: election.winnerDeclaration || '',
        isOpen: Boolean(election.isOpen),
        totalVotes: Number(totals.presidentVotes || 0) + Number(totals.vicePresidentVotes || 0),
        totalContestants: Number(totals.contestants || 0),
        presidentName: president ? president.name : 'N/A',
        presidentPhoto: president ? president.image : DEFAULT_IMAGE,
        presidentVotes: president ? Number(president.votes || 0) : 0,
        vicePresidentName: vice ? vice.name : 'N/A',
        vicePresidentPhoto: vice ? vice.image : DEFAULT_IMAGE,
        vicePresidentVotes: vice ? Number(vice.votes || 0) : 0,
        contestants: Array.isArray(snapshot.contestants) ? snapshot.contestants : []
    };
}

function normalizeLegacyEntry(entry) {
    const year = Number(entry.year);
    const totalVotes = Number(entry.totalVotes || 0);
    const votesWon = Number(entry.votesWon || 0);
    const percentage = totalVotes > 0 ? ((votesWon / totalVotes) * 100) : Number(entry.percentage || 0);

    return {
        year,
        archivedAt: entry.archivedAt || null,
        winnerDeclaration: entry.winnerDeclaration || entry.slogan || '',
        isOpen: false,
        totalVotes,
        totalContestants: Number(entry.totalContestants || 0),
        presidentName: entry.presidentName || 'N/A',
        presidentPhoto: entry.presidentPhoto || DEFAULT_IMAGE,
        presidentVotes: votesWon || Number(entry.presidentVotes || 0),
        vicePresidentName: entry.vicePresidentName || 'N/A',
        vicePresidentPhoto: entry.vicePresidentPhoto || DEFAULT_IMAGE,
        vicePresidentVotes: Number(entry.vicePresidentVotes || 0),
        contestants: Array.isArray(entry.contestants) ? entry.contestants : [],
        percentage
    };
}

async function fetchJson(url) {
    const res = await fetch(url);
    let data = null;
    try {
        data = await res.json();
    } catch (error) {
        data = null;
    }
    return { ok: res.ok, status: res.status, data };
}

async function loadHistory() {
    try {
        const [yearsResp, currentCandidatesResp] = await Promise.all([
            fetchJson(`${API_BASE}/api/leadership-timeline/years`),
            fetchJson(`${API_BASE}/api/candidates`)
        ]);

        currentContestants = currentCandidatesResp.ok && Array.isArray(currentCandidatesResp.data)
            ? currentCandidatesResp.data
            : [];

        if (!yearsResp.ok) {
            const legacyResp = await fetchJson(`${API_BASE}/api/leadership-history`);
            if (!legacyResp.ok || !Array.isArray(legacyResp.data)) {
                throw new Error('Timeline endpoints unavailable');
            }

            entries = legacyResp.data
                .map(normalizeLegacyEntry)
                .filter((entry) => Number.isFinite(entry.year))
                .sort((a, b) => b.year - a.year);

            timelineByYear.clear();
            entries.forEach((entry) => timelineByYear.set(String(entry.year), entry));

            renderYearCalendar();
            renderHistory();
            renderContestants();
            renderCurrentContestants();
            return;
        }

        const yearsData = yearsResp.data || {};
        const years = Array.isArray(yearsData.years) ? yearsData.years : [];
        if (years.length === 0) {
            entries = [];
            timelineByYear.clear();
            renderYearCalendar();
            renderHistory();
            renderContestants();
            renderCurrentContestants();
            return;
        }

        const detailResults = await Promise.all(
            years.map(async (year) => {
                const resp = await fetchJson(`${API_BASE}/api/leadership-timeline/${year}`);
                if (!resp.ok || !resp.data) {
                    return null;
                }
                return normalizeEntry(resp.data);
            })
        );

        entries = detailResults
            .filter(Boolean)
            .sort((a, b) => b.year - a.year);

        timelineByYear.clear();
        entries.forEach((entry) => timelineByYear.set(String(entry.year), entry));

        renderYearCalendar();
        renderHistory();
        renderContestants();
        renderCurrentContestants();
    } catch (error) {
        historyGrid.innerHTML = '<p class="error-message">Failed to load leadership history.</p>';
        contestantsSection.style.display = 'none';
        if (currentContestantsSection) {
            currentContestantsSection.style.display = 'none';
        }
    }
}

function renderYearCalendar() {
    if (!yearCalendar) return;

    const currentYear = new Date().getFullYear();
    const years = [];
    for (let year = currentYear; year >= MIN_CALENDAR_YEAR; year -= 1) {
        years.push(String(year));
    }

    if (!selectedYear) {
        selectedYear = String(currentYear);
    }
    if (!years.includes(String(selectedYear))) {
        selectedYear = String(currentYear);
    }

    yearCalendar.innerHTML = '';

    years.forEach((year) => {
        const hasData = timelineByYear.has(year);
        const tile = document.createElement('button');
        tile.type = 'button';
        tile.className = `year-tile ${selectedYear === year ? 'active' : ''} ${hasData ? 'has-data' : 'no-data'}`;
        tile.innerHTML = `
            <span class="year-number">${year}</span>
            <span class="year-state">${hasData ? 'Archived' : 'No Data'}</span>
        `;
        tile.addEventListener('click', () => {
            selectedYear = year;
            renderYearCalendar();
            renderHistory();
            renderContestants();
        });
        yearCalendar.appendChild(tile);
    });
}

function renderHistory() {
    historyGrid.innerHTML = '';
    const filtered = entries.filter((entry) => String(entry.year) === String(selectedYear));

    if (filtered.length === 0) {
        historyGrid.innerHTML = `<p class="empty-message">No leadership records found for ${sanitize(selectedYear)}.</p>`;
        return;
    }

    filtered.forEach((entry) => {
        const declaration = entry.winnerDeclaration
            ? sanitize(entry.winnerDeclaration)
            : 'No winner declaration';

        const card = document.createElement('article');
        card.className = 'history-card';
        card.innerHTML = `
            <div class="history-header">
                <div class="history-year">${sanitize(entry.year)}</div>
                <div class="candidate-slogan">${declaration}</div>
            </div>
            <div class="history-team">
                <div class="history-person">
                    <img src="${sanitize(entry.presidentPhoto || DEFAULT_IMAGE)}" alt="${sanitize(entry.presidentName)}" onerror="fallbackImage(this)">
                    <div class="history-role">President</div>
                    <div class="history-name">${sanitize(entry.presidentName)}</div>
                </div>
                <div class="history-person">
                    <img src="${sanitize(entry.vicePresidentPhoto || DEFAULT_IMAGE)}" alt="${sanitize(entry.vicePresidentName)}" onerror="fallbackImage(this)">
                    <div class="history-role">Vice President</div>
                    <div class="history-name">${sanitize(entry.vicePresidentName)}</div>
                </div>
            </div>
            <div class="history-metrics">
                <span>President Votes: ${sanitize(entry.presidentVotes)}</span>
                <span>Vice Votes: ${sanitize(entry.vicePresidentVotes)}</span>
            </div>
            <div class="history-summary">
                Total Votes: ${sanitize(entry.totalVotes)} | Contestants: ${sanitize(entry.totalContestants)} | Archived: ${sanitize(formatDate(entry.archivedAt))}
            </div>
        `;
        historyGrid.appendChild(card);
    });
}

function renderContestants() {
    if (!contestantsSection || !contestantsGrid) return;

    const entry = timelineByYear.get(String(selectedYear));
    if (!entry) {
        contestantsSection.style.display = 'none';
        contestantsGrid.innerHTML = '';
        return;
    }

    contestantsSection.style.display = 'block';
    if (contestantsTitle) {
        contestantsTitle.textContent = `${entry.year} Contestants`;
    }

    contestantsGrid.innerHTML = '';
    const contestants = Array.isArray(entry.contestants) ? entry.contestants : [];
    if (!contestants.length) {
        contestantsGrid.innerHTML = `<p class="empty-message">No contestants found for ${sanitize(entry.year)}.</p>`;
        return;
    }

    contestants.forEach((candidate) => {
        const card = document.createElement('article');
        card.className = 'contestant-card';
        card.innerHTML = `
            <img src="${sanitize(candidate.image || DEFAULT_IMAGE)}" alt="${sanitize(candidate.name || 'Candidate')}" onerror="fallbackImage(this)">
            <div class="contestant-name">${sanitize(candidate.name || 'N/A')}</div>
            <div class="contestant-meta">Position: ${sanitize(candidate.position || 'N/A')}</div>
            <div class="contestant-meta">Votes: ${sanitize(candidate.votes || 0)}</div>
            <div class="contestant-meta">Student ID: ${sanitize(candidate.studentId || '-')}</div>
            <div class="contestant-meta">${candidate.slogan ? `"${sanitize(candidate.slogan)}"` : 'No slogan'}</div>
        `;
        contestantsGrid.appendChild(card);
    });
}

function renderCurrentContestants() {
    if (!currentContestantsSection || !currentContestantsGrid) return;
    currentContestantsSection.style.display = 'block';
    currentContestantsGrid.innerHTML = '';

    if (!Array.isArray(currentContestants) || currentContestants.length === 0) {
        currentContestantsGrid.innerHTML = '<p class="empty-message">No present contestants registered yet.</p>';
        return;
    }

    currentContestants.forEach((candidate) => {
        const card = document.createElement('article');
        card.className = 'contestant-card';
        card.innerHTML = `
            <img src="${sanitize(candidate.image || DEFAULT_IMAGE)}" alt="${sanitize(candidate.name || 'Candidate')}" onerror="fallbackImage(this)">
            <div class="contestant-name">${sanitize(candidate.name || 'N/A')}</div>
            <div class="contestant-meta">Position: ${sanitize(candidate.position || 'N/A')}</div>
            <div class="contestant-meta">Votes: ${sanitize(candidate.votes || 0)}</div>
            <div class="contestant-meta">${candidate.slogan ? `"${sanitize(candidate.slogan)}"` : 'No slogan'}</div>
        `;
        currentContestantsGrid.appendChild(card);
    });
}
