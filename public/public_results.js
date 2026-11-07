const API_URL = window.location.origin + '/api/results';
const TOKENS_URL = window.location.origin + '/api/tokens';

// Chart.js instance
let voteChart;
let voteHistory = {
    labels: [],
    presidentData: [],
    viceData: []
};

// Max data points on chart to keep it readable
const MAX_DATA_POINTS = 30;

document.addEventListener('DOMContentLoaded', () => {
    initChart();
    fetchData();
    setInterval(fetchData, 5000); // Poll every 5 seconds

    // Add logout listener
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            sessionStorage.removeItem('authUser');
            sessionStorage.removeItem('authRole');
            window.location.href = 'results.html';
        });
    }
});

function initChart() {
    const ctx = document.getElementById('voteChart').getContext('2d');

    // Gradient for President line (Feza Orange)
    const gradientPres = ctx.createLinearGradient(0, 0, 0, 400);
    gradientPres.addColorStop(0, 'rgba(255, 107, 0, 0.5)');
    gradientPres.addColorStop(1, 'rgba(255, 107, 0, 0)');

    // Gradient for Vice line (Amber/Orange-Yellow)
    const gradientVice = ctx.createLinearGradient(0, 0, 0, 400);
    gradientVice.addColorStop(0, 'rgba(251, 191, 36, 0.5)');
    gradientVice.addColorStop(1, 'rgba(251, 191, 36, 0)');

    voteChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'President Votes',
                    data: [],
                    borderColor: '#FF6B00',
                    backgroundColor: gradientPres,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0
                },
                {
                    label: 'VP Votes',
                    data: [],
                    borderColor: '#fbbf24',
                    backgroundColor: gradientVice,
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { size: 14 } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b' }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#64748b' },
                    beginAtZero: true
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

async function fetchData() {
    try {
        const [resultsRes, tokensRes] = await Promise.all([
            fetch(API_URL),
            fetch(TOKENS_URL)
        ]);

        const results = await resultsRes.json();
        const tokens = await tokensRes.json();

        updateDashboard(results, tokens);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateDashboard(results, tokens) {
    if (!results || !tokens) return;

    // 1. Update Stats
    const totalPresVotes = results.president.totalVotes;
    const totalViceVotes = results.vice_president.totalVotes;
    const totalVotes = totalPresVotes + totalViceVotes; // Simplification, strictly speaking max(pres, vice) or unique tokens is better turnout metric

    // Better turnout metric: spending tokens
    const spentTokens = tokens.spent;
    const totalTokens = tokens.total;
    const turnout = totalTokens > 0 ? ((spentTokens / totalTokens) * 100).toFixed(1) : 0;

    document.getElementById('totalTokenVotes').textContent = totalVotes;
    document.getElementById('turnout').textContent = `${turnout}%`;

    const electionStatusEl = document.getElementById('public-election-status');
    const winnerDeclarationEl = document.getElementById('public-winner-declaration');
    const election = results.election || {};
    const isOpen = Boolean(election.isOpen);
    if (electionStatusEl) {
        electionStatusEl.textContent = isOpen ? 'OPEN' : 'CLOSED';
        electionStatusEl.style.color = isOpen ? '#22c55e' : '#ef4444';
    }
    if (winnerDeclarationEl) {
        winnerDeclarationEl.textContent = (election.winnerDeclaration || '').trim() || 'No winner declaration yet.';
    }

    // 2. Update Chart Info
    const now = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    // Add new data point
    if (voteHistory.labels.length === 0 || voteHistory.labels[voteHistory.labels.length - 1] !== now) {
        // Only add point if time changed (every sec roughly) or on data change? 
        // Let's just push every update to show "live" feel
        voteHistory.labels.push(now);
        voteHistory.presidentData.push(totalPresVotes);
        voteHistory.viceData.push(totalViceVotes);

        // Shift if too many
        if (voteHistory.labels.length > MAX_DATA_POINTS) {
            voteHistory.labels.shift();
            voteHistory.presidentData.shift();
            voteHistory.viceData.shift();
        }

        // Update Chart
        voteChart.data.labels = voteHistory.labels;
        voteChart.data.datasets[0].data = voteHistory.presidentData;
        voteChart.data.datasets[1].data = voteHistory.viceData;
        voteChart.update('none'); // 'none' mode for performance
    }

    // 3. Update Leaderboard
    updateLeaderboard(results);
}

function updateLeaderboard(results) {
    const list = document.getElementById('leaderboard');
    if (!list) return;

    // Color Palettes
    const presidentColors = ['#FF6B00', '#FF8533', '#FFA366', '#FFC299'];
    const viceColors = ['#FBBF24', '#FCD34D', '#FDE68A', '#FEF3C7'];

    const presidents = results.president.candidates.slice(0, 4);
    const vices = results.vice_president.candidates.slice(0, 4);

    let html = '';

    // President Header
    html += `<div style="color: #8b5cf6; font-size: 1vw; font-weight: 600; margin-top: 10px;">PRESIDENT</div>`;
    presidents.forEach((c, idx) => {
        const color = presidentColors[idx % presidentColors.length];
        html += createCandidateCard(c, 'president', results.president.totalVotes, color);
    });

    // Vice Header
    html += `<div style="color: #ec4899; font-size: 1vw; font-weight: 600; margin-top: 20px;">VICE PRESIDENT</div>`;
    vices.forEach((c, idx) => {
        const color = viceColors[idx % viceColors.length];
        html += createCandidateCard(c, 'vice', results.vice_president.totalVotes, color);
    });

    list.innerHTML = html;
}

function createCandidateCard(candidate, type, totalVotes, color) {
    const percent = totalVotes > 0 ? ((candidate.votes / totalVotes) * 100).toFixed(1) : 0;
    const defaultImg = 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect fill=\'%23e2e8f0\' width=\'200\' height=\'200\'/%3E%3Ctext fill=\'%2394a3b8\' font-family=\'sans-serif\' font-size=\'14\' dy=\'10.5\' font-weight=\'bold\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\'%3ENo Image%3C/text%3E%3C/svg%3E';

    return `
    <div class="candidate-card ${type}" style="border-left-color: ${color}">
        <img src="${candidate.image || defaultImg}" class="candidate-img" onerror="this.src='${defaultImg}'">
        <div class="candidate-info">
            <div class="candidate-name">${candidate.name}</div>
            <div class="candidate-pos">${type.toUpperCase()}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${percent}%; background: ${color}"></div>
            </div>
        </div>
        <div class="candidate-votes" style="color: ${color}">${candidate.votes}</div>
    </div>
    `;
}
