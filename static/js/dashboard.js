/* ContHome - Paleta para graficos */
const COLORS = [
    '#2C3E6B', '#4CAF7D', '#5B7FBF', '#E8913A', '#3D5493',
    '#C8E6D0', '#718096', '#6B8DD6', '#48BB78', '#A0AEC0'
];

function loadDashboardCharts(mes) {
    fetch('/api/dashboard-data?mes=' + encodeURIComponent(mes))
        .then(r => r.json())
        .then(data => {
            renderMonthlyChart(data.monthly);
            renderCategoryChart(data.categorias);
        });
}

function renderMonthlyChart(monthly) {
    const ctx = document.getElementById('chartMonthly');
    if (!ctx) return;

    const labels = monthly.map(m => {
        const [y, mo] = m.mes.split('-');
        const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
        return months[parseInt(mo) - 1] + ' ' + y;
    });

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Ingresos',
                    data: monthly.map(m => m.ingresos),
                    backgroundColor: 'rgba(76, 175, 125, 0.75)',
                    borderColor: '#4CAF7D',
                    borderWidth: 2,
                    borderRadius: 6
                },
                {
                    label: 'Gastos',
                    data: monthly.map(m => m.gastos),
                    backgroundColor: 'rgba(232, 145, 58, 0.75)',
                    borderColor: '#E8913A',
                    borderWidth: 2,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: v => '$' + v.toLocaleString(),
                        color: '#718096'
                    },
                    grid: { color: 'rgba(91, 127, 191, 0.1)' }
                },
                x: {
                    ticks: { color: '#718096' },
                    grid: { display: false }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#2C3E6B', font: { weight: 'bold' } }
                },
                tooltip: {
                    backgroundColor: '#2C3E6B',
                    callbacks: {
                        label: ctx => ctx.dataset.label + ': $' + ctx.parsed.y.toLocaleString(undefined, {minimumFractionDigits: 2})
                    }
                }
            }
        }
    });
}

function renderCategoryChart(categorias) {
    const ctx = document.getElementById('chartCategories');
    if (!ctx) return;

    if (categorias.length === 0) {
        ctx.parentElement.innerHTML = '<p style="color: #718096;" class="text-center mt-5">Sin datos de gastos para este mes</p>';
        return;
    }

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categorias.map(c => c.nombre),
            datasets: [{
                data: categorias.map(c => c.total),
                backgroundColor: categorias.map((_, i) => COLORS[i % COLORS.length]),
                borderWidth: 3,
                borderColor: '#F5F6FA'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: { size: 11, family: 'Inter' },
                        color: '#2C3E6B'
                    }
                },
                tooltip: {
                    backgroundColor: '#2C3E6B',
                    callbacks: {
                        label: ctx => ctx.label + ': $' + ctx.parsed.toLocaleString(undefined, {minimumFractionDigits: 2})
                    }
                }
            }
        }
    });
}
