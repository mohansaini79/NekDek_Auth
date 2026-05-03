/**
 * Signup Page Logic
 */
(function () {
  if (Auth.isLoggedIn()) { window.location.href = 'dashboard.html'; return; }

  const alertEl   = document.getElementById('alert');
  const btn       = document.getElementById('submit-btn');
  const pwInput   = document.getElementById('password');
  const fillEl    = document.getElementById('strength-fill');
  const hintsWrap = document.getElementById('strength-hints');
  const swrap     = document.getElementById('strength-wrap');

  initPasswordToggle('password', 'pw-eye');
  initPasswordToggle('confirm',  'cf-eye');

  pwInput.addEventListener('input', () => {
    swrap.classList.toggle('show', pwInput.value.length > 0);
    updatePasswordStrength(pwInput.value, fillEl, hintsWrap);
  });

  document.getElementById('form').addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert(alertEl);

    const name     = document.getElementById('name').value.trim();
    const email    = document.getElementById('email').value.trim();
    const password = pwInput.value;
    const confirm  = document.getElementById('confirm').value;

    if (!name)  { showAlert(alertEl, 'Please enter your full name.'); return; }
    if (!email) { showAlert(alertEl, 'Please enter your email address.'); return; }

    const strong = updatePasswordStrength(password, fillEl, hintsWrap);
    if (!strong)              { showAlert(alertEl, 'Your password does not meet all requirements.'); return; }
    if (password !== confirm) { showAlert(alertEl, 'Passwords do not match.'); return; }

    setLoading(btn, true);
    try {
      const { ok, data } = await apiFetch('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ name, email, password }),
      });
      if (ok) {
        TempEmail.set(email);
        showAlert(alertEl, data.message, 'success');
        setTimeout(() => { window.location.href = 'verify-otp.html'; }, 1400);
      } else {
        showAlert(alertEl, data.message || 'Signup failed. Please try again.');
      }
    } catch {
      showAlert(alertEl, 'Network error. Please check your connection.');
    } finally {
      setLoading(btn, false);
    }
  });
})();
