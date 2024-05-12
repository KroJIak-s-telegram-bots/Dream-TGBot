from configparser import ConfigParser
import sys

def getConfigObject(botConfigPath, commonPath=''):
    config = ConfigParser()
    config.read(commonPath + botConfigPath)
    return config

def changeWorkingPath(path):
    sys.path.insert(1, path)

def getPathAndFileName(fullPath):
    if not fullPath: return None, None
    path = fullPath.split('/')
    fileName = path.pop(-1)
    path = '/'.join(path) + '/'
    return path, fileName

def getDBWorkerObject(tableName, mainPath, commonPath, databasePath=None):
    path, fileName = getPathAndFileName(databasePath)
    changeWorkingPath(mainPath)
    from db.database import dbUsersWorker, dbOrdersWorker, dbLocalWorker
    match tableName:
        case 'users': resultDB = dbUsersWorker(mainPath + path, fileName)
        case 'orders': resultDB = dbOrdersWorker(mainPath + path, fileName)
        case 'local': resultDB = dbLocalWorker()
        case _: resultDB = None
    changeWorkingPath(commonPath)
    return resultDB