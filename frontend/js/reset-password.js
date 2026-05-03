/**
 * Reset Password Page Logic
 */
(function () {
  const resetToken = sessionStorage.getItem('nd_reset_token');
  if (!resetToken) { window.location.href = 'forgot-password.html'; return; }

  const alertEl   = document.getElementById('alert');
  const btn       = document.getElementById('submit-btn');
  const pwInput   = document.getElementById('password');
  const swrap     = document.getElementById('strength-wrap');
  const fillEl    = document.getElementById('strength-fill');
  const hintsWrap = document.getElementById('strength-hints');

  initPasswordToggle('password', 'pw-eye');
  initPasswordToggle('confirm',  'cf-eye');

  pwInput.addEventListener('input', () => {
    swrap.classList.toggle('show', pwInput.value.length > 0);
    updatePasswordStrength(pwInput.value, fillEl, hintsWrap);
  });

  document.getElementById('form').addEventListener('submit', async e => {
    e.preventDefault();
    hideAlert(alertEl);

    const password = pwInput.value;
    const confirm  = document.getElementById('confirm').value;

    const strong = updatePasswordStrength(password, fillEl, hintsWrap);
    if (!strong)              { showAlert(alertEl, 'Your password does not meet all requirements.'); return; }
    if (password !== confirm) { showAlert(alertEl, 'Passwords do not match.'); return; }

    setLoading(btn, true);
    try {
      const { ok, data } = await apiFetch('/api/password/reset', {
        method: 'POST',
        body: JSON.stringify({ resetToken, password }),
      });
      if (ok) {
        sessionStorage.removeItem('nd_reset_token');
        TempEmail.clear();
        showAlert(alertEl, data.message, 'success');
        setTimeout(() => { window.location.href = 'login.html'; }, 1800);
      } else {
        showAlert(alertEl, data.message || 'Failed to reset password.');
        if (data.message && data.message.includes('expired')) {
          setTimeout(() => { window.location.href = 'forgot-password.html'; }, 2500);
        }
      }
    } catch {
      showAlert(alertEl, 'Network error. Please try again.');
    } finally {
      setLoading(btn, false);
    }
  });
})();
