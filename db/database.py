import json
import os
import shutil

class dbWorker():
    def __init__(self, databasePath, fileName, defaultDBFileName='default.json'):
        self.databasePath = databasePath
        self.fileName = fileName
        if not self.isExists():
            shutil.copyfile(databasePath + defaultDBFileName,
                            databasePath + fileName)

    def isExists(self):
        files = os.listdir(self.databasePath)
        return self.fileName in files

    def get(self):
        with open(self.databasePath + self.fileName) as file:
            dbData = json.load(file)
        return dbData

    def save(self, dbData):
        with open(self.databasePath + self.fileName, 'w', encoding='utf-8') as file:
            json.dump(dbData, file, indent=4, ensure_ascii=False)

class dbLocalWorker():
    def __init__(self):
        self.db = {}

    def isUserExists(self, userId):
        return str(userId) in self.db

    def addNewUser(self, userId):
        self.db[str(userId)] = dict(mode=-1,
                                    pageNumber=1,
                                    listBlockLevel=None,
                                    selectedCategoryId=None,
                                    lastLBMessageId=None,
                                    dnevnikru=self.getDnevnikruData())

    def setModeInUser(self, userId, mode):
        self.db[str(userId)]['mode'] = mode

    def getModeFromUser(self, userId):
        return self.db[str(userId)]['mode']

    def getLoginFromUser(self, userId):
        return self.db[str(userId)]['dnevnikru']['login']

    def setLoginInUser(self, userId, login):
        self.db[str(userId)]['dnevnikru']['login'] = login

    def getPasswordFromUser(self, userId):
        return self.db[str(userId)]['dnevnikru']['password']

    def setPasswordInUser(self, userId, password):
        self.db[str(userId)]['dnevnikru']['password'] = password

    def getMessagesFromUser(self, userId):
        return self.db[str(userId)]['dnevnikru']['messages']

    def addMessageInUser(self, userId, messageId):
        self.db[str(userId)]['dnevnikru']['messages'].append(messageId)

    def clearDnevnikruInUser(self, userId):
        self.db[str(userId)]['dnevnikru'] = self.getDnevnikruData()

    def getDnevnikruData(self):
        return dict(login=None,
                    password=None,
                    messages=[])

    def getPageNumber(self, userId):
        return self.db[str(userId)]['pageNumber']

    def setPageNumber(self, userId, pageNumber):
        self.db[str(userId)]['pageNumber'] = pageNumber

    def getListBlockLevel(self, userId):
        return self.db[str(userId)]['listBlockLevel']

    def setListBlockLevel(self, userId, level):
        self.db[str(userId)]['listBlockLevel'] = level

    def getCategoryIdFromUser(self, userId):
        return self.db[str(userId)]['selectedCategoryId']

    def setCategoryIdInUser(self, userId, categoryId):
        self.db[str(userId)]['selectedCategoryId'] = categoryId

    def getLastLBMessageId(self, userId):
        return self.db[str(userId)]['lastLBMessageId']

    def setLastLBMessageId(self, userId, messageId):
        self.db[str(userId)]['lastLBMessageId'] = messageId

class dbUsersWorker(dbWorker):
    def getUserIds(self):
        dbData = self.get()
        userIds = tuple(dbData['users'].keys())
        return userIds

    def getPermissions(self):
        dbData = self.get()
        permissions = dbData['permissions']
        return permissions

    def getPermission(self, userId):
        dbData = self.get()
        permisson = dbData['users'][str(userId)]['permission']
        return permisson

    def isUnregistered(self, userId):
        permisson = self.getPermission(userId)
        return permisson == 'default'

    def isGuest(self, userId):
        permisson = self.getPermission(userId)
        return permisson == 'guest'

    def isAdmin(self, userId):
        permisson = self.getPermission(userId)
        return permisson == 'admin'

    def isUserExists(self, userId):
        dbData = self.get()
        return str(userId) in dbData['users']

    def addNewUser(self, userId, login, fullname, lang, permission='default', mode=-1, cart=[]):
        dbData = self.get()
        newUser = dict(login=login,
                       fullname=fullname,
                       lang=lang,
                       permission=permission,
                       mode=mode,
                       cart=cart,
                       dnevnikru=self.getDnevnikruData())
        dbData['users'][str(userId)] = newUser
        self.save(dbData)

    def getDnevnikruData(self):
        return dict(eula=False,
                    data=None)

    def getFromUser(self, userId, key):
        dbData = self.get()
        return dbData['users'][str(userId)][str(key)]

    def setInUser(self, userId, key, value):
        dbData = self.get()
        dbData['users'][str(userId)][str(key)] = value
        self.save(dbData)

    def addNewMessageInUser(self, userId, role, message):
        dbData = self.get()
        curMessage = {'role': role,
                      'content': message}
        dbData['users'][str(userId)]['messages'].append(curMessage)
        self.save(dbData)

    def getAccountDataFromUser(self, userId):
        dbData = self.get()
        return dbData['users'][str(userId)]['dnevnikru']['data']

    def addAccountDataInUser(self, userId, data):
        dbData = self.get()
        dbData['users'][str(userId)]['dnevnikru']['data'] = data
        self.save(dbData)

    def removeAccountDataFromUser(self, userId):
        dbData = self.get()
        userLogin = dbData['users'][str(userId)]['dnevnikru']['data']['login']
        dbData['users'][str(userId)]['dnevnikru'] = self.getDnevnikruData()
        dbData['verifiedAccounts'].pop(dbData['verifiedAccounts'].index(userLogin))
        self.save(dbData)

    def confirmEulaInUser(self, userId):
        dbData = self.get()
        dbData['users'][str(userId)]['dnevnikru']['eula'] = True
        self.save(dbData)

    def isConfirmedEula(self, userId):
        dbData = self.get()
        result = dbData['users'][str(userId)]['dnevnikru']['eula']
        return result

    def checkLoginInVerifiedList(self, login):
        dbData = self.get()
        return login in dbData['verifiedAccounts']

    def addLoginToVerifiedList(self, login):
        dbData = self.get()
        dbData['verifiedAccounts'].append(login)
        self.save(dbData)

    def addProductToCart(self, userId, productId):
        dbData = self.get()
        dbData['users'][str(userId)]['cart'].append(productId)
        self.save(dbData)

    def removeProductFromCart(self, userId, productId):
        dbData = self.get()
        userCart = dbData['users'][str(userId)]['cart']
        dbData['users'][str(userId)]['cart'].pop(userCart.index(productId))
        self.save(dbData)

    def getProductIdsFromCart(self, userId):
        dbData = self.get()
        return dbData['users'][str(userId)]['cart']

class dbOrdersWorker(dbWorker):
    def getAllProducts(self):
        dbData = self.get()
        allProducts = dbData['products']
        return allProducts

    def getProducts(self, categoryId):
        dbData = self.get()
        allProducts = dbData['products']
        products = {key: product for key, product in allProducts.items()
                                 if str(product['categoryId']) == categoryId}
        return products

    def getProduct(self, id):
        dbData = self.get()
        product = dbData['products'][str(id)]
        return product

    def getCategories(self):
        dbData = self.get()
        categories = dbData['categories']
        return categories

    def getCategory(self, id):
        dbData = self.get()
        category = dbData['categories'][str(id)]
        return category

    def addNewProduct(self, name, price, category):
        dbData = self.get()
        newProduct = dict(name=name,
                          price=price,
                          category=category)
        dbData['products'].append(newProduct)
        self.save(dbData)