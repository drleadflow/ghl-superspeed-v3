// ── Config ──────────────────────────────────────────────────────────────
// Posts straight to the GHL inbound-webhook workflow (creates contact + tags).
const WEBHOOK_URL = 'https://services.leadconnectorhq.com/hooks/jiR5qR3g4OrMRx6BmpF2/webhook-trigger/84bb021f-3cc7-4db9-bd43-46a640396d91';
const NEXT_URL = 'https://tvaa.doctorleadflow.com/botoxoffer';
const MEMBER_RATE = 9;
const TYPICAL_RATE = 14;

// Unit ranges per treatment area (totals, both sides where applicable)
const AREAS = [
  { id: 'frown', name: 'Frown Lines (11s)', min: 15, max: 25 },
  { id: 'forehead', name: 'Forehead Lines', min: 10, max: 20 },
  { id: 'crows', name: "Crow's Feet", min: 10, max: 24 },
  { id: 'brow', name: 'Brow Lift', min: 4, max: 10 },
  { id: 'bunny', name: 'Bunny Lines', min: 5, max: 10 },
  { id: 'gummy', name: 'Gummy Smile', min: 4, max: 8 },
  { id: 'lip', name: 'Lip Flip', min: 4, max: 6 },
  { id: 'chin', name: 'Chin Dimpling', min: 2, max: 6 },
  { id: 'mouth', name: 'Mouth Corners', min: 6, max: 12 },
  { id: 'masseter', name: 'Jaw Slimming', min: 40, max: 80 },
  { id: 'neck', name: 'Neck Bands', min: 60, max: 80 },
  { id: 'trap', name: 'Trapezius (Traptox)', min: 100, max: 200 },
];

// ── Calculator ──────────────────────────────────────────────────────────
const grid = document.getElementById('areaGrid');
AREAS.forEach((a) => {
  const div = document.createElement('div');
  div.className = 'area';
  div.innerHTML = `
    <input type="checkbox" id="a-${a.id}" data-min="${a.min}" data-max="${a.max}">
    <label for="a-${a.id}">
      <img src="/areas/${a.id}.png" alt="${a.name}" loading="lazy" width="44" height="44">
      <em>${a.name}<span>${a.min}–${a.max} units</span></em>
    </label>`;
  grid.appendChild(div);
});

const resultBox = document.getElementById('calcResult');
grid.addEventListener('change', () => {
  const checked = [...grid.querySelectorAll('input:checked')];
  if (!checked.length) {
    resultBox.style.display = 'none';
    return;
  }
  const min = checked.reduce((s, el) => s + Number(el.dataset.min), 0);
  const max = checked.reduce((s, el) => s + Number(el.dataset.max), 0);
  const mid = Math.round((min + max) / 2);
  const fmt = (n) => '$' + n.toLocaleString('en-US');

  document.getElementById('calcUnits').textContent =
    `Estimated ${min}–${max} units for your ${checked.length} area${checked.length > 1 ? 's' : ''}`;
  document.getElementById('calcMember').textContent = fmt(mid * MEMBER_RATE);
  document.getElementById('calcTypical').textContent = fmt(mid * TYPICAL_RATE);
  document.getElementById('calcSave').textContent =
    `You save ~${fmt(mid * (TYPICAL_RATE - MEMBER_RATE))} per visit`;
  resultBox.style.display = 'block';
});

// ── Sticky CTA bar ──────────────────────────────────────────────────────
const bar = document.getElementById('stickybar');
const hero = document.getElementById('formCard');
window.addEventListener('scroll', () => {
  const past = hero.getBoundingClientRect().bottom < 0;
  bar.classList.toggle('show', past);
}, { passive: true });

// ── Qualify form ────────────────────────────────────────────────────────
const form = document.getElementById('qualifyForm');
const btn = document.getElementById('submitBtn');
const errorBox = document.getElementById('errorBox');

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.style.display = 'block';
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorBox.style.display = 'none';

  const firstName = document.getElementById('firstName').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const digits = phone.replace(/\D/g, '');

  if (firstName.length < 2) return showError('Please enter your first name.');
  if (digits.length !== 10 && !(digits.length === 11 && digits.startsWith('1'))) {
    return showError('Please enter a valid US mobile number.');
  }

  btn.disabled = true;
  btn.textContent = 'Checking…';

  const normalized = digits.length === 11 ? `+${digits}` : `+1${digits}`;

  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        first_name: firstName,
        phone: normalized,
        source: 'atlas-landing-page',
        tag: 'atlas',
        offer: 'wrinkle-reset-founding-membership',
      }),
    });
    if (!res.ok) throw new Error('Something went wrong. Please try again.');

    form.style.display = 'none';
    document.getElementById('successBox').style.display = 'block';
    setTimeout(() => { window.location.href = NEXT_URL; }, 1400);
  } catch (err) {
    showError(err.message);
    btn.disabled = false;
    btn.textContent = 'See If I Qualify →';
  }
});
