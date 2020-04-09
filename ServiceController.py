import os
from pystemd.systemd1 import Unit

class ServiceController(object):

    def __init__(self, unit):
        self.unit = Unit(bytes(unit, 'utf-8'), _autoload=True)
        
    def isActive(self):
        if self.unit.Unit.ActiveState == b'active':
            return True
        else:
            return False
    
    def status(self):
        return (self.unit.Unit.SubState).decode()

    def start(self):
        self.unit.Unit.Start(b'replace')

    def stop(self):
        self.unit.Unit.Stop(b'replace')
