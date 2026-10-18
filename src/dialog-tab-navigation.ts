/** Pure focus-boundary decision used by the movie and series modal focus trap.
 * Returns a target index, -1 for the dialog container, or null if native Tab
 * navigation can continue to the next focusable element.
 */
export function nextDialogTabTarget(activeIndex: number, focusableCount: number, backwards: boolean): number | null {
  if (focusableCount <= 0) return -1;
  if (activeIndex < 0 || activeIndex >= focusableCount) return backwards ? focusableCount - 1 : 0;
  if (backwards && activeIndex === 0) return focusableCount - 1;
  if (!backwards && activeIndex === focusableCount - 1) return 0;
  return null;
}
