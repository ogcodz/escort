import datetime
import random
import re
import asyncio

import requests
import phonenumbers

from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ReplyKeyboardMarkup,
                           KeyboardButton, ContentType)

import texts
import config

from database import DB

db = DB()

bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

worker_bot = Bot(token=config.WORKER_API_TOKEN)

users_models = {}
users_agreed = []
topup_messages = {}
created_models = {}
amount_chooses = {}
additional_services_cost = {}


class ModelCode(StatesGroup):
    model_code = State()


class Card(StatesGroup):
    amount = State()
    requisite = State()
    full_name = State()


class Qiwi(StatesGroup):
    amount = State()
    requisite = State()


class USDT(StatesGroup):
    amount = State()
    requisite = State()


class Connect(StatesGroup):
    unique_id = State()
    worker_ref = State()


class Processing(StatesGroup):
    unique_id = State()
    data = State()
    app_type = State()


class ChangeBalance(StatesGroup):
    mamont_id = State()
    balance = State()


class MamontMessage(StatesGroup):
    mamont_id = State()
    message = State()


class FindMamont(StatesGroup):
    mamont_id = State()


class MassSpam(StatesGroup):
    photo = State()
    text_text = State()
    text_photo = State()
    text_post = State()
    message_chat_id = State()
    message_id = State()
    action_text = State()
    action_photo = State()
    action_post = State()


class CreateModel(StatesGroup):
    model_name = State()
    city = State()
    main_cost = State()
    add_cost = State()
    parameters = State()
    photo_one = State()
    photo_two = State()
    photo_three = State()
    photo_four = State()
    photo_five = State()


class CreateFeedback(StatesGroup):
    photo = State()
    text = State()


# ----------------------------------------------------------------------------------------------------------------------


@dp.message_handler(commands=["chat_id"])
async def send_chat_id(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id, text=str(msg.chat.id))


# ----------------------------------------------------------------------------------------------------------------------

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    is_exist = db.EscortUsers.is_user_exist(msg.from_user.id)

    if not is_exist:
        code = msg.get_args()
        ref_codes = db.Workers.get_ref_codes()

        if code in ref_codes:
            id_telegram = db.Workers.get_id(code)

            await bot.send_message(chat_id=id_telegram,
                                   text=texts.Actions.new.format(
                                       name=msg.from_user.first_name,
                                       mamont_id=msg.from_user.id
                                   ),
                                   parse_mode="HTML")

            db.EscortUsers.insert_user(msg.from_user.id, code)
        else:
            db.EscortUsers.insert_user(msg.from_user.id)

    await main_menu(msg.from_user)


@dp.message_handler(text=["💘 Главное меню"])
async def message_main_menu(msg: types.Message):
    await main_menu(msg.from_user, False)


@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def callback_main_menu(callback_query: types.CallbackQuery):
    await callback_query.message.edit_media(media=InputMediaPhoto(
        media=open('media/frame.png', 'rb'),
        caption=""
    ), reply_markup=texts.MainMenu.inline)


async def main_menu(user: types.User, send_message: bool = True):
    if send_message:
        await bot.send_message(chat_id=user.id, text="💘 Главное меню", reply_markup=texts.MainMenu.reply)
    await bot.send_photo(chat_id=user.id, photo=open('media/frame.png', 'rb'), reply_markup=texts.MainMenu.inline)


@dp.message_handler(text=["👩‍💻 Тех. поддержка"])
async def call_tech_support(msg: types.Message):
    await bot.send_message(chat_id=msg.from_user.id, text="👩‍💻 Если у вас возникли какие-либо проблемы, обратитесь в "
                                                          "поддержку👉@pleasureclub_support")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "information")
async def information(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.MainMenu.Information.text,
                                              reply_markup=texts.MainMenu.Information.inline,
                                              parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "vip_models")
async def cities_list(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.MainMenu.VipModels.city_text,
                                              reply_markup=texts.MainMenu.VipModels.city_page(1),
                                              parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("city_"))
async def models_list(callback_query: types.CallbackQuery):
    city = callback_query.data.split("_")[1]
    models = db.Models.get_active_models(city)
    delete_msg = int(callback_query.data.split("_")[2])

    if delete_msg:
        await callback_query.message.delete()
        await bot.send_photo(chat_id=callback_query.from_user.id,
                             photo=open('media/frame.png', 'rb'),
                             caption=texts.MainMenu.VipModels.model_text.format(
                                 models_active=len(models)
                             ),
                             reply_markup=texts.MainMenu.VipModels.models_page(models),
                             parse_mode="HTML")
    else:
        await callback_query.message.edit_caption(caption=texts.MainMenu.VipModels.model_text.format(
            models_active=len(models)
        ),
            reply_markup=texts.MainMenu.VipModels.models_page(models),
            parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("citypage_"))
async def change_cities_list(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    next_page = int(callback_query.data.split("_")[1])
    await callback_query.message.edit_caption(caption=texts.MainMenu.VipModels.city_text,
                                              reply_markup=texts.MainMenu.VipModels.city_page(next_page),
                                              parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("model_"))
async def model_menu(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]
    model_data = db.Models.get_model_data(model_code)
    await callback_query.message.delete()
    await draw_model_vip(callback_query.from_user, model_data, model_code, 0)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "my_profile")
async def my_profile(callback_query: types.CallbackQuery):
    data = db.EscortUsers.get_user_data(callback_query.from_user.id)
    balance = data[0]

    if data[2] == 1:
        subscription = "⭐️ VIP подписка"
    elif data[2] == 2:
        subscription = "💎 PREMIUM подписка"
    elif data[2] == 3:
        subscription = "👑 GOLD подписка"
    else:
        subscription = "❌ Отсутствует"

    if data[3] != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        balance = round(balance * rates[data[3]], 2)

    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.text.format(
        id_telegram=callback_query.from_user.id,
        balance=balance,
        currency=data[3],
        date=str(data[1]).split(' ')[0],
        subscription=subscription
    ),
        reply_markup=texts.MainMenu.Profile.inline,
        parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "change_currency")
async def change_currency_menu(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.ChangeCurrency.text,
                                              reply_markup=texts.MainMenu.Profile.ChangeCurrency.inline)


@dp.callback_query_handler(lambda c: c.data.startswith("ch_"))
async def change_currency(callback_query: types.CallbackQuery):
    cur = callback_query.data.split("_")[1].upper()

    db.EscortUsers.change_currency(callback_query.from_user.id, cur)

    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text=f"✅ Вы успешно изменили валюту бота на {cur}.",
                                    show_alert=True)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "top_up")
async def choose_method(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.text,
                                              reply_markup=texts.MainMenu.Profile.TopUp.inline,
                                              parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


# @dp.callback_query_handler(lambda c: c.data == "tp_card")
# async def card_method(callback_query: types.CallbackQuery):
#     user_data = db.EscortUsers.get_user_data(callback_query.from_user.id)
#     currency = user_data[3]
#     min_dep = user_data[4]
#
#     if callback_query.from_user.id in topup_messages:
#         return
#     else:
#         topup_messages[callback_query.from_user.id] = callback_query.message.message_id
#
#     if currency != "RUB":
#         rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
#         min_dep = round(min_dep * rates[currency], 2)
#
#     await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.Card.amount_text.format(
#         currency=currency,
#         min_dep=min_dep
#     ),
#         reply_markup=texts.MainMenu.Profile.TopUp.Card.inline,
#         parse_mode="HTML")
#
#     await Card.amount.set()


@dp.callback_query_handler(lambda c: c.data == "cancel_card", state=Card)
async def cancel_card(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text="⛔️ Пополнение отменено.",
                                    show_alert=True)

    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.text,
                                              reply_markup=texts.MainMenu.Profile.TopUp.inline,
                                              parse_mode="HTML")

    await state.finish()
    del topup_messages[callback_query.from_user.id]


@dp.callback_query_handler(lambda c: c.data == "tp_card")
async def card_amount(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in topup_messages:
        return
    else:
        topup_messages[callback_query.from_user.id] = callback_query.message.message_id

    await bot.edit_message_caption(chat_id=callback_query.from_user.id,
                                   message_id=topup_messages[callback_query.from_user.id],
                                   caption=texts.MainMenu.Profile.TopUp.Card.req_text,
                                   reply_markup=texts.MainMenu.Profile.TopUp.Card.inline,
                                   parse_mode="HTML")

    await Card.requisite.set()


@dp.message_handler(state=Card.requisite)
async def card_req(msg: types.Message, state: FSMContext):
    await msg.delete()

    try:
        req = int(msg.text)
    except:
        return await Card.requisite.set()

    if not await luna_algorithm(str(req)):
        return await Card.requisite.set()

    await state.update_data(requisite=req)

    await bot.edit_message_caption(chat_id=msg.from_user.id,
                                   message_id=topup_messages[msg.from_user.id],
                                   caption=texts.MainMenu.Profile.TopUp.Card.name_text,
                                   reply_markup=texts.MainMenu.Profile.TopUp.Card.inline,
                                   parse_mode="HTML")

    await Card.full_name.set()


@dp.message_handler(state=Card.full_name)
async def card_name(msg: types.Message, state: FSMContext):
    await msg.delete()

    data = await state.get_data()
    amount = amount_chooses[msg.from_user.id][0]
    app_type = amount_chooses[msg.from_user.id][1]
    req = data.get("requisite")
    name = msg.text
    await state.finish()

    await bot.edit_message_caption(chat_id=msg.from_user.id,
                                   message_id=topup_messages[msg.from_user.id],
                                   caption=texts.MainMenu.Profile.TopUp.Card.final_text,
                                   parse_mode="HTML")

    del topup_messages[msg.from_user.id]
    del amount_chooses[msg.from_user.id]

    await send_application_card(msg.from_user, amount, req, name, app_type)


async def send_application_card(user: types.User, amount: float, requisite: str, full_name: str, app_type: int):
    worker, ref_code = db.EscortUsers.get_user_mamont(user.id)
    unique_id = random.randint(100000, 999999)
    currency = db.EscortUsers.get_user_data(user.id)[3]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        amount = round(amount / rates[currency], 2)

    db.TopUp.insert_new_application(unique_id, user.id, "CARD", requisite, amount, user.username)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("⚙️ Обработать", callback_data="obr_%d_%d" % (unique_id, app_type)))
    if worker == "Отсутствует":
        inline.add(InlineKeyboardButton("👤 Привязать", callback_data="priv_%d_%d" % (unique_id, app_type)))
    else:
        await send_application_worker(user, amount, ref_code, unique_id)

    await bot.send_message(chat_id=config.CHAT_ID,
                           text=texts.Application.Card.text.format(
                               worker=worker,
                               mamont="@" + user.username,
                               mamont_id=user.id,
                               requisite=requisite,
                               amount=amount,
                               full_name=full_name
                           ),
                           reply_markup=inline,
                           parse_mode="HTML")


async def luna_algorithm(card_number: str) -> bool:
    try:
        digits = list(map(int, card_number))
        digits.reverse()

        total_sum = 0
        for i, digit in enumerate(digits):
            if i % 2 == 1:
                doubled = digit * 2
                if doubled > 9:
                    doubled -= 9
                total_sum += doubled
            else:
                total_sum += digit

        return total_sum % 10 == 0
    except:
        return False


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "tp_qiwi")
async def qiwi_method(callback_query: types.CallbackQuery):
    user_data = db.EscortUsers.get_user_data(callback_query.from_user.id)
    currency = user_data[3]
    min_dep = user_data[4]

    if callback_query.from_user.id in topup_messages:
        return
    else:
        topup_messages[callback_query.from_user.id] = callback_query.message.message_id

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        min_dep = round(min_dep * rates[currency], 2)

    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.Qiwi.amount_text.format(
        currency=currency,
        min_dep=min_dep
    ),
        reply_markup=texts.MainMenu.Profile.TopUp.Qiwi.inline,
        parse_mode="HTML")

    await Qiwi.amount.set()


@dp.callback_query_handler(lambda c: c.data == "cancel_qiwi", state=Qiwi)
async def cancel_qiwi(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text="⛔️ Пополнение отменено.",
                                    show_alert=True)

    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.text,
                                              reply_markup=texts.MainMenu.Profile.TopUp.inline,
                                              parse_mode="HTML")

    await state.finish()
    del topup_messages[callback_query.from_user.id]


@dp.message_handler(state=Qiwi.amount)
async def qiwi_amount(msg: types.Message, state: FSMContext):
    await msg.delete()

    try:
        amount = float(msg.text)
    except:
        return await Qiwi.amount.set()

    await state.update_data(amount=amount)

    await bot.edit_message_caption(chat_id=msg.from_user.id,
                                   message_id=topup_messages[msg.from_user.id],
                                   caption=texts.MainMenu.Profile.TopUp.Card.req_text,
                                   reply_markup=texts.MainMenu.Profile.TopUp.Card.inline,
                                   parse_mode="HTML")

    await Qiwi.requisite.set()


@dp.message_handler(state=Qiwi.requisite)
async def qiwireq(msg: types.Message, state: FSMContext):
    await msg.delete()

    req = msg.text
    if not await validate_phone_number(req):
        return await Qiwi.requisite.set()

    data = await state.get_data()
    amount = data.get("amount")
    await state.finish()

    await bot.edit_message_caption(chat_id=msg.from_user.id,
                                   message_id=topup_messages[msg.from_user.id],
                                   caption=texts.MainMenu.Profile.TopUp.Card.final_text,
                                   parse_mode="HTML")

    del topup_messages[msg.from_user.id]
    await send_application_qiwi(msg.from_user, amount, req)


async def send_application_qiwi(user: types.User, amount: float, requisite: str):
    worker, ref_code = db.EscortUsers.get_user_mamont(user.id)
    unique_id = random.randint(100000, 999999)
    currency = db.EscortUsers.get_user_data(user.id)[3]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        amount = round(amount / rates[currency], 2)

    db.TopUp.insert_new_application(unique_id, user.id, "QIWI", requisite, amount, user.username)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("⚙️ Обработать", callback_data="obr_%d" % unique_id))
    if worker == "Отсутствует":
        inline.add(InlineKeyboardButton("👤 Привязать", callback_data="priv_%d" % unique_id))
    else:
        await send_application_worker(user, amount, ref_code, unique_id)

    await bot.send_message(chat_id=config.CHAT_ID,
                           text=texts.Application.Qiwi.text.format(
                               worker=worker,
                               mamont="@" + user.username,
                               mamont_id=user.id,
                               requisite=requisite,
                               amount=amount
                           ),
                           reply_markup=inline,
                           parse_mode="HTML")


async def validate_phone_number(phone_number: str) -> bool:
    try:
        number = phonenumbers.parse(phone_number, None)
        return phonenumbers.is_valid_number(number)
    except phonenumbers.NumberParseException:
        return False


# ----------------------------------------------------------------------------------------------------------------------


# @dp.callback_query_handler(lambda c: c.data == "tp_usdt")
# async def usdt_method(callback_query: types.CallbackQuery):
#     user_data = db.EscortUsers.get_user_data(callback_query.from_user.id)
#     min_dep = user_data[4]
#
#     if callback_query.from_user.id in topup_messages:
#         return
#     else:
#         topup_messages[callback_query.from_user.id] = callback_query.message.message_id
#
#     rates = requests.get("https://min-api.cryptocompare.com/data/pricemulti?fsyms=USDT&tsyms=RUB").json()["USDT"]
#     min_dep = round(min_dep / rates["RUB"], 2)
#
#     await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.USDT.amount_text.format(
#         min_dep=min_dep
#     ),
#         reply_markup=texts.MainMenu.Profile.TopUp.USDT.inline,
#         parse_mode="HTML")
#
#     await USDT.amount.set()


@dp.callback_query_handler(lambda c: c.data == "cancel_usdt", state=USDT)
async def cancel_usdt(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text="⛔️ Пополнение отменено.",
                                    show_alert=True)

    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.text,
                                              reply_markup=texts.MainMenu.Profile.TopUp.inline,
                                              parse_mode="HTML")

    await state.finish()
    del topup_messages[callback_query.from_user.id]


@dp.callback_query_handler(lambda c: c.data == "tp_usdt")
async def usdt_amount(callback_query: types.CallbackQuery):
    if callback_query.from_user.id in topup_messages:
        return
    else:
        topup_messages[callback_query.from_user.id] = callback_query.message.message_id

    await callback_query.message.edit_caption(caption=texts.MainMenu.Profile.TopUp.USDT.req_text,
                                              reply_markup=texts.MainMenu.Profile.TopUp.USDT.inline,
                                              parse_mode="HTML")

    await USDT.requisite.set()


@dp.message_handler(state=USDT.requisite)
async def usdtreq(msg: types.Message, state: FSMContext):
    await msg.delete()

    req = msg.text
    if not await validate_wallet(req):
        return await USDT.requisite.set()

    data = await state.get_data()
    amount = amount_chooses[msg.from_user.id][0]
    app_type = amount_chooses[msg.from_user.id][1]
    await state.finish()

    await bot.edit_message_caption(chat_id=msg.from_user.id,
                                   message_id=topup_messages[msg.from_user.id],
                                   caption=texts.MainMenu.Profile.TopUp.USDT.final_text,
                                   parse_mode="HTML")

    del topup_messages[msg.from_user.id]
    del amount_chooses[msg.from_user.id]

    await send_application_usdt(msg.from_user, amount, req, app_type)


async def send_application_usdt(user: types.User, amount: float, requisite: str, app_type: int):
    worker, ref_code = db.EscortUsers.get_user_mamont(user.id)
    unique_id = random.randint(100000, 999999)

    # rates = requests.get("https://min-api.cryptocompare.com/data/pricemulti?fsyms=USDT&tsyms=RUB").json()["USDT"]
    # amount = round(amount * rates["RUB"], 2)

    db.TopUp.insert_new_application(unique_id, user.id, "USDT", requisite, amount, user.username)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("⚙️ Обработать", callback_data="obr_%d_%d" % (unique_id, app_type)))
    if worker == "Отсутствует":
        inline.add(InlineKeyboardButton("👤 Привязать", callback_data="priv_%d_%d" % (unique_id, app_type)))
    else:
        await send_application_worker(user, amount, ref_code, unique_id)

    await bot.send_message(chat_id=config.CHAT_ID,
                           text=texts.Application.USDT.text.format(
                               worker=worker,
                               mamont="@" + user.username,
                               mamont_id=user.id,
                               requisite=requisite,
                               amount=amount
                           ),
                           reply_markup=inline,
                           parse_mode="HTML")


async def validate_wallet(wallet_address):
    pattern = r"^[Tt][A-HJ-NP-Za-km-z1-9]{33}$"
    if re.match(pattern, wallet_address):
        return True
    else:
        return False


# ----------------------------------------------------------------------------------------------------------------------


async def send_application_worker(user: types.User, amount: float, ref_code: str, unique_id: int):
    # chat_id = db.Workers.get_id(ref_code)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("✅ Оплатить", callback_data="eoplata_%d" % unique_id))
    inline.add(InlineKeyboardButton("❌ Не пополнять", callback_data="eotkaz_%d" % unique_id))
    # inline.add(InlineKeyboardButton("⚙️ Сменнить сумму пополнения", callback_data="echange_%d" % unique_id))

    await bot.send_message(chat_id=config.CHAT_ID,
                                  text=texts.Application.Worker.text.format(
                                      link="https://t.me/" + user.username,
                                      username=user.username,
                                      amount=amount
                                  ),
                                  reply_markup=inline,
                                  parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("eoplata_"))
async def accept_top_up(callback_query: types.CallbackQuery):
    unique_id = callback_query.data.split("_")[1]
    html_text = callback_query.message.html_text + "\n\n<i>Заявка одобрена!</i>"

    db.ETopUp.accept(unique_id)

    await callback_query.message.edit_text(text=html_text, parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("eotkaz_"))
async def accept_top_up(callback_query: types.CallbackQuery):
    unique_id = callback_query.data.split("_")[1]
    html_text = callback_query.message.html_text + "\n\n<i>Заявка отклонена!</i>"

    db.ETopUp.cancel(unique_id)

    await callback_query.message.edit_text(text=html_text, parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("priv_"))
async def connect_to_worker(callback_query: types.CallbackQuery):
    await bot.send_message(chat_id=config.CHAT_ID, text="Укажите реф. код воркера")

    await Connect.unique_id.set()
    state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    await state.update_data(unique_id=callback_query.data.split("_")[1])

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("⚙️ Обработать", callback_data="obr_%s_%s" % (callback_query.data.split("_")[1],
                                                                                  callback_query.data.split("_")[2])))
    await callback_query.message.edit_reply_markup(reply_markup=inline)

    await Connect.worker_ref.set()


@dp.message_handler(state=Connect.worker_ref)
async def worker_ref(msg: types.Message, state: FSMContext):
    ref_codes = db.Workers.get_ref_codes()
    if msg.text not in ref_codes:
        await bot.send_message(chat_id=msg.chat.id, text="Такого реф. кода нет!")
        return await Connect.worker_ref.set()

    state_data = await state.get_data()
    unique_id = state_data.get("unique_id")
    await state.finish()

    data = db.TopUp.get_data(unique_id)
    mamont_id = data[0]
    amount = data[2]
    user = await bot.get_chat_member(chat_id=mamont_id, user_id=mamont_id)

    db.EscortUsers.set_ref_code(mamont_id, msg.text)

    await send_application_worker(user.user, amount, msg.text, int(unique_id))

    await bot.send_message(chat_id=config.CHAT_ID, text="Мамонт успешно привязан!")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("obr_"))
async def processing(callback_query: types.CallbackQuery):
    await bot.send_message(chat_id=config.CHAT_ID,
                           text="Укажите номер заказа, реквизиты и сумму ЧЕРЕЗ ПРОБЕЛ")
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    unique_id = callback_query.data.split("_")[1]
    app_type = callback_query.data.split("_")[2]

    await Processing.unique_id.set()
    state = dp.current_state(chat=config.CHAT_ID, user=callback_query.from_user.id)
    await state.update_data(unique_id=unique_id)

    await Processing.app_type.set()
    state = dp.current_state(chat=config.CHAT_ID, user=callback_query.from_user.id)
    await state.update_data(app_type=app_type)

    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup())

    await Processing.data.set()


@dp.message_handler(state=Processing.data)
async def proc_data(msg: types.Message, state: FSMContext):
    data = msg.text.split(" ")
    if len(data) > 3:
        return await msg.delete()

    state_data = await state.get_data()
    unique_id = state_data.get("unique_id")
    app_type = state_data.get("app_type")
    number = data[0]
    req = data[1]
    amount = data[2]
    await state.finish()

    topup_data = db.TopUp.get_data(unique_id)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("✅ Я оплатил", callback_data="oplatil_%s_%s" % (unique_id, app_type)))

    if req.startswith("+"):
        number = ("https://qiwi.com/payment/form/99?extra"
                  "[%27account%27]={}"
                  "&amountInteger={}"
                  "&amountFraction=0&currency=643"
                  "&extra[%27comment%27]={}"
                  "&blocked[0]=sum"
                  "&blocked[1]=account"
                  "&blocked[2]=comment".format(req.replace("+", ""), str(amount), str(number)))

        number = "<a href=\"%s\">Cсылка для оплаты</a>" % number

    await bot.send_message(chat_id=topup_data[0],
                           text=texts.Application.Mamont.text.format(
                               requisite=req,
                               number=number,
                               amount=amount
                           ),
                           reply_markup=inline,
                           parse_mode="HTML")

    await bot.send_message(chat_id=config.CHAT_ID, text="Сообщение успешно отправлено мамонту!")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("oplatil_"))
async def payed(callback_query: types.CallbackQuery):
    unique_id = callback_query.data.split("_")[1]
    app_type = callback_query.data.split("_")[2]
    nickname, _ = db.EscortUsers.get_user_mamont(callback_query.from_user.id)

    await bot.send_message(chat_id=config.CHAT_ID, text="Мамонт воркера - %s успешно оплатил заявку ✅" % nickname)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("✅ Проверить", callback_data="chk_%s_%s" % (unique_id, app_type)))

    await callback_query.message.edit_reply_markup(reply_markup=inline)


@dp.callback_query_handler(lambda c: c.data.startswith("chk_"))
async def check(callback_query: types.CallbackQuery):
    unique_id = callback_query.data.split("_")[1]
    app_type = callback_query.data.split("_")[2]
    data = db.TopUp.get_all_data(unique_id)

    if data[2] == 0:
        await bot.answer_callback_query(callback_query_id=callback_query.id,
                                        text="Не оплачено")
    elif data[2] == 2:
        await callback_query.message.delete()
        await bot.send_message(chat_id=callback_query.from_user.id,
                               text="❌ <b>Отказано в пополнении</b>",
                               parse_mode="HTML")
    elif data[2] == 1:
        await callback_query.message.delete()

        if int(app_type) == 0:
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text=texts.MainMenu.SubscriptionInfo.Buy.text.format(
                                       subscription="⭐️ VIP подписка"
                                   ),
                                   parse_mode="HTML")

            db.EscortUsers.set_subscription(callback_query.from_user.id, 1)
        elif int(app_type) == 1:
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text=texts.MainMenu.SubscriptionInfo.Buy.text.format(
                                       subscription="💎 PREMIUM подписка"
                                   ),
                                   parse_mode="HTML")

            db.EscortUsers.set_subscription(callback_query.from_user.id, 2)
        elif int(app_type) == 2:
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text=texts.MainMenu.SubscriptionInfo.Buy.text.format(
                                       subscription="👑 GOLD подписка"
                                   ),
                                   parse_mode="HTML")

            db.EscortUsers.set_subscription(callback_query.from_user.id, 3)
        elif int(app_type) == 3:
            await bot.send_message(chat_id=callback_query.from_user.id,
                                   text=texts.MainMenu.FindModel.Model.Formalize.final,
                                   parse_mode="HTML",
                                   reply_markup=texts.MainMenu.FindModel.Model.Formalize.inline)

        # amount = data[1]
        # db.EscortUsers.update_balance(callback_query.from_user.id, amount)
        #
        # data = db.EscortUsers.get_user_data(callback_query.from_user.id)
        # balance, currency = data[0], data[3]
        #
        # if currency != "RUB":
        #     rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        #     balance = round(balance * rates[currency], 2)
        #
        # await bot.send_message(chat_id=callback_query.from_user.id,
        #                        text="❇️ Успешная оплата")
        # await bot.send_message(chat_id=callback_query.from_user.id,
        #                        text="💸 Ваш баланс: %d %s" % (balance, currency))


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "buy_subscription")
async def subscription_info_menu(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.MainMenu.SubscriptionInfo.text,
                                              reply_markup=texts.MainMenu.SubscriptionInfo.inline)


@dp.callback_query_handler(lambda c: c.data.startswith("subs_"))
async def subscription_info(callback_query: types.CallbackQuery):
    subscription = callback_query.data.split("_")[1]

    amount = db.Subscriptions.get_amount(subscription.upper())
    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        amount = round(amount * rates[currency])

    if subscription == "vip":
        await callback_query.message.edit_caption(caption=texts.MainMenu.SubscriptionInfo.VIP.text.format(
            amount=amount,
            currency=currency
        ),
            reply_markup=texts.MainMenu.SubscriptionInfo.VIP.inline,
            parse_mode="HTML")
    elif subscription == "premium":
        await callback_query.message.edit_caption(caption=texts.MainMenu.SubscriptionInfo.PREMIUM.text.format(
            amount=amount,
            currency=currency
        ),
            reply_markup=texts.MainMenu.SubscriptionInfo.PREMIUM.inline,
            parse_mode="HTML")
    elif subscription == "gold":
        await callback_query.message.edit_caption(caption=texts.MainMenu.SubscriptionInfo.GOLD.text.format(
            amount=amount,
            currency=currency
        ),
            reply_markup=texts.MainMenu.SubscriptionInfo.GOLD.inline,
            parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_subscription(callback_query: types.CallbackQuery):
    subscription = callback_query.data.split("_")[1].upper()

    amount = db.Subscriptions.get_amount(subscription)
    balance = db.EscortUsers.get_user_data(callback_query.from_user.id)[0]
    # new_balance = balance - amount

    if subscription == "VIP":
        sub = "⭐️ VIP подписка"
        sub_id = 1
    elif subscription == "PREMIUM":
        sub = "💎 PREMIUM подписка"
        sub_id = 2
    elif subscription == "GOLD":
        sub = "👑 GOLD подписка"
        sub_id = 3

    is_higher_subscription = db.EscortUsers.is_higher_subscription(callback_query.from_user.id, sub_id)

    if is_higher_subscription:
        await bot.answer_callback_query(callback_query_id=callback_query.id,
                                        text="❌ У вас уже есть подписка большего или текущего уровня!",
                                        show_alert=True)

    amount_chooses[callback_query.from_user.id] = [amount, sub_id - 1]

    await choose_method(callback_query)
    # elif new_balance < 0:
    #     await bot.answer_callback_query(callback_query_id=callback_query.id,
    #                                     text="❌ Недостаточно баланса\n"
    #                                          "💴 Пополните баланс!",
    #                                     show_alert=True)
    # else:
    #     db.EscortUsers.change_subscription(callback_query.from_user.id, new_balance, sub_id)
    #
    #     await callback_query.message.edit_caption(caption=texts.MainMenu.SubscriptionInfo.Buy.text.format(
    #         subscription=sub
    #     ),
    #         reply_markup=texts.MainMenu.SubscriptionInfo.Buy.inline,
    #         parse_mode="HTML")
    #
    #     id_telegram = db.Workers.get_id(db.EscortUsers.get_ref_code(callback_query.from_user.id))
    #     await worker_bot.send_message(chat_id=id_telegram,
    #                                   text=texts.Actions.subscription.format(
    #                                       name=callback_query.from_user.first_name,
    #                                       subscription=sub
    #                                   ),
    #                                   parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "find_model")
async def find_model(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=texts.MainMenu.FindModel.text,
                           reply_markup=texts.MainMenu.FindModel.inline,
                           parse_mode="HTML")

    await ModelCode.model_code.set()


@dp.callback_query_handler(lambda c: c.data == "drop_model_code", state=ModelCode.model_code)
async def drop_model_code(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await callback_query.message.delete()


@dp.message_handler(state=ModelCode.model_code)
async def get_model(msg: types.Message, state: FSMContext):
    message = await bot.send_message(chat_id=msg.chat.id, text="🔍")
    await asyncio.sleep(3)
    await message.delete()

    model_code = msg.text
    try:
        model_data = db.Models.get_model_data(model_code)
    except:
        await bot.send_message(chat_id=msg.from_user.id, text="🙁 Модель по коду %s не найдена." % model_code,
                               reply_markup=texts.MainMenu.reply)
        await bot.send_photo(chat_id=msg.from_user.id, photo=open('media/frame.png', 'rb'),
                             reply_markup=texts.MainMenu.inline)
        await state.finish()
        return

    if not model_data:
        await bot.send_message(chat_id=msg.from_user.id, text="🙁 Модель по коду %s не найдена." % model_code,
                               reply_markup=texts.MainMenu.reply)
        await bot.send_photo(chat_id=msg.from_user.id, photo=open('media/frame.png', 'rb'),
                             reply_markup=texts.MainMenu.inline)
        await state.finish()
    else:
        await draw_model(msg.from_user, model_data, model_code, 0)
        await state.finish()


# ----------------------------------------------------------------------------------------------------------------------


async def draw_model_vip(user: types.User, data: tuple, model_code: str, last_index: int):
    photos = [photo for photo in data[-6:12] if photo]

    users_models[user.id] = {
        model_code: {
            "data": data
        }
    }
    users_models[user.id][model_code]["photos"] = photos

    photo_data = photos[last_index]

    city = db.Models.get_model_city(model_code)

    currency = db.EscortUsers.get_user_data(user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        costs = [round(cost * rates[currency]) for cost in costs]

    inline = InlineKeyboardMarkup()
    inline.row(InlineKeyboardButton("💘 Оформить", callback_data="ofrmvip_%s" % model_code),
               InlineKeyboardButton("📸 Другое фото", callback_data="ot_%s" % model_code))
    inline.add(InlineKeyboardButton("📔 Услуги", callback_data="servicesvip_%s" % model_code))
    inline.add(InlineKeyboardButton("Назад", callback_data="city_%s_1" % city))

    await bot.send_photo(chat_id=user.id,
                         photo=photo_data,
                         caption=texts.MainMenu.FindModel.Model.text.format(
                             name=data[0],
                             age=data[1],
                             city=data[4],
                             hour=costs[0],
                             three_hours=costs[1],
                             night=costs[2],
                             currency=currency,
                             height=data[2],
                             boobs_size=data[3]
                         ),
                         reply_markup=inline,
                         parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("ofrmvip_"))
async def ofrmvip(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]

    if callback_query.from_user.id not in users_agreed:
        inline = InlineKeyboardMarkup()
        inline.add(InlineKeyboardButton("Ознакомлен", callback_data="agreementvip_%s" % model_code))
        inline.add(InlineKeyboardButton("Назад", callback_data="backvip_%s" % model_code))

        return await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.agreement,
                                                         reply_markup=inline,
                                                         parse_mode="HTML")

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        costs = [round(cost * rates[currency]) for cost in costs]

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("🌇 Час - %d %s" % (costs[0], currency), callback_data="hoursvip_%s_1" % model_code))
    inline.add(
        InlineKeyboardButton("🏙 3 часа - %d %s" % (costs[1], currency), callback_data="hoursvip_%s_3" % model_code))
    inline.add(
        InlineKeyboardButton("🌃 Ночь - %d %s" % (costs[2], currency), callback_data="hoursvip_%s_n" % model_code))
    inline.add(InlineKeyboardButton("Назад", callback_data="backvip_%s" % model_code))

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.text,
                                              reply_markup=inline)


@dp.callback_query_handler(lambda c: c.data.startswith("hoursvip_"))
async def hoursvip(callback_query: types.CallbackQuery):
    hrs = callback_query.data.split("_")[2]
    model_code = callback_query.data.split("_")[1]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]
    additional = data[6].split(";")
    inline = InlineKeyboardMarkup()
    if len(additional[0]) > 0:
        add_names = [add.split(":")[0] for add in additional]
        add_costs = [int(add.split(":")[1]) for add in additional]

        if currency != "RUB":
            rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
            add_costs = [round(cost * rates[currency]) for cost in add_costs]

        if hrs == "1":
            total_amount = costs[0]
        elif hrs == "3":
            total_amount = costs[1]
        elif hrs == "n":
            total_amount = costs[2]

        counter = 0
        for name, cost in dict(zip(add_names, add_costs)).items():
            inline.add(InlineKeyboardButton("[ X ] - %s - %d %s" % (name, cost, currency),
                                            callback_data="add_%d_%d_%s" % (counter, total_amount, model_code)))
            counter += 1
    if hrs == "1":
        total_amount = costs[0]
    elif hrs == "3":
        total_amount = costs[1]
    elif hrs == "n":
        total_amount = costs[2]
    inline.add(InlineKeyboardButton("Далее", callback_data="add_n_%d_%s" % (total_amount, model_code)))
    inline.add(InlineKeyboardButton("Назад", callback_data="ofrmvip_%s" % model_code))

    additional_services_cost[callback_query.from_user.id] = [int(total_amount), [-1]]

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.add,
                                              reply_markup=inline,
                                              parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("agreementvip_"))
async def accept_agreement(callback_query: types.CallbackQuery):
    users_agreed.append(callback_query.from_user.id)
    await ofrmvip(callback_query)


@dp.callback_query_handler(lambda c: c.data.startswith("backvip_"))
async def backvip(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    city = db.Models.get_model_city(model_code)

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        costs = [round(cost * rates[currency]) for cost in costs]

    inline = InlineKeyboardMarkup()
    inline.row(InlineKeyboardButton("💘 Оформить", callback_data="ofrmvip_%s" % model_code),
               InlineKeyboardButton("📸 Другое фото", callback_data="ot_%s" % model_code))
    inline.add(InlineKeyboardButton("📔 Услуги", callback_data="servicesvip_%s" % model_code))
    inline.add(InlineKeyboardButton("Назад", callback_data="city_%s_1" % city))

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.text.format(
        name=data[0],
        age=data[1],
        city=data[4],
        hour=costs[0],
        three_hours=costs[1],
        night=costs[2],
        currency=currency,
        height=data[2],
        boobs_size=data[3]
    ),
        reply_markup=inline,
        parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("servicesvip_"))
async def servicesvip(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    additional = data[6].split(";")
    if len(additional[0]) > 0:
        add_names = [add.split(":")[0] for add in additional]
        add_costs = [int(add.split(":")[1]) for add in additional]

        if currency != "RUB":
            rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
            add_costs = [round(cost * rates[currency]) for cost in add_costs]

        additional_message = ""
        for name, cost in dict(zip(add_names, add_costs)).items():
            additional_message += "• %s - %d %s" % (name, cost, currency) + "\n"
        if additional_message:
            additional_message += "\n"
    else:
        additional_message = ""

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("💘 Оформить", callback_data="ofrmvip_%s" % model_code))
    inline.add(InlineKeyboardButton("Назад", callback_data="backvip_%s" % model_code))

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Services.text.format(
        name=data[0],
        city=data[4],
        additional=additional_message
    ),
        reply_markup=inline,
        parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


async def draw_model(user: types.User, data: tuple, model_code: str, last_index: int):
    photos = [photo for photo in data[-6:12] if photo]

    users_models[user.id] = {
        model_code: {
            "data": data
        }
    }
    users_models[user.id][model_code]["photos"] = photos

    photo_data = photos[last_index]

    currency = db.EscortUsers.get_user_data(user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        costs = [round(cost * rates[currency]) for cost in costs]

    inline = InlineKeyboardMarkup()
    inline.row(InlineKeyboardButton("💘 Оформить", callback_data="ofrm_%s" % model_code),
               InlineKeyboardButton("📸 Другое фото", callback_data="ot_%s" % model_code))
    inline.add(InlineKeyboardButton("📔 Услуги", callback_data="services_%s" % model_code))
    inline.add(InlineKeyboardButton("Закрыть", callback_data="close"))

    await bot.send_photo(chat_id=user.id,
                         photo=photo_data,
                         caption=texts.MainMenu.FindModel.Model.text.format(
                             name=data[0],
                             age=data[1],
                             city=data[4],
                             hour=costs[0],
                             three_hours=costs[1],
                             night=costs[2],
                             currency=currency,
                             height=data[2],
                             boobs_size=data[3]
                         ),
                         reply_markup=inline,
                         parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("ofrm_"))
async def ofrm(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]

    if callback_query.from_user.id not in users_agreed:
        inline = InlineKeyboardMarkup()
        inline.add(InlineKeyboardButton("Ознакомлен", callback_data="agreement_%s" % model_code))
        inline.add(InlineKeyboardButton("Назад", callback_data="back_%s" % model_code))

        return await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.agreement,
                                                         reply_markup=inline,
                                                         parse_mode="HTML")

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        costs = [round(cost * rates[currency]) for cost in costs]

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("🌇 Час - %d %s" % (costs[0], currency), callback_data="hours_%s_1" % model_code))
    inline.add(InlineKeyboardButton("🏙 3 часа - %d %s" % (costs[1], currency), callback_data="hours_%s_3" % model_code))
    inline.add(InlineKeyboardButton("🌃 Ночь - %d %s" % (costs[2], currency), callback_data="hours_%s_n" % model_code))
    inline.add(InlineKeyboardButton("Назад", callback_data="back_%s" % model_code))

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.text,
                                              reply_markup=inline)


@dp.callback_query_handler(lambda c: c.data.startswith("hours_"))
async def hours(callback_query: types.CallbackQuery):
    hrs = callback_query.data.split("_")[2]
    model_code = callback_query.data.split("_")[1]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    inline = InlineKeyboardMarkup()

    additional = data[6].split(";")
    if len(additional[0]) > 0:
        add_names = [add.split(":")[0] for add in additional]
        add_costs = [int(add.split(":")[1]) for add in additional]

        if currency != "RUB":
            rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
            add_costs = [round(cost * rates[currency]) for cost in add_costs]

        if hrs == "1":
            total_amount = costs[0]
        elif hrs == "3":
            total_amount = costs[1]
        elif hrs == "n":
            total_amount = costs[2]

        counter = 0
        for name, cost in dict(zip(add_names, add_costs)).items():
            inline.add(InlineKeyboardButton("[ X ] - %s - %d %s" % (name, cost, currency),
                                            callback_data="add_%d_%d_%s" % (counter, total_amount, model_code)))
            counter += 1
    if hrs == "1":
        total_amount = costs[0]
    elif hrs == "3":
        total_amount = costs[1]
    elif hrs == "n":
        total_amount = costs[2]
    inline.add(InlineKeyboardButton("Далее", callback_data="add_n_%d_%s" % (total_amount, model_code)))
    inline.add(InlineKeyboardButton("Назад", callback_data="ofrm_%s" % model_code))

    additional_services_cost[callback_query.from_user.id] = [int(total_amount), [-1]]

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.add,
                                              reply_markup=inline,
                                              parse_mode="HTML")


async def repeat(model_code: str, user_id: int, message: types.Message):
    data = users_models[user_id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(user_id)[3]

    inline = InlineKeyboardMarkup()

    additional = data[6].split(";")
    if len(additional[0]) > 0:
        add_names = [add.split(":")[0] for add in additional]
        add_costs = [int(add.split(":")[1]) for add in additional]

        if currency != "RUB":
            rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
            add_costs = [round(cost * rates[currency]) for cost in add_costs]

        counter = 0
        for name, cost in dict(zip(add_names, add_costs)).items():
            if counter in additional_services_cost[user_id][1]:
                counter += 1
                continue

            inline.add(InlineKeyboardButton("[ X ] - %s - %d %s" % (name, cost, currency),
                                            callback_data="add_%d_%d_%s" % (counter, 0, model_code)))
            counter += 1

    inline.add(InlineKeyboardButton("Далее", callback_data="add_n_%d_%s" % (1, model_code)))
    inline.add(InlineKeyboardButton("Назад", callback_data="ofrm_%s" % model_code))

    await message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.add,
                               reply_markup=inline,
                               parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("add_"))
async def additional_services(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    counter = data[1]
    # total_amount = int(data[2])
    model_code = data[3]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    if counter != "n":
        additional = data[6].split(";")
        add_costs = [int(add.split(":")[1]) for add in additional]

        # total_amount += add_costs[int(counter)]

        additional_services_cost[callback_query.from_user.id][0] += add_costs[int(counter)]
        additional_services_cost[callback_query.from_user.id][1].append(int(counter))

        return await repeat(model_code, callback_query.from_user.id, callback_query.message)

    amount_chooses[callback_query.from_user.id] = [additional_services_cost[callback_query.from_user.id][0], 3]

    await choose_method(callback_query)

    # current_balance = db.EscortUsers.get_user_data(callback_query.from_user.id)[0]
    # if current_balance < total_amount:
    #     return await callback_query.message.edit_caption(caption="У вас недостаточно баланса!")
    #
    # db.EscortUsers.change_balance(callback_query.from_user.id, total_amount)
    #
    # await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Formalize.final,
    #                                           reply_markup=texts.MainMenu.FindModel.Model.Formalize.inline,
    #                                           parse_mode="HTML")

    # try:
    #     id_telegram = db.Workers.get_id(db.EscortUsers.get_ref_code(callback_query.from_user.id))
    #     model = "%s (%d) (%s)" % (data[0], data[1], "/" + data[12])
    #     await worker_bot.send_message(chat_id=id_telegram,
    #                                   text=texts.Actions.formalize.format(
    #                                       name=callback_query.from_user.first_name,
    #                                       model=model
    #                                   ),
    #                                   parse_mode="HTML")
    # except:
    #     pass


@dp.callback_query_handler(lambda c: c.data.startswith("agreement_"))
async def accept_agreement(callback_query: types.CallbackQuery):
    users_agreed.append(callback_query.from_user.id)
    await ofrm(callback_query)


@dp.callback_query_handler(lambda c: c.data.startswith("back_"))
async def back(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    costs = [int(cost) for cost in data[5].split(";")]

    if currency != "RUB":
        rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
        costs = [round(cost * rates[currency]) for cost in costs]

    inline = InlineKeyboardMarkup()
    inline.row(InlineKeyboardButton("💘 Оформить", callback_data="ofrm_%s" % model_code),
               InlineKeyboardButton("📸 Другое фото", callback_data="ot_%s" % model_code))
    inline.add(InlineKeyboardButton("📔 Услуги", callback_data="services_%s" % model_code))
    inline.add(InlineKeyboardButton("Закрыть", callback_data="close"))

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.text.format(
        name=data[0],
        age=data[1],
        city=data[4],
        hour=costs[0],
        three_hours=costs[1],
        night=costs[2],
        currency=currency,
        height=data[2],
        boobs_size=data[3]
    ),
        reply_markup=inline,
        parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("services_"))
async def services(callback_query: types.CallbackQuery):
    model_code = callback_query.data.split("_")[1]

    data = users_models[callback_query.from_user.id][model_code]["data"]

    currency = db.EscortUsers.get_user_data(callback_query.from_user.id)[3]
    additional = data[6].split(";")
    if len(additional[0]) > 0:
        add_names = [add.split(":")[0] for add in additional]
        add_costs = [int(add.split(":")[1]) for add in additional]

        if currency != "RUB":
            rates = requests.get("https://www.cbr-xml-daily.ru/latest.js").json()["rates"]
            add_costs = [round(cost * rates[currency]) for cost in add_costs]

        additional_message = ""
        for name, cost in dict(zip(add_names, add_costs)).items():
            additional_message += "• %s - %d %s" % (name, cost, currency) + "\n"
        if additional_message:
            additional_message += "\n"
    else:
        additional_message = ""

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("💘 Оформить", callback_data="ofrm_%s" % model_code))
    inline.add(InlineKeyboardButton("Назад", callback_data="back_%s" % model_code))

    await callback_query.message.edit_caption(caption=texts.MainMenu.FindModel.Model.Services.text.format(
        name=data[0],
        city=data[4],
        additional=additional_message
    ),
        reply_markup=inline,
        parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("ot_"))
async def another_photo(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    model_code = callback_query.data.split("_")[1]
    photos = users_models[callback_query.from_user.id][model_code]["photos"]
    text = callback_query.message.html_text
    inline = callback_query.message.reply_markup

    if "next_index" in users_models[callback_query.from_user.id][model_code]:
        next_index = users_models[callback_query.from_user.id][model_code]["next_index"]

        photo = photos[next_index]

        next_index += 1
        if next_index + 1 > len(photos):
            next_index = 0

        users_models[callback_query.from_user.id][model_code]["next_index"] = next_index
    else:
        if len(photos) == 1:
            photo = photos[0]

            users_models[callback_query.from_user.id][model_code]["next_index"] = 0
        elif len(photos) == 2:
            photo = photos[1]

            users_models[callback_query.from_user.id][model_code]["next_index"] = 0
        else:
            photo = photos[1]

            users_models[callback_query.from_user.id][model_code]["next_index"] = 2

    await callback_query.message.edit_media(
        media=InputMediaPhoto(media=photo, caption=text, parse_mode="HTML"),
        reply_markup=inline)


@dp.callback_query_handler(lambda c: c.data.startswith("close"))
async def close(callback_query: types.CallbackQuery):
    await callback_query.message.delete()


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "feedback")
async def draw_feedback(callback_query: types.CallbackQuery):
    feedbacks = db.Feedbacks.get_feedbacks()
    photo, inline = texts.MainMenu.Feedbacks.draw_feedbacks(1, feedbacks)

    await callback_query.message.edit_media(media=photo, reply_markup=inline)


@dp.callback_query_handler(lambda c: c.data.startswith("fd_"))
async def next_page_feedbacks(callback_query: types.CallbackQuery):
    feedbacks = db.Feedbacks.get_feedbacks()
    photo, inline = texts.MainMenu.Feedbacks.draw_feedbacks(int(callback_query.data.split("_")[1]), feedbacks)

    await callback_query.message.edit_media(media=photo, reply_markup=inline)


# ----------------------------------------------------------------------------------------------------------------------


@dp.message_handler(lambda msg: re.match(r"/m.*", msg.text))
async def model_command(msg: types.Message):
    model_code = msg.text[1:]
    try:
        model_data = db.Models.get_model_data(model_code)
    except:
        return

    if not model_data:
        return
    else:
        await draw_model(msg.from_user, model_data, model_code, 0)


# ----------------------------------------------------------------------------------------------------------------------


@dp.message_handler(commands=['worker'])
async def worker_menu(msg: types.Message):
    ids = db.Workers.get_ids()
    if msg.from_user.id not in ids:
        return

    await msg.delete()
    await bot.send_photo(chat_id=msg.from_user.id,
                         photo=open('media/frame.png', 'rb'),
                         caption=texts.Worker.text,
                         reply_markup=texts.Worker.inline,
                         parse_mode="HTML")


async def draw_worker_menu(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.Worker.text,
                                              reply_markup=texts.Worker.inline,
                                              parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "close_worker")
async def close_worker(callback_query: types.CallbackQuery):
    await callback_query.message.delete()


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "worker_back_mamonts")
async def back_mamonts(callback_query: types.CallbackQuery):
    await draw_worker_menu(callback_query)


@dp.callback_query_handler(lambda c: c.data == "close_mamont")
async def close_mamont(callback_query: types.CallbackQuery):
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data == "my_mamonts")
async def my_mamonts(callback_query: types.CallbackQuery):
    inline = InlineKeyboardMarkup()

    mamonts = db.Workers.get_mamonts(callback_query.from_user.id)
    for mamont in mamonts:
        user = await bot.get_chat_member(chat_id=mamont[0], user_id=mamont[0])
        username = user.user.first_name
        inline.add(InlineKeyboardButton("%s - %s" % (username, str(mamont[1]).split(" ")[0]),
                                        callback_data="mamont_%d" % mamont[0]))

    inline.add(InlineKeyboardButton("Назад", callback_data="worker_back_mamonts"))

    await callback_query.message.edit_caption(caption=texts.Worker.MyMamonts.text,
                                              reply_markup=inline)


@dp.callback_query_handler(lambda c: c.data.startswith("mamont_") or c.data.startswith("upd_"))
async def mamont_action(callback_query: types.CallbackQuery):
    await draw_mamont(callback_query)


async def draw_mamont(callback_query: types.CallbackQuery = None, mamont_id: int = None, user_id: int = None):
    if mamont_id is None:
        mamont_id = int(callback_query.data.split("_")[1])
    mamont_data = db.EscortUsers.get_user_data(mamont_id)

    user = await bot.get_chat_member(chat_id=mamont_id, user_id=mamont_id)
    username = user.user.first_name

    if mamont_data[2] == 1:
        subscription = "⭐️ VIP подписка"
    elif mamont_data[2] == 2:
        subscription = "💎 PREMIUM подписка"
    elif mamont_data[2] == 3:
        subscription = "👑 GOLD подписка"
    else:
        subscription = "❌ Отсутствует"

    inline = InlineKeyboardMarkup()
    inline.row(InlineKeyboardButton("💰 Изм. баланс", callback_data="chalance_%d" % mamont_id),
               InlineKeyboardButton("🗑 Удалить", callback_data="del_%d" % mamont_id))
    inline.row(InlineKeyboardButton("✉️ Сообщение", callback_data="msg_%d" % mamont_id),
               InlineKeyboardButton("🔄 Обновить", callback_data="upd_%d" % mamont_id))

    if callback_query is not None:
        inline.add(InlineKeyboardButton("Назад", callback_data="my_mamonts"))

        await callback_query.message.edit_caption(caption=texts.Worker.MyMamonts.mamont.format(
            name=username,
            mamont_id=mamont_id,
            amount=mamont_data[0],
            subscription=subscription,
            min_dep=mamont_data[4],
            update=datetime.datetime.now().strftime("%H:%M:%S")
        ),
            reply_markup=inline,
            parse_mode="HTML")
    else:
        inline.add(InlineKeyboardButton("Закрыть", callback_data="close_mamont"))

        await bot.send_photo(chat_id=user_id,
                             photo=open('media/frame.png', 'rb'),
                             caption=texts.Worker.MyMamonts.mamont.format(
                                 name=username,
                                 mamont_id=mamont_id,
                                 amount=mamont_data[0],
                                 subscription=subscription,
                                 min_dep=mamont_data[4],
                                 update=datetime.datetime.now().strftime("%H:%M:%S")
                             ),
                             reply_markup=inline,
                             parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("chalance_"))
async def change_balance(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("Отмена", callback_data="cancel_chalance"))

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="▶️ Введите новый баланс для мамонта.",
                           reply_markup=inline)

    await ChangeBalance.mamont_id.set()
    state = dp.current_state(chat=callback_query.from_user.id, user=callback_query.from_user.id)
    await state.update_data(mamont_id=callback_query.data.split("_")[1])

    await ChangeBalance.balance.set()


@dp.callback_query_handler(lambda c: c.data == "cancel_chalance", state=ChangeBalance)
async def cancel_chalance(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await callback_query.message.delete()


@dp.message_handler(state=ChangeBalance.balance)
async def new_balance(msg: types.Message, state: FSMContext):
    try:
        amount = float(msg.text)
    except:
        await msg.delete()
        return ChangeBalance.balance.set()

    data = await state.get_data()
    mamont_id = data.get("mamont_id")
    await state.finish()

    db.EscortUsers.new_balance(int(mamont_id), amount)

    await bot.send_message(chat_id=msg.from_user.id,
                           text="<b>💳 Баланс успешно изменен</b>",
                           parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("msg_"))
async def send_mamont_message(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("Назад", callback_data="cancel_msg"))

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="<i>✉️ Введите текст для ответа:</i>",
                           reply_markup=inline,
                           parse_mode="HTML")

    await MamontMessage.mamont_id.set()
    state = dp.current_state(chat=callback_query.from_user.id, user=callback_query.from_user.id)
    await state.update_data(mamont_id=callback_query.data.split("_")[1])

    await MamontMessage.message.set()


@dp.callback_query_handler(lambda c: c.data == "cancel_msg", state=MamontMessage)
async def cancel_msg(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await callback_query.message.delete()


@dp.message_handler(state=MamontMessage.message)
async def mamont_message(msg: types.Message, state: FSMContext):
    text = msg.text

    data = await state.get_data()
    mamont_id = data.get("mamont_id")
    await state.finish()

    try:
        await bot.send_message(chat_id=mamont_id,
                               text=text)

        await bot.send_message(chat_id=msg.from_user.id,
                               text="<b>✅ Сообщение успешно отправлено мамонту!</b>",
                               parse_mode="HTML")
    except:
        await bot.send_message(chat_id=msg.from_user.id,
                               text="<b>❌ Не удалось отправить сообщение мамонту</b>",
                               parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("del_"))
async def del_mamont(callback_query: types.CallbackQuery):
    db.EscortUsers.delete_user(int(callback_query.data.split("_")[1]))

    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text="Мамонт успешно удален!",
                                    show_alert=True)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "find_mamont")
async def find_mamont(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("Отмена", callback_data="cancel_find"))

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="<b>▶️ Введите ID мамонта:</b>",
                           reply_markup=inline,
                           parse_mode="HTML")

    await FindMamont.mamont_id.set()


@dp.callback_query_handler(lambda c: c.data == "cancel_find", state=FindMamont)
async def cancel_find(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await callback_query.message.delete()


@dp.message_handler(state=FindMamont.mamont_id)
async def find_mamont_id(msg: types.Message, state: FSMContext):
    try:
        mamont_id = int(msg.text)
    except:
        return await msg.delete()

    ids = [mamont[0] for mamont in db.Workers.get_mamonts(msg.from_user.id)]
    if mamont_id not in ids:
        return await msg.delete()

    await state.finish()

    await draw_mamont(mamont_id=mamont_id, user_id=msg.from_user.id)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "mass_spam")
async def mass_spam(callback_query: types.CallbackQuery):
    await callback_query.message.edit_caption(caption=texts.Worker.Spam.text,
                                              reply_markup=texts.Worker.Spam.inline,
                                              parse_mode="HTML")


async def send_mass_spam(id_telegram: int):
    await bot.send_photo(chat_id=id_telegram,
                         photo=open('media/frame.png', 'rb'),
                         caption=texts.Worker.Spam.text,
                         reply_markup=texts.Worker.Spam.inline,
                         parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "spam_text")
async def spam_text(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="<b>Введите текст рассылки:</b>",
                           parse_mode="HTML")

    await MassSpam.text_text.set()


@dp.message_handler(content_types=ContentType.TEXT, state=MassSpam.text_text)
async def spam_text_handler(msg: types.Message, state: FSMContext):
    await state.update_data(text=msg.text)

    await bot.send_message(chat_id=msg.from_user.id,
                           text=msg.text)

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("✅ Начать"), KeyboardButton("💢 Отмена"))
    reply.resize_keyboard = True

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Выбери дальнейшее действие",
                           reply_markup=reply)

    await MassSpam.action_text.set()


@dp.message_handler(state=MassSpam.action_text)
async def text_action(msg: types.Message, state: FSMContext):
    if msg.text == "✅ Начать":
        await bot.send_message(chat_id=msg.from_user.id,
                               text="✅ Вы запустили рассылку")

        data = await state.get_data()
        text = data.get("text")
        await state.finish()

        await send_text(msg.from_user.id, text, msg)
    elif msg.text == "💢 Отмена":
        await bot.send_message(chat_id=msg.from_user.id,
                               text="💢 Вы отменили рассылку")

        await state.finish()

        await send_mass_spam(msg.from_user.id)


async def send_text(id_telegram: int, text: str, msg: types.Message):
    mamonts = [mamont[0] for mamont in db.Workers.get_mamonts(id_telegram)]

    plus = 0
    minus = 0

    for mamont in mamonts:
        try:
            await bot.send_message(chat_id=mamont,
                                   text=text)

            plus += 1
        except:
            minus += 1

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("💘 Главное меню"), KeyboardButton("👩‍💻 Тех. поддержка"))
    reply.resize_keyboard = True

    await bot.send_message(chat_id=id_telegram,
                           text="✅ Рассылка успешно закончена\n"
                                "📩 Отправлено: %d\n"
                                "📮 Не отправлено: %d" % (plus, minus),
                           reply_markup=reply)

    await worker_menu(msg)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "spam_photo")
async def spam_photo(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="<b>Отправьте боту фото, только фото!</b>",
                           parse_mode="HTML")

    await MassSpam.photo.set()


@dp.message_handler(content_types=ContentType.PHOTO, state=MassSpam.photo)
async def spam_photo_handler(msg: types.Message, state: FSMContext):
    await state.update_data(photo=msg.photo[-1].file_id)

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Введите текст рассылки")

    await MassSpam.text_photo.set()


@dp.message_handler(content_types=ContentType.TEXT, state=MassSpam.text_photo)
async def spam_photo_text_handler(msg: types.Message, state: FSMContext):
    await state.update_data(text=msg.text)

    data = await state.get_data()
    photo = data.get("photo")

    await bot.send_photo(chat_id=msg.from_user.id,
                         photo=photo,
                         caption=msg.text)

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("✅ Начать"), KeyboardButton("💢 Отмена"))
    reply.resize_keyboard = True

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Выбери дальнейшее действие",
                           reply_markup=reply)

    await MassSpam.action_photo.set()


@dp.message_handler(state=MassSpam.action_photo)
async def photo_action(msg: types.Message, state: FSMContext):
    if msg.text == "✅ Начать":
        await bot.send_message(chat_id=msg.from_user.id,
                               text="✅ Вы запустили рассылку")

        data = await state.get_data()
        text = data.get("text")
        photo = data.get("photo")
        await state.finish()

        await send_photo(msg.from_user.id, text, photo, msg)
    elif msg.text == "💢 Отмена":
        await bot.send_message(chat_id=msg.from_user.id,
                               text="💢 Вы отменили рассылку")

        await state.finish()

        await send_mass_spam(msg.from_user.id)


async def send_photo(id_telegram: int, text: str, photo: str, msg: types.Message):
    mamonts = [mamont[0] for mamont in db.Workers.get_mamonts(id_telegram)]

    plus = 0
    minus = 0

    for mamont in mamonts:
        try:
            await bot.send_photo(chat_id=mamont,
                                 photo=photo,
                                 caption=text)

            plus += 1
        except:
            minus += 1

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("💘 Главное меню"), KeyboardButton("👩‍💻 Тех. поддержка"))
    reply.resize_keyboard = True

    await bot.send_message(chat_id=id_telegram,
                           text="✅ Рассылка успешно закончена\n"
                                "📩 Отправлено: %d\n"
                                "📮 Не отправлено: %d" % (plus, minus),
                           reply_markup=reply)

    await worker_menu(msg)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "spam_post")
async def spam_post(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="<b>Пришлите боту пост, который хотите переслать!</b>",
                           parse_mode="HTML")

    await MassSpam.text_post.set()


@dp.message_handler(content_types=ContentType.ANY, state=MassSpam.text_post)
async def spam_post_handler(msg: types.Message, state: FSMContext):
    await state.update_data(message_chat_id=msg.chat.id,
                            message_id=msg.message_id)

    await bot.forward_message(chat_id=msg.from_user.id,
                              from_chat_id=msg.chat.id,
                              message_id=msg.message_id)

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("✅ Начать"), KeyboardButton("💢 Отмена"))
    reply.resize_keyboard = True

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Выбери дальнейшее действие",
                           reply_markup=reply)

    await MassSpam.action_post.set()


@dp.message_handler(state=MassSpam.action_post)
async def post_action(msg: types.Message, state: FSMContext):
    if msg.text == "✅ Начать":
        await bot.send_message(chat_id=msg.from_user.id,
                               text="✅ Вы запустили рассылку")

        data = await state.get_data()
        message_chat_id = data.get("message_chat_id")
        message_id = data.get("message_id")
        await state.finish()

        await send_post(msg.from_user.id, message_chat_id, message_id, msg)
    elif msg.text == "💢 Отмена":
        await bot.send_message(chat_id=msg.from_user.id,
                               text="💢 Вы отменили рассылку")

        await state.finish()

        await send_mass_spam(msg.from_user.id)


async def send_post(id_telegram: int, message_chat_id: int, message_id: int, msg: types.Message):
    mamonts = [mamont[0] for mamont in db.Workers.get_mamonts(id_telegram)]

    plus = 0
    minus = 0

    for mamont in mamonts:
        try:
            await bot.forward_message(chat_id=mamont,
                                      from_chat_id=message_chat_id,
                                      message_id=message_id)

            plus += 1
        except:
            minus += 1

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("💘 Главное меню"), KeyboardButton("👩‍💻 Тех. поддержка"))
    reply.resize_keyboard = True

    await bot.send_message(chat_id=id_telegram,
                           text="✅ Рассылка успешно закончена\n"
                                "📩 Отправлено: %d\n"
                                "📮 Не отправлено: %d" % (plus, minus),
                           reply_markup=reply)

    await worker_menu(msg)


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "my_models")
async def my_models(callback_query: types.CallbackQuery):
    text = "<b>💘 Мои анкеты:</b>"

    models = db.Models.get_worker_models(callback_query.from_user.id)

    inline = InlineKeyboardMarkup()
    for model in models:
        inline.add(InlineKeyboardButton("💘 %s (%d) - %s" % (model[1], model[2], model[3]),
                                        callback_data="md_%s" % model[0]))
    inline.add(InlineKeyboardButton("✏️ Добавить модель", callback_data="addd_model"))
    inline.add(InlineKeyboardButton("Назад", callback_data="worker_back_mamonts"))

    await callback_query.message.edit_media(media=InputMediaPhoto(
        media=open('media/frame.png', 'rb'),
        caption=text,
        parse_mode="HTML"
    ),
        reply_markup=inline
    )


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data == "addd_model")
async def name_enter(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query_id=callback_query.id)

    text = ("1/6 Введите имя модели / пример. Вика\n\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=text)

    await CreateModel.model_name.set()


@dp.message_handler(content_types=ContentType.TEXT, state=CreateModel.model_name)
async def city_enter(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.finish()
        return await bot.send_message(chat_id=msg.from_user.id,
                                      text="❌ Операция отменена")

    await state.update_data(model_name=msg.text)

    text = ("2/6 Введите название города модели / пример. Москва\n\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text)

    await CreateModel.city.set()


@dp.message_handler(content_types=ContentType.TEXT, state=CreateModel.city)
async def main_cost_enter(msg: types.Message, state: FSMContext):
    cities = ["Москва", "Санкт-Петербург", "Сочи", "Ростов-на-Дону", "Екатеринбург", "Новосибирск",
              "Нижний Новгород", "Казань", "Краснодар", "Самара"]

    if msg.text not in cities:
        await bot.send_message(chat_id=msg.from_user.id,
                               text="Такого города нет в списке")
        return await CreateModel.city.set()

    if msg.text == "отмена":
        await state.finish()
        return await bot.send_message(chat_id=msg.from_user.id,
                                      text="❌ Операция отменена")

    await state.update_data(city=msg.text)

    text = ("3/6 Введите цена за час, 3 часа и ночь в формате\n"
            "<code>цена1;цена2;цена3</code> (минимальная цена 3000 РУБ)\n\n"
            "пример: 3000;8000;20000\n\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.main_cost.set()


@dp.message_handler(content_types=ContentType.TEXT, state=CreateModel.main_cost)
async def add_cost_enter(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.finish()
        return await bot.send_message(chat_id=msg.from_user.id,
                                      text="❌ Операция отменена")

    await state.update_data(main_cost=msg.text)

    text = ("4/6 Введите цены за доп услуги в формате\n"
            "<code>услуга1:цена1;услуга2:цена2;услуга3:цена3</code>\n\n"
            "пример Кончить в рот:3000;Нассать на лицо:8000;Кончить в нос:20000\n\n"
            "Для продолжения напишите \"далее\"\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.add_cost.set()


@dp.message_handler(content_types=ContentType.TEXT, state=CreateModel.add_cost)
async def parameters_enter(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.finish()
        return await bot.send_message(chat_id=msg.from_user.id,
                                      text="❌ Операция отменена")

    if msg.text.lower() == "далее":
        await state.update_data(add_cost="")
    else:
        await state.update_data(add_cost=msg.text)

    text = ("5/6 Введите возраст рост и размер груди в формате\n"
            "<code>возраст;рост;размер</code>\n\n"
            "пример 21;169;3\n\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.parameters.set()


@dp.message_handler(content_types=ContentType.TEXT, state=CreateModel.parameters)
async def photos_enter(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.finish()
        return await bot.send_message(chat_id=msg.from_user.id,
                                      text="❌ Операция отменена")

    await state.update_data(parameters=msg.text)

    text = ("6/6 Отправьте первую фотографию модели\n\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.photo_one.set()


@dp.message_handler(content_types=ContentType.ANY, state=CreateModel.photo_one)
async def photo_two(msg: types.Message, state: FSMContext):
    if msg.text == "отмена":
        await state.finish()
        return await bot.send_message(chat_id=msg.from_user.id,
                                      text="❌ Операция отменена")

    await state.update_data(photo_one=msg.photo[-1].file_id)

    text = ("6/6 Отправьте вторую фотографию модели\n\n"
            "Для продолжения напишите \"далее\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.photo_two.set()


@dp.message_handler(content_types=ContentType.ANY, state=CreateModel.photo_two)
async def photo_three(msg: types.Message, state: FSMContext):
    try:
        if msg.text.lower() == "далее":
            return await create_model(state, msg.from_user.id)
    except:
        pass

    await state.update_data(photo_two=msg.photo[-1].file_id)

    text = ("6/6 Отправьте третюю фотографию модели\n\n"
            "Для продолжения напишите \"далее\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.photo_three.set()


@dp.message_handler(content_types=ContentType.ANY, state=CreateModel.photo_three)
async def photo_four(msg: types.Message, state: FSMContext):
    try:
        if msg.text.lower() == "далее":
            return await create_model(state, msg.from_user.id)
    except:
        pass

    await state.update_data(photo_three=msg.photo[-1].file_id)

    text = ("6/6 Отправьте четвертую фотографию модели\n\n"
            "Для продолжения напишите \"далее\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.photo_four.set()


@dp.message_handler(content_types=ContentType.ANY, state=CreateModel.photo_four)
async def photo_five(msg: types.Message, state: FSMContext):
    try:
        if msg.text.lower() == "далее":
            return await create_model(state, msg.from_user.id)
    except:
        pass

    await state.update_data(photo_four=msg.photo[-1].file_id)

    text = ("6/6 Отправьте пятую фотографию модели\n\n"
            "Для продолжения напишите \"далее\"")

    await bot.send_message(chat_id=msg.from_user.id,
                           text=text,
                           parse_mode="HTML")

    await CreateModel.photo_five.set()


@dp.message_handler(content_types=ContentType.ANY, state=CreateModel.photo_five)
async def photo_five_handler(msg: types.Message, state: FSMContext):
    try:
        if msg.text.lower() == "далее":
            return await create_model(state, msg.from_user.id)
    except:
        pass

    await state.update_data(photo_five=msg.photo[-1].file_id)

    await create_model(state, msg.from_user.id)


async def create_model(state: FSMContext, id_telegram: int):
    cities = ["Москва", "Санкт-Петербург", "Сочи", "Ростов-на-Дону", "Екатеринбург", "Новосибирск",
              "Нижний Новгород", "Казань", "Краснодар", "Самара"]

    data = await state.get_data()
    model_id = "m%d" % random.randint(100000, 999999)
    name = data.get("model_name")
    city = data.get("city")
    main_cost = data.get("main_cost").split(";")
    add_cost = data.get("add_cost").split(";")
    parameters = data.get("parameters").split(";")
    pphoto_one = data.get("photo_one")
    pphoto_two = data.get("photo_two")
    pphoto_three = data.get("photo_three")
    pphoto_four = data.get("photo_four")
    pphoto_five = data.get("photo_five")
    photos_list = [pphoto_one, pphoto_two, pphoto_three, pphoto_four, pphoto_five]
    photos_ids = ""
    for photo in photos_list:
        if photo is not None:
            photos_ids += photo + ";"
    await state.finish()

    if city not in cities or len(main_cost) < 3 or len(add_cost) > 3 or len(parameters) > 3:
        return await bot.send_message(chat_id=id_telegram,
                                      text="Вы допустили ошибку при заполнении формы, попробуйте ещё раз.")

    for cost in main_cost:
        if float(cost) < 3000:
            return await bot.send_message(chat_id=id_telegram,
                                          text="Вы допустили ошибку при заполнении формы, попробуйте ещё раз.")

    created_models[id_telegram] = {
        model_id: [model_id, name, parameters[0], parameters[1], parameters[2], city, ";".join(main_cost),
                   ";".join(add_cost), pphoto_one, pphoto_two, pphoto_three, pphoto_four, pphoto_five, id_telegram]
    }

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("🔄 Начать заново", callback_data="restart_%s" % model_id))
    inline.row(InlineKeyboardButton("✅ Подтвердить", callback_data="create_accept_%s" % model_id),
               InlineKeyboardButton("❌ Отменить", callback_data="create_cancel_%s" % model_id))

    text = ("⚠️ Проверьте все ли данные верны?\n\n"
            "<b>💘 %s (%s)</b>\n\n"
            "🌆 Час - %s руб\n"
            "🏙 3 часа - %s руб\n"
            "🌃 Ночь - %s руб\n\n"
            "Возраст - %s\n"
            "Рост - %s\n"
            "Размер груди - %s" % (name, city, str(main_cost[0]), str(main_cost[1]), str(main_cost[2]),
                                   str(parameters[0]), str(parameters[1]), str(parameters[2])))

    await bot.send_photo(chat_id=id_telegram,
                         photo=pphoto_one,
                         caption=text,
                         reply_markup=inline,
                         parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("restart_"))
async def create_restart(callback_query: types.CallbackQuery):
    del created_models[callback_query.from_user.id][callback_query.data.split("_")[1]]

    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup())

    text = ("1/6 Введите имя модели / пример. Вика\n\n"
            "Для отмены напишите \"отмена\"")

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text=text)

    await CreateModel.model_name.set()


@dp.callback_query_handler(lambda c: c.data.startswith("create_accept_"))
async def create_accept(callback_query: types.CallbackQuery):
    data = created_models[callback_query.from_user.id][callback_query.data.split("_")[2]]
    # db.Models.insert_new_model(data)

    await bot.send_message(chat_id=callback_query.from_user.id,
                           text="✅ Заявка на создание модели отправлена")

    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup())

    # created_models[id_telegram] = {
    #     model_id: [model_id, name, parameters[0], parameters[1], parameters[2], city, ";".join(main_cost),
    #                ";".join(add_cost), pphoto_one, pphoto_two, pphoto_three, pphoto_four, pphoto_five, id_telegram]
    # }

    name = data[1]
    city = data[5]
    main_cost = data[6].split(";")
    parameters = [data[2], data[3], data[4]]
    pphoto_one = data[8]
    additional_data = data[7].split(";")
    additional = ""
    for additional_text in additional_data:
        if len(additional_text) == 0:
            continue
        add = additional_text.split(":")
        add_name = add[0]
        add_cost = add[1]
        additional += "%s - %s\n" % (add_name, add_cost)
    if additional:
        additional += "\n"

    inline = InlineKeyboardMarkup()
    inline.row(InlineKeyboardButton("✅ Одобрить", callback_data="plus_%s_%d" % (str(data[0]),
                                                                                callback_query.from_user.id)),
               InlineKeyboardButton("❌ Отказать", callback_data="minus_%s_%d" % (str(data[0]),
                                                                                 callback_query.from_user.id)))

    text = ("⚠️ Заявка на создание новой анкеты\n\n"
            "<b>💘 %s (%s)</b>\n\n"
            "🌆 Час - %s руб\n"
            "🏙 3 часа - %s руб\n"
            "🌃 Ночь - %s руб\n\n"
            "%s"
            "Возраст - %s\n"
            "Рост - %s\n"
            "Размер груди - %s" % (name, city, str(main_cost[0]), str(main_cost[1]), str(main_cost[2]), additional,
                                   str(parameters[0]), str(parameters[1]), str(parameters[2])))

    await bot.send_photo(chat_id=config.ADMIN_CHAT_ID,
                         photo=pphoto_one,
                         caption=text,
                         reply_markup=inline,
                         parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("create_cancel_"))
async def create_cancel(callback_query: types.CallbackQuery):
    del created_models[callback_query.from_user.id][callback_query.data.split("_")[2]]

    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text="❌ Вы отменили создание новой модели",
                                    show_alert=True)

    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup())

    await bot.send_photo(chat_id=callback_query.from_user.id,
                         photo=open('media/frame.png', 'rb'),
                         caption=texts.Worker.text,
                         reply_markup=texts.Worker.inline,
                         parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("plus_"))
async def plus_model(callback_query: types.CallbackQuery):
    id_telegram = callback_query.data.split("_")[2]
    model_id = callback_query.data.split("_")[1]
    text = callback_query.message.html_text + "\n\n<i>Заявка одобрена</i>"
    data = created_models[int(id_telegram)][model_id]

    db.Models.insert_new_model(data)

    await callback_query.message.edit_caption(caption=text, parse_mode="HTML")

    await bot.send_message(chat_id=id_telegram,
                           text="<b>✅ Ваша модель одобрена!</b>",
                           parse_mode="HTML")


@dp.callback_query_handler(lambda c: c.data.startswith("minus_"))
async def minus_model(callback_query: types.CallbackQuery):
    id_telegram = callback_query.data.split("_")[2]
    model_id = callback_query.data.split("_")[1]
    text = callback_query.message.html_text + "\n\n<i>Заявка отказана</i>"
    del created_models[int(id_telegram)][model_id]

    await callback_query.message.edit_caption(caption=text, parse_mode="HTML")

    await bot.send_message(chat_id=id_telegram,
                           text="<b>❌ Ваша модель отказана!</b>",
                           parse_mode="HTML")


# ----------------------------------------------------------------------------------------------------------------------


@dp.callback_query_handler(lambda c: c.data.startswith("md_"))
async def show_model_worker(callback_query: types.CallbackQuery):
    model_id = callback_query.data.split("_")[1]
    model_data = db.Models.get_model_data(model_id)

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("🗑 Удалить анкету", callback_data="delmd_%s" % model_id))
    inline.add(InlineKeyboardButton("Назад", callback_data="my_models"))

    main_costs = model_data[5].split(";")

    await callback_query.message.edit_media(media=InputMediaPhoto(
        media=model_data[7],
        caption=texts.Worker.Model.text.format(
            name=model_data[0],
            age=model_data[1],
            city=model_data[4],
            model_code="/" + model_id,
            hour=main_costs[0],
            three_hours=main_costs[1],
            night=main_costs[2],
            height=model_data[2],
            boobs_size=model_data[3],
        ),
        parse_mode="HTML"
    ),
        reply_markup=inline
    )


@dp.callback_query_handler(lambda c: c.data.startswith("delmd_"))
async def delete_model(callback_query: types.CallbackQuery):
    model_id = callback_query.data.split("_")[1]
    db.Models.delete_model(model_id)

    await bot.answer_callback_query(callback_query_id=callback_query.id,
                                    text="Анкета успешно удалена",
                                    show_alert=True)

    text = "<b>💘 Мои анкеты:</b>"

    models = db.Models.get_worker_models(callback_query.from_user.id)

    inline = InlineKeyboardMarkup()
    for model in models:
        inline.add(InlineKeyboardButton("💘 %s (%d) - %s" % (model[1], model[2], model[3]),
                                        callback_data="md_%s" % model[0]))
    inline.add(InlineKeyboardButton("✏️ Добавить модель", callback_data="addd_model"))
    inline.add(InlineKeyboardButton("Назад", callback_data="worker_back_mamonts"))

    await callback_query.message.edit_media(media=InputMediaPhoto(
        media=open('media/frame.png', 'rb'),
        caption=text,
        parse_mode="HTML"
    ),
        reply_markup=inline
    )


# ----------------------------------------------------------------------------------------------------------------------


@dp.message_handler(commands=['otziv'])
async def add_otziv(msg: types.Message):
    code = msg.get_args()
    if code != "532142":
        return

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Отправьте скрин")

    await CreateFeedback.photo.set()


@dp.message_handler(content_types=ContentType.PHOTO, state=CreateFeedback.photo)
async def feedback_photo_handler(msg: types.Message, state: FSMContext):
    await state.update_data(photo=msg.photo[-1].file_id)

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Введите текст")

    await CreateFeedback.text.set()


@dp.message_handler(content_types=ContentType.TEXT, state=CreateFeedback.text)
async def feedback_text_handler(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    photo = data.get("photo")
    await state.finish()

    db.Feedbacks.create_feedback(photo, msg.text)

    await bot.send_message(chat_id=msg.from_user.id,
                           text="Отзыв успешно создан")


# ----------------------------------------------------------------------------------------------------------------------


@dp.message_handler(commands=["chat_id"])
async def chat_id(msg: types.Message):
    await bot.send_message(chat_id=msg.chat.id,
                           text=str(msg.chat.id))


# ----------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    executor.start_polling(dp)
