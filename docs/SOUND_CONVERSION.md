# Local Macintosh sound conversion — issue #13

```sh
python3 scripts/sound_catalog.py local-generated/extracted/manifest.json --output local-generated/sound-catalog
```

The converter validates extraction hashes, recognizes format 1/2 `snd ` command
lists with one offset-based sound/sample buffer, and writes uncompressed PCM WAV.
It supports standard unsigned 8-bit mono and extended 8/16-bit mono/stereo
headers, translating big-endian 16-bit samples to WAV little-endian. Source fixed
sample rate, rounded WAV rate, frame count, base frequency and loop bounds remain
in the resource-ID/hash report. WAV previews do not implement Macintosh command
scheduling or loop playback; retain that metadata for later playback research.

Compressed encodings, external sample pointers, multiple buffers, unsupported
synthesizers/commands and layouts are reported explicitly. Exit status 2 means
not every resource converted. Existing output directories are preserved.

Synthetic tests verify exact PCM bytes/rates/channels, 16-bit byte ordering,
truncation, compressed-format refusal and manifest identity. Original audio was
later supplied and converted as recorded below; auditory comparison remains
unperformed. The application remains silent (safe
no-audio fallback); original event/cue mapping, native playback controls and
audio-focus/device verification are pending. This converter does not complete
#13's original-audio or Android playback acceptance criteria.

## Original-input validation

From the supplied archive, **137 of 138** sound resources converted to local WAV
with hash-linked reports. Resource ID 9015 uses a sampled sound plus frequency/
duration/rest commands; it is explicitly unsupported rather than flattened into
an inaccurate single-buffer preview. PCM conversion does not establish the full
Sound Manager sequence, cue mapping or auditory equivalence. No original audio
was publicly redistributed; native playback/device validation remains pending.

## Timed-sequence audit and sample-only previews

The command inspector now preserves format, synthesizer initialization, command
order, raw command words, offset flags, signed param1 and raw 32-bit param2 values.
Names for `soundCmd`/`bufferCmd`, `freqDurationCmd` and `restCmd` were checked
against an externally supplied Apple Universal Interfaces `Sound.h`; the header
is private and is not bundled. These names identify commands, not a recovered
pitch/duration renderer or original-game cue mapping.

The supplied resource 9015 contains one offset-based sample, two
`freqDurationCmd` commands and one `restCmd`. A new private catalog run writes its
underlying PCM as a **sample-only** preview and retains the complete command list
in the resource-ID/hash-linked report. The result is **137 converted single-buffer
resources, one sample-only resource, zero malformed/unsupported resources**.
This does not mean 138 complete original sound sequences were rendered.

`decode_sound(data)` still refuses timed sequences by default. Explicit
`sample_only=True` allows extracting the one embedded sample when the remaining
commands are the recognized timed pair. Catalog rows distinguish `sample-only`
from `converted`; CLI exit status remains **2** when any row is sample-only,
unsupported or malformed. Unknown commands, external pointers, multiple buffers,
unsupported synthesizers/encodings and invalid offsets remain rejected. Original
WAVs/reports remain ignored, and the app remains silent.

Eight synthetic sound tests pass, including exact sample bytes, retained command
order/parameters, signed param1, sample-only status, malformed offsets and unknown
commands. Native scheduling, pitch/loop semantics, audio focus, cue mapping and
auditory/device comparisons still block completion of #13.
