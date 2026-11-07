// API Base URL
const API_BASE = window.location.origin;

// DOM Elements
const registrationForm = document.getElementById('registration-form');
const candidateNameInput = document.getElementById('candidate-name');
const candidatePositionSelect = document.getElementById('candidate-position');
const customPositionGroup = document.getElementById('custom-position-group');
const customPositionInput = document.getElementById('custom-position');
const candidateImageInput = document.getElementById('candidate-image');
const imagePreview = document.getElementById('image-preview');
const candidateSloganInput = document.getElementById('candidate-slogan');
const candidateStudentIdInput = document.getElementById('candidate-student-id');
const formStatus = document.getElementById('form-status');
const submitBtn = document.getElementById('submit-btn');
const resetBtn = document.getElementById('reset-btn');
const refreshCandidatesBtn = document.getElementById('refresh-candidates');
const registeredCandidatesContainer = document.getElementById('registered-candidates-container');
const registerCandidateSection = document.getElementById('register-candidate-section');
const successModal = document.getElementById('success-modal');
const closeSuccessBtn = document.getElementById('close-success-btn');
const loadingOverlay = document.getElementById('loading-overlay');
const MAX_IMAGE_SIZE_MB = 7;//image size threshold
const MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024;
const REGISTER_BUTTON_TEXT = 'Register as Candidate';
const UPDATE_BUTTON_TEXT = 'Update Candidate Info';
let editingCandidateId = null;
let existingImageBase64 = '';
let loadedCandidates = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadElectionState();
    loadRegisteredCandidates();
    setInterval(loadElectionState, 6000);
});

// Event Listeners
function setupEventListeners() {
    registrationForm.addEventListener('submit', handleFormSubmit);
    resetBtn.addEventListener('click', handleFormReset);
    refreshCandidatesBtn.addEventListener('click', () => loadRegisteredCandidates(true));
    registeredCandidatesContainer.addEventListener('click', handleCandidateCardActions);

    // Handle position selection change
    candidatePositionSelect.addEventListener('change', (e) => {
        if (e.target.value === 'Other') {
            customPositionGroup.style.display = 'block';
            customPositionInput.setAttribute('required', 'required');
        } else {
            customPositionGroup.style.display = 'none';
            customPositionInput.removeAttribute('required');
            customPositionInput.value = '';
        }
    });

    // Update image preview when file is selected
    candidateImageInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                showFormStatus('Please select a valid image file.', 'error');
                candidateImageInput.value = '';
                return;
            }

            // Validate file size (7MB max)
            if (file.size > MAX_IMAGE_SIZE_BYTES) {
                showFormStatus(`Image size must be less than ${MAX_IMAGE_SIZE_MB}MB.`, 'error');
                candidateImageInput.value = '';
                return;
            }

            // Read and display preview
            const reader = new FileReader();
            reader.onload = (event) => {
                imagePreview.src = event.target.result;
                imagePreview.style.display = 'block';
            };
            reader.onerror = () => {
                showFormStatus('Error reading image file.', 'error');
            };
            reader.readAsDataURL(file);
        } else {
            imagePreview.src = '';
            imagePreview.style.display = 'none';
        }
    });

    // Modal close handlers
    closeSuccessBtn.addEventListener('click', closeSuccessModal);
    successModal.addEventListener('click', (e) => {
        if (e.target === successModal) {
            closeSuccessModal();
        }
    });
}

// Handle Form Submit
async function handleFormSubmit(e) {
    e.preventDefault();

    const name = candidateNameInput.value.trim();
    const position = candidatePositionSelect.value === 'Other'
        ? customPositionInput.value.trim()
        : candidatePositionSelect.value;
    const studentId = candidateStudentIdInput.value.trim();
    const slogan = candidateSloganInput.value.trim();
    const imageFile = candidateImageInput.files[0];
    const isEditing = editingCandidateId !== null;

    // Validation
    if (!name || !position || !studentId) {
        showFormStatus('Please fill in all required fields.', 'error');
        return;
    }

    if (!imageFile && !existingImageBase64) {
        showFormStatus('Please select a profile image.', 'error');
        return;
    }

    if (imageFile) {
        // Validate file type
        if (!imageFile.type.startsWith('image/')) {
            showFormStatus('Please select a valid image file.', 'error');
            return;
        }

        // Validate file size (7MB max)
        if (imageFile.size > MAX_IMAGE_SIZE_BYTES) {
            showFormStatus(`Image size must be less than ${MAX_IMAGE_SIZE_MB}MB.`, 'error');
            return;
        }
    }

    if (candidatePositionSelect.value === 'Other' && !customPositionInput.value.trim()) {
        showFormStatus('Please enter a custom position.', 'error');
        return;
    }

    // Convert image to base64
    let imageBase64 = existingImageBase64;
    if (imageFile) {
        try {
            imageBase64 = await fileToBase64(imageFile);
        } catch (error) {
            showFormStatus('Error processing image. Please try again.', 'error');
            return;
        }
    }

    try {
        showLoading();

        // Check if we're accessing through the correct server
        if (API_BASE.includes('5500') || API_BASE.includes('file://')) {
            showFormStatus('Please access this page through the Flask server at http://localhost:3000', 'error');
            hideLoading();
            return;
        }

        const requestUrl = isEditing
            ? `${API_BASE}/api/candidates/${editingCandidateId}`
            : `${API_BASE}/api/candidates/register`;
        const requestMethod = isEditing ? 'PUT' : 'POST';

        const response = await fetch(requestUrl, {
            method: requestMethod,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                position: position,
                image: imageBase64,
                studentId: studentId,
                slogan: slogan
            })
        });

        hideLoading();

        // Check if response is ok before parsing JSON
        if (!response.ok) {
            let errorMessage = isEditing
                ? 'Update failed. Please try again.'
                : 'Registration failed. Please try again.';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = `Error ${response.status}: ${response.statusText || 'Server error'}`;
            }
            showFormStatus(errorMessage, 'error');
            return;
        }

        const data = await response.json();

        showSuccessModal(data.message, data.candidate);
        resetFormState();
        loadRegisteredCandidates();
        // Notify voting page to refresh (using localStorage event)
        const timestamp = Date.now().toString();
        localStorage.setItem('candidatesUpdated', timestamp);
        // Trigger storage event manually for same-tab updates
        window.dispatchEvent(new StorageEvent('storage', {
            key: 'candidatesUpdated',
            newValue: timestamp
        }));
    } catch (error) {
        console.error('Error submitting registration:', error);
        hideLoading();
        showFormStatus(`Network error: ${error.message}. Make sure the Flask server is running on port 3000.`, 'error');
    }
}

// Handle Form Reset
function handleFormReset() {
    resetFormState();
}

function resetFormState() {
    editingCandidateId = null;
    existingImageBase64 = '';
    submitBtn.textContent = REGISTER_BUTTON_TEXT;
    resetBtn.textContent = 'Clear Form';

    registrationForm.reset();
    customPositionGroup.style.display = 'none';
    customPositionInput.removeAttribute('required');
    candidateImageInput.value = '';
    candidateSloganInput.value = '';
    imagePreview.src = '';
    imagePreview.style.display = 'none';
    formStatus.textContent = '';
    formStatus.className = 'form-status';
}

function handleCandidateCardActions(event) {
    const editBtn = event.target.closest('.edit-candidate-btn');
    if (!editBtn) {
        return;
    }

    const candidateId = Number.parseInt(editBtn.dataset.candidateId, 10);
    if (Number.isNaN(candidateId)) {
        return;
    }

    const candidate = loadedCandidates.find((item) => Number(item.id) === candidateId);
    if (!candidate) {
        showFormStatus('Candidate not found for editing. Please refresh and try again.', 'error');
        return;
    }

    editingCandidateId = candidateId;
    existingImageBase64 = candidate.image || '';
    submitBtn.textContent = UPDATE_BUTTON_TEXT;
    resetBtn.textContent = 'Cancel Edit';

    candidateNameInput.value = candidate.name || '';
    candidateStudentIdInput.value = candidate.studentId || '';
    candidateSloganInput.value = candidate.slogan || '';
    candidatePositionSelect.value = candidate.position || '';
    customPositionGroup.style.display = 'none';
    customPositionInput.value = '';
    customPositionInput.removeAttribute('required');

    if (existingImageBase64) {
        imagePreview.src = existingImageBase64;
        imagePreview.style.display = 'block';
    } else {
        imagePreview.src = '';
        imagePreview.style.display = 'none';
    }

    closeSuccessModal();
    if (registerCandidateSection) {
        registerCandidateSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
    candidateNameInput.focus();
    showFormStatus(`Editing candidate: ${candidate.name}`, 'success');
}

async function loadElectionState() {
    try {
        const response = await fetch(`${API_BASE}/api/election-state`);
        const state = await response.json();

        const statusEl = document.getElementById('register-election-status');
        const winnerEl = document.getElementById('register-winner-declaration');

        if (statusEl) {
            statusEl.textContent = state.isOpen ? 'Election is OPEN' : 'Election is CLOSED';
            statusEl.style.color = state.isOpen ? '#22c55e' : '#ef4444';
        }

        if (winnerEl) {
            winnerEl.textContent = (state.winnerDeclaration || '').trim() || 'No winner declaration yet.';
        }
    } catch (error) {
        console.error('Error loading election state:', error);
    }
}

// Load Registered Candidates
async function loadRegisteredCandidates(showAnimation = false) {
    try {
        const response = await fetch(`${API_BASE}/api/candidates`);
        const candidates = await response.json();
        loadedCandidates = Array.isArray(candidates) ? candidates : [];
        renderRegisteredCandidates(loadedCandidates, showAnimation);
    } catch (error) {
        console.error('Error loading candidates:', error);
        loadedCandidates = [];
        registeredCandidatesContainer.innerHTML = '<p class="error-message">Failed to load candidates.</p>';
    }
}

// Render Registered Candidates
function renderRegisteredCandidates(candidates, animate = false) {
    registeredCandidatesContainer.innerHTML = '';

    if (candidates.length === 0) {
        registeredCandidatesContainer.innerHTML = '<p class="empty-message">No candidates registered yet.</p>';
        return;
    }

    candidates.forEach((candidate, index) => {
        const card = document.createElement('div');
        card.className = 'registered-candidate-card';
        if (animate) {
            card.style.animationDelay = `${index * 0.1}s`;
        }

        const defaultImage = 'data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'200\' height=\'200\'%3E%3Crect fill=\'%23e2e8f0\' width=\'200\' height=\'200\'/%3E%3Ctext fill=\'%2394a3b8\' font-family=\'sans-serif\' font-size=\'14\' dy=\'10.5\' font-weight=\'bold\' x=\'50%25\' y=\'50%25\' text-anchor=\'middle\'%3ENo Image%3C/text%3E%3C/svg%3E';
        const registrationDate = candidate.registrationDate ? new Date(candidate.registrationDate).toLocaleDateString() : 'N/A';
        card.innerHTML = `
            <div class="candidate-card-header">
                <img src="${candidate.image || defaultImage}" alt="${candidate.name}" class="candidate-image-large" onerror="this.src='${defaultImage}'">
                <div class="candidate-info">
                    <h3 class="candidate-name-large">${candidate.name}</h3>
                    <p class="candidate-position-large">${candidate.position}</p>
                    ${candidate.slogan ? `<p class="candidate-slogan-small">"${candidate.slogan}"</p>` : ''}
                </div>
            </div>
            <div class="candidate-card-footer">
                <span class="candidate-id">ID: ${candidate.id}</span>
                <span class="candidate-reg-date">Registered: ${registrationDate}</span>
                <button type="button" class="btn btn-secondary candidate-edit-btn edit-candidate-btn" data-candidate-id="${candidate.id}">
                    Edit Candidate
                </button>
            </div>
        `;

        registeredCandidatesContainer.appendChild(card);
    });
}

// Show Success Modal
function showSuccessModal(message, candidate) {
    const successMessage = document.getElementById('success-message');
    successMessage.textContent = `${message} ${candidate ? `Welcome, ${candidate.name}!` : ''}`;
    successModal.classList.add('show');
}

// Close Success Modal
function closeSuccessModal() {
    successModal.classList.remove('show');
}

// Show Form Status
function showFormStatus(message, type) {
    formStatus.textContent = message;
    formStatus.className = `form-status ${type} show`;

    setTimeout(() => {
        formStatus.classList.remove('show');
    }, 5000);
}

// Show Loading
function showLoading() {
    loadingOverlay.classList.add('show');
    submitBtn.disabled = true;
}

// Hide Loading
function hideLoading() {
    loadingOverlay.classList.remove('show');
    submitBtn.disabled = false;
}

// Convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}


