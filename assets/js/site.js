// 사이트 인터랙션: 장르 필터 + 맨 위로 버튼
(function () {
  "use strict";

  // 장르 필터 칩
  var bar = document.querySelector(".filter-bar");
  if (bar) {
    bar.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      var f = btn.getAttribute("data-filter");
      bar.querySelectorAll("[data-filter]").forEach(function (b) {
        b.classList.toggle("active", b === btn);
      });
      document.querySelectorAll(".perf-card").forEach(function (c) {
        var show = f === "all" || c.getAttribute("data-genre") === f;
        c.style.display = show ? "" : "none";
      });
    });
  }

  // 맨 위로 버튼
  var top = document.querySelector(".to-top");
  if (top) {
    var onScroll = function () {
      top.classList.toggle("show", window.scrollY > 600);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    top.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
})();
