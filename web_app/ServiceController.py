import os
from pystemd.systemd1 import Unit
from pystemd.systemd1 import Manager

class ServiceController(object):
    
    manager = Manager(_autoload=True)

    def __init__(self, unit):
        self.unit = Unit(bytes(unit, 'utf-8'), _autoload=True)
        
    def isActive(self):
        if self.unit.Unit.ActiveState == b'active':
            return True
        elif self.unit.Unit.ActiveState == b'activating':
            #TODO manage this transitionnal state differently
            return True
        else:
            return False
    
    def status(self):
        return (self.unit.Unit.SubState).decode()

    def start(self):
        self.manager.Manager.EnableUnitFiles(self.unit.Unit.Names, False, True)
        return self.unit.Unit.Start(b'replace')
        
    def stop(self):
        self.manager.Manager.DisableUnitFiles(self.unit.Unit.Names, False)
        return self.unit.Unit.Stop(b'replace')
        
