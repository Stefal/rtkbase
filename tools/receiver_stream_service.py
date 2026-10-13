"""Open registered GNSS sources while selected by an active NTRIP service."""
import argparse
import configparser
from dataclasses import asdict
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from receiver_stream_fanout import PassiveFanout, SerialInput
from ntrip_routing import desired_sources

class StreamCoordinator:
    def __init__(self, factory):
        self.factory=factory;self.streams={};self.retry_after={};self.errors={}
    def reconcile(self, desired, now):
        for identity,(spec,stream) in list(self.streams.items()):
            if desired.get(identity)!=spec or stream.error:
                if stream.error:
                    self.errors[identity]=stream.error;self.retry_after[identity]=now+30
                stream.close();del self.streams[identity]
        for identity,spec in desired.items():
            if identity in self.streams or now<self.retry_after.get(identity,0):continue
            try:
                stream=self.factory(spec);self.streams[identity]=(spec,stream)
                self.errors.pop(identity,None)
            except Exception as error:
                self.errors[identity]=str(error);self.retry_after[identity]=now+30
    def close(self):
        for identity,(_,stream) in list(self.streams.items()):
            stream.close();del self.streams[identity]

class LockedSerialInput:
    def __init__(self,root,spec):
        import fcntl
        flags=os.O_RDWR|os.O_CREAT|getattr(os,'O_NOFOLLOW',0)
        self.fd=os.open(root/'.receiver-configuration.lock',flags,0o600)
        try:
            owner=(root/'settings.conf').stat();os.fchown(self.fd,owner.st_uid,owner.st_gid)
            fcntl.flock(self.fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
            self.source=SerialInput(spec.device,spec.baudrate)
        except Exception:os.close(self.fd);raise
    def read(self):return self.source.read()
    def close(self):
        try:self.source.close()
        finally:os.close(self.fd)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    if os.geteuid()!=0:parser.error('Root required to verify serial ownership')
    stopped=False
    def stop(*args):
        nonlocal stopped
        stopped=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    def factory(spec):
        stream=PassiveFanout(lambda:LockedSerialInput(args.root,spec),port=spec.port)
        stream.start_reading();return stream
    coordinator=StreamCoordinator(factory)
    try:
        while not stopped:
            try:
                config=configparser.ConfigParser(interpolation=None)
                config.read([args.root/'settings.conf.default',args.root/'settings.conf'])
                units=['str2str_ntrip_'+c+'.service' for c in 'ABCDEF']
                result=subprocess.run(['systemctl','show','--no-pager','--property=Id,ActiveState']+units,capture_output=True,text=True,timeout=5)
                if result.returncode:raise RuntimeError('Cannot read NTRIP service states')
                active=[]
                for block in result.stdout.split('\n\n'):
                    properties=dict(line.split('=',1) for line in block.splitlines() if '=' in line)
                    if properties.get('ActiveState') in ('active','activating'):
                        name=properties.get('Id','')
                        if name in units:active.append(name[len('str2str_ntrip_')])
                coordinator.reconcile(desired_sources(config,active),time.monotonic())
                for identity,message in coordinator.errors.items():print(identity+': '+message,flush=True)
            except Exception as error:
                print(type(error).__name__+': '+str(error),flush=True)
                coordinator.reconcile({},time.monotonic())
            deadline=time.monotonic()+2
            while not stopped and time.monotonic()<deadline:time.sleep(.1)
    finally:coordinator.close()

if __name__=='__main__':main()
