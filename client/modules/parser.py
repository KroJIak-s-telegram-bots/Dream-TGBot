import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel

allObjects = {
    'logoutButton': {
        'name': 'form',
        'attrs': {'name': 'logout'}
    },
    'infoSections': {
        'name': 'div',
        'attrs': {'class': 'col23 first'}
    },
    'schoolName': {
        'name': 'a',
        'attrs': {'title': 'На главную страницу школы'}
    },
    'className': {
        'name': 'h2'
    },
    'photo': {
        'name': 'img'
    },
    'userInfo': {
        'name': 'span',
        'attrs': {'class': ''}
    }
}

class Errors():
    def getLogInError(self):
        return 'Ошибка входа в аккаунт.'

    def getWrongNameSchoolError(self):
        return 'Неверное название школы.'

    def getInfoError(self):
        return 'Не удалось найти данные о пользователе.'

    def getPhotoError(self):
        return 'Не удалось найти фото пользователя.'

    def getUserInfoError(self):
        return 'Не удалось найти информацию о пользователе.'

    def getClassNameError(self):
        return 'Не удалось найти класс.'

    def getSchoolNameError(self):
        return 'Не удалось найти название школы.'

    def getCommonError(self, error):
        return f'Системная ошибка: {error}'

class AccountDataResponse(BaseModel):
    data: dict | None = None
    error: str | None = None

class Session(requests.Session):
    def __init__(self, realSchoolName):
        super().__init__()
        self.realSchoolName = realSchoolName
        self.urlLogin = 'https://login.dnevnik.ru/login/esia/astrakhan'
        self.urlSettings = 'https://dnevnik.ru/v2/user/settings'
        self.urlSchool = 'https://schools.dnevnik.ru/v2/school'
        self.urlClass = 'https://schools.dnevnik.ru/v2/class'
        self.parserType = 'html.parser'
        self.err = Errors()

    def getAccountData(self, login, password):
        try:
            loginData = dict(login=login, password=password)
            loginResponse = self.postLogin(loginData)
            if not self.islogInAccount(loginResponse): return AccountDataResponse(error=Errors().getLogInError())
            schoolResponse = self.getSchool()
            schoolName = self.getSchoolInfo(schoolResponse)
            if schoolName != self.realSchoolName: return AccountDataResponse(error=Errors().getWrongNameSchoolError())
            classResponse = self.getClass()
            className = self.getClassName(classResponse)
            settingsResponse = self.getSettings()
            fullname, birthdate, photoUrl = self.getPersonalInfo(settingsResponse)
            accountData = self.fillAccountData(login, fullname, className, birthdate, photoUrl)
            return AccountDataResponse(data=accountData)
        except Exception as error:
            return AccountDataResponse(data={}, error=Errors().getCommonError(error))

    def fillAccountData(self, login, fullname, className, birthdate, photoUrl):
        data = dict(login=login,
                    fullname=fullname,
                    className=className,
                    birthdate=birthdate,
                    photoUrl=photoUrl)
        return data

    def getPersonalInfo(self, response):
        infoObject = allObjects['infoSections']
        infoSections = self.findObjects(response.text, infoObject['name'], infoObject['attrs'])
        if len(infoSections) < 2: raise ValueError(Errors().getInfoError())
        photoSection, userInfoSection = infoSections[:2]
        photoObject, userInfoObject = allObjects['photo'], allObjects['userInfo']
        photoUrlTitle = self.findObjectsInAnother(photoSection, photoObject['name'])
        if not photoUrlTitle: raise ValueError(Errors().getPhotoError())
        photoUrl = photoUrlTitle[0]['src']
        userInfoTitle = self.findObjectsInAnother(userInfoSection, userInfoObject['name'], userInfoObject['attrs'])
        if not userInfoTitle: raise ValueError(Errors().getUserInfoError())
        fullname, age, SNILS, birthdate = [elm.text for elm in userInfoTitle]
        return fullname, birthdate, photoUrl

    def getClassName(self, response):
        needObject = allObjects['className']
        classNameTitle = self.findObjects(response.text, needObject['name'])
        if not classNameTitle: raise ValueError(Errors().getClassNameError())
        className = classNameTitle[-1].text
        className = className.split(': ')[1]
        return className

    def getSchoolInfo(self, response):
        needObject = allObjects['schoolName']
        schoolNameTitle = self.findObjects(response.text, needObject['name'], needObject['attrs'])
        if not schoolNameTitle: raise ValueError(Errors().getSchoolNameError())
        schoolName = schoolNameTitle[-1].text
        return schoolName

    def islogInAccount(self, response):
        return self.isUserfeedPage(response.text)

    def isUserfeedPage(self, text):
        needObject = allObjects['logoutButton']
        logoutButtons = self.findObjects(text, needObject['name'], needObject['attrs'])
        return bool(logoutButtons)

    def findObjects(self, text, name, attrs=None):
        soup = BeautifulSoup(text, self.parserType)
        objects = soup.findAll(name, attrs)
        return objects

    def findObjectsInAnother(self, obj, name, attrs=None):
        objects = obj.findAll(name, attrs)
        return objects

    def postLogin(self, data):
        response = self.post(self.urlLogin, data=data)
        return response

    def getSettings(self):
        response = self.get(self.urlSettings)
        return response

    def getSchool(self):
        response = self.get(self.urlSchool)
        return response

    def getClass(self):
        response = self.get(self.urlClass)
        return response
