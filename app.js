/**
 * JMU UREC Live Capacity Tracker - Frontend Application
 * 
 * This script handles:
 * - Fetching capacity data from the backend API
 * - Rendering capacity cards dynamically
 * - Auto-refresh every 30 seconds
 * - Manual refresh functionality
 * - Error handling and loading states
 */

// Configuration
const CONFIG = {
    // API endpoint - Update this to your deployed backend URL
    API_BASE_URL: 'http://localhost:8000/api',
    
    // Refresh interval in milliseconds (30 seconds)
    REFRESH_INTERVAL: 30000,
    
    // Capacity thresholds for status determination
    THRESHOLDS: {
        AVAILABLE: 60,  // 0-60% is "Available"
        MODERATE: 85    // 61-85% is "Moderate", 86-100% is "Busy"
    }
};

// Global state
let refreshInterval = null;
let isLoading = false;

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('UREC Capacity Tracker initialized');
    
    // Initial data fetch
    fetchCapacityData();
    
    // Set up auto-refresh
    startAutoRefresh();
    
    // Set up manual refresh button
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', handleManualRefresh);
    }
});

/**
 * Fetch capacity data from the backend API
 */
async function fetchCapacityData() {
    if (isLoading) {
        console.log('Already loading data, skipping...');
        return;
    }
    
    isLoading = true;
    const errorMessage = document.getElementById('errorMessage');
    
    try {
        console.log('Fetching capacity data...');
        
        // Make API request
        const response = await fetch(`${CONFIG.API_BASE_URL}/capacity`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // Hide error message if visible
        if (errorMessage) {
            errorMessage.style.display = 'none';
        }
        
        // Render the capacity data
        renderCapacityCards(data.areas);
        
        // Update last updated timestamp
        updateLastUpdatedTime(data.timestamp);
        
    } catch (error) {
        console.error('Error fetching capacity data:', error);
        
        // Show error message
        if (errorMessage) {
            errorMessage.style.display = 'block';
        }
        
        // If it's the first load, show mock data for demo purposes
        if (!document.querySelector('.capacity-card')) {
            renderMockData();
        }
    } finally {
        isLoading = false;
    }
}

/**
 * Render capacity cards for all areas
 * @param {Array} areas - Array of area capacity objects
 */
function renderCapacityCards(areas) {
    const grid = document.getElementById('capacityGrid');
    
    if (!grid || !areas || areas.length === 0) {
        console.error('No grid element or no areas data');
        return;
    }
    
    // Clear existing content
    grid.innerHTML = '';
    
    // Create a card for each area
    areas.forEach(area => {
        const card = createCapacityCard(area);
        grid.appendChild(card);
    });
}

/**
 * Create a capacity card element for a single area
 * @param {Object} area - Area capacity data
 * @returns {HTMLElement} Card element
 */
function createCapacityCard(area) {
    const card = document.createElement('div');
    
    // Determine status based on capacity percentage
    const status = determineStatus(area);
    
    // Calculate percentage
    const percentage = area.max_capacity > 0 
        ? Math.round((area.current_count / area.max_capacity) * 100)
        : 0;
    
    // Add classes
    card.className = `capacity-card ${status}`;
    
    // Build card HTML
    card.innerHTML = `
        <h3>${area.name}</h3>
        
        <div class="capacity-info">
            <div class="capacity-count">
                ${area.current_count} / ${area.max_capacity}
            </div>
            <div class="capacity-status ${status}">
                ${getStatusLabel(status)}
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill ${status}" style="width: ${percentage}%"></div>
        </div>
        
        <div class="capacity-details">
            ${percentage}% capacity
            ${area.is_open ? '' : '• Currently Closed'}
        </div>
    `;
    
    return card;
}

/**
 * Determine status based on capacity percentage and open status
 * @param {Object} area - Area capacity data
 * @returns {string} Status: 'available', 'moderate', 'busy', or 'closed'
 */
function determineStatus(area) {
    // If closed, return closed status
    if (!area.is_open) {
        return 'closed';
    }
    
    // Calculate percentage
    const percentage = area.max_capacity > 0 
        ? (area.current_count / area.max_capacity) * 100
        : 0;
    
    // Determine status based on thresholds
    if (percentage <= CONFIG.THRESHOLDS.AVAILABLE) {
        return 'available';
    } else if (percentage <= CONFIG.THRESHOLDS.MODERATE) {
        return 'moderate';
    } else {
        return 'busy';
    }
}

/**
 * Get human-readable status label
 * @param {string} status - Status code
 * @returns {string} Human-readable label
 */
function getStatusLabel(status) {
    const labels = {
        'available': 'Available',
        'moderate': 'Moderate',
        'busy': 'Busy',
        'closed': 'Closed'
    };
    
    return labels[status] || 'Unknown';
}

/**
 * Update the last updated timestamp display
 * @param {string} timestamp - ISO timestamp string
 */
function updateLastUpdatedTime(timestamp) {
    const lastUpdateElement = document.getElementById('lastUpdate');
    
    if (!lastUpdateElement) return;
    
    try {
        const date = new Date(timestamp);
        const timeString = date.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
        
        lastUpdateElement.textContent = timeString;
    } catch (error) {
        console.error('Error parsing timestamp:', error);
        lastUpdateElement.textContent = 'Unknown';
    }
}

/**
 * Start auto-refresh interval
 */
function startAutoRefresh() {
    // Clear any existing interval
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Set up new interval
    refreshInterval = setInterval(() => {
        console.log('Auto-refreshing capacity data...');
        fetchCapacityData();
    }, CONFIG.REFRESH_INTERVAL);
    
    console.log(`Auto-refresh started (every ${CONFIG.REFRESH_INTERVAL / 1000} seconds)`);
}

/**
 * Handle manual refresh button click
 */
function handleManualRefresh() {
    console.log('Manual refresh triggered');
    
    // Provide visual feedback
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.textContent = '↻ Refreshing...';
    }
    
    // Fetch data
    fetchCapacityData().finally(() => {
        // Re-enable button after a short delay
        setTimeout(() => {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.textContent = '↻ Refresh';
            }
        }, 1000);
    });
}

/**
 * Render mock data for demonstration purposes
 * This is used when the backend is not available
 */
function renderMockData() {
    console.log('Rendering mock data for demonstration');
    
    const mockAreas = [
        {
            area_id: 'weight-room',
            name: 'Weight Room',
            current_count: 45,
            max_capacity: 100,
            is_open: true
        },
        {
            area_id: 'cardio',
            name: 'Cardio Area',
            current_count: 32,
            max_capacity: 60,
            is_open: true
        },
        {
            area_id: 'track',
            name: 'Indoor Track',
            current_count: 18,
            max_capacity: 50,
            is_open: true
        },
        {
            area_id: 'pool',
            name: 'Swimming Pool',
            current_count: 12,
            max_capacity: 40,
            is_open: true
        },
        {
            area_id: 'basketball',
            name: 'Basketball Courts',
            current_count: 24,
            max_capacity: 30,
            is_open: true
        },
        {
            area_id: 'climbing',
            name: 'Climbing Wall',
            current_count: 8,
            max_capacity: 15,
            is_open: true
        }
    ];
    
    renderCapacityCards(mockAreas);
    updateLastUpdatedTime(new Date().toISOString());
}

/**
 * Handle visibility change (pause auto-refresh when tab is hidden)
 */
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Tab hidden, pausing auto-refresh');
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    } else {
        console.log('Tab visible, resuming auto-refresh');
        fetchCapacityData();
        startAutoRefresh();
    }
});
