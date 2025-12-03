const API_BASE = 'http://localhost:8000';

const makeSelect = document.getElementById('make');
const modelSelect = document.getElementById('model');
const submodelSelect = document.getElementById('submodel');
const engineSelect = document.getElementById('engine');
const yearSelect = document.getElementById('year');
const form = document.getElementById('partForm');
const statusEl = document.getElementById('status');

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error('Error al cargar datos');
  return res.json();
}

function populateOptions(select, items, placeholder = 'Selecciona') {
  select.innerHTML = `<option value="">${placeholder}</option>`;
  items.forEach((item) => {
    const opt = document.createElement('option');
    opt.value = item.id;
    opt.textContent = item.name || item.engine_name;
    opt.dataset.yearStart = item.year_start;
    opt.dataset.yearEnd = item.year_end;
    select.appendChild(opt);
  });
  select.disabled = items.length === 0;
}

async function loadMakes() {
  const makes = await fetchJSON(`${API_BASE}/vehicles/makes`);
  populateOptions(makeSelect, makes, 'Selecciona marca');
}

makeSelect.addEventListener('change', async () => {
  const makeId = makeSelect.value;
  modelSelect.disabled = true;
  submodelSelect.disabled = true;
  engineSelect.disabled = true;
  yearSelect.disabled = true;
  populateOptions(modelSelect, [], 'Selecciona modelo');
  populateOptions(submodelSelect, [], 'Selecciona submodelo');
  populateOptions(engineSelect, [], 'Selecciona motor');
  populateOptions(yearSelect, [], 'Selecciona año');
  if (!makeId) return;
  const models = await fetchJSON(`${API_BASE}/vehicles/models/${makeId}`);
  populateOptions(modelSelect, models, 'Selecciona modelo');
});

modelSelect.addEventListener('change', async () => {
  const modelId = modelSelect.value;
  submodelSelect.disabled = true;
  engineSelect.disabled = true;
  yearSelect.disabled = true;
  populateOptions(submodelSelect, [], 'Selecciona submodelo');
  populateOptions(engineSelect, [], 'Selecciona motor');
  populateOptions(yearSelect, [], 'Selecciona año');
  if (!modelId) return;
  const submodels = await fetchJSON(`${API_BASE}/vehicles/submodels/${modelId}`);
  populateOptions(submodelSelect, submodels, 'Selecciona submodelo');
});

submodelSelect.addEventListener('change', async () => {
  const submodelId = submodelSelect.value;
  engineSelect.disabled = true;
  yearSelect.disabled = true;
  populateOptions(engineSelect, [], 'Selecciona motor');
  populateOptions(yearSelect, [], 'Selecciona año');
  if (!submodelId) return;
  const engines = await fetchJSON(`${API_BASE}/vehicles/engines/${submodelId}`);
  populateOptions(engineSelect, engines, 'Selecciona motor');
});

engineSelect.addEventListener('change', () => {
  const option = engineSelect.options[engineSelect.selectedIndex];
  const yearStart = parseInt(option.dataset.yearStart || '0', 10);
  const yearEnd = parseInt(option.dataset.yearEnd || '0', 10);
  const years = [];
  for (let y = yearStart; y <= yearEnd; y += 1) {
    years.push({ id: y, name: y });
  }
  populateOptions(yearSelect, years, 'Selecciona año');
  yearSelect.disabled = years.length === 0;
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = 'Enviando...';
  const payload = {
    make_id: makeSelect.value ? parseInt(makeSelect.value, 10) : null,
    model_id: modelSelect.value ? parseInt(modelSelect.value, 10) : null,
    submodel_id: submodelSelect.value ? parseInt(submodelSelect.value, 10) : null,
    engine_id: engineSelect.value ? parseInt(engineSelect.value, 10) : null,
    year: yearSelect.value ? parseInt(yearSelect.value, 10) : null,
    oem: document.getElementById('oem').value || null,
    vin: document.getElementById('vin').value || null,
    phone: document.getElementById('phone').value,
    part_name: null,
    notes: document.getElementById('notes').value || null,
  };

  try {
    const res = await fetch(`${API_BASE}/part-request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Error al enviar solicitud');
    const data = await res.json();
    statusEl.textContent = `Solicitud enviada. ID: ${data.request_id}`;
    form.reset();
    populateOptions(modelSelect, [], 'Selecciona modelo');
    populateOptions(submodelSelect, [], 'Selecciona submodelo');
    populateOptions(engineSelect, [], 'Selecciona motor');
    populateOptions(yearSelect, [], 'Selecciona año');
    modelSelect.disabled = true;
    submodelSelect.disabled = true;
    engineSelect.disabled = true;
    yearSelect.disabled = true;
  } catch (err) {
    statusEl.textContent = err.message;
  }
});

loadMakes();
