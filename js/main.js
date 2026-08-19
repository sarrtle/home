/* Sarrtle — small vanilla enhancements. No dependencies, no framework. */
(function () {
  "use strict";

  var doc = document;

  /* 1. progressive enhancement flag (gates reveal animations) */
  doc.documentElement.classList.remove("no-js");
  doc.documentElement.classList.add("js");

  /* 2. footer year */
  var year = doc.querySelector("[data-year]");
  if (year) year.textContent = String(new Date().getFullYear());

  /* 3. header scrolled state */
  var header = doc.getElementById("site-header");
  var onScroll = function () {
    header.classList.toggle("scrolled", window.scrollY > 8);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* 4. mobile navigation */
  var toggle = doc.getElementById("nav-toggle");
  var nav = doc.getElementById("site-nav");
  var setNav = function (open) {
    toggle.setAttribute("aria-expanded", String(open));
    nav.classList.toggle("open", open);
  };
  toggle.addEventListener("click", function () {
    setNav(!nav.classList.contains("open"));
  });
  nav.addEventListener("click", function (e) {
    if (e.target.closest("a")) setNav(false);
  });
  doc.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setNav(false);
  });

  /* 5. reveal-on-scroll (skipped when motion is reduced or observer missing) */
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealEls = doc.querySelectorAll(".reveal");
  if (revealEls.length && !reduceMotion && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in-view"); });
  }

  /* 6. scrollspy for section links */
  var links = doc.querySelectorAll('.site-nav a[href^="#"]');
  var sections = Array.prototype.map.call(links, function (a) {
    return doc.querySelector(a.getAttribute("href"));
  }).filter(Boolean);
  var spy = function () {
    var pos = window.scrollY + 130;
    var current = "";
    sections.forEach(function (sec) {
      if (sec.offsetTop <= pos) current = sec.id;
    });
    if (window.innerHeight + window.scrollY >= doc.body.scrollHeight - 4) {
      current = sections.length ? sections[sections.length - 1].id : current;
    }
    links.forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === "#" + current);
    });
  };
  window.addEventListener("scroll", spy, { passive: true });
  spy();
})();