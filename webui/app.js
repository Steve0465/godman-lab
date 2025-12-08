// Godman AI WebUI - app.js
// Handles all dashboard interactions and API calls

// Get DOM elements
const functionNameInput = document.getElementById('functionName');
const parametersInput = document.getElementById('parameters');
const outputElement = document.getElementById('output');
const runToolBtn = document.getElementById('runToolBtn');
const listToolsBtn = document.getElementById('listToolsBtn');
const loadPresetsBtn = document.getElementById('loadPresetsBtn');
const clearBtn = document.getElementById('clearBtn');
const copyOutputBtn = document.getElementById('copyOutputBtn');

// Helper function to display output
function displayOutput(text, isError = false) {
    outputElement.textContent = text;
    if (isError) {
        outputElement.classList.remove('text-green-400');
        outputElement.classList.add('text-red-400');
    } else {
        outputElement.classList.remove('text-red-400');
        outputElement.classList.add('text-green-400');
    }
}

// Helper function to format JSON
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// Run Tool - Execute the selected function
async function runTool() {
    const functionName = functionNameInput.value.trim();
    const parametersText = parametersInput.value.trim();
    
    if (!functionName) {
        displayOutput('❌ Error: Please enter a function name', true);
        return;
    }
    
    // Parse parameters
    let parameters = {};
    if (parametersText) {
        try {
            parameters = JSON.parse(parametersText);
        } catch (error) {
            displayOutput(`❌ JSON Parse Error: ${error.message}`, true);
            return;
        }
    }
    
    // Display loading state
    displayOutput(`⏳ Executing function "${functionName}"...\n\nParameters:\n${formatJSON(parameters)}\n\nPlease wait...`);
    
    try {
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
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            const output = `✅ SUCCESS

Function: ${functionName}
Status: ${result.status}
Execution Time: ${result.execution_time}s
Timestamp: ${result.timestamp}

Result:
${formatJSON(result.result)}`;
            displayOutput(output);
        } else {
            const errorOutput = `❌ ERROR

Function: ${functionName}
Status: ${result.status || 'error'}

Error Details:
${formatJSON(result.error || result.detail || result)}`;
            displayOutput(errorOutput, true);
        }
        
    } catch (error) {
        displayOutput(`❌ Network Error: ${error.message}`, true);
    }
}

// List Tools - Get all available tools
async function listTools() {
    displayOutput('⏳ Fetching available tools...');
    
    try {
        const response = await fetch('/api/handler/tools');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.count === 0) {
            displayOutput('ℹ️ No tools registered\n\nRegister tools using the @tool decorator in Python.');
            return;
        }
        
        let output = `📋 AVAILABLE TOOLS (${data.count})\n\n`;
        
        for (const [name, info] of Object.entries(data.tools)) {
            output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
            output += `🔧 ${name}\n`;
            output += `   Description: ${info.description || 'No description'}\n`;
            
            if (Object.keys(info.schema).length > 0) {
                output += `   Parameters:\n`;
                for (const [param, type] of Object.entries(info.schema)) {
                    output += `     • ${param}: ${type}\n`;
                }
            } else {
                output += `   Parameters: None\n`;
            }
            
            output += `   Type: ${info.has_command ? 'Command' : 'Function'}\n`;
        }
        
        output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        output += `\nTotal: ${data.count} tools available`;
        
        displayOutput(output);
        
    } catch (error) {
        displayOutput(`❌ Error fetching tools: ${error.message}`, true);
    }
}

// Load Presets - Get model presets
async function loadPresets() {
    displayOutput('⏳ Loading model presets...');
    
    try {
        const response = await fetch('/api/presets');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.presets || data.presets.length === 0) {
            displayOutput('ℹ️ No presets configured');
            return;
        }
        
        let output = `🎨 MODEL PRESETS (${data.presets.length})\n\n`;
        
        for (const preset of data.presets) {
            output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
            output += `📦 ${preset.name}\n`;
            output += `   ID: ${preset.id}\n`;
            output += `   Model: ${preset.model}\n`;
            output += `   Prompt:\n`;
            
            // Wrap prompt text
            const promptLines = preset.prompt.match(/.{1,60}/g) || [preset.prompt];
            promptLines.forEach(line => {
                output += `     ${line}\n`;
            });
            
            output += `\n`;
        }
        
        output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        output += `\nTotal: ${data.presets.length} presets available`;
        
        displayOutput(output);
        
    } catch (error) {
        displayOutput(`❌ Error loading presets: ${error.message}`, true);
    }
}

// Clear - Reset all inputs and output
function clear() {
    functionNameInput.value = '';
    parametersInput.value = '';
    displayOutput(`✨ Cleared!

Ready for new commands.
Enter a function name and parameters, then click "Run Tool".

Try clicking "List Tools" to see what's available.`);
}

// Copy Output - Copy output text to clipboard
async function copyOutput() {
    try {
        await navigator.clipboard.writeText(outputElement.textContent);
        
        // Show feedback
        const originalText = copyOutputBtn.textContent;
        copyOutputBtn.textContent = '✅ Copied!';
        copyOutputBtn.classList.add('bg-green-500', 'text-white');
        copyOutputBtn.classList.remove('bg-gray-200', 'text-gray-700');
        
        setTimeout(() => {
            copyOutputBtn.textContent = originalText;
            copyOutputBtn.classList.remove('bg-green-500', 'text-white');
            copyOutputBtn.classList.add('bg-gray-200', 'text-gray-700');
        }, 2000);
        
    } catch (error) {
        displayOutput(`❌ Failed to copy: ${error.message}`, true);
    }
}

// Event Listeners
runToolBtn.addEventListener('click', runTool);
listToolsBtn.addEventListener('click', listTools);
loadPresetsBtn.addEventListener('click', loadPresets);
clearBtn.addEventListener('click', clear);
copyOutputBtn.addEventListener('click', copyOutput);

// Allow Enter key in function name input to trigger run
functionNameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        runTool();
    }
});

// Initialize - Display welcome message on load
console.log('🚀 Godman AI WebUI Dashboard Loaded');
console.log('Ready to execute tools via Handler API');
