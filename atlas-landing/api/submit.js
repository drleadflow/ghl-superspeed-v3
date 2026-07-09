const GHL_TOKEN = process.env.GHL_PIT_TOKEN;
const GHL_LOCATION_ID = process.env.GHL_LOCATION_ID;
const GHL_API = 'https://services.leadconnectorhq.com';
const TAG = 'atlas';
const SOURCE = 'atlas-landing-page';

function normalizePhone(raw) {
  const digits = String(raw || '').replace(/\D/g, '');
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return null;
}

export default async function handler(req, res) {
  // CORS — form is also embedded on the GHL funnel domain
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') {
    return res.status(204).end();
  }
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  if (!GHL_TOKEN || !GHL_LOCATION_ID) {
    console.error('Missing GHL_PIT_TOKEN or GHL_LOCATION_ID env vars');
    return res.status(500).json({ error: 'Server not configured' });
  }

  const { firstName, phone } = req.body || {};
  const name = String(firstName || '').trim().slice(0, 60);
  const normalizedPhone = normalizePhone(phone);

  if (!name || name.length < 2) {
    return res.status(400).json({ error: 'Please enter your first name.' });
  }
  if (!normalizedPhone) {
    return res.status(400).json({ error: 'Please enter a valid US phone number.' });
  }

  try {
    const ghlRes = await fetch(`${GHL_API}/contacts/upsert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${GHL_TOKEN}`,
        Version: '2021-07-28',
      },
      body: JSON.stringify({
        locationId: GHL_LOCATION_ID,
        firstName: name,
        phone: normalizedPhone,
        tags: [TAG],
        source: SOURCE,
      }),
    });

    if (!ghlRes.ok) {
      const text = await ghlRes.text();
      console.error(`GHL upsert failed (${ghlRes.status}): ${text}`);
      return res.status(502).json({ error: 'Could not save your info. Please try again.' });
    }

    const data = await ghlRes.json();
    const contactId = data?.contact?.id;

    // Upsert replaces tags on existing contacts in some cases — enforce the tag explicitly.
    if (contactId) {
      const tagRes = await fetch(`${GHL_API}/contacts/${contactId}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${GHL_TOKEN}`,
          Version: '2021-07-28',
        },
        body: JSON.stringify({ tags: [TAG] }),
      });
      if (!tagRes.ok) {
        console.error(`GHL add-tag failed (${tagRes.status}): ${await tagRes.text()}`);
      }
    }

    return res.status(200).json({ success: true });
  } catch (err) {
    console.error(`Submit error: ${err.message}`);
    return res.status(500).json({ error: 'Something went wrong. Please try again.' });
  }
}
