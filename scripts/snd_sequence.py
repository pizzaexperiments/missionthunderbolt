#!/usr/bin/env python3
"""Plan a bounded sampled-sound command timeline exactly; never synthesize audio."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import struct

from pict_catalog import Unsupported, manifest_inputs
from sound_catalog import inspect_commands

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_DURATION_SECONDS = 60
MAX_OUTPUT_RATE = 192000
MAX_FRAME_POSITIONS = MAX_DURATION_SECONDS * MAX_OUTPUT_RATE
REFERENCES = [
    'https://developer.apple.com/library/archive/documentation/mac/Sound/Sound-66.html',
    'https://developer.apple.com/library/archive/documentation/mac/Sound/Sound-74.html',
]


def rational(value):
    return {'numerator': value.numerator, 'denominator': value.denominator}


def plan_sequence(data, output_rate=48000, max_seconds=MAX_DURATION_SECONDS,
                  max_frames=MAX_FRAME_POSITIONS):
    """Return command-processing positions, not audible note-end boundaries.

    The supported dialect is format 1, one sampled-synthesizer modifier initialized
    with zero, one offset soundCmd, then null/freqDuration/rest commands. Negative
    duration encodings, pitched resampling and loop rendering are not implemented.
    """
    for name, value, upper in [('output rate', output_rate, MAX_OUTPUT_RATE),
                               ('duration limit', max_seconds, MAX_DURATION_SECONDS),
                               ('frame limit', max_frames, MAX_FRAME_POSITIONS)]:
        if type(value) is not int or not 1 <= value <= upper:
            raise ValueError('invalid '+name)
    if len(data) > MAX_INPUT_BYTES:
        raise ValueError('sound resource exceeds input bound')
    listing = inspect_commands(data)
    if listing['format'] != 1 or listing['modifiers'] != [{'synthesizer': 5, 'initialization': 0}]:
        raise Unsupported('requires format 1 and one sampled synthesizer with zero initialization')
    sample_commands = [c for c in listing['commands'] if c['word'] == 0x8050]
    if len(sample_commands) != 1:
        raise Unsupported('requires one offset soundCmd voice installation')
    install = sample_commands[0]
    if install['param1'] != 0:
        raise Unsupported('nonzero soundCmd parameter is outside the supported dialect')
    offset = install['param2']
    if offset < listing['table_end'] or offset + 22 > len(data):
        raise ValueError('invalid sound header offset')
    pointer, length, fixed_rate, loop_start, loop_end, encoding, base = struct.unpack_from('>IIIIIBB', data, offset)
    if pointer:
        raise Unsupported('external sample pointer')
    if encoding != 0:
        raise Unsupported('only standard uncompressed 8-bit mono headers are supported')
    rate = Fraction(fixed_rate, 65536)
    if not 1 <= rate <= MAX_OUTPUT_RATE or not 1 <= length <= MAX_INPUT_BYTES:
        raise ValueError('invalid source rate or sample length')
    if offset + 22 + length > len(data):
        raise ValueError('truncated PCM samples')
    if not 0 <= loop_start <= loop_end <= length or not 1 <= base <= 127:
        raise ValueError('invalid loop bounds or base frequency')
    elapsed = Fraction(0)
    installed = False
    events = []
    for command in listing['commands']:
        word, duration, param2 = command['word'], command['param1'], command['param2']
        start = elapsed
        event = {'index': command['index'], 'command': command['name']}
        if word == 0:
            if duration or param2:
                raise Unsupported('nonzero nullCmd parameters are outside the supported dialect')
        elif word == 0x8050:
            installed = True
        elif word in (40, 41):
            if not installed:
                raise Unsupported('timed command before sampled voice installation')
            if duration < 0:
                raise Unsupported('negative duration encoding is not interpreted')
            if word == 40:
                if not 0 <= param2 <= 127:
                    raise ValueError('invalid MIDI note value')
                event['requested_note'] = param2
                event['audible_stop'] = 'not inferred; freqDurationCmd alone does not stop the note'
            elif param2 != 0:
                raise Unsupported('nonzero restCmd parameter is outside the supported dialect')
            event['duration_half_milliseconds'] = duration
            elapsed += Fraction(duration, 2000)
        else:
            raise Unsupported(f'unsupported sound command word 0x{word:04x}')
        if elapsed > max_seconds or elapsed * output_rate > max_frames:
            raise ValueError('command timeline exceeds duration or frame bound')
        event.update(start_seconds=rational(start), end_seconds=rational(elapsed),
                     start_frame_position=rational(start * output_rate),
                     end_frame_position=rational(elapsed * output_rate))
        events.append(event)
    return {
        'schema': 1, 'scope': 'command-timing-plan-only',
        'source_sha256': hashlib.sha256(data).hexdigest(),
        'format': listing['format'], 'modifiers': listing['modifiers'],
        'sample': {'channels': 1, 'sample_bits': 8, 'frames': length,
                   'source_rate_fixed': fixed_rate, 'source_rate': rational(rate),
                   'base_frequency': base, 'loop_start': loop_start, 'loop_end': loop_end},
        'output_rate': output_rate, 'duration_seconds': rational(elapsed),
        'end_frame_position': rational(elapsed * output_rate), 'commands': events,
        'limits': {'input_bytes': MAX_INPUT_BYTES, 'duration_seconds': max_seconds, 'frames': max_frames},
        'references': REFERENCES,
        'limitations': [
            'Command-processing intervals are not audible note lifetimes',
            'No terminal quietCmd, channel disposal or original caller behavior is inferred',
            'No sample synthesis, pitch interpolation, loop phase, frame rounding or WAV output',
            'Not original-game playback verification or auditory equivalence',
        ],
    }


def plan_manifest(manifest, output, resource_id, output_rate=48000):
    if type(resource_id) is not int or not -32768 <= resource_id <= 32767:
        raise ValueError('invalid signed resource ID')
    if output.exists():
        raise ValueError('refusing to overwrite output directory')
    repo = Path(__file__).resolve().parents[1]
    resolved = output.resolve()
    if resolved.is_relative_to(repo) and not resolved.is_relative_to(repo/'local-generated'):
        raise ValueError('outputs inside checkout must stay under local-generated/')
    reports = []
    for record, data in manifest_inputs(manifest, 'snd '):
        if record['id'] != resource_id:
            continue
        report = plan_sequence(data, output_rate)
        report.update(fork=record['fork'], id=record['id'])
        reports.append(report)
    if not reports:
        raise ValueError('manifest has no matching sound resource')
    output.mkdir(parents=True)
    (output/'report.json').write_text(json.dumps({'schema': 1, 'resources': reports}, indent=2)+'\n')
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--resource-id', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--output-rate', type=int, default=48000)
    args = parser.parse_args()
    try:
        reports = plan_manifest(args.manifest, args.output, args.resource_id, args.output_rate)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    print(f'Planned {len(reports)} resource(s); no audio rendered or playback fidelity verified')


if __name__ == '__main__':
    main()
