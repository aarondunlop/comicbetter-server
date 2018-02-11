from app.models import Issue, Device
import logging
logger = logging.getLogger(__name__)

class SBDevices(object):
    #def __init__(self, id, **kwargs):
    def __init__(self, id, **kwargs):
        self.id=id
        self.kwargs=kwargs
        for key, value in kwargs.items():
            newvalue=str(value[0]) if isinstance(value, list) else str(value)
            setattr(self, key, newvalue)

    def sync(self):
        return self.id

    def synced(self, device):
        return 'ok'
