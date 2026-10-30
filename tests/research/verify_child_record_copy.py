#!/usr/bin/env python3
"""Compare post-allocation child-copy instructions with the supplied-record model.

Starts at CODE 9 offset 0x5290, after the allocator returns. No allocator call,
trap, service return shim, original allocation or gameplay behavior is verified.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess

from verify_rng_cpu import manifest_inputs

SOURCE_SHA = '6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717'
BASE, SOURCE, DESTINATION, FRAME, STOP = 0x40000, 0xb0000, 0xc0000, 0xe0000, 0xf8000
ENTRY, LAST = 0x5290, 0x52b0
SAVED_A4, SAVED_A6 = 0x12345678, 0x87654320


def cases():
    # Every byte position and value, against an unrelated authored background.
    # Both distinct and exact-alias paths cover every position/value pair.
    for offset in range(56):
        for value in range(256):
            source = bytearray([0x96]*56); source[offset] = value
            initial = bytes((value*13+i*17)&255 for i in range(56))
            for alias in (False, True):
                yield 'basis', alias, bytes(source), initial
    rng = random.Random(5278)
    for index in range(4096):
        source = bytes(rng.randrange(256) for _ in range(56))
        initial = bytes(rng.randrange(256) for _ in range(56))
        yield 'random', bool(index&1), source, initial
    for value in range(256):
        for alias in (False, True):
            yield 'uniform', alias, bytes([value]*56), bytes([255-value]*56)


def verify(manifest, driver):
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
    from unicorn.m68k_const import (UC_CPU_M68K_M68000, UC_M68K_REG_A0,
        UC_M68K_REG_A1, UC_M68K_REG_A4, UC_M68K_REG_A6, UC_M68K_REG_A7,
        UC_M68K_REG_D0, UC_M68K_REG_PC, UC_M68K_REG_SR)
    sources = [data for rec, data in manifest_inputs(manifest, 'CODE') if rec['id'] == 9]
    if len(sources) != 1 or hashlib.sha256(sources[0]).hexdigest() != SOURCE_SHA:
        raise ValueError('missing, ambiguous or unsupported CODE 9')
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN); uc.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    uc.mem_map(0x10000, 0x100000); uc.mem_write(BASE, sources[0])
    current = {'destination': DESTINATION}
    instructions = Counter()
    def code(machine, address, size, user):
        if not BASE+ENTRY <= address <= BASE+LAST:
            raise AssertionError('execution outside supplied-allocation copy body')
        instructions[address-BASE] += 1
    def write(machine, access, address, size, value, user):
        start = current['destination']
        if not start <= address or address+size > start+56:
            raise AssertionError('write outside supplied output record')
    uc.hook_add(UC_HOOK_CODE, code)
    uc.hook_add(UC_HOOK_MEM_WRITE, write)
    uc.ctl_flush_tb()
    inputs = []; wanted = []; counts = Counter()
    for kind, alias, source, initial in cases():
        destination = SOURCE if alias else DESTINATION
        current['destination'] = destination
        source_guarded = b'\xa6'*16+source+b'\x6a'*16
        destination_guarded = b'\xc3'*16+initial+b'\x3c'*16
        uc.mem_write(SOURCE-16, source_guarded)
        if not alias:
            uc.mem_write(DESTINATION-16, destination_guarded)
        frame = bytearray(b'\x5a'*80)
        struct.pack_into('>II', frame, 20, 1, 56)  # pending allocator arguments
        struct.pack_into('>IIII', frame, 28, SAVED_A4, SAVED_A6, STOP, SOURCE)
        frame = bytes(frame); uc.mem_write(FRAME-32, frame)
        for register, value in ((UC_M68K_REG_SR, 0x2000), (UC_M68K_REG_D0, destination),
                                (UC_M68K_REG_A4, SAVED_A4), (UC_M68K_REG_A6, FRAME),
                                (UC_M68K_REG_A7, FRAME-12)):
            uc.reg_write(register, value)
        uc.emu_start(BASE+ENTRY, STOP, count=100)
        expected_registers = ((UC_M68K_REG_PC, STOP), (UC_M68K_REG_D0, destination),
                              (UC_M68K_REG_A4, SAVED_A4), (UC_M68K_REG_A6, SAVED_A6),
                              (UC_M68K_REG_A7, FRAME+8), (UC_M68K_REG_A0, SOURCE+56),
                              (UC_M68K_REG_A1, destination+56))
        if any(uc.reg_read(register) != value for register, value in expected_registers):
            raise AssertionError('copy return/register endpoint mismatch')
        if bytes(uc.mem_read(FRAME-32, len(frame))) != frame:
            raise AssertionError('copy changed frame or allocator argument context')
        source_after = bytes(uc.mem_read(SOURCE, 56))
        output_after = bytes(uc.mem_read(destination, 56))
        if bytes(uc.mem_read(SOURCE-16, 16)) != source_guarded[:16] or bytes(uc.mem_read(SOURCE+56, 16)) != source_guarded[-16:]:
            raise AssertionError('copy changed source guards')
        if not alias:
            if source_after != source:
                raise AssertionError('copy changed distinct source')
            if bytes(uc.mem_read(DESTINATION-16, 16)) != destination_guarded[:16] or bytes(uc.mem_read(DESTINATION+56, 16)) != destination_guarded[-16:]:
                raise AssertionError('copy changed destination guards')
        inputs.append(f'{int(alias)} {source.hex()} {initial.hex()}')
        wanted.append(f'{source_after.hex()} {output_after.hex()}')
        counts[kind] += 1; counts['alias' if alias else 'distinct'] += 1
    if bytes(uc.mem_read(BASE, len(sources[0]))) != sources[0]:
        raise AssertionError('copy changed original instructions')
    run = subprocess.run([str(driver.resolve())], input='\n'.join(inputs)+'\n', text=True,
                         capture_output=True, check=True, timeout=60)
    actual = run.stdout.splitlines()
    if len(actual) != len(wanted):
        raise AssertionError('native copy comparison count mismatch')
    for index, (observed, expected) in enumerate(zip(actual, wanted)):
        if observed != expected:
            raise AssertionError(f'native copy mismatch at case {index}')
    import unicorn
    return {'schema': 1, 'source_sha256': SOURCE_SHA, 'segment': 9,
            'entry': ENTRY, 'last_instruction': LAST, 'unicorn_version': unicorn.__version__,
            'comparisons': len(wanted), 'cases': dict(counts),
            'result_sha256': hashlib.sha256(('\n'.join(wanted)+'\n').encode('ascii')).hexdigest(),
            'scope': 'Original post-allocation copy instructions on supplied records only',
            'allocator_executed': False, 'allocation_return_shim_used': False,
            'partial_overlap_tested': False, 'distinct_source_and_neighbors_preserved': True,
            'exact_self_alias_tested': True, 'register_frame_and_write_bounds_checked': True,
            'instruction_offsets': dict(sorted(instructions.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--native-driver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output.exists(): parser.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):
        parser.error('original-derived evidence must remain private')
    report = verify(args.manifest, args.native_driver)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Matched {report["comparisons"]} supplied-allocation copy probes; allocator not executed')


if __name__ == '__main__':
    main()
