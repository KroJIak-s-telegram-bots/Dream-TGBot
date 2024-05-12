
class configCategoryObject():
    def __init__(self, config, nameCategory):
        self.config = config
        self.nameCategory = nameCategory

    def get(self, elm):
        return self.config.get(self.nameCategory, elm)

class Telegram(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Telegram')
        self.token = self.get('token')
        self.alias = self.get('alias')

class School(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'School')
        self.realSchoolName = self.get('realSchoolName')

class Data(configCategoryObject):
    def __init__(self, config):
        super().__init__(config, 'Data')
        self.usersDatabasePath = self.get('usersDatabasePath')
        self.ordersDatabasePath = self.get('ordersDatabasePath')
        self.availableLangs = self.get('availableLangs')
        self.availableLangs = self.availableLangs.split(', ')
        self.defaultLang = self.get('defaultLang')
        self.secretKey = self.get('secretKey')

class ListBlockCallback():
    def __init__(self):
        self.buttonLeft = 'lb.left'
        self.buttonRight = 'lb.right'

class Prefix():
    def __init__(self):
        self.category = 'ctg'
        self.product = 'pdc'
        self.remove = 'rmv'

class CallbackData():
    def __init__(self):
        self.listBlock = ListBlockCallback()
        self.prefix = Prefix()
        self.empty = 'empty'
        self.order = 'order'

class ListBlock():
    def __init__(self):
        self.heightSize = 4

class ConstPlenty():
    def __init__(self, config=None):
        if config: self.addConstFromConfig(config)
        self.commonPath = '/'.join(__file__.split('/')[:-2]) + '/'
        self.mainPath = '/'.join(__file__.split('/')[:-3]) + '/'
        self.callback = CallbackData()
        self.listblock = ListBlock()

    def addConstFromConfig(self, config):
        self.telegram = Telegram(config)
        self.school = School(config)
        self.data = Data(config)


