/* GiftScope Gift Finder: age -> interests -> budget -> ranked results */
(function () {
  var root = document.querySelector('[data-finder]');
  if (!root || !window.__GIFTS) return;
  var G = window.__GIFTS, st = { age: null, themes: [], budget: null }, step = 1;
  var steps = root.querySelectorAll('[data-step]'), dots = root.querySelectorAll('[data-step-dot]');
  var BUD = ['under-10', 'under-25', 'under-50', 'under-100', 'over-100'];
  var AGE_LBL = {}, THEME_LBL = {}, BUD_LBL = {};
  root.querySelectorAll('[data-q=age]').forEach(function (b) { AGE_LBL[b.dataset.v] = b.querySelector('b').textContent; });
  root.querySelectorAll('[data-q=theme]').forEach(function (b) { THEME_LBL[b.dataset.v] = b.querySelector('b').textContent; });
  root.querySelectorAll('[data-q=budget]').forEach(function (b) { BUD_LBL[b.dataset.v] = b.querySelector('b').textContent; });

  function go(n) {
    step = n;
    steps.forEach(function (s) { s.hidden = +s.dataset.step !== n; });
    dots.forEach(function (d) { d.classList.toggle('is-on', +d.dataset.stepDot <= n); });
    var h = root.querySelector('[data-step="' + n + '"] .qtitle');
    if (h) { h.setAttribute('tabindex', '-1'); h.focus({ preventScroll: true }); }
    root.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function money(x) { return '$' + x.toFixed(2); }
  function rev(n) { return n >= 1000 ? (n / 1000).toFixed(1).replace('.0', '') + 'K' : n; }
  function card(p) {
    return '<article class="card"><a class="card__media" href="' + esc(p.u) + '" target="_blank" rel="sponsored nofollow noopener" tabindex="-1" aria-hidden="true">' +
      '<img src="https://m.media-amazon.com/images/I/' + p.i + '._AC_SL500_.jpg" alt="" loading="lazy" width="500" height="500"></a>' +
      '<div class="card__body"><p class="card__meta"><span class="chip-age">Ages ' + esc(p.g) + '</span><span>' + esc(THEME_LBL[p.t] || '') + '</span></p>' +
      '<h3 class="card__title"><a href="' + esc(p.u) + '" target="_blank" rel="sponsored nofollow noopener">' + esc(p.n) + '</a></h3>' +
      '<p class="card__blurb">' + esc(p.d) + '</p>' +
      '<p class="card__rating"><span class="stars" style="--r:' + p.r + '" aria-hidden="true"></span><span>' + p.r.toFixed(1) + '</span><span class="muted">(' + rev(p.c) + ' ratings)</span></p>' +
      '<div class="card__buy"><span class="price">' + money(p.p) + '<sup>*</sup></span><a class="btn btn--amz" href="' + esc(p.u) + '" target="_blank" rel="sponsored nofollow noopener">See on Amazon</a></div></div></article>';
  }
  function results() {
    var byAge = G.filter(function (p) { return p.a.indexOf(st.age) > -1; });
    var notes = [];
    function inBudget(p, b) { return b === 'any' || p.b === b; }
    var pool = byAge.filter(function (p) { return (!st.themes.length || st.themes.indexOf(p.t) > -1) && inBudget(p, st.budget); });
    var themeHit = pool.length;
    // too few? relax budget to neighbours, then drop interests
    if (pool.length < 6 && st.budget !== 'any') {
      var i = BUD.indexOf(st.budget), near = [BUD[i - 1], BUD[i + 1]].filter(Boolean);
      var extra = byAge.filter(function (p) { return (!st.themes.length || st.themes.indexOf(p.t) > -1) && near.indexOf(p.b) > -1 && pool.indexOf(p) < 0; });
      if (extra.length) { pool = pool.concat(extra); notes.push('We added a few gifts just outside your budget.'); }
    }
    if (pool.length < 6 && st.themes.length) {
      var more = byAge.filter(function (p) { return inBudget(p, st.budget) && pool.indexOf(p) < 0; });
      if (more.length) { pool = pool.concat(more.sort(function (a, b) { return b.s - a.s; }).slice(0, 6 - pool.length)); notes.push('We added other top-rated gifts for this age.'); }
    }
    pool.sort(function (a, b) {
      var ta = (st.themes.indexOf(a.t) > -1) - (st.themes.indexOf(b.t) > -1);
      var ba = (inBudget(a, st.budget)) - (inBudget(b, st.budget));
      return (ba ? -ba : 0) || (ta ? -ta : 0) || b.s - a.s;
    });
    pool = pool.slice(0, 12);
    var title = 'Top gifts for ' + (AGE_LBL[st.age] || '').toLowerCase();
    if (st.themes.length === 1) title += ' who love ' + (THEME_LBL[st.themes[0]] || '').toLowerCase();
    if (st.budget && st.budget !== 'any') title += ' · ' + BUD_LBL[st.budget];
    root.querySelector('[data-rtitle]').textContent = title;
    root.querySelector('[data-rnote]').textContent = (themeHit ? themeHit + ' exact matches. ' : 'No exact matches. ') + notes.join(' ');
    root.querySelector('[data-results]').innerHTML = pool.map(card).join('');
    go(4);
  }
  root.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b || !root.contains(b)) return;
    var q = b.dataset.q;
    if (q === 'age') { st.age = b.dataset.v; go(2); }
    else if (q === 'theme') {
      var v = b.dataset.v, i = st.themes.indexOf(v);
      if (i > -1) st.themes.splice(i, 1); else st.themes.push(v);
      b.setAttribute('aria-pressed', i > -1 ? 'false' : 'true');
    }
    else if (q === 'budget') { st.budget = b.dataset.v; results(); }
    else if (b.hasAttribute('data-next')) go(3);
    else if (b.hasAttribute('data-back')) go(step - 1);
    else if (b.hasAttribute('data-restart')) {
      st = { age: null, themes: [], budget: null };
      root.querySelectorAll('[data-q=theme]').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      go(1);
    }
  });
})();
