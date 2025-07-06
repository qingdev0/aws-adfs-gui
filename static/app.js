// AWS ADFS GUI JavaScript Application

class AWSADFSApp {
    constructor() {
        this.selectedProfiles = new Set();
        this.commandHistory = [];
        this.currentResults = {};
        this.websocket = null;
        this.isExecuting = false;

        this.init();
    }

    async init() {
        await this.loadProfiles();
        await this.loadCommandHistory();
        this.setupEventListeners();
        this.updateUI();
    }

    setupEventListeners() {
        // Command input enter key
        document.getElementById('commandInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeCommand();
            }
        });

        // Command input autocomplete
        document.getElementById('commandInput').addEventListener('input', (e) => {
            this.suggestCommands(e.target.value);
        });
    }

    async loadProfiles() {
        try {
            const response = await fetch('/api/profiles');
            const profiles = await response.json();
            this.renderProfileGroups(profiles);
        } catch (error) {
            console.error('Failed to load profiles:', error);
            this.showNotification('Failed to load profiles', 'error');
        }
    }

    renderProfileGroups(profiles) {
        const container = document.getElementById('profile-groups');
        container.innerHTML = '';

        Object.entries(profiles).forEach(([group, profileList]) => {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'profile-group';

            const groupTitle = document.createElement('h6');
            groupTitle.textContent = this.getGroupDisplayName(group);
            groupDiv.appendChild(groupTitle);

            profileList.forEach(profile => {
                const profileItem = this.createProfileItem(profile);
                groupDiv.appendChild(profileItem);
            });

            container.appendChild(groupDiv);
        });
    }

    createProfileItem(profile) {
        const item = document.createElement('div');
        item.className = 'profile-item';
        item.dataset.profile = profile.name;

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `profile-${profile.name}`;
        checkbox.addEventListener('change', (e) => {
            this.toggleProfile(profile.name, e.target.checked);
        });

        const nameSpan = document.createElement('span');
        nameSpan.className = 'profile-name';
        nameSpan.textContent = profile.name;

        const regionSpan = document.createElement('span');
        regionSpan.className = 'profile-region';
        regionSpan.textContent = profile.region;

        item.appendChild(checkbox);
        item.appendChild(nameSpan);
        item.appendChild(regionSpan);

        return item;
    }

    getGroupDisplayName(group) {
        const names = {
            'dev': 'Development',
            'np': 'Non-Production',
            'pd': 'Production'
        };
        return names[group] || group;
    }

    toggleProfile(profileName, selected) {
        if (selected) {
            this.selectedProfiles.add(profileName);
        } else {
            this.selectedProfiles.delete(profileName);
        }
        this.updateUI();
    }

    selectGroup(group) {
        // Clear current selection
        this.selectedProfiles.clear();

        // Select all profiles in the group
        const checkboxes = document.querySelectorAll(`input[type="checkbox"]`);
        checkboxes.forEach(checkbox => {
            const profileItem = checkbox.closest('.profile-item');
            if (profileItem) {
                const profileName = profileItem.dataset.profile;
                if (profileName.includes(group)) {
                    checkbox.checked = true;
                    this.selectedProfiles.add(profileName);
                } else {
                    checkbox.checked = false;
                }
            }
        });

        this.updateUI();
    }

    selectAll() {
        const checkboxes = document.querySelectorAll(`input[type="checkbox"]`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            const profileItem = checkbox.closest('.profile-item');
            if (profileItem) {
                this.selectedProfiles.add(profileItem.dataset.profile);
            }
        });
        this.updateUI();
    }

    clearSelection() {
        this.selectedProfiles.clear();
        const checkboxes = document.querySelectorAll(`input[type="checkbox"]`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateUI();
    }

    async executeCommand() {
        const command = document.getElementById('commandInput').value.trim();
        const timeout = parseInt(document.getElementById('timeoutInput').value);

        if (!command) {
            this.showNotification('Please enter a command', 'warning');
            return;
        }

        if (this.selectedProfiles.size === 0) {
            this.showNotification('Please select at least one profile', 'warning');
            return;
        }

        if (this.isExecuting) {
            this.showNotification('Command already executing', 'warning');
            return;
        }

        this.isExecuting = true;
        this.updateStatus('Executing...', 'running');
        this.showLoadingModal();

        // Clear previous results
        this.currentResults = {};
        this.clearResults();

        // Add to history
        this.addToHistory(command);

        // Execute via WebSocket
        this.executeViaWebSocket(command, Array.from(this.selectedProfiles), timeout);
    }

    executeViaWebSocket(command, profiles, timeout) {
        const wsUrl = `ws://${window.location.host}/ws/execute`;
        this.websocket = new WebSocket(wsUrl);

        this.websocket.onopen = () => {
            const request = {
                command: command,
                profiles: profiles,
                timeout: timeout
            };
            this.websocket.send(JSON.stringify(request));
        };

        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'complete') {
                this.onExecutionComplete();
            } else if (data.type === 'error') {
                this.onExecutionError(data.error);
            } else {
                // Command result
                this.handleCommandResult(data);
            }
        };

        this.websocket.onerror = (error) => {
            this.onExecutionError('WebSocket error: ' + error);
        };

        this.websocket.onclose = () => {
            this.onExecutionComplete();
        };
    }

    handleCommandResult(result) {
        this.currentResults[result.profile] = result;
        this.updateResultTab(result.profile, result);
    }

    updateResultTab(profile, result) {
        let tab = document.getElementById(`tab-${profile}`);
        let content = document.getElementById(`content-${profile}`);

        if (!tab) {
            // Create new tab
            this.createResultTab(profile);
            tab = document.getElementById(`tab-${profile}`);
            content = document.getElementById(`content-${profile}`);
        }

        // Update tab status
        const statusIcon = tab.querySelector('.status-icon');
        if (result.success) {
            statusIcon.className = 'bi bi-check-circle-fill text-success';
        } else {
            statusIcon.className = 'bi bi-x-circle-fill text-danger';
        }

        // Update content
        content.innerHTML = this.formatResultContent(result);

        // Activate the tab
        const tabInstance = new bootstrap.Tab(tab);
        tabInstance.show();
    }

    createResultTab(profile) {
        const tabsContainer = document.getElementById('resultsTabs');
        const contentContainer = document.getElementById('resultsContent');

        // Create tab
        const tab = document.createElement('li');
        tab.className = 'nav-item';
        tab.id = `tab-${profile}`;

        const tabLink = document.createElement('a');
        tabLink.className = 'nav-link';
        tabLink.href = `#content-${profile}`;
        tabLink.setAttribute('data-bs-toggle', 'tab');
        tabLink.innerHTML = `
            <i class="bi bi-circle-fill status-icon text-warning"></i>
            ${profile}
        `;

        tab.appendChild(tabLink);
        tabsContainer.appendChild(tab);

        // Create content
        const content = document.createElement('div');
        content.className = 'tab-pane fade result-tab';
        content.id = `content-${profile}`;
        contentContainer.appendChild(content);
    }

    formatResultContent(result) {
        const successClass = result.success ? 'result-success' : 'result-error';
        const statusClass = result.success ? 'status-success' : 'status-error';
        const statusIcon = result.success ? 'bi-check-circle-fill' : 'bi-x-circle-fill';
        const statusText = result.success ? 'Success' : 'Error';

        return `
            <div class="result-header">
                <div class="result-status">
                    <i class="bi ${statusIcon} ${statusClass}"></i>
                    <span class="${statusClass}">${statusText}</span>
                    <span class="text-muted">(${result.duration.toFixed(2)}s)</span>
                </div>
            </div>
            <div class="result-content ${successClass}">
                ${result.success ? this.escapeHtml(result.output) : this.escapeHtml(result.error || 'Unknown error')}
            </div>
        `;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    onExecutionComplete() {
        this.isExecuting = false;
        this.updateStatus('Ready', 'ready');
        this.hideLoadingModal();

        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    onExecutionError(error) {
        this.isExecuting = false;
        this.updateStatus('Error', 'error');
        this.hideLoadingModal();
        this.showNotification('Execution failed: ' + error, 'error');

        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }

    async loadCommandHistory() {
        try {
            const response = await fetch('/api/history');
            this.commandHistory = await response.json();
            this.renderCommandHistory();
        } catch (error) {
            console.error('Failed to load command history:', error);
        }
    }

    renderCommandHistory() {
        const container = document.getElementById('commandHistory');
        container.innerHTML = '';

        this.commandHistory.slice(-10).reverse().forEach(history => {
            const item = document.createElement('div');
            item.className = 'list-group-item history-item';
            item.onclick = () => this.useHistoryCommand(history.command);

            item.innerHTML = `
                <div class="command-text">${this.escapeHtml(history.command)}</div>
                <div class="history-meta">
                    ${history.timestamp} • ${history.success_count}/${history.total_count} successful
                </div>
            `;

            container.appendChild(item);
        });
    }

    addToHistory(command) {
        // This will be handled by the backend
        this.loadCommandHistory();
    }

    useHistoryCommand(command) {
        document.getElementById('commandInput').value = command;
    }

    async clearHistory() {
        try {
            await fetch('/api/history', { method: 'DELETE' });
            this.commandHistory = [];
            this.renderCommandHistory();
            this.showNotification('History cleared', 'success');
        } catch (error) {
            console.error('Failed to clear history:', error);
            this.showNotification('Failed to clear history', 'error');
        }
    }

    clearResults() {
        document.getElementById('resultsTabs').innerHTML = '';
        document.getElementById('resultsContent').innerHTML = '';
    }

    async exportResults() {
        if (Object.keys(this.currentResults).length === 0) {
            this.showNotification('No results to export', 'warning');
            return;
        }

        const format = document.getElementById('exportFormat').value;
        const results = Object.values(this.currentResults);

        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    format: format,
                    include_timestamps: true,
                    results: results
                })
            });

            const data = await response.json();

            // Download file
            const blob = new Blob([data.data], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `aws-results-${new Date().toISOString().slice(0, 19)}.${format}`;
            a.click();
            window.URL.revokeObjectURL(url);

            this.showNotification('Results exported successfully', 'success');
        } catch (error) {
            console.error('Failed to export results:', error);
            this.showNotification('Failed to export results', 'error');
        }
    }

    suggestCommands(input) {
        // Simple command suggestions
        const suggestions = [
            'aws s3 ls',
            'aws ec2 describe-instances',
            'aws rds describe-db-instances',
            'aws lambda list-functions',
            'aws iam list-users',
            'aws cloudformation list-stacks'
        ];

        // Could implement autocomplete dropdown here
    }

    updateStatus(text, status) {
        const indicator = document.getElementById('status-indicator');
        const icon = indicator.querySelector('i');

        indicator.innerHTML = `<i class="bi bi-circle-fill text-${this.getStatusColor(status)}"></i> ${text}`;
    }

    getStatusColor(status) {
        const colors = {
            'ready': 'success',
            'running': 'warning',
            'error': 'danger'
        };
        return colors[status] || 'secondary';
    }

    showLoadingModal() {
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }

    hideLoadingModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) {
            modal.hide();
        }
    }

    showNotification(message, type) {
        // Simple notification - could be enhanced with a proper notification library
        console.log(`${type.toUpperCase()}: ${message}`);

        // Create a simple toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }

    updateUI() {
        // Update selected count
        const count = this.selectedProfiles.size;
        // Could add a counter display somewhere in the UI
    }
}

// Global functions for HTML onclick handlers
let app;

document.addEventListener('DOMContentLoaded', () => {
    app = new AWSADFSApp();
});

function executeCommand() {
    if (app) app.executeCommand();
}

function selectGroup(group) {
    if (app) app.selectGroup(group);
}

function selectAll() {
    if (app) app.selectAll();
}

function clearSelection() {
    if (app) app.clearSelection();
}

function clearHistory() {
    if (app) app.clearHistory();
}

function clearResults() {
    if (app) app.clearResults();
}

function exportResults() {
    if (app) app.exportResults();
}
