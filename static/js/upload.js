/**
 * PDF2MD Upload Page
 */

// State
let selectedFile = null;
let statusCheckInterval = null;

// DOM Elements
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const errorSection = document.getElementById('error-section');

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const convertBtn = document.getElementById('convert-btn');
const progressMessage = document.getElementById('progress-message');
const errorMessage = document.getElementById('error-message');
const retryBtn = document.getElementById('retry-btn');
const themeToggle = document.getElementById('theme-toggle');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initEventListeners();
});

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Event Listeners
function initEventListeners() {
    themeToggle.addEventListener('click', toggleTheme);

    // Drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('click', (e) => {
        // Prevent double trigger when clicking on label or input
        if (e.target.closest('.file-input-label') || e.target === fileInput) {
            return;
        }
        fileInput.click();
    });

    // File input
    fileInput.addEventListener('change', handleFileSelect);

    // Convert button
    convertBtn.addEventListener('click', startConversion);

    // Retry button
    retryBtn.addEventListener('click', resetToUpload);
}

// Drag and Drop Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
}

function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('PDFファイルのみ対応しています');
        return;
    }

    selectedFile = file;
    fileName.textContent = file.name;
    convertBtn.disabled = false;
}

// Conversion
async function startConversion() {
    if (!selectedFile) return;

    showSection('progress');
    progressMessage.textContent = 'アップロード中...';

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'アップロードに失敗しました');
        }

        const data = await response.json();
        
        // If cached, redirect immediately
        if (data.cached || data.status === 'done') {
            window.location.href = `/view/${data.task_id}`;
            return;
        }

        // Start polling for status
        startStatusPolling(data.task_id);

    } catch (error) {
        showError(error.message);
    }
}

function startStatusPolling(taskId) {
    progressMessage.textContent = '変換中...';
    
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${taskId}`);
            if (!response.ok) {
                throw new Error('ステータスの取得に失敗しました');
            }

            const data = await response.json();

            switch (data.status) {
                case 'pending':
                    progressMessage.textContent = '変換を準備中...';
                    break;
                case 'processing':
                    progressMessage.textContent = '変換中...';
                    break;
                case 'done':
                    clearInterval(statusCheckInterval);
                    // Redirect to viewer page
                    window.location.href = `/view/${taskId}`;
                    break;
                case 'error':
                    clearInterval(statusCheckInterval);
                    showError(data.error_message || '変換中にエラーが発生しました');
                    break;
            }
        } catch (error) {
            clearInterval(statusCheckInterval);
            showError(error.message);
        }
    }, 1000);
}

// UI Helpers
function showSection(section) {
    uploadSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    switch (section) {
        case 'upload':
            uploadSection.classList.remove('hidden');
            break;
        case 'progress':
            progressSection.classList.remove('hidden');
            break;
        case 'error':
            errorSection.classList.remove('hidden');
            break;
    }
}

function showError(message) {
    errorMessage.textContent = message;
    showSection('error');
}

function resetToUpload() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }

    selectedFile = null;
    fileInput.value = '';
    fileName.textContent = '';
    convertBtn.disabled = true;

    showSection('upload');
}
