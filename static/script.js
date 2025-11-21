// Navigation
function showSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('header, section').forEach(el => {
        if (el.id !== 'hero' && el.id !== 'upload' && el.id !== 'dashboard') return; // Keep other structural elements if any
        el.classList.add('hidden');
    });

    // Show target section
    const target = document.getElementById(sectionId);
    if (target) {
        target.classList.remove('hidden');
    }

    // Special case for Hero which is a header tag
    if (sectionId === 'hero') {
        document.getElementById('hero').classList.remove('hidden');
        document.getElementById('upload').classList.add('hidden');
        document.getElementById('dashboard').classList.add('hidden');
    }
}

// File Upload Logic
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const processBtn = document.getElementById('processBtn');

// Click to browse
if (dropZone) {
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFiles(e.dataTransfer.files);
    });
}

if (fileInput) {
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        fileList.innerHTML = `
            <div style="border: 2px solid #1E1E1E; padding: 10px; background: #39FF14; display: flex; justify-content: space-between; align-items: center; box-shadow: 3px 3px 0px #1E1E1E;">
                <span><strong>${file.name}</strong> (${(file.size / 1024).toFixed(2)} KB)</span>
                <span>READY</span>
            </div>
        `;
        processBtn.disabled = false;
    }
}

async function processData() {
    const btn = document.getElementById('processBtn');
    const originalText = btn.innerText;
    const fileInput = document.getElementById('fileInput');

    if (fileInput.files.length === 0) return;

    btn.innerText = "PROCESSING...";
    btn.disabled = true;

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }

        const data = await response.json();
        renderDashboard(data);
        showSection('dashboard');

    } catch (error) {
        alert("Error processing file: " + error.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

function renderDashboard(data) {
    // Update Stats
    document.getElementById('statRows').innerText = data.rows.toLocaleString();
    document.getElementById('statScore').innerText = data.clean_score + "%";
    document.getElementById('statMissing').innerText = data.missing_values;

    // Render Charts
    const chartsContainer = document.getElementById('chartsContainer');
    chartsContainer.innerHTML = ''; // Clear previous

    const sections = {
        'univariate': 'Univariate Analysis',
        'bivariate': 'Bivariate Analysis',
        'multivariate': 'Multivariate Analysis'
    };

    for (const [key, label] of Object.entries(sections)) {
        if (data.analysis_sections[key] && data.analysis_sections[key].length > 0) {
            // Section Header
            const header = document.createElement('h2');
            header.innerText = label;
            header.style.marginTop = '40px';
            header.style.marginBottom = '20px';
            header.style.borderBottom = '3px solid #39FF14';
            header.style.display = 'inline-block';
            chartsContainer.appendChild(header);

            // Grid Container for this section
            const grid = document.createElement('div');
            grid.className = 'dashboard-grid';
            chartsContainer.appendChild(grid);

            data.analysis_sections[key].forEach((viz, index) => {
                const card = document.createElement('div');
                card.className = 'card-neo';

                // Make complex charts wider
                if (viz.type === 'table' || viz.type === 'heatmap' || viz.type === 'line') {
                    card.classList.add('span-2');
                }

                const title = document.createElement('h3');
                title.innerText = viz.title;
                card.appendChild(title);

                // Insight Text
                if (viz.description) {
                    const desc = document.createElement('p');
                    desc.innerHTML = viz.description; // Allow HTML for bolding
                    desc.className = 'insight-text';
                    card.appendChild(desc);
                }

                const chartDiv = document.createElement('div');
                chartDiv.id = `chart-${key}-${index}`;
                chartDiv.style.height = '400px';
                card.appendChild(chartDiv);

                grid.appendChild(card);

                // Render Plotly Chart
                const figure = JSON.parse(viz.json);
                Plotly.newPlot(`chart-${key}-${index}`, figure.data, figure.layout, { responsive: true });
            });
        }
    }

    // Render Preview Table
    const tableHead = document.querySelector('#previewTable thead');
    const tableBody = document.querySelector('#previewTable tbody');

    tableHead.innerHTML = '';
    tableBody.innerHTML = '';

    if (data.preview && data.preview.length > 0) {
        // Headers
        const headerRow = document.createElement('tr');
        headerRow.style.background = 'var(--color-dark)';
        headerRow.style.color = 'var(--color-white)';

        Object.keys(data.preview[0]).forEach(key => {
            const th = document.createElement('th');
            th.style.padding = '10px';
            th.style.textAlign = 'left';
            th.innerText = key;
            headerRow.appendChild(th);
        });
        tableHead.appendChild(headerRow);

        // Rows
        data.preview.forEach((row, i) => {
            const tr = document.createElement('tr');
            tr.style.borderBottom = '1px solid #ccc';
            if (i % 2 !== 0) tr.style.background = 'var(--color-grey-light)';

            Object.values(row).forEach(val => {
                const td = document.createElement('td');
                td.style.padding = '10px';
                td.innerText = val;
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }
}
