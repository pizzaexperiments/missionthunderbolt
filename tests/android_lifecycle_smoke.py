#!/usr/bin/env python3
"""Explicit-device integration check; uses only the synthetic app's state."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import xml.etree.ElementTree as ET

PACKAGE='org.missionthunderbolt.prototype'

class CliTransport:
    def __init__(self,serial):self.prefix=['adb','-s',serial]
    def shell(self,*args):return subprocess.check_output([*self.prefix,'shell',*args],text=True,timeout=240)
    def pull(self,source,dest):subprocess.run([*self.prefix,'pull',source,str(dest)],check=True,capture_output=True,timeout=240)

class DirectEmulatorTransport:
    def __init__(self,port):
        from adb_shell.adb_device import AdbDeviceTcp
        self.adb=AdbDeviceTcp('127.0.0.1',port,default_transport_timeout_s=90)
        self.adb.connect(auth_timeout_s=30)
    def shell(self,*args):return self.adb.shell(shlex.join(args),transport_timeout_s=90,read_timeout_s=180,timeout_s=180)
    def pull(self,source,dest):self.adb.pull(source,str(dest),transport_timeout_s=90)


def run(transport,output,check_control_placement=False):
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as temporary:
        xml=Path(temporary)/'ui.xml'
        def nodes():
            transport.shell('uiautomator','dump','/data/local/tmp/mt-ui.xml')
            transport.pull('/data/local/tmp/mt-ui.xml',xml)
            return list(ET.parse(xml).iter('node'))
        def status():return next(n.attrib['text'] for n in nodes() if n.attrib.get('resource-id','').endswith(':id/status'))
        def tap(identifier):
            node=next(n for n in nodes() if n.attrib.get('resource-id','').endswith(':id/'+identifier))
            x1,y1,x2,y2=map(int,re.findall(r'\d+',node.attrib['bounds']))
            transport.shell('input','tap',str((x1+x2)//2),str((y1+y2)//2))
        def placement():return next(n.attrib['text'] for n in nodes() if n.attrib.get('resource-id','').endswith(':id/controls_position'))
        transport.shell('am','force-stop',PACKAGE)  # Start with a fresh view/scroll position; demo is reset below.
        transport.shell('am','start','-W','-n',PACKAGE+'/.MainActivity')
        tap('restart')
        assert 'Turns: 0' in status(),'restart failed'
        for turn in (1,2):
            transport.shell('input','keyevent','22')
            assert f'Turns: {turn}' in status(),'keyboard move lost after touch input'
        before=status()
        if check_control_placement:
            for _ in range(3):
                if placement()=='Controls: Left':break
                tap('controls_position')
            assert placement()=='Controls: Left','could not select left controls'
            assert status()==before,'placement changed simulation'
        transport.shell('input','keyevent','3');nodes()  # Wait for Home UI / onPause.
        transport.shell('am','force-stop',PACKAGE)
        launch=transport.shell('am','start','-W','-n',PACKAGE+'/.MainActivity')
        after=status();assert before==after,'state lost across background/process death'
        if check_control_placement:assert placement()=='Controls: Left','control setting lost across process death'
        for _ in range(3):
            transport.shell('input','keyevent','3');nodes()
            transport.shell('am','start','-W','-n',PACKAGE+'/.MainActivity')
            assert status()==before,'state lost across background/foreground'
            if check_control_placement:assert placement()=='Controls: Left','control setting lost across background/foreground'
        crashes=transport.shell('logcat','-d','-b','crash')
        assert 'Process: '+PACKAGE+',' not in crashes,'app crash in device crash buffer'
        package_info=transport.shell('dumpsys','package',PACKAGE)
        target_sdk=int(re.search(r'targetSdk=(\d+)',package_info).group(1))
        report={'target_sdk':target_sdk,'api':transport.shell('getprop','ro.build.version.sdk').strip(),
                'abi':transport.shell('getprop','ro.product.cpu.abi').strip(),'before':before,'after':after,
                'background_cycles':3,'app_crash_buffer_clean':True,'launch':launch}
        if check_control_placement:report['control_placement']='Controls: Left'
        (output/'android-lifecycle.json').write_text(json.dumps(report,indent=2)+'\n')
        transport.shell('screencap','-p','/data/local/tmp/mt-demo.png')
        transport.pull('/data/local/tmp/mt-demo.png',output/'android-demo.png')
        return report


def main():
    p=argparse.ArgumentParser(description=__doc__);selection=p.add_mutually_exclusive_group(required=True)
    selection.add_argument('--serial');selection.add_argument('--direct-emulator',type=int,metavar='LOCAL_ADBD_PORT')
    p.add_argument('--output',type=Path,default=Path('dist/verification'))
    p.add_argument('--check-control-placement',action='store_true');a=p.parse_args()
    transport=CliTransport(a.serial) if a.serial else DirectEmulatorTransport(a.direct_emulator)
    report=run(transport,a.output,a.check_control_placement)
    print(f'Lifecycle smoke passed on API {report["api"]} {report["abi"]}; report and synthetic screenshot saved')

if __name__=='__main__':main()
