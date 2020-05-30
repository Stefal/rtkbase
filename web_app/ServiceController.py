import os
from pystemd.systemd1 import Unit
from pystemd.systemd1 import Manager

class ServiceController(object):
    """
        A simple wrapper around pystemd to manage systemd services
    """
    
    manager = Manager(_autoload=True)

    def __init__(self, unit):
        """
            param: unit: a systemd unit name (ie str2str_tcp.service...)
        """
        self.unit = Unit(bytes(unit, 'utf-8'), _autoload=True)
        
    def isActive(self):
        if self.unit.Unit.ActiveState == b'active':
            return True
        elif self.unit.Unit.ActiveState == b'activating':
            #TODO manage this transitionnal state differently
            return True
        else:
            return False

    def getUser(self):
        return self.unit.Service.User.decode()
    
    def status(self):
        return (self.unit.Unit.SubState).decode()

    def start(self):
        self.manager.Manager.EnableUnitFiles(self.unit.Unit.Names, False, True)
        return self.unit.Unit.Start(b'replace')
        
    def stop(self):
        self.manager.Manager.DisableUnitFiles(self.unit.Unit.Names, False)
        return self.unit.Unit.Stop(b'replace')
        
    def restart(self):
        return self.unit.Unit.Restart(b'replace')