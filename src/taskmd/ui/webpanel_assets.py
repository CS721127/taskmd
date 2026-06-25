"""
HTML/CSS/JS asset for the TaskMD web control panel.

Design concept: the panel looks like the markdown source file it controls.
Section headers render as "# Section", subsections as "## Sub", and each
task row reads like a line straight out of tasks.md — but the checkbox,
due date, and priority are live controls, not static text. There is no
card grid, no sidebar chrome: the file *is* the interface.
"""

PANEL_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TaskMD — Control Panel</title>
<style>
:root {
  --paper: #f2f1e8;
  --paper-raised: #ebe9dc;
  --ink: #24261f;
  --ink-soft: #5b5d4f;
  --ink-faint: #8a8c7c;
  --rule: #d8d6c5;
  --amber: #c2741f;
  --amber-soft: #e8d3b3;
  --teal: #3d6b62;
  --teal-soft: #cfe0db;
  --red: #a8392c;
  --red-soft: #ecd2cc;
  --focus: #2f6e63;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "JetBrains Mono", "IBM Plex Mono", "SF Mono", Menlo, Consolas, monospace;
  font-size: 14px;
  line-height: 1.55;
}

body {
  background-image: linear-gradient(var(--rule) 1px, transparent 1px);
  background-size: 100% 28px;
  background-attachment: local;
}

a { color: var(--teal); text-decoration: none; }
::selection { background: var(--amber-soft); }

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--paper);
  border-bottom: 1px solid var(--rule);
  padding: 14px 22px 10px;
}

.topbar .path-line {
  color: var(--ink-faint);
  font-size: 12px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.path-line .comment { color: var(--ink-faint); }
.path-line .file-path { color: var(--ink-soft); }

.live-dot {
  display: inline-block;
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--teal);
  margin-right: 6px;
  box-shadow: 0 0 0 0 rgba(61,107,98,0.5);
  animation: pulse 2.4s ease-out infinite;
}
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(61,107,98,0.35); }
  70%  { box-shadow: 0 0 0 6px rgba(61,107,98,0); }
  100% { box-shadow: 0 0 0 0 rgba(61,107,98,0); }
}

.stats-line {
  margin-top: 8px;
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  font-size: 13px;
}
.stats-line .stat { color: var(--ink-soft); }
.stats-line .stat b { color: var(--ink); font-weight: 600; }
.stats-line .stat.warn b { color: var(--red); }
.stats-line .stat.good b { color: var(--teal); }

main {
  max-width: 880px;
  margin: 0 auto;
  padding: 18px 22px 80px;
}

.section-header {
  margin: 30px 0 4px;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.section-header:first-child { margin-top: 12px; }

.section-header .hash { color: var(--amber); font-weight: 700; }
.section-header .name { font-weight: 700; font-size: 16px; letter-spacing: 0.2px; }
.section-header .progress { color: var(--ink-faint); font-size: 12px; }
.section-rule { border: none; border-top: 1px solid var(--rule); margin: 6px 0 10px; }

.sub-header {
  margin: 16px 0 2px 18px;
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: var(--ink-soft);
  font-size: 13px;
}
.sub-header .hash { color: var(--ink-faint); }
.sub-header .name { font-weight: 600; }

.toolbar {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.toolbar .search-wrap {
  position: relative;
  flex: 1;
  min-width: 160px;
  max-width: 280px;
}
.toolbar input[type="search"] {
  width: 100%;
  font-family: inherit;
  font-size: 12px;
  padding: 5px 10px 5px 24px;
  border: 1px solid var(--rule);
  border-radius: 5px;
  background: #fff;
  color: var(--ink);
  outline: none;
}
.toolbar input[type="search"]:focus { border-color: var(--focus); }
.toolbar .search-wrap::before {
  content: "\1F50D";
  position: absolute;
  left: 7px; top: 50%;
  transform: translateY(-50%);
  font-size: 10px;
  opacity: 0.5;
}
.tb-btn {
  font-family: inherit;
  font-size: 11px;
  font-weight: 600;
  background: #fff;
  color: var(--ink-soft);
  border: 1px solid var(--rule);
  border-radius: 5px;
  padding: 5px 10px;
  cursor: pointer;
  white-space: nowrap;
}
.tb-btn:hover { background: var(--paper-raised); color: var(--ink); }
.tb-btn.danger:hover { background: var(--red-soft); color: var(--red); border-color: var(--red); }
.tb-btn.tag-filter-active { background: var(--teal); color: #fff; border-color: var(--teal); }

.search-results {
  margin: 14px 0 24px;
  padding: 10px 14px;
  background: var(--paper-raised);
  border-radius: 6px;
  border: 1px dashed var(--rule);
}
.search-results .sr-header {
  font-size: 12px;
  color: var(--ink-faint);
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
}
.search-results .sr-clear { cursor: pointer; color: var(--teal); }

.tag-chip-bar {
  margin: 10px 0 0;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag-chip {
  font-size: 11px;
  background: var(--teal-soft);
  color: var(--teal);
  border-radius: 10px;
  padding: 2px 9px;
  cursor: pointer;
  border: 1px solid transparent;
}
.tag-chip:hover { border-color: var(--teal); }
.tag-chip .count { opacity: 0.6; margin-left: 3px; }
.tag-chip.active { background: var(--teal); color: #fff; }

.task-row {
  display: grid;
  grid-template-columns: 22px 30px 1fr auto auto auto 20px;
  align-items: center;
  gap: 8px;
  padding: 3px 8px 3px 18px;
  margin: 1px 0;
  border-radius: 4px;
  transition: background 0.15s ease;
  position: relative;
}
.task-row:hover { background: var(--paper-raised); }
.task-row.flash { background: var(--amber-soft); }

.checkbox-btn {
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink-soft);
  padding: 0;
  width: 22px;
  text-align: center;
}
.checkbox-btn:hover { color: var(--ink); }
.checkbox-btn[data-status="[x]"] { color: var(--teal); }
.checkbox-btn[data-status="[-]"] { color: var(--amber); }

.task-id { color: var(--ink-faint); font-size: 12px; }

.task-name { outline: none; padding: 1px 4px; border-radius: 3px; cursor: text; }
.task-name:focus { background: #fff; box-shadow: 0 0 0 1px var(--focus); }
.task-row.is-done .task-name { color: var(--ink-faint); text-decoration: line-through; text-decoration-color: var(--ink-faint); }
.task-row.is-progress .task-name { color: var(--ink); }

.task-tags { color: var(--teal); font-size: 12px; white-space: nowrap; }
.task-tags .tag::before { content: "#"; opacity: 0.6; }
.task-tags .tag { margin-right: 6px; }

.task-due {
  font-size: 12px;
  white-space: nowrap;
  padding: 1px 6px;
  border-radius: 3px;
  cursor: pointer;
  color: var(--ink-soft);
  background: transparent;
  border: 1px dashed transparent;
}
.task-due:hover { border-color: var(--rule); }
.task-due.due-OVERDUE { color: var(--red); background: var(--red-soft); border-color: transparent; }
.task-due.due-DUE_TODAY { color: var(--amber); background: var(--amber-soft); border-color: transparent; }
.task-due.due-DUE_SOON { color: var(--amber); }
.task-due.empty { opacity: 0; transition: opacity 0.12s ease; }
.task-row:hover .task-due.empty { opacity: 0.55; }
.task-due.empty:hover { opacity: 1; border-color: var(--rule); }
.task-due input {
  font-family: inherit; font-size: 12px; width: 130px;
  border: 1px solid var(--focus); border-radius: 3px; padding: 1px 4px;
  background: #fff; color: var(--ink);
}

.task-pri {
  color: var(--amber);
  font-size: 12px;
  letter-spacing: -1px;
  min-width: 28px;
  text-align: right;
  cursor: pointer;
  border-radius: 3px;
  padding: 1px 4px;
  border: 1px dashed transparent;
}
.task-pri:hover { border-color: var(--rule); }
.task-pri.empty {
  color: var(--ink-faint);
  letter-spacing: 0;
  opacity: 0;
  transition: opacity 0.12s ease;
}
.task-row:hover .task-pri.empty { opacity: 0.55; }
.task-pri.empty:hover { opacity: 1; border-color: var(--rule); }
.task-pri.empty::before { content: "+ pri"; font-size: 10px; }
.task-pri input {
  font-family: inherit; font-size: 12px; width: 32px; text-align: right;
  border: 1px solid var(--focus); border-radius: 3px; padding: 1px 4px;
  background: #fff; color: var(--ink);
}

.task-tags { color: var(--teal); font-size: 12px; white-space: nowrap; cursor: pointer; }
.task-tags .tag { margin-right: 6px; position: relative; }
.task-tags .tag::before { content: "#"; opacity: 0.6; }
.task-tags .tag .tag-x {
  opacity: 0; margin-left: 2px; color: var(--red); font-weight: 700;
}
.task-tags .tag:hover .tag-x { opacity: 1; }
.task-tags .tag-add-btn {
  color: var(--ink-faint);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.12s ease;
  font-size: 11px;
}
.task-row:hover .task-tags .tag-add-btn { opacity: 0.55; }
.task-tags .tag-add-btn:hover { color: var(--teal); opacity: 1; }

.menu-btn {
  background: none; border: none; cursor: pointer;
  color: var(--ink-faint); font-size: 14px; padding: 0;
  width: 20px; text-align: center; line-height: 1;
}
.menu-btn:hover { color: var(--ink); }

.action-menu {
  position: absolute;
  right: 8px;
  top: 26px;
  background: #fff;
  border: 1px solid var(--rule);
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(36,38,31,0.14);
  z-index: 20;
  min-width: 168px;
  padding: 4px;
}
.action-menu button {
  display: block;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  font-family: inherit;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--ink);
}
.action-menu button:hover { background: var(--paper-raised); }
.action-menu button.danger { color: var(--red); }
.action-menu button.danger:hover { background: var(--red-soft); }
.action-menu hr { border: none; border-top: 1px solid var(--rule); margin: 4px 0; }

.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(36,38,31,0.35);
  display: flex; align-items: center; justify-content: center;
  z-index: 50;
}
.modal-box {
  background: var(--paper);
  border-radius: 8px;
  padding: 20px 22px;
  max-width: 360px;
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}
.modal-box h3 { margin: 0 0 8px; font-size: 14px; }
.modal-box p { margin: 0 0 16px; font-size: 12px; color: var(--ink-soft); line-height: 1.5; }
.modal-box .modal-row { display: flex; gap: 8px; margin-bottom: 10px; }
.modal-box label { font-size: 11px; color: var(--ink-faint); display: block; margin-bottom: 3px; }
.modal-box input[type="text"] {
  width: 100%; font-family: inherit; font-size: 13px;
  border: 1px solid var(--rule); border-radius: 4px; padding: 5px 8px;
  background: #fff; color: var(--ink); outline: none;
}
.modal-box input[type="text"]:focus { border-color: var(--focus); }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px; }
.modal-actions button {
  font-family: inherit; font-size: 12px; font-weight: 600;
  border: none; border-radius: 5px; padding: 6px 14px; cursor: pointer;
}
.modal-actions .btn-cancel { background: var(--paper-raised); color: var(--ink-soft); }
.modal-actions .btn-confirm { background: var(--teal); color: #fff; }
.modal-actions .btn-danger { background: var(--red); color: #fff; }

.validate-panel {
  margin: 14px 0 24px;
  padding: 10px 14px;
  background: var(--red-soft);
  border-radius: 6px;
  border: 1px dashed var(--red);
  font-size: 12px;
}
.validate-panel.clean { background: var(--teal-soft); border-color: var(--teal); }
.validate-panel ul { margin: 6px 0 0; padding-left: 18px; }
.validate-panel .sr-clear { cursor: pointer; color: var(--teal); float: right; }

.empty-state { margin: 60px 0; text-align: center; color: var(--ink-faint); }
.empty-state .glyph { font-size: 28px; display: block; margin-bottom: 8px; }

.add-bar {
  position: sticky;
  bottom: 0;
  background: linear-gradient(to top, var(--paper) 70%, transparent);
  padding: 18px 22px 22px;
  max-width: 880px;
  margin: 0 auto;
}
.add-bar form {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid var(--rule);
  border-radius: 6px;
  padding: 8px 12px;
  box-shadow: 0 2px 10px rgba(36,38,31,0.06);
}
.add-bar .prompt { color: var(--ink-faint); }
.add-bar input[type="text"] {
  flex: 1;
  border: none;
  outline: none;
  font-family: inherit;
  font-size: 14px;
  background: transparent;
  color: var(--ink);
}
.add-bar input[type="text"]::placeholder { color: var(--ink-faint); }
.add-bar button {
  font-family: inherit;
  font-size: 12px;
  font-weight: 600;
  background: var(--teal);
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
}
.add-bar button:hover { background: var(--focus); }

.toast {
  position: fixed;
  bottom: 90px;
  left: 50%;
  transform: translateX(-50%) translateY(8px);
  background: var(--ink);
  color: var(--paper);
  padding: 7px 14px;
  border-radius: 5px;
  font-size: 12px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
.toast.err { background: var(--red); }

@media (max-width: 640px) {
  .task-row { grid-template-columns: 20px 26px 1fr 20px; }
  .task-due, .task-pri, .task-tags { grid-column: 3; margin-left: 0; }
  .task-tags { display: none; }
  .toolbar .search-wrap { max-width: none; }
}
</style>
</head>
<body>

<div class="topbar">
  <div class="path-line">
    <span class="comment">&lt;!-- <span class="live-dot"></span><span id="file-path">taskmd</span> --&gt;</span>
    <span class="file-path" id="last-sync">connecting&hellip;</span>
  </div>
  <div class="stats-line" id="stats-line"></div>
  <div class="toolbar">
    <div class="search-wrap">
      <input type="search" id="search-input" placeholder="Search name, tag, section, note&hellip;">
    </div>
    <button class="tb-btn" id="btn-validate" title="Check the file for formatting issues">Validate</button>
    <button class="tb-btn" id="btn-archive" title="Move all completed tasks to the archive file">Archive done</button>
    <button class="tb-btn danger" id="btn-rmdone" title="Delete all completed tasks">Delete done</button>
    <button class="tb-btn danger" id="btn-clear" title="Delete every task">Clear all</button>
  </div>
  <div class="tag-chip-bar" id="tag-chip-bar"></div>
</div>

<main id="main">
  <div id="search-results-area"></div>
  <div id="validate-area"></div>
  <div id="task-list-area">
    <div class="empty-state"><span class="glyph">&#9203;</span>Loading tasks&hellip;</div>
  </div>
</main>

<div class="add-bar">
  <form id="add-form" autocomplete="off">
    <span class="prompt">- [ ]</span>
    <input type="text" id="add-input" placeholder="Write report #work !3 @tomorrow /Section //Sub   (quick-capture tokens supported)">
    <button type="submit">Add</button>
  </form>
</div>

<div id="modal-root"></div>
<div class="toast" id="toast"></div>

<script>
const STATUS_CYCLE = { "[ ]": "[-]", "[-]": "[x]", "[x]": "[ ]" };
const STATUS_GLYPH  = { "[ ]": "\u2610", "[-]": "\u25D0", "[x]": "\u2611" };
let state = null;
let pollTimer = null;
let editCount = 0;       // >0 while any due-date input or task-name field is being edited
let pendingData = null;  // latest server snapshot received while an edit was in progress
let renderSeq = 0;       // monotonically increasing; guards against a slow/stale
                          // response overwriting a result that arrived after it

function beginEdit() { editCount++; }
function endEdit() {
  editCount = Math.max(0, editCount - 1);
  if (editCount === 0 && pendingData) {
    const data = pendingData;
    pendingData = null;
    render(data);
  }
}

function showToast(msg, isErr) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isErr ? ' err' : '');
  clearTimeout(t._hideTimer);
  t._hideTimer = setTimeout(() => t.classList.remove('show'), 2200);
}

async function api(path, method, body) {
  const opts = { method: method || 'GET' };
  if (body !== undefined) {
    opts.headers = { 'Content-Type': 'application/json' };
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || ('Request failed (' + res.status + ')'));
  return data;
}

function renderIfCurrent(data, mySeq) {
  // Only paint this result if nothing newer has already been requested —
  // protects against a slow response landing after a faster, later action.
  if (mySeq === renderSeq) render(data);
}

function escapeHtml(s) {
  return (s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderStats(stats) {
  const el = document.getElementById('stats-line');
  el.innerHTML =
    '<span class="stat">total <b>' + stats.total + '</b></span>' +
    '<span class="stat good">done <b>' + stats.done + '</b></span>' +
    '<span class="stat">in progress <b>' + stats.in_progress + '</b></span>' +
    '<span class="stat">todo <b>' + stats.todo + '</b></span>' +
    '<span class="stat ' + (stats.overdue > 0 ? 'warn' : '') + '">overdue <b>' + stats.overdue + '</b></span>' +
    '<span class="stat ' + (stats.due_today > 0 ? 'warn' : '') + '">due today <b>' + stats.due_today + '</b></span>' +
    '<span class="stat">' + stats.completion_rate + ' complete</span>';
}

function renderTaskRow(task) {
  const statusClass = task.status === '[x]' ? 'is-done' : (task.status === '[-]' ? 'is-progress' : '');
  const glyph = STATUS_GLYPH[task.status] || '\u2610';
  const dueClass = task.due ? ('due-' + task.urgency) : 'empty';
  const dueText = task.due ? escapeHtml(task.due) : '+ due';
  const tagsHtml = (task.tags || []).map(t =>
    '<span class="tag" data-tag="' + escapeHtml(t) + '">' + escapeHtml(t) + '<span class="tag-x" data-remove-tag="' + escapeHtml(t) + '">&times;</span></span>'
  ).join('') + '<span class="tag-add-btn" title="Add tag">+#</span>';
  const priEmpty = !task.pri;
  const priText = priEmpty ? '' : '!'.repeat(Math.min(task.pri, 5));

  return '' +
    '<div class="task-row ' + statusClass + '" data-id="' + task.id + '">' +
      '<button class="checkbox-btn" data-status="' + task.status + '" title="Click to change status">' + glyph + '</button>' +
      '<span class="task-id">' + escapeHtml(task.short_id) + '</span>' +
      '<span class="task-name" contenteditable="true" spellcheck="false" data-field="name">' + escapeHtml(task.name) + '</span>' +
      '<span class="task-tags" data-field="tags">' + tagsHtml + '</span>' +
      '<span class="task-due ' + dueClass + '" data-field="due">' + dueText + '</span>' +
      '<span class="task-pri' + (priEmpty ? ' empty' : '') + '" data-field="pri">' + priText + '</span>' +
      '<button class="menu-btn" data-menu-toggle title="More actions">&#8942;</button>' +
    '</div>';
}

let activeTagFilter = null;

function renderTagChipBar(tags) {
  const bar = document.getElementById('tag-chip-bar');
  const entries = Object.entries(tags || {});
  if (entries.length === 0) { bar.innerHTML = ''; return; }
  bar.innerHTML = entries.map(([name, count]) =>
    '<span class="tag-chip' + (activeTagFilter === name ? ' active' : '') + '" data-tag-filter="' + escapeHtml(name) + '">' +
      '#' + escapeHtml(name) + '<span class="count">' + count + '</span>' +
    '</span>'
  ).join('');
  bar.querySelectorAll('.tag-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const tag = chip.dataset.tagFilter;
      activeTagFilter = (activeTagFilter === tag) ? null : tag;
      renderTaskListArea(state);
      renderTagChipBar(state.tags);
    });
  });
}

function renderTaskListArea(data) {
  const area = document.getElementById('task-list-area');
  let sections = data.sections || {};

  if (activeTagFilter) {
    const filtered = {};
    for (const sec in sections) {
      for (const sub in sections[sec]) {
        const matches = sections[sec][sub].filter(t => (t.tags || []).includes(activeTagFilter));
        if (matches.length) {
          filtered[sec] = filtered[sec] || {};
          filtered[sec][sub] = matches;
        }
      }
    }
    sections = filtered;
  }

  const sectionNames = Object.keys(sections);
  if (sectionNames.length === 0) {
    const msg = activeTagFilter
      ? 'No tasks tagged #' + escapeHtml(activeTagFilter) + '.'
      : 'No tasks yet &mdash; add your first one below.';
    area.innerHTML = '<div class="empty-state"><span class="glyph">&#9633;</span>' + msg + '</div>';
    return;
  }

  let html = '';
  for (const sec of sectionNames) {
    const subs = sections[sec];
    let secDone = 0, secTotal = 0;
    for (const sub in subs) { for (const t of subs[sub]) { secTotal++; if (t.status === '[x]') secDone++; } }

    html += '<div class="section-header"><span class="hash">#</span><span class="name">' + escapeHtml(sec) +
            '</span><span class="progress">' + secDone + '/' + secTotal + '</span></div><hr class="section-rule">';
    for (const sub in subs) {
      html += '<div class="sub-header"><span class="hash">##</span><span class="name">' + escapeHtml(sub) + '</span></div>';
      for (const t of subs[sub]) html += renderTaskRow(t);
    }
  }
  area.innerHTML = html;
  attachRowHandlers();
}

function render(data) {
  state = data;
  renderStats(data.stats);
  renderTagChipBar(data.tags);
  renderTaskListArea(data);

  document.getElementById('file-path').textContent = (data.task_file || 'taskmd').split('/').pop();
  document.getElementById('last-sync').textContent = 'synced ' + new Date().toLocaleTimeString();
}

function attachRowHandlers() {
  document.querySelectorAll('.checkbox-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const row = btn.closest('.task-row');
      const id = row.dataset.id;
      const next = STATUS_CYCLE[btn.dataset.status] || '[ ]';
      const mySeq = ++renderSeq;
      try {
        flashRow(row);
        const data = await api('/api/tasks/' + id + '/status', 'POST', { status: next });
        renderIfCurrent(data, mySeq);
        showToast(next === '[x]' ? 'Marked done' : (next === '[-]' ? 'Marked in progress' : 'Marked todo'));
      } catch (e) { showToast(e.message, true); }
    });
  });

  document.querySelectorAll('.task-name').forEach(el => {
    el.addEventListener('focus', beginEdit);
    el.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); el.blur(); } });
    el.addEventListener('blur', async () => {
      const row = el.closest('.task-row');
      const id = row.dataset.id;
      const value = el.textContent.trim();
      if (!value) { el.textContent = '(unnamed)'; endEdit(); return; }
      try {
        const data = await api('/api/tasks/' + id + '/field', 'POST', { field: 'name', value: value });
        state = data;
        showToast('Saved');
      } catch (e) { showToast(e.message, true); }
      endEdit();
    });
  });

  document.querySelectorAll('.task-due').forEach(el => {
    el.addEventListener('click', () => {
      if (el.querySelector('input')) return;
      beginEdit();
      const row = el.closest('.task-row');
      const id = row.dataset.id;
      const current = (state.tasks.find(t => t.id === id) || {}).due || '';
      el.innerHTML = '<input type="text" value="' + escapeHtml(current) + '" placeholder="YYYY-MM-DD or YYYY-MM-DD HH:MM">';
      const input = el.querySelector('input');
      input.focus();
      input.select();
      let settled = false;

      const commit = async () => {
        if (settled) return;
        settled = true;
        const value = input.value.trim();
        const mySeq = ++renderSeq;
        try {
          const data = await api('/api/tasks/' + id + '/field', 'POST', { field: 'due', value: value || null });
          endEdit();
          renderIfCurrent(data, mySeq);
          showToast('Due date updated');
        } catch (e) {
          endEdit();
          showToast(e.message, true);
          renderIfCurrent(state, mySeq);
        }
      };
      const cancel = () => {
        if (settled) return;
        settled = true;
        endEdit();
        render(state);
      };
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); commit(); }
        if (e.key === 'Escape') { e.preventDefault(); cancel(); }
      });
      input.addEventListener('blur', commit);
    });
  });

  document.querySelectorAll('.task-pri').forEach(el => {
    el.addEventListener('click', () => {
      if (el.querySelector('input')) return;
      beginEdit();
      const row = el.closest('.task-row');
      const id = row.dataset.id;
      const current = (state.tasks.find(t => t.id === id) || {}).pri;
      el.innerHTML = '<input type="text" value="' + (current || '') + '" placeholder="0-5">';
      const input = el.querySelector('input');
      input.focus();
      input.select();
      let settled = false;

      const commit = async () => {
        if (settled) return;
        settled = true;
        const raw = input.value.trim();
        const mySeq = ++renderSeq;
        try {
          const data = await api('/api/tasks/' + id + '/field', 'POST', { field: 'pri', value: raw === '' ? null : raw });
          endEdit();
          renderIfCurrent(data, mySeq);
          showToast('Priority updated');
        } catch (e) {
          endEdit();
          showToast(e.message, true);
          renderIfCurrent(state, mySeq);
        }
      };
      const cancel = () => { if (settled) return; settled = true; endEdit(); render(state); };
      input.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); commit(); }
        if (e.key === 'Escape') { e.preventDefault(); cancel(); }
      });
      input.addEventListener('blur', commit);
    });
  });

  document.querySelectorAll('.task-tags').forEach(el => {
    el.querySelectorAll('[data-remove-tag]').forEach(x => {
      x.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        const row = el.closest('.task-row');
        const id = row.dataset.id;
        const tag = x.dataset.removeTag;
        const mySeq = ++renderSeq;
        try {
          const data = await api('/api/tasks/' + id + '/tags', 'POST', { action: 'rm', tag: tag });
          renderIfCurrent(data, mySeq);
          showToast('Removed #' + tag);
        } catch (e) { showToast(e.message, true); }
      });
    });
    const addBtn = el.querySelector('.tag-add-btn');
    if (addBtn) {
      addBtn.addEventListener('click', (ev) => {
        ev.stopPropagation();
        const row = el.closest('.task-row');
        const id = row.dataset.id;
        promptAddTag(id);
      });
    }
  });

  document.querySelectorAll('[data-menu-toggle]').forEach(btn => {
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const row = btn.closest('.task-row');
      const isOpen = row.querySelector('.action-menu');
      closeAllActionMenus();
      if (isOpen) return;
      openActionMenu(row);
    });
  });
}

function closeAllActionMenus() {
  document.querySelectorAll('.action-menu').forEach(m => m.remove());
}
document.addEventListener('click', closeAllActionMenus);

function openActionMenu(row) {
  const id = row.dataset.id;
  const menu = document.createElement('div');
  menu.className = 'action-menu';
  menu.innerHTML =
    '<button data-act="move">Move to section&hellip;</button>' +
    '<button data-act="tag">Add tag&hellip;</button>' +
    '<hr>' +
    '<button data-act="delete" class="danger">Delete task</button>';
  row.appendChild(menu);
  menu.addEventListener('click', (ev) => ev.stopPropagation());
  menu.querySelector('[data-act="move"]').addEventListener('click', () => { closeAllActionMenus(); openMoveDialog(id); });
  menu.querySelector('[data-act="tag"]').addEventListener('click', () => { closeAllActionMenus(); promptAddTag(id); });
  menu.querySelector('[data-act="delete"]').addEventListener('click', () => { closeAllActionMenus(); deleteTaskWithConfirm(id); });
}

function promptAddTag(id) {
  openModal({
    title: 'Add tag',
    bodyHtml: '<div class="modal-row" style="flex-direction:column;"><label>Tag name</label><input type="text" id="modal-tag-input" placeholder="e.g. urgent"></div>',
    confirmLabel: 'Add',
    onOpen: (box) => box.querySelector('#modal-tag-input').focus(),
    onConfirm: async (box) => {
      const tag = box.querySelector('#modal-tag-input').value.trim();
      if (!tag) return false;
      const data = await api('/api/tasks/' + id + '/tags', 'POST', { action: 'add', tag: tag });
      render(data);
      showToast('Added #' + tag);
      return true;
    },
  });
}

function openMoveDialog(id) {
  const task = (state.tasks || []).find(t => t.id === id);
  openModal({
    title: 'Move task',
    bodyHtml:
      '<div class="modal-row"><div style="flex:1;"><label>Section</label><input type="text" id="modal-section-input" value="' + escapeHtml(task ? task.section : '') + '"></div></div>' +
      '<div class="modal-row"><div style="flex:1;"><label>Subsection</label><input type="text" id="modal-sub-input" value="' + escapeHtml(task ? task.sub : '') + '"></div></div>',
    confirmLabel: 'Move',
    onOpen: (box) => box.querySelector('#modal-section-input').focus(),
    onConfirm: async (box) => {
      const section = box.querySelector('#modal-section-input').value.trim();
      const sub = box.querySelector('#modal-sub-input').value.trim();
      if (!section && !sub) return false;
      const data = await api('/api/tasks/' + id + '/move', 'POST', { section: section || null, sub: sub || null });
      render(data);
      showToast('Moved task');
      return true;
    },
  });
}

function deleteTaskWithConfirm(id) {
  const task = (state.tasks || []).find(t => t.id === id);
  openModal({
    title: 'Delete task?',
    bodyHtml: '<p>This will permanently delete &ldquo;' + escapeHtml(task ? task.name : '') + '&rdquo;.</p>',
    confirmLabel: 'Delete',
    danger: true,
    onConfirm: async () => {
      const data = await api('/api/tasks/' + id, 'DELETE');
      render(data);
      showToast('Task deleted');
      return true;
    },
  });
}

function openModal({ title, bodyHtml, confirmLabel, cancelLabel, danger, onOpen, onConfirm }) {
  const root = document.getElementById('modal-root');
  root.innerHTML =
    '<div class="modal-backdrop"><div class="modal-box">' +
      '<h3>' + escapeHtml(title) + '</h3>' +
      (bodyHtml || '') +
      '<div class="modal-actions">' +
        '<button class="btn-cancel" data-modal-cancel>' + escapeHtml(cancelLabel || 'Cancel') + '</button>' +
        '<button class="' + (danger ? 'btn-danger' : 'btn-confirm') + '" data-modal-confirm>' + escapeHtml(confirmLabel || 'OK') + '</button>' +
      '</div>' +
    '</div></div>';
  const backdrop = root.querySelector('.modal-backdrop');
  const box = root.querySelector('.modal-box');
  const close = () => { root.innerHTML = ''; };
  backdrop.addEventListener('click', (ev) => { if (ev.target === backdrop) close(); });
  box.querySelector('[data-modal-cancel]').addEventListener('click', close);
  const confirmBtn = box.querySelector('[data-modal-confirm]');
  confirmBtn.addEventListener('click', async () => {
    try {
      const ok = await onConfirm(box);
      if (ok !== false) close();
    } catch (e) { showToast(e.message, true); }
  });
  box.addEventListener('keydown', (ev) => {
    if (ev.key === 'Enter' && ev.target.tagName === 'INPUT') { ev.preventDefault(); confirmBtn.click(); }
    if (ev.key === 'Escape') close();
  });
  if (onOpen) onOpen(box);
}

function flashRow(row) {
  row.classList.add('flash');
  setTimeout(() => row.classList.remove('flash'), 350);
}

document.getElementById('add-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('add-input');
  const name = input.value.trim();
  if (!name) return;
  const mySeq = ++renderSeq;
  try {
    const data = await api('/api/tasks', 'POST', { name: name });
    input.value = '';
    renderIfCurrent(data, mySeq);
    if (data.capture_warnings && data.capture_warnings.length) {
      showToast(data.capture_warnings[0], true);
    } else {
      showToast('Task added');
    }
  } catch (err) { showToast(err.message, true); }
});

// ── Toolbar: validate / archive / delete-done / clear-all ─────────────────

document.getElementById('btn-validate').addEventListener('click', async () => {
  try {
    const data = await api('/api/validate');
    renderValidatePanel(data.errors || []);
  } catch (e) { showToast(e.message, true); }
});

function renderValidatePanel(errors) {
  const area = document.getElementById('validate-area');
  if (!errors.length) {
    area.innerHTML =
      '<div class="validate-panel clean"><span class="sr-clear" id="validate-close">close &times;</span>' +
      '&#10003; No issues found &mdash; the file is clean.</div>';
  } else {
    area.innerHTML =
      '<div class="validate-panel"><span class="sr-clear" id="validate-close">close &times;</span>' +
      errors.length + ' issue(s) found:<ul>' +
      errors.map(e => '<li>' + escapeHtml(e) + '</li>').join('') +
      '</ul></div>';
  }
  document.getElementById('validate-close').addEventListener('click', () => { area.innerHTML = ''; });
}

document.getElementById('btn-archive').addEventListener('click', () => {
  openModal({
    title: 'Archive completed tasks',
    bodyHtml: '<p>Moves every <strong>done</strong> task out of the active list and into the archive file, keeping your working list focused.</p>',
    confirmLabel: 'Archive',
    onConfirm: async () => {
      const data = await api('/api/bulk/archive', 'POST', {});
      render(data);
      const n = data.archived_count || 0;
      showToast(n > 0 ? ('Archived ' + n + ' task(s)') : 'No completed tasks to archive');
      return true;
    },
  });
});

document.getElementById('btn-rmdone').addEventListener('click', () => {
  openModal({
    title: 'Delete all completed tasks?',
    bodyHtml: '<p>This permanently removes every task marked done. This cannot be undone.</p>',
    confirmLabel: 'Delete done',
    danger: true,
    onConfirm: async () => {
      const data = await api('/api/bulk/rm_done', 'POST', {});
      render(data);
      const n = data.removed_count || 0;
      showToast(n > 0 ? ('Deleted ' + n + ' completed task(s)') : 'No completed tasks to delete');
      return true;
    },
  });
});

document.getElementById('btn-clear').addEventListener('click', () => {
  openModal({
    title: 'Clear ALL tasks?',
    bodyHtml: '<p><strong>This deletes every task in the file</strong>, not just completed ones. This cannot be undone.</p>',
    confirmLabel: 'Clear everything',
    danger: true,
    onConfirm: async () => {
      const data = await api('/api/bulk/clear', 'POST', { confirm: true });
      render(data);
      showToast('All tasks cleared');
      return true;
    },
  });
});

// ── Search ──────────────────────────────────────────────────────────────

let searchDebounce = null;
document.getElementById('search-input').addEventListener('input', (e) => {
  const q = e.target.value.trim();
  clearTimeout(searchDebounce);
  if (!q) {
    document.getElementById('search-results-area').innerHTML = '';
    document.getElementById('task-list-area').style.display = '';
    return;
  }
  searchDebounce = setTimeout(() => runSearch(q), 250);
});

async function runSearch(q) {
  try {
    const data = await api('/api/search?q=' + encodeURIComponent(q));
    renderSearchResults(q, data.results || []);
  } catch (e) { showToast(e.message, true); }
}

function renderSearchResults(query, results) {
  const area = document.getElementById('search-results-area');
  const listArea = document.getElementById('task-list-area');
  listArea.style.display = 'none';

  if (results.length === 0) {
    area.innerHTML =
      '<div class="search-results"><div class="sr-header"><span>No matches for &ldquo;' + escapeHtml(query) + '&rdquo;</span>' +
      '<span class="sr-clear" id="sr-clear-btn">clear &times;</span></div></div>';
  } else {
    area.innerHTML =
      '<div class="search-results"><div class="sr-header"><span>' + results.length + ' match(es) for &ldquo;' + escapeHtml(query) + '&rdquo;</span>' +
      '<span class="sr-clear" id="sr-clear-btn">clear &times;</span></div>' +
      results.map(renderTaskRow).join('') +
      '</div>';
    attachRowHandlers();
  }
  document.getElementById('sr-clear-btn').addEventListener('click', clearSearch);
}

function clearSearch() {
  document.getElementById('search-input').value = '';
  document.getElementById('search-results-area').innerHTML = '';
  document.getElementById('task-list-area').style.display = '';
}

async function poll() {
  const mySeq = ++renderSeq;
  try {
    const data = await api('/api/state');
    if (editCount > 0) {
      // Don't yank the DOM out from under an active edit (open due-date
      // input, or a task-name field mid-edit) — stash the snapshot and
      // apply it once the edit commits or cancels.
      pendingData = data;
      document.getElementById('last-sync').textContent = 'synced ' + new Date().toLocaleTimeString() + ' (editing\u2026)';
    } else {
      renderIfCurrent(data, mySeq);
    }
  } catch (e) {
    document.getElementById('last-sync').textContent = 'connection lost \u2014 retrying\u2026';
  } finally {
    pollTimer = setTimeout(poll, 1500);
  }
}

poll();
</script>
</body>
</html>
"""
