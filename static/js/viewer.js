/**
 * PDF2MD Document Viewer
 */

// Get task_id from URL
const pathParts = window.location.pathname.split('/');
const taskId = pathParts[pathParts.length - 1];

// DOM Elements
const loadingEl = document.getElementById('loading');
const contentEl = document.getElementById('content');
const errorEl = document.getElementById('error');
const errorMessageEl = document.getElementById('error-message');
const themeToggle = document.getElementById('theme-toggle');
const downloadBtn = document.getElementById('download-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initEventListeners();
    loadDocument();
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
    downloadBtn.addEventListener('click', downloadMarkdown);
}

// Load document
async function loadDocument() {
    try {
        // Get task status first
        const statusResponse = await fetch(`/api/status/${taskId}`);
        if (!statusResponse.ok) {
            throw new Error('Document not found');
        }
        
        const status = await statusResponse.json();
        
        if (status.status !== 'done') {
            throw new Error('Document conversion not completed');
        }
        
        // Fetch markdown content
        const mdResponse = await fetch(`/api/markdown/${taskId}`);
        if (!mdResponse.ok) {
            throw new Error('Failed to load document');
        }
        
        const markdown = await mdResponse.text();
        
        // Configure marked
        const renderer = new marked.Renderer();
        renderer.image = function(href, title, text) {
            const src = typeof href === 'object' ? href.href : href;
            const imgTitle = typeof href === 'object' ? href.title : title;
            const imgText = typeof href === 'object' ? href.text : text;
            return `<img src="${src}" alt="${imgText || ''}" title="${imgTitle || ''}" loading="lazy">`;
        };
        
        marked.setOptions({
            renderer: renderer,
            breaks: true,
            gfm: true,
        });
        
        // Render content with title
        const title = status.title || 'Document';
        contentEl.innerHTML = `<h2 class="doc-title">${title}</h2>${marked.parse(markdown)}`;
        
        // Update page title
        document.title = `${title} - PDF2MD`;
        
        // Show content
        showContent();
        
    } catch (error) {
        showError(error.message);
    }
}

function downloadMarkdown() {
    window.location.href = `/api/download/${taskId}`;
}

// UI State
function showContent() {
    loadingEl.classList.add('hidden');
    errorEl.classList.add('hidden');
    contentEl.classList.remove('hidden');
}

function showError(message) {
    loadingEl.classList.add('hidden');
    contentEl.classList.add('hidden');
    errorMessageEl.textContent = message;
    errorEl.classList.remove('hidden');
}
