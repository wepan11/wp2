const API_KEY_STORAGE = 'control_panel_api_key';
const SELECTED_ACCOUNT_STORAGE = 'control_panel_selected_account';

class ControlPanel {
    constructor() {
        this.apiKey = localStorage.getItem(API_KEY_STORAGE) || '';
        this.selectedAccount = localStorage.getItem(SELECTED_ACCOUNT_STORAGE) || '';
        this.accounts = [];
        this.eventBus = new EventBus();
        this.currentTab = 'browse';
        this.dashboardRefreshTimer = null;
        this.autoRefreshInterval = 5000;
        this.init();
    }

    init() {
        this.setupEventListeners();
        if (this.apiKey) {
            this.showMainContent();
            this.loadAccounts();
            this.loadDashboard();
        }
    }

    setupEventListeners() {
        document.getElementById('saveApiKeyBtn').addEventListener('click', () => this.saveApiKey());
        document.getElementById('apiKeyInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.saveApiKey();
        });

        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = item.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        const accountSelect = document.getElementById('accountSelect');
        accountSelect.addEventListener('change', (e) => {
            this.selectedAccount = e.target.value;
            localStorage.setItem(SELECTED_ACCOUNT_STORAGE, this.selectedAccount);
            this.eventBus.emit('accountChanged', this.selectedAccount);
            this.updateAccountInfo();
        });

        const refreshDashboardBtn = document.getElementById('refreshDashboardBtn');
        if (refreshDashboardBtn) {
            refreshDashboardBtn.addEventListener('click', () => this.loadDashboard());
        }

        this.eventBus.on('settingsUpdated', (settings) => {
            if (settings.autoRefreshInterval) {
                this.autoRefreshInterval = settings.autoRefreshInterval;
            }
        });
    }

    async saveApiKey() {
        const apiKeyInput = document.getElementById('apiKeyInput');
        const apiKey = apiKeyInput.value.trim();

        if (!apiKey) {
            this.showToast('请输入API密钥', 'error');
            return;
        }

        this.apiKey = apiKey;
        localStorage.setItem(API_KEY_STORAGE, apiKey);

        const isValid = await this.validateApiKey();
        if (isValid) {
            this.showMainContent();
            await this.loadAccounts();
            this.showToast('API密钥已保存', 'success');
        } else {
            this.apiKey = '';
            localStorage.removeItem(API_KEY_STORAGE);
            this.showToast('API密钥无效', 'error');
        }
    }

    async validateApiKey() {
        try {
            const response = await fetch('/api/health');
            if (!response.ok) return false;

            const authResponse = await fetch('/api/info', {
                headers: { 'X-API-Key': this.apiKey }
            });

            return authResponse.ok;
        } catch (error) {
            console.error('API key validation failed:', error);
            return false;
        }
    }

    async loadAccounts() {
        try {
            const response = await this.fetchAPI('/api/info');
            if (response.success && response.data.accounts) {
                this.accounts = response.data.accounts;
                this.renderAccountSelector();
                
                if (!this.selectedAccount && this.accounts.length > 0) {
                    this.selectedAccount = this.accounts[0];
                    localStorage.setItem(SELECTED_ACCOUNT_STORAGE, this.selectedAccount);
                }
                
                const accountSelect = document.getElementById('accountSelect');
                accountSelect.value = this.selectedAccount;
                
                this.updateAccountInfo();
                this.eventBus.emit('accountsLoaded', this.accounts);
                this.eventBus.emit('accountChanged', this.selectedAccount);
            }
        } catch (error) {
            console.error('Failed to load accounts:', error);
            this.showToast('加载账户失败', 'error');
        }
    }

    renderAccountSelector() {
        const select = document.getElementById('accountSelect');
        select.innerHTML = '<option value="">选择账户...</option>';
        
        this.accounts.forEach(account => {
            const option = document.createElement('option');
            option.value = account;
            option.textContent = account;
            select.appendChild(option);
        });
    }

    updateAccountInfo() {
        const accountInfo = document.getElementById('accountInfo');
        if (this.selectedAccount) {
            accountInfo.textContent = `当前账户: ${this.selectedAccount}`;
        } else {
            accountInfo.textContent = '未选择账户';
        }
    }

    showMainContent() {
        document.getElementById('apiKeySection').style.display = 'none';
        document.getElementById('mainContent').style.display = 'flex';
    }

    switchTab(tabName) {
        if (this.currentTab === tabName) return;

        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-tab') === tabName);
        });

        document.querySelectorAll('.tab-view').forEach(view => {
            const isActive = view.id === `${tabName}View`;
            view.classList.toggle('active', isActive);
            view.style.display = isActive ? 'flex' : 'none';
        });

        this.currentTab = tabName;
        this.eventBus.emit('tabChanged', tabName);
    }

    async fetchAPI(endpoint) {
        const response = await fetch(endpoint, {
            headers: { 'X-API-Key': this.apiKey }
        });

        if (!response.ok) {
            if (response.status === 401) {
                this.apiKey = '';
                localStorage.removeItem(API_KEY_STORAGE);
                location.reload();
            }
            throw new Error(`API request failed: ${response.statusText}`);
        }

        return await response.json();
    }

    getApiKey() {
        return this.apiKey;
    }

    getSelectedAccount() {
        return this.selectedAccount;
    }

    async loadDashboard() {
        try {
            const response = await this.fetchAPI('/api/control/overview');
            if (response.success && response.data) {
                this.renderDashboard(response.data.queues_summary);
                document.getElementById('dashboardSummary').style.display = 'block';
            }
        } catch (error) {
            console.error('Failed to load dashboard:', error);
        }
    }

    renderDashboard(summary) {
        if (!summary) return;
        
        document.getElementById('dashTransferPending').textContent = summary.total_transfer_pending || 0;
        document.getElementById('dashTransferRunning').textContent = summary.total_transfer_running || 0;
        document.getElementById('dashSharePending').textContent = summary.total_share_pending || 0;
        document.getElementById('dashShareRunning').textContent = summary.total_share_running || 0;
    }

    getAutoRefreshInterval() {
        return this.autoRefreshInterval;
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';

        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }
}

class EventBus {
    constructor() {
        this.events = {};
    }

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }

    off(event, callback) {
        if (!this.events[event]) return;
        this.events[event] = this.events[event].filter(cb => cb !== callback);
    }

    emit(event, data) {
        if (!this.events[event]) return;
        this.events[event].forEach(callback => callback(data));
    }
}

window.controlPanel = new ControlPanel();
