// ===== State Management =====
let selfieFiles = [];
let clothingFiles = [];
let socket = null;
let socketId = null;
let sessionId = null;

// Pre-processing cache: Map of filename -> description
let imageDescriptions = new Map();
let preprocessingInProgress = false;

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
const preprocessingSection = document.getElementById('preprocessing-section');
const preprocessingFill = document.getElementById('preprocessing-fill');
const preprocessingText = document.getElementById('preprocessing-text');

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

// ===== Unsplash Carousel =====
const unsplashImages = [
    'corey-saldana-pIKQbdSzF_k-unsplash.jpg',
    'emmanuel-akinte-ryfMb5hF4mg-unsplash.jpg',
    'hamza-nouasria-owpsBDBK5nY-unsplash.jpg',
    'joao-vitor-duarte-pbHk4grW63Q-unsplash.jpg',
    'jon-ly-Xn7GvimQrk8-unsplash.jpg',
    'joshua-rawson-harris-haUQC3eto2s-unsplash.jpg',
    'karsten-winegeart-UicC_FIozPc-unsplash.jpg',
    'majid-akbari-Egj4Dg107kc-unsplash.jpg',
    'mike-von-V4cl7_0N2mc-unsplash.jpg',
    'ospan-ali-nyrSsBzhZ4Y-unsplash.jpg',
    'vic-domic-RvYwaBjo83M-unsplash.jpg',
    'zahir-namane-TjUJJACTav4-unsplash.jpg'
];

let carouselInterval = null;
let leftIndex = 0;
let rightIndex = 6;

function startCarousel() {
    const leftSide = document.querySelector('.carousel-left');
    const rightSide = document.querySelector('.carousel-right');

    // Set initial images
    leftSide.style.backgroundImage = `url('/unsplash/${unsplashImages[leftIndex]}')`;
    rightSide.style.backgroundImage = `url('/unsplash/${unsplashImages[rightIndex]}')`;

    // Carousel loop: display - wait 2s - scroll to next
    carouselInterval = setInterval(() => {
        leftIndex = (leftIndex + 1) % 6;
        rightIndex = 6 + ((rightIndex - 6 + 1) % 6);

        leftSide.style.backgroundImage = `url('/unsplash/${unsplashImages[leftIndex]}')`;
        rightSide.style.backgroundImage = `url('/unsplash/${unsplashImages[rightIndex]}')`;
    }, 2000);
}

function stopCarousel() {
    if (carouselInterval) {
        clearInterval(carouselInterval);
        carouselInterval = null;
    }

    // Fade out carousel
    const carousel = document.querySelector('.background-carousel');
    if (carousel) {
        carousel.style.transition = 'opacity 3s ease-in-out';
        carousel.style.opacity = '0';
        setTimeout(() => {
            carousel.style.display = 'none';
        }, 3000);
    }
}

// Initialize WebSocket on load
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    startCarousel();
    loadLocationWeatherBackground();
});

// ===== GPS Geolocation =====
async function getUserLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation not supported'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                });
            },
            (error) => {
                console.warn('Geolocation error:', error);
                reject(error);
            },
            {
                enableHighAccuracy: false,
                timeout: 5000,
                maximumAge: 300000 // 5 minutes cache
            }
        );
    });
}

// ===== Location, Weather, and Background =====
async function loadLocationWeatherBackground() {
    try {
        // Try to get GPS location first
        let coords = null;
        try {
            coords = await getUserLocation();
            console.log('Got GPS coordinates:', coords);
        } catch (gpsError) {
            console.log('GPS unavailable, falling back to IP-based location');
        }

        // Fetch location and weather (pass GPS coords if available)
        const url = coords
            ? `/api/location-weather?lat=${coords.latitude}&lon=${coords.longitude}`
            : '/api/location-weather';
        const response = await fetch(url);
        const data = await response.json();

        console.log('Location/Weather:', data);

        // Generate background image
        const bgResponse = await fetch('/api/generate-background', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                location: data.location,
                weather: data.weather
            })
        });

        const bgData = await bgResponse.json();

        if (bgData.success) {
            // Apply background with fade-in effect
            applyBackground(bgData.image_url, data.location, data.weather);
        }
    } catch (error) {
        console.error('Error loading background:', error);
    }
}

function applyBackground(imageUrl, location, weather) {
    // Stop the carousel before showing weather background
    stopCarousel();

    // Create background element
    const bgDiv = document.createElement('div');
    bgDiv.className = 'dynamic-background';
    bgDiv.style.backgroundImage = `url(${imageUrl})`;
    bgDiv.style.opacity = '0';

    // Insert as first child of body
    document.body.insertBefore(bgDiv, document.body.firstChild);

    // Fade in slowly after carousel fades out
    setTimeout(() => {
        bgDiv.style.opacity = '1';
    }, 3100);

    // Add location indicator
    const locationTag = document.createElement('div');
    locationTag.className = 'location-tag';
    locationTag.innerHTML = `
        <span class="location-icon">📍</span>
        <span class="location-text">${location} • ${weather}</span>
    `;
    document.body.appendChild(locationTag);
}

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

    // Create placeholder cards when outfit generation starts
    if (step === 'generating_images' && details && details.total_outfits) {
        createOutfitPlaceholders(details.total_outfits);
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
    const files = Array.from(e.target.files);

    // Limit to 3 selfies (silently take first 3)
    selfieFiles = files.slice(0, 3);

    if (selfieFiles.length > 0) {
        displaySelfiePreview(selfieFiles);
        updateFileLabel(selfieInput, `${selfieFiles.length} selfie(s) selected`);
        // Show clear button
        document.getElementById('clear-selfie-btn').style.display = 'inline-block';
    }
});

clothingInput.addEventListener('change', async (e) => {
    clothingFiles = Array.from(e.target.files);
    displayClothingPreviews(clothingFiles);
    updateFileLabel(clothingInput, `${clothingFiles.length} file(s) selected`);
    // Show clear button
    document.getElementById('clear-clothing-btn').style.display = 'inline-block';
    // Update button text
    updateGenerateButtonText();
    // Start pre-processing images immediately
    preprocessImages(clothingFiles);
});

// Update button text based on whether images are uploaded
function updateGenerateButtonText() {
    const btnText = generateBtn.querySelector('.btn-text');
    if (clothingFiles.length > 0) {
        btnText.textContent = 'Generate Outfits';
    } else {
        btnText.textContent = 'Submit';
    }
}

// Listen to query input changes to update button text
queryInput.addEventListener('input', () => {
    updateGenerateButtonText();
});

function updateFileLabel(input, text) {
    const label = input.nextElementSibling;
    const labelText = label.querySelector('.file-label-text');
    labelText.textContent = text;
}

// ===== Display Previews =====
async function displaySelfiePreview(files) {
    selfiePreview.innerHTML = '';

    // Handle multiple selfies
    for (let index = 0; index < files.length; index++) {
        const file = files[index];

        // Show loading placeholder immediately
        const placeholderDiv = document.createElement('div');
        placeholderDiv.className = 'preview-item preview-loading';
        placeholderDiv.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <span style="font-size:2rem;">📷</span>
                <span style="font-size:0.7rem;color:white;margin-top:5px;">Converting...</span>
            </div>
            <button class="remove-btn" onclick="removeSelfie(${index})">×</button>
        `;
        selfiePreview.appendChild(placeholderDiv);

        // Convert async
        convertAndDisplaySelfie(file, index, placeholderDiv);
    }
}

async function convertAndDisplaySelfie(file, index, placeholderDiv) {
    try {
        const imageUrl = await getImagePreviewUrl(file);
        // Replace placeholder with actual image
        if (placeholderDiv.parentNode) {
            placeholderDiv.className = 'preview-item';
            placeholderDiv.innerHTML = `
                <img src="${imageUrl}" alt="Selfie ${index + 1}">
                <button class="remove-btn" onclick="removeSelfie(${index})">×</button>
            `;
        }
    } catch (error) {
        console.error('Error displaying selfie preview:', error);
        // Show error placeholder
        if (placeholderDiv.parentNode) {
            placeholderDiv.className = 'preview-item';
            placeholderDiv.innerHTML = `
                <div style="display:flex;align-items:center;justify-content:center;height:100%;background:#ffebee;">
                    <span style="font-size:1.5rem;">⚠️</span>
                </div>
                <button class="remove-btn" onclick="removeSelfie(${index})">×</button>
            `;
        }
    }
}

// ===== Pre-processing Functions =====
async function preprocessImages(files) {
    if (preprocessingInProgress || files.length === 0) {
        return;
    }

    preprocessingInProgress = true;
    preprocessingSection.style.display = 'block';

    let completed = 0;
    const total = files.length;

    // De-duplicate files by name
    const uniqueFiles = new Map();
    for (const file of files) {
        if (!uniqueFiles.has(file.name)) {
            uniqueFiles.set(file.name, file);
        }
    }

    const filesToProcess = Array.from(uniqueFiles.values());

    try {
        // Process files in parallel (limited to 3 at a time to avoid overwhelming the server)
        const batchSize = 3;
        for (let i = 0; i < filesToProcess.length; i += batchSize) {
            const batch = filesToProcess.slice(i, i + batchSize);

            await Promise.all(batch.map(async (file) => {
                // Skip if already cached
                if (imageDescriptions.has(file.name)) {
                    completed++;
                    updatePreprocessingProgress(completed, total);
                    return;
                }

                try {
                    const formData = new FormData();
                    formData.append('image', file);
                    formData.append('filename', file.name);

                    const response = await fetch('/api/describe-image', {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        const data = await response.json();
                        if (data.success) {
                            imageDescriptions.set(file.name, data.description);
                        }
                    }
                } catch (error) {
                    console.error(`Error preprocessing ${file.name}:`, error);
                }

                completed++;
                updatePreprocessingProgress(completed, total);
            }));
        }

        // Hide preprocessing section after a short delay
        setTimeout(() => {
            preprocessingSection.style.display = 'none';
            preprocessingInProgress = false;
        }, 500);

    } catch (error) {
        console.error('Error during preprocessing:', error);
        preprocessingSection.style.display = 'none';
        preprocessingInProgress = false;
    }
}

function updatePreprocessingProgress(completed, total) {
    const percent = Math.round((completed / total) * 100);
    preprocessingFill.style.width = `${percent}%`;
    preprocessingText.textContent = `Analyzed ${completed}/${total} images...`;
}

async function displayClothingPreviews(files) {
    clothingPreview.innerHTML = '';

    for (let index = 0; index < files.length; index++) {
        const file = files[index];
        const previewDiv = document.createElement('div');
        previewDiv.className = 'preview-item preview-loading';
        previewDiv.setAttribute('data-index', index);
        previewDiv.setAttribute('data-filename', file.name);

        // Show placeholder immediately
        previewDiv.innerHTML = `
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                <span style="font-size:2rem;">👕</span>
                <span style="font-size:0.7rem;color:white;margin-top:5px;">Loading...</span>
            </div>
            <button class="remove-btn" onclick="removeClothing(${index})">×</button>
        `;
        clothingPreview.appendChild(previewDiv);

        // Convert HEIC on backend if needed, then load
        convertAndDisplayImage(file, index, previewDiv);
    }
}

async function convertAndDisplayImage(file, index, previewDiv) {
    const isHEIC = file.name.toLowerCase().endsWith('.heic') || file.name.toLowerCase().endsWith('.heif');

    if (isHEIC) {
        // Send to backend for conversion
        try {
            const formData = new FormData();
            formData.append('image', file);
            formData.append('filename', file.name);

            const response = await fetch('/api/convert-heic', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const blob = await response.blob();
                const imageUrl = URL.createObjectURL(blob);

                // Replace placeholder with converted image
                if (previewDiv.parentNode) {
                    previewDiv.className = 'preview-item';
                    previewDiv.innerHTML = `
                        <img src="${imageUrl}" alt="Clothing ${index + 1}">
                        <button class="remove-btn" onclick="removeClothing(${index})">×</button>
                    `;
                }
            } else {
                throw new Error('Conversion failed');
            }
        } catch (error) {
            console.error('HEIC conversion error:', error);
            // Fallback to FileReader
            loadImageWithFileReader(file, index, previewDiv);
        }
    } else {
        // Regular images - just use FileReader
        loadImageWithFileReader(file, index, previewDiv);
    }
}

function loadImageWithFileReader(file, index, previewDiv) {
    const reader = new FileReader();
    reader.onload = (e) => {
        if (previewDiv.parentNode) {
            previewDiv.className = 'preview-item';
            previewDiv.innerHTML = `
                <img src="${e.target.result}" alt="Clothing ${index + 1}">
                <button class="remove-btn" onclick="removeClothing(${index})">×</button>
            `;
        }
    };
    reader.readAsDataURL(file);
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
            let convertedBlob = await heic2any({
                blob: file,
                toType: 'image/jpeg',
                quality: 0.8
            });

            // heic2any might return an array of blobs, take the first one
            if (Array.isArray(convertedBlob)) {
                convertedBlob = convertedBlob[0];
            }

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
function removeSelfie(index) {
    // Remove from array
    selfieFiles.splice(index, 1);

    // Remove only the specific preview item
    const previewItems = selfiePreview.querySelectorAll('.preview-item');
    if (previewItems[index]) {
        previewItems[index].remove();
    }

    // Update indices on remaining remove buttons
    const remainingItems = selfiePreview.querySelectorAll('.preview-item');
    remainingItems.forEach((item, newIndex) => {
        const removeBtn = item.querySelector('.remove-btn');
        if (removeBtn) {
            removeBtn.setAttribute('onclick', `removeSelfie(${newIndex})`);
        }
    });

    // Update label and clear button visibility
    if (selfieFiles.length === 0) {
        selfieInput.value = '';
        updateFileLabel(selfieInput, 'Choose selfies...');
        document.getElementById('clear-selfie-btn').style.display = 'none';
    } else {
        updateFileLabel(selfieInput, `${selfieFiles.length} selfie(s) selected`);
    }
}

function clearSelfie() {
    selfieFiles = [];
    selfieInput.value = '';
    selfiePreview.innerHTML = '';
    updateFileLabel(selfieInput, 'Choose selfies...');
    document.getElementById('clear-selfie-btn').style.display = 'none';
}

function removeClothing(index) {
    // Remove from array
    clothingFiles.splice(index, 1);

    // Remove only the specific preview item
    const previewItems = clothingPreview.querySelectorAll('.preview-item');
    if (previewItems[index]) {
        previewItems[index].remove();
    }

    // Update indices on remaining remove buttons
    const remainingItems = clothingPreview.querySelectorAll('.preview-item');
    remainingItems.forEach((item, newIndex) => {
        const removeBtn = item.querySelector('.remove-btn');
        if (removeBtn) {
            removeBtn.setAttribute('onclick', `removeClothing(${newIndex})`);
        }
    });

    // Update file input
    const dt = new DataTransfer();
    clothingFiles.forEach(file => dt.items.add(file));
    clothingInput.files = dt.files;

    // Update label and clear button
    if (clothingFiles.length === 0) {
        updateFileLabel(clothingInput, 'Choose clothing images...');
        document.getElementById('clear-clothing-btn').style.display = 'none';
    } else {
        updateFileLabel(clothingInput, `${clothingFiles.length} file(s) selected`);
    }

    // Update button text
    updateGenerateButtonText();
}

function clearClothing() {
    clothingFiles = [];
    clothingInput.value = '';
    clothingPreview.innerHTML = '';
    updateFileLabel(clothingInput, 'Choose clothing images...');
    document.getElementById('clear-clothing-btn').style.display = 'none';
    updateGenerateButtonText();
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
                // Replace placeholder with actual image
                const placeholder = existingCard.querySelector('.outfit-image-placeholder');
                if (placeholder) {
                    const img = document.createElement('img');
                    img.className = 'outfit-image';
                    img.src = image_url;
                    img.alt = `Outfit ${outfit_number}`;
                    img.loading = 'eager';
                    placeholder.replaceWith(img);
                    existingCard.classList.remove('outfit-card-loading');
                } else {
                    // Update existing image
                    const img = existingCard.querySelector('.outfit-image');
                    if (img) {
                        img.src = image_url;
                    }
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
    // Get query text
    const query = queryInput.value.trim();

    // Validation - allow either images OR text query
    if (clothingFiles.length === 0 && !query) {
        showError('Please upload clothing images or ask a question');
        return;
    }

    if (clothingFiles.length > 30) {
        showError('Maximum 30 clothing items allowed');
        return;
    }

    // Hide previous errors
    hideError();

    // Create assistant message placeholder early (before API call) for live updates
    if (clothingFiles.length > 0) {
        createAssistantPlaceholder({ outfits: [] }); // Empty placeholder
    }

    // Show progress
    if (progressSection) {
        progressSection.style.display = 'block';
        progressFill.style.width = '0%';
        progressText.textContent = 'Starting...';

        // Smooth scroll to progress bar
        setTimeout(() => {
            progressSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
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

        // Add clothing images (de-duplicated by filename)
        const uniqueFiles = new Map();
        clothingFiles.forEach(file => {
            if (!uniqueFiles.has(file.name)) {
                uniqueFiles.set(file.name, file);
            }
        });

        const filesToSubmit = Array.from(uniqueFiles.values());
        filesToSubmit.forEach(file => {
            formData.append('clothing_images', file);
        });

        // Add pre-computed descriptions if available (only for selected files)
        const precomputedDescriptions = {};
        filesToSubmit.forEach((file, index) => {
            if (imageDescriptions.has(file.name)) {
                precomputedDescriptions[index] = imageDescriptions.get(file.name);
            }
        });

        if (Object.keys(precomputedDescriptions).length > 0) {
            formData.append('precomputed_descriptions', JSON.stringify(precomputedDescriptions));
        }

        // Add selfies if provided (up to 3)
        if (selfieFiles && selfieFiles.length > 0) {
            selfieFiles.forEach((file, index) => {
                formData.append('selfies', file);
            });
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

        // Update assistant message with final data (placeholder already created)
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

// ===== Create Assistant Placeholder for Live Updates =====
function createAssistantPlaceholder(data) {
    // Check if placeholder already exists
    const existingPlaceholder = chatMessages.querySelector('.assistant-placeholder');
    if (existingPlaceholder) return; // Already created

    // Show chat history
    chatHistory.style.display = 'block';

    // Remove welcome placeholder if it exists
    const welcomePlaceholder = chatMessages.querySelector('.chat-placeholder');
    if (welcomePlaceholder) {
        welcomePlaceholder.remove();
    }

    // Create NEW placeholder with loading dots
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message assistant-placeholder';

    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'chat-message-assistant';

    // Just show loading dots, no content yet
    assistantBubble.innerHTML = `
        <div class="message-label">DebonAIr</div>
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <div class="outfits-grid"></div>
    `;

    messageDiv.appendChild(assistantBubble);
    chatMessages.appendChild(messageDiv);

    // Scroll to message
    messageDiv.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

// ===== Chat Message Display =====
function addChatMessage(role, content) {
    // Show chat history
    chatHistory.style.display = 'block';

    // Remove welcome placeholder if it exists
    const welcomePlaceholder = chatMessages.querySelector('.chat-placeholder');
    if (welcomePlaceholder) {
        welcomePlaceholder.remove();
    }

    // Check if we're updating an existing assistant placeholder
    const existingAssistantPlaceholder = chatMessages.querySelector('.assistant-placeholder');

    const messageDiv = existingAssistantPlaceholder || document.createElement('div');
    if (!existingAssistantPlaceholder) {
        messageDiv.className = 'chat-message';
    } else {
        messageDiv.classList.remove('assistant-placeholder');
    }

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
        // If updating existing placeholder, get it and update content
        if (existingAssistantPlaceholder) {
            const assistantBubble = existingAssistantPlaceholder.querySelector('.chat-message-assistant');

            // Remove loading dots
            const loadingDots = assistantBubble.querySelector('.loading-dots');
            if (loadingDots) {
                loadingDots.remove();
            }

            // Check if outfits grid already exists (from live preview)
            let existingOutfitsGrid = assistantBubble.querySelector('.outfits-grid');

            // Only rebuild if no existing outfits grid, otherwise preserve it
            if (!existingOutfitsGrid) {
                let bubbleHTML = '<div class="message-label">DebonAIr</div>';

                // Add query response if exists
                if (content.query_response) {
                    bubbleHTML += `<div class="message-text">${escapeHtml(content.query_response)}</div>`;
                }

                // Add outfits grid
                if (content.outfits && content.outfits.length > 0) {
                    bubbleHTML += '<div class="outfits-grid"></div>';
                }

                assistantBubble.innerHTML = bubbleHTML;
                existingOutfitsGrid = assistantBubble.querySelector('.outfits-grid');
            }

            // Update outfit cards with details if they exist
            if (content.outfits && content.outfits.length > 0 && existingOutfitsGrid) {
                content.outfits.forEach(outfit => {
                    let existingCard = existingOutfitsGrid.querySelector(`[data-outfit-number="${outfit.outfit_number}"]`);

                    if (existingCard) {
                        // Update the existing card with full details
                        const details = existingCard.querySelector('.outfit-details');
                        if (details) {
                            // Preserve thumbnails if they exist
                            const thumbnails = details.querySelector('.outfit-thumbnails');

                            details.innerHTML = `
                                <h4>Style</h4>
                                <p>${outfit.reasoning}</p>
                                <h4>How to Wear</h4>
                                <p>${outfit.wearing_instructions}</p>
                                ${outfit.fashion_advice ? `<h4>Fashion Tip</h4><p class="fashion-advice">💡 ${outfit.fashion_advice}</p>` : ''}
                            `;

                            // Re-add thumbnails if they existed
                            if (thumbnails) {
                                details.insertBefore(thumbnails, details.firstChild);
                            }
                        }
                    } else {
                        // Create new card if it doesn't exist
                        const card = createOutfitCard(outfit);
                        existingOutfitsGrid.appendChild(card);
                    }
                });
            }
        } else {
            // Create new message bubble
            const assistantBubble = document.createElement('div');
            assistantBubble.className = 'chat-message-assistant';

            let bubbleHTML = '<div class="message-label">DebonAIr</div>';

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
    }

    // Only append if it's a new message
    if (!existingAssistantPlaceholder) {
        chatMessages.appendChild(messageDiv);
    }

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
    card.setAttribute('data-outfit-number', outfit.outfit_number);

    // Add click handler for 3D magnification
    card.addEventListener('click', (e) => {
        if (!e.target.classList.contains('remove-btn')) {
            magnifyCard(card);
        }
    });

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

        // Add clothing item thumbnails if available
        if (outfit.clothing_items && outfit.clothing_items.length > 0) {
            const thumbnailsContainer = document.createElement('div');
            thumbnailsContainer.className = 'outfit-thumbnails';

            outfit.clothing_items.forEach((itemPath, idx) => {
                const thumbnail = document.createElement('img');
                thumbnail.className = 'outfit-thumbnail';
                thumbnail.src = itemPath;
                thumbnail.alt = `Item ${idx + 1}`;
                thumbnail.loading = 'lazy';
                thumbnailsContainer.appendChild(thumbnail);
            });

            details.appendChild(thumbnailsContainer);
        }

        details.innerHTML += `
            <h4>Style</h4>
            <p>${outfit.reasoning}</p>
            <h4>How to Wear</h4>
            <p>${outfit.wearing_instructions}</p>
            ${outfit.fashion_advice ? `<h4>Fashion Tip</h4><p class="fashion-advice">💡 ${outfit.fashion_advice}</p>` : ''}
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

// ===== 3D Card Magnification =====
function magnifyCard(card) {
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'outfit-card-overlay';

    // Get just the image from the card
    const originalImg = card.querySelector('.outfit-image');
    if (!originalImg) return; // No image to magnify

    // Create magnified image container
    const magnifiedCard = document.createElement('div');
    magnifiedCard.className = 'outfit-card-magnified';

    const img = document.createElement('img');
    img.src = originalImg.src;
    img.alt = originalImg.alt;
    img.className = 'outfit-image-magnified';
    img.style.width = '100%';
    img.style.height = 'auto';
    img.style.display = 'block';
    img.style.borderRadius = 'var(--radius-sm)';

    magnifiedCard.appendChild(img);

    // Add to body
    document.body.appendChild(overlay);
    document.body.appendChild(magnifiedCard);

    // 3D mouse tracking
    function handleMouseMove(e) {
        const rect = magnifiedCard.getBoundingClientRect();
        const cardCenterX = rect.left + rect.width / 2;
        const cardCenterY = rect.top + rect.height / 2;

        // Calculate normalized mouse position (-1 to 1)
        const mouseX = (e.clientX - cardCenterX) / (rect.width / 2);
        const mouseY = (e.clientY - cardCenterY) / (rect.height / 2);

        // Apply 3D rotation (max 20 degrees in both directions)
        const rotateY = mouseX * 20;  // Horizontal mouse movement -> Y-axis rotation
        const rotateX = -mouseY * 20; // Vertical mouse movement -> X-axis rotation

        magnifiedCard.style.transform = `
            translate(-50%, -50%)
            scale(1.5)
            perspective(1000px)
            rotateX(${rotateX}deg)
            rotateY(${rotateY}deg)
        `;
    }

    // Close on overlay click or Escape key
    function closeCard() {
        overlay.remove();
        magnifiedCard.remove();
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('keydown', handleEscape);
        // Restore scroll
        document.body.style.overflow = 'auto';
    }

    function handleEscape(e) {
        if (e.key === 'Escape') {
            closeCard();
        }
    }

    overlay.addEventListener('click', closeCard);
    magnifiedCard.addEventListener('click', closeCard);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('keydown', handleEscape);

    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

// ===== Outfit Placeholder Creation =====
function createOutfitPlaceholders(totalOutfits) {
    const assistantMessages = chatMessages.querySelectorAll('.chat-message-assistant');
    const currentMessage = assistantMessages[assistantMessages.length - 1];

    if (currentMessage) {
        const outfitsGrid = currentMessage.querySelector('.outfits-grid');

        if (outfitsGrid && outfitsGrid.children.length === 0) {
            // Create placeholder cards for all outfits
            for (let i = 1; i <= totalOutfits; i++) {
                const placeholderCard = createPlaceholderOutfitCard(i);
                outfitsGrid.appendChild(placeholderCard);
            }
        }
    }
}

function createPlaceholderOutfitCard(outfitNumber) {
    const card = document.createElement('div');
    card.className = 'outfit-card outfit-card-loading';
    card.setAttribute('data-outfit-number', outfitNumber);

    card.innerHTML = `
        <div class="outfit-header">Outfit ${outfitNumber}</div>
        <div class="outfit-image-placeholder">
            <div class="loading-spinner">
                <div class="spinner-circle"></div>
                <div class="spinner-text">Generating...</div>
            </div>
        </div>
        <div class="outfit-details">
            <p class="outfit-reasoning">Preparing outfit details...</p>
            <p class="outfit-wearing">Instructions will appear once generated</p>
        </div>
    `;

    return card;
}

// ===== Make Functions Global =====
window.removeSelfie = removeSelfie;
window.clearSelfie = clearSelfie;
window.removeClothing = removeClothing;
window.clearClothing = clearClothing;
