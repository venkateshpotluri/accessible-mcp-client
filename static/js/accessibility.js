/**
 * Accessibility enhancements and utilities
 * Additional accessibility features beyond the main app
 */

(function() {
    'use strict';
    
    const AccessibilityEnhancer = {
        
        init: function() {
            this.setupKeyboardShortcuts();
            this.setupHeadingNavigation();
            this.setupTableEnhancements();
            this.setupFormEnhancements();
            this.setupColorContrastWarnings();
            this.setupMotionControls();
            this.monitorAccessibilityIssues();
        },
        
        // Setup keyboard shortcuts for accessibility
        setupKeyboardShortcuts: function() {
            document.addEventListener('keydown', (e) => {
                // Alt + 1: Skip to main content
                if (e.altKey && e.key === '1') {
                    e.preventDefault();
                    const mainContent = document.getElementById('main-content') || 
                                      document.querySelector('main');
                    if (mainContent) {
                        mainContent.focus();
                        this.announceShortcut('Skipped to main content');
                    }
                }
                
                // Alt + 2: Skip to navigation
                if (e.altKey && e.key === '2') {
                    e.preventDefault();
                    const nav = document.querySelector('nav[role="navigation"]') || 
                               document.querySelector('nav');
                    if (nav) {
                        const firstLink = nav.querySelector('a');
                        if (firstLink) {
                            firstLink.focus();
                            this.announceShortcut('Skipped to navigation');
                        }
                    }
                }
                
                // Alt + 3: Skip to search (if available)
                if (e.altKey && e.key === '3') {
                    e.preventDefault();
                    const searchInput = document.querySelector('input[type="search"]') ||
                                       document.querySelector('#search');
                    if (searchInput) {
                        searchInput.focus();
                        this.announceShortcut('Skipped to search');
                    }
                }
                
                // Alt + H: Navigate headings
                if (e.altKey && e.key === 'h') {
                    e.preventDefault();
                    this.showHeadingNavigation();
                }
                
                // Alt + L: Navigate landmarks
                if (e.altKey && e.key === 'l') {
                    e.preventDefault();
                    this.showLandmarkNavigation();
                }
                
                // Alt + T: Navigate tables
                if (e.altKey && e.key === 't') {
                    e.preventDefault();
                    this.showTableNavigation();
                }
            });
        },
        
        // Setup heading navigation
        setupHeadingNavigation: function() {
            this.headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
                .map((heading, index) => ({
                    element: heading,
                    level: parseInt(heading.tagName.substr(1)),
                    text: heading.textContent.trim(),
                    index: index
                }));
            
            // Add IDs to headings without them
            this.headings.forEach((heading, index) => {
                if (!heading.element.id) {
                    heading.element.id = `heading-${index}`;
                }
            });
        },
        
        // Show heading navigation dialog
        showHeadingNavigation: function() {
            if (this.headings.length === 0) {
                this.announceShortcut('No headings found on this page');
                return;
            }
            
            const dialog = this.createNavigationDialog('Headings', this.headings.map(h => ({
                text: `${'  '.repeat(h.level - 1)}${h.text} (Level ${h.level})`,
                action: () => {
                    h.element.focus();
                    h.element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            })));
            
            document.body.appendChild(dialog);
            this.showDialog(dialog);
        },
        
        // Show landmark navigation
        showLandmarkNavigation: function() {
            const landmarks = Array.from(document.querySelectorAll('[role], main, nav, aside, section, article, header, footer'))
                .filter(el => {
                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    return ['main', 'navigation', 'banner', 'contentinfo', 'complementary', 
                           'region', 'search', 'form'].includes(role) ||
                           ['main', 'nav', 'aside', 'section', 'article', 'header', 'footer'].includes(role);
                })
                .map(el => {
                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    const label = el.getAttribute('aria-label') || 
                                 el.getAttribute('aria-labelledby') && 
                                 document.getElementById(el.getAttribute('aria-labelledby'))?.textContent ||
                                 el.querySelector('h1, h2, h3, h4, h5, h6')?.textContent ||
                                 role;
                    
                    return {
                        element: el,
                        text: `${role}: ${label}`,
                        action: () => {
                            el.focus();
                            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    };
                });
            
            if (landmarks.length === 0) {
                this.announceShortcut('No landmarks found on this page');
                return;
            }
            
            const dialog = this.createNavigationDialog('Landmarks', landmarks);
            document.body.appendChild(dialog);
            this.showDialog(dialog);
        },
        
        // Show table navigation
        showTableNavigation: function() {
            const tables = Array.from(document.querySelectorAll('table'))
                .map((table, index) => {
                    const caption = table.querySelector('caption')?.textContent ||
                                   table.getAttribute('aria-label') ||
                                   `Table ${index + 1}`;
                    
                    return {
                        element: table,
                        text: caption,
                        action: () => {
                            table.focus();
                            table.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    };
                });
            
            if (tables.length === 0) {
                this.announceShortcut('No tables found on this page');
                return;
            }
            
            const dialog = this.createNavigationDialog('Tables', tables);
            document.body.appendChild(dialog);
            this.showDialog(dialog);
        },
        
        // Create navigation dialog
        createNavigationDialog: function(title, items) {
            const dialog = document.createElement('div');
            dialog.className = 'accessibility-dialog';
            dialog.setAttribute('role', 'dialog');
            dialog.setAttribute('aria-modal', 'true');
            dialog.setAttribute('aria-labelledby', 'accessibility-dialog-title');
            
            dialog.innerHTML = `
                <div class="accessibility-dialog__overlay"></div>
                <div class="accessibility-dialog__content">
                    <header class="accessibility-dialog__header">
                        <h2 id="accessibility-dialog-title">${title} Navigation</h2>
                        <button type="button" class="accessibility-dialog__close" aria-label="Close dialog">×</button>
                    </header>
                    <div class="accessibility-dialog__body">
                        <p class="accessibility-dialog__instructions">
                            Use arrow keys to navigate, Enter to select, or Escape to close.
                        </p>
                        <ul class="accessibility-dialog__list" role="listbox" aria-labelledby="accessibility-dialog-title">
                            ${items.map((item, index) => `
                                <li class="accessibility-dialog__item" role="option" tabindex="${index === 0 ? '0' : '-1'}" data-index="${index}">
                                    ${item.text}
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                </div>
            `;
            
            // Add event listeners
            const closeBtn = dialog.querySelector('.accessibility-dialog__close');
            const list = dialog.querySelector('.accessibility-dialog__list');
            const items_elements = dialog.querySelectorAll('.accessibility-dialog__item');
            
            let currentIndex = 0;
            
            closeBtn.addEventListener('click', () => this.closeDialog(dialog));
            
            dialog.addEventListener('keydown', (e) => {
                switch (e.key) {
                    case 'Escape':
                        e.preventDefault();
                        this.closeDialog(dialog);
                        break;
                        
                    case 'ArrowDown':
                        e.preventDefault();
                        currentIndex = (currentIndex + 1) % items.length;
                        this.updateDialogFocus(items_elements, currentIndex);
                        break;
                        
                    case 'ArrowUp':
                        e.preventDefault();
                        currentIndex = (currentIndex - 1 + items.length) % items.length;
                        this.updateDialogFocus(items_elements, currentIndex);
                        break;
                        
                    case 'Enter':
                        e.preventDefault();
                        items[currentIndex].action();
                        this.closeDialog(dialog);
                        break;
                        
                    case 'Home':
                        e.preventDefault();
                        currentIndex = 0;
                        this.updateDialogFocus(items_elements, currentIndex);
                        break;
                        
                    case 'End':
                        e.preventDefault();
                        currentIndex = items.length - 1;
                        this.updateDialogFocus(items_elements, currentIndex);
                        break;
                }
            });
            
            // Click handlers for items
            items_elements.forEach((element, index) => {
                element.addEventListener('click', () => {
                    items[index].action();
                    this.closeDialog(dialog);
                });
            });
            
            return dialog;
        },
        
        // Update focus in navigation dialog
        updateDialogFocus: function(items, currentIndex) {
            items.forEach((item, index) => {
                item.tabIndex = index === currentIndex ? 0 : -1;
                item.setAttribute('aria-selected', (index === currentIndex).toString());
            });
            items[currentIndex].focus();
        },
        
        // Show dialog
        showDialog: function(dialog) {
            dialog.style.display = 'flex';
            
            // Focus first item
            setTimeout(() => {
                const firstItem = dialog.querySelector('.accessibility-dialog__item');
                if (firstItem) {
                    firstItem.focus();
                }
            }, 100);
        },
        
        // Close dialog
        closeDialog: function(dialog) {
            dialog.style.display = 'none';
            dialog.remove();
        },
        
        // Setup table enhancements
        setupTableEnhancements: function() {
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {
                // Add scope to headers if missing
                const headers = table.querySelectorAll('th');
                headers.forEach(header => {
                    if (!header.hasAttribute('scope')) {
                        // Determine scope based on position
                        const row = header.closest('tr');
                        const rowIndex = Array.from(table.querySelectorAll('tr')).indexOf(row);
                        const cellIndex = Array.from(row.children).indexOf(header);
                        
                        if (rowIndex === 0) {
                            header.setAttribute('scope', 'col');
                        } else if (cellIndex === 0) {
                            header.setAttribute('scope', 'row');
                        }
                    }
                });
                
                // Add table summary if missing
                if (!table.querySelector('caption') && !table.hasAttribute('aria-label')) {
                    const rowCount = table.querySelectorAll('tr').length;
                    const colCount = table.querySelector('tr')?.children.length || 0;
                    table.setAttribute('aria-label', `Data table with ${rowCount} rows and ${colCount} columns`);
                }
                
                // Make table responsive
                if (!table.closest('.table-responsive')) {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'table-responsive';
                    wrapper.setAttribute('tabindex', '0');
                    wrapper.setAttribute('role', 'region');
                    wrapper.setAttribute('aria-label', 'Scrollable table');
                    
                    table.parentNode.insertBefore(wrapper, table);
                    wrapper.appendChild(table);
                }
            });
        },
        
        // Setup form enhancements
        setupFormEnhancements: function() {
            // Add required indicators
            const requiredFields = document.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                const label = document.querySelector(`label[for="${field.id}"]`);
                if (label && !label.textContent.includes('*')) {
                    label.innerHTML += ' <span class="required-indicator" aria-label="required">*</span>';
                }
            });
            
            // Enhance fieldsets
            const fieldsets = document.querySelectorAll('fieldset');
            fieldsets.forEach(fieldset => {
                const legend = fieldset.querySelector('legend');
                if (legend && !fieldset.hasAttribute('aria-labelledby')) {
                    if (!legend.id) {
                        legend.id = `legend-${Math.random().toString(36).substr(2, 9)}`;
                    }
                    fieldset.setAttribute('aria-labelledby', legend.id);
                }
            });
            
            // Enhance select elements
            const selects = document.querySelectorAll('select');
            selects.forEach(select => {
                if (!select.hasAttribute('aria-describedby')) {
                    const helpText = select.parentElement.querySelector('.form-help');
                    if (helpText) {
                        if (!helpText.id) {
                            helpText.id = `help-${Math.random().toString(36).substr(2, 9)}`;
                        }
                        select.setAttribute('aria-describedby', helpText.id);
                    }
                }
            });
        },
        
        // Setup color contrast warnings
        setupColorContrastWarnings: function() {
            if (window.MCPClientApp && window.MCPClientApp.settings.highContrast) {
                return; // Skip if high contrast mode is already enabled
            }
            
            // Check for potential contrast issues
            this.checkColorContrast();
        },
        
        // Check color contrast
        checkColorContrast: function() {
            // This is a simplified contrast checker
            // In a real implementation, you might use a more sophisticated library
            
            const elements = document.querySelectorAll('*');
            let contrastIssues = 0;
            
            elements.forEach(element => {
                const style = window.getComputedStyle(element);
                const backgroundColor = style.backgroundColor;
                const color = style.color;
                
                // Skip elements with transparent or inherited colors
                if (backgroundColor === 'rgba(0, 0, 0, 0)' || 
                    backgroundColor === 'transparent' ||
                    color === 'rgba(0, 0, 0, 0)' ||
                    color === 'transparent') {
                    return;
                }
                
                // Simple contrast check (this is very basic)
                if (this.hasLowContrast(color, backgroundColor)) {
                    contrastIssues++;
                    element.setAttribute('data-contrast-warning', 'true');
                }
            });
            
            if (contrastIssues > 0) {
                console.warn(`Found ${contrastIssues} potential color contrast issues`);
            }
        },
        
        // Simple contrast detection (placeholder for real implementation)
        hasLowContrast: function(foreground, background) {
            // This is a placeholder - real implementation would calculate
            // actual contrast ratios based on RGB values
            return false;
        },
        
        // Setup motion controls
        setupMotionControls: function() {
            // Respect prefers-reduced-motion
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            
            if (prefersReducedMotion) {
                document.documentElement.setAttribute('data-reduced-motion', 'true');
                this.announceToUser('Reduced motion mode detected');
            }
            
            // Listen for changes
            window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (e) => {
                document.documentElement.setAttribute('data-reduced-motion', e.matches.toString());
                this.announceToUser(e.matches ? 'Reduced motion enabled' : 'Reduced motion disabled');
            });
        },
        
        // Monitor accessibility issues
        monitorAccessibilityIssues: function() {
            // Check for common accessibility issues
            this.checkMissingAltText();
            this.checkMissingLabels();
            this.checkHeadingStructure();
            this.checkFocusManagement();
        },
        
        // Check for images without alt text
        checkMissingAltText: function() {
            const images = document.querySelectorAll('img');
            const missingAlt = Array.from(images).filter(img => 
                !img.hasAttribute('alt') && !img.hasAttribute('aria-label')
            );
            
            if (missingAlt.length > 0) {
                console.warn(`Found ${missingAlt.length} images without alt text`);
                missingAlt.forEach(img => {
                    img.setAttribute('data-accessibility-warning', 'missing-alt');
                });
            }
        },
        
        // Check for form controls without labels
        checkMissingLabels: function() {
            const formControls = document.querySelectorAll('input, select, textarea');
            const missingLabels = Array.from(formControls).filter(control => {
                if (control.type === 'hidden' || control.type === 'submit' || control.type === 'button') {
                    return false;
                }
                
                const hasLabel = document.querySelector(`label[for="${control.id}"]`) ||
                                control.hasAttribute('aria-label') ||
                                control.hasAttribute('aria-labelledby');
                
                return !hasLabel;
            });
            
            if (missingLabels.length > 0) {
                console.warn(`Found ${missingLabels.length} form controls without labels`);
                missingLabels.forEach(control => {
                    control.setAttribute('data-accessibility-warning', 'missing-label');
                });
            }
        },
        
        // Check heading structure
        checkHeadingStructure: function() {
            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
                .map(h => parseInt(h.tagName.substr(1)));
            
            let hasIssues = false;
            
            // Check for missing h1
            if (!headings.includes(1)) {
                console.warn('Page is missing an h1 heading');
                hasIssues = true;
            }
            
            // Check for skipped heading levels
            for (let i = 1; i < headings.length; i++) {
                if (headings[i] > headings[i-1] + 1) {
                    console.warn(`Heading level skipped: h${headings[i-1]} followed by h${headings[i]}`);
                    hasIssues = true;
                }
            }
            
            if (hasIssues) {
                document.documentElement.setAttribute('data-heading-issues', 'true');
            }
        },
        
        // Check focus management
        checkFocusManagement: function() {
            // Check for focusable elements without visible focus indicators
            const focusableElements = document.querySelectorAll(
                'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            focusableElements.forEach(element => {
                element.addEventListener('focus', () => {
                    // Check if focus is visible
                    const style = window.getComputedStyle(element);
                    const outline = style.outline;
                    const outlineWidth = style.outlineWidth;
                    
                    if (outline === 'none' || outlineWidth === '0px') {
                        element.setAttribute('data-accessibility-warning', 'no-focus-indicator');
                    }
                });
            });
        },
        
        // Announce accessibility shortcut
        announceShortcut: function(message) {
            if (window.MCPClientApp) {
                window.MCPClientApp.announceToUser(message);
            }
        },
        
        // Announce to user (fallback)
        announceToUser: function(message) {
            const announcer = document.getElementById('status-announcements');
            if (announcer) {
                announcer.textContent = message;
                setTimeout(() => {
                    announcer.textContent = '';
                }, 1000);
            }
        }
    };
    
    // Add styles for accessibility dialog
    const style = document.createElement('style');
    style.textContent = `
        .accessibility-dialog {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        }
        
        .accessibility-dialog__content {
            background: var(--color-bg);
            border: var(--border-width) solid var(--color-border);
            border-radius: var(--border-radius);
            max-width: 500px;
            max-height: 70vh;
            width: 90%;
            display: flex;
            flex-direction: column;
        }
        
        .accessibility-dialog__header {
            padding: var(--spacing-md);
            border-bottom: var(--border-width) solid var(--color-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .accessibility-dialog__header h2 {
            margin: 0;
            font-size: var(--font-size-lg);
        }
        
        .accessibility-dialog__close {
            background: none;
            border: none;
            font-size: var(--font-size-xl);
            cursor: pointer;
            padding: var(--spacing-xs);
            border-radius: var(--border-radius-sm);
        }
        
        .accessibility-dialog__close:hover {
            background: var(--color-bg-alt);
        }
        
        .accessibility-dialog__close:focus {
            outline: var(--border-width-thick) solid var(--color-focus);
            outline-offset: 2px;
        }
        
        .accessibility-dialog__body {
            padding: var(--spacing-md);
            flex: 1;
            overflow-y: auto;
        }
        
        .accessibility-dialog__instructions {
            margin-bottom: var(--spacing-md);
            font-size: var(--font-size-sm);
            color: var(--color-text-muted);
        }
        
        .accessibility-dialog__list {
            list-style: none;
            margin: 0;
            padding: 0;
        }
        
        .accessibility-dialog__item {
            padding: var(--spacing-sm) var(--spacing-md);
            cursor: pointer;
            border-radius: var(--border-radius-sm);
            margin-bottom: var(--spacing-xs);
        }
        
        .accessibility-dialog__item:hover,
        .accessibility-dialog__item:focus {
            background: var(--color-bg-alt);
            outline: none;
        }
        
        .accessibility-dialog__item[aria-selected="true"] {
            background: var(--color-primary);
            color: var(--color-bg);
        }
        
        [data-accessibility-warning] {
            position: relative;
        }
        
        [data-accessibility-warning="missing-alt"]::after,
        [data-accessibility-warning="missing-label"]::after,
        [data-accessibility-warning="no-focus-indicator"]::after {
            content: "⚠️";
            position: absolute;
            top: 0;
            right: 0;
            background: var(--color-warning);
            color: var(--color-text);
            font-size: 12px;
            padding: 2px 4px;
            border-radius: 2px;
            z-index: 1000;
        }
    `;
    document.head.appendChild(style);
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => AccessibilityEnhancer.init());
    } else {
        AccessibilityEnhancer.init();
    }
    
    // Make globally available
    window.AccessibilityEnhancer = AccessibilityEnhancer;
    
})();
