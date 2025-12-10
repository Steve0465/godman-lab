// Godman AI WebUI - app.js
// Simple, clean implementation with fetch() only

// ============================================
// Core API Functions
// ============================================

/**
 * Call the Handler API to execute a function
 * @param {string} functionName - Name of the function to execute
 * @param {Object} parameters - Function parameters as object
 * @returns {Promise<Object>} - API response
 */
async function callHandler(functionName, parameters) {
    const response = await fetch('/api/handler', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            function: functionName,
            parameters: parameters
        })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(JSON.stringify(data, null, 2));
    }
    
    return data;
}

/**
 * Get list of all available tools
 * @returns {Promise<Object>} - Tools data
 */
async function listTools() {
    const response = await fetch('/api/handler/tools');
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

/**
 * Load model presets
 * @returns {Promise<Object>} - Presets data
 */
async function loadPresets() {
    const response = await fetch('/api/presets');
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

// ============================================
// UI Helper Functions
// ============================================

/**
 * Update the output display
 * @param {Object|string} content - Content to display
 * @param {boolean} isError - Whether this is an error message
 */
function updateOutput(content, isError = false) {
    const outputElement = document.getElementById('output');
    
    // Format content as JSON if it's an object
    const text = typeof content === 'string' 
        ? content 
        : JSON.stringify(content, null, 2);
    
    outputElement.textContent = text;
    
    // Update colors based on error state
    if (isError) {
        outputElement.classList.remove('text-green-400');
        outputElement.classList.add('text-red-400');
    } else {
        outputElement.classList.remove('text-red-400');
        outputElement.classList.add('text-green-400');
    }
}

/**
 * Show loading state
 * @param {string} message - Loading message
 */
function showLoading(message) {
    updateOutput(`⏳ ${message}\n\nPlease wait...`);
}

/**
 * Display error message
 * @param {Error} error - Error object
 * @param {string} context - Context of the error
 */
function displayError(error, context) {
    const errorMessage = {
        error: context,
        message: error.message,
        timestamp: new Date().toISOString()
    };
    
    updateOutput(errorMessage, true);
}

// ============================================
// Button Handlers
// ============================================

/**
 * Handle Run Tool button click
 */
async function handleRunTool() {
    const functionName = document.getElementById('functionName').value.trim();
    const parametersText = document.getElementById('parameters').value.trim();
    
    // Validate function name
    if (!functionName) {
        updateOutput({
            error: 'Validation Error',
            message: 'Please enter a function name'
        }, true);
        return;
    }
    
    // Parse parameters
    let parameters = {};
    if (parametersText) {
        try {
            parameters = JSON.parse(parametersText);
        } catch (error) {
            updateOutput({
                error: 'JSON Parse Error',
                message: error.message,
                input: parametersText
            }, true);
            return;
        }
    }
    
    // Execute function
    showLoading(`Executing function: ${functionName}`);
    
    try {
        const result = await callHandler(functionName, parameters);
        updateOutput(result);
    } catch (error) {
        displayError(error, 'Handler API Error');
    }
}

/**
 * Handle List Tools button click
 */
async function handleListTools() {
    showLoading('Fetching available tools');
    
    try {
        const result = await listTools();
        updateOutput(result);
    } catch (error) {
        displayError(error, 'List Tools Error');
    }
}

/**
 * Handle Load Presets button click
 */
async function handleLoadPresets() {
    showLoading('Loading model presets');
    
    try {
        const result = await loadPresets();
        updateOutput(result);
    } catch (error) {
        displayError(error, 'Load Presets Error');
    }
}

/**
 * Handle Clear button click
 */
function handleClear() {
    document.getElementById('functionName').value = '';
    document.getElementById('parameters').value = '';
    
    updateOutput({
        message: 'Cleared!',
        ready: true,
        hint: 'Enter a function name and parameters, then click "Run Tool"'
    });
}

/**
 * Handle Copy button click
 */
async function handleCopy() {
    const output = document.getElementById('output').textContent;
    const copyBtn = document.getElementById('copyOutputBtn');
    
    try {
        await navigator.clipboard.writeText(output);
        
        // Show success feedback
        const originalText = copyBtn.textContent;
        copyBtn.textContent = '✅ Copied!';
        copyBtn.classList.add('bg-green-500', 'text-white');
        copyBtn.classList.remove('bg-gray-200', 'text-gray-700');
        
        setTimeout(() => {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('bg-green-500', 'text-white');
            copyBtn.classList.add('bg-gray-200', 'text-gray-700');
        }, 2000);
        
    } catch (error) {
        displayError(error, 'Copy Failed');
    }
}

// ============================================
// Event Listeners & Initialization
// ============================================

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    // Attach button event listeners
    document.getElementById('runToolBtn').addEventListener('click', handleRunTool);
    document.getElementById('listToolsBtn').addEventListener('click', handleListTools);
    document.getElementById('loadPresetsBtn').addEventListener('click', handleLoadPresets);
    document.getElementById('clearBtn').addEventListener('click', handleClear);
    document.getElementById('copyOutputBtn').addEventListener('click', handleCopy);
    
    // Allow Enter key to trigger run
    document.getElementById('functionName').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleRunTool();
        }
    });
    
    // Initial welcome message
    updateOutput({
        message: 'Welcome to Godman AI WebUI Dashboard!',
        status: 'ready',
        available_actions: [
            'Click "Run Tool" to execute a function',
            'Click "List Tools" to see available tools',
            'Click "Load Presets" to view model presets'
        ],
        server: 'http://localhost:8000',
        timestamp: new Date().toISOString()
    });
    
    console.log('🚀 Godman AI WebUI Dashboard Loaded');
});
