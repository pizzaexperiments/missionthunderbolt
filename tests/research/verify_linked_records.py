#!/usr/bin/env python3
"""Private original-instruction comparisons for linked-record query and unlink."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
from verify_rng_cpu import manifest_inputs

PROFILES = {
    7: {'base': 0x20000, 'sha256': '43eb181114493dd938496157cf0943d5fb5d152b56086fb684122fe50385e852'},
    9: {'base': 0x30000, 'sha256': '6212eb2b13c828c35e7593f05d15a439421dca9bdd7d6746c04f24220a96c717'},
}
GRID, CELL, STACK, STOP = 0x60000, 0x50000, 0xf0000, 0xf8000


def machine(payloads):
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_CPU_M68K_M68000
    uc = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    uc.ctl_set_cpu_model(UC_CPU_M68K_M68000); uc.mem_map(0x10000, 0x100000)
    for sid, data in payloads.items(): uc.mem_write(PROFILES[sid]['base'], data)
    return uc


def call(uc, sid, entry, args):
    from unicorn.m68k_const import UC_M68K_REG_A2, UC_M68K_REG_A3, UC_M68K_REG_A4, UC_M68K_REG_A6, UC_M68K_REG_A7, UC_M68K_REG_SR
    uc.mem_write(STACK, struct.pack('>I', STOP)+args)
    uc.reg_write(UC_M68K_REG_SR, 0x2000); uc.reg_write(UC_M68K_REG_A7, STACK)
    for index, reg in enumerate([UC_M68K_REG_A2, UC_M68K_REG_A3, UC_M68K_REG_A4, UC_M68K_REG_A6]):
        uc.reg_write(reg, 0x12340000+index*0x100)
    uc.emu_start(PROFILES[sid]['base']+entry, STOP, count=10000)


def check_return(uc):
    from unicorn.m68k_const import UC_M68K_REG_PC, UC_M68K_REG_A2, UC_M68K_REG_A3, UC_M68K_REG_A4, UC_M68K_REG_A6, UC_M68K_REG_A7
    if uc.reg_read(UC_M68K_REG_PC) != STOP or uc.reg_read(UC_M68K_REG_A7) != STACK+4:
        raise AssertionError('routine failed to return with balanced stack')
    for index, reg in enumerate([UC_M68K_REG_A2, UC_M68K_REG_A3, UC_M68K_REG_A4, UC_M68K_REG_A6]):
        if uc.reg_read(reg) != 0x12340000+index*0x100:
            raise AssertionError('routine failed to preserve callee register')


def query_sweep(payloads, driver):
    from unicorn.m68k_const import UC_M68K_REG_D0
    uc = machine(payloads); inputs = []; wanted = []; accepted = [[], []]
    for group, field in enumerate([0, 0xffffffff]):
        for word in range(65536):
            raw = bytearray(b'\xa5'*40); struct.pack_into('>H', raw, 0, word); struct.pack_into('>I', raw, 30, field)
            uc.mem_write(CELL, bytes(raw)); call(uc, 9, 27148, struct.pack('>I', CELL)); check_return(uc)
            if bytes(uc.mem_read(CELL, 40)) != bytes(raw): raise AssertionError('query mutated record')
            value = uc.reg_read(UC_M68K_REG_D0)
            if value not in (0, 1): raise AssertionError('query returned nonboolean')
            if value: accepted[group].append(word)
            inputs.append(f'{word} {field}'); wanted.append(str(value))
    run = subprocess.run([str(driver.resolve()), '--query'], input='\n'.join(inputs)+'\n',
                         capture_output=True, text=True, check=True, timeout=30)
    if run.stdout.splitlines() != wanted: raise AssertionError('native query sweep disagrees')
    return {'comparisons': len(wanted), 'accepted_without_link': accepted[0], 'accepted_with_link': accepted[1]}


def cases():
    for length in range(1, 10):
        identities = [0xb0000+i*0x100 for i in range(length)]
        nodes = dict(zip(identities, identities[1:]+[0]))
        for position, target in enumerate(identities):
            for budget in sorted({0, 1, length-1, length}):
                for count in [0, 1, 32768, 65535]:
                    row, column = [(0, 0), (1, 1), (17, 65), (18, 66)][(position+budget+count)%4]
                    yield {'name': f'list-{length}-{position}-{budget}-{count}', 'nodes': nodes,
                           'target': target, 'head': identities[0], 'budget': budget,
                           'count': count, 'row': row, 'column': column, 'link': 0x12345678}
    for budget in [0, 1, 2, 7, 31]:
        for head in [0xb0000, 0xb0100]:
            yield {'name': f'cycle-{head}-{budget}', 'nodes': {0xb0000: 0xb0100, 0xb0100: 0xb0000, 0xb0200: 0xb0200},
                   'target': 0xb0200, 'head': head, 'budget': budget, 'count': 0, 'row': 18, 'column': 66, 'link': 0}
    yield {'name': 'self-head', 'nodes': {0xb0000: 0xb0000}, 'target': 0xb0000, 'head': 0xb0000,
           'budget': 0, 'count': 65535, 'row': 0, 'column': 66, 'link': 0xffffffff}


def unlink_case(payloads, case):
    from unicorn import UC_HOOK_CODE
    uc = machine(payloads); raw = bytearray(b'\x5a'*(104+1273*20+16))
    struct.pack_into('>H', raw, 18, case['count']); struct.pack_into('>I', raw, 20, case['head'])
    cell_offset = 104+(case['row']*67+case['column'])*20+12
    struct.pack_into('>I', raw, cell_offset, case['link']); uc.mem_write(GRID, bytes(raw))
    node_bytes = {}
    for identity, following in case['nodes'].items():
        node = bytearray(b'\xa5'*64); node[48] = case['row']; node[49] = case['column']
        struct.pack_into('>I', node, 56, following); node_bytes[identity] = bytes(node); uc.mem_write(identity, bytes(node))
    observed = {'visits': 0, 'status': 0}
    def hook(machine, address, size, user):
        if observed['visits'] == case['budget']:
            observed['status'] = 1; machine.emu_stop()
        else: observed['visits'] += 1
    uc.hook_add(UC_HOOK_CODE, hook, begin=PROFILES[7]['base']+0xf68, end=PROFILES[7]['base']+0xf68)
    call(uc, 7, 3872, struct.pack('>II', GRID, case['target']))
    if observed['status'] == 0: check_return(uc)
    after = bytes(uc.mem_read(GRID, len(raw)))
    allowed = set(range(18, 24)) | set(range(cell_offset, cell_offset+4))
    if any(a != b for i, (a,b) in enumerate(zip(raw, after)) if i not in allowed):
        raise AssertionError('unlink changed unrelated grid/header/guard bytes')
    result = [observed['status'], observed['visits'], struct.unpack_from('>H', after, 18)[0],
              struct.unpack_from('>I', after, 20)[0], struct.unpack_from('>I', after, cell_offset)[0]]
    for identity in sorted(node_bytes):
        after_node = bytes(uc.mem_read(identity, 64)); before = node_bytes[identity]
        if after_node[:56] != before[:56] or after_node[60:] != before[60:]:
            raise AssertionError('unlink changed unrelated node/guard bytes')
        result.extend([identity, struct.unpack_from('>I', after_node, 56)[0]])
    return ' '.join(map(str, result))


def verify(manifest, driver):
    payloads = {}
    for record, data in manifest_inputs(manifest, 'CODE'):
        sid = record['id']
        if sid not in PROFILES: continue
        if sid in payloads or hashlib.sha256(data).hexdigest() != PROFILES[sid]['sha256']:
            raise ValueError('ambiguous or unsupported original segment')
        payloads[sid] = data
    if set(payloads) != set(PROFILES): raise ValueError('required source segments missing')
    query = query_sweep(payloads, driver); inputs = []; wanted = []; summaries = []
    for case in cases():
        line = ' '.join(str(case[k]) for k in ['count', 'head', 'target', 'budget', 'row', 'column', 'link'])
        inputs.append(line+' '+str(len(case['nodes']))+''.join(f' {i} {n}' for i,n in sorted(case['nodes'].items())))
        result = unlink_case(payloads, case); wanted.append(result)
        summaries.append({'name': case['name'], 'result': result})
    run = subprocess.run([str(driver.resolve())], input='\n'.join(inputs)+'\n', text=True,
                         capture_output=True, check=True, timeout=30)
    for index, (actual, expected) in enumerate(zip(run.stdout.splitlines(), wanted)):
        if actual != expected: raise AssertionError(f'unlink mismatch {summaries[index]["name"]}: {actual} != {expected}')
    if len(run.stdout.splitlines()) != len(wanted): raise AssertionError('unlink result count mismatch')
    import unicorn
    return {'schema': 1, 'scope': 'isolated original instructions on authored records; not original gameplay',
            'unicorn_version': unicorn.__version__, 'source_profiles': PROFILES, 'query': query,
            'unlink_cases': len(wanted), 'unlink_results': summaries,
            'limits': ['valid grid coordinates required', 'traversal budget is a research stop, absent in original',
                       'missing-node native status is not an original return contract',
                       'record type meanings and allocation/release callbacks are not recovered']}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('manifest', type=Path)
    p.add_argument('--native-driver', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); repo = Path(__file__).resolve().parents[2]; output = a.output.resolve()
    if output.exists(): p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):
        p.error('original-derived reports must stay private')
    report = verify(a.manifest, a.native_driver); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Matched {report["query"]["comparisons"]} query probes and {report["unlink_cases"]} unlink cases')


if __name__ == '__main__': main()
