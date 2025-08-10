/**
 * Court Data Fetcher - Main JavaScript File
 * Handles UI interactions and form validations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize utility functions
    initializeUtilities();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validations
 */
function initializeFormValidations() {
    // Case number validation
    const caseNumberInputs = document.querySelectorAll('input[name="case_number"]');
    caseNumberInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            validateCaseNumber(e.target);
        });
        
        input.addEventListener('paste', function(e) {
            setTimeout(() => validateCaseNumber(e.target), 10);
        });
    });
    
    // Filing year validation
    const filingYearSelects = document.querySelectorAll('select[name="filing_year"]');
    filingYearSelects.forEach(function(select) {
        select.addEventListener('change', function(e) {
            validateFilingYear(e.target);
        });
    });
    
    // Search form submission
    const searchForms = document.querySelectorAll('#searchForm');
    searchForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!validateSearchForm(form)) {
                e.preventDefault();
                return false;
            }
            handleFormSubmission(form);
        });
    });
}

/**
 * Validate case number input
 */
function validateCaseNumber(input) {
    const value = input.value.trim();
    const isValid = /^[0-9]*$/.test(value) && value.length > 0;
    
    // Remove existing validation classes
    input.classList.remove('is-valid', 'is-invalid');
    
    // Add appropriate validation class
    if (value === '') {
        // Empty is neutral
        return true;
    } else if (isValid && value.length <= 10) {
        input.classList.add('is-valid');
        hideFieldError(input);
        return true;
    } else {
        input.classList.add('is-invalid');
        showFieldError(input, 'Please enter numbers only (max 10 digits)');
        return false;
    }
}

/**
 * Validate filing year
 */
function validateFilingYear(select) {
    const value = parseInt(select.value);
    const currentYear = new Date().getFullYear();
    const isValid = value >= 1950 && value <= currentYear;
    
    select.classList.remove('is-valid', 'is-invalid');
    
    if (select.value === '') {
        return true;
    } else if (isValid) {
        select.classList.add('is-valid');
        hideFieldError(select);
        return true;
    } else {
        select.classList.add('is-invalid');
        showFieldError(select, 'Please select a valid year');
        return false;
    }
}

/**
 * Validate entire search form
 */
function validateSearchForm(form) {
    const caseType = form.querySelector('[name="case_type"]');
    const caseNumber = form.querySelector('[name="case_number"]');
    const filingYear = form.querySelector('[name="filing_year"]');
    
    let isValid = true;
    
    // Validate case type
    if (!caseType.value) {
        showFieldError(caseType, 'Please select a case type');
        caseType.classList.add('is-invalid');
        isValid = false;
    }
    
    // Validate case number
    if (!validateCaseNumber(caseNumber) || !caseNumber.value) {
        isValid = false;
    }
    
    // Validate filing year
    if (!validateFilingYear(filingYear) || !filingYear.value) {
        isValid = false;
    }
    
    return isValid;
}

/**
 * Handle form submission
 */
function handleFormSubmission(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
    submitBtn.disabled = true;
    
    // Add loading class to form
    form.classList.add('form-loading');
    
    // Re-enable button after timeout (in case of errors)
    setTimeout(function() {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
        form.classList.remove('form-loading');
    }, 60000); // 60 seconds timeout
}

/**
 * Show field error message
 */
function showFieldError(field, message) {
    hideFieldError(field); // Remove existing error
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback d-block';
    errorDiv.textContent = message;
    errorDiv.setAttribute('data-error-for', field.name);
    
    field.parentNode.appendChild(errorDiv);
}

/**
 * Hide field error message
 */
function hideFieldError(field) {
    const existingError = field.parentNode.querySelector(`[data-error-for="${field.name}"]`);
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Initialize animations
 */
function initializeAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Initialize utility functions
 */
function initializeUtilities() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 500);
            }
        }, 5000);
    });
    
    // Add loading states to download links
    const downloadLinks = document.querySelectorAll('a[href*="/download/"]');
    downloadLinks.forEach(link => {
        link.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Downloading...';
            this.classList.add('disabled');
            
            setTimeout(() => {
                this.innerHTML = originalText;
                this.classList.remove('disabled');
            }, 3000);
        });
    });
    
    // Add copy functionality to API URLs
    const copyButtons = document.querySelectorAll('[onclick*="copyApiUrl"]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            copyToClipboard(this);
        });
    });
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(element) {
    const apiUrl = window.location.origin + '/api/case/' + getCaseNumberFromUrl();
    
    if (navigator.clipboard) {
        navigator.clipboard.writeText(apiUrl).then(function() {
            showCopySuccess(element);
        }).catch(function() {
            fallbackCopyToClipboard(apiUrl);
            showCopySuccess(element);
        });
    } else {
        fallbackCopyToClipboard(apiUrl);
        showCopySuccess(element);
    }
}

/**
 * Fallback copy to clipboard
 */
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
    } catch (err) {
        console.error('Fallback copy failed:', err);
    }
    
    document.body.removeChild(textArea);
}

/**
 * Show copy success feedback
 */
function showCopySuccess(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
    button.classList.remove('btn-outline-primary');
    button.classList.add('btn-success');
    
    setTimeout(function() {
        button.innerHTML = originalText;
        button.classList.remove('btn-success');
        button.classList.add('btn-outline-primary');
    }, 2000);
}

/**
 * Get case number from current URL
 */
function getCaseNumberFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1] || '';
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * Show loading overlay
 */
function showLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-3">Fetching case information...</p>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.9);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        backdrop-filter: blur(2px);
    `;
    
    document.body.appendChild(overlay);
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getIconForType(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                    data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

/**
 * Get icon for toast type
 */
function getIconForType(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle',
        'primary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Debounce function for performance
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

/**
 * Check if element is in viewport
 */
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Smooth scroll to element
 */
function smoothScrollTo(element, duration = 1000) {
    const targetPosition = element.offsetTop - 100; // Offset for navbar
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;
    
    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }
    
    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }
    
    requestAnimationFrame(animation);
}

// Export functions for global use
window.CourtDataFetcher = {
    validateCaseNumber,
    validateFilingYear,
    showToast,
    showLoadingOverlay,
    hideLoadingOverlay,
    copyToClipboard,
    formatDate,
    smoothScrollTo
};