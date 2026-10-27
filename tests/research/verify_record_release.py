#!/usr/bin/env python3
"""Execute original release walkers on authored graphs; allocator calls are observation-only."""
import argparse
import json
from pathlib import Path
import random
import struct
import subprocess
import hashlib
from verify_linked_records import PROFILES, machine, call, check_return, STACK
from verify_rng_cpu import manifest_inputs

A5, PARENT = 0x80000, 0xc0000


def cases():
    graphs = [
        {0xb0000: (0, 0)},
        {0xb0000: (0xb0100, 0xb0200), 0xb0100: (0, 0), 0xb0200: (0, 0)},
        {0xb0000: (0xb0100, 0xb0200), 0xb0100: (0, 0xb0300), 0xb0200: (0, 0), 0xb0300: (0, 0)},
        {0xb0000: (0xb0000, 0)},
        {0xb0000: (0, 0xb0000)},
        {0xb0000: (0xb0100, 0xb0100), 0xb0100: (0, 0)},
    ]
    rng = random.Random(1706)
    for size in range(1, 9):
        ids = [0xb0000+i*0x100 for i in range(size)]
        for _ in range(8):
            graphs.append({i: (rng.choice([0]+ids), rng.choice([0]+ids)) for i in ids})
    for index, nodes in enumerate(graphs):
        for budget in [0, 1, 2, 3, 7, 32]:
            yield {'name': f'graph-{index}-{budget}', 'mode': 0, 'root': 0xb0000, 'budget': budget,
                   'nodes': nodes, 'count': 0, 'field52': 0, 'slots': [0]*127}
    for count in range(128):
        ids = [0xb0000+i*0x100 for i in range(8)]
        nodes = {i: (0, 0) for i in ids}
        slots = [ids[i%8] for i in range(count)]+[0xdeadbeef]*(127-count)
        for extra in [0, 0xe0000]:
            for budget in [0, 1, 2, 7, 1000]:
                yield {'name': f'parent-{count}-{extra}-{budget}', 'mode': 1, 'root': PARENT,
                       'budget': budget, 'nodes': nodes, 'count': count, 'field52': extra, 'slots': slots}
    # Release one child graph in reverse-slot context, including recursive cycles.
    for index, nodes in enumerate(graphs[:6]):
        for budget in [0, 1, 2, 7, 32]:
            yield {'name': f'parent-graph-{index}-{budget}', 'mode': 1, 'root': PARENT, 'budget': budget,
                   'nodes': nodes, 'count': 2, 'field52': 0xe0000, 'slots': [0xb0000]*2+[0]*125}


def snapshot(uc, identities):
    raw = bytearray()
    for identity in sorted(identities):
        raw.extend(struct.pack('>I', identity)); raw.extend(uc.mem_read(identity+26, 8))
    raw.extend(uc.mem_read(PARENT+51, 5)); raw.extend(uc.mem_read(PARENT+60, 127*4))
    value = 2166136261
    for byte in raw: value = ((value ^ byte)*16777619) & 0xffffffff
    return value


def execute(payloads, case):
    from unicorn import UC_HOOK_CODE
    from unicorn.m68k_const import UC_M68K_REG_A5, UC_M68K_REG_A7, UC_M68K_REG_D7
    uc = machine(payloads); uc.reg_write(UC_M68K_REG_A5, A5); uc.reg_write(UC_M68K_REG_D7, 0x77777777)
    uc.mem_write(A5+0xde2, b'\x4e\xf9'+struct.pack('>I', PROFILES[9]['base']+28968))
    uc.mem_write(A5+0x1312, b'\x4e\x75')
    before = {}
    for identity, (following, branch) in case['nodes'].items():
        raw = bytearray(b'\xa5'*64); struct.pack_into('>II', raw, 26, following, branch)
        before[identity] = bytes(raw); uc.mem_write(identity, bytes(raw))
    parent = bytearray(b'\x5a'*580); parent[51] = case['count']
    struct.pack_into('>I', parent, 52, case['field52']); struct.pack_into('>127I', parent, 60, *case['slots'])
    uc.mem_write(PARENT, bytes(parent))
    observed = {'steps': 0, 'status': 0}; events = []
    def hook(machine, address, size, user):
        if address == A5+0x1312:
            sp = machine.reg_read(UC_M68K_REG_A7)
            identity = struct.unpack('>I', bytes(machine.mem_read(sp+4, 4)))[0]
            events.append((identity, snapshot(machine, case['nodes'])))
        elif observed['steps'] == case['budget']:
            observed['status'] = 1; machine.emu_stop()
        else: observed['steps'] += 1
    boundaries = [PROFILES[9]['base']+offset for offset in (28968, 0x7142, 0x7176)]
    boundaries += [PROFILES[7]['base']+offset for offset in (4104, 0x101a)]
    for point in boundaries+[A5+0x1312]: uc.hook_add(UC_HOOK_CODE, hook, begin=point, end=point)
    call(uc, 7 if case['mode'] else 9, 4104 if case['mode'] else 28968, struct.pack('>I', case['root']))
    if observed['status'] == 0:
        check_return(uc)
        if uc.reg_read(UC_M68K_REG_D7) != 0x77777777: raise AssertionError('D7 not preserved')
    for identity, raw in before.items():
        after = bytes(uc.mem_read(identity, 64))
        if after[:26] != raw[:26] or after[34:] != raw[34:]: raise AssertionError('unrelated graph bytes changed')
    after = bytes(uc.mem_read(PARENT, 580))
    if after[:51] != parent[:51] or after[52:60] != parent[52:60] or after[568:] != parent[568:]:
        raise AssertionError('unrelated parent/guard bytes changed')
    result = [observed['status'], observed['steps'], snapshot(uc, case['nodes']), len(events)]
    for event in events: result.extend(event)
    result.extend([after[51], struct.unpack_from('>I', after, 52)[0], *struct.unpack_from('>127I', after, 60)])
    for identity in sorted(case['nodes']):
        result.extend([identity, *struct.unpack('>II', bytes(uc.mem_read(identity+26, 8)))])
    return ' '.join(map(str, result))


def verify(manifest, driver):
    payloads = {}
    for record, data in manifest_inputs(manifest, 'CODE'):
        sid = record['id']
        if sid not in PROFILES: continue
        if sid in payloads or hashlib.sha256(data).hexdigest() != PROFILES[sid]['sha256']:
            raise ValueError('ambiguous or unsupported source segment')
        payloads[sid] = data
    if set(payloads) != set(PROFILES): raise ValueError('missing source segment')
    inputs = []; wanted = []; summaries = []
    for case in cases():
        line = ' '.join(str(case[k]) for k in ('mode', 'root', 'budget', 'count', 'field52'))
        line += ' '+' '.join(map(str, case['slots']))+' '+str(len(case['nodes']))
        line += ''.join(f' {i} {n} {b}' for i,(n,b) in sorted(case['nodes'].items()))
        inputs.append(line); result = execute(payloads, case); wanted.append(result)
        summaries.append({'name': case['name'], 'mode': case['mode'], 'result': result})
    run = subprocess.run([str(driver.resolve())], input='\n'.join(inputs)+'\n', text=True,
                         capture_output=True, check=True, timeout=30)
    lines = run.stdout.splitlines()
    if len(lines) != len(wanted): raise AssertionError('native release result count mismatch')
    for index, (actual, expected) in enumerate(zip(lines, wanted)):
        if actual != expected: raise AssertionError(f'release mismatch {summaries[index]["name"]}: {actual} != {expected}')
    import unicorn
    return {'schema': 1, 'unicorn_version': unicorn.__version__, 'source_profiles': PROFILES,
            'scope': 'original release control flow; disposal calls are observation-only, not actual freeing',
            'cases': len(wanted), 'complete': sum(r['result'].split()[0] == '0' for r in summaries),
            'budget_stops': sum(r['result'].split()[0] == '1' for r in summaries), 'results': summaries}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('manifest', type=Path)
    p.add_argument('--native-driver', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); repo = Path(__file__).resolve().parents[2]; output = a.output.resolve()
    if output.exists(): p.error('refusing to overwrite evidence')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'local-generated'):
        p.error('original-derived evidence must remain private')
    report = verify(a.manifest, a.native_driver); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(f'Matched {report["cases"]} release cases: {report["complete"]} complete, {report["budget_stops"]} budget stops')


if __name__ == '__main__': main()
