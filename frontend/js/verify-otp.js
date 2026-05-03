/**
 * OTP Verification Page Logic
 */
(function () {
  const email = TempEmail.get();
  if (!email) { window.location.href = 'signup.html'; return; }

  document.getElementById('email-display').textContent = email;

  const alertEl   = document.getElementById('alert');
  const submitBtn = document.getElementById('submit-btn');
  const resendBtn = document.getElementById('resend-btn');
  const timerRow  = document.getElementById('timer-row');
  const countEl   = document.getElementById('countdown');
  const inputs    = Array.from({ length: 6 }, (_, i) => document.getElementById(`d${i}`));

  // ── OTP input navigation ──────────────────────────────────────────────────
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

  const getOtp = () => inputs.map(i => i.value).join('');

  // ── Countdown ─────────────────────────────────────────────────────────────
  let secs = 300;
  let timerId = null;

  function startTimer() {
    secs = 300;
    timerRow.classList.remove('expired');
    clearInterval(timerId);
    timerId = setInterval(() => {
      secs--;
      const m = String(Math.floor(secs / 60)).padStart(2, '0');
      const s = String(secs % 60).padStart(2, '0');
      countEl.textContent = `${m}:${s}`;
      if (secs <= 0) {
        clearInterval(timerId);
        countEl.textContent = 'Expired';
        timerRow.classList.add('expired');
        resendBtn.disabled = false;
      }
    }, 1000);
  }

  startTimer();

  // ── Submit ─────────────────────────────────────────────────────────────────
  document.getElementById('form').addEventListener('submit', async e => {
    e.preventDefault();
    hideAlert(alertEl);
    const otp = getOtp();
    if (otp.length !== 6) { showAlert(alertEl, 'Please enter all 6 digits of the code.'); return; }

    setLoading(submitBtn, true);
    try {
      const { ok, data } = await apiFetch('/api/auth/verify-otp', {
        method: 'POST',
        body: JSON.stringify({ email, otp }),
      });
      if (ok) {
        clearInterval(timerId);
        TempEmail.clear();
        showAlert(alertEl, data.message, 'success');
        setTimeout(() => { window.location.href = 'login.html'; }, 1800);
      } else {
        showAlert(alertEl, data.message || 'Invalid code. Please try again.');
        inputs.forEach(i => { i.value = ''; i.classList.add('is-error'); });
        setTimeout(() => inputs.forEach(i => i.classList.remove('is-error')), 1500);
        inputs[0].focus();
      }
    } catch {
      showAlert(alertEl, 'Network error. Please check your connection.');
    } finally {
      setLoading(submitBtn, false);
    }
  });

  // ── Resend ─────────────────────────────────────────────────────────────────
  resendBtn.addEventListener('click', async () => {
    hideAlert(alertEl);
    setLoading(resendBtn, true);
    resendBtn.disabled = true;
    try {
      const { ok, data } = await apiFetch('/api/auth/resend-otp', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      showAlert(alertEl, data.message, ok ? 'success' : 'error');
      if (ok) startTimer();
    } catch {
      showAlert(alertEl, 'Network error. Please try again.');
    } finally {
      setLoading(resendBtn, false);
    }
  });
})();
