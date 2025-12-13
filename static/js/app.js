// ===== State Management =====
let selfieFile = null;
let clothingFiles = [];
let socket = null;
let socketId = null;
let sessionId = null;

// ===== DOM Elements =====
const selfieInput = document.getElementById('selfie');
const clothingInput = document.getElementById('clothing');
const selfiePreview = document.getElementById('selfie-preview');
const clothingPreview = document.getElementById('clothing-preview');
const generateBtn = document.getElementById('generate-btn');
const queryInput = document.getElementById('query');
const resultsSection = document.getElementById('results-section');
const queryResponseDiv = document.getElementById('query-response');
const queryAnswer = document.getElementById('query-answer');
const outfitsContainer = document.getElementById('outfits-container');
const errorSection = document.getElementById('error-section');
const errorMessage = document.getElementById('error-message');
const progressSection = document.getElementById('progress-section');
const progressBar = document.getElementById('progress-bar');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const sessionInfo = document.getElementById('session-info');

// ===== WebSocket Setup =====
function initWebSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('WebSocket connected');
        socketId = socket.id;
        console.log('Socket ID:', socketId);
    });

    socket.on('connected', (data) => {
        socketId = data.sid;
        console.log('Server confirmed connection:', socketId);
    });

    socket.on('progress', (data) => {
        console.log('Progress update:', data);
        updateProgress(data);
    });

    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
    });

    socket.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
}

// Initialize WebSocket on load
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
});

// ===== Progress Updates =====
function updateProgress(data) {
    const { step, message, progress_percent, details } = data;

    // Show progress section
    if (progressSection) {
        progressSection.style.display = 'block';
    }

    // Update progress bar
    if (progressFill) {
        progressFill.style.width = `${progress_percent}%`;
    }

    // Update progress text
    if (progressText) {
        progressText.textContent = message;
    }

    // Store session ID if provided
    if (details && details.session_id) {
        sessionId = details.session_id;
        updateSessionInfo(details.session_id, details.is_new_session);
    }

    // Handle completion
    if (step === 'complete') {
        setTimeout(() => {
            if (progressSection) {
                progressSection.style.display = 'none';
            }
        }, 2000);
    }

    // Handle errors
    if (step === 'error') {
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    }
}

function updateSessionInfo(sid, isNew) {
    if (sessionInfo) {
        if (isNew) {
            sessionInfo.textContent = `🆕 New conversation started`;
        } else {
            sessionInfo.textContent = `💬 Continuing conversation`;
        }
        sessionInfo.style.display = 'block';
    }
}

// ===== File Input Handlers =====
selfieInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        selfieFile = file;
        displaySelfiePreview(file);
        updateFileLabel(selfieInput, file.name);
        // Show clear button
        document.getElementById('clear-selfie-btn').style.display = 'inline-block';
    }
});

clothingInput.addEventListener('change', (e) => {
    clothingFiles = Array.from(e.target.files);
    displayClothingPreviews(clothingFiles);
    updateFileLabel(clothingInput, `${clothingFiles.length} file(s) selected`);
    // Show clear button
    document.getElementById('clear-clothing-btn').style.display = 'inline-block';
});

function updateFileLabel(input, text) {
    const label = input.nextElementSibling;
    const labelText = label.querySelector('.file-label-text');
    labelText.textContent = text;
}

// ===== Display Previews =====
function displaySelfiePreview(file) {
    selfiePreview.innerHTML = '';
    const reader = new FileReader();
    reader.onload = (e) => {
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `
            <img src="${e.target.result}" alt="Selfie preview">
            <button class="remove-btn" onclick="removeSelfie()">×</button>
        `;
        selfiePreview.appendChild(div);
    };
    reader.readAsDataURL(file);
}

function displayClothingPreviews(files) {
    clothingPreview.innerHTML = '';
    files.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.className = 'preview-item';
            div.innerHTML = `
                <img src="${e.target.result}" alt="Clothing ${index + 1}">
                <button class="remove-btn" onclick="removeClothing(${index})">×</button>
            `;
            clothingPreview.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

// ===== Remove Functions =====
function removeSelfie() {
    selfieFile = null;
    selfieInput.value = '';
    selfiePreview.innerHTML = '';
    updateFileLabel(selfieInput, 'Choose selfie...');
    document.getElementById('clear-selfie-btn').style.display = 'none';
}

function clearSelfie() {
    removeSelfie();
}

function removeClothing(index) {
    clothingFiles.splice(index, 1);
    displayClothingPreviews(clothingFiles);

    const dt = new DataTransfer();
    clothingFiles.forEach(file => dt.items.add(file));
    clothingInput.files = dt.files;

    if (clothingFiles.length === 0) {
        updateFileLabel(clothingInput, 'Choose clothing images...');
        document.getElementById('clear-clothing-btn').style.display = 'none';
    } else {
        updateFileLabel(clothingInput, `${clothingFiles.length} file(s) selected`);
    }
}

function clearClothing() {
    clothingFiles = [];
    clothingInput.value = '';
    clothingPreview.innerHTML = '';
    updateFileLabel(clothingInput, 'Choose clothing images...');
    document.getElementById('clear-clothing-btn').style.display = 'none';
}

// ===== Generate Outfits =====
generateBtn.addEventListener('click', async () => {
    // Validation
    if (clothingFiles.length === 0) {
        showError('Please upload at least one clothing item image');
        return;
    }

    if (clothingFiles.length > 20) {
        showError('Maximum 20 clothing items allowed');
        return;
    }

    // Hide previous results and errors
    hideError();
    resultsSection.style.display = 'none';
    queryResponseDiv.style.display = 'none';
    outfitsContainer.innerHTML = '';

    // Show progress
    if (progressSection) {
        progressSection.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Starting...';
    }

    // Show loading state
    const btnText = generateBtn.querySelector('.btn-text');
    const spinner = generateBtn.querySelector('.spinner');
    btnText.style.display = 'none';
    spinner.style.display = 'inline-block';
    generateBtn.disabled = true;

    try {
        // Build form data
        const formData = new FormData();

        // Add clothing images
        clothingFiles.forEach(file => {
            formData.append('clothing_images', file);
        });

        // Add selfie if provided
        if (selfieFile) {
            formData.append('selfie', selfieFile);
        }

        // Add query if provided
        const query = queryInput.value.trim();
        if (query) {
            formData.append('query', query);
        }

        // Add session ID if exists (for continued conversation)
        if (sessionId) {
            formData.append('session_id', sessionId);
        }

        // Make API request with socket ID in header
        const headers = {};
        if (socketId) {
            headers['X-Socket-ID'] = socketId;
        }

        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData,
            headers: headers
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate outfits');
        }

        // Update session ID
        if (data.session_id) {
            sessionId = data.session_id;
        }

        // Display results
        displayResults(data);

        // Don't clear query input - allow continued conversation
        // queryInput.value = '';  // REMOVED

    } catch (error) {
        showError(error.message);
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    } finally {
        // Reset button state
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        generateBtn.disabled = false;
    }
});

// ===== Display Results =====
function displayResults(data) {
    resultsSection.style.display = 'block';

    // Show session context
    if (data.conversation_context && sessionInfo) {
        sessionInfo.textContent = `💬 ${data.conversation_context}`;
        sessionInfo.style.display = 'block';
    }

    // Show query response if exists
    if (data.query_response) {
        queryResponseDiv.style.display = 'block';
        queryAnswer.textContent = data.query_response;
    }

    // Display outfits
    if (data.outfits && data.outfits.length > 0) {
        data.outfits.forEach(outfit => {
            const card = createOutfitCard(outfit);
            outfitsContainer.appendChild(card);
        });

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ===== Create Outfit Card =====
function createOutfitCard(outfit) {
    const card = document.createElement('div');
    card.className = 'outfit-card';

    const header = document.createElement('div');
    header.className = 'outfit-header';
    header.textContent = `Outfit ${outfit.outfit_number}`;
    card.appendChild(header);

    if (outfit.image_url) {
        const img = document.createElement('img');
        img.className = 'outfit-image';
        img.src = outfit.image_url;
        img.alt = `Outfit ${outfit.outfit_number}`;
        img.loading = 'lazy';
        card.appendChild(img);

        const details = document.createElement('div');
        details.className = 'outfit-details';

        details.innerHTML = `
            <h4>Style</h4>
            <p>${outfit.reasoning}</p>
            <h4>How to Wear</h4>
            <p>${outfit.wearing_instructions}</p>
        `;
        card.appendChild(details);
    } else if (outfit.error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'outfit-error';
        errorDiv.textContent = `Error: ${outfit.error}`;
        card.appendChild(errorDiv);
    }

    return card;
}

// ===== Error Handling =====
function showError(message) {
    errorSection.style.display = 'block';
    errorMessage.textContent = `❌ ${message}`;
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    errorSection.style.display = 'none';
    errorMessage.textContent = '';
}

// ===== Make Functions Global =====
window.removeSelfie = removeSelfie;
window.clearSelfie = clearSelfie;
window.removeClothing = removeClothing;
window.clearClothing = clearClothing;
