class QueueManager {
    constructor(controlPanel) {
        this.controlPanel = controlPanel;
        this.autoRefreshEnabled = true;
        this.refreshInterval = null;
        this.refreshIntervalMs = 5000;
        this.currentAccount = null;
        this.queueData = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.subscribeToEvents();
    }

    setupEventListeners() {
        const autoRefreshToggle = document.getElementById('autoRefreshToggle');
        const refreshQueuesBtn = document.getElementById('refreshQueuesBtn');
        const retryQueueBtn = document.getElementById('retryQueueBtn');

        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                this.autoRefreshEnabled = e.target.checked;
                if (this.autoRefreshEnabled) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        if (refreshQueuesBtn) {
            refreshQueuesBtn.addEventListener('click', () => this.refreshQueues());
        }

        if (retryQueueBtn) {
            retryQueueBtn.addEventListener('click', () => this.refreshQueues());
        }

        this.setupTransferControls();
        this.setupShareControls();
    }

    setupTransferControls() {
        document.getElementById('startTransferBtn')?.addEventListener('click', () => this.controlTransfer('start'));
        document.getElementById('pauseTransferBtn')?.addEventListener('click', () => this.controlTransfer('pause'));
        document.getElementById('resumeTransferBtn')?.addEventListener('click', () => this.controlTransfer('resume'));
        document.getElementById('stopTransferBtn')?.addEventListener('click', () => this.controlTransfer('stop'));
        document.getElementById('clearTransferBtn')?.addEventListener('click', () => this.controlTransfer('clear'));
        document.getElementById('exportTransferBtn')?.addEventListener('click', () => this.exportTransfer());
    }

    setupShareControls() {
        document.getElementById('startShareBtn')?.addEventListener('click', () => this.controlShare('start'));
        document.getElementById('pauseShareBtn')?.addEventListener('click', () => this.controlShare('pause'));
        document.getElementById('resumeShareBtn')?.addEventListener('click', () => this.controlShare('resume'));
        document.getElementById('stopShareBtn')?.addEventListener('click', () => this.controlShare('stop'));
        document.getElementById('clearShareBtn')?.addEventListener('click', () => this.controlShare('clear'));
        document.getElementById('exportShareBtn')?.addEventListener('click', () => this.exportShare());
    }

    subscribeToEvents() {
        this.controlPanel.eventBus.on('tabChanged', (tab) => {
            if (tab === 'queue') {
                this.onQueueTabActivated();
            } else {
                this.stopAutoRefresh();
            }
        });

        this.controlPanel.eventBus.on('accountChanged', (account) => {
            this.currentAccount = account;
            if (this.isQueueTabActive()) {
                this.refreshQueues();
            }
        });

        this.controlPanel.eventBus.on('accountsLoaded', () => {
            if (this.isQueueTabActive()) {
                this.refreshQueues();
            }
        });
    }

    isQueueTabActive() {
        const queueView = document.getElementById('queueView');
        return queueView && queueView.classList.contains('active');
    }

    onQueueTabActivated() {
        this.currentAccount = this.controlPanel.getSelectedAccount();
        this.refreshQueues();
        if (this.autoRefreshEnabled) {
            this.startAutoRefresh();
        }
    }

    startAutoRefresh() {
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            if (this.isQueueTabActive()) {
                this.refreshQueues();
            }
        }, this.refreshIntervalMs);
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    async refreshQueues() {
        this.showLoading();
        
        try {
            const response = await this.controlPanel.fetchAPI('/api/control/queues');
            
            if (response.success && response.data) {
                this.queueData = response.data;
                this.renderQueues();
                this.showContent();
            } else {
                this.showError(response.error || '获取队列数据失败');
            }
        } catch (error) {
            console.error('Failed to fetch queues:', error);
            this.showError('无法连接到服务器');
        }
    }

    renderQueues() {
        if (!this.queueData || !this.currentAccount) {
            return;
        }

        const accountData = this.queueData.accounts[this.currentAccount];
        
        if (!accountData || !accountData.available) {
            this.showError(`账户 ${this.currentAccount} 不可用`);
            return;
        }

        this.renderTransferQueue(accountData.transfer);
        this.renderShareQueue(accountData.share);
        
        document.getElementById('transferLastUpdate').textContent = `更新于: ${this.queueData.timestamp}`;
        document.getElementById('shareLastUpdate').textContent = `更新于: ${this.queueData.timestamp}`;
    }

    renderTransferQueue(transferData) {
        const status = transferData.status;
        const queue = transferData.queue || [];

        document.getElementById('transferPending').textContent = status.pending || 0;
        document.getElementById('transferRunning').textContent = status.running || 0;
        document.getElementById('transferCompleted').textContent = status.completed || 0;
        document.getElementById('transferFailed').textContent = status.failed || 0;

        const tbody = document.getElementById('transferQueueBody');
        tbody.innerHTML = '';

        if (queue.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #757575;">暂无任务</td></tr>';
            return;
        }

        queue.slice(0, 50).forEach(task => {
            const row = document.createElement('tr');
            
            const statusBadge = this.createStatusBadge(task.status);
            const link = this.truncateText(task.share_link || '', 40);
            const targetPath = this.truncateText(task.target_path || '', 30);
            const time = this.formatTime(task.created_at);
            
            row.innerHTML = `
                <td>${statusBadge}</td>
                <td title="${this.escapeHtml(task.share_link || '')}">${this.escapeHtml(link)}</td>
                <td title="${this.escapeHtml(task.target_path || '')}">${this.escapeHtml(targetPath)}</td>
                <td>${this.escapeHtml(time)}</td>
            `;
            
            tbody.appendChild(row);
        });

        if (queue.length > 50) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="4" style="text-align: center; color: #757575;">显示前50条，共${queue.length}条任务</td>`;
            tbody.appendChild(row);
        }
    }

    renderShareQueue(shareData) {
        const status = shareData.status;
        const queue = shareData.queue || [];

        document.getElementById('sharePending').textContent = status.pending || 0;
        document.getElementById('shareRunning').textContent = status.running || 0;
        document.getElementById('shareCompleted').textContent = status.completed || 0;
        document.getElementById('shareFailed').textContent = status.failed || 0;

        const tbody = document.getElementById('shareQueueBody');
        tbody.innerHTML = '';

        if (queue.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #757575;">暂无任务</td></tr>';
            return;
        }

        queue.slice(0, 50).forEach(task => {
            const row = document.createElement('tr');
            
            const statusBadge = this.createStatusBadge(task.status);
            const fileName = task.file_info ? task.file_info.name : task.title || '';
            const shareLink = task.share_link || '未生成';
            const time = this.formatTime(task.created_at);
            
            row.innerHTML = `
                <td>${statusBadge}</td>
                <td title="${this.escapeHtml(fileName)}">${this.escapeHtml(this.truncateText(fileName, 30))}</td>
                <td title="${this.escapeHtml(shareLink)}">${this.escapeHtml(this.truncateText(shareLink, 40))}</td>
                <td>${this.escapeHtml(time)}</td>
            `;
            
            tbody.appendChild(row);
        });

        if (queue.length > 50) {
            const row = document.createElement('tr');
            row.innerHTML = `<td colspan="4" style="text-align: center; color: #757575;">显示前50条，共${queue.length}条任务</td>`;
            tbody.appendChild(row);
        }
    }

    createStatusBadge(status) {
        const statusMap = {
            'pending': { text: '待处理', class: 'badge-pending' },
            'running': { text: '进行中', class: 'badge-running' },
            'completed': { text: '已完成', class: 'badge-success' },
            'failed': { text: '失败', class: 'badge-error' },
            'skipped': { text: '跳过', class: 'badge-secondary' }
        };
        
        const statusInfo = statusMap[status] || { text: status, class: 'badge-secondary' };
        return `<span class="status-badge ${statusInfo.class}">${statusInfo.text}</span>`;
    }

    async controlTransfer(action) {
        if (!this.currentAccount) {
            this.controlPanel.showToast('请先选择账户', 'error');
            return;
        }

        try {
            const endpoint = `/api/transfer/${action}`;
            const method = action === 'export' ? 'GET' : 'POST';
            
            const response = await fetch(`${endpoint}?account=${this.currentAccount}`, {
                method: method,
                headers: {
                    'X-API-Key': this.controlPanel.getApiKey(),
                    'Content-Type': 'application/json'
                },
                body: method === 'POST' ? JSON.stringify({ account: this.currentAccount }) : undefined
            });

            const data = await response.json();
            
            if (data.success) {
                this.controlPanel.showToast(data.message || `转存${action}成功`, 'success');
                this.refreshQueues();
            } else {
                this.controlPanel.showToast(data.error || `转存${action}失败`, 'error');
            }
        } catch (error) {
            console.error(`Transfer ${action} failed:`, error);
            this.controlPanel.showToast('操作失败', 'error');
        }
    }

    async controlShare(action) {
        if (!this.currentAccount) {
            this.controlPanel.showToast('请先选择账户', 'error');
            return;
        }

        try {
            const endpoint = `/api/share/${action}`;
            const method = action === 'export' ? 'GET' : 'POST';
            
            const response = await fetch(`${endpoint}?account=${this.currentAccount}`, {
                method: method,
                headers: {
                    'X-API-Key': this.controlPanel.getApiKey(),
                    'Content-Type': 'application/json'
                },
                body: method === 'POST' ? JSON.stringify({ account: this.currentAccount }) : undefined
            });

            const data = await response.json();
            
            if (data.success) {
                this.controlPanel.showToast(data.message || `分享${action}成功`, 'success');
                this.refreshQueues();
            } else {
                this.controlPanel.showToast(data.error || `分享${action}失败`, 'error');
            }
        } catch (error) {
            console.error(`Share ${action} failed:`, error);
            this.controlPanel.showToast('操作失败', 'error');
        }
    }

    async exportTransfer() {
        if (!this.currentAccount) {
            this.controlPanel.showToast('请先选择账户', 'error');
            return;
        }

        try {
            const apiKey = this.controlPanel.getApiKey();
            const url = `/api/transfer/export?account=${this.currentAccount}&format=csv`;
            
            const response = await fetch(url, {
                headers: { 'X-API-Key': apiKey }
            });

            if (response.ok) {
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `transfer_results_${Date.now()}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.controlPanel.showToast('导出成功', 'success');
            } else {
                this.controlPanel.showToast('导出失败', 'error');
            }
        } catch (error) {
            console.error('Export transfer failed:', error);
            this.controlPanel.showToast('导出失败', 'error');
        }
    }

    async exportShare() {
        if (!this.currentAccount) {
            this.controlPanel.showToast('请先选择账户', 'error');
            return;
        }

        try {
            const apiKey = this.controlPanel.getApiKey();
            const url = `/api/share/export?account=${this.currentAccount}&format=csv`;
            
            const response = await fetch(url, {
                headers: { 'X-API-Key': apiKey }
            });

            if (response.ok) {
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `share_results_${Date.now()}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.controlPanel.showToast('导出成功', 'success');
            } else {
                this.controlPanel.showToast('导出失败', 'error');
            }
        } catch (error) {
            console.error('Export share failed:', error);
            this.controlPanel.showToast('导出失败', 'error');
        }
    }

    showLoading() {
        document.getElementById('queueLoadingState').style.display = 'flex';
        document.getElementById('queueErrorState').style.display = 'none';
        document.getElementById('queueContent').style.display = 'none';
    }

    showError(message) {
        document.getElementById('queueLoadingState').style.display = 'none';
        document.getElementById('queueErrorState').style.display = 'flex';
        document.getElementById('queueContent').style.display = 'none';
        document.getElementById('queueErrorMessage').textContent = message;
    }

    showContent() {
        document.getElementById('queueLoadingState').style.display = 'none';
        document.getElementById('queueErrorState').style.display = 'none';
        document.getElementById('queueContent').style.display = 'block';
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    formatTime(timestamp) {
        if (!timestamp) return '';
        return timestamp;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

if (window.controlPanel) {
    window.queueManager = new QueueManager(window.controlPanel);
}
