/**
 * NekDek Auth – Shared JavaScript Utilities
 */

// ── API Base URL ──────────────────────────────────────────────────────────────
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:5000'
  : 'https://nekdek-auth.onrender.com';  // ← replace after deployment

// ── Token / User helpers ──────────────────────────────────────────────────────
const Auth = {
  setToken(token)  { localStorage.setItem('nd_token', token); },
  getToken()       { return localStorage.getItem('nd_token'); },
  removeToken()    { localStorage.removeItem('nd_token'); },
  setUser(user)    { localStorage.setItem('nd_user', JSON.stringify(user)); },
  getUser()        { const u = localStorage.getItem('nd_user'); return u ? JSON.parse(u) : null; },
  removeUser()     { localStorage.removeItem('nd_user'); },
  isLoggedIn()     { return !!this.getToken(); },
  logout() {
    this.removeToken();
    this.removeUser();
    window.location.href = 'login.html';
  },
};

// ── API fetch wrapper ─────────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res  = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

// ── Alert helpers ─────────────────────────────────────────────────────────────
const ALERT_ICONS = {
  success: 'fa-solid fa-circle-check',
  error:   'fa-solid fa-circle-exclamation',
  info:    'fa-solid fa-circle-info',
};

function showAlert(el, message, type = 'error') {
  if (!el) return;
  el.className = `alert alert-${type} show`;
  el.innerHTML = `<i class="${ALERT_ICONS[type] || ALERT_ICONS.error}"></i><span>${message}</span>`;
}

function hideAlert(el) {
  if (!el) { return; }
  el.className = 'alert';
}

// ── Button loading state ──────────────────────────────────────────────────────
function setLoading(btn, state) {
  if (!btn) return;
  btn.disabled = state;
  btn.classList.toggle('loading', state);
}

// ── Password strength ─────────────────────────────────────────────────────────
const PW_RULES = [
  { id: 'h-len',     test: p => p.length >= 8,         label: '8+ characters' },
  { id: 'h-upper',   test: p => /[A-Z]/.test(p),       label: 'Uppercase letter' },
  { id: 'h-lower',   test: p => /[a-z]/.test(p),       label: 'Lowercase letter' },
  { id: 'h-number',  test: p => /\d/.test(p),           label: 'Number' },
  { id: 'h-special', test: p => /[@$!%*?&]/.test(p),   label: 'Special char (@$!%*?&)' },
];

function updatePasswordStrength(password, fillEl, hintsWrap) {
  const passed = PW_RULES.filter(r => r.test(password)).length;
  const pct    = (passed / PW_RULES.length) * 100;

  if (fillEl) {
    fillEl.style.width = `${pct}%`;
    const colors = ['#ef4444', '#f59e0b', '#f59e0b', '#06b6d4', '#10b981'];
    fillEl.style.background = colors[passed - 1] || '#ef4444';
    if (passed === 0) fillEl.style.width = '0%';
  }

  if (hintsWrap) {
    PW_RULES.forEach(rule => {
      const li = hintsWrap.querySelector(`#${rule.id}`);
      if (li) li.classList.toggle('ok', rule.test(password));
    });
  }

  return passed === PW_RULES.length;
}

// ── Toggle password visibility ────────────────────────────────────────────────
function initPasswordToggle(inputId, btnId) {
  const input = document.getElementById(inputId);
  const btn   = document.getElementById(btnId);
  if (!input || !btn) return;
  btn.addEventListener('click', () => {
    const isText = input.type === 'text';
    input.type   = isText ? 'password' : 'text';
    const icon   = btn.querySelector('i');
    if (icon) {
      icon.className = isText ? 'fa-regular fa-eye' : 'fa-regular fa-eye-slash';
    }
  });
}

// ── Session helpers ───────────────────────────────────────────────────────────
const TempEmail = {
  set(e)  { sessionStorage.setItem('nd_email', e); },
  get()   { return sessionStorage.getItem('nd_email') || ''; },
  clear() { sessionStorage.removeItem('nd_email'); },
};
