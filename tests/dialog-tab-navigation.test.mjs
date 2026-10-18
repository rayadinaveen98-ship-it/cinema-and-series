import test from "node:test";
import assert from "node:assert/strict";
import { nextDialogTabTarget } from "../src/dialog-tab-navigation.ts";

test("Tab wraps from final modal action to the first", () => {
  assert.equal(nextDialogTabTarget(2, 3, false), 0);
  assert.equal(nextDialogTabTarget(1, 3, false), null);
});
test("Shift+Tab wraps from first modal action to the last", () => {
  assert.equal(nextDialogTabTarget(0, 3, true), 2);
  assert.equal(nextDialogTabTarget(1, 3, true), null);
});
test("Tab starting outside modal cannot escape modal", () => {
  assert.equal(nextDialogTabTarget(-1, 3, false), 0);
  assert.equal(nextDialogTabTarget(-1, 3, true), 2);
  assert.equal(nextDialogTabTarget(12, 3, false), 0);
});
test("Single or empty modal action lists remain trapped", () => {
  assert.equal(nextDialogTabTarget(0, 1, false), 0);
  assert.equal(nextDialogTabTarget(0, 1, true), 0);
  assert.equal(nextDialogTabTarget(-1, 0, false), -1);
  assert.equal(nextDialogTabTarget(-1, 0, true), -1);
});
