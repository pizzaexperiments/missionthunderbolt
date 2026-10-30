# Exact sound-command timing plans — issue #13

`scripts/snd_sequence.py` produces local JSON command-processing plans. It does
not synthesize samples, write WAV files, determine audible note endings, or
change the existing sound decoder's strict default behavior.

## Documented semantics and limits

Apple's archived [Inside Macintosh: Sound, Sound Command Numbers](https://developer.apple.com/library/archive/documentation/mac/Sound/Sound-66.html)
defines `soundCmd` as installing a sampled voice, rather than playing a buffer.
The command's high bit makes its address a resource-relative offset. The same
reference defines `freqDurationCmd` and `restCmd` durations in half milliseconds,
and frequency-command note values from 0 through 127. It explicitly says a
`quietCmd` is needed to stop a note after `freqDurationCmd`'s duration. A
command interval ending therefore does not establish an audible note ending.

[Sound Header Records](https://developer.apple.com/library/archive/documentation/mac/Sound/Sound-74.html)
defines the fixed-point source rate, base frequency and sample loop bounds.
These are preserved as metadata. Those descriptions alone do not establish
Classic Sound Manager interpolation, playback phase, loop transitions, channel
shutdown or the game's caller behavior. The analyzer infers none of these and
never approximates pitched commands with a resampler.

The supported dialect is deliberately narrow:

- Format 1 with exactly one sampled-synthesizer modifier (ID 5), initialized
  with zero; one offset-based `soundCmd` installs a voice before timed commands.
- Standard uncompressed, inline, 8-bit mono samples with a valid source rate,
  base frequency and bounded sample/loop positions.
- Canonical zero-parameter `nullCmd`, nonnegative signed `freqDurationCmd`
  durations and canonical `restCmd` with zero second parameter.

Unknown commands, other flags, pointer-based samples, compressed/extended
headers, multiple installations, nonzero ignored-parameter variants, differing
initialization and negative duration encodings are rejected. Some may be valid
Sound Manager inputs; they are outside the verified dialect. In particular,
negative-duration handling and floating-note/loop rendering require
separate implementation and verification. `quietCmd` and `bufferCmd` are also unsupported by this
analyzer, rather than silently reinterpreted.

The default hard bounds are 8 MiB input, 1,024 commands, 60 seconds of command
processing, an output position rate of at most 192,000 Hz and at most 11,520,000
frame positions. Callers may lower duration/frame bounds. The output rate is a
coordinate system; no PCM is rendered at that rate. Fixed source rates and
cumulative times/frame positions use exact rational numbers. For example, one
half millisecond at 11,025 Hz is exactly `441/80` frames; repeated commands do
not accumulate integer rounding error. JSON represents a rational with integer
`numerator` and positive `denominator` fields.

## Local use and provenance

```sh
python3 scripts/snd_sequence.py local-generated/original-resources/manifest.json \
  --resource-id 9015 --output-rate 11025 \
  --output local-generated/sound-timing-plan-9015
```

The extraction manifest must pass its existing schema, path and payload-hash
checks. The report preserves resource ID, resource-fork identity, exact payload
SHA256, source-format/sample metadata, command indexes and documentation links.
A matching ID in several forks produces separate entries. Unsupported/malformed
inputs fail before creating the output directory. Existing outputs are refused;
choose a fresh ignored directory for a new run. Outputs inside the checkout must
stay under `local-generated/`. Keep original-derived reports private.

The private supplied-resource check produced four command entries and a total
command-processing duration of exactly `71/200` seconds. At 11,025 Hz its final
position is `31311/8` frames. This is a static timing calculation, not measured
original playback, a verified audio duration, or a fully rendered version of
resource 9015. The original sequence, sample bytes and report are not public
fixtures. No audio was added to the app.

## Validation

```sh
PYTHONPATH=scripts:tests python3 -m unittest test_snd_sequence test_sound_catalog -v
```

The 18 authored tests cover rational timing across 1,000 timed commands, source
rate fractions, pitched-note metadata without synthesis, zero durations, strict
command/parameter/format rejection, voice ordering, truncation, malformed bounds,
resource identity/hash checks, output protection, and the existing decoder's
strict/sample-only behavior. Historical auditory equivalence, pitched loop
rendering, cue mapping and audible Android hardware output remain open in #13.
