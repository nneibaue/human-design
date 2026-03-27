/* ==========================================================================
   Transcription Service - JavaScript Application
   ========================================================================== */

/**
 * Core application modules:
 * - Auth: JWT token management and authorization
 * - FormValidation: Email, password, YouTube URL validation
 * - FileUpload: File selection, drag & drop, upload with progress
 * - JobPolling: Real-time job status updates
 * - UI: User interface interactions and state management
 */

/* ==========================================================================
   Configuration
   ========================================================================== */

const CONFIG = {
  // API endpoints
  API_BASE: '/api',
  AUTH_BASE: '/api/auth',
  JOBS_BASE: '/api/jobs',

  // Polling configuration
  POLL_INTERVAL: 5000, // 5 seconds
  DASHBOARD_REFRESH_INTERVAL: 5000, // 5 seconds

  // Upload limits
  MAX_FILE_SIZE: 5 * 1024 * 1024 * 1024, // 5GB
  PRESIGNED_THRESHOLD: 100 * 1024 * 1024, // 100MB

  // Validation patterns
  EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  YOUTUBE_PATTERN: /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/,

  // JWT storage key
  TOKEN_KEY: 'transcription_jwt_token',
};

/* ==========================================================================
   Auth Module - JWT Token Management
   ========================================================================== */

const Auth = {
  /**
   * Store JWT token in localStorage
   * @param {string} token - JWT access token
   */
  setToken(token) {
    localStorage.setItem(CONFIG.TOKEN_KEY, token);
  },

  /**
   * Retrieve JWT token from localStorage
   * @returns {string|null} JWT token or null if not found
   */
  getToken() {
    return localStorage.getItem(CONFIG.TOKEN_KEY);
  },

  /**
   * Remove JWT token from localStorage
   */
  removeToken() {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
  },

  /**
   * Check if user is authenticated
   * @returns {boolean} True if token exists
   */
  isAuthenticated() {
    return this.getToken() !== null;
  },

  /**
   * Logout user and redirect to login page
   */
  logout() {
    this.removeToken();
    window.location.href = '/';
  },

  /**
   * Make authenticated API request with JWT token
   * @param {string} url - API endpoint URL
   * @param {RequestInit} options - Fetch options
   * @returns {Promise<Response>} Fetch response
   */
  async fetch(url, options = {}) {
    const token = this.getToken();

    // Add Authorization header
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized - token expired or invalid
      if (response.status === 401) {
        this.removeToken();
        window.location.href = '/';
        throw new Error('Unauthorized - please login again');
      }

      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  },

  /**
   * Make authenticated JSON API request
   * @param {string} url - API endpoint URL
   * @param {RequestInit} options - Fetch options
   * @returns {Promise<any>} Parsed JSON response
   */
  async fetchJSON(url, options = {}) {
    const response = await this.fetch(url, options);

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  },
};

/* ==========================================================================
   Form Validation Module
   ========================================================================== */

const FormValidation = {
  /**
   * Validate email format
   * @param {string} email - Email address to validate
   * @returns {Object} Validation result {valid: boolean, error?: string}
   */
  validateEmail(email) {
    if (!email) {
      return { valid: false, error: 'Email is required' };
    }

    if (!CONFIG.EMAIL_PATTERN.test(email)) {
      return { valid: false, error: 'Please enter a valid email address' };
    }

    return { valid: true };
  },

  /**
   * Validate password requirements
   * @param {string} password - Password to validate
   * @returns {Object} Validation result {valid: boolean, error?: string}
   */
  validatePassword(password) {
    if (!password) {
      return { valid: false, error: 'Password is required' };
    }

    if (password.length < 8) {
      return { valid: false, error: 'Password must be at least 8 characters' };
    }

    return { valid: true };
  },

  /**
   * Validate YouTube URL format
   * @param {string} url - YouTube URL to validate
   * @returns {Object} Validation result {valid: boolean, error?: string}
   */
  validateYouTubeURL(url) {
    if (!url) {
      return { valid: false, error: 'YouTube URL is required' };
    }

    if (!CONFIG.YOUTUBE_PATTERN.test(url)) {
      return { valid: false, error: 'Please enter a valid YouTube URL' };
    }

    return { valid: true };
  },

  /**
   * Show inline error message for form field
   * @param {string} fieldId - ID of the input field
   * @param {string} error - Error message to display
   */
  showError(fieldId, error) {
    const errorElement = document.querySelector(`[data-error-for="${fieldId}"]`);
    if (errorElement) {
      errorElement.textContent = error;
      errorElement.classList.remove('hidden');
    }
  },

  /**
   * Hide inline error message for form field
   * @param {string} fieldId - ID of the input field
   */
  hideError(fieldId) {
    const errorElement = document.querySelector(`[data-error-for="${fieldId}"]`);
    if (errorElement) {
      errorElement.classList.add('hidden');
      errorElement.textContent = '';
    }
  },

  /**
   * Clear all errors in a form
   * @param {HTMLFormElement} form - Form element
   */
  clearFormErrors(form) {
    const errorElements = form.querySelectorAll('[data-error-for]');
    errorElements.forEach(el => {
      el.classList.add('hidden');
      el.textContent = '';
    });
  },
};

/* ==========================================================================
   File Upload Module
   ========================================================================== */

const FileUpload = {
  selectedFiles: [],

  /**
   * Initialize file upload functionality
   */
  init() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-file-form');

    if (!uploadArea || !fileInput || !uploadForm) {
      return; // Not on dashboard page
    }

    // File input change handler
    fileInput.addEventListener('change', (e) => {
      this.handleFileSelection(e.target.files);
    });

    // Drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('dragover');
      this.handleFileSelection(e.dataTransfer.files);
    });

    // Form submit handler
    uploadForm.addEventListener('submit', (e) => {
      e.preventDefault();
      this.uploadFiles();
    });
  },

  /**
   * Handle file selection (from input or drag & drop)
   * @param {FileList} files - Selected files
   */
  handleFileSelection(files) {
    if (!files || files.length === 0) {
      return;
    }

    // Convert FileList to array and validate
    const validFiles = Array.from(files).filter(file => {
      // Check file size
      if (file.size > CONFIG.MAX_FILE_SIZE) {
        UI.showMessage(`File ${file.name} is too large (max 5GB)`, 'error');
        return false;
      }

      // Check file type (basic check)
      const validTypes = ['audio/', 'video/'];
      const isValid = validTypes.some(type => file.type.startsWith(type)) ||
                      ['.mp3', '.mp4', '.wav', '.m4a', '.mov'].some(ext => file.name.toLowerCase().endsWith(ext));

      if (!isValid) {
        UI.showMessage(`File ${file.name} is not a valid audio/video file`, 'error');
        return false;
      }

      return true;
    });

    if (validFiles.length === 0) {
      return;
    }

    this.selectedFiles = validFiles;
    this.updateFilePreview();
    this.enableUploadButton();
  },

  /**
   * Update file preview list
   */
  updateFilePreview() {
    const previewContainer = document.getElementById('file-preview');
    const previewList = document.getElementById('file-preview-list');

    if (!previewContainer || !previewList) {
      return;
    }

    if (this.selectedFiles.length === 0) {
      previewContainer.classList.add('hidden');
      return;
    }

    // Show preview
    previewContainer.classList.remove('hidden');
    previewList.innerHTML = '';

    this.selectedFiles.forEach(file => {
      const li = document.createElement('li');
      li.className = 'file-preview-item';
      li.innerHTML = `
        <span class="file-name">${file.name}</span>
        <span class="file-size text-small text-muted">${this.formatFileSize(file.size)}</span>
      `;
      previewList.appendChild(li);
    });
  },

  /**
   * Enable upload button
   */
  enableUploadButton() {
    const uploadButton = document.querySelector('[data-action="upload-files"]');
    if (uploadButton) {
      uploadButton.disabled = false;
    }
  },

  /**
   * Upload files to server
   */
  async uploadFiles() {
    if (this.selectedFiles.length === 0) {
      return;
    }

    const uploadButton = document.querySelector('[data-action="upload-files"]');
    const buttonLabel = uploadButton?.querySelector('[data-label]');
    const buttonSpinner = uploadButton?.querySelector('[data-spinner]');

    try {
      // Show loading state
      if (uploadButton) uploadButton.disabled = true;
      if (buttonLabel) buttonLabel.textContent = 'Uploading...';
      if (buttonSpinner) buttonSpinner.classList.remove('hidden');

      // Check if any files exceed presigned threshold
      const largeFiles = this.selectedFiles.filter(f => f.size > CONFIG.PRESIGNED_THRESHOLD);

      if (largeFiles.length > 0) {
        // Use presigned upload for large files
        await this.uploadViaPresigned();
      } else {
        // Direct upload for smaller files
        await this.uploadDirect();
      }

      // Success
      UI.showMessage('Files uploaded successfully! Transcription started.', 'success');

      // Reset form
      this.selectedFiles = [];
      this.updateFilePreview();
      document.getElementById('file-input').value = '';

      // Refresh job list
      if (window.Dashboard) {
        Dashboard.loadJobs();
      }

    } catch (error) {
      console.error('Upload failed:', error);
      UI.showMessage(error.message || 'Upload failed. Please try again.', 'error');
    } finally {
      // Reset button state
      if (uploadButton) uploadButton.disabled = false;
      if (buttonLabel) buttonLabel.textContent = 'Upload Files';
      if (buttonSpinner) buttonSpinner.classList.add('hidden');
    }
  },

  /**
   * Upload files directly (< 100MB)
   */
  async uploadDirect() {
    const formData = new FormData();
    this.selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    const response = await Auth.fetch(`${CONFIG.JOBS_BASE}/upload`, {
      method: 'POST',
      headers: {}, // Don't set Content-Type for FormData
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  /**
   * Upload files via presigned URLs (> 100MB)
   */
  async uploadViaPresigned() {
    // Request presigned URLs
    const fileMetadata = this.selectedFiles.map(file => ({
      filename: file.name,
      content_type: file.type || 'application/octet-stream',
      size_bytes: file.size,
    }));

    const presignedResponse = await Auth.fetchJSON(`${CONFIG.JOBS_BASE}/upload/presigned`, {
      method: 'POST',
      body: JSON.stringify({ files: fileMetadata }),
    });

    const { job_id, uploads } = presignedResponse;

    // Upload each file to S3 using presigned URLs
    const uploadPromises = uploads.map((upload, index) => {
      const file = this.selectedFiles[index];
      return fetch(upload.upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type || 'application/octet-stream',
        },
      });
    });

    await Promise.all(uploadPromises);

    // Confirm upload completion
    const fileIds = uploads.map(u => u.file_id);
    await Auth.fetchJSON(`${CONFIG.JOBS_BASE}/upload/complete`, {
      method: 'POST',
      body: JSON.stringify({
        job_id,
        file_ids: fileIds,
      }),
    });
  },

  /**
   * Format file size for display
   * @param {number} bytes - File size in bytes
   * @returns {string} Formatted file size (e.g., "1.5 MB")
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },
};

/* ==========================================================================
   Job Polling Module
   ========================================================================== */

const JobPolling = {
  pollInterval: null,
  isPolling: false,
  visibilityChangeHandler: null,

  /**
   * Start polling for job updates
   */
  start() {
    if (this.isPolling) {
      return;
    }

    this.isPolling = true;
    this.poll(); // Initial poll

    this.pollInterval = setInterval(() => {
      // Only poll if page is visible
      if (!document.hidden) {
        this.poll();
      }
    }, CONFIG.POLL_INTERVAL);

    // Handle page visibility changes
    this.visibilityChangeHandler = () => {
      if (!document.hidden && this.isPolling) {
        this.poll(); // Poll immediately when page becomes visible
      }
    };

    document.addEventListener('visibilitychange', this.visibilityChangeHandler);
  },

  /**
   * Stop polling for job updates
   */
  stop() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    if (this.visibilityChangeHandler) {
      document.removeEventListener('visibilitychange', this.visibilityChangeHandler);
      this.visibilityChangeHandler = null;
    }

    this.isPolling = false;
  },

  /**
   * Poll for job updates
   */
  async poll() {
    try {
      const response = await Auth.fetchJSON(`${CONFIG.JOBS_BASE}?limit=20&offset=0`);
      this.updateJobList(response);
    } catch (error) {
      console.error('Failed to poll jobs:', error);
    }
  },

  /**
   * Update job list UI with new data
   * @param {Array} jobs - Array of job objects
   */
  updateJobList(jobs) {
    const jobsLoading = document.getElementById('jobs-loading');
    const jobsEmpty = document.getElementById('jobs-empty');
    const jobsList = document.getElementById('jobs-list');
    const jobsCards = document.getElementById('jobs-cards');
    const jobsTableBody = document.getElementById('jobs-table-body');

    if (!jobsList) {
      return; // Not on dashboard page
    }

    // Hide loading state
    if (jobsLoading) {
      jobsLoading.classList.add('hidden');
    }

    // Show empty state or job list
    if (jobs.length === 0) {
      if (jobsEmpty) jobsEmpty.classList.remove('hidden');
      if (jobsList) jobsList.classList.add('hidden');
      return;
    }

    if (jobsEmpty) jobsEmpty.classList.add('hidden');
    if (jobsList) jobsList.classList.remove('hidden');

    // Update mobile cards
    if (jobsCards) {
      jobsCards.innerHTML = jobs.map(job => this.renderJobCard(job)).join('');
    }

    // Update desktop table
    if (jobsTableBody) {
      jobsTableBody.innerHTML = jobs.map(job => this.renderJobRow(job)).join('');
    }

    // Add event listeners for delete buttons
    this.attachDeleteHandlers();
  },

  /**
   * Render job card for mobile view
   * @param {Object} job - Job object
   * @returns {string} HTML string
   */
  renderJobCard(job) {
    const statusClass = this.getStatusClass(job.status);
    const progress = job.total_files > 0 ? (job.completed_files / job.total_files) * 100 : 0;
    const createdDate = new Date(job.created_at).toLocaleString();

    return `
      <div class="job-card card">
        <div class="job-card-header">
          <div class="job-card-id">
            <span class="text-small text-muted">Job ID:</span>
            <code class="text-small">${job.job_id.substring(0, 8)}</code>
          </div>
          <span class="status-badge status-${statusClass}">${job.status}</span>
        </div>

        <div class="job-card-body">
          <div class="job-card-stat">
            <span class="job-card-label">Created:</span>
            <span class="job-card-value">${createdDate}</span>
          </div>

          <div class="job-card-stat">
            <span class="job-card-label">Progress:</span>
            <span class="job-card-value">${job.completed_files}/${job.total_files} files</span>
          </div>

          ${job.total_files > 0 ? `
            <div class="progress-bar">
              <div class="progress-bar-fill" style="width: ${progress}%"></div>
            </div>
          ` : ''}
        </div>

        <div class="job-card-actions btn-group">
          <a href="/jobs/${job.job_id}" class="btn btn-sm btn-secondary">View Details</a>
          <button
            class="btn btn-sm btn-danger"
            data-action="delete-job"
            data-job-id="${job.job_id}"
          >
            Delete
          </button>
        </div>
      </div>
    `;
  },

  /**
   * Render job row for desktop table view
   * @param {Object} job - Job object
   * @returns {string} HTML string
   */
  renderJobRow(job) {
    const statusClass = this.getStatusClass(job.status);
    const progress = job.total_files > 0 ? (job.completed_files / job.total_files) * 100 : 0;
    const createdDate = new Date(job.created_at).toLocaleString();

    return `
      <tr>
        <td><code class="text-small">${job.job_id.substring(0, 8)}</code></td>
        <td><span class="status-badge status-${statusClass}">${job.status}</span></td>
        <td>${createdDate}</td>
        <td>
          ${job.total_files > 0 ? `
            <div style="min-width: 120px;">
              <div class="text-small mb-xs">${job.completed_files}/${job.total_files} files</div>
              <div class="progress-bar">
                <div class="progress-bar-fill" style="width: ${progress}%"></div>
              </div>
            </div>
          ` : 'No files'}
        </td>
        <td>
          <div class="btn-group">
            <a href="/jobs/${job.job_id}" class="btn btn-sm btn-secondary">View</a>
            <button
              class="btn btn-sm btn-danger"
              data-action="delete-job"
              data-job-id="${job.job_id}"
            >
              Delete
            </button>
          </div>
        </td>
      </tr>
    `;
  },

  /**
   * Get CSS class for job status
   * @param {string} status - Job status
   * @returns {string} CSS class name
   */
  getStatusClass(status) {
    const statusMap = {
      queued: 'warning',
      running: 'warning',
      completed: 'success',
      failed: 'error',
    };
    return statusMap[status] || 'warning';
  },

  /**
   * Attach event listeners for delete buttons
   */
  attachDeleteHandlers() {
    const deleteButtons = document.querySelectorAll('[data-action="delete-job"]');
    deleteButtons.forEach(button => {
      button.addEventListener('click', async (e) => {
        const jobId = e.target.dataset.jobId;
        await this.deleteJob(jobId);
      });
    });
  },

  /**
   * Delete a job with confirmation
   * @param {string} jobId - Job UUID
   */
  async deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      return;
    }

    try {
      await Auth.fetch(`${CONFIG.JOBS_BASE}/${jobId}`, {
        method: 'DELETE',
      });

      UI.showMessage('Job deleted successfully', 'success');

      // Refresh job list
      this.poll();
    } catch (error) {
      console.error('Failed to delete job:', error);
      UI.showMessage(error.message || 'Failed to delete job', 'error');
    }
  },
};

/* ==========================================================================
   UI Module - User Interface Interactions
   ========================================================================== */

const UI = {
  /**
   * Show message to user
   * @param {string} message - Message text
   * @param {string} type - Message type: 'success', 'error', 'warning', 'info'
   */
  showMessage(message, type = 'info') {
    const container = document.getElementById('message-container');
    if (!container) {
      return;
    }

    // Clear existing message
    container.innerHTML = '';
    container.classList.remove('hidden');

    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.textContent = message;

    container.appendChild(messageEl);

    // Auto-hide after 5 seconds
    setTimeout(() => {
      container.classList.add('hidden');
    }, 5000);
  },

  /**
   * Hide message
   */
  hideMessage() {
    const container = document.getElementById('message-container');
    if (container) {
      container.classList.add('hidden');
    }
  },

  /**
   * Show loading spinner on button
   * @param {HTMLButtonElement} button - Button element
   * @param {boolean} loading - True to show spinner, false to hide
   */
  setButtonLoading(button, loading) {
    const label = button.querySelector('[data-label]');
    const spinner = button.querySelector('[data-spinner]');

    if (loading) {
      button.disabled = true;
      if (spinner) spinner.classList.remove('hidden');
    } else {
      button.disabled = false;
      if (spinner) spinner.classList.add('hidden');
    }
  },
};

/* ==========================================================================
   Auth Page - Login/Register
   ========================================================================== */

const AuthPage = {
  /**
   * Initialize auth page
   */
  init() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const toggleLink = document.getElementById('toggle-form');
    const logoutLink = document.getElementById('logout-link');

    // Form toggle
    if (toggleLink) {
      toggleLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleForm();
      });
    }

    // Login form
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleLogin(e.target);
      });
    }

    // Register form
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleRegister(e.target);
      });
    }

    // Logout link
    if (logoutLink) {
      logoutLink.addEventListener('click', (e) => {
        e.preventDefault();
        Auth.logout();
      });
    }

    // Redirect if already authenticated
    if (Auth.isAuthenticated() && window.location.pathname === '/') {
      window.location.href = '/dashboard';
    }
  },

  /**
   * Toggle between login and register forms
   */
  toggleForm() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const toggleText = document.getElementById('toggle-text');
    const toggleLinkText = document.getElementById('toggle-link-text');

    const showingLogin = !loginForm.classList.contains('hidden');

    if (showingLogin) {
      // Show register form
      loginForm.classList.add('hidden');
      registerForm.classList.remove('hidden');
      toggleText.textContent = 'Already have an account?';
      toggleLinkText.textContent = 'Sign in';
    } else {
      // Show login form
      registerForm.classList.add('hidden');
      loginForm.classList.remove('hidden');
      toggleText.textContent = "Don't have an account?";
      toggleLinkText.textContent = 'Sign up';
    }

    // Clear form errors
    FormValidation.clearFormErrors(loginForm);
    FormValidation.clearFormErrors(registerForm);
    UI.hideMessage();
  },

  /**
   * Handle login form submission
   * @param {HTMLFormElement} form - Login form element
   */
  async handleLogin(form) {
    const email = form.querySelector('#login-email').value;
    const password = form.querySelector('#login-password').value;
    const submitButton = form.querySelector('[data-action="login"]');

    // Validate
    FormValidation.clearFormErrors(form);

    const emailValidation = FormValidation.validateEmail(email);
    if (!emailValidation.valid) {
      FormValidation.showError('login-email', emailValidation.error);
      return;
    }

    const passwordValidation = FormValidation.validatePassword(password);
    if (!passwordValidation.valid) {
      FormValidation.showError('login-password', passwordValidation.error);
      return;
    }

    try {
      // Show loading state
      UI.setButtonLoading(submitButton, true);

      // Login request
      const response = await fetch(`${CONFIG.AUTH_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(error.detail);
      }

      const data = await response.json();

      // Store token
      Auth.setToken(data.access_token);

      // Redirect to dashboard
      window.location.href = '/dashboard';

    } catch (error) {
      console.error('Login failed:', error);
      UI.showMessage(error.message || 'Login failed. Please try again.', 'error');
      UI.setButtonLoading(submitButton, false);
    }
  },

  /**
   * Handle register form submission
   * @param {HTMLFormElement} form - Register form element
   */
  async handleRegister(form) {
    const email = form.querySelector('#register-email').value;
    const password = form.querySelector('#register-password').value;
    const displayName = form.querySelector('#register-display-name').value;
    const submitButton = form.querySelector('[data-action="register"]');

    // Validate
    FormValidation.clearFormErrors(form);

    const emailValidation = FormValidation.validateEmail(email);
    if (!emailValidation.valid) {
      FormValidation.showError('register-email', emailValidation.error);
      return;
    }

    const passwordValidation = FormValidation.validatePassword(password);
    if (!passwordValidation.valid) {
      FormValidation.showError('register-password', passwordValidation.error);
      return;
    }

    if (!displayName) {
      FormValidation.showError('register-display-name', 'Display name is required');
      return;
    }

    try {
      // Show loading state
      UI.setButtonLoading(submitButton, true);

      // Register request
      const response = await fetch(`${CONFIG.AUTH_BASE}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, display_name: displayName }),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
        throw new Error(error.detail);
      }

      const data = await response.json();

      // Store token
      Auth.setToken(data.access_token);

      // Redirect to dashboard
      window.location.href = '/dashboard';

    } catch (error) {
      console.error('Registration failed:', error);
      UI.showMessage(error.message || 'Registration failed. Please try again.', 'error');
      UI.setButtonLoading(submitButton, false);
    }
  },
};

/* ==========================================================================
   Dashboard Page - File Upload & Job Management
   ========================================================================== */

const Dashboard = {
  /**
   * Initialize dashboard page
   */
  init() {
    // Initialize modules
    FileUpload.init();
    this.initYouTubeUpload();
    this.loadJobs();
    JobPolling.start();

    // Initialize logout link
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
      logoutLink.addEventListener('click', (e) => {
        e.preventDefault();
        Auth.logout();
      });
    }

    // Check authentication
    if (!Auth.isAuthenticated()) {
      window.location.href = '/';
    }
  },

  /**
   * Initialize YouTube upload form
   */
  initYouTubeUpload() {
    const youtubeForm = document.getElementById('upload-youtube-form');
    const youtubeInput = document.getElementById('youtube-url');
    const youtubeButton = document.querySelector('[data-action="upload-youtube"]');

    if (!youtubeForm || !youtubeInput) {
      return;
    }

    // Enable/disable button based on input
    youtubeInput.addEventListener('input', () => {
      if (youtubeButton) {
        youtubeButton.disabled = !youtubeInput.value.trim();
      }
    });

    // Form submit handler
    youtubeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleYouTubeUpload();
    });
  },

  /**
   * Handle YouTube URL upload
   */
  async handleYouTubeUpload() {
    const youtubeInput = document.getElementById('youtube-url');
    const youtubeButton = document.querySelector('[data-action="upload-youtube"]');
    const url = youtubeInput.value.trim();

    // Validate URL
    const validation = FormValidation.validateYouTubeURL(url);
    if (!validation.valid) {
      FormValidation.showError('youtube-url', validation.error);
      return;
    }

    FormValidation.hideError('youtube-url');

    try {
      // Show loading state
      UI.setButtonLoading(youtubeButton, true);

      // Submit YouTube URL
      const response = await Auth.fetchJSON(`${CONFIG.JOBS_BASE}/youtube`, {
        method: 'POST',
        body: JSON.stringify({ urls: [url] }),
      });

      UI.showMessage('YouTube video queued for transcription!', 'success');

      // Reset form
      youtubeInput.value = '';
      youtubeButton.disabled = true;

      // Refresh job list
      this.loadJobs();

    } catch (error) {
      console.error('YouTube upload failed:', error);
      UI.showMessage(error.message || 'Failed to submit YouTube URL', 'error');
    } finally {
      UI.setButtonLoading(youtubeButton, false);
    }
  },

  /**
   * Load jobs from API
   */
  async loadJobs() {
    try {
      const jobs = await Auth.fetchJSON(`${CONFIG.JOBS_BASE}?limit=20&offset=0`);
      JobPolling.updateJobList(jobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      UI.showMessage('Failed to load jobs', 'error');
    }
  },
};

/* ==========================================================================
   Global Initialization
   ========================================================================== */

// Initialize appropriate page on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPage);
} else {
  initPage();
}

function initPage() {
  // Determine which page we're on and initialize accordingly
  if (window.location.pathname === '/' || window.location.pathname === '/login') {
    window.AuthPage = AuthPage;
  } else if (window.location.pathname === '/dashboard') {
    window.Dashboard = Dashboard;
  }
}
