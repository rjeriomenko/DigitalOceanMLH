// State management
let selfieFile = null;
let clothingFiles = [];

// DOM elements
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

// File input handlers
selfieInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        selfieFile = file;
        displaySelfiePreview(file);
        updateFileLabel(selfieInput, file.name);
    }
});

clothingInput.addEventListener('change', (e) => {
    clothingFiles = Array.from(e.target.files);
    displayClothingPreviews(clothingFiles);
    updateFileLabel(clothingInput, `${clothingFiles.length} file(s) selected`);
});

// Update file label text
function updateFileLabel(input, text) {
    const label = input.nextElementSibling;
    const labelText = label.querySelector('.file-label-text');
    labelText.textContent = text;
}

// Display selfie preview
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

// Display clothing previews
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

// Remove selfie
function removeSelfie() {
    selfieFile = null;
    selfieInput.value = '';
    selfiePreview.innerHTML = '';
    updateFileLabel(selfieInput, 'Choose selfie...');
}

// Remove clothing item
function removeClothing(index) {
    clothingFiles.splice(index, 1);
    displayClothingPreviews(clothingFiles);

    // Update file input
    const dt = new DataTransfer();
    clothingFiles.forEach(file => dt.items.add(file));
    clothingInput.files = dt.files;

    if (clothingFiles.length === 0) {
        updateFileLabel(clothingInput, 'Choose clothing images...');
    } else {
        updateFileLabel(clothingInput, `${clothingFiles.length} file(s) selected`);
    }
}

// Generate outfits
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

        // Make API request
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate outfits');
        }

        // Display results
        displayResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        // Reset button state
        btnText.style.display = 'inline-block';
        spinner.style.display = 'none';
        generateBtn.disabled = false;
    }
});

// Display results
function displayResults(data) {
    resultsSection.style.display = 'block';

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

// Create outfit card
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

// Show error
function showError(message) {
    errorSection.style.display = 'block';
    errorMessage.textContent = `❌ ${message}`;
    errorSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Hide error
function hideError() {
    errorSection.style.display = 'none';
    errorMessage.textContent = '';
}

// Make remove functions global
window.removeSelfie = removeSelfie;
window.removeClothing = removeClothing;
