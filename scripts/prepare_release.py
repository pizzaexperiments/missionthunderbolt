#!/usr/bin/env python3
"""Prepare local review-only artifact hashes/SPDX metadata; never publish."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import subprocess
import tempfile
import shutil
import tarfile
import uuid
import zipfile


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


def check_members(path):
    def safe(name):
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\\' in name:
            raise ValueError('unsafe package member')
        if any(part in {'local-original','local-generated','__MACOSX'} or part.startswith('._') for part in p.parts):
            raise ValueError('private research input in package')
        if p.suffix.lower() in {'.sit','.sitx','.hqx','.rsrc','.pict','.snd'}:
            raise ValueError('historical input extension in package')
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():safe(info.filename)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            for info in archive:
                safe(info.name)
                if info.issym() or info.islnk():safe(info.linkname)


def reviewed_attribution(manifest_path, ndk, evidence):
    """Verify notice-evidence coverage, without converting it into license clearance."""
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('schema') != 1 or manifest.get('kind') != 'android-ndk-notice-attribution':
        raise ValueError('unsupported attribution manifest')
    if evidence is None:
        raise ValueError('attribution requires dependency evidence')
    for key in ('ndk_version','llvm_version'):
        if manifest.get(key) != evidence.get(key):
            raise ValueError('attribution version does not match dependency evidence')
    if manifest.get('notices') != evidence.get('notices'):
        raise ValueError('attribution notice hashes do not match dependency evidence')
    notices=[]
    if {row.get('name') for row in manifest.get('notices',[])} != {'NOTICE','NOTICE.toolchain'} or len(manifest['notices']) != 2:
        raise ValueError('attribution requires both upstream NDK notices')
    ndk=ndk.resolve()
    for row in manifest['notices']:
        path=ndk/row['name']
        if not path.is_file() or digest(path) != row['sha256']:
            raise ValueError('installed upstream notice hash does not match attribution')
        notices.append(path)
    components=manifest.get('components',{})
    for name,component in components.items():
        if (not re.fullmatch(r'[A-Za-z0-9_+.-]+',name)
                or component.get('licenseDeclared') != 'NOASSERTION'
                or not isinstance(component.get('notice_evidence'),str)
                or not component['notice_evidence'].strip()):
            raise ValueError('component attribution must retain unresolved archive licenses and notice evidence')
    coverage={}
    for archive in manifest.get('archives',[]):
        key=(archive['abi'],archive['path'])
        path=PurePosixPath(archive['path'])
        if (key in coverage or path.is_absolute() or '..' in path.parts or '\\' in str(path)
                or not re.fullmatch(r'[0-9a-f]{64}',archive['sha256'])
                or str(path) != archive['path'] or archive.get('component') not in components):
            raise ValueError('invalid or duplicate attribution archive')
        coverage[key]=archive
    matched={}
    for abi,build in evidence.get('builds',{}).items():
        for archive in build.get('archives',[]):
            key=(abi,archive['path']);reviewed=coverage.get(key)
            if reviewed is None or reviewed['sha256'] != archive['sha256']:
                raise ValueError('unknown or mismatched archive requires attribution review')
            path=ndk/archive['path']
            if not path.is_file() or digest(path) != archive['sha256']:
                raise ValueError('installed archive hash does not match attribution')
            matched[key]=(reviewed['component'],components[reviewed['component']])
    if not matched:
        raise ValueError('attribution has no matching runtime archives')
    return manifest,matched,notices


def dependency_packages(evidence, rows, attribution=None):
    """Bind separately collected runtime evidence to exact artifact digests."""
    if evidence.get('schema') != 1 or evidence.get('kind') != 'android-ndk-link-review':
        raise ValueError('unsupported dependency evidence')
    supplied=evidence.get('artifacts',[])
    expected={(r['name'],r['sha256']) for r in rows}
    if len(supplied)!=len(rows) or {(r['name'],r['sha256']) for r in supplied}!=expected:
        raise ValueError('dependency evidence artifact hashes do not match')
    if evidence.get('java_runtime_modules') != [] or not evidence.get('builds'):
        raise ValueError('unsupported or missing runtime dependency records')
    packages=[];ids=[]
    for abi,build in sorted(evidence['builds'].items()):
        if not re.fullmatch(r'[A-Za-z0-9_-]+',abi) or not build.get('archives'):
            raise ValueError('invalid runtime ABI evidence')
        for index,archive in enumerate(build['archives']):
            path=PurePosixPath(archive['path'])
            if path.is_absolute() or '..' in path.parts or '\\' in str(path) or not re.fullmatch(r'[0-9a-f]{64}',archive['sha256']):
                raise ValueError('invalid runtime archive evidence')
            identifier=f'SPDXRef-NDK-{abi}-{index}';ids.append(identifier)
            comment='Archive contributed sections according to linker map; review preserved NDK notices for component license attribution.'
            if attribution is not None:
                component,review=attribution[(abi,str(path))]
                comment=(f'Component: {component}. Notice evidence: {review["notice_evidence"]} '
                         'Exact archive and upstream notice hashes verified against the attribution manifest; '
                         'archive-wide license applicability and third-party exceptions remain unresolved.')
            packages.append({'name':f'{abi}/{path.name}','SPDXID':identifier,
                'versionInfo':f'NDK {evidence["ndk_version"]}; LLVM {evidence["llvm_version"]}',
                'downloadLocation':'https://developer.android.com/ndk/downloads',
                'filesAnalyzed':False,'licenseDeclared':'NOASSERTION','licenseConcluded':'NOASSERTION',
                'copyrightText':'NOASSERTION',
                'checksums':[{'algorithm':'SHA256','checksumValue':archive['sha256']}],
                'sourceInfo':f'NDK-relative archive: {path}',
                'comment':comment})
    return packages,ids


def prepare(repo,artifacts,output,version,apksigner=None,dependency_evidence=None,attribution_manifest=None,ndk=None):
    repo=repo.resolve();output=output.resolve()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+\-]*',version):raise ValueError('invalid version label')
    if output.exists():raise ValueError('refusing to overwrite review directory')
    if output.is_relative_to(repo) and not output.is_relative_to(repo/'dist'):
        raise ValueError('review outputs inside checkout must stay under dist/')
    license_file=repo/'LICENSE'
    if not license_file.is_file() or 'MIT License' not in license_file.read_text():raise ValueError('project MIT license missing')
    def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
    commit=git('rev-parse','--verify','HEAD^{commit}')
    if git('status','--porcelain','--untracked-files=no'):raise ValueError('commit tracked source changes before preparing release provenance')
    stamp=int(git('show','-s','--format=%ct','HEAD'))
    created=datetime.datetime.fromtimestamp(stamp,datetime.timezone.utc).isoformat().replace('+00:00','Z')
    rows=[];seen=set()
    for artifact in artifacts:
        artifact=artifact.resolve()
        if not artifact.is_file() or artifact.name in seen:raise ValueError('missing artifact or duplicate basename')
        seen.add(artifact.name);check_members(artifact)
        signature='unverified'
        if apksigner and artifact.suffix=='.apk':
            subprocess.run([str(apksigner),'verify','--verbose',str(artifact)],check=True,capture_output=True,text=True)
            signature='verified (certificate/release approval still requires review)'
        rows.append({'name':artifact.name,'bytes':artifact.stat().st_size,'sha256':digest(artifact),'signature':signature})
    if not rows:raise ValueError('at least one artifact is required')
    evidence=json.loads(dependency_evidence.read_text()) if dependency_evidence else None
    if (attribution_manifest is None) != (ndk is None):
        raise ValueError('attribution manifest and NDK directory must be supplied together')
    attribution,coverage,notices=reviewed_attribution(attribution_manifest,ndk,evidence) if attribution_manifest else (None,None,[])
    dependencies,dependency_ids=dependency_packages(evidence,rows,coverage) if evidence is not None else ([],[])
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,commit+version+json.dumps([rows,evidence,attribution],sort_keys=True))
    source={'name':'missionthunderbolt-source','SPDXID':'SPDXRef-Source','versionInfo':commit,
            'downloadLocation':'https://github.com/pizzaexperiments/missionthunderbolt',
            'filesAnalyzed':False,'licenseDeclared':'MIT','licenseConcluded':'NOASSERTION',
            'copyrightText':'Copyright (c) 2026 Mission Thunderbolt contributors'}
    packages=[source];relationships=[{'spdxElementId':'SPDXRef-DOCUMENT','relationshipType':'DESCRIBES','relatedSpdxElement':'SPDXRef-Source'}]
    for index,row in enumerate(rows):
        identifier=f'SPDXRef-Artifact-{index}'
        packages.append({'name':row['name'],'SPDXID':identifier,'versionInfo':version,'downloadLocation':'NOASSERTION',
                         'filesAnalyzed':False,'licenseDeclared':'NOASSERTION','licenseConcluded':'NOASSERTION',
                         'copyrightText':'NOASSERTION','checksums':[{'algorithm':'SHA256','checksumValue':row['sha256']}]})
        relationships.append({'spdxElementId':identifier,'relationshipType':'OTHER','relatedSpdxElement':'SPDXRef-Source',
                              'comment':'Source checkout recorded; artifact correspondence requires build provenance review'})
        for dependency_id in dependency_ids:
            relationships.append({'spdxElementId':identifier,'relationshipType':'STATIC_LINK','relatedSpdxElement':dependency_id})
    packages.extend(dependencies)
    spdx={'spdxVersion':'SPDX-2.3','dataLicense':'CC0-1.0','SPDXID':'SPDXRef-DOCUMENT',
          'name':f'MissionThunderbolt-{version}-review','documentNamespace':f'https://spdx.org/spdxdocs/missionthunderbolt-{namespace}',
          'creationInfo':{'created':created,'creators':['Tool: mission-thunderbolt-release-prep-1']},
          'packages':packages,'relationships':relationships,
          'comment':'Review-only inventory with optional NDK static archive dependencies. License completeness and rights/signing approval require review.'}
    report={'schema':1,'status':'review-required','version':version,'source_commit':commit,'artifacts':rows,
            'project_license':'MIT','license_sha256':digest(license_file),
            'original_asset_distribution':'not authorized','published':False,
            'dependency_evidence':'android-dependencies.json' if evidence is not None else None,
            'component_attribution':'android-ndk-attribution.json' if attribution is not None else None,
            'attribution_status':'notice-evidence-only; archive licenses unresolved' if attribution is not None else 'unreviewed',
            'limitations':['Package-path guard is not content-based rights verification',
                           'Transitive/native runtime dependencies require a separate license/SBOM review',
                           'Artifact hashes do not establish reproducible builds or device acceptance'],
            'tools':{'python':platform.python_version()}}
    output.parent.mkdir(parents=True,exist_ok=True);temp=Path(tempfile.mkdtemp(prefix='.release-review-',dir=output.parent))
    try:
        (temp/'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["name"]}\n' for r in rows))
        (temp/'release-review.json').write_text(json.dumps(report,indent=2)+'\n')
        (temp/'sbom.spdx.json').write_text(json.dumps(spdx,indent=2)+'\n')
        if evidence is not None:(temp/'android-dependencies.json').write_text(json.dumps(evidence,indent=2)+'\n')
        if attribution is not None:
            (temp/'android-ndk-attribution.json').write_text(json.dumps(attribution,indent=2)+'\n')
            (temp/'licenses').mkdir()
            for notice_path in notices:shutil.copy2(notice_path,temp/'licenses'/notice_path.name)
        shutil.copy2(license_file,temp/'LICENSE')
        notice=repo/'THIRD_PARTY_NOTICES.md'
        if notice.exists():shutil.copy2(notice,temp/notice.name)
        temp.rename(output)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--version',required=True);p.add_argument('--apksigner',type=Path)
    p.add_argument('--dependency-evidence',type=Path)
    p.add_argument('--attribution-manifest',type=Path,help='Exact archive/notice coverage; not archive-wide license clearance')
    p.add_argument('--ndk',type=Path,help='Installed NDK used to verify attribution and preserve its upstream notices')
    a=p.parse_args()
    try:report=prepare(Path(__file__).resolve().parents[1],a.artifact,a.output,a.version,a.apksigner,a.dependency_evidence,a.attribution_manifest,a.ndk)
    except (ValueError,OSError,subprocess.CalledProcessError,zipfile.BadZipFile,tarfile.TarError) as e:p.error(str(e))
    print(f'Prepared review metadata for {len(report["artifacts"])} artifact(s); no publication or rights approval performed')

if __name__=='__main__':main()
