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
const chatHistory = document.getElementById('chat-history');
const chatMessages = document.getElementById('chat-messages');
const errorSection = document.getElementById('error-section');
const errorMessage = document.getElementById('error-message');
const progressSection = document.getElementById('progress-section');
const progressBar = document.getElementById('progress-bar');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

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

    socket.on('outfit_ready', (data) => {
        console.log('Outfit ready:', data);
        displayLiveOutfit(data);
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
async function displaySelfiePreview(file) {
    selfiePreview.innerHTML = '';

    try {
        const imageUrl = await getImagePreviewUrl(file);
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `
            <img src="${imageUrl}" alt="Selfie preview">
            <button class="remove-btn" onclick="removeSelfie()">×</button>
        `;
        selfiePreview.appendChild(div);
    } catch (error) {
        console.error('Error displaying selfie preview:', error);
        // Show a placeholder
        const div = document.createElement('div');
        div.className = 'preview-item';
        div.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:100%;background:#f0f0f0;">
                <span>📷</span>
            </div>
            <button class="remove-btn" onclick="removeSelfie()">×</button>
        `;
        selfiePreview.appendChild(div);
    }
}

async function displayClothingPreviews(files) {
    clothingPreview.innerHTML = '';

    for (let index = 0; index < files.length; index++) {
        const file = files[index];

        try {
            const imageUrl = await getImagePreviewUrl(file);
            const div = document.createElement('div');
            div.className = 'preview-item';
            div.innerHTML = `
                <img src="${imageUrl}" alt="Clothing ${index + 1}">
                <button class="remove-btn" onclick="removeClothing(${index})">×</button>
            `;
            clothingPreview.appendChild(div);
        } catch (error) {
            console.error(`Error displaying preview for file ${index}:`, error);
            // Show a placeholder
            const div = document.createElement('div');
            div.className = 'preview-item';
            div.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:center;height:100%;background:#f0f0f0;">
                    <span>👕</span>
                </div>
                <button class="remove-btn" onclick="removeClothing(${index})">×</button>
            `;
            clothingPreview.appendChild(div);
        }
    }
}

// Helper function to get preview URL (handles HEIC conversion)
async function getImagePreviewUrl(file) {
    // Check if it's a HEIC/HEIF file
    const isHEIC = file.type === 'image/heic' ||
                   file.type === 'image/heif' ||
                   file.name.toLowerCase().endsWith('.heic') ||
                   file.name.toLowerCase().endsWith('.heif');

    if (isHEIC && typeof heic2any !== 'undefined') {
        // Convert HEIC to JPEG using heic2any library
        try {
            const convertedBlob = await heic2any({
                blob: file,
                toType: 'image/jpeg',
                quality: 0.8
            });
            return URL.createObjectURL(convertedBlob);
        } catch (error) {
            console.error('HEIC conversion failed:', error);
            // Fall through to try regular FileReader
        }
    }

    // For regular images or if HEIC conversion failed, use FileReader
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
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

// ===== Live Outfit Preview =====
function displayLiveOutfit(data) {
    const { outfit_number, image_url, total_outfits } = data;

    // Show chat history if not visible
    chatHistory.style.display = 'block';

    // Look for the current assistant message (last one)
    const assistantMessages = chatMessages.querySelectorAll('.chat-message-assistant');
    const currentMessage = assistantMessages[assistantMessages.length - 1];

    if (currentMessage) {
        const outfitsGrid = currentMessage.querySelector('.outfits-grid');

        if (outfitsGrid) {
            // Check if this outfit card already exists
            let existingCard = outfitsGrid.querySelector(`[data-outfit-number="${outfit_number}"]`);

            if (existingCard) {
                // Update existing card with the image
                const img = existingCard.querySelector('.outfit-image');
                if (img) {
                    img.src = image_url;
                }
            } else {
                // Create a placeholder card immediately
                const card = document.createElement('div');
                card.className = 'outfit-card';
                card.setAttribute('data-outfit-number', outfit_number);

                const header = document.createElement('div');
                header.className = 'outfit-header';
                header.textContent = `Outfit ${outfit_number}`;
                card.appendChild(header);

                const img = document.createElement('img');
                img.className = 'outfit-image';
                img.src = image_url;
                img.alt = `Outfit ${outfit_number}`;
                img.loading = 'eager'; // Load immediately for live preview
                card.appendChild(img);

                // Add placeholder details (will be filled when full response arrives)
                const details = document.createElement('div');
                details.className = 'outfit-details';
                details.innerHTML = `
                    <h4>Style</h4>
                    <p class="outfit-reasoning">Loading details...</p>
                    <h4>How to Wear</h4>
                    <p class="outfit-wearing">Loading...</p>
                `;
                card.appendChild(details);

                outfitsGrid.appendChild(card);

                // Scroll to the new card
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }
    }
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

    // Hide previous errors
    hideError();

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

        // Add user message to chat if query exists
        if (query) {
            addChatMessage('user', query);
        }

        // Add assistant message with outfits
        addChatMessage('assistant', data);

        // Clear query input for next message
        queryInput.value = '';

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

// ===== Chat Message Display =====
function addChatMessage(role, content) {
    // Show chat history
    chatHistory.style.display = 'block';

    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message';

    if (role === 'user') {
        // User message bubble
        const userBubble = document.createElement('div');
        userBubble.className = 'chat-message-user';
        userBubble.innerHTML = `
            <div class="message-label">You</div>
            <div class="message-text">${escapeHtml(content)}</div>
        `;
        messageDiv.appendChild(userBubble);
    } else if (role === 'assistant') {
        // Assistant message with outfits
        const assistantBubble = document.createElement('div');
        assistantBubble.className = 'chat-message-assistant';

        let bubbleHTML = '<div class="message-label">Fashion AI</div>';

        // Add query response if exists
        if (content.query_response) {
            bubbleHTML += `<div class="message-text">${escapeHtml(content.query_response)}</div>`;
        }

        // Add outfits grid
        if (content.outfits && content.outfits.length > 0) {
            bubbleHTML += '<div class="outfits-grid"></div>';
        }

        assistantBubble.innerHTML = bubbleHTML;

        // Add outfit cards
        if (content.outfits && content.outfits.length > 0) {
            const outfitsGrid = assistantBubble.querySelector('.outfits-grid');

            content.outfits.forEach(outfit => {
                // Check if card already exists from live preview
                let existingCard = outfitsGrid.querySelector(`[data-outfit-number="${outfit.outfit_number}"]`);

                if (existingCard) {
                    // Update the existing card with full details
                    const reasoningP = existingCard.querySelector('.outfit-reasoning');
                    const wearingP = existingCard.querySelector('.outfit-wearing');

                    if (reasoningP) reasoningP.textContent = outfit.reasoning;
                    if (wearingP) wearingP.textContent = outfit.wearing_instructions;

                    // Handle errors
                    if (outfit.error && !outfit.image_url) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'outfit-error';
                        errorDiv.textContent = `Error: ${outfit.error}`;
                        existingCard.appendChild(errorDiv);
                    }
                } else {
                    // Create new card if it doesn't exist (shouldn't happen with live preview)
                    const card = createOutfitCard(outfit);
                    outfitsGrid.appendChild(card);
                }
            });
        }

        messageDiv.appendChild(assistantBubble);
    }

    chatMessages.appendChild(messageDiv);

    // Scroll to the latest message
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
