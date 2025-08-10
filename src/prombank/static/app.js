// Prombank Web Interface
class PromptManager {
    constructor() {
        this.currentPrompt = null;
        this.isDirty = false;
        this.prompts = [];
        this.categories = [];
        
        this.initializeApp();
        this.bindEvents();
        this.loadInitialData();
    }
    
    initializeApp() {
        this.elements = {
            promptList: document.getElementById('prompt-list'),
            searchInput: document.getElementById('search-input'),
            newPromptBtn: document.getElementById('new-prompt-btn'),
            saveBtn: document.getElementById('save-btn'),
            
            promptTitle: document.getElementById('prompt-title'),
            promptContent: document.getElementById('prompt-content'),
            promptDescription: document.getElementById('prompt-description'),
            promptCategory: document.getElementById('prompt-category'),
            promptTags: document.getElementById('prompt-tags'),
            isPublic: document.getElementById('is-public'),
            isTemplate: document.getElementById('is-template'),
            
            charCount: document.getElementById('char-count'),
            wordCount: document.getElementById('word-count'),
            lineCount: document.getElementById('line-count'),
            variablesList: document.getElementById('variables-list'),
            
            deleteModal: document.getElementById('delete-modal'),
            confirmDelete: document.getElementById('confirm-delete')
        };
    }
    
    bindEvents() {
        // Header actions
        this.elements.newPromptBtn.addEventListener('click', () => this.createNewPrompt());
        this.elements.saveBtn.addEventListener('click', () => this.saveCurrentPrompt());
        
        // Search
        this.elements.searchInput.addEventListener('input', (e) => this.searchPrompts(e.target.value));
        
        // Editor changes
        this.elements.promptTitle.addEventListener('input', () => this.markDirty());
        this.elements.promptContent.addEventListener('input', () => {
            this.markDirty();
            this.updateStats();
            this.updateVariables();
        });
        this.elements.promptDescription.addEventListener('input', () => this.markDirty());
        this.elements.promptCategory.addEventListener('change', () => this.markDirty());
        this.elements.promptTags.addEventListener('input', () => this.markDirty());
        this.elements.isPublic.addEventListener('change', () => this.markDirty());
        this.elements.isTemplate.addEventListener('change', () => this.markDirty());
        
        // Tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // Delete confirmation
        this.elements.confirmDelete.addEventListener('click', () => this.deleteConfirmed());
        
        // User profile actions
        document.getElementById('manage-tokens-btn')?.addEventListener('click', () => this.showTokenModal());
        document.getElementById('logout-btn')?.addEventListener('click', () => this.logout());
        
        // Token management
        document.getElementById('generate-token-btn')?.addEventListener('click', () => this.generateToken());
        document.getElementById('copy-token-btn')?.addEventListener('click', () => this.copyToken());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Auto-save
        setInterval(() => this.autoSave(), 30000); // Auto-save every 30 seconds
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadPrompts(),
                this.loadCategories(),
                this.loadUserProfile()
            ]);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load data. Please refresh the page.');
        }
    }
    
    async loadPrompts() {
        try {
            const response = await fetch('/api/v1/prompts?limit=100');
            if (!response.ok) throw new Error('Failed to fetch prompts');
            
            const data = await response.json();
            this.prompts = data.data || [];
            this.renderPromptList();
            
            // Load first prompt if available
            if (this.prompts.length > 0 && !this.currentPrompt) {
                this.loadPrompt(this.prompts[0].id);
            }
        } catch (error) {
            console.error('Error loading prompts:', error);
            this.elements.promptList.innerHTML = '<div class="loading">Failed to load prompts</div>';
        }
    }
    
    async loadCategories() {
        try {
            const response = await fetch('/api/v1/categories');
            if (!response.ok) throw new Error('Failed to fetch categories');
            
            const data = await response.json();
            this.categories = data.data || [];
            this.renderCategoryOptions();
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }
    
    renderPromptList(filteredPrompts = null) {
        const promptsToShow = filteredPrompts || this.prompts;
        
        if (promptsToShow.length === 0) {
            this.elements.promptList.innerHTML = `
                <div class="loading">
                    ${filteredPrompts ? 'No prompts found' : 'No prompts yet'}
                </div>
            `;
            return;
        }
        
        this.elements.promptList.innerHTML = promptsToShow.map(prompt => {
            // Handle tags properly - they might be objects or strings
            const tagNames = prompt.tags?.map(tag => typeof tag === 'string' ? tag : tag.name) || [];
            const tagsDisplay = tagNames.length > 0 ? tagNames.join(', ') : 'No tags';
            
            return `
                <div class="prompt-item ${this.currentPrompt?.id === prompt.id ? 'active' : ''}" 
                     data-id="${prompt.id}">
                    <div class="prompt-item-title">${this.escapeHtml(prompt.title)}</div>
                    <div class="prompt-item-meta">
                        <span>${prompt.category || 'No category'}</span>
                        <span>${tagsDisplay}</span>
                    </div>
                    <div class="prompt-item-actions">
                        <button class="btn btn-small btn-primary" onclick="window.open('/api/v1/prompts/${prompt.id}/raw?include_metadata=true', '_blank')">
                            👁️ View
                        </button>
                        <button class="btn btn-small btn-secondary" onclick="app.loadPrompt(${prompt.id})">
                            📝 Edit
                        </button>
                        <button class="btn btn-small btn-danger" onclick="app.deletePrompt(${prompt.id})">
                            🗑️
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        
        // Bind click events
        this.elements.promptList.querySelectorAll('.prompt-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.prompt-item-actions')) {
                    this.loadPrompt(parseInt(item.dataset.id));
                }
            });
        });
    }
    
    renderCategoryOptions() {
        const options = this.categories.map(cat => 
            `<option value="${cat.id}">${this.escapeHtml(cat.name)}</option>`
        ).join('');
        
        this.elements.promptCategory.innerHTML = `
            <option value="">No Category</option>
            ${options}
        `;
    }
    
    async loadPrompt(promptId) {
        try {
            const response = await fetch(`/api/v1/prompts/${promptId}`);
            if (!response.ok) throw new Error('Failed to fetch prompt');
            
            const prompt = await response.json();
            console.log('Loaded prompt data:', prompt); // Debug logging
            this.currentPrompt = prompt;
            this.populateEditor(prompt);
            this.updateActivePromptInList();
            this.isDirty = false;
            this.updateSaveButton();
        } catch (error) {
            console.error('Error loading prompt:', error);
            this.showError('Failed to load prompt');
        }
    }
    
    populateEditor(prompt) {
        this.elements.promptTitle.value = prompt.title || '';
        this.elements.promptContent.value = prompt.content || '';
        this.elements.promptDescription.value = prompt.description || '';
        this.elements.promptCategory.value = prompt.category_id || '';
        
        // Handle tags - they come as objects with 'name' field
        const tagNames = prompt.tags?.map(tag => typeof tag === 'string' ? tag : tag.name) || [];
        this.elements.promptTags.value = tagNames.join(', ');
        
        this.elements.isPublic.checked = prompt.is_public || false;
        this.elements.isTemplate.checked = prompt.is_template || false;
        
        this.updateStats();
        this.updateVariables();
    }
    
    createNewPrompt() {
        if (this.isDirty && !confirm('You have unsaved changes. Continue?')) {
            return;
        }
        
        this.currentPrompt = null;
        this.populateEditor({
            title: '',
            content: '',
            description: '',
            category_id: '',
            tags: [],
            is_public: false,
            is_template: false
        });
        
        this.updateActivePromptInList();
        this.elements.promptTitle.focus();
        this.isDirty = false;
        this.updateSaveButton();
    }
    
    async saveCurrentPrompt() {
        const promptData = {
            title: this.elements.promptTitle.value.trim() || 'Untitled Prompt',
            content: this.elements.promptContent.value,
            description: this.elements.promptDescription.value,
            category_id: this.elements.promptCategory.value || null,
            tags: this.elements.promptTags.value.split(',').map(t => t.trim()).filter(t => t),
            is_public: this.elements.isPublic.checked,
            is_template: this.elements.isTemplate.checked
        };
        
        try {
            let response;
            if (this.currentPrompt?.id) {
                // Update existing prompt
                response = await fetch(`/api/v1/prompts/${this.currentPrompt.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(promptData)
                });
            } else {
                // Create new prompt
                response = await fetch('/api/v1/prompts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(promptData)
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save prompt');
            }
            
            const savedPrompt = await response.json();
            this.currentPrompt = savedPrompt;
            this.isDirty = false;
            this.updateSaveButton();
            
            await this.loadPrompts(); // Refresh the list
            this.showSuccess('Prompt saved successfully!');
            
        } catch (error) {
            console.error('Error saving prompt:', error);
            this.showError(`Failed to save prompt: ${error.message}`);
        }
    }
    
    async deletePrompt(promptId) {
        // Store the ID for the confirmation dialog
        this.deletePromptId = promptId;
        this.showModal('delete-modal');
    }
    
    async deleteConfirmed() {
        if (!this.deletePromptId) return;
        
        try {
            const response = await fetch(`/api/v1/prompts/${this.deletePromptId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to delete prompt');
            
            // If we deleted the current prompt, create a new one
            if (this.currentPrompt?.id === this.deletePromptId) {
                this.createNewPrompt();
            }
            
            await this.loadPrompts(); // Refresh the list
            this.closeModal('delete-modal');
            this.showSuccess('Prompt deleted successfully!');
            
        } catch (error) {
            console.error('Error deleting prompt:', error);
            this.showError('Failed to delete prompt');
        } finally {
            this.deletePromptId = null;
        }
    }
    
    searchPrompts(query) {
        if (!query.trim()) {
            this.renderPromptList();
            return;
        }
        
        const filtered = this.prompts.filter(prompt => {
            const title = prompt.title?.toLowerCase() || '';
            const content = prompt.content?.toLowerCase() || '';
            const queryLower = query.toLowerCase();
            
            // Handle tags properly - they might be objects or strings
            const tagNames = prompt.tags?.map(tag => typeof tag === 'string' ? tag : tag.name) || [];
            const tagsMatch = tagNames.some(tagName => 
                tagName?.toLowerCase().includes(queryLower)
            );
            
            return title.includes(queryLower) || 
                   content.includes(queryLower) || 
                   tagsMatch;
        });
        
        this.renderPromptList(filtered);
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }
    
    updateStats() {
        const content = this.elements.promptContent.value;
        const chars = content.length;
        const words = content.trim() ? content.trim().split(/\s+/).length : 0;
        const lines = content.split('\n').length;
        
        this.elements.charCount.textContent = `${chars} characters`;
        this.elements.wordCount.textContent = `${words} words`;
        this.elements.lineCount.textContent = `${lines} lines`;
    }
    
    updateVariables() {
        const content = this.elements.promptContent.value;
        const variables = [...new Set(content.match(/\{\{([^}]+)\}\}/g) || [])];
        
        if (variables.length === 0) {
            this.elements.variablesList.innerHTML = 
                '<p class="no-variables">No variables detected. Use {{variable_name}} syntax in your content.</p>';
        } else {
            this.elements.variablesList.innerHTML = variables.map(variable => {
                const name = variable.slice(2, -2).trim();
                return `
                    <div class="variable-item">
                        <span class="variable-name">${this.escapeHtml(variable)}</span>
                        <span class="variable-description">${this.escapeHtml(name)}</span>
                    </div>
                `;
            }).join('');
        }
    }
    
    markDirty() {
        this.isDirty = true;
        this.updateSaveButton();
    }
    
    updateSaveButton() {
        this.elements.saveBtn.disabled = !this.isDirty;
        this.elements.saveBtn.textContent = this.isDirty ? '💾 Save *' : '💾 Saved';
    }
    
    updateActivePromptInList() {
        document.querySelectorAll('.prompt-item').forEach(item => {
            item.classList.toggle('active', 
                this.currentPrompt && parseInt(item.dataset.id) === this.currentPrompt.id
            );
        });
    }
    
    autoSave() {
        if (this.isDirty && this.currentPrompt?.id) {
            console.log('Auto-saving...');
            this.saveCurrentPrompt();
        }
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + S: Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            if (!this.elements.saveBtn.disabled) {
                this.saveCurrentPrompt();
            }
        }
        
        // Ctrl/Cmd + N: New prompt
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            this.createNewPrompt();
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal.active').forEach(modal => {
                this.closeModal(modal.id);
            });
        }
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }
    
    closeModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }
    
    showSuccess(message) {
        // Simple success notification (you could enhance this with a proper toast system)
        console.log('Success:', message);
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        // Simple error notification (you could enhance this with a proper toast system)
        console.error('Error:', message);
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type = 'info') {
        // Create a simple notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            color: white;
            z-index: 1001;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            font-size: 14px;
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // User Profile Methods
    async loadUserProfile() {
        try {
            // Check if we have access token in URL (from OAuth redirect)
            const urlParams = new URLSearchParams(window.location.search);
            const accessToken = urlParams.get('access_token');
            
            if (accessToken) {
                // Store token and clean URL
                localStorage.setItem('auth_token', accessToken);
                window.history.replaceState({}, document.title, window.location.pathname);
            }

            const token = localStorage.getItem('auth_token');
            if (!token) {
                // No token, redirect to login
                window.location.href = '/';
                return;
            }

            // Get user profile from token
            const userData = this.parseJWT(token);
            if (!userData) {
                this.logout();
                return;
            }

            // Display user profile
            this.displayUserProfile(userData);
            
        } catch (error) {
            console.error('Error loading user profile:', error);
            this.logout();
        }
    }

    parseJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (error) {
            console.error('Error parsing JWT:', error);
            return null;
        }
    }

    displayUserProfile(userData) {
        const userProfile = document.getElementById('user-profile');
        const userAvatar = document.getElementById('user-avatar');
        const userName = document.getElementById('user-name');
        const userEmail = document.getElementById('user-email');

        if (userProfile && userName && userEmail) {
            userName.textContent = userData.name || userData.email.split('@')[0];
            userEmail.textContent = userData.email;
            
            // Set avatar if available (from Google OAuth)
            if (userAvatar && userData.picture) {
                userAvatar.src = userData.picture;
            } else if (userAvatar) {
                // Default avatar
                userAvatar.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(userData.email)}&background=3b82f6&color=fff`;
            }

            userProfile.style.display = 'block';
        }
    }

    // Token Management Methods
    showTokenModal() {
        console.log('🔑 Opening token modal...');
        const modal = document.getElementById('token-modal');
        if (modal) {
            modal.classList.add('active');
            console.log('✅ Modal opened, loading tokens...');
            this.loadTokens();
        } else {
            console.error('❌ Token modal not found!');
            this.showError('Token modal not found');
        }
    }

    async loadTokens() {
        console.log('📋 Loading tokens...');
        try {
            const token = localStorage.getItem('auth_token');
            console.log('🎫 Auth token found:', token ? `${token.substring(0, 20)}...` : 'NONE');
            
            if (!token) {
                console.error('❌ No auth token found');
                this.showError('Please login first');
                return;
            }

            console.log('🔗 Making request to /api/v1/tokens');
            const response = await fetch('/api/v1/tokens', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            console.log('📡 Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Tokens loaded:', data);
                // Handle response structure: { tokens: [...], count: N }
                this.displayTokens(data.tokens || []);
            } else {
                const errorText = await response.text();
                console.error('❌ Failed to load tokens:', response.status, errorText);
                this.showError(`Failed to load tokens: ${response.status}`);
            }
        } catch (error) {
            console.error('💥 Error loading tokens:', error);
            document.getElementById('tokens-list').innerHTML = '<div class="error">Failed to load tokens</div>';
            this.showError('Network error loading tokens');
        }
    }

    displayTokens(tokens) {
        const tokensList = document.getElementById('tokens-list');
        if (!tokensList) return;

        if (tokens.length === 0) {
            tokensList.innerHTML = '<p style="color: var(--text-muted); text-align: center;">No tokens created yet.</p>';
            return;
        }

        tokensList.innerHTML = tokens.map(token => `
            <div class="token-item">
                <div class="token-info">
                    <h5>${this.escapeHtml(token.name)}</h5>
                    <p>Created: ${new Date(token.created_at).toLocaleDateString()}</p>
                </div>
                <div class="token-actions">
                    <button class="btn btn-small btn-danger" onclick="app.deleteToken(${token.id})">Delete</button>
                </div>
            </div>
        `).join('');
    }

    async generateToken() {
        console.log('🔑 Generating new token...');
        const tokenName = document.getElementById('token-name');
        const name = tokenName?.value.trim();
        
        console.log('📝 Token name:', name);
        
        if (!name) {
            console.error('❌ No token name provided');
            this.showError('Please enter a token name');
            return;
        }

        try {
            const authToken = localStorage.getItem('auth_token');
            console.log('🎫 Using auth token:', authToken ? `${authToken.substring(0, 20)}...` : 'NONE');
            
            if (!authToken) {
                console.error('❌ No auth token found');
                this.showError('Please login first');
                return;
            }

            console.log('🚀 Making POST request to /api/v1/tokens');
            const response = await fetch('/api/v1/tokens', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({ name })
            });

            console.log('📡 Generate response status:', response.status);

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Token generated successfully:', result);
                // Match working implementation: result.token.accessLink
                this.showGeneratedToken(result.token.accessLink);
                tokenName.value = '';
                this.loadTokens(); // Refresh the list
            } else {
                const errorText = await response.text();
                console.error('❌ Failed to generate token:', response.status, errorText);
                let errorMessage;
                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.detail || 'Failed to generate token';
                } catch {
                    errorMessage = `Failed to generate token (${response.status})`;
                }
                this.showError(errorMessage);
            }
        } catch (error) {
            console.error('💥 Error generating token:', error);
            this.showError('Network error generating token');
        }
    }

    showGeneratedToken(token) {
        const tokenDisplay = document.getElementById('token-display');
        const generatedToken = document.getElementById('generated-token');
        
        if (tokenDisplay && generatedToken) {
            generatedToken.textContent = token;
            tokenDisplay.style.display = 'block';
        }
    }

    copyToken() {
        const generatedToken = document.getElementById('generated-token');
        if (generatedToken) {
            navigator.clipboard.writeText(generatedToken.textContent).then(() => {
                this.showSuccess('Token copied to clipboard!');
            }).catch(() => {
                this.showError('Failed to copy token');
            });
        }
    }

    async deleteToken(tokenId) {
        if (!confirm('Are you sure you want to delete this token? This action cannot be undone.')) {
            return;
        }

        try {
            const authToken = localStorage.getItem('auth_token');
            const response = await fetch(`/api/v1/tokens/${tokenId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });

            if (response.ok) {
                this.showSuccess('Token deleted successfully');
                this.loadTokens(); // Refresh the list
            } else {
                this.showError('Failed to delete token');
            }
        } catch (error) {
            console.error('Error deleting token:', error);
            this.showError('Failed to delete token');
        }
    }

    logout() {
        localStorage.removeItem('auth_token');
        window.location.href = '/';
    }
}

// Global functions for onclick handlers
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PromptManager();
});

// Prevent accidental page refresh when there are unsaved changes
window.addEventListener('beforeunload', (e) => {
    if (window.app && window.app.isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
});