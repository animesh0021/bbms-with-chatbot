// Blood Bank Management System - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let valid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    valid = false;
                    field.classList.add('is-invalid');
                    
                    // Add error message if not exists
                    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('invalid-feedback')) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'invalid-feedback';
                        errorDiv.textContent = 'This field is required.';
                        field.parentNode.appendChild(errorDiv);
                    }
                } else {
                    field.classList.remove('is-invalid');
                    // Remove error message if exists
                    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
                    if (errorDiv) {
                        errorDiv.remove();
                    }
                }
            });

            // Email validation
            const emailFields = form.querySelectorAll('input[type="email"]');
            emailFields.forEach(field => {
                if (field.value && !isValidEmail(field.value)) {
                    valid = false;
                    field.classList.add('is-invalid');
                    const errorDiv = field.parentNode.querySelector('.invalid-feedback') || document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'Please enter a valid email address.';
                    if (!field.parentNode.querySelector('.invalid-feedback')) {
                        field.parentNode.appendChild(errorDiv);
                    }
                }
            });

            // Phone number validation
            const phoneFields = form.querySelectorAll('input[type="tel"]');
            phoneFields.forEach(field => {
                if (field.value && !isValidPhone(field.value)) {
                    valid = false;
                    field.classList.add('is-invalid');
                    const errorDiv = field.parentNode.querySelector('.invalid-feedback') || document.createElement('div');
                    errorDiv.className = 'invalid-feedback';
                    errorDiv.textContent = 'Please enter a valid phone number.';
                    if (!field.parentNode.querySelector('.invalid-feedback')) {
                        field.parentNode.appendChild(errorDiv);
                    }
                }
            });

            if (!valid) {
                e.preventDefault();
                // Scroll to first error
                const firstError = form.querySelector('.is-invalid');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                // Show error message
                if (!form.querySelector('.form-error-alert')) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'alert alert-danger alert-dismissible fade show form-error-alert mt-3';
                    errorDiv.innerHTML = `
                        Please correct the errors in the form.
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    form.prepend(errorDiv);
                }
            }
        });
    });

    // Auto-format phone numbers
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 3 && value.length <= 6) {
                value = value.replace(/(\d{3})(\d+)/, '$1-$2');
            } else if (value.length > 6) {
                value = value.replace(/(\d{3})(\d{3})(\d+)/, '$1-$2-$3');
            }
            e.target.value = value;
        });
    });

    // Enhanced date validation
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            
            if (selectedDate > today) {
                this.classList.add('is-invalid');
                const errorDiv = this.parentNode.querySelector('.invalid-feedback') || document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'Date cannot be in the future.';
                if (!this.parentNode.querySelector('.invalid-feedback')) {
                    this.parentNode.appendChild(errorDiv);
                }
            } else {
                this.classList.remove('is-invalid');
                const errorDiv = this.parentNode.querySelector('.invalid-feedback');
                if (errorDiv) {
                    errorDiv.remove();
                }
            }
        });
    });

    // Age validation for donors
    const ageInputs = document.querySelectorAll('input[name="age"]');
    ageInputs.forEach(input => {
        input.addEventListener('change', function() {
            const age = parseInt(this.value);
            if (age < 18 || age > 65) {
                this.classList.add('is-invalid');
                const errorDiv = this.parentNode.querySelector('.invalid-feedback') || document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.textContent = 'Age must be between 18 and 65 years.';
                if (!this.parentNode.querySelector('.invalid-feedback')) {
                    this.parentNode.appendChild(errorDiv);
                }
            } else {
                this.classList.remove('is-invalid');
                const errorDiv = this.parentNode.querySelector('.invalid-feedback');
                if (errorDiv) {
                    errorDiv.remove();
                }
            }
        });
    });

    // Low stock warning for blood requests
    const bloodTypeSelects = document.querySelectorAll('select[name="blood_type"]');
    bloodTypeSelects.forEach(select => {
        select.addEventListener('change', function() {
            const selectedType = this.value;
            let lowStockAlert = this.parentNode.querySelector('.low-stock-alert');
            
            if (!lowStockAlert) {
                lowStockAlert = document.createElement('div');
                lowStockAlert.className = 'alert alert-warning mt-2 low-stock-alert';
                this.parentNode.appendChild(lowStockAlert);
            }
            
            if (selectedType) {
                // Simulate API call with timeout
                setTimeout(() => {
                    const randomStock = Math.floor(Math.random() * 10);
                    if (randomStock < 3) {
                        lowStockAlert.style.display = 'block';
                        lowStockAlert.innerHTML = `
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            Low stock alert: Only ${randomStock} units of ${selectedType} available.
                        `;
                    } else {
                        lowStockAlert.style.display = 'none';
                    }
                }, 500);
            } else {
                lowStockAlert.style.display = 'none';
            }
        });
    });

    // Auto-calculate expiry date for new inventory
    const inventoryForms = document.querySelectorAll('form[action*="add_inventory"], form[action*="edit_inventory"]');
    inventoryForms.forEach(form => {
        const expiryDateInput = form.querySelector('input[name="expiry_date"]');
        if (expiryDateInput && !expiryDateInput.value) {
            // Set default expiry date to 42 days from now
            const today = new Date();
            const expiryDate = new Date(today);
            expiryDate.setDate(today.getDate() + 42);
            const formattedDate = expiryDate.toISOString().split('T')[0];
            expiryDateInput.value = formattedDate;
        }
    });
});

// Utility functions
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function isValidPhone(phone) {
    const phoneRegex = /^[\d\s\-\(\)\+]+$/;
    return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function calculateAge(birthDate) {
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    
    return age;
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.error('Table not found:', tableId);
        return;
    }
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Clean innerText, remove commas, and escape quotes
            const data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ')
                                         .replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // Download CSV file
    const csvFile = new Blob([csv.join('\n')], {type: 'text/csv'});
    const downloadLink = document.createElement('a');
    downloadLink.download = filename || 'export.csv';
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Print table
function printTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.error('Table not found:', tableId);
        return;
    }
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Print</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                ${table.outerHTML}
            </body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}
