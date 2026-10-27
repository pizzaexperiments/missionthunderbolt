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


def prepare(repo,artifacts,output,version,apksigner=None):
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
    namespace=uuid.uuid5(uuid.NAMESPACE_URL,commit+version+json.dumps(rows,sort_keys=True))
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
    spdx={'spdxVersion':'SPDX-2.3','dataLicense':'CC0-1.0','SPDXID':'SPDXRef-DOCUMENT',
          'name':f'MissionThunderbolt-{version}-review','documentNamespace':f'https://spdx.org/spdxdocs/missionthunderbolt-{namespace}',
          'creationInfo':{'created':created,'creators':['Tool: mission-thunderbolt-release-prep-1']},
          'packages':packages,'relationships':relationships,
          'comment':'Review-only artifact inventory. Not a complete transitive dependency SBOM or rights/signing approval.'}
    report={'schema':1,'status':'review-required','version':version,'source_commit':commit,'artifacts':rows,
            'project_license':'MIT','license_sha256':digest(license_file),
            'original_asset_distribution':'not authorized','published':False,
            'limitations':['Package-path guard is not content-based rights verification',
                           'Transitive/native runtime dependencies require a separate license/SBOM review',
                           'Artifact hashes do not establish reproducible builds or device acceptance'],
            'tools':{'python':platform.python_version()}}
    output.parent.mkdir(parents=True,exist_ok=True);temp=Path(tempfile.mkdtemp(prefix='.release-review-',dir=output.parent))
    try:
        (temp/'SHA256SUMS').write_text(''.join(f'{r["sha256"]}  {r["name"]}\n' for r in rows))
        (temp/'release-review.json').write_text(json.dumps(report,indent=2)+'\n')
        (temp/'sbom.spdx.json').write_text(json.dumps(spdx,indent=2)+'\n')
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
    a=p.parse_args()
    try:report=prepare(Path(__file__).resolve().parents[1],a.artifact,a.output,a.version,a.apksigner)
    except (ValueError,OSError,subprocess.CalledProcessError,zipfile.BadZipFile,tarfile.TarError) as e:p.error(str(e))
    print(f'Prepared review metadata for {len(report["artifacts"])} artifact(s); no publication or rights approval performed')

if __name__=='__main__':main()
