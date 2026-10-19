import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { ANDROID_BACK_EVENT, consumeAndroidBack } from "../src/android-back.ts";

test("Android Back is consumed once by an open dialog", () => {
  const event = new Event(ANDROID_BACK_EVENT, { cancelable: true });
  const calls = [];
  assert.equal(consumeAndroidBack(event, () => calls.push("detail")), true);
  assert.equal(event.defaultPrevented, true);
  assert.equal(consumeAndroidBack(event, () => calls.push("filter")), false);
  assert.deepEqual(calls, ["detail"]);
});

test("Blocked filters and absent dialogs defer Back to navigation", () => {
  const blocked = new Event(ANDROID_BACK_EVENT, { cancelable: true });
  assert.equal(consumeAndroidBack(blocked, () => assert.fail("filter must not close"), true), false);
  assert.equal(blocked.defaultPrevented, false);
  let closed = 0;
  assert.equal(consumeAndroidBack(blocked, () => closed++), true);
  assert.equal(closed, 1);
});

test("Uncancelable events cannot silently intercept native Back", () => {
  const event = new Event(ANDROID_BACK_EVENT);
  assert.equal(consumeAndroidBack(event, () => assert.fail("unexpected close")), false);
  assert.equal(event.defaultPrevented, false);
});

test("Dialog and filters subscribe to the same cancelable event and clean up listeners", () => {
  const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
  assert.match(app, /document\.addEventListener\(ANDROID_BACK_EVENT, onAndroidBack\)/);
  assert.match(app, /document\.removeEventListener\(ANDROID_BACK_EVENT, onAndroidBack\)/);
  assert.match(app, /document\.addEventListener\(ANDROID_BACK_EVENT, onBack\)/);
  assert.match(app, /document\.removeEventListener\(ANDROID_BACK_EVENT, onBack\)/);
  assert.match(app, /const modalOpen = Boolean\(document\.querySelector/);
  assert.equal((app.match(/useAndroidFilterBack\(filterOpen,/g) || []).length, 2);
});

test("Android wrapper dispatches Back before history without a JS-to-native bridge", () => {
  const java = readFileSync(new URL("../android-app/app/src/main/java/com/cinemaandseries/app/MainActivity.java", import.meta.url), "utf8");
  assert.match(java, /new Event\('cinema-android-back',\{cancelable:true\}\)/);
  assert.match(java, /return e\.defaultPrevented/);
  assert.match(java, /webView\.evaluateJavascript\(WEB_BACK_EVENT/);
  assert.match(java, /if \(!"true"\.equals\(result\)\) backThroughHistoryOrFinish\(\)/);
  assert.match(java, /request\.isForMainFrame\(\)/);
  assert.match(java, /showLoadFailure\(\)/);
  assert.match(java, /retry\.setOnClickListener/);
  assert.match(java, /registerOnBackInvokedCallback\(/);
  assert.match(java, /unregisterOnBackInvokedCallback\(/);
  assert.match(java, /Build.VERSION_CODES.TIRAMISU/);
  assert.match(java, /private void handleBack\(\)/);
  assert.doesNotMatch(java, /addJavascriptInterface\(/);
});
