
class DataBase:
    def __init__(self):
        self._data = {}

    def getInfo(self, key):
        if key in self._data.keys():
            return self._data[key]
        
        return None
    
    def isInBase(self, key):
        if key in self._data.keys():
            return True
        
        return False
    
    def getDict(self):
        return self._data
    
    def saveInfo(self, key, info):
        self._data[key] = info