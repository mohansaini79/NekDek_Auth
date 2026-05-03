/**
 * Dashboard Page Logic
 */
(function () {
  if (!Auth.isLoggedIn()) { window.location.href = 'login.html'; return; }

  const dashAlert = document.getElementById('dash-alert');
  let currentUser = null;

  // ── Load profile ──────────────────────────────────────────────────────────
  async function loadProfile() {
    try {
      const { ok, status, data } = await apiFetch('/api/user/me');
      if (!ok) {
        if (status === 401) { Auth.logout(); return; }
        showAlert(dashAlert, data.message || 'Failed to load profile.', 'error');
        return;
      }
      currentUser = data.user;
      render(currentUser);
    } catch {
      showAlert(dashAlert, 'Network error. Could not load profile.', 'error');
    }
  }

  function render(user) {
    const initial = (user.name || user.email || 'U')[0].toUpperCase();

    // Topbar
    document.getElementById('topbar-name').textContent = user.name || user.email;
    document.getElementById('topbar-avatar').textContent = initial;

    // Welcome
    const firstName = (user.name || '').split(' ')[0] || 'there';
    document.getElementById('welcome-heading').textContent = `Welcome back, ${firstName}`;

    // Stats
    document.getElementById('stat-verified').textContent = user.isVerified ? 'Verified' : 'Unverified';
    document.getElementById('stat-joined').textContent = new Date(user.createdAt).toLocaleDateString('en-US', {
      year: 'numeric', month: 'short', day: 'numeric',
    });
    document.getElementById('stat-email').textContent = user.email;

    // Profile card
    document.getElementById('profile-avatar').textContent = initial;
    document.getElementById('profile-name').textContent   = user.name;
    document.getElementById('profile-email').textContent  = user.email;
    document.getElementById('edit-name').value            = user.name;

    const badge = document.getElementById('profile-badge');
    if (user.isVerified) {
      badge.className = 'badge-verified';
      badge.innerHTML = '<i class="fa-solid fa-circle-check" style="font-size:10px;"></i> Verified';
    } else {
      badge.className = 'badge-unverified';
      badge.innerHTML = '<i class="fa-solid fa-circle-xmark" style="font-size:10px;"></i> Unverified';
    }
  }

  // ── Save profile ──────────────────────────────────────────────────────────
  document.getElementById('save-btn').addEventListener('click', async () => {
    const btn     = document.getElementById('save-btn');
    const newName = document.getElementById('edit-name').value.trim();
    hideAlert(dashAlert);

    if (!newName) { showAlert(dashAlert, 'Display name cannot be empty.', 'error'); return; }

    setLoading(btn, true);
    try {
      const { ok, data } = await apiFetch('/api/user/profile', {
        method: 'PUT',
        body: JSON.stringify({ name: newName }),
      });
      if (ok) {
        currentUser = data.user;
        Auth.setUser(data.user);
        render(data.user);
        showAlert(dashAlert, 'Profile updated successfully.', 'success');
      } else {
        showAlert(dashAlert, data.message || 'Update failed.');
      }
    } catch {
      showAlert(dashAlert, 'Network error. Please try again.');
    } finally {
      setLoading(btn, false);
    }
  });

  // ── Logout ────────────────────────────────────────────────────────────────
  document.getElementById('logout-btn').addEventListener('click', () => Auth.logout());

  // ── Delete Modal ──────────────────────────────────────────────────────────
  const modal      = document.getElementById('delete-modal');
  const modalAlert = document.getElementById('modal-alert');

  document.getElementById('delete-btn').addEventListener('click', () => {
    document.getElementById('delete-pw').value = '';
    hideAlert(modalAlert);
    modal.classList.add('open');
  });

  document.getElementById('cancel-btn').addEventListener('click', () => modal.classList.remove('open'));

  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('open'); });

  initPasswordToggle('delete-pw', 'del-pw-eye');

  document.getElementById('confirm-delete-btn').addEventListener('click', async () => {
    const btn      = document.getElementById('confirm-delete-btn');
    const password = document.getElementById('delete-pw').value;
    hideAlert(modalAlert);

    if (!password) { showAlert(modalAlert, 'Please enter your password.', 'error'); return; }

    setLoading(btn, true);
    try {
      const { ok, data } = await apiFetch('/api/user/account', {
        method: 'DELETE',
        body: JSON.stringify({ password }),
      });
      if (ok) {
        showAlert(modalAlert, 'Account deleted. Signing out…', 'success');
        setTimeout(() => Auth.logout(), 1500);
      } else {
        showAlert(modalAlert, data.message || 'Deletion failed.', 'error');
      }
    } catch {
      showAlert(modalAlert, 'Network error. Please try again.', 'error');
    } finally {
      setLoading(btn, false);
    }
  });

  // ── Init ──────────────────────────────────────────────────────────────────
  loadProfile();
})();
