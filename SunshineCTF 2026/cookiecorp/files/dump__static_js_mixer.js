(function () {
  'use strict';

  var recipe = window.__recipe || { id: null, ingredients: [] };
  var logEl = document.getElementById('mixer-log');

  function log(line, cls) {
    if (!logEl) return;
    var div = document.createElement('div');
    div.className = 'mix-line' + (cls ? ' ' + cls : '');
    div.textContent = line;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function dispense(ing) {
    document.cookie = ing.name + '=' + (ing.value || '') + '; path=/';
  }

  async function run() {
    log('> spinning up fabrication drum...', 'ok');
    log('> dispensing ' + recipe.ingredients.length + ' ingredient(s)', 'ok');

    for (var i = 0; i < recipe.ingredients.length; i++) {
      dispense(recipe.ingredients[i]);
    }
    log('> ingredients loaded. cookie tray settled.', 'ok');

    log('> stamping inspector verdict...', 'ok');
    var result;
    try {
      var resp = await fetch('/api/seal', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ recipeId: recipe.id }),
      });
      result = await resp.json().catch(function () { return { ok: false }; });
      result.httpStatus = resp.status;
    } catch (e) {
      result = { ok: false, error: String(e) };
    }

    if (result && result.seal === 'chief') {
      log('> GOLDEN SEAL APPLIED. batch certified by the Chief.', 'gold');
    } else if (result && result.seal === 'reviewed') {
      log('> standard seal applied. batch reviewed.', 'ok');
    } else {
      log('> verdict rejected: ' + (result && (result.error || result.httpStatus)), 'bad');
    }

    window.__cc_done = result || { ok: false };
  }

  run();
})();
