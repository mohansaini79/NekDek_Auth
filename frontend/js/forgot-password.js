/**
 * Forgot Password Page Logic
 */
(function () {
  let emailValue = '';

  // ── Step 1: Send OTP ──────────────────────────────────────────────────────
  document.getElementById('form-email').addEventListener('submit', async e => {
    e.preventDefault();
    const alertEl = document.getElementById('alert-email');
    const btn     = document.getElementById('send-btn');
    hideAlert(alertEl);

    emailValue = document.getElementById('email').value.trim().toLowerCase();
    if (!emailValue) { showAlert(alertEl, 'Please enter your email address.'); return; }

    setLoading(btn, true);
    try {
      const { ok, data } = await apiFetch('/api/password/forgot', {
        method: 'POST',
        body: JSON.stringify({ email: emailValue }),
      });
      if (ok) {
        TempEmail.set(emailValue);
        document.getElementById('otp-email-display').textContent = emailValue;
        document.getElementById('step-email').style.display = 'none';
        document.getElementById('step-otp').style.display   = 'block';
        startTimer();
      } else {
        showAlert(alertEl, data.message || 'Something went wrong. Please try again.');
      }
    } catch {
      showAlert(alertEl, 'Network error. Please check your connection.');
    } finally {
      setLoading(btn, false);
    }
  });

  // ── OTP inputs ────────────────────────────────────────────────────────────
  const inputs = Array.from({ length: 6 }, (_, i) => document.getElementById(`d${i}`));
  inputs.forEach((inp, idx) => {
    inp.addEventListener('input', () => {
      inp.value = inp.value.replace(/\D/g, '');
      if (inp.value && idx < 5) inputs[idx + 1].focus();
    });
    inp.addEventListener('keydown', e => {
      if (e.key === 'Backspace' && !inp.value && idx > 0) inputs[idx - 1].focus();
    });
    inp.addEventListener('paste', e => {
      e.preventDefault();
      const digits = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
      digits.split('').slice(0, 6).forEach((ch, i) => { if (inputs[i]) inputs[i].value = ch; });
      inputs[Math.min(digits.length, 5)].focus();
    });
  });

  // ── Step 2: Verify OTP ────────────────────────────────────────────────────
  document.getElementById('form-otp').addEventListener('submit', async e => {
    e.preventDefault();
    const alertEl = document.getElementById('alert-otp');
    const btn     = document.getElementById('verify-btn');
    hideAlert(alertEl);

    const otp = inputs.map(i => i.value).join('');
    if (otp.length !== 6) { showAlert(alertEl, 'Please enter all 6 digits.'); return; }

    setLoading(btn, true);
    try {
      const { ok, data } = await apiFetch('/api/password/verify', {
        method: 'POST',
        body: JSON.stringify({ email: TempEmail.get(), otp }),
      });
      if (ok) {
        sessionStorage.setItem('nd_reset_token', data.resetToken);
        showAlert(alertEl, 'Code verified. Redirecting…', 'success');
        setTimeout(() => { window.location.href = 'reset-password.html'; }, 1200);
      } else {
        showAlert(alertEl, data.message || 'Invalid code. Please try again.');
        inputs.forEach(i => { i.value = ''; i.classList.add('is-error'); });
        setTimeout(() => inputs.forEach(i => i.classList.remove('is-error')), 1500);
        inputs[0].focus();
      }
    } catch {
      showAlert(alertEl, 'Network error. Please try again.');
    } finally {
      setLoading(btn, false);
    }
  });

  // ── Countdown ─────────────────────────────────────────────────────────────
  function startTimer() {
    let secs = 300;
    const timerRow = document.getElementById('timer-row');
    const countEl  = document.getElementById('countdown');
    const id = setInterval(() => {
      secs--;
      const m = String(Math.floor(secs / 60)).padStart(2, '0');
      const s = String(secs % 60).padStart(2, '0');
      countEl.textContent = `${m}:${s}`;
      if (secs <= 0) {
        clearInterval(id);
        countEl.textContent = 'Expired';
        timerRow.classList.add('expired');
      }
    }, 1000);
  }
})();
