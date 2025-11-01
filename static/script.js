let filteredData = [];

// --- FBA Fee calculation
function calculateFBAFee(weight) {
    if (weight <= 0.5) return 2.50;
    if (weight <= 1) return 3.00;
    if (weight <= 2) return 3.50;
    if (weight <= 5) return 4.50;
    return 5.50 + (weight - 5) * 0.5;
}

function extractWeight(dimensions) {
    if (!dimensions) return 0.5;
    const match = dimensions.match(/(\d+\.?\d*)\s*kg/i);
    return match ? parseFloat(match[1]) : 0.5;
}

// --- Analyze products
function analyzeProducts() {
    const shippingCost = parseFloat(document.getElementById('shippingCost').value);
    const referralFeePercent = parseFloat(document.getElementById('referralFee').value);
    const minProfit = parseFloat(document.getElementById('minProfit').value);
    const maxRank = parseFloat(document.getElementById('maxRank').value);

    productsData.forEach(product => {
        const eurolotusPrice = parseFloat(product.eurolotus_price) || 0;
        const amazonPrice = parseFloat(product.amazon_price) || 0;
        const weight = extractWeight(product.dimensions_cm);
        const fbaFee = calculateFBAFee(weight);
        const amazonFee = amazonPrice * (referralFeePercent / 100);
        const totalCost = eurolotusPrice + shippingCost;
        const netProfit = amazonPrice - totalCost - amazonFee - fbaFee;
        const profitMargin = amazonPrice ? (netProfit / amazonPrice) * 100 : 0;

        const sellers = parseInt(product.amazon_sellers) || 0;
        const fba = parseInt(product.fba_sellers) || 0;
        const fbaPercent = sellers ? (fba / sellers) * 100 : 0;
        let competition = 'Low';
        if (fbaPercent > 70 || sellers > 10) competition = 'High';
        else if (fbaPercent > 40 || sellers > 5) competition = 'Medium';

        let recommendation = '⚡ Consider';
        const rank = parseInt(product.amazon_rank) || 999999;
        if (profitMargin >= minProfit && rank <= maxRank && competition === 'Low') recommendation = '✅ Highly Recommended';
        else if (profitMargin >= minProfit && rank <= maxRank) recommendation = '👍 Recommended';
        else if (profitMargin < 15) recommendation = '❌ Low Profit';
        else if (rank > maxRank) recommendation = '⚠️ Slow Sales';
        else if (competition === 'High') recommendation = '⚠️ High Competition';

        product.analysis = {
            totalCost: totalCost.toFixed(2),
            amazonFee: amazonFee.toFixed(2),
            fbaFee: fbaFee.toFixed(2),
            netProfit: netProfit.toFixed(2),
            profitMargin: profitMargin.toFixed(1),
            roi: totalCost ? ((netProfit / totalCost) * 100).toFixed(1) : 0,
            competition,
            recommendation
        };
    });

    filteredData = [...productsData];
    displayResults();
}

// --- Display results
function displayResults() {
    const table = document.getElementById('resultsTable');
    let html = `
        <thead class="table-primary">
            <tr>
                <th>Product</th>
                <th>EuroLotus Price</th>
                <th>Amazon Price</th>
                <th>Total Cost</th>
                <th>Fees</th>
                <th>Net Profit</th>
                <th>Margin %</th>
                <th>ROI %</th>
                <th>Sales Rank</th>
                <th>Competition</th>
                <th>Recommendation</th>
            </tr>
        </thead>
        <tbody>
    `;

    filteredData.forEach(p => {
        const a = p.analysis;
        const netProfit = parseFloat(a.netProfit);
        const roi = parseFloat(a.roi);
        const rec = a.recommendation;

        let rowClass = '';
        if (netProfit < 0 || rec.includes('Low Profit')) {
            rowClass = 'table-danger';
        } else if (rec.includes('Highly Recommended') || rec.includes('Recommended') || roi >= 50) {
            rowClass = 'table-success';
        } else if (rec.includes('Slow') || rec.includes('High Competition') || roi >= 20) {
            rowClass = 'table-warning';
        }

        html += `
            <tr class="${rowClass}">
                <td><a href="${p.amazon_url}" target="_blank">${p.product_name}</a></td>
                <td>€${p.eurolotus_price || '-'}</td>
                <td>€${p.amazon_price || '-'}</td>
                <td>€${a.totalCost}</td>
                <td>€${(parseFloat(a.amazonFee) + parseFloat(a.fbaFee)).toFixed(2)}</td>
                <td>€${a.netProfit}</td>
                <td>${a.profitMargin}%</td>
                <td>${a.roi}</td>
                <td>${p.amazon_rank || '-'}</td>
                <td>${a.competition}</td>
                <td>${a.recommendation}</td>
            </tr>
        `;
    });

    html += '</tbody>';
    table.innerHTML = html;

    // Re-apply last sort automatically
    const lastSort = JSON.parse(localStorage.getItem('sortState'));
    if (lastSort && lastSort.field) {
        applyStoredSort(lastSort.field, lastSort.order, false);
    }
}

// --- Sort with persistence
document.getElementById('sortAsc').addEventListener('click', () => sortData('asc'));
document.getElementById('sortDesc').addEventListener('click', () => sortData('desc'));

function sortData(order = 'asc') {
    const key = document.getElementById('sortField').value;
    if (!key) return;

    localStorage.setItem('sortState', JSON.stringify({ field: key, order }));

    filteredData.sort((a, b) => {
        let valA, valB;
        if (a.analysis && a.analysis[key] !== undefined) {
            valA = a.analysis[key];
            valB = b.analysis[key];
        } else {
            valA = a[key];
            valB = b[key];
        }

        const numA = parseFloat(valA);
        const numB = parseFloat(valB);

        if (!isNaN(numA) && !isNaN(numB)) {
            return order === 'asc' ? numA - numB : numB - numA;
        }
        return order === 'asc'
            ? String(valA).localeCompare(String(valB))
            : String(valB).localeCompare(String(valA));
    });

    displayResults();
    document.getElementById('sortAsc').classList.toggle('btn-primary', order === 'asc');
    document.getElementById('sortDesc').classList.toggle('btn-primary', order === 'desc');
}

// --- Reapply saved sorting (used internally)
function applyStoredSort(key, order, display = true) {
    if (!key) return;
    const sortField = document.getElementById('sortField');
    sortField.value = key;
    filteredData.sort((a, b) => {
        let valA, valB;
        if (a.analysis && a.analysis[key] !== undefined) {
            valA = a.analysis[key];
            valB = b.analysis[key];
        } else {
            valA = a[key];
            valB = b[key];
        }
        const numA = parseFloat(valA);
        const numB = parseFloat(valB);
        if (!isNaN(numA) && !isNaN(numB)) {
            return order === 'asc' ? numA - numB : numB - numA;
        }
        return order === 'asc'
            ? String(valA).localeCompare(String(valB))
            : String(valB).localeCompare(String(valA));
    });
    if (display) displayResults();
    document.getElementById('sortAsc').classList.toggle('btn-primary', order === 'asc');
    document.getElementById('sortDesc').classList.toggle('btn-primary', order === 'desc');
}

// --- Apply saved sort on load
window.addEventListener('DOMContentLoaded', () => {
    const lastSort = JSON.parse(localStorage.getItem('sortState'));
    if (lastSort && lastSort.field) {
        document.getElementById('sortField').value = lastSort.field;
        applyStoredSort(lastSort.field, lastSort.order);
    }
});

// --- Update analysis when settings change
document.querySelectorAll('.setting-item input').forEach(input => {
    input.addEventListener('change', () => analyzeProducts());
});

// --- Export CSV
document.getElementById('exportBtn').addEventListener('click', () => {
    let csv = 'Product Name,EuroLotus Price,Amazon Price,Total Cost,Amazon Fee,FBA Fee,Net Profit,Profit Margin %,ROI %,Sales Rank,Competition,Recommendation,Amazon URL\n';
    filteredData.forEach(p => {
        const a = p.analysis;
        csv += `"${p.product_name}",${p.eurolotus_price},${p.amazon_price},${a.totalCost},${a.amazonFee},${a.fbaFee},${a.netProfit},${a.profitMargin},${a.roi},${p.amazon_rank},${a.competition},"${a.recommendation}","${p.amazon_url}"\n`;
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'eurolotus_analysis.csv';
    a.click();
});
