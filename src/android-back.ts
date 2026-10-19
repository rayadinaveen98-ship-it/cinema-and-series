/**
 * Android WebView dispatches this cancelable DOM event before falling back
 * to its own navigation stack. A visible sheet or filter can claim it.
 *
 * No JavaScript bridge and no access to native Android APIs is required.
 */
export const ANDROID_BACK_EVENT = "cinema-android-back";

export function consumeAndroidBack(event: Event, close: () => void, blocked = false): boolean {
  if (!event.cancelable || event.defaultPrevented || blocked) return false;
  event.preventDefault();
  close();
  return true;
}
