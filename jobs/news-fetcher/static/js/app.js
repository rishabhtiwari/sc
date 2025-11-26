// Global state
let currentPage = 1;
let currentTab = 'overview';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadCategories();
    loadLanguages();
    loadCountries();
});

// Tab switching
function switchTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.nav-tab').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tab}-tab`).classList.add('active');
    
    // Load data for the tab
    if (tab === 'news') {
        loadNews();
    } else if (tab === 'seeds') {
        loadSeeds();
    } else if (tab === 'overview') {
        loadStats();
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/enrichment/status');
        const data = await response.json();
        
        if (data.status === 'success') {
            const statsHtml = `
                <div class="stat-card">
                    <h3>Total Articles</h3>
                    <div class="value">${data.total_articles || 0}</div>
                </div>
                <div class="stat-card">
                    <h3>Enriched</h3>
                    <div class="value">${data.enriched_articles || 0}</div>
                </div>
                <div class="stat-card">
                    <h3>Pending Enrichment</h3>
                    <div class="value">${data.pending_enrichment || 0}</div>
                </div>
                <div class="stat-card">
                    <h3>Failed</h3>
                    <div class="value">${data.failed_articles || 0}</div>
                </div>
            `;
            document.getElementById('stats-container').innerHTML = statsHtml;
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
        document.getElementById('stats-container').innerHTML = '<div class="empty-state">Failed to load statistics</div>';
    }
}

// Load news records
async function loadNews(page = 1) {
    currentPage = page;
    const container = document.getElementById('news-container');
    container.innerHTML = '<div class="loading">Loading news records...</div>';
    
    try {
        const category = document.getElementById('filter-category').value;
        const language = document.getElementById('filter-language').value;
        const country = document.getElementById('filter-country').value;
        const pageSize = document.getElementById('page-size').value;
        
        const params = new URLSearchParams({
            page: page,
            page_size: pageSize
        });
        
        if (category) params.append('category', category);
        if (language) params.append('language', language);
        if (country) params.append('country', country);
        
        const response = await fetch(`/news?${params}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.articles && data.articles.length > 0) {
            let tableHtml = `
                <table>
                    <thead>
                        <tr>
                            <th>Title</th>
                            <th>Category</th>
                            <th>Source</th>
                            <th>Published</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.articles.forEach(article => {
                const statusBadge = getStatusBadge(article.status);
                const publishedDate = new Date(article.publishedAt).toLocaleDateString();
                
                tableHtml += `
                    <tr>
                        <td><strong>${article.title || 'N/A'}</strong></td>
                        <td><span class="badge badge-info">${article.category || 'general'}</span></td>
                        <td>${article.source?.name || 'Unknown'}</td>
                        <td>${publishedDate}</td>
                        <td>${statusBadge}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="viewArticle('${article.id}')">View</button>
                        </td>
                    </tr>
                `;
            });
            
            tableHtml += '</tbody></table>';
            container.innerHTML = tableHtml;
            
            // Update pagination
            updatePagination(data.pagination);
        } else {
            container.innerHTML = '<div class="empty-state"><div class="icon">📭</div><p>No news records found</p></div>';
        }
    } catch (error) {
        console.error('Failed to load news:', error);
        container.innerHTML = '<div class="empty-state">Failed to load news records</div>';
    }
}

// Load seed URLs
async function loadSeeds() {
    const container = document.getElementById('seeds-container');
    container.innerHTML = '<div class="loading">Loading seed URLs...</div>';
    
    try {
        const response = await fetch('/seed-urls/status');
        const data = await response.json();
        
        if (data.status === 'success' && data.seed_urls && data.seed_urls.length > 0) {
            let tableHtml = `
                <table>
                    <thead>
                        <tr>
                            <th>Partner Name</th>
                            <th>Partner ID</th>
                            <th>Categories</th>
                            <th>Status</th>
                            <th>Frequency</th>
                            <th>Last Run</th>
                            <th>Due</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.seed_urls.forEach(seed => {
                const statusBadge = seed.is_active
                    ? '<span class="badge badge-success">Active</span>'
                    : '<span class="badge badge-danger">Inactive</span>';
                const dueBadge = seed.is_due
                    ? '<span class="badge badge-warning">Due</span>'
                    : '<span class="badge badge-success">Not Due</span>';
                const lastRun = seed.last_run
                    ? new Date(seed.last_run).toLocaleString()
                    : 'Never';

                // Display categories - handle both string and array
                let categoriesDisplay = '';
                if (Array.isArray(seed.category)) {
                    categoriesDisplay = seed.category.map(cat =>
                        `<span class="badge" style="background: #4CAF50; margin: 2px;">${cat}</span>`
                    ).join(' ');
                } else {
                    categoriesDisplay = `<span class="badge" style="background: #4CAF50;">${seed.category || 'general'}</span>`;
                }

                tableHtml += `
                    <tr>
                        <td><strong>${seed.partner_name}</strong></td>
                        <td>${seed.partner_id}</td>
                        <td>${categoriesDisplay}</td>
                        <td>${statusBadge}</td>
                        <td>${seed.frequency_minutes} min</td>
                        <td>${lastRun}</td>
                        <td>${dueBadge}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick='editSeed(${JSON.stringify(seed)})'>Edit</button>
                            <button class="btn btn-sm ${seed.is_active ? 'btn-warning' : 'btn-success'}"
                                    onclick="toggleSeedStatus('${seed.partner_id}', ${!seed.is_active})">
                                ${seed.is_active ? 'Disable' : 'Enable'}
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteSeed('${seed.partner_id}')">Delete</button>
                        </td>
                    </tr>
                `;
            });
            
            tableHtml += '</tbody></table>';
            container.innerHTML = tableHtml;
        } else {
            container.innerHTML = '<div class="empty-state"><div class="icon">🌱</div><p>No seed URLs configured</p></div>';
        }
    } catch (error) {
        console.error('Failed to load seeds:', error);
        container.innerHTML = '<div class="empty-state">Failed to load seed URLs</div>';
    }
}

// Load categories for filter
async function loadCategories() {
    try {
        const response = await fetch('/news/categories');
        const data = await response.json();
        
        if (data.status === 'success' && data.categories) {
            const select = document.getElementById('filter-category');
            Object.keys(data.categories).forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = `${category} (${data.categories[category]})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load languages for filter
async function loadLanguages() {
    try {
        const response = await fetch('/news/filters');
        const data = await response.json();
        
        if (data.status === 'success' && data.languages) {
            const select = document.getElementById('filter-language');
            Object.keys(data.languages).forEach(lang => {
                const option = document.createElement('option');
                option.value = lang;
                option.textContent = `${lang.toUpperCase()} (${data.languages[lang]})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load languages:', error);
    }
}

// Load countries for filter
async function loadCountries() {
    try {
        const response = await fetch('/news/filters');
        const data = await response.json();
        
        if (data.status === 'success' && data.countries) {
            const select = document.getElementById('filter-country');
            Object.keys(data.countries).forEach(country => {
                const option = document.createElement('option');
                option.value = country;
                option.textContent = `${country.toUpperCase()} (${data.countries[country]})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load countries:', error);
    }
}

// Update pagination
function updatePagination(pagination) {
    const container = document.getElementById('news-pagination');
    if (!pagination) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button ${!pagination.has_prev ? 'disabled' : ''} onclick="loadNews(${pagination.prev_page})">Previous</button>`;
    
    // Page info
    html += `<span style="padding: 8px 16px;">Page ${pagination.current_page} of ${pagination.total_pages}</span>`;
    
    // Next button
    html += `<button ${!pagination.has_next ? 'disabled' : ''} onclick="loadNews(${pagination.next_page})">Next</button>`;
    
    container.innerHTML = html;
}

// Helper function to get status badge
function getStatusBadge(status) {
    const badges = {
        'completed': '<span class="badge badge-success">Completed</span>',
        'progress': '<span class="badge badge-warning">In Progress</span>',
        'failed': '<span class="badge badge-danger">Failed</span>'
    };
    return badges[status] || '<span class="badge badge-info">Unknown</span>';
}

// Run fetch job
async function runFetchJob() {
    if (!confirm('Run news fetch job now?')) return;

    try {
        const response = await fetch('/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        const data = await response.json();

        if (data.job_id) {
            alert(`✅ Job started successfully!\nJob ID: ${data.job_id}`);
            setTimeout(refreshStats, 2000);
        } else {
            alert(`❌ Failed to start job: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// Refresh stats
function refreshStats() {
    loadStats();
    if (currentTab === 'news') loadNews(currentPage);
    if (currentTab === 'seeds') loadSeeds();
}

// View article details
function viewArticle(articleId) {
    alert(`Article details for ID: ${articleId}\n\nThis feature will open article details in a modal.`);
}

// Open add seed modal
function openAddSeedModal() {
    document.getElementById('modal-title').textContent = 'Add Seed URL';
    document.getElementById('seed-form').reset();
    document.getElementById('seed-form').dataset.mode = 'add';
    document.getElementById('seed-form').dataset.partnerId = '';

    // Hide partner ID field for add mode (auto-generated in backend)
    document.getElementById('partner-id-group').style.display = 'none';

    document.getElementById('seed-modal').classList.add('active');
}

// Open edit seed modal
async function editSeed(seed) {
    try {
        // Fetch full seed URL data from the server
        const response = await fetch(`/seed-urls/${seed.partner_id}`);
        const data = await response.json();

        if (data.status !== 'success') {
            alert(`❌ Failed to load seed URL: ${data.error}`);
            return;
        }

        const fullSeed = data.seed_url;

        document.getElementById('modal-title').textContent = 'Edit Seed URL';
        document.getElementById('seed-form').dataset.mode = 'edit';
        document.getElementById('seed-form').dataset.partnerId = fullSeed.partner_id;

        // Show partner ID field for edit mode (read-only)
        document.getElementById('partner-id-group').style.display = 'block';

        // Populate form fields with full data
        document.getElementById('seed-partner-id').value = fullSeed.partner_id || '';
        document.getElementById('seed-partner-name').value = fullSeed.partner_name || '';
        document.getElementById('seed-name').value = fullSeed.name || '';
        document.getElementById('seed-url').value = fullSeed.url || '';
        document.getElementById('seed-provider').value = fullSeed.provider || 'gnews';

        // Handle category - can be string or array
        const categorySelect = document.getElementById('seed-category');
        const categories = Array.isArray(fullSeed.category) ? fullSeed.category : [fullSeed.category || 'general'];
        // Clear all selections first
        Array.from(categorySelect.options).forEach(option => option.selected = false);
        // Select the categories
        categories.forEach(cat => {
            Array.from(categorySelect.options).forEach(option => {
                if (option.value === cat) {
                    option.selected = true;
                }
            });
        });

        document.getElementById('seed-country').value = fullSeed.country || 'in';
        document.getElementById('seed-language').value = fullSeed.language || 'en';
        document.getElementById('seed-frequency').value = fullSeed.frequency_minutes || 60;
        document.getElementById('seed-active').checked = fullSeed.is_active !== false;

        document.getElementById('seed-modal').classList.add('active');
    } catch (error) {
        alert(`❌ Error loading seed URL: ${error.message}`);
    }
}

// Close seed modal
function closeSeedModal() {
    document.getElementById('seed-modal').classList.remove('active');
    document.getElementById('seed-form').reset();
    document.getElementById('seed-partner-id').disabled = false;
}

// Save seed URL
async function saveSeedUrl(event) {
    event.preventDefault();

    const form = document.getElementById('seed-form');
    const mode = form.dataset.mode || 'add';
    const partnerId = form.dataset.partnerId;

    // Get selected categories (multi-select)
    const categorySelect = document.getElementById('seed-category');
    const selectedCategories = Array.from(categorySelect.selectedOptions).map(option => option.value);

    // If only one category selected, send as string; if multiple, send as array
    const category = selectedCategories.length === 1 ? selectedCategories[0] : selectedCategories;

    const seedData = {
        partner_name: document.getElementById('seed-partner-name').value,
        name: document.getElementById('seed-name').value,
        url: document.getElementById('seed-url').value,
        provider: document.getElementById('seed-provider').value,
        category: category,
        country: document.getElementById('seed-country').value,
        language: document.getElementById('seed-language').value,
        frequency_minutes: parseInt(document.getElementById('seed-frequency').value),
        is_active: document.getElementById('seed-active').checked
    };

    try {
        let response;
        if (mode === 'edit') {
            // Update existing seed URL - include partner_id for update
            seedData.partner_id = partnerId;
            response = await fetch(`/seed-urls/${partnerId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(seedData)
            });
        } else {
            // Create new seed URL - partner_id will be auto-generated in backend
            response = await fetch('/seed-urls', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(seedData)
            });
        }

        const data = await response.json();

        if (data.status === 'success') {
            alert(`✅ Seed URL ${mode === 'edit' ? 'updated' : 'added'} successfully!`);
            closeSeedModal();
            loadSeeds();
        } else {
            alert(`❌ Failed to ${mode === 'edit' ? 'update' : 'add'} seed URL: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

// Toggle seed status
async function toggleSeedStatus(partnerId, newStatus) {
    // This would require a new API endpoint to update seed URL
    alert(`Toggle status for ${partnerId} to ${newStatus ? 'active' : 'inactive'}\n\nThis feature requires a PATCH endpoint.`);
}

// Delete seed
async function deleteSeed(partnerId) {
    if (!confirm(`Delete seed URL: ${partnerId}?`)) return;
    
    try {
        const response = await fetch(`/seed-urls/${partnerId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.status === 'success') {
            alert('✅ Seed URL deleted successfully!');
            loadSeeds();
        } else {
            alert(`❌ Failed to delete seed URL: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

