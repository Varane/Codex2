let carsData = {};

async function fetchJson(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error('Failed to load data');
    }
    return response.json();
}

function renderResult(data) {
    const resultDiv = document.getElementById('result');
    if (data.error) {
        resultDiv.innerHTML = `<p style="color:red;">${data.error}</p>`;
        return;
    }

    const priceText = data.final_price !== undefined ? `Price: ${data.final_price} €` : 'Price unavailable';
    const imageHtml = data.photo ? `<img src="${data.photo}" alt="Part photo">` : '<p>No image available</p>';
    resultDiv.innerHTML = `${imageHtml}<h2>${priceText}</h2>`;
}

async function searchPart() {
    const input = document.getElementById('oem');
    const query = input.value.trim();
    if (!query) {
        renderResult({ error: 'Please enter a search term.' });
        return;
    }

    const resultDiv = document.getElementById('result');
    resultDiv.innerHTML = '<p>Loading...</p>';

    try {
        const data = await fetchJson(`/api/part?q=${encodeURIComponent(query)}`);
        renderResult(data);
    } catch (error) {
        renderResult({ error: 'Failed to fetch offers.' });
    }
}

function populateSelect(select, options) {
    select.innerHTML = '';
    options.forEach((opt) => {
        const optionEl = document.createElement('option');
        optionEl.value = opt;
        optionEl.textContent = opt;
        select.appendChild(optionEl);
    });
}

function getDetailsForModel(car, model) {
    const systems = car && model && carsData[car] && carsData[car][model] ? carsData[car][model] : {};
    const detailLists = Object.values(systems);
    return detailLists.flat();
}

async function loadCars() {
    try {
        carsData = await fetchJson('/cars.json');
        const carSelect = document.getElementById('car');
        populateSelect(carSelect, Object.keys(carsData));
        loadModels();
    } catch (error) {
        console.error('Unable to load cars.json', error);
    }
}

function loadModels() {
    const carSelect = document.getElementById('car');
    const modelSelect = document.getElementById('model');
    const detailSelect = document.getElementById('detail');

    const car = carSelect.value;
    const models = car && carsData[car] ? Object.keys(carsData[car]) : [];
    populateSelect(modelSelect, models);

    const selectedModel = modelSelect.value;
    const details = getDetailsForModel(car, selectedModel);
    populateSelect(detailSelect, details);
}

function loadDetails() {
    const car = document.getElementById('car').value;
    const model = document.getElementById('model').value;
    const detailSelect = document.getElementById('detail');
    const details = getDetailsForModel(car, model);
    populateSelect(detailSelect, details);
}

async function searchByDetail() {
    const car = document.getElementById('car').value;
    const model = document.getElementById('model').value;
    const detail = document.getElementById('detail').value;

    if (!car || !model || !detail) {
        renderResult({ error: 'Please select car, model, and detail.' });
        return;
    }

    const query = `${car} ${model} ${detail}`;
    document.getElementById('oem').value = query;
    await searchPart();
}

window.addEventListener('DOMContentLoaded', loadCars);
