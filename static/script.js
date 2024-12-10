let currentMode = 'image';
let currentImage = null;
let currentLanguage = 'en';
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const imagePreview = document.getElementById('imagePreview');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorMessage = document.getElementById('errorMessage');
const resultsSection = document.querySelector('.results-section');
const resultsContainer = document.getElementById('resultsContainer');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const historyContainer = document.getElementById('historyContainer');

// Translations
const translations = {
    en: {
        title: 'Azure Vision Analyzer',
        subtitle: 'Advanced image analysis powered by Azure Computer Vision',
        imageRecognition: 'Image Recognition',
        textDetection: 'Text Detection',
        uploadText: 'Drop your image here or click to upload',
        analyze: 'Analyze Image',
        loading: 'Analyzing...',
        detectedObjects: 'Detected Objects',
        detectedText: 'Detected Text',
        colors: 'Colors',
        noText: 'No text detected in the image',
        clearHistory: 'Clear History',
        history: 'Analysis History',
        errorOccurred: 'An error occurred',
        accentColor: 'Accent Color',
        blackAndWhite: 'Black and White',
        yes: 'Yes',
        no: 'No',
        noImageError: 'Please select an image',
        description: 'Description',
        dominantColors: 'Dominant Colors',
        objects: 'Objects',
        uploadImage: 'Upload Image',
        analyzeImage: 'Analyze',
        imageMode: 'Image Analysis',
        textMode: 'Text Detection',
        analyzing: 'Analyzing'
    },
    fr: {
        title: 'Analyseur de Vision Azure',
        subtitle: 'Analyse d\'images avancée propulsée par Azure Computer Vision',
        imageRecognition: 'Reconnaissance d\'Image',
        textDetection: 'Détection de Texte',
        uploadText: 'Déposez votre image ici ou cliquez pour télécharger',
        analyze: 'Analyser l\'Image',
        loading: 'Analyse en cours...',
        detectedObjects: 'Objets Détectés',
        detectedText: 'Texte Détecté',
        colors: 'Couleurs',
        noText: 'Aucun texte détecté dans l\'image',
        clearHistory: 'Effacer l\'Historique',
        history: 'Historique d\'Analyse',
        errorOccurred: 'Une erreur est survenue',
        accentColor: 'Couleur d\'Accent',
        blackAndWhite: 'Noir et Blanc',
        yes: 'Oui',
        no: 'Non',
        noImageError: 'Veuillez sélectionner une image',
        description: 'Description',
        dominantColors: 'Couleurs Dominantes',
        objects: 'Objets',
        uploadImage: 'Télécharger l\'Image',
        analyzeImage: 'Analyser',
        imageMode: 'Analyse d\'Image',
        textMode: 'Détection de Texte',
        analyzing: 'Analyse en cours'
    },
    ar: {
        title: 'محلل الرؤية من Azure',
        subtitle: 'تحليل متقدم للصور مدعوم بتقنية Azure للرؤية الحاسوبية',
        imageRecognition: 'التعرف على الصور',
        textDetection: 'اكتشاف النص',
        uploadText: 'اسحب الصورة هنا أو انقر للتحميل',
        analyze: 'تحليل الصورة',
        loading: 'جاري التحليل...',
        detectedObjects: 'الكائنات المكتشفة',
        detectedText: 'النص المكتشف',
        colors: 'الألوان',
        noText: 'لم يتم اكتشاف نص في الصورة',
        clearHistory: 'مسح السجل',
        history: 'السجل',
        errorOccurred: 'حدث خطأ',
        accentColor: 'اللون المميز',
        blackAndWhite: 'أبيض وأسود',
        yes: 'نعم',
        no: 'لا',
        noImageError: 'يرجى اختيار صورة',
        description: 'الوصف',
        dominantColors: 'الألوان السائدة',
        objects: 'الأشياء',
        uploadImage: 'رفع صورة',
        analyzeImage: 'تحليل',
        imageMode: 'تحليل الصورة',
        textMode: 'اكتشاف النص',
        analyzing: 'جاري التحليل'
    }
};

// Language handling
const languageSelector = document.querySelector('.language-selector');
const languageDropdown = languageSelector.querySelector('.language-dropdown');
const languageBtn = languageSelector.querySelector('.language-btn');
const langOptions = languageDropdown.querySelectorAll('.lang-option');

// Check for saved language preference
const savedLanguage = localStorage.getItem('language') || 'en';
langOptions.forEach(option => {
    if (option.dataset.lang === savedLanguage) {
        option.classList.add('selected');
        languageBtn.querySelector('.current-lang').textContent = option.querySelector('.lang-code').textContent;
    }
});

languageBtn.addEventListener('click', () => {
    languageDropdown.classList.toggle('open');
});

langOptions.forEach(option => {
    option.addEventListener('click', () => {
        langOptions.forEach(opt => opt.classList.remove('selected'));
        option.classList.add('selected');
        languageBtn.querySelector('.current-lang').textContent = option.querySelector('.lang-code').textContent;
        setLanguage(option.dataset.lang);
        localStorage.setItem('language', option.dataset.lang);
        languageDropdown.classList.remove('open');
    });
});

function setLanguage(language) {
    document.documentElement.lang = language;
    document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
    currentLanguage = language;
    
    // Update all translatable elements
    document.querySelector('.header h1').textContent = translations[language].title;
    document.querySelector('.header p').textContent = translations[language].subtitle;
    document.querySelectorAll('.mode-btn')[0].textContent = translations[language].imageRecognition;
    document.querySelectorAll('.mode-btn')[1].textContent = translations[language].textDetection;
    document.querySelector('.upload-area p').textContent = translations[language].uploadText;
    document.querySelector('.analyze-btn').textContent = translations[language].analyze;
    document.querySelector('#resultsTitle').textContent = translations[language].analysisResults;
    document.querySelector('#historyTitle').textContent = translations[language].history;
    document.querySelector('#clearHistoryBtn').textContent = translations[language].clearHistory;
    document.querySelector('#analyzingText').textContent = translations[language].analyzing;
    
    // Update dynamic content if it exists
    const loadingElement = document.querySelector('.loading-overlay p');
    if (loadingElement) {
        loadingElement.textContent = translations[language].loading;
    }
}

// Mode selection
document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelector('.mode-btn.active').classList.remove('active');
        btn.classList.add('active');
        currentMode = btn.dataset.mode;
        resetUI();
    });
});

// Drag and drop handling
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

dropZone.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                currentImage = e.target.result;
                imagePreview.src = currentImage;
                imagePreview.style.display = 'block';
                analyzeBtn.disabled = false;
            };
            reader.readAsDataURL(file);
        } else {
            showError(translations[currentLanguage].noImageError);
        }
    }
}

// Analysis handling
analyzeBtn.addEventListener('click', async () => {
    if (!currentImage) {
        showError(translations[currentLanguage].noImageError);
        return;
    }

    const mode = document.querySelector('.mode-btn.active').dataset.mode;
    document.querySelector('.spinner-container').style.display = 'flex';
    analyzeBtn.disabled = true;

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: currentImage,
                mode: mode,
                language: currentLanguage
            })
        });

        if (!response.ok) throw new Error(translations[currentLanguage].errorOccurred);

        const data = await response.json();
        displayResults(data);
        saveToHistory(data);
    } catch (error) {
        showError(translations[currentLanguage].errorOccurred);
    } finally {
        document.querySelector('.spinner-container').style.display = 'none';
        analyzeBtn.disabled = false;
    }
});

function displayResults(data) {
    resultsSection.style.display = 'block';
    resultsContainer.innerHTML = '';

    const resultTitle = document.createElement('h2');
    resultTitle.className = 'results-title';
    resultTitle.textContent = translations[currentLanguage].analysisResults;
    resultsContainer.appendChild(resultTitle);

    if (currentMode === 'image') {
        // Display image description
        if (data.description) {
            const descriptionSection = document.createElement('div');
            descriptionSection.className = 'result-item';
            
            const descriptionTitle = document.createElement('h3');
            descriptionTitle.innerHTML = `<i class="fas fa-info-circle"></i> ${translations[currentLanguage].description}`;
            descriptionSection.appendChild(descriptionTitle);

            const descriptionText = document.createElement('p');
            descriptionText.className = 'description-text';
            descriptionText.textContent = data.description;
            descriptionSection.appendChild(descriptionText);

            resultsContainer.appendChild(descriptionSection);
        }

        // Display colors
        if (data.colors) {
            const colorSection = document.createElement('div');
            colorSection.className = 'result-item';
            
            const colorTitle = document.createElement('h3');
            colorTitle.innerHTML = `<i class="fas fa-palette"></i> ${translations[currentLanguage].colors}`;
            colorSection.appendChild(colorTitle);

            // Dominant Colors
            if (data.colors.dominant_colors && data.colors.dominant_colors.length > 0) {
                const dominantTitle = document.createElement('h4');
                dominantTitle.textContent = translations[currentLanguage].dominantColors;
                colorSection.appendChild(dominantTitle);

                const dominantGrid = document.createElement('div');
                dominantGrid.className = 'color-grid';
                data.colors.dominant_colors.forEach(color => {
                    const colorBox = document.createElement('div');
                    colorBox.className = 'color-box';
                    colorBox.style.backgroundColor = color.toLowerCase();
                    
                    const colorTooltip = document.createElement('span');
                    colorTooltip.className = 'color-tooltip';
                    colorTooltip.textContent = color;
                    
                    colorBox.appendChild(colorTooltip);
                    dominantGrid.appendChild(colorBox);
                });
                colorSection.appendChild(dominantGrid);
            }

            // Accent Color
            if (data.colors.accent_color) {
                const accentTitle = document.createElement('h4');
                accentTitle.textContent = translations[currentLanguage].accentColor;
                colorSection.appendChild(accentTitle);

                const accentGrid = document.createElement('div');
                accentGrid.className = 'color-grid';
                
                const accentBox = document.createElement('div');
                accentBox.className = 'color-box accent-color';
                accentBox.style.backgroundColor = data.colors.accent_color.toLowerCase();
                
                const accentTooltip = document.createElement('span');
                accentTooltip.className = 'color-tooltip';
                accentTooltip.textContent = data.colors.accent_color;
                
                accentBox.appendChild(accentTooltip);
                accentGrid.appendChild(accentBox);
                colorSection.appendChild(accentGrid);
            }

            // Black and White Information
            if (data.colors.hasOwnProperty('is_bw')) {
                const bwInfo = document.createElement('p');
                bwInfo.className = 'bw-info';
                bwInfo.innerHTML = `<i class="fas fa-adjust"></i> ${translations[currentLanguage].blackAndWhite}: ${data.colors.is_bw ? translations[currentLanguage].yes : translations[currentLanguage].no}`;
                colorSection.appendChild(bwInfo);
            }

            resultsContainer.appendChild(colorSection);
        }

        // Display objects
        if (data.objects && data.objects.length > 0) {
            const objectsSection = document.createElement('div');
            objectsSection.className = 'result-item';
            
            const objectTitle = document.createElement('h3');
            objectTitle.innerHTML = `<i class="fas fa-cube"></i> ${translations[currentLanguage].objects}`;
            objectsSection.appendChild(objectTitle);

            data.objects.forEach(obj => {
                const objDiv = document.createElement('div');
                objDiv.className = 'object-item';
                
                const confidence = Math.round(obj.confidence * 100);
                objDiv.innerHTML = `
                    <div class="text-content">
                        <p>${obj.name}</p>
                        <span class="confidence-percentage">${confidence}%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                `;
                objectsSection.appendChild(objDiv);
            });
            
            resultsContainer.appendChild(objectsSection);
        }
    } else {
        // Display OCR results
        if (data.text_results && data.text_results.length > 0) {
            const textSection = document.createElement('div');
            textSection.className = 'result-item';
            
            const textTitle = document.createElement('h3');
            textTitle.innerHTML = `<i class="fas fa-font"></i> ${translations[currentLanguage].detectedText}`;
            textSection.appendChild(textTitle);

            data.text_results.forEach(item => {
                const textDiv = document.createElement('div');
                textDiv.className = 'text-item';
                
                const confidence = Math.round(item.confidence * 100);
                textDiv.innerHTML = `
                    <div class="text-content">
                        <p>${item.text}</p>
                        <span class="confidence-percentage">${confidence}%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidence}%"></div>
                    </div>
                `;
                textSection.appendChild(textDiv);
            });
            
            resultsContainer.appendChild(textSection);
        } else {
            resultsContainer.innerHTML = `<p class="no-text-message">${translations[currentLanguage].noText}</p>`;
        }
    }
}

// Save analysis to localStorage
function saveToHistory(data) {
    const historyItem = {
        timestamp: new Date().toISOString(),
        mode: currentMode,
        results: data,
        image: currentImage ? currentImage.name : 'Unknown',
        imageData: imagePreview.src // Store base64 image data
    };

    let history = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
    history.unshift(historyItem);
    
    // Keep only the last 10 items
    if (history.length > 10) {
        history = history.slice(0, 10);
    }
    
    localStorage.setItem('analysisHistory', JSON.stringify(history));
    loadHistory();
}

// Load history from localStorage
async function loadHistory() {
    const historyContainer = document.getElementById('historyContainer');
    historyContainer.innerHTML = '';
    
    const history = JSON.parse(localStorage.getItem('analysisHistory') || '[]');
    
    history.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const timestamp = new Date(item.timestamp).toLocaleString();
        const mode = item.mode === 'image' ? 'Image Analysis' : 'Text Detection';
        
        historyItem.innerHTML = `
            <img src="${item.imageData}" alt="Analyzed image" class="history-image">
            <div class="history-content">
                <div class="history-timestamp">${timestamp}</div>
                <div class="history-mode">${mode}</div>
                <div class="history-results">
                    ${formatHistoryResults(item.results, item.mode)}
                </div>
            </div>
        `;
        
        historyContainer.appendChild(historyItem);
    });
}

function formatHistoryResults(results, mode) {
    if (mode === 'image') {
        let output = '';
        if (results.colors && results.colors.length > 0) {
            output += '<div class="history-colors">';
            results.colors.forEach(color => {
                output += `<div class="history-color-box" style="background-color: ${color.toLowerCase()}"></div>`;
            });
            output += '</div>';
        }
        if (results.objects && results.objects.length > 0) {
            output += `<div>Objects: ${results.objects.map(obj => obj.name).join(', ')}</div>`;
        }
        return output;
    } else {
        return results.text_results && results.text_results.length > 0 
            ? results.text_results.map(item => item.text).join(' ') 
            : 'No text detected';
    }
}

// Clear history
document.getElementById('clearHistoryBtn').addEventListener('click', () => {
    localStorage.removeItem('analysisHistory');
    loadHistory();
});

// Theme toggle functionality
const themeToggle = document.querySelector('.theme-toggle');
const lightIcon = themeToggle.querySelector('.light-icon');
const darkIcon = themeToggle.querySelector('.dark-icon');

// Check for saved theme preference
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
updateThemeIcon(savedTheme);

themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
});

function updateThemeIcon(theme) {
    if (theme === 'light') {
        lightIcon.style.display = 'block';
        darkIcon.style.display = 'none';
    } else {
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'block';
    }
}

// Load history on page load
loadHistory();

function showError(message) {
    errorMessage.textContent = message;
    document.getElementById('errorToast').style.display = 'block';
    setTimeout(() => {
        document.getElementById('errorToast').style.display = 'none';
    }, 3000);
}

function resetUI() {
    imagePreview.style.display = 'none';
    analyzeBtn.disabled = true;
    resultsSection.style.display = 'none';
    resultsContainer.innerHTML = '';
}

// Add scroll behavior for nav buttons
let lastScrollPosition = window.pageYOffset;
const navButtons = document.querySelector('.nav-buttons');

window.addEventListener('scroll', () => {
    const currentScrollPosition = window.pageYOffset;
    
    if (currentScrollPosition > lastScrollPosition && currentScrollPosition > 50) {
        // Scrolling down - hide buttons
        navButtons.classList.add('nav-hidden');
    } else {
        // Scrolling up - show buttons
        navButtons.classList.remove('nav-hidden');
    }
    
    lastScrollPosition = currentScrollPosition;
});

// Add image URL input handling
const imageUrlInput = document.getElementById('imageUrlInput');
const imageUrlBtn = document.getElementById('imageUrlBtn');

imageUrlBtn.addEventListener('click', () => {
    const imageUrl = imageUrlInput.value.trim();
    if (imageUrl) {
        fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image_url: imageUrl,
                mode: currentMode,
                language: currentLanguage
            })
        })
        .then(response => {
            if (!response.ok) throw new Error(translations[currentLanguage].errorOccurred);
            return response.json();
        })
        .then(data => {
            displayResults(data);
            saveToHistory(data);
        })
        .catch(error => {
            showError(translations[currentLanguage].errorOccurred);
        });
    } else {
        showError(translations[currentLanguage].noImageError);
    }
});