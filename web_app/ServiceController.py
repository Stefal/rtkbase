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
    
    def get_nrestart(self):
        """
            Get the number of restarts since the last service startup
        """
        return self.unit.Service.NRestarts

    def get_result(self):
        """
            Get the unit return status.
            success => it's ok
            exit-code => str2str doesn't start successfully
            We can read a success between the startup and the first error
        """
        if "org.freedesktop.systemd1.Service" in self.unit._interfaces:
            return self.unit.Service.Result.decode()
        elif "org.freedesktop.systemd1.Timer" in self.unit._interfaces:
            return self.unit.Timer.Result.decode()

    def getUser(self):
        return self.unit.Service.User.decode()
    
    def status(self):
        """
            get the unit status:
            auto-restart: the service will restart later
            start: the service is starting
            running; the service is running
        """
        return (self.unit.Unit.SubState).decode()

    def start(self):
        """
            Start the unit.
            It will reset the failed counter before starting the unit.
        """
        self.manager.Manager.ResetFailedUnit(self.unit.Unit.Names[0])
        self.manager.Manager.EnableUnitFiles(self.unit.Unit.Names, False, True)
        return self.unit.Unit.Start(b'replace')
        
    def stop(self):
        """
            Stop the unit.
        """
        self.manager.Manager.DisableUnitFiles(self.unit.Unit.Names, False)
        return self.unit.Unit.Stop(b'replace')
        
    def restart(self):
        """
            Restart the unit.
        """
        return self.unit.Unit.Restart(b'replace')