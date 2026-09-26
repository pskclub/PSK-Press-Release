// PSK Press guide: menu, theme, "on this page", screenshot zoom and search.
(function () {
  var doc = document.documentElement;

  // Mobile menu.
  var menuBtn = document.querySelector(".menu-btn");
  var nav = document.getElementById("nav");
  if (menuBtn && nav) {
    menuBtn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", String(open));
    });
  }

  // Theme: system -> the other one -> back to system.
  var themeBtn = document.querySelector(".theme-btn");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var dark = doc.dataset.theme
        ? doc.dataset.theme === "dark"
        : window.matchMedia("(prefers-color-scheme: dark)").matches;
      var next = dark ? "light" : "dark";
      doc.dataset.theme = next;
      try {
        localStorage.setItem("psk-guide-theme", next);
      } catch (e) {}
    });
  }

  // Heading anchors and the "on this page" list.
  var heads = document.querySelectorAll(".doc h2[id], .doc h3[id]");
  var toc = document.querySelector(".toc");
  if (toc && heads.length > 1) {
    var b = document.createElement("b");
    b.textContent = "ในหน้านี้";
    toc.appendChild(b);
  }
  var links = [];
  heads.forEach(function (h) {
    var a = document.createElement("a");
    a.className = "anchor";
    a.href = "#" + h.id;
    a.setAttribute("aria-label", "ลิงก์ไปหัวข้อนี้");
    a.textContent = "#";
    h.appendChild(a);
    if (toc && heads.length > 1) {
      var t = document.createElement("a");
      t.href = "#" + h.id;
      t.textContent = h.firstChild ? h.childNodes[0].textContent : h.textContent;
      if (h.tagName === "H3") t.className = "sub";
      toc.appendChild(t);
      links.push([h, t]);
    }
  });
  if (links.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(
      function () {
        var cur = links[0];
        links.forEach(function (l) {
          if (l[0].getBoundingClientRect().top < 120) cur = l;
        });
        links.forEach(function (l) {
          l[1].classList.toggle("on", l === cur);
        });
      },
      { rootMargin: "0px 0px -60% 0px", threshold: [0, 1] }
    );
    links.forEach(function (l) {
      io.observe(l[0]);
    });
  }

  // Screenshot zoom.
  var box = document.querySelector(".lightbox");
  var boxImg = box && box.querySelector("img");
  document.querySelectorAll("a.shot").forEach(function (a) {
    a.addEventListener("click", function (e) {
      if (!box) return;
      e.preventDefault();
      boxImg.src = a.getAttribute("href");
      boxImg.alt = (a.querySelector("img") || {}).alt || "";
      box.classList.add("open");
      box.scrollTop = 0;
    });
  });
  if (box) {
    box.addEventListener("click", function () {
      box.classList.remove("open");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") box.classList.remove("open");
    });
  }

  // Search over every page's sections (assets/search.json).
  var input = document.querySelector(".search input");
  var results = document.querySelector(".results");
  var index = null;
  function load() {
    if (index) return Promise.resolve(index);
    return fetch("assets/search.json")
      .then(function (r) {
        return r.json();
      })
      .then(function (d) {
        index = d;
        return d;
      });
  }
  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function show(q) {
    q = q.trim().toLowerCase();
    if (!q) {
      results.classList.remove("open");
      return;
    }
    load().then(function (d) {
      var words = q.split(/\s+/);
      var hits = d
        .map(function (e) {
          var t = e.t.toLowerCase();
          var x = e.x.toLowerCase();
          var score = 0;
          for (var i = 0; i < words.length; i++) {
            var w = words[i];
            if (t.indexOf(w) >= 0) score += 3;
            else if (x.indexOf(w) >= 0) score += 1;
            else return null;
          }
          return { e: e, score: score };
        })
        .filter(Boolean)
        .sort(function (a, b) {
          return b.score - a.score;
        })
        .slice(0, 12);
      results.innerHTML = hits.length
        ? hits
            .map(function (h) {
              return '<a href="' + h.e.u + '">' + esc(h.e.t) + "<small>" + esc(h.e.s) + "</small></a>";
            })
            .join("")
        : "<p>ไม่พบ “" + esc(q) + "”</p>";
      results.classList.add("open");
    });
  }
  if (input && results) {
    input.addEventListener("input", function () {
      show(input.value);
    });
    input.addEventListener("focus", function () {
      load();
      if (input.value) show(input.value);
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        input.value = "";
        results.classList.remove("open");
      }
      if (e.key === "Enter") {
        var first = results.querySelector("a");
        if (first) location.href = first.href;
      }
      if (e.key === "ArrowDown") {
        var a = results.querySelector("a");
        if (a) {
          e.preventDefault();
          a.focus();
        }
      }
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".search")) results.classList.remove("open");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
        e.preventDefault();
        input.focus();
      }
    });
  }
})();
