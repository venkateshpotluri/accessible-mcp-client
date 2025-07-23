/**
 * Main JavaScript functionality for Accessible MCP Client
 * Handles UI interactions, accessibility features, and general functionality
 */

(function() {
    'use strict';
    
    // Global state
    const App = {
        settings: {
            highContrast: false,
            fontSize: 'normal',
        },
        init: function() {
            this.loadSettings();
            this.setupEventListeners();
            this.setupAccessibilityControls();
            this.setupModalHandling();
            this.setupFormValidation();
            this.setupFlashMessages();
            this.announcePageLoad();
        },
        
        // Load user preferences from localStorage
        loadSettings: function() {
            try {
                const savedSettings = localStorage.getItem('mcp-client-settings');
                if (savedSettings) {
                    this.settings = { ...this.settings, ...JSON.parse(savedSettings) };
                }
                
                // Apply saved settings
                this.applyHighContrast(this.settings.highContrast);
                this.applyFontSize(this.settings.fontSize);
                
            } catch (error) {
                console.warn('Failed to load settings:', error);
            }
        },
        
        // Save user preferences to localStorage
        saveSettings: function() {
            try {
                localStorage.setItem('mcp-client-settings', JSON.stringify(this.settings));
            } catch (error) {
                console.warn('Failed to save settings:', error);
            }
        },
        
        // Setup main event listeners
        setupEventListeners: function() {
            // Handle keyboard navigation
            document.addEventListener('keydown', this.handleKeyDown.bind(this));
            
            // Handle window resize for responsive updates
            window.addEventListener('resize', this.debounce(this.handleResize.bind(this), 250));
            
            // Handle visibility change for accessibility announcements
            document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
            
            // Handle focus events for better UX
            document.addEventListener('focusin', this.handleFocusIn.bind(this));
            document.addEventListener('focusout', this.handleFocusOut.bind(this));
        },
        
        // Setup accessibility controls
        setupAccessibilityControls: function() {
            // High contrast toggle
            const highContrastBtn = document.getElementById('toggle-high-contrast');
            if (highContrastBtn) {
                highContrastBtn.addEventListener('click', () => {
                    this.toggleHighContrast();
                });
                
                // Update button state
                this.updateHighContrastButton();
            }
            
            // Font size controls
            const increaseFontBtn = document.getElementById('increase-font-size');
            const decreaseFontBtn = document.getElementById('decrease-font-size');
            
            if (increaseFontBtn) {
                increaseFontBtn.addEventListener('click', () => {
                    this.increaseFontSize();
                });
            }
            
            if (decreaseFontBtn) {
                decreaseFontBtn.addEventListener('click', () => {
                    this.decreaseFontSize();
                });
            }
        },
        
        // Toggle high contrast mode
        toggleHighContrast: function() {
            this.settings.highContrast = !this.settings.highContrast;
            this.applyHighContrast(this.settings.highContrast);
            this.updateHighContrastButton();
            this.saveSettings();
            
            const message = this.settings.highContrast ? 
                'High contrast mode enabled' : 'High contrast mode disabled';
            this.announceToUser(message);
        },
        
        // Apply high contrast styles
        applyHighContrast: function(enabled) {
            document.documentElement.setAttribute('data-high-contrast', enabled.toString());
        },
        
        // Update high contrast button appearance
        updateHighContrastButton: function() {
            const button = document.getElementById('toggle-high-contrast');
            if (button) {
                const isEnabled = this.settings.highContrast;
                button.setAttribute('aria-pressed', isEnabled.toString());
                button.title = isEnabled ? 
                    'Disable high contrast mode' : 'Enable high contrast mode';
            }
        },
        
        // Increase font size
        increaseFontSize: function() {
            const sizes = ['small', 'normal', 'large', 'extra-large'];
            const currentIndex = sizes.indexOf(this.settings.fontSize);
            const nextIndex = Math.min(currentIndex + 1, sizes.length - 1);
            
            if (nextIndex !== currentIndex) {
                this.settings.fontSize = sizes[nextIndex];
                this.applyFontSize(this.settings.fontSize);
                this.saveSettings();
                this.announceToUser(`Font size increased to ${this.settings.fontSize}`);
            } else {
                this.announceToUser('Font size is already at maximum');
            }
        },
        
        // Decrease font size
        decreaseFontSize: function() {
            const sizes = ['small', 'normal', 'large', 'extra-large'];
            const currentIndex = sizes.indexOf(this.settings.fontSize);
            const nextIndex = Math.max(currentIndex - 1, 0);
            
            if (nextIndex !== currentIndex) {
                this.settings.fontSize = sizes[nextIndex];
                this.applyFontSize(this.settings.fontSize);
                this.saveSettings();
                this.announceToUser(`Font size decreased to ${this.settings.fontSize}`);
            } else {
                this.announceToUser('Font size is already at minimum');
            }
        },
        
        // Apply font size
        applyFontSize: function(size) {
            document.documentElement.setAttribute('data-font-size', size);
        },
        
        // Setup modal handling
        setupModalHandling: function() {
            // Handle modal triggers
            document.addEventListener('click', (e) => {
                const trigger = e.target.closest('[data-modal-target]');
                if (trigger) {
                    e.preventDefault();
                    const targetId = trigger.getAttribute('data-modal-target');
                    const modal = document.getElementById(targetId);
                    if (modal) {
                        this.openModal(modal);
                    }
                }
                
                // Handle modal close buttons
                const closeBtn = e.target.closest('[data-dismiss="modal"]');
                if (closeBtn) {
                    e.preventDefault();
                    const modal = closeBtn.closest('.modal');
                    if (modal) {
                        this.closeModal(modal);
                    }
                }
            });
            
            // Handle ESC key to close modals
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const openModal = document.querySelector('.modal[aria-hidden="false"]');
                    if (openModal) {
                        this.closeModal(openModal);
                    }
                }
            });
            
            // Handle modal overlay clicks
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('modal__overlay')) {
                    const modal = e.target.closest('.modal');
                    if (modal) {
                        this.closeModal(modal);
                    }
                }
            });
        },
        
        // Open modal with accessibility features
        openModal: function(modal) {
            if (!modal) return;
            
            // Store the element that triggered the modal
            modal._previousFocus = document.activeElement;
            
            // Show modal
            modal.style.display = 'flex';
            modal.setAttribute('aria-hidden', 'false');
            
            // Focus first focusable element
            const focusableElements = this.getFocusableElements(modal);
            if (focusableElements.length > 0) {
                setTimeout(() => {
                    focusableElements[0].focus();
                }, 100);
            }
            
            // Add body class to prevent scrolling
            document.body.classList.add('modal-open');
            
            // Announce modal opening
            const title = modal.querySelector('.modal__title');
            if (title) {
                this.announceToUser(`Dialog opened: ${title.textContent}`);
            }
        },
        
        // Close modal with accessibility features
        closeModal: function(modal) {
            if (!modal) return;
            
            // Hide modal
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            
            // Remove body class
            document.body.classList.remove('modal-open');
            
            // Restore focus to trigger element
            if (modal._previousFocus) {
                modal._previousFocus.focus();
                delete modal._previousFocus;
            }
            
            // Announce modal closing
            this.announceToUser('Dialog closed');
        },
        
        // Get focusable elements within a container
        getFocusableElements: function(container) {
            const focusableSelectors = [
                'button:not([disabled])',
                'input:not([disabled])',
                'select:not([disabled])',
                'textarea:not([disabled])',
                'a[href]',
                '[tabindex]:not([tabindex="-1"])'
            ].join(', ');
            
            return Array.from(container.querySelectorAll(focusableSelectors))
                .filter(el => !el.closest('[hidden]') && !el.closest('[aria-hidden="true"]'));
        },
        
        // Setup form validation
        setupFormValidation: function() {
            // Real-time validation
            document.addEventListener('input', (e) => {
                if (e.target.matches('input, select, textarea')) {
                    this.validateField(e.target);
                }
            });
            
            // Form submission validation
            document.addEventListener('submit', (e) => {
                const form = e.target;
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    this.announceToUser('Please correct the errors in the form');
                }
            });
        },
        
        // Validate individual field
        validateField: function(field) {
            const errorElement = field.parentElement.querySelector('.form-error');
            let isValid = true;
            let errorMessage = '';
            
            // Required field validation
            if (field.hasAttribute('required') && !field.value.trim()) {
                isValid = false;
                errorMessage = 'This field is required';
            }
            
            // Email validation
            if (field.type === 'email' && field.value) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(field.value)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid email address';
                }
            }
            
            // URL validation
            if (field.type === 'url' && field.value) {
                try {
                    new URL(field.value);
                } catch {
                    isValid = false;
                    errorMessage = 'Please enter a valid URL';
                }
            }
            
            // Number validation
            if (field.type === 'number' && field.value) {
                const num = parseFloat(field.value);
                if (isNaN(num)) {
                    isValid = false;
                    errorMessage = 'Please enter a valid number';
                } else {
                    if (field.min && num < parseFloat(field.min)) {
                        isValid = false;
                        errorMessage = `Value must be at least ${field.min}`;
                    }
                    if (field.max && num > parseFloat(field.max)) {
                        isValid = false;
                        errorMessage = `Value must be no more than ${field.max}`;
                    }
                }
            }
            
            // Update field state
            field.setAttribute('aria-invalid', (!isValid).toString());
            
            if (errorElement) {
                errorElement.textContent = errorMessage;
                if (!isValid) {
                    errorElement.setAttribute('role', 'alert');
                } else {
                    errorElement.removeAttribute('role');
                }
            }
            
            return isValid;
        },
        
        // Validate entire form
        validateForm: function(form) {
            const fields = form.querySelectorAll('input, select, textarea');
            let isValid = true;
            let firstInvalidField = null;
            
            fields.forEach(field => {
                const fieldValid = this.validateField(field);
                if (!fieldValid) {
                    isValid = false;
                    if (!firstInvalidField) {
                        firstInvalidField = field;
                    }
                }
            });
            
            // Focus first invalid field
            if (firstInvalidField) {
                firstInvalidField.focus();
            }
            
            return isValid;
        },
        
        // Setup flash message handling
        setupFlashMessages: function() {
            document.addEventListener('click', (e) => {
                const closeBtn = e.target.closest('.flash-message__close');
                if (closeBtn) {
                    const message = closeBtn.closest('.flash-message');
                    if (message) {
                        this.dismissFlashMessage(message);
                    }
                }
            });
            
            // Auto-dismiss success messages after 5 seconds
            const successMessages = document.querySelectorAll('.flash-message--success');
            successMessages.forEach(message => {
                setTimeout(() => {
                    this.dismissFlashMessage(message);
                }, 5000);
            });
        },
        
        // Dismiss flash message
        dismissFlashMessage: function(message) {
            message.style.opacity = '0';
            message.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                message.remove();
            }, 200);
            
            this.announceToUser('Message dismissed');
        },
        
        // Handle keyboard navigation
        handleKeyDown: function(e) {
            // Handle tab trapping in modals
            const openModal = document.querySelector('.modal[aria-hidden="false"]');
            if (openModal && e.key === 'Tab') {
                this.trapFocus(e, openModal);
            }
            
            // Handle arrow key navigation in radio groups
            if (e.target.type === 'radio' && ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                this.handleRadioNavigation(e);
            }
        },
        
        // Trap focus within modal
        trapFocus: function(e, modal) {
            const focusableElements = this.getFocusableElements(modal);
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];
            
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        },
        
        // Handle radio button arrow key navigation
        handleRadioNavigation: function(e) {
            e.preventDefault();
            
            const currentRadio = e.target;
            const radioGroup = currentRadio.closest('[role="radiogroup"]') || 
                             currentRadio.form.querySelector(`[name="${currentRadio.name}"]`).closest('fieldset');
            
            if (!radioGroup) return;
            
            const radios = Array.from(radioGroup.querySelectorAll(`input[name="${currentRadio.name}"]`));
            const currentIndex = radios.indexOf(currentRadio);
            
            let nextIndex;
            if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
                nextIndex = currentIndex === 0 ? radios.length - 1 : currentIndex - 1;
            } else {
                nextIndex = currentIndex === radios.length - 1 ? 0 : currentIndex + 1;
            }
            
            const nextRadio = radios[nextIndex];
            nextRadio.checked = true;
            nextRadio.focus();
            
            // Trigger change event
            nextRadio.dispatchEvent(new Event('change', { bubbles: true }));
        },
        
        // Handle window resize
        handleResize: function() {
            // Update any responsive components
            this.updateResponsiveElements();
        },
        
        // Handle visibility change
        handleVisibilityChange: function() {
            if (!document.hidden) {
                // Page became visible, refresh dynamic content if needed
                this.refreshDynamicContent();
            }
        },
        
        // Handle focus in events
        handleFocusIn: function(e) {
            // Add focus class to parent elements for styling
            const focusableElement = e.target;
            const parentCard = focusableElement.closest('.card');
            if (parentCard) {
                parentCard.classList.add('has-focus');
            }
        },
        
        // Handle focus out events
        handleFocusOut: function(e) {
            // Remove focus class from parent elements
            const focusableElement = e.target;
            const parentCard = focusableElement.closest('.card');
            if (parentCard) {
                parentCard.classList.remove('has-focus');
            }
        },
        
        // Update responsive elements
        updateResponsiveElements: function() {
            // Update any elements that need responsive adjustments
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                const wrapper = table.parentElement;
                if (wrapper && wrapper.classList.contains('table-responsive')) {
                    const isOverflowing = table.scrollWidth > wrapper.clientWidth;
                    wrapper.setAttribute('aria-label', 
                        isOverflowing ? 'Scrollable table' : 'Table');
                }
            });
        },
        
        // Refresh dynamic content
        refreshDynamicContent: function() {
            // Override in specific pages as needed
        },
        
        // Announce page load for screen readers
        announcePageLoad: function() {
            const pageTitle = document.querySelector('.page-title');
            if (pageTitle) {
                setTimeout(() => {
                    this.announceToUser(`Page loaded: ${pageTitle.textContent}`);
                }, 1000);
            }
        },
        
        // Announce message to screen readers
        announceToUser: function(message, priority = 'polite') {
            const announcerId = priority === 'assertive' ? 
                'error-announcements' : 'status-announcements';
            const announcer = document.getElementById(announcerId);
            
            if (announcer) {
                announcer.textContent = message;
                
                // Clear after announcement
                setTimeout(() => {
                    announcer.textContent = '';
                }, 1000);
            }
        },
        
        // Utility: Debounce function calls
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func.apply(this, args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Utility: Format date for display
        formatDate: function(dateString) {
            try {
                const date = new Date(dateString);
                return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            } catch (error) {
                return dateString;
            }
        },
        
        // Utility: Show loading state
        showLoading: function(element, message = 'Loading...') {
            if (!element) return;
            
            element.setAttribute('aria-busy', 'true');
            element.innerHTML = `
                <div class="loading-state">
                    <div class="loading-spinner" role="status" aria-label="${message}">
                        <span class="sr-only">${message}</span>
                    </div>
                </div>
            `;
        },
        
        // Utility: Hide loading state
        hideLoading: function(element) {
            if (!element) return;
            
            element.removeAttribute('aria-busy');
        },
        
        // Utility: Copy text to clipboard
        copyToClipboard: async function(text) {
            try {
                await navigator.clipboard.writeText(text);
                this.announceToUser('Copied to clipboard');
                return true;
            } catch (error) {
                console.error('Failed to copy to clipboard:', error);
                this.announceToUser('Failed to copy to clipboard', 'assertive');
                return false;
            }
        }
        
    };
    
    // Initialize app when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => App.init());
    } else {
        App.init();
    }
    
    // Make App globally available
    window.MCPClientApp = App;
    
})();
