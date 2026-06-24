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

.task-row {
  display: grid;
  grid-template-columns: 22px 30px 1fr auto auto auto;
  align-items: center;
  gap: 8px;
  padding: 3px 8px 3px 18px;
  margin: 1px 0;
  border-radius: 4px;
  transition: background 0.15s ease;
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
.task-due input {
  font-family: inherit; font-size: 12px; width: 130px;
  border: 1px solid var(--focus); border-radius: 3px; padding: 1px 4px;
  background: #fff; color: var(--ink);
}

.task-pri { color: var(--amber); font-size: 12px; letter-spacing: -1px; min-width: 28px; text-align: right; }

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
  .task-row { grid-template-columns: 20px 26px 1fr; }
  .task-due, .task-pri, .task-tags { grid-column: 3; margin-left: 0; }
  .task-tags { display: none; }
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
</div>

<main id="main">
  <div class="empty-state"><span class="glyph">&#9203;</span>Loading tasks&hellip;</div>
</main>

<div class="add-bar">
  <form id="add-form" autocomplete="off">
    <span class="prompt">- [ ]</span>
    <input type="text" id="add-input" placeholder="Write report #work !3 @tomorrow   (quick-capture tokens supported)">
    <button type="submit">Add</button>
  </form>
</div>

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
  const dueClass = task.due ? ('due-' + task.urgency) : '';
  const dueText = task.due ? escapeHtml(task.due) : '+ due';
  const tagsHtml = (task.tags || []).map(t => '<span class="tag">' + escapeHtml(t) + '</span>').join('');
  const priText = task.pri ? '!'.repeat(Math.min(task.pri, 5)) : '';

  return '' +
    '<div class="task-row ' + statusClass + '" data-id="' + task.id + '">' +
      '<button class="checkbox-btn" data-status="' + task.status + '" title="Click to change status">' + glyph + '</button>' +
      '<span class="task-id">' + escapeHtml(task.short_id) + '</span>' +
      '<span class="task-name" contenteditable="true" spellcheck="false" data-field="name">' + escapeHtml(task.name) + '</span>' +
      '<span class="task-tags">' + tagsHtml + '</span>' +
      '<span class="task-due ' + dueClass + '" data-field="due">' + dueText + '</span>' +
      '<span class="task-pri">' + priText + '</span>' +
    '</div>';
}

function render(data) {
  state = data;
  renderStats(data.stats);

  const main = document.getElementById('main');
  const sections = data.sections || {};
  const sectionNames = Object.keys(sections);

  document.getElementById('file-path').textContent = (data.task_file || 'taskmd').split('/').pop();
  document.getElementById('last-sync').textContent = 'synced ' + new Date().toLocaleTimeString();

  if (sectionNames.length === 0) {
    main.innerHTML = '<div class="empty-state"><span class="glyph">&#9633;</span>No tasks yet &mdash; add your first one below.</div>';
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
  main.innerHTML = html;
  attachRowHandlers();
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
    showToast('Task added');
  } catch (err) { showToast(err.message, true); }
});

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
