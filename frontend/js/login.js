/**
 * Login Page Logic
 */
(function () {
  if (Auth.isLoggedIn()) { window.location.href = 'dashboard.html'; return; }

  const alertEl = document.getElementById('alert');
  const btn     = document.getElementById('submit-btn');

  initPasswordToggle('password', 'pw-eye');

  document.getElementById('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert(alertEl);

    const email    = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
      showAlert(alertEl, 'Please enter your email and password.');
      return;
    }

    setLoading(btn, true);
    try {
      const { ok, status, data } = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      if (ok) {
        Auth.setToken(data.token);
        Auth.setUser(data.user);
        showAlert(alertEl, 'Login successful. Redirecting…', 'success');
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 900);
      } else if (status === 403 && data.needsVerification) {
        TempEmail.set(email);
        showAlert(alertEl,
          `${data.message} <a href="verify-otp.html" style="color:inherit;font-weight:700;text-decoration:underline;">Verify now</a>`,
          'info');
      } else {
        showAlert(alertEl, data.message || 'Login failed. Please try again.');
      }
    } catch {
      showAlert(alertEl, 'Network error. Please check your connection.');
    } finally {
      setLoading(btn, false);
    }
  });
})();
