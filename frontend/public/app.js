/**
 * Main application JavaScript for Web Crawler Admin UI
 */

// ============ Theme Management ============
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'auto';
    setTheme(savedTheme);
}

function setTheme(theme) {
    localStorage.setItem('theme', theme);
    
    let actualTheme = theme;
    
    if (theme === 'auto') {
        // Use system preference
        actualTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', actualTheme);
    
    // Update theme buttons
    document.getElementById('theme-light')?.classList.remove('active');
    document.getElementById('theme-auto')?.classList.remove('active');
    document.getElementById('theme-dark')?.classList.remove('active');
    
    if (theme === 'light') {
        document.getElementById('theme-light')?.classList.add('active');
    } else if (theme === 'auto') {
        document.getElementById('theme-auto')?.classList.add('active');
    } else if (theme === 'dark') {
        document.getElementById('theme-dark')?.classList.add('active');
    }
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'auto') {
        setTheme('auto');
    }
});

// Global application state
const appState = {
    token: localStorage.getItem('token') || null,
    currentUser: null,
    currentView: 'dashboard',
    selectedCrawlerId: null,

    // Initialize app
    async init() {
        // Initialize theme first
        initTheme();
        
        if (this.token) {
            // Verify token and load main app
            try {
                const response = await fetch('/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${this.token}` }
                });
                if (response.ok) {
                    this.currentUser = await response.json();
                    this.showMainApp();
                    this.navigate('dashboard');
                } else {
                    this.token = null;
                    this.showLoginForm();
                }
            } catch (e) {
                this.showLoginForm();
            }
        } else {
            this.showLoginForm();
        }
    },

    // Authentication
    async login() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (!username || !password) {
            this.showError('Please enter username and password');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                this.token = data.access_token;
                this.currentUser = data.user;
                localStorage.setItem('token', this.token);
                this.showMainApp();
                this.navigate('dashboard');
            } else {
                this.showError('Invalid credentials');
            }
        } catch (e) {
            this.showError(e.message);
        }
    },

    logout() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('token');
        this.showLoginForm();
    },

    // UI Navigation
    showLoginForm() {
        document.getElementById('login-view').classList.remove('hidden');
        document.getElementById('main-view').classList.add('hidden');
    },

    showMainApp() {
        document.getElementById('login-view').classList.add('hidden');
        document.getElementById('main-view').classList.remove('hidden');
        this.checkUserPermissions();
    },

    checkUserPermissions() {
        const hasAdmin = this.currentUser && this.currentUser.roles.includes('admin');
        const hasEditor = this.currentUser && (this.currentUser.roles.includes('editor') || hasAdmin);

        if (!hasAdmin) {
            document.getElementById('nav-admin').classList.add('hidden');
        }
    },

    navigate(view) {
        this.currentView = view;

        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
        document.querySelectorAll('.navbar-menu a').forEach(a => a.classList.remove('active'));

        // Show selected view
        const viewEl = document.getElementById(`${view}-view`);
        if (viewEl) {
            viewEl.classList.remove('hidden');
            document.getElementById(`nav-${view}`).classList.add('active');
        }

        // Load view data
        if (view === 'dashboard') {
            this.loadDashboard();
        } else if (view === 'crawlers') {
            this.loadCrawlers();
        } else if (view === 'jobs') {
            this.loadJobs();
        } else if (view === 'admin') {
            this.loadAdminData();
        }
    },

    // Dashboard
    async loadDashboard() {
        try {
            const response = await this.apiCall('/api/admin/stats', 'GET');
            document.getElementById('crawler-count').textContent = response.crawler_count;
            document.getElementById('job-count').textContent = response.job_count;
            document.getElementById('user-count').textContent = response.user_count;
            document.getElementById('storage-used').textContent = response.storage_used_mb + ' MB';
        } catch (e) {
            console.error('Error loading dashboard:', e);
        }
    },

    // Crawlers Management
    async loadCrawlers() {
        try {
            const crawlers = await this.apiCall('/api/crawlers', 'GET');
            const list = document.getElementById('crawlers-list');
            
            if (crawlers.length === 0) {
                list.innerHTML = '<tr><td colspan="5" style="text-align: center;">No crawlers configured</td></tr>';
                return;
            }

            list.innerHTML = crawlers.map(c => `
                <tr>
                    <td><strong>${c.name}</strong></td>
                    <td>${c.description || '—'}</td>
                    <td><span class="badge ${c.enabled ? 'badge-success' : 'badge-danger'}">${c.enabled ? 'Enabled' : 'Disabled'}</span></td>
                    <td>${c.opensearch_index_name}</td>
                    <td>
                        <button onclick="appState.startCrawl(${c.id})">Start</button>
                        <button class="secondary" onclick="appState.editCrawler(${c.id})">Edit</button>
                        <button class="danger" onclick="appState.deleteCrawler(${c.id})">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (e) {
            console.error('Error loading crawlers:', e);
        }
    },

    openCreateCrawlerModal() {
        document.getElementById('crawler-name').value = '';
        document.getElementById('crawler-description').value = '';
        document.getElementById('crawler-seed-urls').value = '';
        document.getElementById('crawler-allowed-domains').value = '';
        document.getElementById('crawler-max-depth').value = '2';
        document.getElementById('crawler-extract-pdfs').checked = true;
        document.getElementById('crawler-extract-docx').checked = true;
        document.getElementById('crawler-follow-sitemap').checked = true;
        document.getElementById('crawler-modal').classList.add('active');
    },

    closeCrawlerModal() {
        document.getElementById('crawler-modal').classList.remove('active');
    },

    async saveCrawler(event) {
        event.preventDefault();

        const crawler = {
            name: document.getElementById('crawler-name').value,
            description: document.getElementById('crawler-description').value,
            seed_urls: document.getElementById('crawler-seed-urls').value.split('\n').filter(u => u.trim()),
            allow_domains: document.getElementById('crawler-allowed-domains').value.split('\n').filter(d => d.trim()),
            max_depth: parseInt(document.getElementById('crawler-max-depth').value),
            extract_pdfs: document.getElementById('crawler-extract-pdfs').checked,
            extract_docx: document.getElementById('crawler-extract-docx').checked,
            follow_sitemap: document.getElementById('crawler-follow-sitemap').checked,
            enabled: true
        };

        try {
            await this.apiCall('/api/crawlers', 'POST', crawler);
            this.showSuccess('Crawler created successfully');
            this.closeCrawlerModal();
            this.loadCrawlers();
        } catch (e) {
            this.showError(e.message);
        }
    },

    async startCrawl(crawlerId) {
        if (!confirm('Start crawl for this configuration?')) return;

        try {
            await this.apiCall(`/api/jobs/${crawlerId}/start`, 'POST');
            this.showSuccess('Crawl job started');
            this.loadJobs();
        } catch (e) {
            this.showError(e.message);
        }
    },

    async deleteCrawler(crawlerId) {
        if (!confirm('Delete this crawler? This cannot be undone.')) return;

        try {
            await this.apiCall(`/api/crawlers/${crawlerId}`, 'DELETE');
            this.showSuccess('Crawler deleted');
            this.loadCrawlers();
        } catch (e) {
            this.showError(e.message);
        }
    },

    // Jobs Management
    async loadJobs() {
        try {
            // In production, fetch actual jobs from API
            const list = document.getElementById('jobs-list');
            list.innerHTML = '<tr><td colspan="7" style="text-align: center;">No jobs yet</td></tr>';
        } catch (e) {
            console.error('Error loading jobs:', e);
        }
    },

    // Search
    async search() {
        const query = document.getElementById('search-input').value;
        if (!query) {
            this.showError('Please enter a search query');
            return;
        }

        try {
            const response = await this.apiCall('/api/search', 'POST', {
                q: query,
                content_type: document.getElementById('search-type').value,
                limit: 20
            });

            const results = document.getElementById('search-results-list');
            if (response.results.length === 0) {
                results.innerHTML = '<p>No results found</p>';
                return;
            }

            results.innerHTML = response.results.map(r => `
                <div class="card" style="margin-bottom: 1rem;">
                    <strong><a href="${r.url}" target="_blank">${r.title}</a></strong>
                    <span class="badge badge-info">${r.content_type}</span>
                    <p style="margin-top: 0.5rem; color: #666;">${r.content_snippet}</p>
                    <small style="color: #999;">${r.url}</small>
                </div>
            `).join('');
        } catch (e) {
            this.showError(e.message);
        }
    },

    // Admin
    async loadAdminData() {
        this.loadSystemStats();
        this.loadUsers();
        this.loadIndices();
        this.loadCollections();
    },

    switchAdminTab(tab) {
        document.querySelectorAll('#admin-view .tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('#admin-view .tab').forEach(t => t.classList.remove('active'));
        document.getElementById(`${tab}-tab`).classList.add('active');
        event.target.classList.add('active');
    },

    async loadSystemStats() {
        try {
            const stats = await this.apiCall('/api/admin/stats', 'GET');
            const container = document.getElementById('system-stats');
            const health = await this.apiCall('/api/admin/opensearch/health', 'GET');

            container.innerHTML = `
                <div class="grid">
                    <div class="stat-box">
                        <div class="stat-value">${stats.crawler_count}</div>
                        <div class="stat-label">Crawlers</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${stats.job_count}</div>
                        <div class="stat-label">Jobs</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${stats.user_count}</div>
                        <div class="stat-label">Users</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${stats.storage_used_mb} MB</div>
                        <div class="stat-label">Storage</div>
                    </div>
                </div>
                <div style="margin-top: 2rem;">
                    <h3>OpenSearch Status</h3>
                    <p>Status: <span class="badge ${health.status === 'ok' ? 'badge-success' : 'badge-danger'}">${health.status.toUpperCase()}</span></p>
                    ${health.version ? `<p>Version: ${health.version}</p>` : ''}
                </div>
            `;
        } catch (e) {
            console.error('Error loading system stats:', e);
        }
    },

    async loadUsers() {
        try {
            const users = await this.apiCall('/api/auth/users', 'GET');
            const list = document.getElementById('users-list');

            list.innerHTML = users.map(u => `
                <tr>
                    <td>${u.username}</td>
                    <td>${u.email}</td>
                    <td>${u.roles.join(', ')}</td>
                    <td><span class="badge badge-success">Active</span></td>
                </tr>
            `).join('');
        } catch (e) {
            console.error('Error loading users:', e);
        }
    },

    async loadIndices() {
        try {
            const response = await this.apiCall('/api/search/indices', 'GET');
            const list = document.getElementById('indices-list');

            if (response.indices.length === 0) {
                list.innerHTML = '<tr><td colspan="4" style="text-align: center;">No indices</td></tr>';
                return;
            }

            list.innerHTML = response.indices.map(i => `
                <tr>
                    <td>${i.name}</td>
                    <td>${i.document_count}</td>
                    <td>${i.size_mb} MB</td>
                    <td>
                        <button class="secondary" onclick="appState.reindexDocuments('${i.name}')">Reindex</button>
                        <button class="danger" onclick="appState.deleteIndex('${i.name}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (e) {
            console.error('Error loading indices:', e);
        }
    },

    async loadCollections() {
        try {
            const response = await this.apiCall('/api/admin/collections', 'GET');
            const list = document.getElementById('collections-list');

            if (response.collections.length === 0) {
                list.innerHTML = '<tr><td colspan="5" style="text-align: center;">No collections</td></tr>';
                return;
            }

            list.innerHTML = response.collections.map(c => `
                <tr>
                    <td>${c.name}</td>
                    <td>${c.document_count}</td>
                    <td>${c.file_size_bytes / 1024 / 1024 > 0 ? (c.file_size_bytes / 1024 / 1024).toFixed(2) : 0} MB</td>
                    <td>${c.created || '—'}</td>
                    <td>
                        <button class="danger" onclick="appState.deleteCollection('${c.name}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } catch (e) {
            console.error('Error loading collections:', e);
        }
    },

    async reindexDocuments(indexName) {
        if (!confirm('Reindex documents from collection?')) return;

        try {
            await this.apiCall(`/api/admin/indices/${indexName}/reindex`, 'POST');
            this.showSuccess('Reindexing started');
            this.loadIndices();
        } catch (e) {
            this.showError(e.message);
        }
    },

    async deleteIndex(indexName) {
        if (!confirm('Delete this index? This cannot be undone.')) return;

        try {
            await this.apiCall(`/api/admin/indices/${indexName}`, 'DELETE');
            this.showSuccess('Index deleted');
            this.loadIndices();
        } catch (e) {
            this.showError(e.message);
        }
    },

    async deleteCollection(collectionName) {
        if (!confirm('Delete this collection? This cannot be undone.')) return;

        try {
            await this.apiCall(`/api/admin/collections/${collectionName}`, 'DELETE');
            this.showSuccess('Collection deleted');
            this.loadCollections();
        } catch (e) {
            this.showError(e.message);
        }
    },

    // API Helper
    async apiCall(url, method = 'GET', body = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (this.token) {
            options.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            if (response.status === 401) {
                this.logout();
                throw new Error('Authentication failed');
            }
            const error = await response.text();
            throw new Error(error || `HTTP ${response.status}`);
        }

        return await response.json();
    },

    // Notifications
    showError(message) {
        const errorEl = document.getElementById('login-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.remove('hidden');
        }
    },

    showSuccess(message) {
        alert(message); // Simple notification - enhance in production
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => appState.init());
