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

        // Competition calculation
        const sellers = parseInt(product.amazon_sellers) || 0;
        const fba = parseInt(product.fba_sellers) || 0;
        const fbaPercent = sellers ? (fba / sellers) * 100 : 0;
        let competition = 'Low';
        if (fbaPercent > 70 || sellers > 10) competition = 'High';
        else if (fbaPercent > 40 || sellers > 5) competition = 'Medium';

        // Recommendation
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
            recommendation,
            profitLevel: profitMargin >= 40 ? 'High' : profitMargin >= 25 ? 'Medium' : 'Low'
        };
    });

    filteredData = [...productsData];
    displayResults();
}

// --- Display table
function displayResults() {
    const table = document.getElementById('resultsTable');
    let html = `
        <thead>
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
        html += `
            <tr>
                <td><a href="${p.amazon_url}" target="_blank">${p.product_name}</a></td>
                <td>€${p.eurolotus_price}</td>
                <td>€${p.amazon_price}</td>
                <td>€${a.totalCost}</td>
                <td>€${(parseFloat(a.amazonFee)+parseFloat(a.fbaFee)).toFixed(2)}</td>
                <td>€${a.netProfit}</td>
                <td>${a.profitMargin}%</td>
                <td>${a.roi}</td>
                <td>${p.amazon_rank}</td>
                <td>${a.competition}</td>
                <td>${a.recommendation}</td>
            </tr>
        `;
    });

    html += '</tbody>';
    table.innerHTML = html;
}

// --- Filters
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const filter = btn.dataset.filter;
        if(filter==='all') filteredData = [...productsData];
        else if(filter==='profitable') filteredData = productsData.filter(p => parseFloat(p.analysis.profitMargin)>=40);
        else if(filter==='low-comp') filteredData = productsData.filter(p => p.analysis.competition==='Low');
        else if(filter==='recommended') filteredData = productsData.filter(p => p.analysis.recommendation.includes('Recommended'));

        displayResults();
    });
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
    const blob = new Blob([csv], {type:'text/csv'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'eurolotus_analysis.csv';
    a.click();
});
