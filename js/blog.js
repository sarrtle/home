/* Sarrtle — blog renderer + code-block chrome.
   Data-driven: reads the post catalog from the URL given by a container's
   data-posts attribute ("blog/posts.json" on the homepage, "posts.json" on
   the blog index). Posts themselves are hand-written HTML; this script only
   builds the listings and the window-style chrome around highlighted code.
   highlight.js is optional — when present (post pages), code is highlighted
   and wrapped in a copyable window. No frameworks, no dependencies. */
(function () {
  "use strict";

  var doc = document;

  function onReady(fn) {
    if (doc.readyState === "loading") {
      doc.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function el(tag, cls, text) {
    var node = doc.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function fmtDate(iso) {
    var d = new Date(iso + "T00:00:00");
    if (isNaN(d.getTime())) return iso;
    return MONTHS[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
  }

  /* prefix: where "posts/…" paths resolve from this page ("blog/" on the
     homepage, "" on the blog index). Derived from the catalog URL. */
  function prefixFrom(url) {
    return url.replace(/posts\.json$/, "");
  }

  function emptyNote(text) {
    return el("p", "blog-empty", text || "No posts yet — the first write-up is in the works.");
  }

  function failNote(url, err) {
    var msg = "The post list couldn\u2019t be loaded from " + url +
              (err && err.message ? " (" + err.message + ")" : "") +
              ". If you opened this page from disk, serve the site instead: " +
              "run \u201cpython3 server.py\u201d and open http://localhost:8000/";
    var note = el("p", "blog-empty");
    note.textContent = msg;
    return note;
  }

  function renderCard(post, prefix) {
    var art = el("article", "blog-card");
    var href = prefix + "posts/" + post.slug + "/";

    if (post.cover) {
      var link = el("a", "blog-card-cover");
      link.href = href;
      var img = el("img");
      img.src = prefix + post.cover;
      img.alt = post.coverAlt || "";
      img.loading = "lazy";
      img.width = 1200;
      img.height = 675;
      link.appendChild(img);
      art.appendChild(link);
    }

    var body = el("div", "blog-card-body");
    var meta = el("div", "blog-meta");
    var time = el("time", "blog-date", fmtDate(post.date));
    time.dateTime = post.date;
    meta.appendChild(time);
    meta.appendChild(el("span", "badge blog-cat", post.category || ""));
    body.appendChild(meta);

    var h3 = el("h3", "blog-card-title");
    var titleLink = el("a", null, post.title);
    titleLink.href = href;
    h3.appendChild(titleLink);
    body.appendChild(h3);

    if (post.excerpt) body.appendChild(el("p", "blog-card-excerpt", post.excerpt));

    if (post.tags && post.tags.length) {
      body.appendChild(el("p", "work-tags", post.tags.join(" \u00b7 ")));
    }

    var read = el("a", "work-link", "Read post \u2192");
    read.href = href;
    body.appendChild(read);

    art.appendChild(body);
    return art;
  }

  function published(posts) {
    return (posts || []).filter(function (p) { return p.status !== "draft"; });
  }

  function newest(a, b) {
    return (b.date || "").localeCompare(a.date || "");
  }

  /* Homepage: latest 3 posts. */
  function renderLatest(container) {
    var url = container.getAttribute("data-posts");
    var prefix = prefixFrom(url);
    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var posts = published(data.posts).sort(newest);
        var grid = el("div", "blog-grid");
        posts.slice(0, 3).forEach(function (p) {
          grid.appendChild(renderCard(p, prefix));
        });
        container.appendChild(grid);
        if (!posts.length) container.appendChild(emptyNote());
      })
      .catch(function (e) { container.appendChild(failNote(url, e)); });
  }

  /* Blog index: full list + category filter chips (derived from the data). */
  function renderList(container) {
    var url = container.getAttribute("data-posts");
    var prefix = prefixFrom(url);
    var chipsHost = doc.getElementById(container.getAttribute("data-chips"));
    var countEl = doc.getElementById("blog-count");
    var grid = el("div", "blog-grid");
    var active = "All";
    try {
      active = new URLSearchParams(location.search).get("cat") || "All";
    } catch (e) { /* older browsers: stay on All */ }

    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var posts = published(data.posts).sort(newest);

        var cats = [];
        posts.forEach(function (p) {
          if (p.category && cats.indexOf(p.category) === -1) cats.push(p.category);
        });
        if (active !== "All" && cats.indexOf(active) === -1) active = "All";

        function apply(cat) {
          grid.textContent = "";
          posts.filter(function (p) {
            return cat === "All" || p.category === cat;
          }).forEach(function (p) { grid.appendChild(renderCard(p, prefix)); });
          var n = grid.children.length;
          if (countEl) countEl.textContent = n + (n === 1 ? " post" : " posts");
          if (!n) grid.appendChild(emptyNote());
        }

        function chip(label) {
          var b = el("button", "filter-chip", label);
          b.type = "button";
          b.setAttribute("aria-pressed", String(label === active));
          if (label === active) b.classList.add("is-active");
          b.addEventListener("click", function () {
            active = label;
            [].forEach.call(chipsHost.querySelectorAll(".filter-chip"), function (c) {
              var on = c === b;
              c.classList.toggle("is-active", on);
              c.setAttribute("aria-pressed", String(on));
            });
            apply(active);
            var q = active === "All" ? location.pathname
                                    : location.pathname + "?cat=" + encodeURIComponent(active);
            try { history.replaceState(null, "", q); } catch (err) { /* file:// etc. */ }
          });
          return b;
        }

        chipsHost.textContent = "";
        chipsHost.appendChild(chip("All"));
        cats.forEach(function (c) { chipsHost.appendChild(chip(c)); });

        container.insertBefore(grid, container.firstChild);
        apply(active);
      })
      .catch(function (e) { container.appendChild(failNote(url, e)); });
  }

  /* Post pages: highlight (when hljs present), wrap in window chrome,
     attach a copy button (navigator.clipboard with execCommand fallback). */
  function initCodeBlocks() {
    var codeEls = doc.querySelectorAll("pre code");
    if (!codeEls.length) return;

    if (window.hljs && !doc.querySelector("pre code.hljs")) {
      hljs.highlightAll();
    }

    [].forEach.call(codeEls, function (code) {
      if (code.closest && code.closest(".code-block")) return;
      var pre = code.parentNode;
      var block = el("div", "code-block");

      var head = el("div", "code-block-head");
      ["r", "y", "g"].forEach(function (c) {
        var dot = el("span", "c-dot c-dot-" + c);
        dot.setAttribute("aria-hidden", "true");
        head.appendChild(dot);
      });
      var langMatch = /language-([\w+-]+)/.exec(code.className || "");
      head.appendChild(el("span", "code-block-lang", langMatch ? langMatch[1] : "text"));

      var copy = el("button", "code-copy", "Copy");
      copy.type = "button";
      copy.setAttribute("aria-label", "Copy code to clipboard");
      head.appendChild(copy);

      block.appendChild(head);
      pre.parentNode.insertBefore(block, pre);
      block.appendChild(pre);

      copy.addEventListener("click", function () {
        var text = code.innerText;
        function feedback(ok) {
          copy.textContent = ok ? "Copied!" : "Press Ctrl+C";
          copy.classList.add("copied");
          window.setTimeout(function () {
            copy.textContent = "Copy";
            copy.classList.remove("copied");
          }, 1800);
        }
        function legacyCopy() {
          var ok = false;
          try {
            var ta = doc.createElement("textarea");
            ta.value = text;
            ta.setAttribute("readonly", "");
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            doc.body.appendChild(ta);
            ta.select();
            ok = doc.execCommand("copy");
            doc.body.removeChild(ta);
          } catch (e) { ok = false; }
          feedback(ok);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(text).then(function () { feedback(true); },
                                                  legacyCopy);
        } else {
          legacyCopy();
        }
      });
    });
  }

  onReady(function () {
    [].forEach.call(doc.querySelectorAll("[data-posts]"), function (c) {
      if (c.getAttribute("data-chips")) renderList(c);
      else renderLatest(c);
    });
    initCodeBlocks();
  });
})();
