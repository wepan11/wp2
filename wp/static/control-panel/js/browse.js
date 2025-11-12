class BrowseModule {
    constructor() {
        this.currentPath = '/';
        this.currentFiles = [];
        this.selectedFile = null;
        this.isSearching = false;
        this.searchKeyword = '';
        this.searchDebounceTimer = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.subscribeToEvents();
    }

    setupEventListeners() {
        document.getElementById('refreshFilesBtn').addEventListener('click', () => {
            if (this.isSearching) {
                this.performSearch();
            } else {
                this.loadDirectory(this.currentPath);
            }
        });

        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchDebounceTimer);
            const value = e.target.value.trim();
            
            if (value.length > 0) {
                this.searchDebounceTimer = setTimeout(() => {
                    this.performSearch(value);
                }, 500);
            }
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(this.searchDebounceTimer);
                const value = e.target.value.trim();
                if (value) {
                    this.performSearch(value);
                }
            }
        });

        document.getElementById('searchBtn').addEventListener('click', () => {
            const value = document.getElementById('searchInput').value.trim();
            if (value) {
                this.performSearch(value);
            }
        });

        document.getElementById('clearSearchBtn').addEventListener('click', () => {
            this.clearSearch();
        });

        document.getElementById('retryBtn').addEventListener('click', () => {
            if (this.isSearching) {
                this.performSearch(this.searchKeyword);
            } else {
                this.loadDirectory(this.currentPath);
            }
        });

        document.getElementById('closeDrawerBtn').addEventListener('click', () => {
            this.closeDrawer();
        });

        document.getElementById('copyPathBtn').addEventListener('click', () => {
            this.copyPath();
        });

        document.getElementById('queueShareBtn').addEventListener('click', () => {
            this.queueShare();
        });
    }

    subscribeToEvents() {
        window.controlPanel.eventBus.on('accountChanged', (account) => {
            if (account) {
                this.loadDirectory('/');
            }
        });

        window.controlPanel.eventBus.on('tabChanged', (tab) => {
            if (tab === 'browse' && window.controlPanel.getSelectedAccount()) {
                this.loadDirectory(this.currentPath);
            }
        });
    }

    async loadDirectory(path) {
        this.currentPath = path;
        this.isSearching = false;
        document.getElementById('clearSearchBtn').style.display = 'none';
        
        this.showLoadingState();
        this.renderBreadcrumbs(path);

        const account = window.controlPanel.getSelectedAccount();
        if (!account) {
            this.showErrorState('请先选择账户');
            return;
        }

        try {
            const params = new URLSearchParams({
                path: path,
                account: account
            });

            const response = await this.fetchAPI(`/api/files/list?${params}`);
            
            if (response.success) {
                this.currentFiles = response.data;
                this.renderFiles(response.data);
            } else {
                this.showErrorState(response.error || '加载文件列表失败');
            }
        } catch (error) {
            console.error('Failed to load directory:', error);
            this.showErrorState('加载文件列表时出错');
        }
    }

    async performSearch(keyword) {
        if (!keyword) {
            keyword = document.getElementById('searchInput').value.trim();
        }
        
        if (!keyword) {
            return;
        }

        this.searchKeyword = keyword;
        this.isSearching = true;
        document.getElementById('clearSearchBtn').style.display = 'inline-flex';
        
        this.showLoadingState();

        const account = window.controlPanel.getSelectedAccount();
        if (!account) {
            this.showErrorState('请先选择账户');
            return;
        }

        try {
            const params = new URLSearchParams({
                keyword: keyword,
                path: this.currentPath,
                account: account
            });

            const response = await this.fetchAPI(`/api/files/search?${params}`);
            
            if (response.success) {
                this.currentFiles = response.data;
                this.renderSearchResults(response.data, keyword);
            } else {
                this.showErrorState(response.error || '搜索失败');
            }
        } catch (error) {
            console.error('Search failed:', error);
            this.showErrorState('搜索时出错');
        }
    }

    clearSearch() {
        document.getElementById('searchInput').value = '';
        document.getElementById('clearSearchBtn').style.display = 'none';
        this.searchKeyword = '';
        this.isSearching = false;
        this.loadDirectory(this.currentPath);
    }

    renderBreadcrumbs(path) {
        const container = document.getElementById('breadcrumbsContainer');
        container.innerHTML = '';

        const parts = path.split('/').filter(p => p);
        
        const homeItem = document.createElement('span');
        homeItem.className = 'breadcrumb-item';
        homeItem.textContent = '根目录';
        homeItem.addEventListener('click', () => this.loadDirectory('/'));
        container.appendChild(homeItem);

        let currentPath = '';
        parts.forEach((part, index) => {
            currentPath += '/' + part;
            
            const separator = document.createElement('span');
            separator.className = 'breadcrumb-separator';
            separator.textContent = '/';
            container.appendChild(separator);

            const item = document.createElement('span');
            item.className = 'breadcrumb-item';
            item.textContent = part;
            
            if (index === parts.length - 1) {
                item.classList.add('current');
            } else {
                const pathToLoad = currentPath;
                item.addEventListener('click', () => this.loadDirectory(pathToLoad));
            }
            
            container.appendChild(item);
        });
    }

    renderFiles(files) {
        if (!files || files.length === 0) {
            this.showEmptyState('此目录为空');
            return;
        }

        const container = document.getElementById('filesList');
        container.innerHTML = '';

        files.forEach(file => {
            const fileItem = this.createFileItem(file);
            container.appendChild(fileItem);
        });

        document.getElementById('filesContainer').style.display = 'block';
        this.hideStates();
    }

    renderSearchResults(results, keyword) {
        if (!results || results.length === 0) {
            this.showEmptyState(`没有找到包含 "${keyword}" 的文件`);
            return;
        }

        const container = document.getElementById('filesList');
        container.innerHTML = '';

        const header = document.createElement('div');
        header.style.padding = '0.5rem 0';
        header.style.marginBottom = '0.5rem';
        header.style.color = 'var(--text-secondary)';
        header.textContent = `找到 ${results.length} 个结果`;
        container.appendChild(header);

        results.forEach(file => {
            const fileItem = this.createFileItem(file);
            container.appendChild(fileItem);
        });

        document.getElementById('filesContainer').style.display = 'block';
        this.hideStates();
    }

    createFileItem(file) {
        const item = document.createElement('div');
        item.className = 'file-item';

        const isDir = file.isdir === 1 || file.isdir === true;
        const icon = document.createElement('span');
        icon.className = 'file-icon';
        icon.textContent = isDir ? '📁' : '📄';

        const info = document.createElement('div');
        info.className = 'file-info';

        const name = document.createElement('div');
        name.className = 'file-name';
        name.textContent = file.server_filename || file.filename || 'Unknown';

        const meta = document.createElement('div');
        meta.className = 'file-meta';

        if (!isDir && file.size !== undefined) {
            const sizeSpan = document.createElement('span');
            sizeSpan.textContent = this.formatFileSize(file.size);
            meta.appendChild(sizeSpan);
        }

        if (file.server_mtime || file.mtime) {
            const timeSpan = document.createElement('span');
            timeSpan.textContent = this.formatTime(file.server_mtime || file.mtime);
            meta.appendChild(timeSpan);
        }

        info.appendChild(name);
        info.appendChild(meta);

        item.appendChild(icon);
        item.appendChild(info);

        if (isDir) {
            item.addEventListener('click', () => {
                this.loadDirectory(file.path);
            });
        } else {
            item.addEventListener('click', () => {
                this.showFileDetails(file);
            });
        }

        return item;
    }

    showFileDetails(file) {
        this.selectedFile = file;
        
        const drawer = document.getElementById('fileDetailsDrawer');
        const content = document.getElementById('fileDetailsContent');
        
        content.innerHTML = '';

        const fields = [
            { label: '文件名', value: file.server_filename || file.filename },
            { label: '路径', value: file.path },
            { label: '大小', value: this.formatFileSize(file.size) },
            { label: '修改时间', value: this.formatTime(file.server_mtime || file.mtime) },
            { label: 'fs_id', value: file.fs_id },
        ];

        if (file.md5) {
            fields.push({ label: 'MD5', value: file.md5 });
        }

        fields.forEach(field => {
            if (field.value !== undefined && field.value !== null) {
                const row = document.createElement('div');
                row.className = 'detail-row';

                const label = document.createElement('div');
                label.className = 'detail-label';
                label.textContent = field.label;

                const value = document.createElement('div');
                value.className = 'detail-value';
                value.textContent = field.value;

                row.appendChild(label);
                row.appendChild(value);
                content.appendChild(row);
            }
        });

        drawer.classList.add('open');
        drawer.style.display = 'flex';
    }

    closeDrawer() {
        const drawer = document.getElementById('fileDetailsDrawer');
        drawer.classList.remove('open');
        setTimeout(() => {
            drawer.style.display = 'none';
        }, 300);
    }

    copyPath() {
        if (!this.selectedFile) return;
        
        const path = this.selectedFile.path;
        navigator.clipboard.writeText(path).then(() => {
            window.controlPanel.showToast('路径已复制', 'success');
        }).catch(err => {
            console.error('Failed to copy path:', err);
            window.controlPanel.showToast('复制失败', 'error');
        });
    }

    queueShare() {
        if (!this.selectedFile) return;
        
        window.controlPanel.showToast('此功能即将推出', 'info');
    }

    formatFileSize(bytes) {
        if (bytes === undefined || bytes === null) return '-';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = parseInt(bytes);
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(2)} ${units[unitIndex]}`;
    }

    formatTime(timestamp) {
        if (!timestamp) return '-';
        
        const date = new Date(parseInt(timestamp) * 1000);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    async fetchAPI(url) {
        return await window.controlPanel.fetchAPI(url);
    }

    showLoadingState() {
        document.getElementById('loadingState').style.display = 'flex';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('filesContainer').style.display = 'none';
    }

    showErrorState(message) {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'flex';
        document.getElementById('emptyState').style.display = 'none';
        document.getElementById('filesContainer').style.display = 'none';
    }

    showEmptyState(message) {
        document.getElementById('emptyMessage').textContent = message;
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'flex';
        document.getElementById('filesContainer').style.display = 'none';
    }

    hideStates() {
        document.getElementById('loadingState').style.display = 'none';
        document.getElementById('errorState').style.display = 'none';
        document.getElementById('emptyState').style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.browseModule = new BrowseModule();
});
