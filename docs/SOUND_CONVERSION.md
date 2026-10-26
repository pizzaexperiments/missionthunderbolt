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
truncation, compressed-format refusal and manifest identity. No original audio
has been supplied for auditory comparison. The application remains silent (safe
no-audio fallback); original event/cue mapping, native playback controls and
audio-focus/device verification are pending. This converter does not complete
#13's original-audio or Android playback acceptance criteria.
