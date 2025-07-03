// dashboard.js - Handles dashboard functionality for both HR and candidate views

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard based on user type
    initializeDashboard();
    
    // Set up event listeners
    setupEventListeners();
});

// Initialize dashboard based on user type
function initializeDashboard() {
    const dashboardType = document.body.getAttribute('data-dashboard');
    
    if (dashboardType === 'hr') {
        initializeHRDashboard();
    } else if (dashboardType === 'candidate') {
        initializeCandidateDashboard();
    }
    
    // Initialize shared components
    initializeStatistics();
    initializeNotifications();
}

// Initialize HR dashboard specific elements
function initializeHRDashboard() {
    // Initialize interview tables with sorting and filtering
    const interviewTable = document.getElementById('interviewTable');
    if (interviewTable) {
        initializeDataTable(interviewTable);
    }
    
    // Load HR statistics
    loadHRStatistics();
    
    // Check for completed interviews that need review
    checkCompletedInterviews();
}

// Initialize candidate dashboard specific elements
function initializeCandidateDashboard() {
    // Initialize upcoming interviews
    const upcomingInterviews = document.getElementById('upcomingInterviews');
    if (upcomingInterviews) {
        loadUpcomingInterviews();
    }
    
    // Initialize interview history
    const interviewHistory = document.getElementById('interviewHistory');
    if (interviewHistory) {
        loadInterviewHistory();
    }
}

// Initialize dashboard statistics
function initializeStatistics() {
    const statsContainers = document.querySelectorAll('.stats-container');
    
    statsContainers.forEach(container => {
        // Animate counters
        const counters = container.querySelectorAll('.stat-counter');
        counters.forEach(counter => {
            const target = parseInt(counter.getAttribute('data-target'));
            const duration = 1500; // ms
            const step = Math.max(1, Math.floor(target / (duration / 16)));
            
            let current = 0;
            const timer = setInterval(() => {
                current += step;
                if (current >= target) {
                    counter.textContent = target;
                    clearInterval(timer);
                } else {
                    counter.textContent = current;
                }
            }, 16);
        });
    });
}

// Initialize notification system
function initializeNotifications() {
    const notificationBell = document.getElementById('notificationBell');
    const notificationPanel = document.getElementById('notificationPanel');
    
    if (notificationBell && notificationPanel) {
        notificationBell.addEventListener('click', (e) => {
            e.preventDefault();
            notificationPanel.classList.toggle('hidden');
            
            // Mark notifications as read
            if (!notificationPanel.classList.contains('hidden')) {
                markNotificationsAsRead();
            }
        });
        
        // Close panel when clicking outside
        document.addEventListener('click', (e) => {
            if (!notificationBell.contains(e.target) && !notificationPanel.contains(e.target)) {
                notificationPanel.classList.add('hidden');
            }
        });
        
        // Load notifications
        loadNotifications();
    }
}

// Initialize data table with sorting and filtering
function initializeDataTable(table) {
    // Add sorting functionality
    const headers = table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');
            const currentDirection = header.getAttribute('data-direction') || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            
            // Reset all headers
            headers.forEach(h => h.setAttribute('data-direction', ''));
            
            // Set current header
            header.setAttribute('data-direction', newDirection);
            
            // Sort the table
            sortTable(table, column, newDirection);
        });
    });
    
    // Add filtering functionality
    const filterInput = document.getElementById('tableFilter');
    if (filterInput) {
        filterInput.addEventListener('input', () => {
            filterTable(table, filterInput.value.toLowerCase());
        });
    }
}

// Sort table based on column and direction
function sortTable(table, column, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.querySelector(`td[data-column="${column}"]`).textContent.trim();
        const bValue = b.querySelector(`td[data-column="${column}"]`).textContent.trim();
        
        // Check if values are dates
        if (!isNaN(Date.parse(aValue)) && !isNaN(Date.parse(bValue))) {
            return direction === 'asc' 
                ? new Date(aValue) - new Date(bValue)
                : new Date(bValue) - new Date(aValue);
        }
        
        // Check if values are numbers
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return direction === 'asc'
                ? parseFloat(aValue) - parseFloat(bValue)
                : parseFloat(bValue) - parseFloat(aValue);
        }
        
        // Default string comparison
        return direction === 'asc'
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Clear and repopulate table
    while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
    }
    
    rows.forEach(row => tbody.appendChild(row));
}

// Filter table based on search input
function filterTable(table, searchText) {
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchText) ? '' : 'none';
    });
}

// Load HR statistics
function loadHRStatistics() {
    // This would be replaced with actual API calls
    // For demo purposes, we're just updating with static data
    updateStatistic('totalInterviews', 0, 28);
    updateStatistic('completedInterviews', 0, 17);
    updateStatistic('averageScore', 0, 76);
}

// Update statistic counter with animation
function updateStatistic(id, start, end) {
    const element = document.getElementById(id);
    if (!element) return;
    
    const duration = 1500; // ms
    const step = Math.max(1, Math.floor((end - start) / (duration / 16)));
    let current = start;
    
    const timer = setInterval(() => {
        current += step;
        if (current >= end) {
            element.textContent = end;
            clearInterval(timer);
        } else {
            element.textContent = current;
        }
    }, 16);
}

// Check for completed interviews
function checkCompletedInterviews() {
    // This would be replaced with actual API calls
    // For demo purposes, we're just simulating
    console.log("Checking for completed interviews...");
}

// Load upcoming interviews for candidate
function loadUpcomingInterviews() {
    // This would be replaced with actual API calls
    console.log("Loading upcoming interviews...");
}

// Load interview history for candidate
function loadInterviewHistory() {
    // This would be replaced with actual API calls
    console.log("Loading interview history...");
}

// Load notifications
function loadNotifications() {
    // This would be replaced with actual API calls
    console.log("Loading notifications...");
    
    // Update notification badge
    updateNotificationBadge(3);
}

// Update notification badge count
function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove('hidden');
        } else {
            badge.classList.add('hidden');
        }
    }
}

// Mark notifications as read
function markNotificationsAsRead() {
    // This would be replaced with actual API calls
    console.log("Marking notifications as read...");
    
    // Update badge
    updateNotificationBadge(0);
}

// Set up event listeners for dashboard interactions
function setupEventListeners() {
    // Interview creation form
    const createInterviewForm = document.getElementById('createInterviewForm');
    if (createInterviewForm) {
        createInterviewForm.addEventListener('submit', handleInterviewFormSubmit);
    }
    
    // Custom questions section
    const addQuestionBtn = document.getElementById('addQuestionBtn');
    if (addQuestionBtn) {
        addQuestionBtn.addEventListener('click', addCustomQuestion);
    }
    
    // Date picker initialization
    const datePickers = document.querySelectorAll('.datepicker');
    datePickers.forEach(picker => {
        // This would be replaced with actual date picker initialization
        console.log("Initializing date picker...");
    });
}

// Handle interview form submission
function handleInterviewFormSubmit(e) {
    e.preventDefault();
    
    // Show loading state
    const submitButton = e.target.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
    
    // Get form data
    const formData = new FormData(e.target);
    
    // Add custom questions as JSON
    const customQuestions = getCustomQuestions();
    formData.append('custom_questions', JSON.stringify(customQuestions));
    
    // Submit form
    fetch(e.target.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.interview_id) {
            // Show success message
            showAlert('Interview created successfully!', 'success');
            
            // Redirect to dashboard
            setTimeout(() => {
                window.location.href = '/hr/dashboard';
            }, 1500);
        } else {
            showAlert('Error creating interview: ' + (data.message || 'Unknown error'), 'error');
            
            // Reset button
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error creating interview. Please try again.', 'error');
        
        // Reset button
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    });
}

// Get custom questions from the form
function getCustomQuestions() {
    const questions = [];
    const questionInputs = document.querySelectorAll('.custom-question-input');
    
    questionInputs.forEach(input => {
        const question = input.value.trim();
        if (question) {
            questions.push(question);
        }
    });
    
    return questions;
}

// Add custom question input field
function addCustomQuestion() {
    const container = document.getElementById('customQuestionsContainer');
    const index = container.querySelectorAll('.custom-question').length + 1;
    
    const questionDiv = document.createElement('div');
    questionDiv.className = 'custom-question mb-2 flex';
    questionDiv.innerHTML = `
        <input type="text" name="custom_question_${index}" 
               class="custom-question-input flex-grow px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-blue-500 focus:border-blue-500" 
               placeholder="Enter custom question">
        <button type="button" class="remove-question-btn px-3 py-2 bg-red-500 text-white rounded-r-md hover:bg-red-600">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(questionDiv);
    
    // Add event listener to remove button
    const removeBtn = questionDiv.querySelector('.remove-question-btn');
    removeBtn.addEventListener('click', () => {
        container.removeChild(questionDiv);
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alertContainer');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} mb-4 px-4 py-3 rounded relative`;
    
    let icon = '';
    switch (type) {
        case 'success':
            icon = '<i class="fas fa-check-circle mr-2"></i>';
            break;
        case 'error':
            icon = '<i class="fas fa-exclamation-circle mr-2"></i>';
            break;
        case 'info':
            icon = '<i class="fas fa-info-circle mr-2"></i>';
            break;
    }
    
    alert.innerHTML = `
        ${icon}${message}
        <button class="alert-close absolute top-0 right-0 mt-3 mr-4">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Add event listener to close button
    const closeBtn = alert.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
        alertContainer.removeChild(alert);
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertContainer.contains(alert)) {
            alertContainer.removeChild(alert);
        }
    }, 5000);
}