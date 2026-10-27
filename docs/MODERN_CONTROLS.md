# Demo presentation and input — issue #17

Classic/Modern selects two **synthetic demo skins** on the same native game.
Neither is a faithful original-game renderer (#16 still needs reference work).
Switching skins preserves player/map/turns and does not change mechanics.

- Direction buttons have accessible labels and minimum 48 dp targets.
- Status uses scalable `sp` text; TalkBack can focus the labeled board and buttons.
- Portrait places controls below the board; landscape places them beside it.
- `Controls` shows/hides the virtual D-pad; the setting stays app-private.
- `Controls: Auto → Left → Right` selects persistent placement. Auto centers the
  portrait D-pad and uses the right landscape panel. Left/Right align the portrait
  directional rows and move the landscape panel to that side. Placement preserves
  game state, zoom and D-pad visibility; it consumes no turn.
- Arrow keys/WASD move; joystick/hat directions use a dead zone and one action
  per direction change, preventing continuous duplicate steps from held axes.
- Pinch zoom is bounded to 1–4× with nearest-neighbor cell drawing. A pinch does
  not also trigger movement. Center taps have a dead zone. Zoom is app-private.
- Restart is explicit and retains the presentation selection.

The synthetic board now exposes virtual player/wall/floor cells with one-based
column/row descriptions and collection coordinates. Accessibility focus and text
search inspect cells without consuming a turn. The board offers named movement,
WAIT, zoom-in/out and Show entire map actions. Zoomed-offscreen cells are excluded
from visible children; zooming clears a cell focus that becomes offscreen.
Touch-exploration hover events target the same cell geometry used by the renderer.
No original graphics or recovered enemy/item semantics are packaged.

Instrumentation checks the actual Android framework tree as well as provider
queries, coordinates, read-only focus, shared movement/WAIT state, mode switching,
zoom clipping and full-map reset. Physical TalkBack gesture/speech usability,
physical gamepad coverage and broader device/font-scale validation remain open.

Build test APKs with `cd android && gradle --no-daemon assembleDebug assembleDebugAndroidTest`.
On a selected emulator/device:

```sh
adb -s SERIAL install -r android/app/build/outputs/apk/debug/app-debug.apk
adb -s SERIAL install -r android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk
adb -s SERIAL shell am instrument -w org.missionthunderbolt.prototype.test/android.test.InstrumentationTestRunner
```

The initial three platform instrumentation tests passed on a Linux software-emulated
Android API 23 x86_64 image: mode/turn preservation, accessible target labels/sizes,
and Activity recreation. App install and `am start -W` also succeeded. APK tests
use Android's platform test runner without third-party test dependencies; no CI
run was triggered. Physical ARM64/API 35 acceptance is not implied by this result.

The expanded 19-test suite, measured 1.3× font scaling, lifecycle and current
limitations are recorded in [Android runtime evidence](ANDROID_RUNTIME.md).

WAIT, Space and keypad-5 now consume one prototype time unit in place; see
[the manual-backed rule](MANUAL_RULES.md). Invalid zero-direction movement is unchanged.

Sound is opt-in and muted by default. The authored demo cue, volume slider, focus
and lifecycle behavior are documented in [native demo audio](NATIVE_AUDIO.md).
Left/right adjust volume while its slider has keyboard focus; otherwise the
existing game-direction shortcuts apply. Sound controls do not consume turns.
