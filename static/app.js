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

        // Track connected profiles
        this.connectedProfiles = new Set();

        this.init();
    }

    init() {
        this.setupWebSocket();
        this.setupEventListeners();
        this.loadSettings();
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

    handleConnectionStatus(message) {
        const { profile, status, error } = message;
        const outputBodyElement = document.getElementById(`output-body-${profile}`);

        if (status === 'connected') {
            this.updateConnectionStatus(profile, 'connected');

            // Update connection command output to show success
            if (outputBodyElement) {
                // Clear loading indicators
                const loadingElements = outputBodyElement.querySelectorAll('.connection-command');
                loadingElements.forEach(el => el.remove());

                // Add success message
                const successDiv = document.createElement('div');
                successDiv.className = 'success mt-2';
                successDiv.innerHTML = `<i class="fas fa-check-circle me-2"></i>Successfully connected to AWS profile: ${profile}`;
                outputBodyElement.appendChild(successDiv);

                // Add credential validation info
                const infoDiv = document.createElement('div');
                infoDiv.className = 'text-info mt-2';
                infoDiv.innerHTML = `<i class="fas fa-key me-2"></i>AWS credentials validated and ready for use`;
                outputBodyElement.appendChild(infoDiv);

                // Add separator
                const separator = document.createElement('div');
                separator.className = 'border-top my-3';
                outputBodyElement.appendChild(separator);

                // Add ready message
                const readyDiv = document.createElement('div');
                readyDiv.className = 'text-muted';
                readyDiv.innerHTML = '<i class="fas fa-terminal me-2"></i>Ready to execute AWS CLI commands...';
                outputBodyElement.appendChild(readyDiv);

                outputBodyElement.scrollTop = outputBodyElement.scrollHeight;
            }
        } else if (status === 'error') {
            this.updateConnectionStatus(profile, 'disconnected');

            // Update connection command output to show error
            if (outputBodyElement) {
                // Clear loading indicators
                const loadingElements = outputBodyElement.querySelectorAll('.connection-command');
                loadingElements.forEach(el => el.remove());

                // Add error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error mt-2';
                errorDiv.innerHTML = `<i class="fas fa-times-circle me-2"></i>Connection failed: ${error || 'Unknown error'}`;
                outputBodyElement.appendChild(errorDiv);

                // Add troubleshooting info
                const helpDiv = document.createElement('div');
                helpDiv.className = 'text-warning mt-2';
                helpDiv.innerHTML = `<i class="fas fa-lightbulb me-2"></i>Check your ADFS credentials and network connection`;
                outputBodyElement.appendChild(helpDiv);

                outputBodyElement.scrollTop = outputBodyElement.scrollHeight;
            }

            this.showAlert(`Failed to connect to ${profile}: ${error || 'Unknown error'}`, 'error');
        }
    }

    handleCommandOutput(message) {
        const { profile, output, isError } = message;
        this.updateCommandOutput(profile, output, isError);
    }

    handleCommandComplete(message) {
        const { profile, success, duration } = message;
        this.commandComplete(profile, success, duration);
    }

    handleCommandResult(message) {
        const { profile, result } = message;
        if (result.success) {
            this.updateCommandOutput(profile, result.output, false);
        } else {
            this.updateCommandOutput(profile, result.error || 'Command failed', true);
        }
        this.commandComplete(profile, result.success, result.duration);
    }

    handleCommandError(message) {
        const { profile, error } = message;
        this.updateCommandOutput(profile, error, true);
        this.commandComplete(profile, false, 0);
    }

    handleError(message) {
        this.showAlert(message.error || 'An error occurred', 'error');
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

        // Always create tab first so user can see what's happening
        this.createProfileTab(profile);

        // Get credentials from settings
        const credentials = this.getCredentials();
        if (!credentials) {
            // Show credentials needed message in the tab
            this.showCredentialsNeeded(profile);
            this.showAlert('Please configure ADFS credentials in settings first', 'warning');
            return;
        }

        // Show connection command in output
        this.showConnectionCommand(profile, credentials);

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

    showCredentialsNeeded(profile) {
        const outputElement = document.getElementById(`output-${profile}`);
        if (!outputElement) return;

        // Clear existing content and create new structure
        outputElement.innerHTML = '';

        // Create command header for credentials needed
        const commandHeader = document.createElement('div');
        commandHeader.className = 'command-header';

        const commandIcon = document.createElement('i');
        commandIcon.className = 'fas fa-exclamation-triangle command-icon';
        commandIcon.style.color = '#ffc107';

        const commandText = document.createElement('div');
        commandText.className = 'command-text';
        commandText.textContent = '⚠️ ADFS Credentials Required';
        commandText.style.color = '#ffc107';

        const commandTimestamp = document.createElement('div');
        commandTimestamp.className = 'command-timestamp';
        commandTimestamp.textContent = new Date().toLocaleTimeString();

        commandHeader.appendChild(commandIcon);
        commandHeader.appendChild(commandText);
        commandHeader.appendChild(commandTimestamp);

        // Create command body
        const commandBody = document.createElement('div');
        commandBody.className = 'command-body';
        commandBody.id = `output-body-${profile}`;

        // Add credentials setup instructions
        const warningDiv = document.createElement('div');
        warningDiv.className = 'text-warning mt-2';
        warningDiv.innerHTML = `<i class="fas fa-info-circle me-2"></i><strong>Please configure your ADFS credentials first</strong>`;
        commandBody.appendChild(warningDiv);

        const step1Div = document.createElement('div');
        step1Div.className = 'text-info mt-2';
        step1Div.innerHTML = `<i class="fas fa-cog me-2"></i>1. Click the Settings button (gear icon) in the top-right`;
        commandBody.appendChild(step1Div);

        const step2Div = document.createElement('div');
        step2Div.className = 'text-info mt-1';
        step2Div.innerHTML = `<i class="fas fa-user me-2"></i>2. Enter your ADFS username, password, and server hostname`;
        commandBody.appendChild(step2Div);

        const step3Div = document.createElement('div');
        step3Div.className = 'text-info mt-1';
        step3Div.innerHTML = `<i class="fas fa-save me-2"></i>3. Click "Save Settings" and then try connecting again`;
        commandBody.appendChild(step3Div);

        const awsAdfsDiv = document.createElement('div');
        awsAdfsDiv.className = 'connection-command mt-3';
        awsAdfsDiv.innerHTML = `<i class="fas fa-terminal me-2"></i>Once configured, will execute: aws-adfs login --profile=${profile} --adfs-host=[your-host] --env --no-sspi`;
        commandBody.appendChild(awsAdfsDiv);

        outputElement.appendChild(commandHeader);
        outputElement.appendChild(commandBody);
    }

        showConnectionCommand(profile, credentials) {
        const outputElement = document.getElementById(`output-${profile}`);
        if (!outputElement) return;

        const adfsHost = credentials ? credentials.adfs_host : 'your-adfs-host.com';

        // Build the actual aws-adfs command that will be executed
        const awsAdfsCommand = `aws-adfs login --profile=${profile} --adfs-host=${adfsHost} --env --no-sspi`;

        // Clear existing content and create new structure
        outputElement.innerHTML = '';

        // Create command header for connection
        const commandHeader = document.createElement('div');
        commandHeader.className = 'command-header';

        const commandIcon = document.createElement('i');
        commandIcon.className = 'fas fa-link command-icon';

        const commandText = document.createElement('div');
        commandText.className = 'command-text';
        commandText.textContent = `$ ${awsAdfsCommand}`;

        const commandTimestamp = document.createElement('div');
        commandTimestamp.className = 'command-timestamp';
        commandTimestamp.textContent = new Date().toLocaleTimeString();

        commandHeader.appendChild(commandIcon);
        commandHeader.appendChild(commandText);
        commandHeader.appendChild(commandTimestamp);

        // Create command body
        const commandBody = document.createElement('div');
        commandBody.className = 'command-body';
        commandBody.id = `output-body-${profile}`;

        // Add connection status with more detail
        const connectingDiv = document.createElement('div');
        connectingDiv.className = 'connection-command';
        connectingDiv.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>Executing aws-adfs login command...`;
        commandBody.appendChild(connectingDiv);

        // Add step-by-step info
        const step1Div = document.createElement('div');
        step1Div.className = 'text-info mt-2';
        step1Div.innerHTML = `<i class="fas fa-server me-2"></i>Connecting to ADFS server: ${adfsHost}`;
        commandBody.appendChild(step1Div);

        const step2Div = document.createElement('div');
        step2Div.className = 'text-info mt-1';
        step2Div.innerHTML = `<i class="fas fa-user-shield me-2"></i>Authenticating with provided credentials`;
        commandBody.appendChild(step2Div);

        const step3Div = document.createElement('div');
        step3Div.className = 'text-info mt-1';
        step3Div.innerHTML = `<i class="fas fa-key me-2"></i>Requesting AWS STS tokens for profile: ${profile}`;
        commandBody.appendChild(step3Div);

        outputElement.appendChild(commandHeader);
        outputElement.appendChild(commandBody);
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
        // Check if tab already exists
        const existingTab = document.getElementById(`${profile}-tab`);
        const existingContent = document.getElementById(profile);

        if (existingTab && existingContent) {
            // Tab already exists, just activate it
            const tab = new bootstrap.Tab(existingTab);
            tab.show();
            return;
        }

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
                <!-- Command structure will be populated dynamically -->
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
            // Clear existing content and create new structure
            outputElement.innerHTML = '';

            // Create command header
            const commandHeader = document.createElement('div');
            commandHeader.className = 'command-header';

            const commandIcon = document.createElement('i');
            commandIcon.className = 'fas fa-terminal command-icon';

            const commandText = document.createElement('div');
            commandText.className = 'command-text';
            commandText.textContent = `$ ${command}`;

            const commandTimestamp = document.createElement('div');
            commandTimestamp.className = 'command-timestamp';
            commandTimestamp.textContent = new Date().toLocaleTimeString();

            commandHeader.appendChild(commandIcon);
            commandHeader.appendChild(commandText);
            commandHeader.appendChild(commandTimestamp);

            // Create command body
            const commandBody = document.createElement('div');
            commandBody.className = 'command-body';
            commandBody.id = `output-body-${profile}`;

            // Add loading indicator to body
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'text-warning';
            loadingDiv.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Executing...';
            commandBody.appendChild(loadingDiv);

            outputElement.appendChild(commandHeader);
            outputElement.appendChild(commandBody);
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
        const outputBodyElement = document.getElementById(`output-body-${profile}`);

        if (outputBodyElement) {
            // Remove loading indicator
            const loadingDiv = outputBodyElement.querySelector('.text-warning');
            if (loadingDiv) {
                loadingDiv.remove();
            }

            // Add output
            const outputDiv = document.createElement('div');
            outputDiv.className = isError ? 'error' : 'success';
            outputDiv.textContent = output;
            outputBodyElement.appendChild(outputDiv);

            // Scroll to bottom
            outputBodyElement.scrollTop = outputBodyElement.scrollHeight;
        }
    }

    commandComplete(profile, success, duration) {
        const outputBodyElement = document.getElementById(`output-body-${profile}`);

        if (outputBodyElement) {
            // Add completion status
            const statusDiv = document.createElement('div');
            statusDiv.className = `mt-2 ${success ? 'success' : 'error'}`;
            statusDiv.innerHTML = `
                <i class="fas fa-${success ? 'check' : 'times'} me-2"></i>
                ${success ? 'Success' : 'Failed'} - Duration: ${duration}s
            `;
            outputBodyElement.appendChild(statusDiv);

            // Add separator
            const separator = document.createElement('div');
            separator.className = 'border-top my-3';
            outputBodyElement.appendChild(separator);

            // Scroll to bottom
            outputBodyElement.scrollTop = outputBodyElement.scrollHeight;
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
            // Create the default empty state with command header
            outputElement.innerHTML = '';

            // Create command header for ready state
            const commandHeader = document.createElement('div');
            commandHeader.className = 'command-header';

            const commandIcon = document.createElement('i');
            commandIcon.className = 'fas fa-terminal command-icon';

            const commandText = document.createElement('div');
            commandText.className = 'command-text';
            commandText.textContent = '$ Ready for commands...';

            const commandTimestamp = document.createElement('div');
            commandTimestamp.className = 'command-timestamp';
            commandTimestamp.textContent = new Date().toLocaleTimeString();

            commandHeader.appendChild(commandIcon);
            commandHeader.appendChild(commandText);
            commandHeader.appendChild(commandTimestamp);

            // Create empty command body
            const commandBody = document.createElement('div');
            commandBody.className = 'command-body';
            commandBody.id = `output-body-${profile}`;
            commandBody.innerHTML = '<div class="text-muted">Execute commands to see output here...</div>';

            outputElement.appendChild(commandHeader);
            outputElement.appendChild(commandBody);
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
        console.log('Setting up welcome page event listeners');

        // Use Bootstrap's built-in modal events for reliable handling
        const welcomeModal = document.getElementById('welcome-modal');
        if (welcomeModal) {
            // Listen for when the modal is hidden
                        welcomeModal.addEventListener('hidden.bs.modal', () => {
                console.log('Modal hidden event fired');

                // Return focus to help button
                setTimeout(() => {
                    const helpBtn = document.getElementById('helpBtn');
                    if (helpBtn) {
                        helpBtn.focus();
                    }
                }, 300);
            });

            // Listen for when modal is shown for accessibility
            welcomeModal.addEventListener('shown.bs.modal', () => {
                console.log('Welcome modal shown');
                const closeBtn = document.getElementById('welcome-close-btn');
                if (closeBtn) {
                    closeBtn.focus();
                }
            });
        }

        // Handle the main Help button click
        document.addEventListener('click', (e) => {
            if (e.target.id === 'helpBtn') {
                e.preventDefault();
                console.log('Help button clicked - showing help modal');
                this.showWelcome();
            }
        });
    }

                checkWelcomeDisplay() {
        // Since this is now a help page accessed via Help button,
        // we don't auto-display it on page load
        console.log('Help page is now manually accessed via Help button - no auto-display');
    }

                showWelcome() {
        console.log('showWelcome called');
        const welcomeModal = document.getElementById('welcome-modal');
        if (welcomeModal) {
            console.log('Welcome modal found, showing modal');

            // Get or create Bootstrap modal instance
            let modal = bootstrap.Modal.getInstance(welcomeModal);
            if (!modal) {
                modal = new bootstrap.Modal(welcomeModal, {
                    backdrop: true,     // Allow closing by clicking backdrop
                    keyboard: true      // Allow ESC key to close
                });
            }

            console.log('Showing welcome modal');
            modal.show();
        } else {
            console.error('Welcome modal element not found in DOM');
        }
    }

                closeWelcome() {
        console.log('closeWelcome called');
        const welcomeModal = document.getElementById('welcome-modal');

        if (welcomeModal) {
            const modal = bootstrap.Modal.getInstance(welcomeModal);
            if (modal) {
                console.log('Hiding modal via Bootstrap API');
                modal.hide();
            } else {
                console.log('No modal instance found');
            }
        } else {
            console.log('Welcome modal not found');
        }
    }

            resetWelcomePreferences() {
        // Method is no longer needed since help page has no persistent preferences
        console.log('Help page has no preferences to reset - access via Help button anytime');
    }

    // Debug function to test welcome functionality
        debugWelcome() {
        console.log('=== Welcome Debug Info ===');

        const modal = document.getElementById('welcome-modal');
        const closeBtn = document.getElementById('welcome-close-btn');
        const gotItBtn = document.getElementById('welcome-got-it-btn');
        const helpBtn = document.getElementById('helpBtn');

        console.log('Modal element:', !!modal);
        console.log('Close button:', !!closeBtn);
        console.log('Got it button:', !!gotItBtn);
        console.log('Help button:', !!helpBtn);

        if (modal) {
            console.log('Modal classes:', modal.className);
            console.log('Modal display:', getComputedStyle(modal).display);
            console.log('Modal instance:', !!bootstrap.Modal.getInstance(modal));
        }

        if (closeBtn) {
            console.log('Close button clickable:', closeBtn.style.pointerEvents !== 'none');
        }

        if (gotItBtn) {
            console.log('Got it button clickable:', gotItBtn.style.pointerEvents !== 'none');
        }

        // Test clicking buttons programmatically
        console.log('Testing programmatic clicks...');
        if (closeBtn) {
            console.log('Triggering close button click');
            closeBtn.click();
        }
    }

    getWelcomeStatus() {
        // Help page is now accessed manually via Help button
        return {
            note: 'Help page is manually accessed - no persistent status needed',
            available: true
        };
    }

    shouldShowWelcome() {
        // Help page is manually accessed, so it should always be available when requested
        return true;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AWSADFSApp();
});
