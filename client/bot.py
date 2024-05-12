from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.utils.keyboard import InlineKeyboardMarkup
import asyncio
from utils.funcs import *
from utils.const import ConstPlenty
from traceback import format_exc
import json
import logging
from modules.parser import Session
from math import ceil

# SETTINGS
logging.basicConfig(level=logging.INFO)
const = ConstPlenty()
botConfig = getConfigObject('config/bot.ini', const.commonPath)
const.addConstFromConfig(botConfig)
dbUsers = getDBWorkerObject('users', const.mainPath, const.commonPath, databasePath=const.data.usersDatabasePath)
dbOrders = getDBWorkerObject('orders', const.mainPath, const.commonPath, databasePath=const.data.ordersDatabasePath)
dbLocal = getDBWorkerObject('local', const.mainPath, const.commonPath)
bot = Bot(const.telegram.token)
dp = Dispatcher()

def getTranslation(userId, key, inserts=[], lang=None):
    try:
        if not lang: lang = dbUsers.getFromUser(userId, 'lang')
        with open(f'lang/{lang}.json', encoding='utf-8') as langFile:
            langJson = json.load(langFile)
        text = langJson[key]
        if not inserts: return text
        for ins in inserts: text = text.replace('%{}%', str(ins), 1)
        return text
    except Exception:
        if dbUsers.isAdmin(userId): return getTranslation(userId, 'error.message', [format_exc()])
        else: return getTranslation(userId, 'error.message', ['wwc...'])

def getUserInfo(message):
    userInfo = { 'chatId': message.chat.id,
                 'userId': message.from_user.id,
                 'username': message.from_user.username,
                 'userFirstName': message.from_user.first_name,
                 'userFullName': message.from_user.full_name,
                 'messageId': message.message_id,
                 'userText': message.text }
    if not dbUsers.isUserExists(userInfo['userId']):
        permissions = dbUsers.getPermissions()
        lowestPermission = permissions['0']
        dbUsers.addNewUser(userInfo['userId'], userInfo['username'], userInfo['userFullName'], const.data.defaultLang, lowestPermission)
    if not dbLocal.isUserExists(userInfo['userId']):
        dbLocal.addNewUser(userInfo['userId'])
    if userInfo['userText'] == const.data.secretKey and dbUsers.isUnregistered(userInfo['userId']):
        dbUsers.setInUser(userInfo['userId'], 'permission', 'guest')
    print(' | '.join(list(map(str, userInfo.values())) + [str(dbLocal.getModeFromUser(userInfo['userId']))]))
    print(dbLocal.db[str(userInfo['userId'])])
    return userInfo

def getCountPages(countButtons):
    countPages = ceil(countButtons / const.listblock.heightSize)
    return countPages

def getListBlockKeyboard(userId, buttons, pageNumber, useLeft, useRight):
    heightSize = const.listblock.heightSize
    startList = (pageNumber-1) * heightSize
    endList = pageNumber * heightSize
    buttonsOnCurrentPage = buttons[startList:endList]
    countPages = getCountPages(len(buttons))
    pageNumber = min(pageNumber, countPages)
    controlButtons = getControlInlineButtons(userId, pageNumber, countPages, useLeft, useRight)
    buttonsOnCurrentPage += controlButtons
    inlineKeyboard = InlineKeyboardMarkup(inline_keyboard=buttonsOnCurrentPage)
    return inlineKeyboard

def getControlInlineButtons(userId, pageNumber, countPages, useLeft, useRight):
    leftKey = 'inlinebutton.left' if useLeft else 'inlinebutton.empty'
    leftCallback = const.callback.listBlock.buttonLeft if useLeft else const.callback.empty
    rightKey = 'inlinebutton.right' if useRight else 'inlinebutton.empty'
    rightCallback = const.callback.listBlock.buttonRight if useRight else const.callback.empty
    buttonLeft = types.InlineKeyboardButton(text=getTranslation(userId, leftKey),
                                            callback_data=leftCallback)
    buttonPage = types.InlineKeyboardButton(text=f'{pageNumber}/{countPages}',
                                            callback_data=const.callback.empty)
    buttonRight = types.InlineKeyboardButton(text=getTranslation(userId, rightKey),
                                             callback_data=rightCallback)
    inlineButtons = [[buttonLeft, buttonPage, buttonRight]]
    return inlineButtons

def getCurrentStatusControlButtons(userId, countButtons):
    countPage = getCountPages(countButtons)
    currentPage = dbLocal.getPageNumber(userId)
    useLeft = (currentPage - 1 > 0)
    useRight = (currentPage < countPage)
    return useLeft, useRight

def getNewStatusControlButtons(userId, callbackAction, countButtons):
    currentCallbacks = const.callback.listBlock
    countPage = getCountPages(countButtons)
    currentPage = dbLocal.getPageNumber(userId)
    useLeft, useRight = True, True
    match callbackAction:
        case currentCallbacks.buttonLeft:
            nextPage = max(1, currentPage - 1)
            doubleNextPage = max(1, currentPage - 2)
            useLeft = (nextPage != doubleNextPage)
            dbLocal.setPageNumber(userId, nextPage)
        case currentCallbacks.buttonRight:
            nextPage = min(countPage, currentPage + 1)
            doubleNextPage = min(countPage, currentPage + 2)
            useRight = (nextPage != doubleNextPage)
            dbLocal.setPageNumber(userId, nextPage)
    return useLeft, useRight

@dp.callback_query(F.data.startswith("lb."))
async def listBlockCallbacks(callback: types.CallbackQuery):
    userId = callback.from_user.id
    lbLevel = dbLocal.getListBlockLevel(userId)
    match lbLevel:
        case 'category':
            countButtons = len(getInlineButtonsCategories())
            useLeft, useRight = getNewStatusControlButtons(userId, callback.data, countButtons)
            resultKeyboard = getCategoryKeyboard(userId, useLeft, useRight)
        case 'product':
            userCategoryId = dbLocal.getCategoryIdFromUser(userId)
            countButtons = len(getInlineButtonsProducts(userCategoryId))
            useLeft, useRight = getNewStatusControlButtons(userId, callback.data, countButtons)
            resultKeyboard = getProductKeyboard(userId, userCategoryId, useLeft, useRight)
        case 'cart':
            countButtons = len(getInlineButtonsCart(userId))
            useLeft, useRight = getNewStatusControlButtons(userId, callback.data, countButtons)
            resultKeyboard = getCartKeyboard(userId, useLeft, useRight)
        case _: return
    await bot.edit_message_reply_markup(userId, callback.message.message_id, reply_markup=resultKeyboard)

def getChangeLangTranslation(userId):
    curLang = dbUsers.getFromUser(userId, 'lang')
    availableLangs = const.data.availableLangs
    nextIndexLang = (availableLangs.index(curLang) + 1) % len(availableLangs)
    curCountryFlag = getTranslation(userId, 'lang.countryflag')
    nextCountryFlag = getTranslation(userId, 'lang.countryflag', lang=availableLangs[nextIndexLang])
    resultTranslation = getTranslation(userId, 'button.changelang', [curCountryFlag, nextCountryFlag])
    return resultTranslation

def getMainKeyboard(userId):
    mainButtons = []
    if dbUsers.getAccountDataFromUser(userId):
        mainButtons.append([types.KeyboardButton(text=getTranslation(userId, 'button.order'))])
        mainButtons.append([types.KeyboardButton(text=getTranslation(userId, 'button.cart'))])
        mainButtons.append([types.KeyboardButton(text=getTranslation(userId, 'button.unlink'))])
    else:
        mainButtons.append([types.KeyboardButton(text=getTranslation(userId, 'button.login'))])
    mainButtons.append([types.KeyboardButton(text=getChangeLangTranslation(userId))])
    mainKeyboard = types.ReplyKeyboardMarkup(keyboard=mainButtons, resize_keyboard=True)
    return mainKeyboard

# COMMANDS
@dp.message(Command('start'))
async def startHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if dbUsers.isUnregistered(userInfo['userId']):
        await message.answer(getTranslation(userInfo['userId'], 'permissons.getsecretkey'), parse_mode='HTML')
        return
    dbLocal.setModeInUser(userInfo['userId'], 0)
    mainKeyboard = getMainKeyboard(userInfo['userId'])
    await message.answer(getTranslation(userInfo['userId'], 'start.message', [userInfo['userFirstName']]), reply_markup=mainKeyboard, parse_mode='HTML')

def isChangeLangCommand(userId, userText):
    return userText in ['/changelang', f'/changelang@{const.telegram.alias}', getChangeLangTranslation(userId)]

async def changelangHandler(userInfo, message):
    curLang = dbUsers.getFromUser(userInfo['userId'], 'lang')
    availableLangs = const.data.availableLangs
    nextIndexLang = (availableLangs.index(curLang) + 1) % len(availableLangs)
    dbUsers.setInUser(userInfo['userId'], 'lang', availableLangs[nextIndexLang])
    mainKeyboard = getMainKeyboard(userInfo['userId'])
    await message.answer(getTranslation(userInfo['userId'], 'success.message'), reply_markup=mainKeyboard)

def isLoginCommand(userId, userText):
    return userText in ['/login', f'/login@{const.telegram.alias}', getTranslation(userId, 'button.login')]

async def loginHandler(userInfo, message):
    mainKeyboard = getMainKeyboard(userInfo['userId'])
    if not dbUsers.isConfirmedEula(userInfo['userId']):
        await message.answer(getTranslation(userInfo['userId'], 'login.message.confirm'), reply_markup=mainKeyboard, parse_mode='HTML')
        return
    if dbUsers.getAccountDataFromUser(userInfo['userId']):
        await message.answer(getTranslation(userInfo['userId'], 'login.message.warn.already'), reply_markup=mainKeyboard, parse_mode='HTML')
        return
    dbLocal.setModeInUser(userInfo['userId'], 1)
    botMessage = await message.answer(getTranslation(userInfo['userId'], 'login.message.username'), parse_mode='HTML')
    dbLocal.addMessageInUser(userInfo['userId'], botMessage.message_id)

async def loginUsernameHandler(userInfo, message):
    if dbUsers.checkLoginInVerifiedList(userInfo['userText']):
        dbLocal.setModeInUser(userInfo['userId'], 0)
        dbLocal.clearDnevnikruInUser(userInfo['userId'])
        await message.answer(getTranslation(userInfo['userId'], 'login.message.warn.busy'), parse_mode='HTML')
        return
    dbLocal.setLoginInUser(userInfo['userId'], userInfo['userText'])
    dbLocal.addMessageInUser(userInfo['userId'], userInfo['messageId'])
    dbLocal.setModeInUser(userInfo['userId'], 2)
    botMessage = await message.answer(getTranslation(userInfo['userId'], 'login.message.password'), parse_mode='HTML')
    dbLocal.addMessageInUser(userInfo['userId'], botMessage.message_id)

async def loginPasswordHandler(userInfo, message):
    dbLocal.setPasswordInUser(userInfo['userId'], userInfo['userText'])
    dbLocal.addMessageInUser(userInfo['userId'], userInfo['messageId'])
    waitMessage = await message.answer(getTranslation(userInfo['userId'], 'login.message.wait.1'), parse_mode='HTML')
    session = Session(const.school.realSchoolName)
    accountData = session.getAccountData(dbLocal.getLoginFromUser(userInfo['userId']),
                                         dbLocal.getPasswordFromUser(userInfo['userId']))
    dbLocal.setModeInUser(userInfo['userId'], 0)

    if not accountData.data:
        await bot.delete_message(userInfo['chatId'], waitMessage.message_id)
        dbLocal.clearDnevnikruInUser(userInfo['userId'])
        mainKeyboard = getMainKeyboard(userInfo['userId'])
        await message.answer(getTranslation(userInfo['userId'], 'error.message', [accountData.error]), reply_markup=mainKeyboard, parse_mode='HTML')
        return

    await bot.edit_message_text(getTranslation(userInfo['userId'], 'login.message.wait.2'), userInfo['chatId'], waitMessage.message_id, parse_mode='HTML')
    dbUsers.addAccountDataInUser(userInfo['userId'], accountData.data)
    dbUsers.addLoginToVerifiedList(accountData.data['login'])
    for messageId in dbLocal.getMessagesFromUser(userInfo['userId']):
        await bot.delete_message(userInfo['chatId'], messageId)
    dbLocal.clearDnevnikruInUser(userInfo['userId'])

    await bot.delete_message(userInfo['chatId'], waitMessage.message_id)
    mainKeyboard = getMainKeyboard(userInfo['userId'])
    await message.answer(getTranslation(userInfo['userId'], 'login.message.welcome', [accountData.data['fullname']]), reply_markup=mainKeyboard, parse_mode='HTML')

@dp.message(Command('confirm'))
async def confirmHandler(message: types.Message):
    userInfo = getUserInfo(message)
    if dbUsers.isUnregistered(userInfo['userId']):
        await message.answer(getTranslation(userInfo['userId'], 'permissons.getsecretkey'), parse_mode='HTML')
        return
    dbUsers.confirmEulaInUser(userInfo['userId'])
    await message.answer(getTranslation(userInfo['userId'], 'success.message'))
    await loginHandler(userInfo, message)

def isUnlinkCommand(userId, userText):
    return userText in ['/unlink', f'/unlink@{const.telegram.alias}', getTranslation(userId, 'button.unlink')]

async def unlinkHandler(userInfo, message):
    if not dbUsers.getAccountDataFromUser(userInfo['userId']):
        mainKeyboard = getMainKeyboard(userInfo['userId'])
        await message.answer(getTranslation(userInfo['userId'], 'unlink.message.warn'), reply_markup=mainKeyboard, parse_mode='HTML')
        return

    dbUsers.removeAccountDataFromUser(userInfo['userId'])
    mainKeyboard = getMainKeyboard(userInfo['userId'])
    await message.answer(getTranslation(userInfo['userId'], 'unlink.message.success'), reply_markup=mainKeyboard, parse_mode='HTML')

def isUnknownCommand(userText):
    return userText[0] == '/'

async def unknownCommandHandler(userInfo, message):
    mainKeyboard = getMainKeyboard(userInfo['userId'])
    await message.answer(getTranslation(userInfo['userId'], 'unknown.command.message'), reply_markup=mainKeyboard, parse_mode='HTML')

async def lastLBMessageHandler(chatId, userId, text, keyboard):
    lastLBMessageId = dbLocal.getLastLBMessageId(userId)
    if lastLBMessageId: await bot.delete_message(chatId, lastLBMessageId)
    lbBotMessage = await bot.send_message(chatId, text, reply_markup=keyboard, parse_mode='HTML')
    dbLocal.setLastLBMessageId(userId, lbBotMessage.message_id)

def isOrderCommand(userId, userText):
    return userText in ['/order', f'/order@{const.telegram.alias}', getTranslation(userId, 'button.order')]

async def orderHandler(userInfo, message):
    if not dbUsers.getAccountDataFromUser(userInfo['userId']):
        mainKeyboard = getMainKeyboard(userInfo['userId'])
        await message.answer(getTranslation(userInfo['userId'], 'order.message.warn'), reply_markup=mainKeyboard, parse_mode='HTML')
        return
    dbLocal.setPageNumber(userInfo['userId'], 1)
    dbLocal.setListBlockLevel(userInfo['userId'], 'category')
    useLeft, useRight = getCurrentStatusControlButtons(userInfo['userId'], len(getInlineButtonsCategories()))
    categoryKeyboard = getCategoryKeyboard(userInfo['userId'], useLeft, useRight)
    await lastLBMessageHandler(userInfo['chatId'], userInfo['userId'], getTranslation(userInfo['userId'], 'order.message.category'), categoryKeyboard)

def getInlineButtonsCategories():
    categoriesList = dbOrders.getCategories()
    inlineButtons = [[types.InlineKeyboardButton(text=category['name'], callback_data=f'{const.callback.prefix.category}.{key}')]
                     for key, category in categoriesList.items()]
    return inlineButtons

def getCategoryKeyboard(userId, useLeft, useRight):
    inlineButtons = getInlineButtonsCategories()
    pageNumber = dbLocal.getPageNumber(userId)
    keyboard = getListBlockKeyboard(userId, inlineButtons, pageNumber, useLeft, useRight)
    return keyboard

def getTextWithPrice(product):
    resultText = f"{product['name']} - [{product['price']} ₽]"
    return resultText

def getInlineButtonsProducts(categoryId):
    productsList = dbOrders.getProducts(categoryId)
    inlineButtons = [[types.InlineKeyboardButton(text=getTextWithPrice(product), callback_data=f'{const.callback.prefix.product}.{key}')]
                     for key, product in productsList.items() if product['active']]
    return inlineButtons

def getProductKeyboard(userId, categoryId, useLeft, useRight):
    inlineButtons = getInlineButtonsProducts(categoryId)
    pageNumber = dbLocal.getPageNumber(userId)
    keyboard = getListBlockKeyboard(userId, inlineButtons, pageNumber, useLeft, useRight)
    return keyboard

@dp.callback_query(F.data.startswith(f'{const.callback.prefix.category}.'))
async def categoryCallbacks(callback: types.CallbackQuery):
    userId = callback.from_user.id
    chatId = callback.message.chat.id
    callbackAction = callback.data
    categoryId = callbackAction.split('.')[1]
    category = dbOrders.getCategory(categoryId)
    dbLocal.setPageNumber(userId, 1)
    dbLocal.setListBlockLevel(userId, 'product')
    dbLocal.setCategoryIdInUser(userId, categoryId)
    useLeft, useRight = getCurrentStatusControlButtons(userId, len(getInlineButtonsProducts(categoryId)))
    productKeyboard = getProductKeyboard(userId, categoryId, useLeft, useRight)
    await lastLBMessageHandler(chatId, userId, getTranslation(userId, 'order.message.product', [category['name']]), productKeyboard)

@dp.callback_query(F.data.startswith(f'{const.callback.prefix.product}.'))
async def productCallbacks(callback: types.CallbackQuery):
    userId = callback.from_user.id
    chatId = callback.message.chat.id
    callbackAction = callback.data
    productId = callbackAction.split('.')[1]
    product = dbOrders.getProduct(productId)
    dbUsers.addProductToCart(userId, productId)
    userInfo = dict(userId=userId, chatId=chatId)
    await bot.send_message(chatId, getTranslation(userId, 'order.message.cart.add', [product['name']]), parse_mode='HTML')
    await orderHandler(userInfo, None)

@dp.callback_query(F.data.startswith(f'{const.callback.prefix.remove}.'))
async def removeCallbacks(callback: types.CallbackQuery):
    userId = callback.from_user.id
    chatId = callback.message.chat.id
    callbackAction = callback.data
    productId = callbackAction.split('.')[1]
    dbUsers.removeProductFromCart(userId, productId)
    dbLocal.setPageNumber(userId, 1)
    useLeft, useRight = getCurrentStatusControlButtons(userId, len(getInlineButtonsCart(userId)))
    cartKeyboard = getCartKeyboard(userId, useLeft, useRight)
    await lastLBMessageHandler(chatId, userId, getTranslation(userId, 'cart.message'), cartKeyboard)

def isCartCommand(userId, userText):
    return userText in ['/cart', f'/cart@{const.telegram.alias}', getTranslation(userId, 'button.cart')]

async def cartHandler(userInfo, message):
    if not dbUsers.getAccountDataFromUser(userInfo['userId']):
        mainKeyboard = getMainKeyboard(userInfo['userId'])
        await message.answer(getTranslation(userInfo['userId'], 'cart.message.warn'), reply_markup=mainKeyboard, parse_mode='HTML')
        return
    dbLocal.setPageNumber(userInfo['userId'], 1)
    dbLocal.setListBlockLevel(userInfo['userId'], 'cart')
    useLeft, useRight = getCurrentStatusControlButtons(userInfo['userId'], len(getInlineButtonsCart(userInfo['userId'])))
    cartKeyboard = getCartKeyboard(userInfo['userId'], useLeft, useRight)
    await lastLBMessageHandler(userInfo['chatId'], userInfo['userId'], getTranslation(userInfo['userId'], 'cart.message'), cartKeyboard)

def getCartKeyboard(userId, useLeft, useRight):
    inlineButtons = getInlineButtonsCart(userId)
    pageNumber = dbLocal.getPageNumber(userId)
    keyboard = getListBlockKeyboard(userId, inlineButtons, pageNumber, useLeft, useRight)
    return keyboard

def getInlineButtonsCart(userId):
    productIdsList = dbUsers.getProductIdsFromCart(userId)
    inlineButtons = []
    resultPrice = 0
    for productId in productIdsList:
        product = dbOrders.getProduct(productId)
        productName, productPrice = product['name'], product['price']
        resultPrice += productPrice
        inlineButtons.append([types.InlineKeyboardButton(text=productName, callback_data=f'{const.callback.empty}'),
                              types.InlineKeyboardButton(text=getTranslation(userId, 'inlinebutton.empty'), callback_data=f'{const.callback.empty}'),
                              types.InlineKeyboardButton(text=getTranslation(userId, 'inlinebutton.remove'), callback_data=f'{const.callback.prefix.remove}.{productId}')])
    inlineButtons.append([types.InlineKeyboardButton(text=getTranslation(userId, 'cart.price', [resultPrice]), callback_data=f'{const.callback.empty}'),
                          types.InlineKeyboardButton(text=getTranslation(userId, 'cart.order'), callback_data=f'{const.callback.order}')])
    return inlineButtons

@dp.callback_query(F.data.startswith(f'{const.callback.order}.'))
async def orderCallbacks(callback: types.CallbackQuery):
    userId = callback.from_user.id
    chatId = callback.message.chat.id
    callbackAction = callback.data


@dp.message()
async def mainHandler(message: types.Message):
    userInfo = getUserInfo(message)
    userMode = dbLocal.getModeFromUser(userInfo['userId'])
    if dbUsers.isUnregistered(userInfo['userId']):
        await message.answer(getTranslation(userInfo['userId'], 'permissons.getsecretkey'), parse_mode='HTML')
        return

    elif isChangeLangCommand(userInfo['userId'], userInfo['userText']):
        await changelangHandler(userInfo, message)
        return

    elif isLoginCommand(userInfo['userId'], userInfo['userText']):
        await loginHandler(userInfo, message)
        return

    elif isUnlinkCommand(userInfo['userId'], userInfo['userText']):
        await unlinkHandler(userInfo, message)
        return

    elif isOrderCommand(userInfo['userId'], userInfo['userText']):
        await orderHandler(userInfo, message)
        return

    elif isCartCommand(userInfo['userId'], userInfo['userText']):
        await cartHandler(userInfo, message)
        return

    elif isUnknownCommand(userInfo['userText']):
        await unknownCommandHandler(userInfo, message)
        return

    elif userMode > 0:
        match userMode:
            case 1: await loginUsernameHandler(userInfo, message)
            case 2: await loginPasswordHandler(userInfo, message)
        return

async def mainTelegram():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(mainTelegram())