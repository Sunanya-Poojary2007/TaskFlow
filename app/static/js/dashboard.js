// Chart.js charts for the dashboard. Data comes from window.DASH (set in dashboard.html).
(function () {
  if (!window.Chart || !window.DASH) return;
  var charts = [];

  function textColor() {
    return document.documentElement.getAttribute("data-bs-theme") === "dark" ? "#cbd5e1" : "#475569";
  }

  function draw() {
    charts.forEach(function (c) { c.destroy(); });
    charts = [];
    Chart.defaults.color = textColor();

    charts.push(new Chart(document.getElementById("statusChart"), {
      type: "doughnut",
      data: {
        labels: DASH.statusLabels,
        datasets: [{ data: DASH.statusData, backgroundColor: ["#94a3b8", "#3b82f6", "#22c55e"], borderWidth: 0 }]
      },
      options: { maintainAspectRatio: false, cutout: "62%", plugins: { legend: { position: "bottom" } } }
    }));

    charts.push(new Chart(document.getElementById("priorityChart"), {
      type: "bar",
      data: {
        labels: DASH.priorityLabels,
        datasets: [{ label: "Tasks", data: DASH.priorityData,
          backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"], borderRadius: 6 }]
      },
      options: {
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    }));
  }

  window.redrawCharts = draw;
  draw();
})();
