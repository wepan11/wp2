/**
 * Settings Module
 * 
 * Handles settings view functionality:
 * - Load and display current settings
 * - Form validation and submission
 * - Apply settings updates
 * - Broadcast UI preference changes via EventBus
 */

(function() {
    'use strict';

    // State
    let currentSettings = null;
    let isLoading = false;

    // DOM Elements
    const settingsView = document.getElementById('settingsView');
    const loadingState = document.getElementById('settingsLoadingState');
    const settingsContent = document.getElementById('settingsContent');
    const saveBtn = document.getElementById('saveSettingsBtn');

    // Initialize when settings tab is activated
    EventBus.subscribe('tabChanged', (tabName) => {
        if (tabName === 'settings') {
            loadSettings();
        }
    });

    /**
     * Load settings from backend
     */
    async function loadSettings() {
        if (isLoading) return;
        
        isLoading = true;
        showLoading();

        try {
            const apiKey = localStorage.getItem('apiKey');
            if (!apiKey) {
                showToast('请先配置API密钥', 'error');
                return;
            }

            const response = await fetch('/api/control/settings', {
                method: 'GET',
                headers: {
                    'X-API-Key': apiKey
                }
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.error || result.message || '加载设置失败');
            }

            currentSettings = result.data;
            populateForm(currentSettings);
            showContent();

        } catch (error) {
            console.error('Failed to load settings:', error);
            showToast(`加载设置失败: ${error.message}`, 'error');
        } finally {
            isLoading = false;
        }
    }

    /**
     * Populate form fields with settings
     */
    function populateForm(settings) {
        // Throttle settings
        if (settings.throttle) {
            document.getElementById('jitter_ms_min').value = settings.throttle.jitter_ms_min || 500;
            document.getElementById('jitter_ms_max').value = settings.throttle.jitter_ms_max || 1500;
            document.getElementById('ops_per_window').value = settings.throttle.ops_per_window || 50;
            document.getElementById('window_sec').value = settings.throttle.window_sec || 60;
            document.getElementById('window_rest_sec').value = settings.throttle.window_rest_sec || 20;
            document.getElementById('max_consecutive_failures').value = settings.throttle.max_consecutive_failures || 5;
            document.getElementById('pause_sec_on_failure').value = settings.throttle.pause_sec_on_failure || 60;
            document.getElementById('cooldown_on_errno_62_sec').value = settings.throttle['cooldown_on_errno_-62_sec'] || 120;
        }

        // Worker settings
        if (settings.workers) {
            document.getElementById('max_transfer_workers').value = settings.workers.max_transfer_workers || 1;
            document.getElementById('max_share_workers').value = settings.workers.max_share_workers || 1;
        }

        // Rate limit settings
        if (settings.rate_limit) {
            document.getElementById('rate_limit_enabled').checked = settings.rate_limit.enabled !== false;
        }

        // UI settings
        if (settings.ui) {
            document.getElementById('auto_refresh_interval').value = settings.ui.auto_refresh_interval || 5000;
            document.getElementById('api_key_retention').checked = settings.ui.api_key_retention !== false;
        }
    }

    /**
     * Collect form data into settings object
     */
    function collectFormData() {
        return {
            throttle: {
                jitter_ms_min: parseInt(document.getElementById('jitter_ms_min').value),
                jitter_ms_max: parseInt(document.getElementById('jitter_ms_max').value),
                ops_per_window: parseInt(document.getElementById('ops_per_window').value),
                window_sec: parseInt(document.getElementById('window_sec').value),
                window_rest_sec: parseInt(document.getElementById('window_rest_sec').value),
                max_consecutive_failures: parseInt(document.getElementById('max_consecutive_failures').value),
                pause_sec_on_failure: parseInt(document.getElementById('pause_sec_on_failure').value),
                backoff_factor: currentSettings?.throttle?.backoff_factor || 1.5,
                'cooldown_on_errno_-62_sec': parseInt(document.getElementById('cooldown_on_errno_62_sec').value)
            },
            workers: {
                max_transfer_workers: parseInt(document.getElementById('max_transfer_workers').value),
                max_share_workers: parseInt(document.getElementById('max_share_workers').value)
            },
            rate_limit: {
                enabled: document.getElementById('rate_limit_enabled').checked
            },
            ui: {
                auto_refresh_interval: parseInt(document.getElementById('auto_refresh_interval').value),
                api_key_retention: document.getElementById('api_key_retention').checked
            }
        };
    }

    /**
     * Validate form data
     */
    function validateFormData(data) {
        const errors = [];

        // Throttle validation
        if (data.throttle.jitter_ms_min < 0 || data.throttle.jitter_ms_min > 10000) {
            errors.push('最小延迟必须在0-10000毫秒之间');
        }
        if (data.throttle.jitter_ms_max < data.throttle.jitter_ms_min || data.throttle.jitter_ms_max > 10000) {
            errors.push('最大延迟必须在最小延迟和10000毫秒之间');
        }
        if (data.throttle.ops_per_window < 1 || data.throttle.ops_per_window > 1000) {
            errors.push('时间窗口操作数必须在1-1000之间');
        }
        if (data.throttle.window_sec < 1 || data.throttle.window_sec > 3600) {
            errors.push('时间窗口必须在1-3600秒之间');
        }
        if (data.throttle.window_rest_sec < 0 || data.throttle.window_rest_sec > 600) {
            errors.push('窗口休息时间必须在0-600秒之间');
        }
        if (data.throttle.max_consecutive_failures < 1 || data.throttle.max_consecutive_failures > 100) {
            errors.push('最大连续失败次数必须在1-100之间');
        }
        if (data.throttle.pause_sec_on_failure < 0 || data.throttle.pause_sec_on_failure > 3600) {
            errors.push('失败后暂停时间必须在0-3600秒之间');
        }
        if (data.throttle['cooldown_on_errno_-62_sec'] < 0 || data.throttle['cooldown_on_errno_-62_sec'] > 3600) {
            errors.push('错误-62冷却时间必须在0-3600秒之间');
        }

        // Worker validation
        if (data.workers.max_transfer_workers < 1 || data.workers.max_transfer_workers > 10) {
            errors.push('最大转存工作线程必须在1-10之间');
        }
        if (data.workers.max_share_workers < 1 || data.workers.max_share_workers > 10) {
            errors.push('最大分享工作线程必须在1-10之间');
        }

        // UI validation
        if (data.ui.auto_refresh_interval < 1000 || data.ui.auto_refresh_interval > 60000) {
            errors.push('自动刷新间隔必须在1000-60000毫秒之间');
        }

        return errors;
    }

    /**
     * Save settings to backend
     */
    async function saveSettings() {
        const formData = collectFormData();
        const errors = validateFormData(formData);

        if (errors.length > 0) {
            showToast(`验证失败:\n${errors.join('\n')}`, 'error');
            return;
        }

        try {
            saveBtn.disabled = true;
            saveBtn.textContent = '保存中...';

            const apiKey = localStorage.getItem('apiKey');
            const response = await fetch('/api/control/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': apiKey
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.error || result.message || '保存设置失败');
            }

            currentSettings = result.data;
            showToast('✅ 设置已保存并应用到运行中的服务', 'success');

            // Broadcast UI preference changes
            EventBus.publish('settingsUpdated', {
                autoRefreshInterval: formData.ui.auto_refresh_interval,
                apiKeyRetention: formData.ui.api_key_retention
            });

        } catch (error) {
            console.error('Failed to save settings:', error);
            showToast(`保存设置失败: ${error.message}`, 'error');
        } finally {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<span class="icon">💾</span> 保存设置';
        }
    }

    /**
     * Show loading state
     */
    function showLoading() {
        loadingState.style.display = 'block';
        settingsContent.style.display = 'none';
    }

    /**
     * Show content
     */
    function showContent() {
        loadingState.style.display = 'none';
        settingsContent.style.display = 'block';
    }

    /**
     * Show toast notification
     */
    function showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.style.display = 'block';

        setTimeout(() => {
            toast.style.display = 'none';
        }, 5000);
    }

    // Event listeners
    saveBtn.addEventListener('click', saveSettings);

    // Export for testing
    window.SettingsModule = {
        loadSettings,
        saveSettings
    };
})();
