# Opt-in native demo audio — issues #13 and #18

The Android research demo now has an opt-in **Sound** toggle and volume slider.
Sound defaults off. The only cue is an authored 80 ms, 660 Hz PCM tone with a short
attack/release envelope, generated in code at 22,050 Hz. It is not an original
sample, conversion preview, historical cue or reconstructed Sound Manager sequence.
No historical audio is packaged, and the gameplay model remains synthetic.

## Playback and lifecycle contract

`DemoAudio` writes signed 16-bit mono PCM to a static Android `AudioTrack`, checks
the full sample count and initialized state, and starts only after transient audio
focus is granted while the Activity is active. A valid move or WAIT can request
the cue; blocked moves, mute, zero volume or inactive/closed output do not play.
A missing audio service or output failure falls back to silence without stopping
the game. The UI reports unavailable output for that Activity instance.

A static track initially reports `STATE_NO_STATIC_DATA`. PCM must be written before
requiring `STATE_INITIALIZED`; the first runtime test caught that ordering defect,
and the implementation was corrected without weakening the playback assertion.
Repeated cues pause/reset the existing buffer. A single delayed completion stops
playback and abandons focus; no continuous playback timer or wake lock is added.

Mute releases the track. Pause/Activity destruction cancels completion callbacks,
stops output, abandons focus and releases resources. Resume does not replay an old
cue. Activity memory callbacks at `TRIM_MEMORY_RUNNING_LOW` or higher, plus
`onLowMemory`, also cancel completion, abandon focus and release the cached track.
The lower `RUNNING_MODERATE` hint keeps the cache. Trimming retains enabled/volume
settings and the foreground active flag: no cue is replayed automatically, and
the next explicit cue can lazily recreate output. Paused/closed output stays
inactive after trimming. Focus loss stops output; ducking applies a 0.2 gain factor, and focus gain
restores the selected gain without automatically replaying. Hardware routing,
headphone changes and real focus competition still need broader device testing.

Sound/volume preferences are app-private and separate from portable gameplay save
state. The volume slider has an accessibility description and 48 dp target height.
When it has keyboard focus, left/right adjust volume instead of moving the player;
other game shortcuts preserve the existing input behavior. Sound controls do not
consume turns, and mode switching does not change the simulation or cue mapping.

## Validation boundaries

The instrumentation suite tests actual `AudioTrack` initialization/write/start and
positive PCM playback-head advancement. It also checks mute/zero volume, explicit
focus callbacks, pause/resume/release, missing-service fallback, control/turn
independence, keyboard slider behavior and preference recreation. Callback
injection verifies the handler's behavior; it is not an OS focus-arbitration test.

The cloud emulator uses `-no-audio`, so advancing AudioTrack frames proves Android
output-stack consumption, not audible host/device output. Auditory equivalence,
original event/cue mapping, timed sequence 9015 rendering and physical-device
output remain unverified. See [sound conversion](SOUND_CONVERSION.md) for the
separate private PCM/catalog research. This increment does not complete #13.

The 2026-10-27 API 23 x86_64/normal portrait/target-35 run passed all **15 tests**
and measured **528 consumed PCM frames**. The following lifecycle run preserved
state across process death and three background cycles. Debug/release builds and
lint passed. Physical output, API 35 runtime and original-audio fidelity remain
open acceptance items.

The following memory-pressure increment passed the complete **19-test suite**
on API 23 x86_64, measured 1.3× font/portrait, target SDK 35. Callback tests verify
track release/lazy recreation and unchanged complete native game serialization.
This is injected callback coverage, not an actual memory-exhaustion measurement;
see ANDROID_RUNTIME.md for the configuration-check failure and exact limits.
