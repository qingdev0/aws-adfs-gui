// AWS ADFS GUI - Enhanced JavaScript

class AWSADFSApp {
    constructor() {
        this.ws = null;
        this.isConnected = false;
        this.connectionAttempts = 0;
        this.maxConnectionAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2 seconds
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.profiles = {
            'aws-dev-eu': false,
            'aws-dev-sg': false,
            'kds-ets-np': false,
            'kds-gps-np': false,
            'kds-iss-np': false,
            'kds-ets-pd': false,
            'kds-gps-pd': false,
            'kds-iss-pd': false
        };
        this.devProfiles = ['aws-dev-eu', 'aws-dev-sg'];
        this.npProfiles = ['kds-ets-np', 'kds-gps-np', 'kds-iss-np'];
        this.pdProfiles = ['kds-ets-pd', 'kds-gps-pd', 'kds-iss-pd'];

        // Add credentials status tracking
        this.credentialsStatus = {};
        this.isValidatingCredentials = false;

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadSettings();
        this.setupPanelFunctionality();
        this.setupWelcomePage();

        // Validate credentials on startup
        this.validateCredentialsOnStartup();
    }

    setupEventListeners() {
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

        // Help button
        document.getElementById('helpBtn').addEventListener('click', () => {
            this.showWelcome();
        });

                // Save settings
        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        // Password toggle
        document.getElementById('togglePassword').addEventListener('click', () => {
            this.togglePasswordVisibility();
        });

        // Test credentials
        document.getElementById('testCredentials').addEventListener('click', () => {
            this.testCredentials();
        });

        // Panel toggle buttons
        const toggleBtn = document.getElementById('togglePanelBtn');
        const showBtn = document.getElementById('showPanelBtn');

        if (toggleBtn) {
            console.log('Adding toggle button event listener');
            toggleBtn.addEventListener('click', () => {
                this.toggleLeftPanel();
            });
        } else {
            console.error('Toggle button not found!');
        }

        if (showBtn) {
            console.log('Adding show button event listener');
            showBtn.addEventListener('click', () => {
                this.showLeftPanel();
            });
        } else {
            console.error('Show button not found!');
        }

        // Panel resize functionality
        this.setupPanelResize();

        // Window resize handling
        window.addEventListener('resize', () => {
            this.handleWindowResize();
        });

        // Click outside to close panel on mobile
        document.addEventListener('click', (e) => {
            this.handleClickOutside(e);
        });
    }

    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.connectionAttempts = 0;
            this.reconnectDelay = 2000; // Reset delay
            this.updateConnectionStatus();
        };

        this.ws.onmessage = (event) => {
            this.handleWebSocketMessage(JSON.parse(event.data));
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus();
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'connection_status':
                this.handleConnectionStatus(message);
                break;
            case 'command_output':
                this.handleCommandOutput(message);
                break;
            case 'command_complete':
                this.handleCommandComplete(message);
                break;
            case 'command_result':
                this.handleCommandResult(message);
                break;
            case 'command_error':
                this.handleCommandError(message);
                break;
            case 'credentials_validation_result':
                this.handleCredentialsValidationResult(message);
                break;
            case 'credentials_validation_error':
                this.handleCredentialsValidationError(message);
                break;
            case 'error':
                this.handleError(message);
                break;
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

    updateDevProfilesState() {
        const devProfiles = ['aws-dev-eu', 'aws-dev-sg'];
        const selectDevBtn = document.getElementById('selectDevBtn');

        // Check how many dev profiles are connected
        const connectedDevProfiles = devProfiles.filter(profile =>
            this.connectedProfiles.has(profile)
        );

        // Update the Select Dev button state
        if (connectedDevProfiles.length === devProfiles.length) {
            // All dev profiles are connected
            this.devProfilesSelected = true;
            selectDevBtn.classList.add('active');
            selectDevBtn.innerHTML = '<i class="fas fa-check me-2"></i>Dev Selected';
        } else if (connectedDevProfiles.length === 0) {
            // No dev profiles are connected
            this.devProfilesSelected = false;
            selectDevBtn.classList.remove('active');
            selectDevBtn.innerHTML = '<i class="fas fa-rocket me-2"></i>Select Dev';
        } else {
            // Some dev profiles are connected
            this.devProfilesSelected = false;
            selectDevBtn.classList.remove('active');
            selectDevBtn.innerHTML = `<i class="fas fa-rocket me-2"></i>Select Dev (${connectedDevProfiles.length}/${devProfiles.length})`;
        }
    }

    toggleNpProfiles() {
        const selectNpBtn = document.getElementById('selectNpBtn');
        const npProfiles = ['kds-ets-np', 'kds-gps-np', 'kds-iss-np'];

        if (this.npProfilesSelected) {
            // Disconnect non-prod profiles
            this.npProfilesSelected = false;
            selectNpBtn.classList.remove('active');
            selectNpBtn.innerHTML = '<i class="fas fa-vial me-2"></i>Select Non-Prod';

            npProfiles.forEach(profile => {
                this.disconnectProfile(profile);
            });
        } else {
            // Connect non-prod profiles
            this.npProfilesSelected = true;
            selectNpBtn.classList.add('active');
            selectNpBtn.innerHTML = '<i class="fas fa-check me-2"></i>Non-Prod Selected';

            npProfiles.forEach(profile => {
                this.connectProfile(profile);
            });
        }
    }

    updateNpProfilesState() {
        const npProfiles = ['kds-ets-np', 'kds-gps-np', 'kds-iss-np'];
        const selectNpBtn = document.getElementById('selectNpBtn');

        // Check how many non-prod profiles are connected
        const connectedNpProfiles = npProfiles.filter(profile =>
            this.connectedProfiles.has(profile)
        );

        // Update the Select Non-Prod button state
        if (connectedNpProfiles.length === npProfiles.length) {
            // All non-prod profiles are connected
            this.npProfilesSelected = true;
            selectNpBtn.classList.add('active');
            selectNpBtn.innerHTML = '<i class="fas fa-check me-2"></i>Non-Prod Selected';
        } else if (connectedNpProfiles.length === 0) {
            // No non-prod profiles are connected
            this.npProfilesSelected = false;
            selectNpBtn.classList.remove('active');
            selectNpBtn.innerHTML = '<i class="fas fa-vial me-2"></i>Select Non-Prod';
        } else {
            // Some non-prod profiles are connected
            this.npProfilesSelected = false;
            selectNpBtn.classList.remove('active');
            selectNpBtn.innerHTML = `<i class="fas fa-vial me-2"></i>Select Non-Prod (${connectedNpProfiles.length}/${npProfiles.length})`;
        }
    }

    togglePdProfiles() {
        const selectPdBtn = document.getElementById('selectPdBtn');
        const pdProfiles = ['kds-ets-pd', 'kds-gps-pd', 'kds-iss-pd'];

        if (this.pdProfilesSelected) {
            // Disconnect production profiles
            this.pdProfilesSelected = false;
            selectPdBtn.classList.remove('active');
            selectPdBtn.innerHTML = '<i class="fas fa-lock me-2"></i>Select Production';

            pdProfiles.forEach(profile => {
                this.disconnectProfile(profile);
            });
        } else {
            // Connect production profiles
            this.pdProfilesSelected = true;
            selectPdBtn.classList.add('active');
            selectPdBtn.innerHTML = '<i class="fas fa-check me-2"></i>Production Selected';

            pdProfiles.forEach(profile => {
                this.connectProfile(profile);
            });
        }
    }

    updatePdProfilesState() {
        const pdProfiles = ['kds-ets-pd', 'kds-gps-pd', 'kds-iss-pd'];
        const selectPdBtn = document.getElementById('selectPdBtn');

        // Check how many production profiles are connected
        const connectedPdProfiles = pdProfiles.filter(profile =>
            this.connectedProfiles.has(profile)
        );

        // Update the Select Production button state
        if (connectedPdProfiles.length === pdProfiles.length) {
            // All production profiles are connected
            this.pdProfilesSelected = true;
            selectPdBtn.classList.add('active');
            selectPdBtn.innerHTML = '<i class="fas fa-check me-2"></i>Production Selected';
        } else if (connectedPdProfiles.length === 0) {
            // No production profiles are connected
            this.pdProfilesSelected = false;
            selectPdBtn.classList.remove('active');
            selectPdBtn.innerHTML = '<i class="fas fa-lock me-2"></i>Select Production';
        } else {
            // Some production profiles are connected
            this.pdProfilesSelected = false;
            selectPdBtn.classList.remove('active');
            selectPdBtn.innerHTML = `<i class="fas fa-lock me-2"></i>Select Production (${connectedPdProfiles.length}/${pdProfiles.length})`;
        }
    }

    updateAllGroupStates(profile) {
        // Update the appropriate group state based on the profile
        if (['aws-dev-eu', 'aws-dev-sg'].includes(profile)) {
            this.updateDevProfilesState();
        } else if (['kds-ets-np', 'kds-gps-np', 'kds-iss-np'].includes(profile)) {
            this.updateNpProfilesState();
        } else if (['kds-ets-pd', 'kds-gps-pd', 'kds-iss-pd'].includes(profile)) {
            this.updatePdProfilesState();
        }
    }

    connectProfile(profile) {
        // Check if already connected
        if (this.connectedProfiles.has(profile)) {
            // If connected, disconnect
            this.disconnectProfile(profile);
            return;
        }

        // Get credentials from settings
        const credentials = this.getCredentials();
        if (!credentials) {
            this.showAlert('Please configure ADFS credentials in settings first', 'warning');
            return;
        }

        // Update status to connecting
        this.updateConnectionStatus(profile, 'connecting');
        this.updateProfileButtonState(profile, 'connecting');

        // Send connection request via WebSocket with credentials
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'connect_profile',
                profile: profile,
                credentials: credentials
            }));
        }
    }

    disconnectProfile(profile) {
        this.updateConnectionStatus(profile, 'disconnected');
        this.updateProfileButtonState(profile, 'disconnected');
        this.removeProfileTab(profile);
        this.connectedProfiles.delete(profile);

        // Send disconnection request via WebSocket
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'disconnect_profile',
                profile: profile
            }));
        }

        // Update group states
        this.updateAllGroupStates(profile);
    }

    updateProfileButtonState(profile, status) {
        const profileBtn = document.getElementById(`${profile}-btn`);
        if (profileBtn) {
            // Remove all status classes
            profileBtn.classList.remove('connected', 'connecting', 'disconnected');

            // Add appropriate status class
            switch (status) {
                case 'connected':
                    profileBtn.classList.add('connected');
                    break;
                case 'connecting':
                    profileBtn.classList.add('connecting');
                    break;
                case 'disconnected':
                default:
                    profileBtn.classList.add('disconnected');
                    break;
            }
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

        // Update button state as well
        this.updateProfileButtonState(profile, status);

        // Update group states
        this.updateAllGroupStates(profile);
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

        // If there are remaining tabs, activate the first one
        const remainingTabs = document.querySelectorAll('#profileTabs .nav-item').length;
        if (remainingTabs > 0) {
            const firstTab = document.querySelector('#profileTabs .nav-link');
            if (firstTab) {
                const tab = new bootstrap.Tab(firstTab);
                tab.show();
            }
        }
    }

    closeTab(profile) {
        this.removeProfileTab(profile);
        this.disconnectProfile(profile);
    }

    getCredentials() {
        // Check if credentials are saved and user wants to use them
        const savedCredentials = localStorage.getItem('awsAdfsCredentials');
        const settings = JSON.parse(localStorage.getItem('awsAdfsSettings') || '{}');

        if (savedCredentials && settings.saveCredentials) {
            try {
                const credentials = JSON.parse(atob(savedCredentials));
                // Add current settings
                credentials.timeout = settings.timeout || 30;
                credentials.retries = settings.retries || 3;
                credentials.no_sspi = settings.noSspi !== false;
                credentials.env_mode = settings.envMode !== false;
                return credentials;
            } catch (e) {
                console.warn('Failed to load saved credentials');
                localStorage.removeItem('awsAdfsCredentials');
            }
        }

        // Try to get credentials from current form values
        const username = document.getElementById('adfsUsername')?.value;
        const password = document.getElementById('adfsPassword')?.value;
        const adfsHost = document.getElementById('adfsHost')?.value;

        if (username && password && adfsHost) {
            return {
                username: username,
                password: password,
                adfs_host: adfsHost,
                timeout: settings.timeout || 30,
                retries: settings.retries || 3,
                no_sspi: settings.noSspi !== false,
                env_mode: settings.envMode !== false
            };
        }

        return null;
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

        togglePasswordVisibility() {
        const passwordInput = document.getElementById('adfsPassword');
        const toggleButton = document.getElementById('togglePassword');
        const icon = toggleButton.querySelector('i');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            passwordInput.type = 'password';
            icon.className = 'fas fa-eye';
        }
    }

    async testCredentials() {
        const username = document.getElementById('adfsUsername').value;
        const password = document.getElementById('adfsPassword').value;
        const adfsHost = document.getElementById('adfsHost').value;

        if (!username || !password || !adfsHost) {
            this.showAlert('Please fill in all credential fields', 'warning');
            return;
        }

        const testButton = document.getElementById('testCredentials');
        const originalText = testButton.innerHTML;

        // Show loading state
        testButton.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
        testButton.disabled = true;

        try {
            const response = await fetch('/api/auth/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    adfs_host: adfsHost
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('✅ Connection test successful!', 'success');
            } else {
                this.showAlert(`❌ Connection test failed: ${result.message}`, 'error');
            }

        } catch (error) {
            this.showAlert(`❌ Connection test failed: ${error.message}`, 'error');
        } finally {
            // Restore button state
            testButton.innerHTML = originalText;
            testButton.disabled = false;
        }
    }

    saveSettings() {
        const settings = {
            // Connection settings
            timeout: document.getElementById('timeoutSetting').value,
            retries: document.getElementById('retriesSetting').value,
            noSspi: document.getElementById('noSspi').checked,
            envMode: document.getElementById('envMode').checked,

            // Export settings
            exportFormat: document.getElementById('exportFormat').value,
            includeTimestamps: document.getElementById('includeTimestamps').checked,
            excludeCredentials: document.getElementById('excludeCredentials').checked,
            compressExports: document.getElementById('compressExports').checked,

            // Credential settings (only save if user wants to)
            saveCredentials: document.getElementById('saveCredentials').checked
        };

        // Handle credentials securely
        if (settings.saveCredentials) {
            const credentials = {
                username: document.getElementById('adfsUsername').value,
                password: document.getElementById('adfsPassword').value,
                adfsHost: document.getElementById('adfsHost').value
            };

            // Only save if all required fields are filled
            if (credentials.username && credentials.password && credentials.adfsHost) {
                // In a real implementation, these should be encrypted
                // For now, we'll encode them (NOT secure for production)
                const encodedCredentials = btoa(JSON.stringify(credentials));
                localStorage.setItem('awsAdfsCredentials', encodedCredentials);
                settings.hasCredentials = true;
            } else {
                this.showAlert('Please fill in all credential fields', 'warning');
                return;
            }
        } else {
            // Clear saved credentials if user doesn't want to save them
            localStorage.removeItem('awsAdfsCredentials');
            settings.hasCredentials = false;
        }

        localStorage.setItem('awsAdfsSettings', JSON.stringify(settings));

        this.showAlert('Settings saved successfully', 'success');
        bootstrap.Modal.getInstance(document.getElementById('settingsModal')).hide();
    }

    loadSettings() {
        const saved = localStorage.getItem('awsAdfsSettings');
        if (saved) {
            const settings = JSON.parse(saved);

            // Connection settings
            document.getElementById('timeoutSetting').value = settings.timeout || 30;
            document.getElementById('retriesSetting').value = settings.retries || 3;
            document.getElementById('noSspi').checked = settings.noSspi !== false;
            document.getElementById('envMode').checked = settings.envMode !== false;

            // Export settings
            document.getElementById('exportFormat').value = settings.exportFormat || 'json';
            document.getElementById('includeTimestamps').checked = settings.includeTimestamps !== false;
            document.getElementById('excludeCredentials').checked = settings.excludeCredentials !== false;
            document.getElementById('compressExports').checked = settings.compressExports || false;

            // Credential settings
            document.getElementById('saveCredentials').checked = settings.saveCredentials !== false;
        }

        // Load credentials if they exist and user wants to save them
        const savedCredentials = localStorage.getItem('awsAdfsCredentials');
        if (savedCredentials && document.getElementById('saveCredentials').checked) {
            try {
                // Decode credentials (NOT secure for production)
                const credentials = JSON.parse(atob(savedCredentials));
                document.getElementById('adfsUsername').value = credentials.username || '';
                document.getElementById('adfsHost').value = credentials.adfsHost || '';
                // Don't auto-fill password for security
            } catch (e) {
                console.warn('Failed to load saved credentials');
                localStorage.removeItem('awsAdfsCredentials');
            }
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

    showConnectionDiagnostic(profile, errorMessage) {
        // Create diagnostic modal
        const modalHtml = `
            <div class="modal fade" id="diagnosticModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                Connection Failed - ${profile}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-danger">
                                <h6><i class="fas fa-times-circle me-2"></i>Error Details</h6>
                                <p class="mb-0">${errorMessage}</p>
                            </div>

                            <div class="card mt-3">
                                <div class="card-header">
                                    <h6 class="mb-0"><i class="fas fa-lightbulb me-2"></i>Troubleshooting Tips</h6>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled mb-0">
                                        ${this.getTroubleshootingTips(errorMessage)}
                                    </ul>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-primary" onclick="app.showSettings()">
                                <i class="fas fa-cog me-2"></i>Check Settings
                            </button>
                            <button type="button" class="btn btn-warning" onclick="app.retryConnection('${profile}')">
                                <i class="fas fa-redo me-2"></i>Retry Connection
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing diagnostic modal if any
        const existingModal = document.getElementById('diagnosticModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add new modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('diagnosticModal'));
        modal.show();

        // Clean up modal when hidden
        document.getElementById('diagnosticModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('diagnosticModal').remove();
        });
    }

    getTroubleshootingTips(errorMessage) {
        const tips = [];
        const errorLower = errorMessage.toLowerCase();

        if (errorLower.includes('username') || errorLower.includes('password')) {
            tips.push('<li><i class="fas fa-key text-warning me-2"></i>Verify your username and password in Settings</li>');
            tips.push('<li><i class="fas fa-user-lock text-info me-2"></i>Check if your account is locked or expired</li>');
        }

        if (errorLower.includes('connect') || errorLower.includes('network')) {
            tips.push('<li><i class="fas fa-wifi text-primary me-2"></i>Check your internet connection</li>');
            tips.push('<li><i class="fas fa-server text-secondary me-2"></i>Verify the ADFS server hostname in Settings</li>');
            tips.push('<li><i class="fas fa-shield-alt text-success me-2"></i>Check if you\'re behind a firewall or proxy</li>');
        }

        if (errorLower.includes('ssl') || errorLower.includes('certificate')) {
            tips.push('<li><i class="fas fa-certificate text-warning me-2"></i>Check your SSL certificate file</li>');
            tips.push('<li><i class="fas fa-toggle-off text-danger me-2"></i>Try disabling SSL verification temporarily</li>');
        }

        if (errorLower.includes('timeout')) {
            tips.push('<li><i class="fas fa-clock text-info me-2"></i>The server may be slow or overloaded</li>');
            tips.push('<li><i class="fas fa-hourglass-half text-warning me-2"></i>Try again in a few minutes</li>');
        }

        if (errorLower.includes('command not found') || errorLower.includes('aws-adfs')) {
            tips.push('<li><i class="fas fa-download text-primary me-2"></i>Install aws-adfs: <code>pip install aws-adfs</code></li>');
        }

        // Default tips if no specific error detected
        if (tips.length === 0) {
            tips.push('<li><i class="fas fa-cog text-primary me-2"></i>Check your credentials and settings</li>');
            tips.push('<li><i class="fas fa-network-wired text-info me-2"></i>Verify network connectivity</li>');
            tips.push('<li><i class="fas fa-redo text-success me-2"></i>Try reconnecting in a few moments</li>');
        }

        return tips.join('');
    }

    retryConnection(profile) {
        // Close diagnostic modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('diagnosticModal'));
        if (modal) {
            modal.hide();
        }

        // Retry the connection
        this.connectProfile(profile);
    }

        // Panel Management Methods
    toggleLeftPanel() {
        console.log('Toggle left panel called');
        const leftPanel = document.getElementById('leftPanel');

        if (leftPanel.classList.contains('hidden')) {
            console.log('Showing left panel');
            this.showLeftPanel();
        } else {
            console.log('Hiding left panel');
            this.hideLeftPanel();
        }
    }

        hideLeftPanel() {
        const leftPanel = document.getElementById('leftPanel');
        const showPanelBtn = document.getElementById('showPanelBtn');
        const togglePanelBtn = document.getElementById('togglePanelBtn');

        leftPanel.classList.add('hidden');
        leftPanel.classList.remove('mobile-show');
        showPanelBtn.classList.remove('d-none');
        showPanelBtn.classList.add('show');

        // Update toggle button icon
        togglePanelBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        togglePanelBtn.title = 'Show Panel';

        // Save panel state (but not on mobile)
        if (!this.isMobile()) {
            localStorage.setItem('leftPanelHidden', 'true');
        }
    }

        showLeftPanel() {
        const leftPanel = document.getElementById('leftPanel');
        const showPanelBtn = document.getElementById('showPanelBtn');
        const togglePanelBtn = document.getElementById('togglePanelBtn');

        leftPanel.classList.remove('hidden');
        if (this.isMobile()) {
            leftPanel.classList.add('mobile-show');
        }
        showPanelBtn.classList.add('d-none');
        showPanelBtn.classList.remove('show');

        // Update toggle button icon
        togglePanelBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        togglePanelBtn.title = 'Hide Panel';

        // Save panel state (but not on mobile)
        if (!this.isMobile()) {
            localStorage.setItem('leftPanelHidden', 'false');
        }
    }

    setupPanelResize() {
        console.log('Setting up panel resize...');
        const resizeHandle = document.getElementById('resizeHandle');
        const leftPanel = document.getElementById('leftPanel');

        if (!resizeHandle) {
            console.error('Resize handle not found!');
            return;
        }
        if (!leftPanel) {
            console.error('Left panel not found!');
            return;
        }

        let isResizing = false;
        let startX = 0;
        let startWidth = 0;

        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = leftPanel.offsetWidth;

            resizeHandle.classList.add('dragging');
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';

            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;

            const deltaX = e.clientX - startX;
            const newWidth = startWidth + deltaX;
            const minWidth = 200;
            const maxWidth = Math.min(600, window.innerWidth * 0.5);

            if (newWidth >= minWidth && newWidth <= maxWidth) {
                leftPanel.style.width = newWidth + 'px';
                leftPanel.style.flex = `0 0 ${newWidth}px`;
            }
        });

        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                resizeHandle.classList.remove('dragging');
                document.body.style.cursor = '';
                document.body.style.userSelect = '';

                // Save panel width
                localStorage.setItem('leftPanelWidth', leftPanel.style.width);
            }
        });

        // Double-click to reset width
        resizeHandle.addEventListener('dblclick', () => {
            leftPanel.style.width = '320px';
            leftPanel.style.flex = '0 0 320px';
            localStorage.removeItem('leftPanelWidth');
        });
    }

        // Load panel preferences on init
    loadPanelPreferences() {
        const leftPanel = document.getElementById('leftPanel');

        // Don't apply desktop preferences on mobile
        if (this.isMobile()) {
            this.hideLeftPanel(); // Start hidden on mobile
            return;
        }

        const isHidden = localStorage.getItem('leftPanelHidden') === 'true';
        const savedWidth = localStorage.getItem('leftPanelWidth');

        if (savedWidth) {
            leftPanel.style.width = savedWidth;
            leftPanel.style.flex = `0 0 ${savedWidth}`;
        }

        if (isHidden) {
            this.hideLeftPanel();
        }
    }

    // Helper method to detect mobile devices
    isMobile() {
        return window.innerWidth <= 768;
    }

    // Handle window resize for responsive behavior
    handleWindowResize() {
        const leftPanel = document.getElementById('leftPanel');

        if (this.isMobile()) {
            // On mobile, ensure panel follows mobile behavior
            leftPanel.classList.remove('mobile-show');
            if (!leftPanel.classList.contains('hidden')) {
                leftPanel.classList.add('mobile-show');
            }
        } else {
            // On desktop, remove mobile classes and apply desktop behavior
            leftPanel.classList.remove('mobile-show');

            // Restore desktop width if available
            const savedWidth = localStorage.getItem('leftPanelWidth');
            if (savedWidth) {
                leftPanel.style.width = savedWidth;
                leftPanel.style.flex = `0 0 ${savedWidth}`;
            } else {
                leftPanel.style.width = '320px';
                leftPanel.style.flex = '0 0 320px';
            }
        }
    }

    // Handle click outside panel to close it on mobile
    handleClickOutside(e) {
        if (!this.isMobile()) return;

        const leftPanel = document.getElementById('leftPanel');
        const showPanelBtn = document.getElementById('showPanelBtn');
        const togglePanelBtn = document.getElementById('togglePanelBtn');

        // Check if panel is open and click is outside
        if (!leftPanel.classList.contains('hidden') &&
            !leftPanel.contains(e.target) &&
            !showPanelBtn.contains(e.target) &&
            !togglePanelBtn.contains(e.target)) {
            this.hideLeftPanel();
        }
    }

    async validateCredentialsOnStartup() {
        try {
            this.isValidatingCredentials = true;
            this.updateCredentialsStatusDisplay();

            const response = await fetch('/api/credentials/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.credentialsStatus = data.profiles;
                this.updateCredentialsStatusDisplay();

                console.log('Credentials validation completed:', data.summary);
            } else {
                console.error('Failed to validate credentials on startup');
            }
        } catch (error) {
            console.error('Error validating credentials:', error);
        } finally {
            this.isValidatingCredentials = false;
        }
    }

    async validateCredentials(profiles = null) {
        try {
            this.isValidatingCredentials = true;
            this.updateCredentialsStatusDisplay();

            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                // Use WebSocket for real-time updates
                this.ws.send(JSON.stringify({
                    type: 'validate_credentials',
                    profiles: profiles
                }));
            } else {
                // Fallback to HTTP API
                const response = await fetch('/api/credentials/validate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ profiles: profiles })
                });

                if (response.ok) {
                    const data = await response.json();
                    this.credentialsStatus = data.profiles;
                    this.updateCredentialsStatusDisplay();
                }
            }
        } catch (error) {
            console.error('Error validating credentials:', error);
            this.showAlert('Failed to validate credentials: ' + error.message, 'error');
        } finally {
            this.isValidatingCredentials = false;
        }
    }

    handleCredentialsValidationResult(message) {
        this.credentialsStatus = message.results;
        this.updateCredentialsStatusDisplay();
        this.isValidatingCredentials = false;

        const summary = message.summary;
        let summaryText = `Validation complete: `;
        if (summary.valid) summaryText += `${summary.valid} active, `;
        if (summary.expired) summaryText += `${summary.expired} expired, `;
        if (summary.invalid) summaryText += `${summary.invalid} invalid, `;
        if (summary.missing) summaryText += `${summary.missing} not configured`;

        this.showAlert(summaryText, 'info');
    }

    handleCredentialsValidationError(message) {
        this.isValidatingCredentials = false;
        this.showAlert('Credential validation failed: ' + message.error, 'error');
    }

    updateCredentialsStatusDisplay() {
        Object.keys(this.profiles).forEach(profile => {
            this.updateProfileCredentialStatus(profile);
        });

        // Update group status indicators
        this.updateGroupCredentialStatus();
    }

    updateProfileCredentialStatus(profile) {
        const status = this.credentialsStatus[profile];
        const profileElement = document.getElementById(profile);
        const statusElement = document.getElementById(`${profile}-status`);

        if (!profileElement || !statusElement) return;

        if (this.isValidatingCredentials && !status) {
            // Show loading state
            statusElement.innerHTML = `
                <i class="fas fa-spinner fa-spin" style="color: #17a2b8;"></i>
                <span style="color: #17a2b8;">Checking...</span>
            `;
            return;
        }

        if (status) {
            const config = status;
            statusElement.innerHTML = `
                <i class="${config.icon}" style="color: ${config.color};"></i>
                <span style="color: ${config.color};">${config.label}</span>
            `;

            // Add tooltip with detailed message
            statusElement.setAttribute('title', status.message);
            statusElement.setAttribute('data-bs-toggle', 'tooltip');

            // Add click handler for expired/invalid credentials
            if (status.status === 'expired' || status.status === 'invalid') {
                statusElement.style.cursor = 'pointer';
                statusElement.onclick = () => {
                    this.refreshCredentials(profile);
                };
            }
        } else {
            statusElement.innerHTML = `
                <i class="fas fa-question-circle" style="color: #6c757d;"></i>
                <span style="color: #6c757d;">Unknown</span>
            `;
        }
    }

    updateGroupCredentialStatus() {
        this.updateGroupStatus('dev', this.devProfiles);
        this.updateGroupStatus('np', this.npProfiles);
        this.updateGroupStatus('pd', this.pdProfiles);
    }

    updateGroupStatus(groupName, profileList) {
        const groupStatusElement = document.getElementById(`${groupName}-group-status`);
        if (!groupStatusElement) return;

        let validCount = 0;
        let expiredCount = 0;
        let invalidCount = 0;
        let missingCount = 0;
        let totalCount = profileList.length;

        profileList.forEach(profile => {
            const status = this.credentialsStatus[profile];
            if (status) {
                switch (status.status) {
                    case 'valid': validCount++; break;
                    case 'expired': expiredCount++; break;
                    case 'invalid': invalidCount++; break;
                    case 'missing': missingCount++; break;
                }
            } else {
                missingCount++;
            }
        });

        let statusColor, statusIcon, statusText;

        if (validCount === totalCount) {
            statusColor = '#28a745';
            statusIcon = 'fas fa-check-circle';
            statusText = 'All Active';
        } else if (expiredCount > 0) {
            statusColor = '#ffc107';
            statusIcon = 'fas fa-clock';
            statusText = `${expiredCount} Expired`;
        } else if (invalidCount > 0 || missingCount > 0) {
            statusColor = '#dc3545';
            statusIcon = 'fas fa-exclamation-triangle';
            statusText = `${invalidCount + missingCount} Issues`;
        } else {
            statusColor = '#6c757d';
            statusIcon = 'fas fa-question-circle';
            statusText = 'Unknown';
        }

        groupStatusElement.innerHTML = `
            <i class="${statusIcon}" style="color: ${statusColor};"></i>
            <span style="color: ${statusColor};">${statusText}</span>
        `;

        // Add click handler for group refresh
        groupStatusElement.style.cursor = 'pointer';
        groupStatusElement.onclick = () => {
            this.refreshGroupCredentials(profileList);
        };
    }

    async refreshCredentials(profile) {
        const credentials = this.getCredentials();
        if (!credentials) {
            this.showAlert('Please configure ADFS credentials first', 'warning');
            return;
        }

        this.connectProfile(profile);
    }

    async refreshGroupCredentials(profileList) {
        const credentials = this.getCredentials();
        if (!credentials) {
            this.showAlert('Please configure ADFS credentials first', 'warning');
            return;
        }

        // Connect all profiles in the group
        profileList.forEach(profile => {
            if (this.credentialsStatus[profile]?.status !== 'valid') {
                this.connectProfile(profile);
            }
        });
    }

    async refreshAllCredentials() {
        const credentials = this.getCredentials();
        if (!credentials) {
            this.showAlert('Please configure ADFS credentials first', 'warning');
            return;
        }

        // Find all profiles that need refresh
        const profilesToRefresh = Object.keys(this.profiles).filter(profile => {
            const status = this.credentialsStatus[profile];
            return !status || status.status !== 'valid';
        });

        if (profilesToRefresh.length === 0) {
            this.showAlert('All credentials are already active', 'info');
            return;
        }

        // Connect profiles that need refresh
        profilesToRefresh.forEach(profile => {
            this.connectProfile(profile);
        });

        this.showAlert(`Refreshing ${profilesToRefresh.length} profiles...`, 'info');
    }

    // Welcome Page Functionality
    setupWelcomePage() {
        // Add event listeners for welcome page elements
        this.setupWelcomeEventListeners();

        // Check if welcome should be shown on startup
        this.checkWelcomeDisplay();
    }

    setupWelcomeEventListeners() {
        // Close button
        const closeBtn = document.getElementById('welcome-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeWelcome();
            });
        }

        // Got it button
        const gotItBtn = document.getElementById('welcome-got-it-btn');
        if (gotItBtn) {
            gotItBtn.addEventListener('click', () => {
                this.closeWelcome();
            });
        }

        // Show welcome again button
        const showAgainBtn = document.getElementById('show-welcome-btn');
        if (showAgainBtn) {
            showAgainBtn.addEventListener('click', () => {
                this.showWelcome();
            });
        }

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const welcomeModal = document.getElementById('welcome-modal');
                if (welcomeModal && welcomeModal.classList.contains('show')) {
                    this.closeWelcome();
                }
            }
        });

        // Click outside to close modal
        const welcomeModal = document.getElementById('welcome-modal');
        if (welcomeModal) {
            welcomeModal.addEventListener('click', (e) => {
                if (e.target === welcomeModal) {
                    this.closeWelcome();
                }
            });
        }
    }

    checkWelcomeDisplay() {
        // Check localStorage to see if welcome was dismissed
        const welcomeDismissed = localStorage.getItem('welcomeDismissed');
        const dontShowAgain = localStorage.getItem('welcomeDontShowAgain');

        // Show welcome if it hasn't been dismissed or if "don't show again" is not set
        if (!welcomeDismissed || dontShowAgain !== 'true') {
            // Add a small delay to ensure DOM is fully loaded
            setTimeout(() => {
                this.showWelcome();
            }, 1000);
        }
    }

    showWelcome() {
        const welcomeModal = document.getElementById('welcome-modal');
        if (welcomeModal) {
            const modal = new bootstrap.Modal(welcomeModal, {
                backdrop: 'static', // Prevent closing by clicking backdrop
                keyboard: true,     // Allow ESC key to close
                focus: true         // Focus management
            });

            modal.show();

            // Focus management - focus the close button for accessibility
            welcomeModal.addEventListener('shown.bs.modal', () => {
                const closeBtn = document.getElementById('welcome-close-btn');
                if (closeBtn) {
                    closeBtn.focus();
                }
            });
        }
    }

    closeWelcome() {
        const welcomeModal = document.getElementById('welcome-modal');
        const dontShowAgainCheck = document.getElementById('dontShowAgain');

        if (welcomeModal) {
            const modal = bootstrap.Modal.getInstance(welcomeModal);
            if (modal) {
                modal.hide();
            }

            // Save dismissal to localStorage
            localStorage.setItem('welcomeDismissed', 'true');
            localStorage.setItem('welcomeDismissedAt', Date.now().toString());

            // Check if "don't show again" was selected
            if (dontShowAgainCheck && dontShowAgainCheck.checked) {
                localStorage.setItem('welcomeDontShowAgain', 'true');
            }

            // Focus management - return focus to help button
            const helpBtn = document.getElementById('helpBtn');
            if (helpBtn) {
                helpBtn.focus();
            }
        }
    }

    resetWelcomePreferences() {
        // Method to reset welcome preferences (useful for testing)
        localStorage.removeItem('welcomeDismissed');
        localStorage.removeItem('welcomeDismissedAt');
        localStorage.removeItem('welcomeDontShowAgain');

        // Uncheck the "don't show again" checkbox
        const dontShowAgainCheck = document.getElementById('dontShowAgain');
        if (dontShowAgainCheck) {
            dontShowAgainCheck.checked = false;
        }
    }

    getWelcomeStatus() {
        // Method to get current welcome status (useful for debugging)
        return {
            dismissed: localStorage.getItem('welcomeDismissed'),
            dismissedAt: localStorage.getItem('welcomeDismissedAt'),
            dontShowAgain: localStorage.getItem('welcomeDontShowAgain'),
            shouldShow: this.shouldShowWelcome()
        };
    }

    shouldShowWelcome() {
        // Check if welcome should be shown based on current settings
        const welcomeDismissed = localStorage.getItem('welcomeDismissed');
        const dontShowAgain = localStorage.getItem('welcomeDontShowAgain');

        return !welcomeDismissed || dontShowAgain !== 'true';
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AWSADFSApp();
});
