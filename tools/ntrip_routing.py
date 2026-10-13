"""Validated receiver routing and EX commands for independent NTRIP services."""
from dataclasses import dataclass, field
import math
from pathlib import Path
import re
from urllib.parse import quote
from usb_identity import stable_path, device_key

CHANNELS = tuple('ABCDEF')
FORMATS = {'sbf', 'ubx', 'rtcm3', 'unicore'}
DEFAULT_MESSAGES = '1004,1005(10),1006,1008(10),1012,1019,1020,1033(10),1042,1045,1046,1077,1087,1097,1107,1127,1230'

def value(config, section, key, default=''):
    return config.get(section, key, fallback=default).strip().strip("'")

def port_number(value):
    if not str(value).isdigit() or not 1 <= int(value) <= 65535:
        raise ValueError('Port must be between 1 and 65535')
    return int(value)

@dataclass(frozen=True)
class ReceiverSource:
    identity: str
    label: str
    format: str
    port: int
    device: str = ''
    baudrate: int = 115200

@dataclass(frozen=True)
class NtripRoute:
    channel: str
    source: ReceiverSource
    caster: str
    port: int
    mountpoint: str
    messages: str
    password: str = field(repr=False)
    receiver_options: str = ''

def source_catalog(config):
    main = ReceiverSource('main', value(config, 'main', 'receiver') or 'Main receiver', value(config,'main','receiver_format'), port_number(value(config,'main','tcp_port')))
    result = {'main': main}
    ports = {main.port}
    main_device = value(config, 'main', 'com_port')
    if main_device and not main_device.startswith('/'):
        main_device = '/dev/' + main_device
    devices = {device_key(main_device)} if main_device else set()
    for section in config.sections():
        if not section.startswith('receiver_stream_'):
            continue
        identity = section[len('receiver_stream_'):]
        if not re.fullmatch(r'[a-z0-9_-]{1,48}',identity) or identity=='main':
            raise ValueError('Invalid receiver identity')
        prefix = 'stream_'+identity+'_'
        fmt = value(config,section,prefix+'format')
        port = port_number(value(config,section,prefix+'port'))
        device = value(config,section,prefix+'device')
        # This catalog reads metadata only: no device is opened or queried.
        path = Path(device)
        if not stable_path(device):
            raise ValueError('Use a stable USB identity or physical port')
        physical_device = device_key(device)
        if fmt not in FORMATS or port in ports or physical_device in devices:
            raise ValueError('Receiver format, local port or device conflicts')
        baudrate = int(value(config,section,prefix+'baudrate','115200'))
        if baudrate not in (9600,19200,38400,57600,115200,230400,460800,921600):
            raise ValueError('Unsupported serial baudrate')
        label=value(config,section,prefix+'label',identity)
        result[identity]=ReceiverSource(identity,label,fmt,port,device,baudrate)
        ports.add(port);devices.add(physical_device)
    if len(result)>16:raise ValueError('At most 16 receiver sources are supported')
    return result

def route_settings(config,channel):
    if channel not in CHANNELS:raise ValueError('Invalid NTRIP channel')
    section='ntrip_'+channel;suffix=channel.lower()
    keys=('svr_addr_'+suffix,'svr_port_'+suffix,'svr_pwd_'+suffix,'mnt_name_'+suffix,'rtcm_msg_'+suffix,'ntrip_'+suffix+'_receiver_options','ntrip_'+suffix+'_source')
    defaults=('', '2101', '', '', DEFAULT_MESSAGES, '', 'main')
    return {key:value(config,section,key,default) for key,default in zip(keys,defaults)}

def resolve_route(config,channel):
    settings=route_settings(config,channel);suffix=channel.lower();catalog=source_catalog(config)
    identity=settings['ntrip_'+suffix+'_source']
    if identity not in catalog:raise ValueError('Selected receiver is unavailable')
    caster=settings['svr_addr_'+suffix]
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.-]*',caster):raise ValueError('Invalid caster hostname or IPv4 address')
    mount=settings['mnt_name_'+suffix]
    if not re.fullmatch(r'[A-Za-z0-9_-]+',mount):raise ValueError('Set a valid mountpoint')
    messages=settings['rtcm_msg_'+suffix]
    for token in messages.split(','):
        match=re.fullmatch(r'(\d{4})(?:\((\d+(?:\.\d+)?)\))?',token)
        if not match or not 1001<=int(match[1])<=4095 or (match[2] is not None and not 0<float(match[2])<=86400):raise ValueError('Invalid RTCM message selection')
    options=settings['ntrip_'+suffix+'_receiver_options']
    if any(ord(c)<32 for c in options):raise ValueError('Invalid receiver options')
    if not re.fullmatch(r'[a-z0-9]+',catalog[identity].format):raise ValueError('Configure the receiver input format first')
    return NtripRoute(channel,catalog[identity],caster,port_number(settings['svr_port_'+suffix]),mount,messages,settings['svr_pwd_'+suffix],options)

def ex_command(binary,route,position,output=None):
    values=position.split() if isinstance(position,str) else list(position)
    coords=list(map(float,values))
    if len(coords)!=3 or not all(math.isfinite(v) for v in coords) or not -90<=coords[0]<=90 or not -180<=coords[1]<=180:raise ValueError('Invalid base coordinates')
    if not output and any(c in route.password for c in '@/#?\r\n'):
        raise ValueError('Password contains a delimiter unsupported by the RTKLIB stream URL')
    destination=output or 'ntrips://:'+route.password+'@'+route.caster+':'+str(route.port)+'/'+route.mountpoint+'#rtcm3'
    command=[str(binary),'-in','tcpcli://127.0.0.1:'+str(route.source.port)+'#'+route.source.format,'-msg',route.messages,'-out',destination,'-p',*map(str,values)]
    if route.receiver_options:command.extend(['-opt',route.receiver_options])
    return command


def settings_context(config, installed_channels=()):
    catalog=source_catalog(config)
    channels=[]
    labels=('Caster address','Caster port','Password','Mountpoint','RTCM messages','Receiver options')
    types=('text','number','password','text','text','text')
    for letter in CHANNELS:
        lower=letter.lower(); settings=route_settings(config,letter)
        fields=[]
        for key,label,kind in zip(list(settings)[:6],labels,types):
            fields.append({'name':key,'label':label,'type':kind,'value':settings[key],'required':label in ('Caster address','Caster port','Mountpoint','RTCM messages')})
        identity=settings['ntrip_'+lower+'_source']
        channels.append({'letter':letter,'lower':lower,'installed':letter in installed_channels,'source':identity,'source_missing':identity not in catalog,'fields':fields})
    return {'receiver_sources':list(catalog.values()),'ntrip_channels':channels}


def desired_sources(config, active_channels):
    catalog=source_catalog(config)
    result={}
    for channel in active_channels:
        if channel not in CHANNELS:raise ValueError('Invalid active channel')
        source_id=route_settings(config,channel)['ntrip_'+channel.lower()+'_source']
        if source_id not in catalog:raise ValueError('Selected receiver is unavailable: '+source_id)
        if source_id!='main':result[source_id]=catalog[source_id]
    return result

def validate_channel_update(config,channel,submitted):
    import copy
    allowed=set(route_settings(config,channel))
    if not submitted or not set(submitted)<=allowed:raise ValueError('Unexpected NTRIP settings')
    if any(not isinstance(v,str) or "'" in v or any(ord(c)<32 for c in v) for v in submitted.values()):raise ValueError('Invalid NTRIP setting value')
    candidate=copy.deepcopy(config);section='ntrip_'+channel
    if not candidate.has_section(section):candidate.add_section(section)
    for key,v in submitted.items():candidate.set(section,key,v)
    resolve_route(candidate,channel)
    return candidate


def register_source(config,payload):
    import copy
    identity=payload.get('identity','');label=payload.get('label','')
    if not isinstance(identity,str) or not re.fullmatch(r'[a-z0-9_-]{1,48}',identity) or identity=='main':raise ValueError('Invalid receiver identity')
    if not isinstance(label,str) or not re.fullmatch(r'[\w ._-]{1,80}',label):raise ValueError('Invalid receiver name')
    section='receiver_stream_'+identity
    if config.has_section(section):raise ValueError('This receiver identity is already registered')
    allowed={'identity','label','device','format','port','baudrate'}
    if not set(payload)<=allowed:raise ValueError('Unexpected receiver setting')
    device=payload.get('device','')
    if not stable_path(device):raise ValueError('Use a stable USB data port')
    if 'Septentrio' in device and not device.endswith('-if02'):raise ValueError('Select the Septentrio data port, not its control port')
    candidate=copy.deepcopy(config);prefix='stream_'+identity+'_'
    candidate[section]={prefix+key:str(payload.get(key,'115200' if key=='baudrate' else '')) for key in ('label','device','format','port','baudrate')}
    source_catalog(candidate)
    return candidate
