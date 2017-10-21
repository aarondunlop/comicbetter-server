from app.models import Issue, Device

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
        for k in self.kwargs:
            print(k)
        print(device)
        return 'ok'
