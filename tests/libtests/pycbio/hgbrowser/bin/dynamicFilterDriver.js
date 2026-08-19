// Run the JavaScript of a generated BrowserDirDynamic page under node and report
// what it built, so the client code is tested rather than only text-compared.
//
// The page's script is data (_colSpec, _tableData, _opts) followed by the client
// code, and the client code ends by constructing a Tabulator.  Stubbing that
// constructor is what hands us the column definitions and the row data it was built
// with, without depending on how eval scopes the page's own variables.
//
// usage: node dynamicFilterDriver.js DIR_HTML
"use strict";
const fs = require("fs");

// the value standing for "no value" in a select filter, as browserDirDynamic.js
// defines it; the choice carrying it is the empty choice
const EMPTY = String.fromCharCode(0);

function pageScript(htmlFile) {
    const html = fs.readFileSync(htmlFile, "utf8");
    const start = html.indexOf("var _colSpec");
    const end = html.indexOf("</script>", start);
    if (start < 0 || end < 0) {
        throw new Error("no page script found in " + htmlFile);
    }
    return html.slice(start, end);
}

// the browser objects the client code touches as it loads; none has to behave, since
// every path that uses them is an event callback that never fires here
function installStubs() {
    const element = {hidden: true, value: "", addEventListener: function() {}};
    globalThis.document = {
        addEventListener: function() {},
        dispatchEvent: function() {},
        getElementById: function() { return element; },
        createElement: function() { return element; },
        documentElement: {addEventListener: function() {}},
    };
    globalThis.window = {addEventListener: function() {}};
    globalThis.MouseEvent = function() {};
    globalThis.Tabulator = function(selector, config) { globalThis._built = config; };
    globalThis.Tabulator.prototype.on = function() {};
}

function filterDesc(col) {
    if (col.headerFilter === undefined) return "none";
    if (typeof col.headerFilter === "function") return "function";
    let desc = col.headerFilter;
    const params = col.headerFilterParams;
    if (params) {
        if (params.multiselect) desc += " multiselect";
        if (params.clearable) desc += " clearable";
    }
    return desc;
}

function choiceName(choice) {
    return (choice.value === EMPTY) ? choice.label + "(empty)" : choice.label;
}

function keptRows(col, data, picked) {
    return data.filter(function(row) {
        return col.headerFilterFunc(picked, null, row, col.headerFilterFuncParams);
    }).length;
}

// each select column against its own choices: the first alone, the first with the
// last, and the empty choice when the column offers one; then nothing picked, which
// the empty check has to read as no filter at all
function reportSelect(col, data) {
    const choices = col.headerFilterParams.values;
    const values = choices.map(function(c) { return c.value; });
    console.log("  " + col.title + " choices: " + choices.map(choiceName).join(", "));
    const plain = values.filter(function(v) { return v !== EMPTY; });
    const cases = [[plain[0]], [plain[0], plain[plain.length - 1]]];
    if (values.indexOf(EMPTY) >= 0) {
        cases.push([EMPTY], [EMPTY, plain[0]]);
    }
    cases.forEach(function(picked) {
        const names = picked.map(function(v) { return (v === EMPTY) ? "<empty>" : v; });
        console.log("    picked [" + names.join(", ") + "] keeps "
                    + keptRows(col, data, picked) + " rows");
    });
    console.log("    nothing picked is no filter: " + col.headerFilterEmptyCheck([]));
}

installStubs();
eval(pageScript(process.argv[2]));
const built = globalThis._built;
console.log("rows: " + built.data.length);
console.log("header filters:");
built.columns.forEach(function(col) {
    console.log("  " + col.title + ": " + filterDesc(col));
});
console.log("select columns:");
built.columns.filter(function(col) {
    return col.headerFilterParams && col.headerFilterParams.multiselect;
}).forEach(function(col) { reportSelect(col, built.data); });
