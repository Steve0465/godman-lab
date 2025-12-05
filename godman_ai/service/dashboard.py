"""
Web Dashboard for GodmanAI

Simple HTML dashboard for system monitoring.
"""

import logging

logger = logging.getLogger(__name__)

# Simple HTML dashboard template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>GodmanAI Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric {
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background: #e8f5e9;
            border-radius: 4px;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2e7d32;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #f0f0f0;
            font-weight: bold;
        }
        .status-ok {
            color: #4CAF50;
        }
        .status-error {
            color: #f44336;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
        }
        button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <h1>🤖 GodmanAI Dashboard</h1>
    
    <div class="section">
        <h2>System Health</h2>
        <div id="health-metrics">Loading...</div>
        <button onclick="refreshHealth()">Refresh</button>
    </div>
    
    <div class="section">
        <h2>Queue Status</h2>
        <div id="queue-status">Loading...</div>
        <button onclick="refreshQueue()">Refresh</button>
    </div>
    
    <div class="section">
        <h2>Loaded Tools</h2>
        <div id="tools-list">Loading...</div>
        <button onclick="refreshTools()">Refresh</button>
    </div>
    
    <div class="section">
        <h2>Memory Store</h2>
        <div id="memory-status">Loading...</div>
        <button onclick="refreshMemory()">Refresh</button>
    </div>
    
    <script>
        async function fetchJSON(url) {
            const response = await fetch(url);
            return await response.json();
        }
        
        async function refreshHealth() {
            try {
                const health = await fetchJSON('/os/health');
                const html = Object.entries(health).map(([key, value]) => 
                    `<div class="metric">
                        <div class="metric-label">${key}</div>
                        <div class="metric-value">${JSON.stringify(value)}</div>
                    </div>`
                ).join('');
                document.getElementById('health-metrics').innerHTML = html;
            } catch (e) {
                document.getElementById('health-metrics').innerHTML = '<p class="status-error">Error loading health metrics</p>';
            }
        }
        
        async function refreshQueue() {
            try {
                const queue = await fetchJSON('/queue/status');
                document.getElementById('queue-status').innerHTML = 
                    `<div class="metric">
                        <div class="metric-label">Pending Jobs</div>
                        <div class="metric-value">${queue.size}</div>
                    </div>`;
            } catch (e) {
                document.getElementById('queue-status').innerHTML = '<p class="status-error">Error loading queue status</p>';
            }
        }
        
        async function refreshTools() {
            try {
                const data = await fetchJSON('/tools');
                const html = `<table>
                    <tr><th>Tool Name</th><th>Description</th></tr>
                    ${data.tools.map(tool => 
                        `<tr><td>${tool.name}</td><td>${tool.description}</td></tr>`
                    ).join('')}
                </table>`;
                document.getElementById('tools-list').innerHTML = html;
            } catch (e) {
                document.getElementById('tools-list').innerHTML = '<p class="status-error">Error loading tools</p>';
            }
        }
        
        async function refreshMemory() {
            try {
                const state = await fetchJSON('/os/state');
                document.getElementById('memory-status').innerHTML = 
                    `<div class="metric">
                        <div class="metric-label">Status</div>
                        <div class="metric-value">Active</div>
                    </div>`;
            } catch (e) {
                document.getElementById('memory-status').innerHTML = '<p class="status-error">Error loading memory status</p>';
            }
        }
        
        // Auto-refresh every 5 seconds
        setInterval(() => {
            refreshHealth();
            refreshQueue();
        }, 5000);
        
        // Initial load
        refreshHealth();
        refreshQueue();
        refreshTools();
        refreshMemory();
    </script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    """Return the dashboard HTML"""
    return DASHBOARD_HTML
