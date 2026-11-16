// Shared behaviour: theme toggle, mobile sidebar, delete confirmation, loading buttons.
(function () {
  var root = document.documentElement;

  // Dark / light mode (remembered in the browser)
  var themeBtn = document.getElementById("themeToggle");
  function syncIcon() {
    if (!themeBtn) return;
    var dark = root.getAttribute("data-bs-theme") === "dark";
    themeBtn.innerHTML = dark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
  }
  syncIcon();
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      root.setAttribute("data-bs-theme", next);
      try { localStorage.setItem("theme", next); } catch (e) {}
      syncIcon();
      if (window.redrawCharts) window.redrawCharts();
    });
  }

  // Mobile sidebar
  var toggle = document.getElementById("sidebarToggle");
  var sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () { sidebar.classList.toggle("open"); });
  }

  // Confirmation before destructive actions
  var modalEl = document.getElementById("confirmModal");
  if (modalEl && window.bootstrap) {
    var modal = new bootstrap.Modal(modalEl);
    var pendingForm = null;
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        pendingForm = form;
        document.getElementById("confirmText").textContent = form.getAttribute("data-confirm");
        modal.show();
      });
    });
    document.getElementById("confirmYes").addEventListener("click", function () {
      if (pendingForm) { pendingForm.submit(); }
    });
  }

  // Loading indicator on submit buttons
  document.querySelectorAll("form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (e.defaultPrevented) return;
      var btn = form.querySelector("button[data-loading]");
      if (!btn) return;
      btn.classList.add("is-loading");
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>' +
        btn.getAttribute("data-loading");
    });
  });
})();
