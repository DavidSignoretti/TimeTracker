/**
 * Time Tracker & Invoicing Application
 * Global JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips if any
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers if any
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Handle hourly rates in client forms
    initHourlyRatesManager();

    // Auto-close alert messages after 5 seconds
    const alertList = document.querySelectorAll('.alert:not(.alert-permanent)');
    alertList.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value.replace(/[^\d.-]/g, ''));
            if (!isNaN(value)) {
                this.value = '$' + value.toFixed(2);
            }
        });

        input.addEventListener('focus', function() {
            this.value = this.value.replace(/[^\d.-]/g, '');
        });
    });

    // Format percentage inputs
    const percentInputs = document.querySelectorAll('.percent-input');
    percentInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value.replace(/[^\d.-]/g, ''));
            if (!isNaN(value)) {
                this.value = value.toFixed(2) + '%';
            }
        });

        input.addEventListener('focus', function() {
            this.value = this.value.replace(/[^\d.-]/g, '');
        });
    });

    // Confirm delete actions
    const confirmDeleteForms = document.querySelectorAll('.confirm-delete-form');
    confirmDeleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Add "active" class to current navigation item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(function(link) {
        const href = link.getAttribute('href');

        // Match the exact path or the start of the path
        if (href === currentPath || 
            (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
        }
    });

    // Print invoice button functionality
    const printInvoiceBtn = document.getElementById('printInvoiceBtn');
    if (printInvoiceBtn) {
        printInvoiceBtn.addEventListener('click', function() {
            window.print();
        });
    }

    // Time duration calculator
    function updateTimeDuration() {
        const timeInElement = document.getElementById('time_in');
        const timeOutElement = document.getElementById('time_out');
        const totalHoursElement = document.getElementById('total_hours');

        if (timeInElement && timeOutElement && totalHoursElement) {
            const timeIn = timeInElement.value;
            const timeOut = timeOutElement.value;

            if (timeIn && timeOut) {
                // Parse the time values
                const [inHours, inMinutes] = timeIn.split(':').map(Number);
                const [outHours, outMinutes] = timeOut.split(':').map(Number);

                // Calculate duration in minutes
                let durationMinutes = (outHours * 60 + outMinutes) - (inHours * 60 + inMinutes);

                // Handle overnight shifts
                if (durationMinutes < 0) {
                    durationMinutes += 24 * 60;
                }

                // Convert to hours with 2 decimal places
                const durationHours = (durationMinutes / 60).toFixed(2);
                totalHoursElement.value = durationHours;

                // Update total amount if rate is available
                const hourlyRateElement = document.getElementById('hourly_rate');
                const totalAmountElement = document.getElementById('total_amount');

                if (hourlyRateElement && totalAmountElement) {
                    const hourlyRate = parseFloat(hourlyRateElement.value);
                    if (!isNaN(hourlyRate)) {
                        const totalAmount = (hourlyRate * durationHours).toFixed(2);
                        totalAmountElement.value = '$' + totalAmount;
                    }
                }
            }
        }
    }

    // Add event listeners for time calculation
    const timeInputs = document.querySelectorAll('#time_in, #time_out');
    timeInputs.forEach(function(input) {
        input.addEventListener('change', updateTimeDuration);
    });

    // Run the time calculation once on page load in case fields are pre-filled
    updateTimeDuration();
});

// Custom filter functionality for tables
function filterTable(tableId, inputId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) { // Start at 1 to skip header row
        let visible = false;
        const cells = rows[i].getElementsByTagName('td');

        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell) {
                const text = cell.textContent || cell.innerText;
                if (text.toUpperCase().indexOf(filter) > -1) {
                    visible = true;
                    break;
                }
            }
        }

        rows[i].style.display = visible ? '' : 'none';
    }
}

// Hourly rates manager for client forms
function initHourlyRatesManager() {
    const addRateBtn = document.getElementById('add-rate-btn');
    const ratesContainer = document.getElementById('hourly-rates-container');

    if (!addRateBtn || !ratesContainer) {
        return; // Not on a client form page
    }

    // Add a new rate row
    addRateBtn.addEventListener('click', function() {
        // Remove the "no rates" message if it exists
        const noRatesMsg = ratesContainer.querySelector('.alert-info');
        if (noRatesMsg) {
            noRatesMsg.remove();
        }

        // Get the template and clone it
        const template = document.getElementById('rate-row-template');
        const clone = document.importNode(template.content, true);

        // Set the default rate radio value to the current row count
        const rowCount = ratesContainer.querySelectorAll('.hourly-rate-row').length;
        const radioBtn = clone.querySelector('.default-rate-checkbox');
        radioBtn.value = rowCount;

        // Add event listener for the remove button
        const removeBtn = clone.querySelector('.remove-rate');
        removeBtn.addEventListener('click', function() {
            this.closest('.hourly-rate-row').remove();
            updateDefaultRateRadios();

            // If no rates left, show the "no rates" message
            if (ratesContainer.querySelectorAll('.hourly-rate-row').length === 0) {
                const noRatesMsg = document.createElement('div');
                noRatesMsg.className = 'alert alert-info';
                noRatesMsg.textContent = 'No hourly rates defined yet. Add your first rate below.';
                ratesContainer.appendChild(noRatesMsg);
            }
        });

        // Append the new row
        ratesContainer.appendChild(clone);
    });

    // Add event listeners to existing remove buttons
    const removeButtons = ratesContainer.querySelectorAll('.remove-rate');
    removeButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            this.closest('.hourly-rate-row').remove();
            updateDefaultRateRadios();

            // If no rates left, show the "no rates" message
            if (ratesContainer.querySelectorAll('.hourly-rate-row').length === 0) {
                const noRatesMsg = document.createElement('div');
                noRatesMsg.className = 'alert alert-info';
                noRatesMsg.textContent = 'No hourly rates defined yet. Add your first rate below.';
                ratesContainer.appendChild(noRatesMsg);
            }
        });
    });

    // Function to update the default rate radio values
    function updateDefaultRateRadios() {
        const rows = ratesContainer.querySelectorAll('.hourly-rate-row');
        rows.forEach(function(row, index) {
            const radio = row.querySelector('.default-rate-checkbox');
            radio.value = index;
        });
    }
}

// Date helper functions for reports
function getFirstDayOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth(), 1);
}

function getLastDayOfMonth(date) {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

function getFirstDayOfYear(date) {
    return new Date(date.getFullYear(), 0, 1);
}

function getLastDayOfYear(date) {
    return new Date(date.getFullYear(), 11, 31);
}

function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}
