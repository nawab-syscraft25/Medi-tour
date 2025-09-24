// Medi-Tour Admin Panel JavaScript

// Global variables
let currentPage = 1;
let searchTimeout = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAdmin();
});

// Initialize admin panel functionality
function initializeAdmin() {
    // Add fade-in animation to main content
    document.querySelector('main').classList.add('fade-in');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize table interactions
    initializeTableInteractions();
    
    // Initialize notifications
    initializeNotifications();
    
    console.log('Medi-Tour Admin Panel initialized');
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize search functionality
function initializeSearch() {
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="Search"]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(e.target.value, e.target);
            }, 300);
        });
    });
}

// Perform search on table rows
function performSearch(searchTerm, inputElement) {
    const table = inputElement.closest('.card').querySelector('table tbody');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const term = searchTerm.toLowerCase();
    let visibleCount = 0;
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(term)) {
            row.style.display = '';
            row.classList.add('slide-in');
            visibleCount++;
        } else {
            row.style.display = 'none';
            row.classList.remove('slide-in');
        }
    });
    
    // Update empty state
    updateEmptyState(table, visibleCount, searchTerm);
}

// Update empty state message
function updateEmptyState(table, visibleCount, searchTerm) {
    let emptyRow = table.querySelector('.empty-search-row');
    
    if (visibleCount === 0 && searchTerm.length > 0) {
        if (!emptyRow) {
            emptyRow = document.createElement('tr');
            emptyRow.className = 'empty-search-row';
            const colCount = table.closest('table').querySelector('thead tr').children.length;
            emptyRow.innerHTML = `
                <td colspan="${colCount}" class="text-center py-4 text-muted">
                    <i class="fas fa-search fa-2x mb-2"></i>
                    <p>No results found for "${searchTerm}"</p>
                    <small>Try adjusting your search terms</small>
                </td>
            `;
            table.appendChild(emptyRow);
        }
    } else if (emptyRow) {
        emptyRow.remove();
    }
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate="true"], form.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
            
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.checkValidity()) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            });
        });
    });
}

// Initialize table interactions
function initializeTableInteractions() {
    // Row hover effects
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'transform 0.2s ease';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Sortable columns
    const sortableHeaders = document.querySelectorAll('th[data-sortable="true"]');
    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', function() {
            sortTable(this);
        });
    });
}

// Sort table by column
function sortTable(header) {
    const table = header.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const columnIndex = Array.from(header.parentNode.children).indexOf(header);
    const isAscending = !header.classList.contains('sort-asc');
    
    // Clear previous sort indicators
    header.parentNode.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // Add current sort indicator
    header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        // Check if values are numbers
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }
        
        // String comparison
        return isAscending ? 
            aValue.localeCompare(bValue) : 
            bValue.localeCompare(aValue);
    });
    
    // Reorder rows in table
    rows.forEach(row => tbody.appendChild(row));
}

// Initialize notifications
function initializeNotifications() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.add('fade');
                setTimeout(() => {
                    alert.remove();
                }, 150);
            }
        }, 5000);
    });
}

// Show notification
function showNotification(message, type = 'info', duration = 3000) {
    const alertTypes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const icons = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-exclamation-circle',
        'info': 'fas fa-info-circle'
    };
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertTypes[type]} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alert.innerHTML = `
        <i class="${icons[type]} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, duration);
}

// Loading state management
function showLoading(element, message = 'Loading...') {
    const originalContent = element.innerHTML;
    element.dataset.originalContent = originalContent;
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        ${message}
    `;
    element.disabled = true;
}

function hideLoading(element) {
    if (element.dataset.originalContent) {
        element.innerHTML = element.dataset.originalContent;
        delete element.dataset.originalContent;
    }
    element.disabled = false;
}

// Confirm delete dialog
function confirmDelete(type, id, name, callback) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i class="fas fa-exclamation-triangle text-danger me-2"></i>
                        Confirm Delete
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete this ${type}?</p>
                    <div class="alert alert-warning">
                        <strong>${name}</strong>
                    </div>
                    <p class="text-danger mb-0">
                        <i class="fas fa-warning me-1"></i>
                        This action cannot be undone.
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                        Cancel
                    </button>
                    <button type="button" class="btn btn-danger" id="confirmDeleteBtn">
                        <i class="fas fa-trash me-1"></i>
                        Delete ${type}
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Handle confirm button
    modal.querySelector('#confirmDeleteBtn').addEventListener('click', function() {
        if (callback) {
            callback(id);
        }
        bsModal.hide();
    });
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// Image preview functionality
function previewImage(input, previewId) {
    const file = input.files[0];
    const preview = document.getElementById(previewId);
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(file);
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Debounce function
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

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard!', 'success', 1500);
    }).catch(function() {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Copied to clipboard!', 'success', 1500);
    });
}

// Export functionality
function exportTable(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = Array.from(rows).map(row => {
        const cells = row.querySelectorAll('th, td');
        return Array.from(cells).map(cell => 
            `"${cell.textContent.trim().replace(/"/g, '""')}"`
        ).join(',');
    }).join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
    
    showNotification('Table exported successfully!', 'success');
}

// Dark mode toggle (if needed)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDark);
}

// Initialize dark mode from localStorage
function initializeDarkMode() {
    const isDark = localStorage.getItem('darkMode') === 'true';
    if (isDark) {
        document.body.classList.add('dark-mode');
    }
}

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showNotification('An error occurred. Please try again.', 'error');
});

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showNotification('An error occurred. Please try again.', 'error');
});

// Expose global functions
window.MediTourAdmin = {
    showNotification,
    showLoading,
    hideLoading,
    confirmDelete,
    previewImage,
    formatFileSize,
    copyToClipboard,
    exportTable,
    toggleDarkMode
};