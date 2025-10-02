// Emergency Response Agent - Main JavaScript

// Global variables
let emergencyStatus = 'normal'; // normal, monitoring, active
let dashboardInterval = null;
let weatherInterval = null;
let notificationQueue = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    updateEmergencyStatus();
    
    // Start background services
    if (window.location.pathname === '/dashboard') {
        startDashboardServices();
    }
});

// Application initialization
function initializeApp() {
    console.log('Emergency Response Agent initialized');
    
    // Add loading animation to page
    document.body.classList.add('fade-in-up');
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Check for emergency status in localStorage
    const savedStatus = localStorage.getItem('emergency_status');
    if (savedStatus) {
        emergencyStatus = savedStatus;
        updateEmergencyStatus();
    }
}

// Event listeners setup
function setupEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl+N or Cmd+N for new scenario
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && !e.target.matches('input, textarea, select')) {
            e.preventDefault();
            window.location.href = '/create_scenario';
        }
        
        // Ctrl+D or Cmd+D for dashboard
        if ((e.ctrlKey || e.metaKey) && e.key === 'd' && !e.target.matches('input, textarea, select')) {
            e.preventDefault();
            window.location.href = '/dashboard';
        }
        
        // Escape key to close modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    });
    
    // Auto-save forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', debounce(autoSaveForm, 1000));
        });
    });
    
    // Network status monitoring
    window.addEventListener('online', function() {
        showToast('Connection restored', 'success');
        updateConnectionStatus(true);
    });
    
    window.addEventListener('offline', function() {
        showToast('Connection lost - working offline', 'warning');
        updateConnectionStatus(false);
    });
}

// Emergency status management
function updateEmergencyStatus(status = null) {
    if (status) {
        emergencyStatus = status;
        localStorage.setItem('emergency_status', status);
    }
    
    // Create or update status indicator
    let statusIndicator = document.getElementById('emergency-status-indicator');
    if (!statusIndicator) {
        statusIndicator = document.createElement('div');
        statusIndicator.id = 'emergency-status-indicator';
        statusIndicator.className = 'emergency-status';
        document.body.appendChild(statusIndicator);
    }
    
    // Update status indicator
    statusIndicator.className = `emergency-status ${emergencyStatus}`;
    
    const statusMessages = {
        normal: '✓ All Systems Normal',
        monitoring: '⚠ Monitoring Situation',
        active: '🚨 Emergency Active'
    };
    
    statusIndicator.textContent = statusMessages[emergencyStatus] || statusMessages.normal;
}

// Dashboard services
function startDashboardServices() {
    // Real-time updates every 30 seconds
    dashboardInterval = setInterval(function() {
        updateDashboardData();
    }, 30000);
    
    // Weather updates every 5 minutes
    weatherInterval = setInterval(function() {
        updateWeatherWidget();
    }, 300000);
    
    // Check for new notifications
    setInterval(checkNotifications, 10000);
}

// Dashboard data updates
async function updateDashboardData() {
    try {
        const response = await fetch('/api/scenarios');
        const scenarios = await response.json();
        
        // Update scenario counts
        updateScenarioCounts(scenarios);
        
        // Update recent activity
        updateRecentActivity(scenarios);
        
        // Check for critical scenarios
        const criticalScenarios = scenarios.filter(s => s.severity === 'Critical');
        if (criticalScenarios.length > 0) {
            updateEmergencyStatus('active');
        } else if (scenarios.length > 0) {
            updateEmergencyStatus('monitoring');
        } else {
            updateEmergencyStatus('normal');
        }
        
    } catch (error) {
        console.error('Error updating dashboard:', error);
        showToast('Error updating dashboard data', 'error');
    }
}

// Weather widget updates
async function updateWeatherWidget() {
    const weatherWidget = document.getElementById('weather-widget');
    if (!weatherWidget) return;
    
    try {
        const response = await fetch('/api/weather?location=current');
        const weather = await response.json();
        
        weatherWidget.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="fas ${getWeatherIcon(weather.condition)} fa-2x text-primary"></i>
                </div>
                <div>
                    <h5 class="mb-1">${weather.temperature}°F</h5>
                    <p class="mb-1">${weather.description}</p>
                    <small class="text-muted">
                        <i class="fas fa-wind me-1"></i>${weather.wind_speed} mph
                        <span class="ms-2">
                            <i class="fas fa-eye me-1"></i>${weather.visibility || 'Good'}
                        </span>
                    </small>
                </div>
            </div>
        `;
        
        // Check for severe weather alerts
        if (weather.alerts && weather.alerts.length > 0) {
            weather.alerts.forEach(alert => {
                showToast(`Weather Alert: ${alert.title}`, 'warning', 10000);
            });
        }
        
    } catch (error) {
        console.error('Error updating weather:', error);
    }
}

// Notification system
function checkNotifications() {
    // Simulate checking for new notifications
    // In a real app, this would make an API call
    
    const notifications = [
        { type: 'info', message: 'Weather data updated', timestamp: new Date() },
        { type: 'warning', message: 'Resource allocation at 85%', timestamp: new Date() }
    ];
    
    notifications.forEach(notification => {
        if (!isNotificationSeen(notification)) {
            showNotification(notification);
            markNotificationAsSeen(notification);
        }
    });
}

function showNotification(notification) {
    // Create notification element
    const notificationEl = document.createElement('div');
    notificationEl.className = `alert alert-${notification.type} alert-dismissible fade show position-fixed`;
    notificationEl.style.cssText = 'top: 100px; right: 20px; z-index: 1050; max-width: 350px;';
    
    notificationEl.innerHTML = `
        ${notification.message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notificationEl);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notificationEl.parentNode) {
            notificationEl.remove();
        }
    }, 5000);
}

function isNotificationSeen(notification) {
    const seen = JSON.parse(localStorage.getItem('seen_notifications') || '[]');
    return seen.includes(notification.message + notification.timestamp.toISOString());
}

function markNotificationAsSeen(notification) {
    const seen = JSON.parse(localStorage.getItem('seen_notifications') || '[]');
    seen.push(notification.message + notification.timestamp.toISOString());
    localStorage.setItem('seen_notifications', JSON.stringify(seen.slice(-50))); // Keep last 50
}

// Toast notification system
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${getToastColor(type)} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas ${getToastIcon(type)} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Initialize and show toast
    const toastElement = document.getElementById(toastId);
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    } else {
        // Fallback if Bootstrap is not available
        setTimeout(() => {
            toastElement.remove();
        }, duration);
    }
}

function getToastColor(type) {
    const colors = {
        success: 'success',
        error: 'danger',
        warning: 'warning',
        info: 'primary'
    };
    return colors[type] || 'primary';
}

function getToastIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || 'fa-info-circle';
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minutes ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} days ago`;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function getWeatherIcon(condition) {
    const icons = {
        'clear': 'fa-sun',
        'cloudy': 'fa-cloud',
        'rainy': 'fa-cloud-rain',
        'stormy': 'fa-bolt',
        'snowy': 'fa-snowflake',
        'foggy': 'fa-smog'
    };
    return icons[condition] || 'fa-cloud';
}

function updateConnectionStatus(isOnline) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.className = `badge ${isOnline ? 'bg-success' : 'bg-danger'}`;
        statusElement.textContent = isOnline ? 'Online' : 'Offline';
    }
}

function autoSaveForm(event) {
    const form = event.target.closest('form');
    if (!form || !form.id) return;
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem(`autosave_${form.id}`, JSON.stringify({
        data: data,
        timestamp: new Date().toISOString()
    }));
    
    console.log('Form auto-saved:', form.id);
}

function loadAutoSavedForm(formId) {
    const saved = localStorage.getItem(`autosave_${formId}`);
    if (!saved) return false;
    
    try {
        const { data, timestamp } = JSON.parse(saved);
        const form = document.getElementById(formId);
        if (!form) return false;
        
        // Check if save is recent (within 24 hours)
        const saveTime = new Date(timestamp);
        const now = new Date();
        const hoursDiff = (now - saveTime) / (1000 * 60 * 60);
        
        if (hoursDiff > 24) {
            localStorage.removeItem(`autosave_${formId}`);
            return false;
        }
        
        // Fill form with saved data
        Object.keys(data).forEach(key => {
            const element = form.querySelector(`[name="${key}"]`);
            if (element) {
                if (element.type === 'checkbox' || element.type === 'radio') {
                    element.checked = element.value === data[key];
                } else {
                    element.value = data[key];
                }
            }
        });
        
        return true;
    } catch (error) {
        console.error('Error loading auto-saved form:', error);
        return false;
    }
}

// API helper functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    // Clear intervals
    if (dashboardInterval) clearInterval(dashboardInterval);
    if (weatherInterval) clearInterval(weatherInterval);
    
    // Save any unsaved form data
    const forms = document.querySelectorAll('form[id]');
    forms.forEach(form => {
        const event = { target: form.querySelector('input, textarea, select') };
        if (event.target) autoSaveForm(event);
    });
});

// Accessibility enhancements
document.addEventListener('keydown', function(e) {
    // Skip to main content with Alt+M
    if (e.altKey && e.key === 'm') {
        const main = document.querySelector('main');
        if (main) {
            main.focus();
            main.scrollIntoView();
        }
    }
    
    // Focus search with Alt+S
    if (e.altKey && e.key === 's') {
        const search = document.querySelector('input[type="search"]');
        if (search) {
            search.focus();
        }
    }
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log('Page load time:', loadTime + 'ms');
        
        // Report slow loads
        if (loadTime > 3000) {
            console.warn('Slow page load detected:', loadTime + 'ms');
        }
    });
}

// Export functions for use in other scripts
window.EmergencyApp = {
    showToast,
    updateEmergencyStatus,
    formatTimeAgo,
    formatNumber,
    apiRequest
};