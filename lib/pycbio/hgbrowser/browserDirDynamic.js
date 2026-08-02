// Client code for pycbio BrowserDirDynamic pages, inlined into each generated
// dir.html.  Tabulator (from a CDN) is already loaded, and the per-page globals
// _colSpec, _tableData and _opts have been defined ahead of this code.

function _keySort(a, b, aRow, bRow, column, dir, params) {
    var x = aRow.getData()[params.field];
    var y = bRow.getData()[params.field];
    if (params.numeric) {
        x = parseFloat(x); y = parseFloat(y);
        if (isNaN(x)) x = -Infinity;
        if (isNaN(y)) y = -Infinity;
    }
    if (x === y) return 0;
    return (x > y) ? 1 : -1;
}
// A filter pattern is applied to every row, so compile it just once.  A
// pattern that will not compile is normally one that is still being typed, so
// it falls back to a literal substring match rather than matching nothing.
var _reCache = {};
function _patternRe(pattern) {
    if (!(pattern in _reCache)) {
        try {
            _reCache[pattern] = new RegExp(pattern, "i");
        } catch (e) {
            _reCache[pattern] = null;
        }
    }
    return _reCache[pattern];
}
function _textMatch(text, pattern) {
    var re = _opts.regexpFilters ? _patternRe(pattern) : null;
    if (re !== null) {
        return re.test(text);
    }
    return text.toLowerCase().indexOf(pattern.toLowerCase()) > -1;
}
function _colFilter(headerValue, rowValue, rowData, params) {
    return _textMatch("" + (rowData[params.field] || ""), "" + headerValue);
}
function _anySearch(data, params) {
    for (var i = 0; i < params.fields.length; i++) {
        if (_textMatch("" + (data[params.fields[i]] || ""), params.value)) return true;
    }
    return false;
}
function _dirToggleDesc() {
    var desc = document.getElementById("dirDesc");
    desc.hidden = !desc.hidden;
}
function _dirToggleHelp() {
    var help = document.getElementById("dirHelp");
    help.hidden = !help.hidden;
}
// Escape closes it too.  Not a click anywhere off it: the help is in the flow rather
// than over the table, so it hides nothing, and a stray click closing it while being
// read is worse than leaving it open.
document.addEventListener("keydown", function(ev) {
    if (ev.key === "Escape") {
        var help = document.getElementById("dirHelp");
        if (help) help.hidden = true;
        var desc = document.getElementById("dirDesc");
        if (desc) desc.hidden = true;
    }
});
function _rangeEditor(cell, onRendered, success, cancel, params) {
    var wrap = document.createElement("span");
    var lo = document.createElement("input");
    var hi = document.createElement("input");
    wrap.className = "dirRange";
    lo.type = hi.type = "number";
    lo.placeholder = "min";
    hi.placeholder = "max";
    function val() {
        return {min: lo.value === "" ? null : parseFloat(lo.value),
                max: hi.value === "" ? null : parseFloat(hi.value)};
    }
    // Tabulator's live filter calls success(editorElement.value); expose the
    // range object as the element's value so that path works, not just ours.
    Object.defineProperty(wrap, "value", {get: val});
    function commit() { success(val()); }
    function stop(e) { e.stopPropagation(); }
    function key(e) { if (e.key === "Escape") cancel(); e.stopPropagation(); }
    lo.addEventListener("input", commit);
    hi.addEventListener("input", commit);
    lo.addEventListener("keydown", key);
    hi.addEventListener("keydown", key);
    lo.addEventListener("mousedown", stop);
    hi.addEventListener("mousedown", stop);
    wrap.appendChild(lo);
    wrap.appendChild(hi);
    return wrap;
}
function _rangeFilter(headerValue, rowValue, rowData, params) {
    var n = rowData[params.field];
    if (n === null || n === undefined || n === "") return false;
    n = parseFloat(n);
    if (isNaN(n)) return false;
    if (headerValue.min !== null && n < headerValue.min) return false;
    if (headerValue.max !== null && n > headerValue.max) return false;
    return true;
}
function _rangeEmpty(value) {
    return (value == null) || (value.min == null && value.max == null);
}
function _fontOf(el, fallback) {
    if (!el) return fallback;
    var cs = getComputedStyle(el);
    return cs.fontStyle + " " + cs.fontWeight + " " + cs.fontSize + " " + cs.fontFamily;
}
function _maxDataWidth(ctx, field) {
    var w = 0;
    for (var i = 0; i < _tableData.length; i++) {
        var t = _tableData[i][field];
        var cw = ctx.measureText(t == null ? "" : ("" + t)).width;
        if (cw > w) w = cw;
    }
    return w;
}
// Apply a measured fit width.  An expanding column keeps flexing, with the
// measured size as its floor; a plain fit column is pinned to it.  Both the
// definition and the live column must be set: the layout reads the definition
// (a column with a width is excluded from the flex pool, and minWidth is read
// off the column), but only setWidth/setMinWidth resize what is rendered.
//
// EVERY fit column also gets the measured size as its minWidth, pinned or not.
// Without it the layout still shrinks a pinned column when the columns do not
// fit the window, and the content does not shrink with it: a wrapped cell has
// overflow visible, so its text runs over the next column, and a plain cell
// loses characters to the ellipsis.  The measured size is what the content
// needs, so it is the floor.
function _setFitWidth(col, spec, need) {
    col.getDefinition().minWidth = need;
    col._getSelf().setMinWidth(need);
    if (!spec.grow) {
        col.getDefinition().width = need;
        col.setWidth(need);
    }
}
// The lines a wrapped cell actually renders as: its content split at the breaks
// it carries, with the markup taken out.  Measuring the whole cell instead would
// size the column to every line laid end to end, which is the opposite of
// wrapping; measuring the plain text field would miss the breaks, since they are
// markup and the text field has none.
function _htmlLines(value) {
    return ("" + value).split(/<br\s*\/?>/i).map(function(s) {
        return s.replace(/<[^>]*>/g, "").replace(/&nbsp;/g, " ")
                .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
    });
}
function _maxLineWidth(ctx, field) {
    var w = 0;
    for (var i = 0; i < _tableData.length; i++) {
        var lines = _htmlLines(_tableData[i][field] == null ? "" : _tableData[i][field]);
        for (var j = 0; j < lines.length; j++) {
            var lw = ctx.measureText(lines[j]).width;
            if (lw > w) w = lw;
        }
    }
    return w;
}
function _maxWordWidth(ctx, text) {
    var words = ("" + text).split(" ");
    var w = 0;
    for (var i = 0; i < words.length; i++) {
        var ww = ctx.measureText(words[i]).width;
        if (ww > w) w = ww;
    }
    return w;
}
// Size each fit column to the widest of its data and its header.  The header
// word-wraps, so what must fit on a line is its longest single word, not the
// whole title.  A fit column that also expands gets the measured size as its
// minWidth, not a fixed width: a column with a definition width is excluded
// from the fitColumns flex pool, so giving an expanding column a width would
// stop it absorbing slack (and leave the table with no flexible column).
function _fitColumnWidths() {
    var fits = _colSpec.filter(function(c) { return c.fit; });
    if (!fits.length) return;
    var el = _dirTable.element;
    var cellFont = _fontOf(el.querySelector(".tabulator-cell"), "14px sans-serif");
    var hdrFont = _fontOf(el.querySelector(".tabulator-col-title"), cellFont);
    var ctx = document.createElement("canvas").getContext("2d");
    fits.forEach(function(c) {
        ctx.font = cellFont;
        // a wrap column fits its longest LINE -- what has to fit across is one
        // line of the cell, not the cell
        var data = c.wrap ? _maxLineWidth(ctx, c.field)
                          : _maxDataWidth(ctx, c.textField);
        ctx.font = hdrFont;
        var header = c.headerWrap ? _maxWordWidth(ctx, c.title)
                                  : ctx.measureText(c.title).width;
        // cell: 4+4 padding + 1 border; header also reserves the 25px sort
        // arrow space (padding-right) plus the 4+4 content padding + border
        var need = Math.max(data + 9, header + 34);
        if (c.filter === "range") need = Math.max(need, 70);
        var col = _dirTable.getColumn(c.field);
        if (col) _setFitWidth(col, c, Math.ceil(need));
    });
    _dirTable.redraw(true);
}

// ---- build the table from the per-page globals ----

var _columns = _colSpec.map(function(c) {
    var col = {title: c.title, field: c.field, formatter: "html",
               sorter: _keySort,
               sorterParams: {field: c.sortField, numeric: !!c.numericSort}};
    if (_opts.headerFilters && c.filter !== "none") {
        if (c.filter === "range") {
            col.headerFilter = _rangeEditor;
            col.headerFilterFunc = _rangeFilter;
            col.headerFilterFuncParams = {field: c.numberField};
            col.headerFilterEmptyCheck = _rangeEmpty;
        } else {
            col.headerFilter = "input";
            col.headerFilterFunc = _colFilter;
            col.headerFilterFuncParams = {field: c.textField};
        }
    }
    // one class, not two: Tabulator's cssClass splitting is its business, and a
    // wrap column differs only in whether a token may be broken to fit
    if (c.wrap) col.cssClass = (c.breakWords === false) ? "dirWrapKeep" : "dirWrap";
    if (c.headerWrap) col.headerWordWrap = true;
    if ("align" in c) col.hozAlign = c.align;               // data cells
    if ("headerAlign" in c) col.headerHozAlign = c.headerAlign;
    if ("width" in c) col.width = c.width;       // fixed; does not flex
    if ("minWidth" in c) col.minWidth = c.minWidth;
    if ("grow" in c) col.widthGrow = c.grow;
    // no widthShrink for fit columns: with fitColumns, shrinking only ever
    // engages when there is space left over (the layout takes |gap| + leftover
    // as overflow), so it narrowed the table as the window widened instead of
    // giving space back when it was too narrow
    if ("shrink" in c) col.widthShrink = c.shrink;
    return col;
});
var _currentId = null;
var _config = {data: _tableData, columns: _columns, layout: _opts.layout,
               height: "100%", index: "_id",
               // dragging a column edge moves the NEXT column's edge with it, so
               // the table still ends at the window edge.  Without this, widening
               // one column pushes the rest off to the right and narrowing one
               // leaves blank space where the table used to reach.
               resizableColumnFit: true,
               rowFormatter: function(row) {
                   var el = row.getElement();
                   var data = row.getData();
                   if (data._cls) el.classList.add(data._cls);
                   if (data._id === _currentId) {
                       el.classList.add("dirCurrent");
                   } else {
                       el.classList.remove("dirCurrent");
                   }
               }};
for (var k in _opts.extra) { _config[k] = _opts.extra[k]; }
var _dirTable = new Tabulator("#dirTable", _config);
// Tabulator 6 requires event callbacks to be registered via on(), not as
// constructor options.  Highlight the row whose link was last clicked.
function _dirSetCurrent(e, row) {
    if (!e.target.closest("a")) return;
    var prevId = _currentId;
    _currentId = row.getData()._id;
    if (prevId !== null) {
        var prev = _dirTable.getRow(prevId);
        if (prev) prev.reformat();
    }
    row.reformat();
}
_dirTable.on("rowClick", _dirSetCurrent);
_dirTable.on("tableBuilt", _fitColumnWidths);

// A column drag that leaves this document never ends: the resize listens for
// mouseup on the document, and once the pointer is over a DIFFERENT frame -- the
// browser image beside the directory, or the page outside it -- that is where the
// mouseup lands.  The column then follows the mouse until the next click in here.
// Dragging past the rightmost edge is how it happens, since the pointer leaves at
// the one edge a resize handle sits on.  Ending the drag when the pointer goes is
// what the missing mouseup would have done.
var _dirDragging = false;
document.addEventListener("mousedown", function() { _dirDragging = true; });
document.addEventListener("mouseup", function() { _dirDragging = false; });
function _dirEndDrag() {
    if (_dirDragging) {
        _dirDragging = false;
        document.dispatchEvent(new MouseEvent("mouseup", {bubbles: true, cancelable: true}));
    }
}
document.documentElement.addEventListener("mouseleave", _dirEndDrag);
window.addEventListener("blur", _dirEndDrag);

// Give the table back to the frame when the frame changes size.  Tabulator sizes
// its scrolling area in PIXELS when it is built; the containing div is a flex
// item and grows, but the table inside keeps the height it was born with, so
// dragging the frameset divider to make the directory taller just adds blank
// space under the table.  A redraw recomputes it.
//
// Plain redraw(), not redraw(true): the height is all that has to be recomputed,
// and a full redraw would also throw away the column widths the reader dragged.
// Both signals, since neither covers the other: a frameset divider need not
// raise a window resize, and a window resize need not change this element's box.
// Debounced, and the observer only fires on a height it has not already handled,
// so a redraw cannot feed itself.
var _dirResizeTimer = null;
function _dirRelayout() {
    if (_dirResizeTimer !== null) clearTimeout(_dirResizeTimer);
    _dirResizeTimer = setTimeout(function() {
        _dirResizeTimer = null;
        _dirTable.redraw();
    }, 60);
}
window.addEventListener("resize", _dirRelayout);
if (window.ResizeObserver) {
    var _dirLastHeight = 0;
    new ResizeObserver(function(entries) {
        var h = Math.round(entries[0].contentRect.height);
        if (h !== _dirLastHeight) {
            _dirLastHeight = h;
            _dirRelayout();
        }
    }).observe(document.getElementById("dirTable"));
}
var _searchFields = _colSpec.map(function(c) { return c.textField; });
function _dirGlobalSearch() {
    var v = document.getElementById("dirSearch").value;
    if (v === "") {
        _dirTable.clearFilter();
    } else {
        _dirTable.setFilter(_anySearch, {fields: _searchFields, value: v});
    }
}
