// viewer.js: draws Figures 1 and 2 of history-of-hash-function-attacks.md
// as year-by-year coloured timelines, after Markdeep has rendered the page.
//
// Load order in the page: this file first, then markdeep.min.js. Markdeep
// calls window.markdeepOptions.onLoad once the page is rendered.
//
// Input (contract): the first table whose header starts "hash | designed".
// Each row is: hash, designed year, bits, cpb, collisions, pre-images. The
// last two cells hold a chain of transitions "<dot> <year> [refs] → ...",
// where <dot> is one of 🟢 🟡 🟠 🔴, or a lone 🟢 for "never broken".
// The grid's last column is the year in the page's "Date:" line.
'use strict';

// Fill colours are muted so dark text reads on them; EDGE marks a transition.
var COLOUR = { '🟢': '#cfe8c3', '🟡': '#f7e8a4', '🟠': '#f6c994', '🔴': '#f0a8a0' };
var EDGE   = { '🟢': '#5d9c54', '🟡': '#c9a92e', '🟠': '#d0802c', '🔴': '#c4463a' };
var BRUTE_FORCE_BITS = 160; // collision search on this many bits or fewer may be feasible

function fail(msg) { throw new Error('viewer.js: ' + msg); }

function cellText(cell) { return cell.textContent.replace(/\s+/g, ' ').trim(); }

// "🟡 1989 [21] → 🔴 2010 [45]" -> [{dot, year, refs:[<a>...]}, ...]
// A lone "🟢" means no transition.
function parseTransitions(cell) {
  var segments = [];
  var current = null;
  var re = /(🟢|🟡|🟠|🔴)\s*(\d{4})?/g;
  // Walk every descendant in document order: Markdeep may nest the links.
  var walker = document.createTreeWalker(cell, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  for (var node = walker.nextNode(); node; node = walker.nextNode()) {
    if (node.tagName === 'A') {
      if (current) current.refs.push(node.cloneNode(true));
    } else if (node.nodeType === Node.TEXT_NODE && !node.parentNode.closest('a')) {
      var m;
      while ((m = re.exec(node.textContent)) !== null) {
        if (m[2] === undefined) { current = null; continue; } // lone 🟢
        current = { dot: m[1], year: +m[2], refs: [] };
        segments.push(current);
      }
    }
  }
  return segments;
}

function findTransitionsTable() {
  var tables = document.getElementsByTagName('table');
  for (var i = 0; i < tables.length; ++i) {
    var h = tables[i].rows[0] && tables[i].rows[0].cells;
    if (h && cellText(h[0]) === 'hash' && cellText(h[1]) === 'designed') return tables[i];
  }
  fail('transitions table (header "hash | designed | ...") missing');
}

function lastYear() {
  var m = /Date:\D*(\d{4})/.exec(document.body.textContent);
  if (!m) fail('"Date:" line missing');
  return +m[1];
}

function buildGrid(caption, rows, column, firstYear, lastYear, colourBits) {
  var table = document.createElement('table');
  table.className = 'timeline';
  table.createCaption().textContent = caption;

  var head = table.createTHead().insertRow();
  ['hash', 'bits', 'cpb'].forEach(function (t) { head.appendChild(document.createElement('th')).textContent = t; });
  for (var y = firstYear; y <= lastYear; ++y) {
    var th = head.appendChild(document.createElement('th'));
    th.textContent = "'" + String(y).slice(2);
    if (y % 10 === 0) th.className = 'decade';
  }

  var body = table.createTBody();
  rows.forEach(function (r) {
    var designed = +cellText(r.cells[1]);
    var bits = +cellText(r.cells[2]);
    var transitions = parseTransitions(r.cells[column]);
    var tr = body.insertRow();
    var hashCell = tr.insertCell();
    r.cells[0].childNodes.forEach(function (n) { hashCell.appendChild(n.cloneNode(true)); });
    var bitsCell = tr.insertCell();
    bitsCell.textContent = bits;
    if (colourBits && bits <= BRUTE_FORCE_BITS) {
      bitsCell.style.background = COLOUR['🟠'];
      bitsCell.style.color = '#5a3a10';
      bitsCell.title = 'brute force may be feasible at this output size';
    }
    tr.insertCell().textContent = cellText(r.cells[3]);

    var name = cellText(r.cells[0]);
    var dot = null;
    for (var y = firstYear; y <= lastYear; ++y) {
      var td = tr.insertCell();
      if (y % 10 === 0) td.className = 'decade';
      td.title = name + ', ' + y;
      if (y < designed) { td.classList.add('empty'); continue; }
      if (y === designed) dot = '🟢';
      transitions.forEach(function (t) {
        if (t.year === y) {
          dot = t.dot;
          td.style.boxShadow = 'inset 3px 0 ' + EDGE[dot];
          t.refs.forEach(function (a) { td.appendChild(a); });
        }
      });
      td.style.background = COLOUR[dot];
    }
  });
  // Column highlight follows the cursor; the row highlight is CSS :hover.
  var lit = [];
  table.addEventListener('mouseover', function (e) {
    var td = e.target.closest('td');
    if (!td || td.cellIndex < 3) return;
    lit.forEach(function (el) { el.classList.remove('col'); });
    lit = [head.cells[td.cellIndex]];
    Array.from(body.rows).forEach(function (row) { lit.push(row.cells[td.cellIndex]); });
    lit.forEach(function (el) { el.classList.add('col'); });
  });
  table.addEventListener('mouseleave', function () {
    lit.forEach(function (el) { el.classList.remove('col'); });
    lit = [];
  });
  return table;
}

// Replace each emoji dot in the page's text with a swatch of the same palette,
// so the legend and the grids show the same colours.
function swatchDots(root) {
  var re = /(🟢|🟡|🟠|🔴)/;
  var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  var nodes = [];
  for (var n = walker.nextNode(); n; n = walker.nextNode()) if (re.test(n.textContent)) nodes.push(n);
  nodes.forEach(function (n) {
    var frag = document.createDocumentFragment();
    n.textContent.split(re).forEach(function (part) {
      if (COLOUR[part]) {
        var sw = document.createElement('span');
        sw.className = 'dot';
        sw.style.background = COLOUR[part];
        sw.style.boxShadow = 'inset 0 0 0 1px ' + EDGE[part];
        frag.appendChild(sw);
      } else if (part) {
        frag.appendChild(document.createTextNode(part));
      }
    });
    n.parentNode.replaceChild(frag, n);
  });
}

// Give each reference link ([21], [‡]) a tooltip holding its bibliography
// entry or note, read from the anchor the link points at.
function tooltipRefs(root) {
  root.querySelectorAll('a[href^="#ref-"], a[href^="#note-"]').forEach(function (a) {
    var target = document.getElementById(a.getAttribute('href').slice(1));
    if (!target) fail('link target ' + a.getAttribute('href') + ' missing');
    a.title = target.parentNode.textContent.replace(/\s+/g, ' ').trim();
  });
}

function draw() {
  var source = findTransitionsTable();
  // Markdeep keeps the header row inside <tbody>; data rows have a numeric year.
  var rows = Array.from(source.rows).filter(function (r) { return /^\d{4}$/.test(cellText(r.cells[1])); });
  if (rows.length === 0) fail('transitions table has no data rows');
  var first = Math.min.apply(null, rows.map(function (r) { return +cellText(r.cells[1]); }));
  var last = lastYear();

  var style = document.createElement('style');
  var T = '.md .timeline';
  style.textContent =
    T + '{border-collapse:separate;border-spacing:1px;font-size:80%;margin:1.5em 0;line-height:1.5}' +
    T + ' caption{font-style:italic;text-align:left;padding-bottom:.4em}' +
    T + ' th{font-weight:normal;color:#777;padding:0 .15em;text-align:center;vertical-align:bottom;border:0;background:none}' +
    T + ' th.decade{font-weight:bold;color:#333}' +
    T + ' th:nth-child(-n+3){color:#333;text-align:left}' +
    T + ' td{padding:0 .15em;text-align:center;min-width:1.6em;white-space:nowrap;border:0}' +
    T + ' td:nth-child(-n+3){text-align:left;padding:0 .5em 0 .2em;color:#333}' +
    T + ' td:nth-child(2),' + T + ' td:nth-child(3){color:#666;font-variant-numeric:tabular-nums}' +
    T + ' td.decade{border-left:1px solid rgba(0,0,0,.18)}' +
    T + ' a{font-size:75%;color:#222;text-decoration:none;opacity:.8}' +
    T + ' a:hover{text-decoration:underline;opacity:1}' +
    T + ' tbody tr:hover td,' + T + ' td.col{filter:brightness(.93)}' +
    T + ' td.col.empty,' + T + ' tbody tr:hover td.empty{background:#ececec}' +
    T + ' th.col{color:#111;font-weight:bold}' +
    T + ' tbody tr:hover td.col{outline:2px solid #333;outline-offset:-1px;filter:brightness(.88)}' +
    '.dot{display:inline-block;width:.8em;height:.8em;border-radius:.15em;vertical-align:-.05em;margin:0 .1em}';
  document.head.appendChild(style);

  var fig1 = buildGrid('Figure 1: Chronological view of collision attacks', rows, 4, first, last, true);
  var fig2 = buildGrid('Figure 2: Chronological view of (second-)pre-image attacks', rows, 5, first, last, false);

  var details = document.createElement('details');
  details.appendChild(document.createElement('summary')).textContent = 'the same history, as a list of transitions';
  source.parentNode.insertBefore(fig1, source);
  source.parentNode.insertBefore(fig2, source);
  source.parentNode.insertBefore(details, source);
  details.appendChild(source);
  swatchDots(document.body);
  tooltipRefs(document.body);
}

window.markdeepOptions = window.markdeepOptions || {};
window.markdeepOptions.onLoad = draw;
