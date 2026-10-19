/* Climate Control Solutions: menu, booking modal, lightbox, call/book tracking */
(function () {
  var doc = document.documentElement, body = document.body;

  // Mobile menu
  var menuBtn = document.querySelector(".menu-btn");
  function setMenu(open) {
    body.classList.toggle("menu-open", open);
    if (menuBtn) { menuBtn.setAttribute("aria-expanded", open); menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu"); }
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { setMenu(!body.classList.contains("menu-open")); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setMenu(false); });

  // Dropdowns: click toggles (needed for touch + mobile drawer)
  document.querySelectorAll(".nav-top").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var li = btn.parentElement, open = !li.classList.contains("open");
      document.querySelectorAll(".has-sub.open").forEach(function (o) { if (o !== li) { o.classList.remove("open"); o.querySelector(".nav-top").setAttribute("aria-expanded", "false"); } });
      li.classList.toggle("open", open);
      btn.setAttribute("aria-expanded", open);
    });
  });
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".has-sub")) document.querySelectorAll(".has-sub.open").forEach(function (o) { o.classList.remove("open"); });
  });

  // Tracking hooks (GTM picks these up when the live build loads it)
  function push(ev) { window.dataLayer = window.dataLayer || []; window.dataLayer.push({ event: ev }); if (window.fbq && ev === "phone_click") window.fbq("track", "Contact"); }
  document.querySelectorAll("[data-call]").forEach(function (a) { a.addEventListener("click", function () { push("phone_click"); }); });

  // Booking: Housecall Pro's own widget, loaded on first click; falls back to their booking page in a new tab
  var HCP = "https://online-booking.housecallpro.com/script.js?token=3ab20efed2974c9b8daffc812da8843f&orgName=Climate-Control-Solutions";
  var hcpLoading = false;
  function openBooking(fallbackUrl) {
    if (window.HCPWidget) { window.HCPWidget.openModal(); return; }
    var t0 = Date.now();
    if (!hcpLoading) { hcpLoading = true; var sc = document.createElement("script"); sc.src = HCP; sc.async = true; document.head.appendChild(sc); }
    (function wait() {
      if (window.HCPWidget) { window.HCPWidget.openModal(); return; }
      if (Date.now() - t0 > 5000) { window.open(fallbackUrl, "_blank", "noopener"); return; }
      setTimeout(wait, 100);
    })();
  }
  document.querySelectorAll("[data-book]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      push("book_online_click");
      e.preventDefault();
      setMenu(false);
      openBooking(a.href);
    });
  });

  // Project photo lightbox
  var links = document.querySelectorAll("[data-lightbox]");
  if (links.length && window.HTMLDialogElement) {
    var lb = document.createElement("dialog");
    lb.className = "lightbox";
    lb.innerHTML = '<button aria-label="Close photo"><svg class="i" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button><img alt="">';
    body.appendChild(lb);
    lb.addEventListener("click", function () { lb.close(); });
    links.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var im = lb.querySelector("img");
        im.src = a.href; im.alt = (a.querySelector("img") || {}).alt || "";
        lb.showModal();
      });
    });
  }

  // Hide "Swipe →" once the user scrolls a row
  document.querySelectorAll("[data-swipe]").forEach(function (row) {
    row.addEventListener("scroll", function () {
      var hint = row.nextElementSibling;
      if (hint && hint.classList.contains("swipe-hint") && row.scrollLeft > 30) hint.style.visibility = "hidden";
    }, { passive: true });
  });
})();
