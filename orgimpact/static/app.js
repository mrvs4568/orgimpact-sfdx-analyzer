(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  let snapshot = null;
  let report = null;
  const selected = new Map();

  const make = (tag, text, className) => {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = String(text);
    if (className) el.className = className;
    return el;
  };

  function feedback(message) { $('feedback').textContent = message; }

  function invalidateReport() {
    report = null;
    $('download-report').disabled = true;
    $('metric-impacted').textContent = '0';
    $('result-state').textContent = 'NOT RUN';
    $('result-empty').hidden = false;
    $('result-body').hidden = true;
  }

  function renderSelections() {
    const panel = $('selected-changes');
    panel.replaceChildren();
    if (!selected.size) panel.append(make('p', 'No components selected.', 'empty'));
    for (const [id, change] of selected) {
      const row = make('div', undefined, 'selection');
      const detail = make('span');
      detail.append(make('span', change.status, 'operation'), make('span', id));
      const remove = make('button', 'Remove');
      remove.type = 'button'; remove.setAttribute('aria-label', `Remove ${id}`);
      remove.addEventListener('click', () => { selected.delete(id); invalidateReport(); renderSelections(); });
      row.append(detail, remove); panel.append(row);
    }
    $('metric-changed').textContent = String(selected.size);
  }

  function renderInventory(filter = '') {
    if (!snapshot) return;
    const body = $('inventory-body'); body.replaceChildren();
    const value = filter.toLowerCase();
    const items = snapshot.components.filter(c => (c.id + ' ' + c.paths.join(' ')).toLowerCase().includes(value));
    const counts = new Map();
    for (const edge of snapshot.references) counts.set(edge.source, (counts.get(edge.source) || 0) + 1);
    for (const c of items) {
      const row = make('tr');
      const name = make('td'); name.append(make('strong', c.name));
      const kind = make('td'); kind.append(make('span', c.kind, 'type-tag'));
      row.append(name, kind, make('td', c.paths.length), make('td', counts.get(c.id) || 0));
      body.append(row);
    }
    if (!items.length) { const row = make('tr'); const cell = make('td', 'No matching components'); cell.colSpan = 4; row.append(cell); body.append(row); }
    $('inventory-count').textContent = `${items.length} of ${snapshot.components.length} components`;
  }

  function renderReport(data) {
    $('metric-impacted').textContent = data.summary.impacted_components;
    $('result-empty').hidden = true;
    $('result-body').hidden = false;
    $('result-state').textContent = 'COMPLETE';
    const risks = $('risk-cards'); risks.replaceChildren();
    for (const change of data.changes) {
      const item = make('article', undefined, 'risk-item');
      const head = make('header');
      head.append(make('strong', change.id), make('span', `${change.risk_level.toUpperCase()} · ${change.risk_score}/100`, `risk-label ${change.risk_level}`));
      item.append(head, make('p', `${change.status} · ${change.direct_dependents.length} direct and ${change.indirect_dependents.length} transitive consumers`), make('small', change.risk_factors.join(' | ')));
      risks.append(item);
    }
    if (!data.changes.length) risks.append(make('p', 'No supported metadata change was selected.', 'empty'));
    const impacts = $('impact-list'); impacts.replaceChildren();
    if (!data.impacted.length) impacts.append(make('p', 'No additional consumers detected.', 'empty'));
    for (const item of data.impacted) {
      const row = make('div', undefined, 'impact-row');
      row.append(make('span', item.id), make('small', `Depth ${item.min_depth}`));
      impacts.append(row);
    }
    $('download-report').disabled = false;
    feedback(data.ignored_changes.concat(data.warnings).join(' | '));
  }

  async function api(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({detail: 'Unknown server error'}));
      throw new Error(typeof error.detail === 'string' ? error.detail : JSON.stringify(error.detail));
    }
    return response;
  }

  async function initialize() {
    try {
      snapshot = await (await api('/api/snapshot')).json();
      $('metric-components').textContent = snapshot.components.length;
      $('metric-edges').textContent = snapshot.references.length;
      $('scan-warnings').textContent = snapshot.warnings.length ? `${snapshot.warnings.length} scan warning(s)` : 'No scan warnings';
      const select = $('component-select'); select.replaceChildren();
      for (const c of snapshot.components) {
        const option = make('option', `${c.kind} · ${c.name}`);
        option.value = c.id; select.append(option);
      }
      renderInventory(); renderSelections();
    } catch (err) {
      const row = make('tr'); const cell = make('td', 'Failed to load workspace'); cell.colSpan = 4; row.append(cell); $('inventory-body').replaceChildren(row);
      feedback(`Unable to load snapshot: ${err.message}`);
    }
  }

  $('add-change').addEventListener('click', () => {
    const id = $('component-select').value;
    if (!snapshot || !id) return;
    const component = snapshot.components.find(c => c.id === id);
    if (!component) return;
    selected.set(id, {path: component.paths[0], status: $('change-status').value});
    invalidateReport(); renderSelections(); feedback('');
  });
  $('filter-components').addEventListener('input', event => renderInventory(event.target.value));
  $('run-analysis').addEventListener('click', async () => {
    if (!selected.size) { feedback('Select at least one component first.'); return; }
    const button = $('run-analysis'); button.disabled = true; feedback('');
    try {
      const data = {changes: [...selected.values()]};
      report = await (await api('/api/analyze', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)})).json();
      renderReport(report);
    } catch (err) { feedback(`Analysis failed: ${err.message}`); }
    finally { button.disabled = false; }
  });
  $('download-report').addEventListener('click', async () => {
    if (!report) return;
    try {
      const response = await api('/api/export.md', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({changes: [...selected.values()]})});
      const blob = new Blob([await response.text()], {type: 'text/markdown'});
      const url = URL.createObjectURL(blob);
      const link = make('a'); link.href = url; link.download = 'orgimpact-review.md';
      document.body.append(link); link.click(); link.remove(); URL.revokeObjectURL(url);
    } catch (err) { feedback(`Export failed: ${err.message}`); }
  });
  initialize();
})();
