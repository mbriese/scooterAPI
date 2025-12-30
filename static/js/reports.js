/**
 * Reports Module - Admin reports and analytics
 */

/**
 * Load all reports data
 */
async function loadReportsData() {
    const days = document.getElementById('reportPeriod')?.value || 30;
    
    // Load all reports in parallel
    await Promise.all([
        loadRevenueReport(),
        loadTransactions(days),
        loadRentalHistory(days)
    ]);
}

/**
 * Load revenue summary report
 */
async function loadRevenueReport() {
    const result = await apiGet('/admin/reports/revenue');
    
    if (result.ok) {
        const data = result.data;
        
        // Update revenue cards
        document.getElementById('revenueToday').textContent = `$${data.today.total_revenue.toFixed(2)}`;
        document.getElementById('rentalsToday').textContent = data.today.total_rentals;
        
        document.getElementById('revenueWeek').textContent = `$${data.this_week.total_revenue.toFixed(2)}`;
        document.getElementById('rentalsWeek').textContent = data.this_week.total_rentals;
        
        document.getElementById('revenueMonth').textContent = `$${data.this_month.total_revenue.toFixed(2)}`;
        document.getElementById('rentalsMonth').textContent = data.this_month.total_rentals;
        
        document.getElementById('revenueAllTime').textContent = `$${data.all_time.total_revenue.toFixed(2)}`;
        document.getElementById('rentalsAllTime').textContent = data.all_time.total_rentals;
        
        // Update top scooters
        updateTopScootersTable(data.top_scooters || []);
    } else {
        showStatus('Failed to load revenue report', 'error');
    }
}

/**
 * Load transactions log
 */
async function loadTransactions(days) {
    const result = await apiGet(`/admin/reports/transactions?days=${days}&limit=100`);
    
    if (result.ok) {
        updateTransactionsTable(result.data.transactions || []);
    } else {
        document.getElementById('transactionsTableBody').innerHTML = 
            '<tr><td colspan="7" class="error-text">Failed to load transactions</td></tr>';
    }
}

/**
 * Load rental history
 */
async function loadRentalHistory(days) {
    const result = await apiGet(`/admin/reports/rentals?days=${days}`);
    
    if (result.ok) {
        updateRentalsTable(result.data || []);
    } else {
        document.getElementById('rentalsTableBody').innerHTML = 
            '<tr><td colspan="8" class="error-text">Failed to load rental history</td></tr>';
    }
}

/**
 * Update transactions table
 */
function updateTransactionsTable(transactions) {
    const tbody = document.getElementById('transactionsTableBody');
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-text">No transactions found</td></tr>';
        return;
    }
    
    tbody.innerHTML = transactions.map(txn => `
        <tr>
            <td class="date-cell">${formatDateTime(txn.end_time)}</td>
            <td class="txn-id">${txn.transaction_id || 'N/A'}</td>
            <td>${txn.user_name}</td>
            <td>${txn.scooter_id}</td>
            <td>${formatDurationShort(txn.duration_minutes)}</td>
            <td class="amount-cell">$${txn.amount.toFixed(2)}</td>
            <td>
                <span class="status-badge ${txn.status === 'APPROVED' ? 'approved' : 'pending'}">
                    ${txn.status}
                </span>
                ${txn.is_simulation ? '<span class="sim-badge">SIM</span>' : ''}
            </td>
        </tr>
    `).join('');
}

/**
 * Update rentals table
 */
function updateRentalsTable(rentals) {
    const tbody = document.getElementById('rentalsTableBody');
    
    if (rentals.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-text">No rentals found</td></tr>';
        return;
    }
    
    tbody.innerHTML = rentals.map(rental => {
        const cost = rental.cost || {};
        const distanceKm = ((rental.distance_traveled_m || 0) / 1000).toFixed(2);
        const status = rental.status || 'unknown';
        
        return `
            <tr class="${status === 'active' ? 'active-rental' : ''}">
                <td class="date-cell">${formatDateTime(rental.start_time)}</td>
                <td class="date-cell">${rental.end_time ? formatDateTime(rental.end_time) : '<em>In progress</em>'}</td>
                <td>${rental.user_name || rental.user_email || 'Unknown'}</td>
                <td>${rental.scooter_id}</td>
                <td>${formatDurationShort(cost.duration_minutes || 0)}</td>
                <td>${distanceKm} km</td>
                <td class="amount-cell">$${(cost.total_cost || 0).toFixed(2)}</td>
                <td>
                    <span class="status-badge ${status}">${status}</span>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Update top scooters table
 */
function updateTopScootersTable(scooters) {
    const tbody = document.getElementById('topScootersTableBody');
    
    if (scooters.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-text">No data yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = scooters.map((scooter, index) => `
        <tr>
            <td class="rank-cell">
                ${index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
            </td>
            <td>${scooter.scooter_id}</td>
            <td>${scooter.rentals}</td>
            <td class="amount-cell">$${scooter.revenue.toFixed(2)}</td>
        </tr>
    `).join('');
}

/**
 * Format date/time for display
 */
function formatDateTime(isoString) {
    if (!isoString) return '--';
    try {
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return isoString;
    }
}

/**
 * Format duration in short format
 */
function formatDurationShort(minutes) {
    if (!minutes || minutes < 1) return '< 1m';
    if (minutes < 60) return `${Math.round(minutes)}m`;
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    if (hours < 24) return `${hours}h ${mins}m`;
    const days = Math.floor(hours / 24);
    return `${days}d ${hours % 24}h`;
}

/**
 * Initialize reports event listeners
 */
function initReportsEvents() {
    // Report tabs
    document.querySelectorAll('.report-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.report-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.report-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(tab.dataset.report + 'Report')?.classList.add('active');
        });
    });
    
    // Refresh button
    document.getElementById('refreshReportsBtn')?.addEventListener('click', loadReportsData);
    
    // Period selector
    document.getElementById('reportPeriod')?.addEventListener('change', loadReportsData);
}


