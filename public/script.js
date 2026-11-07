// API Base URL
const API_BASE = window.location.origin;

// State Management
let candidates = [];
let currentToken = '';
let isTokenValid = false;
let votedPositions = []; // Track which positions we've voted for: ['president'], ['vice_president'], or both
let isElectionOpen = true;
let votingSessionVersion = 0;
let candidatesRequestInFlight = null;
let tokenCheckInFlight = false;

// DOM Elements
const tokenInput = document.getElementById('voter-token');
const checkTokenBtn = document.getElementById('check-token-btn');
const voterStatus = document.getElementById('voter-status');
const electionStatusBanner = document.getElementById('election-status-banner');
const voteModal = document.getElementById('vote-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const loadingOverlay = document.getElementById('loading-overlay');

// Voting Sections
const presidentSection = document.getElementById('president-section');
const vicePresidentSection = document.getElementById('vice-president-section');
const completionSection = document.getElementById('completion-section');
const presidentCandidates = document.getElementById('president-candidates');
const vicePresidentCandidates = document.getElementById('vice-president-candidates');
const presStatus = document.getElementById('pres-status');
const viceStatus = document.getElementById('vice-status');
const newVoteBtn = document.getElementById('new-vote-btn');
const voteAgainBtn = document.getElementById('vote-again-btn');
const voteAgainDashboardBtn = document.getElementById('vote-again-dashboard-btn');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, checking DOM elements...');

    // Verify all DOM elements exist
    const requiredElements = {
        tokenInput, checkTokenBtn, voterStatus, voteModal, closeModalBtn, loadingOverlay,
        presidentSection, vicePresidentSection, completionSection,
        presidentCandidates, vicePresidentCandidates, presStatus, viceStatus, newVoteBtn, voteAgainBtn, voteAgainDashboardBtn
    };

    for (const [key, element] of Object.entries(requiredElements)) {
        if (!element) {
            console.error(`Missing DOM element: ${key}`);
        }
    }

    console.log('DOM elements verified, loading candidates...');
    loadElectionState();
    loadCandidates();
    setupEventListeners();

    // Auto-refresh candidates every 5 seconds to reduce server churn
    setInterval(loadCandidates, 5000);
    setInterval(loadElectionState, 5000);
});

// Event Listeners
function setupEventListeners() {
    checkTokenBtn.addEventListener('click', checkTokenStatus);
    tokenInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            checkTokenStatus();
        }
    });

    closeModalBtn.addEventListener('click', closeModal);
    voteModal.addEventListener('click', (e) => {
        if (e.target === voteModal) {
            closeModal();
        }
    });

    newVoteBtn.addEventListener('click', triggerVoteAgainKillSwitch);
    if (voteAgainBtn) {
        voteAgainBtn.addEventListener('click', triggerVoteAgainKillSwitch);
    }
    if (voteAgainDashboardBtn) {
        voteAgainDashboardBtn.addEventListener('click', triggerVoteAgainKillSwitch);
    }
}

// Load Candidates
async function loadCandidates(showLoadingIndicator = false) {
    if (candidatesRequestInFlight) {
        return candidatesRequestInFlight;
    }

    candidatesRequestInFlight = (async () => {
    try {
        if (showLoadingIndicator) {
            showLoading();
        }
        const response = await fetch(`${API_BASE}/api/candidates`);
        const newCandidates = await response.json();
        if (!response.ok) {
            throw new Error(newCandidates.error || 'Failed to load candidates');
        }

        // Only update if candidates changed
        const candidatesChanged = JSON.stringify(candidates) !== JSON.stringify(newCandidates);
        if (candidatesChanged) {
            candidates = newCandidates;
            renderCandidates();
        } else if (candidates.length === 0 && newCandidates.length > 0) {
            candidates = newCandidates;
            renderCandidates();
        }

        if (showLoadingIndicator) {
            hideLoading();
        }
    } catch (error) {
        console.error('Error loading candidates:', error);
        if (showLoadingIndicator) {
            showError('Failed to load candidates. Please refresh the page.');
            hideLoading();
        }
    } finally {
        candidatesRequestInFlight = null;
    }
    })();

    return candidatesRequestInFlight;
}

async function loadElectionState() {
    try {
        const response = await fetch(`${API_BASE}/api/election-state`);
        const data = await response.json();

        isElectionOpen = Boolean(data.isOpen);
        updateElectionStateUI(data);
        updateVoteButtons();
    } catch (error) {
        console.error('Error loading election state:', error);
    }
}

function updateElectionStateUI(data) {
    if (!electionStatusBanner) {
        return;
    }

    if (data.isOpen) {
        electionStatusBanner.textContent = 'Election is OPEN. Voting is enabled.';
        electionStatusBanner.className = 'voter-status success show';
        checkTokenBtn.disabled = false;
    } else {
        electionStatusBanner.textContent = 'Election is CLOSED. Voting is disabled by admin.';
        electionStatusBanner.className = 'voter-status warning show';
        checkTokenBtn.disabled = true;
        presidentSection.style.display = 'none';
        vicePresidentSection.style.display = 'none';
    }
}

// Render Candidates by Position
function renderCandidates() {
    const presidents = candidates.filter(c => c.position === 'president');
    const vicePresidents = candidates.filter(c => c.position === 'vice_president');

    presidentCandidates.innerHTML = '';
    vicePresidentCandidates.innerHTML = '';

    if (presidents.length === 0) {
        presidentCandidates.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">No president candidates registered yet.</p>';
    }

    if (vicePresidents.length === 0) {
        vicePresidentCandidates.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--text-secondary);">No vice president candidates registered yet.</p>';
    }

    presidents.forEach(candidate => {
        const card = createCandidateCard(candidate, 'president');
        presidentCandidates.appendChild(card);
    });

    vicePresidents.forEach(candidate => {
        const card = createCandidateCard(candidate, 'vice_president');
        vicePresidentCandidates.appendChild(card);
    });
}

// Create Candidate Card
function createCandidateCard(candidate, position) {
    const card = document.createElement('div');
    card.className = 'candidate-card';
    card.dataset.candidateId = candidate.id;
    card.dataset.position = position;

    const defaultImage = 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect fill=\'%23e2e8f0\' width=\'200\' height=\'200\'/%3E%3Ctext fill=\'%2394a3b8\' font-family=\'sans-serif\' font-size=\'14\' dy=\'10.5\' font-weight=\'bold\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\'%3ENo Image%3C/text%3E%3C/svg%3E';
    const imageUrl = candidate.image || defaultImage;

    const isVoted = votedPositions.includes(position);

    card.innerHTML = `
        <img src="${imageUrl}" alt="${candidate.name}" class="candidate-image" onerror="this.src='${defaultImage}'">
        <div class="candidate-name">${candidate.name}</div>
        <div class="candidate-position">${candidate.position}</div>
        ${candidate.slogan ? `<div class="candidate-slogan">"${candidate.slogan}"</div>` : ''}
        <div class="candidate-actions">
            <button class="btn btn-primary vote-btn" ${!isTokenValid || isVoted ? 'disabled' : ''}>
                ${isVoted ? 'Voted ✓' : 'Vote'}
            </button>

        </div>
    `;

    // Add click event for vote button
    const voteBtn = card.querySelector('.vote-btn');
    voteBtn.addEventListener('click', () => selectCandidate(candidate.id, position, card));



    // Card click to select
    card.addEventListener('click', (e) => {
        if (e.target !== voteBtn && e.target.tagName !== 'IMG' && isTokenValid && !isVoted) {
            selectCandidate(candidate.id, position, card);
        }
    });

    return card;
}

// Select Candidate
function selectCandidate(candidateId, position, cardElement) {
    if (!isElectionOpen) {
        showVoterStatus('Election is closed. Voting is disabled.', 'warning');
        return;
    }

    if (!isTokenValid) {
        showVoterStatus('Please validate your Token first!', 'warning');
        tokenInput.focus();
        return;
    }

    if (votedPositions.includes(position)) {
        showVoterStatus(`You have already voted for ${position}!`, 'warning');
        return;
    }

    if (!currentToken) {
        showVoterStatus('Please enter your Token first!', 'warning');
        tokenInput.focus();
        return;
    }

    // Remove previous selection for this position
    const container = position === 'president' ? presidentCandidates : vicePresidentCandidates;
    container.querySelectorAll('.candidate-card').forEach(card => {
        card.classList.remove('selected');
    });

    // Add selection to current card
    cardElement.classList.add('selected');

    // Submit vote
    submitVote(candidateId, position);
}

// Submit Vote
async function submitVote(candidateId, position) {
    if (!isElectionOpen) {
        showVoterStatus('Election is closed. Voting is disabled.', 'warning');
        return;
    }

    if (!currentToken) {
        showVoterStatus('Please enter your Token!', 'warning');
        return;
    }

    try {
        const requestSession = votingSessionVersion;
        showLoading();
        const payload = {
            candidateId: parseInt(candidateId),
            position: position,
            token: currentToken
        };
        console.log('Submitting vote with payload:', payload);

        const response = await fetch(`${API_BASE}/api/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (requestSession !== votingSessionVersion) {
            hideLoading();
            return;
        }
        console.log('Vote response:', data);

        if (response.ok) {
            votedPositions.push(position);
            const candidate = candidates.find(c => c.id === candidateId);
            showVoterStatus(`Voted for ${candidate.name}!`, 'success');
            showModal(data.message, data.candidate, position);

            // Update buttons for this position
            updateVoteButtons();

            // Check if both positions are voted
            if (votedPositions.length === 2) {
                showCompletion();
            }

            loadCandidates();
        } else {
            showVoterStatus(data.error || 'Failed to submit vote', 'warning');
        }

        hideLoading();
    } catch (error) {
        console.error('Error submitting vote:', error);
        showVoterStatus('Network error. Please try again.', 'warning');
        hideLoading();
    }
}

// Check Token Status
async function checkTokenStatus() {
    if (!isElectionOpen) {
        showVoterStatus('Election is closed. Voting is disabled.', 'warning');
        return;
    }

    const token = tokenInput.value.trim();

    if (!token) {
        showVoterStatus('Please enter your Voting Token', 'warning');
        return;
    }

    if (tokenCheckInFlight) {
        return;
    }

    currentToken = token;

    try {
        tokenCheckInFlight = true;
        const requestSession = votingSessionVersion;
        showLoading();
        await loadCandidates();
        const response = await fetch(`${API_BASE}/api/check-token/${encodeURIComponent(token)}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to validate token');
        }
        if (requestSession !== votingSessionVersion) {
            hideLoading();
            return;
        }

        isTokenValid = data.isValid;
        votedPositions = data.votedPositions || [];

        if (!isTokenValid) {
            showVoterStatus('Invalid token!', 'warning');
            presidentSection.style.display = 'none';
            vicePresidentSection.style.display = 'none';
        } else if (data.isSpent) {
            showVoterStatus('Token already used for both positions!', 'warning');
            showCompletion();
        } else {
            showVoterStatus('Token valid! Select candidates below.', 'success');
            presidentSection.style.display = 'block';
            vicePresidentSection.style.display = 'block';
            completionSection.style.display = 'none';

            // Update status messages
            presStatus.textContent = votedPositions.includes('president') ? '✓ Voted' : 'Not yet voted';
            viceStatus.textContent = votedPositions.includes('vice_president') ? '✓ Voted' : 'Not yet voted';
        }

        updateVoteButtons();
        hideLoading();
    } catch (error) {
        console.error('Error checking token status:', error);
        showVoterStatus('Error checking status. Please try again.', 'warning');
        hideLoading();
    } finally {
        tokenCheckInFlight = false;
    }
}

// Update Vote Buttons
function updateVoteButtons() {
    // President buttons
    presidentCandidates.querySelectorAll('.vote-btn').forEach(btn => {
        const isVoted = votedPositions.includes('president');
        if (!isElectionOpen || !isTokenValid || isVoted) {
            btn.disabled = true;
            btn.textContent = isElectionOpen ? (isVoted ? 'Voted ✓' : 'Token Required') : 'Closed';
        } else {
            btn.disabled = false;
            btn.textContent = 'Vote';
        }
    });

    // Vice President buttons
    vicePresidentCandidates.querySelectorAll('.vote-btn').forEach(btn => {
        const isVoted = votedPositions.includes('vice_president');
        if (!isElectionOpen || !isTokenValid || isVoted) {
            btn.disabled = true;
            btn.textContent = isElectionOpen ? (isVoted ? 'Voted ✓' : 'Token Required') : 'Closed';
        } else {
            btn.disabled = false;
            btn.textContent = 'Vote';
        }
    });

    // Update card opacity
    presidentCandidates.querySelectorAll('.candidate-card').forEach(card => {
        const isVoted = votedPositions.includes('president');
        if (!isElectionOpen || !isTokenValid || isVoted) {
            card.style.cursor = 'not-allowed';
            card.style.opacity = isVoted ? '0.5' : '0.7';
        } else {
            card.style.cursor = 'pointer';
            card.style.opacity = '1';
        }
    });

    vicePresidentCandidates.querySelectorAll('.candidate-card').forEach(card => {
        const isVoted = votedPositions.includes('vice_president');
        if (!isElectionOpen || !isTokenValid || isVoted) {
            card.style.cursor = 'not-allowed';
            card.style.opacity = isVoted ? '0.5' : '0.7';
        } else {
            card.style.cursor = 'pointer';
            card.style.opacity = '1';
        }
    });
}

// Show Completion Message
function showCompletion() {
    presidentSection.style.display = 'none';
    vicePresidentSection.style.display = 'none';
    completionSection.style.display = 'block';
    isTokenValid = false;
}

function triggerVoteAgainKillSwitch() {
    votingSessionVersion += 1;
    resetVoting();
    showVoterStatus('Voting reset. Enter a new token to vote again.', 'success');
}

// Reset Voting
function resetVoting() {
    currentToken = '';
    isTokenValid = false;
    votedPositions = [];
    tokenInput.value = '';
    voterStatus.classList.remove('show');
    presidentSection.style.display = 'none';
    vicePresidentSection.style.display = 'none';
    completionSection.style.display = 'none';
    closeModal();
    hideLoading();
    presStatus.textContent = '';
    viceStatus.textContent = '';
    updateVoteButtons();
    tokenInput.focus();
}

// Show Modal
function showModal(message, candidateName, position) {
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = `${message} You voted for ${candidateName} as ${position}.`;
    voteModal.classList.add('show');

    // Auto close after 3 seconds
    setTimeout(() => {
        closeModal();
    }, 3000);
}

// Close Modal
function closeModal() {
    voteModal.classList.remove('show');
}

// Show Voter Status
function showVoterStatus(message, type) {
    voterStatus.textContent = message;
    voterStatus.className = `voter-status ${type} show`;

    // Auto hide after 5 seconds
    setTimeout(() => {
        voterStatus.classList.remove('show');
    }, 5000);
}

// Show Loading
function showLoading() {
    loadingOverlay.classList.add('show');
}

// Hide Loading
function hideLoading() {
    loadingOverlay.classList.remove('show');
}

// Show Error
function showError(message) {
    alert(message);
}
