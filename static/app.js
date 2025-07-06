// AWS ADFS GUI - Enhanced JavaScript

class AWSADFSApp {
    constructor() {
        this.ws = null;
        this.connectedProfiles = new Set();
        this.devProfilesSelected = false;
        this.commandHistory = [];
        this.maxHistorySize = 100;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupWebSocket();
        this.loadSettings();
        this.loadHistory();
    }

    setupEventListeners() {
        // Select Dev button
        document.getElementById('selectDevBtn').addEventListener('click', () => {
            this.toggleDevProfiles();
        });

        // Execute command
        document.getElementById('executeBtn').addEventListener('click', () => {
            this.executeCommand();
        });

        // Command input enter key
        document.getElementById('commandInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeCommand();
            }
        });

        // Settings button
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettings();
        });

        // History button
        document.getElementById('historyBtn').addEventListener('click', () => {
            this.showHistory();
        });

        // Save settings
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Profile checkboxes
        document.querySelectorAll('.profile-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.toggleProfile(e.target.value, e.target.checked);
            });
        });
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateStatus('Connected', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('Disconnected', 'error');
            // Try to reconnect after 3 seconds
            setTimeout(() => this.setupWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('Error', 'error');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'connection_status':
                this.updateConnectionStatus(data.profile, data.status);
                break;
            case 'command_output':
                this.updateCommandOutput(data.profile, data.output, data.is_error);
                break;
            case 'command_complete':
                this.commandComplete(data.profile, data.success, data.duration);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    toggleDevProfiles() {
        const selectDevBtn = document.getElementById('selectDevBtn');
        const devProfiles = ['aws-dev-eu', 'aws-dev-sg'];

        if (this.devProfilesSelected) {
            // Disconnect dev profiles
            this.devProfilesSelected = false;
            selectDevBtn.classList.remove('active');
            selectDevBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Select Dev';

            devProfiles.forEach(profile => {
                this.disconnectProfile(profile);
            });
        } else {
            // Connect dev profiles
            this.devProfilesSelected = true;
            selectDevBtn.classList.add('active');
            selectDevBtn.innerHTML = '<i class="fas fa-check me-2"></i>Dev Selected';

            devProfiles.forEach(profile => {
                this.connectProfile(profile);
            });
        }
    }

    connectProfile(profile) {
        // Update status to connecting
        this.updateConnectionStatus(profile, 'connecting');

        // Send connection request via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'connect_profile',
                profile: profile
            }));
        }

        // Simulate connection process (remove this in production)
        setTimeout(() => {
            this.updateConnectionStatus(profile, 'connected');
            this.createProfileTab(profile);
        }, 2000);
    }

    disconnectProfile(profile) {
        this.updateConnectionStatus(profile, 'disconnected');
        this.removeProfileTab(profile);
        this.connectedProfiles.delete(profile);

        // Send disconnection request via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'disconnect_profile',
                profile: profile
            }));
        }
    }

    updateConnectionStatus(profile, status) {
        const statusIcon = document.getElementById(`status-${profile}`);
        const statusBadge = document.getElementById(`badge-${profile}`);

        if (statusIcon) {
            statusIcon.className = 'fas fa-circle';
            switch (status) {
                case 'connected':
                    statusIcon.classList.add('text-connected');
                    if (statusBadge) {
                        statusBadge.className = 'badge bg-success ms-auto';
                        statusBadge.textContent = 'Connected';
                    }
                    this.connectedProfiles.add(profile);
                    break;
                case 'connecting':
                    statusIcon.classList.add('text-connecting', 'pulse');
                    if (statusBadge) {
                        statusBadge.className = 'badge bg-warning ms-auto';
                        statusBadge.textContent = 'Connecting...';
                    }
                    break;
                case 'disconnected':
                default:
                    statusIcon.classList.add('text-disconnected');
                    if (statusBadge) {
                        statusBadge.className = 'badge bg-secondary ms-auto';
                        statusBadge.textContent = 'Disconnected';
                    }
                    this.connectedProfiles.delete(profile);
                    break;
            }
        }
    }

    createProfileTab(profile) {
        const tabsContainer = document.getElementById('profileTabs');
        const contentContainer = document.getElementById('profileTabsContent');

        // Create tab navigation item
        const tabItem = document.createElement('li');
        tabItem.className = 'nav-item';
        tabItem.role = 'presentation';

        const tabButton = document.createElement('button');
        tabButton.className = 'nav-link';
        tabButton.id = `${profile}-tab`;
        tabButton.setAttribute('data-bs-toggle', 'tab');
        tabButton.setAttribute('data-bs-target', `#${profile}`);
        tabButton.type = 'button';
        tabButton.role = 'tab';
        tabButton.innerHTML = `
            <i class="fas fa-server me-1"></i>
            ${profile}
            <button class="btn btn-sm btn-outline-secondary ms-2 close-tab" data-profile="${profile}">
                <i class="fas fa-times"></i>
            </button>
        `;

        tabItem.appendChild(tabButton);
        tabsContainer.appendChild(tabItem);

        // Create tab content
        const tabContent = document.createElement('div');
        tabContent.className = 'tab-pane fade p-3';
        tabContent.id = profile;
        tabContent.role = 'tabpanel';
        tabContent.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">
                    <i class="fas fa-server me-2"></i>
                    ${profile}
                </h6>
                <div>
                    <button class="btn btn-outline-primary btn-sm" onclick="app.exportResults('${profile}')">
                        <i class="fas fa-download me-1"></i> Export
                    </button>
                    <button class="btn btn-outline-secondary btn-sm ms-2" onclick="app.clearResults('${profile}')">
                        <i class="fas fa-trash me-1"></i> Clear
                    </button>
                </div>
            </div>
            <div class="command-output" id="output-${profile}">
                <div class="command-line">$ Ready for commands...</div>
            </div>
        `;

        contentContainer.appendChild(tabContent);

        // Add close tab event listener
        tabButton.querySelector('.close-tab').addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeTab(profile);
        });

        // Activate the new tab
        const tab = new bootstrap.Tab(tabButton);
        tab.show();

        // Add animation
        tabContent.classList.add('animate-in');
    }

    removeProfileTab(profile) {
        const tabButton = document.getElementById(`${profile}-tab`);
        const tabContent = document.getElementById(profile);

        if (tabButton) {
            tabButton.parentElement.remove();
        }

        if (tabContent) {
            tabContent.remove();
        }

        // If no tabs left, show welcome tab
        const remainingTabs = document.querySelectorAll('#profileTabs .nav-item').length;
        if (remainingTabs === 1) { // Only welcome tab remains
            const welcomeTab = new bootstrap.Tab(document.getElementById('welcome-tab'));
            welcomeTab.show();
        }
    }

    closeTab(profile) {
        this.removeProfileTab(profile);
        this.disconnectProfile(profile);

        // Update dev profiles selection if needed
        if (['aws-dev-eu', 'aws-dev-sg'].includes(profile)) {
            const devProfiles = ['aws-dev-eu', 'aws-dev-sg'];
            const connectedDevProfiles = devProfiles.filter(p => this.connectedProfiles.has(p));

            if (connectedDevProfiles.length === 0) {
                this.devProfilesSelected = false;
                const selectDevBtn = document.getElementById('selectDevBtn');
                selectDevBtn.classList.remove('active');
                selectDevBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Select Dev';
            }
        }
    }

    toggleProfile(profile, checked) {
        if (checked) {
            this.connectProfile(profile);
        } else {
            this.disconnectProfile(profile);
        }
    }

    executeCommand() {
        const commandInput = document.getElementById('commandInput');
        const command = commandInput.value.trim();

        if (!command) {
            this.showAlert('Please enter a command', 'warning');
            return;
        }

        if (this.connectedProfiles.size === 0) {
            this.showAlert('Please connect to at least one profile', 'warning');
            return;
        }

        // Add to history
        this.addToHistory(command);

        // Execute command on all connected profiles
        this.connectedProfiles.forEach(profile => {
            this.executeCommandOnProfile(profile, command);
        });

        // Clear input
        commandInput.value = '';
    }

    executeCommandOnProfile(profile, command) {
        const outputElement = document.getElementById(`output-${profile}`);

        if (outputElement) {
            // Add command line to output
            const commandLine = document.createElement('div');
            commandLine.className = 'command-line';
            commandLine.textContent = `$ ${command}`;
            outputElement.appendChild(commandLine);

            // Add loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'text-warning';
            loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Executing...';
            outputElement.appendChild(loadingDiv);

            // Scroll to bottom
            outputElement.scrollTop = outputElement.scrollHeight;
        }

        // Send command via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'execute_command',
                profile: profile,
                command: command
            }));
        }
    }

    updateCommandOutput(profile, output, isError) {
        const outputElement = document.getElementById(`output-${profile}`);

        if (outputElement) {
            // Remove loading indicator
            const loadingDiv = outputElement.querySelector('.text-warning');
            if (loadingDiv) {
                loadingDiv.remove();
            }

            // Add output
            const outputDiv = document.createElement('div');
            outputDiv.className = isError ? 'error' : 'success';
            outputDiv.textContent = output;
            outputElement.appendChild(outputDiv);

            // Scroll to bottom
            outputElement.scrollTop = outputElement.scrollHeight;
        }
    }

    commandComplete(profile, success, duration) {
        const outputElement = document.getElementById(`output-${profile}`);

        if (outputElement) {
            // Add completion status
            const statusDiv = document.createElement('div');
            statusDiv.className = `mt-2 ${success ? 'success' : 'error'}`;
            statusDiv.innerHTML = `
                <i class="fas fa-${success ? 'check' : 'times'} me-2"></i>
                ${success ? 'Success' : 'Failed'} - Duration: ${duration}s
            `;
            outputElement.appendChild(statusDiv);

            // Add separator
            const separator = document.createElement('div');
            separator.className = 'border-top my-3';
            outputElement.appendChild(separator);

            // Scroll to bottom
            outputElement.scrollTop = outputElement.scrollHeight;
        }
    }

    addToHistory(command) {
        const historyItem = {
            command: command,
            timestamp: new Date().toISOString(),
            profiles: Array.from(this.connectedProfiles)
        };

        this.commandHistory.unshift(historyItem);

        // Limit history size
        if (this.commandHistory.length > this.maxHistorySize) {
            this.commandHistory = this.commandHistory.slice(0, this.maxHistorySize);
        }

        // Save to localStorage
        localStorage.setItem('awsAdfsHistory', JSON.stringify(this.commandHistory));
    }

    loadHistory() {
        const saved = localStorage.getItem('awsAdfsHistory');
        if (saved) {
            this.commandHistory = JSON.parse(saved);
        }
    }

    showHistory() {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        if (this.commandHistory.length === 0) {
            historyList.innerHTML = '<div class="text-muted text-center py-4">No command history</div>';
        } else {
            this.commandHistory.forEach((item, index) => {
                const historyItem = document.createElement('div');
                historyItem.className = 'list-group-item list-group-item-action';
                historyItem.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <code class="text-primary">${item.command}</code>
                            <small class="d-block text-muted mt-1">
                                <i class="fas fa-clock me-1"></i>
                                ${new Date(item.timestamp).toLocaleString()}
                                <span class="ms-2">
                                    <i class="fas fa-server me-1"></i>
                                    ${item.profiles.join(', ')}
                                </span>
                            </small>
                        </div>
                        <button class="btn btn-sm btn-outline-primary" onclick="app.useHistoryCommand('${item.command}')">
                            <i class="fas fa-play"></i>
                        </button>
                    </div>
                `;
                historyList.appendChild(historyItem);
            });
        }

        const historyModal = new bootstrap.Modal(document.getElementById('historyModal'));
        historyModal.show();
    }

    useHistoryCommand(command) {
        document.getElementById('commandInput').value = command;
        bootstrap.Modal.getInstance(document.getElementById('historyModal')).hide();
    }

    showSettings() {
        const settingsModal = new bootstrap.Modal(document.getElementById('settingsModal'));
        settingsModal.show();
    }

    saveSettings() {
        const settings = {
            timeout: document.getElementById('timeoutSetting').value,
            retries: document.getElementById('retriesSetting').value,
            exportFormat: document.getElementById('exportFormat').value,
            includeTimestamps: document.getElementById('includeTimestamps').checked
        };

        localStorage.setItem('awsAdfsSettings', JSON.stringify(settings));

        this.showAlert('Settings saved successfully', 'success');
        bootstrap.Modal.getInstance(document.getElementById('settingsModal')).hide();
    }

    loadSettings() {
        const saved = localStorage.getItem('awsAdfsSettings');
        if (saved) {
            const settings = JSON.parse(saved);
            document.getElementById('timeoutSetting').value = settings.timeout || 30;
            document.getElementById('retriesSetting').value = settings.retries || 3;
            document.getElementById('exportFormat').value = settings.exportFormat || 'json';
            document.getElementById('includeTimestamps').checked = settings.includeTimestamps !== false;
        }
    }

    exportResults(profile) {
        const outputElement = document.getElementById(`output-${profile}`);
        if (!outputElement) return;

        const content = outputElement.textContent;
        const format = document.getElementById('exportFormat').value;

        let filename, data, mimeType;

        switch (format) {
            case 'json':
                filename = `${profile}-results.json`;
                data = JSON.stringify({
                    profile: profile,
                    timestamp: new Date().toISOString(),
                    content: content
                }, null, 2);
                mimeType = 'application/json';
                break;
            case 'csv':
                filename = `${profile}-results.csv`;
                data = `Profile,Timestamp,Content\n"${profile}","${new Date().toISOString()}","${content.replace(/"/g, '""')}"`;
                mimeType = 'text/csv';
                break;
            default:
                filename = `${profile}-results.txt`;
                data = `Profile: ${profile}\nTimestamp: ${new Date().toISOString()}\n\n${content}`;
                mimeType = 'text/plain';
        }

        const blob = new Blob([data], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        this.showAlert(`Results exported as ${filename}`, 'success');
    }

    clearResults(profile) {
        const outputElement = document.getElementById(`output-${profile}`);
        if (outputElement) {
            outputElement.innerHTML = '<div class="command-line">$ Ready for commands...</div>';
        }
    }

    updateStatus(status, type) {
        const statusText = document.getElementById('statusText');
        const statusIndicator = document.getElementById('statusIndicator');

        statusText.textContent = status;
        statusIndicator.className = 'fas fa-circle pulse';

        const statusBadge = statusIndicator.closest('.badge');
        statusBadge.className = `badge bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'warning'}`;
    }

    showAlert(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alert);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AWSADFSApp();
});
