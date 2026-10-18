import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
const css = readFileSync(new URL("../src/app-v2.css", import.meta.url), "utf8");

test("Both detail dialogs have accessible titles, close labels and modal focus hooks", () => {
  assert.equal((app.match(/aria-modal="true" aria-labelledby=\{titleId\}/g) ?? []).length, 2);
  assert.equal((app.match(/ref=\{dialogRef\} tabIndex=\{-1\}/g) ?? []).length, 2);
  assert.match(app, /aria-label="Close movie details"/);
  assert.match(app, /aria-label="Close series details"/);
  assert.equal((app.match(/<h2 id=\{titleId\}>/g) ?? []).length, 2);
  assert.match(app, /document\.addEventListener\("focusin", onFocus\)/);
  assert.match(app, /previousFocus\?\.isConnected/);
});

test("Searches and filter panels expose explicit accessible names and state", () => {
  assert.match(app, /htmlFor=\{searchId\}>Search movies/);
  assert.match(app, /htmlFor=\{searchId\}>Search series/);
  assert.equal((app.match(/type="search"/g) ?? []).length, 2);
  assert.match(app, /aria-expanded=\{open\} aria-controls=\{controlsId\}/);
  assert.equal((app.match(/id=\{filterPanelId\} hidden=\{!filterOpen\}/g) ?? []).length, 2);
  assert.match(css, /\.filter-panel\[hidden\]\{display:none!important\}/);
});

test("Mobile controls have visible focus and readable tap targets", () => {
  assert.match(css, /:focus-visible\{outline:3px solid/);
  assert.match(css, /\.modal-close\{width:44px;height:44px\}/);
  assert.match(css, /\.mobile-nav-v2 small\{font-size:12px/);
  assert.match(css, /\.media-copy strong\{display:-webkit-box/);
});
