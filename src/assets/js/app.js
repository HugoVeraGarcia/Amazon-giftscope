/* GiftScope: menu + listing filters */
(function () {
  var btn = document.querySelector('[data-menu]'), nav = document.getElementById('nav');
  if (btn && nav) btn.addEventListener('click', function () {
    var open = nav.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });

  var box = document.querySelector('[data-filters]'), grid = document.querySelector('[data-grid]');
  if (!box || !grid) return;
  var cards = Array.prototype.slice.call(grid.querySelectorAll('.card'));
  var chips = Array.prototype.slice.call(box.querySelectorAll('.fchip'));
  var sortSel = box.querySelector('[data-sort]'), countEl = box.querySelector('[data-count]');
  var clears = document.querySelectorAll('[data-clear]'), empty = document.querySelector('[data-empty]');
  var attr = { age: 'ages', theme: 'theme', budget: 'budget' };

  function active() {
    var a = {};
    chips.forEach(function (c) {
      if (c.getAttribute('aria-pressed') === 'true') (a[c.dataset.f] = a[c.dataset.f] || []).push(c.dataset.v);
    });
    return a;
  }
  function apply(push) {
    var a = active(), shown = 0, any = Object.keys(a).length > 0;
    cards.forEach(function (card) {
      var ok = Object.keys(a).every(function (k) {
        var vals = (card.dataset[attr[k]] || '').split(' ');
        return a[k].some(function (v) { return vals.indexOf(v) > -1; });
      });
      card.hidden = !ok;
      if (ok) shown++;
    });
    var s = sortSel.value;
    var sorted = cards.slice().sort(function (x, y) {
      var px = +x.dataset.price, py = +y.dataset.price;
      if (s === 'price-asc') return px - py;
      if (s === 'price-desc') return py - px;
      if (s === 'reviews') return y.dataset.reviews - x.dataset.reviews;
      return y.dataset.score - x.dataset.score;
    });
    sorted.forEach(function (c) { grid.appendChild(c); });
    var ranks = grid.querySelectorAll('.card__rank');
    var rankOn = !any && s === 'score';
    ranks.forEach(function (r) { r.hidden = !rankOn; });
    countEl.textContent = shown + (shown === 1 ? ' gift' : ' gifts');
    clears.forEach(function (c) { c.hidden = !any; });
    if (empty) empty.hidden = shown > 0;
    if (push !== false) {
      var q = new URLSearchParams();
      Object.keys(a).forEach(function (k) { q.set(k, a[k].join(',')); });
      if (s !== 'score') q.set('sort', s);
      var qs = q.toString();
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
    }
  }
  chips.forEach(function (c) {
    c.addEventListener('click', function () {
      c.setAttribute('aria-pressed', c.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      apply();
    });
  });
  sortSel.addEventListener('change', function () { apply(); });
  clears.forEach(function (c) {
    c.addEventListener('click', function () {
      chips.forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
      apply();
    });
  });
  // restore from URL (?age=teens&budget=under-25)
  var q = new URLSearchParams(location.search);
  chips.forEach(function (c) {
    var v = q.get(c.dataset.f);
    if (v && v.split(',').indexOf(c.dataset.v) > -1) c.setAttribute('aria-pressed', 'true');
  });
  if (q.get('sort')) sortSel.value = q.get('sort');
  apply(false);
})();
