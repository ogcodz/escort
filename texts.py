from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    InputMediaPhoto


class Actions:
    new = ("<b>🦣 Мамонт зашел в бот</b>\n\n"
           "🚀 Сервис: <b>💘 Эскорт</b>\n"
           "🤖 Бот: <b>Pleasure Club</b>\n"
           "👤 Имя: <b>{name}</b>\n"
           "🆔 ID мамонта: <code>{mamont_id}</code>")

    formalize = "💘 Мамонт {name} оформил девушку {model}."

    subscription = "💘 Мамонт {name} оформил подписку {subscription}."


class MainMenu:
    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("💘 VIP Модели", callback_data="vip_models"))
    inline.row(InlineKeyboardButton("✨ Купить подписку", callback_data="buy_subscription"),
               InlineKeyboardButton("🔍 Найти девушку", callback_data="find_model"))
    inline.row(InlineKeyboardButton("👤 Мой профиль", callback_data="my_profile"),
               InlineKeyboardButton("📔 Отзывы", callback_data="feedback"))
    inline.row(InlineKeyboardButton("👩‍💻 Тех. поддержка", url="https://t.me/pleasureclub_support"),
               InlineKeyboardButton("✅ Информация", callback_data="information"))

    reply = ReplyKeyboardMarkup()
    reply.row(KeyboardButton("💘 Главное меню"), KeyboardButton("👩‍💻 Тех. поддержка"))
    reply.resize_keyboard = True

    class VipModels:
        city_text = "<b>💘 Выберите город:</b>"

        @staticmethod
        def city_page(page: int) -> InlineKeyboardMarkup:
            cities = ["Москва", "Санкт-Петербург", "Сочи", "Ростов-на-Дону", "Екатеринбург", "Новосибирск",
              "Нижний Новгород", "Казань", "Краснодар", "Самара"]

            total_pages = len(cities) // 10 + (1 if len(cities) % 10 > 0 else 0)

            start_index = (page - 1) * 10
            end_index = start_index + 10
            page_cities = cities[start_index:end_index]

            inline = InlineKeyboardMarkup(row_width=2)
            for city in page_cities:
                inline.insert(InlineKeyboardButton(city, callback_data="city_%s_0" % city))

            up_page = page + 1
            if up_page > total_pages:
                up_page = 1

            down_page = page - 1
            if down_page == 0:
                down_page = total_pages

            inline.row(InlineKeyboardButton("<", callback_data="citypage_%d" % down_page),
                       InlineKeyboardButton("%d из %d" % (page, total_pages), callback_data="pages"),
                       InlineKeyboardButton(">", callback_data="citypage_%d" % up_page))
            inline.add(InlineKeyboardButton("Назад", callback_data="main_menu"))

            return inline

        model_text = ("💘 Все анкеты проходили строгую проверку личности нашим агентством. Свободных девушек: "
                      "<b>{models_active}</b>")

        @staticmethod
        def models_page(models: dict) -> InlineKeyboardMarkup:
            page_models = list(models.keys())[0:8]

            inline = InlineKeyboardMarkup(row_width=2)
            for model_id in page_models:
                inline.insert(InlineKeyboardButton(models[model_id], callback_data="model_%s" % model_id))

            inline.add(InlineKeyboardButton("Назад", callback_data="vip_models"))

            return inline

    class SubscriptionInfo:
        text = "✨ Выберите подписку:"

        inline = InlineKeyboardMarkup()
        inline.add(InlineKeyboardButton("⭐️ VIP подписка", callback_data="subs_vip"))
        inline.add(InlineKeyboardButton("💎 PREMIUM подписка", callback_data="subs_premium"))
        inline.add(InlineKeyboardButton("👑 GOLD подписка", callback_data="subs_gold"))
        inline.add(InlineKeyboardButton("Назад", callback_data="main_menu"))

        class VIP:
            text = ("<b>⭐️ VIP подписка</b>\n\n"
                    "• 3-часовая приватная встреча с любой моделью (стоимость модели отдельно)\n\n"
                    "• Личный менеджер, доступный 24/7 для консультаций и организации встреч\n\n"
                    "• Персонализированный подход к удовлетворению ваших пожеланий\n\n"
                    "• Доступ к конфиденциальным и эксклюзивным фотографиям моделей\n\n"
                    "<b>💵 Цена за месяц: {amount} руб</b>")

            inline = InlineKeyboardMarkup()
            inline.add(InlineKeyboardButton("💘 Купить", callback_data="buy_vip"))
            inline.add(InlineKeyboardButton("Назад", callback_data="buy_subscription"))

        class PREMIUM:
            text = ("<b>💎 PREMIUM подписка</b>\n\n"
                    "• 5 - часовая приватная встреча с выбранной моделью\n\n"
                    "• Дополнительные опции для расширения опыта "
                    "(например, ужин в ресторане, поездка за город и т. д.)\n\n"
                    "• Предварительное планирование встречи заранее\n\n"
                    "• Дополнительные фото и видео материалы моделей\n\n"
                    "<b>💵 Цена за месяц: {amount} руб</b>")

            inline = InlineKeyboardMarkup()
            inline.add(InlineKeyboardButton("💘 Купить", callback_data="buy_premium"))
            inline.add(InlineKeyboardButton("Назад", callback_data="buy_subscription"))

        class GOLD:
            text = ("<b>👑 GOLD подписка</b>\n\n"
                    "• 24 - часовая приватная встреча с выбранной моделью\n\n"
                    "• Эксклюзивные услуги, такие как спа-процедуры или массажи для расслабления и наслаждения\n\n"
                    "• Возможность выбора модели из специальной категории \"Элитные модели\"\n\n"
                    "• Бонусные подарки и скидки на последующие встречи\n\n"
                    "<b>💵 Цена за месяц: {amount} руб</b>")

            inline = InlineKeyboardMarkup()
            inline.add(InlineKeyboardButton("💘 Купить", callback_data="buy_gold"))
            inline.add(InlineKeyboardButton("Назад", callback_data="buy_subscription"))

        class Buy:
            text = ("💘 Вы успешно формили подписку {subscription}.\n\n"
                    "▶️ <i>Пожалуйста, напишите в поддержку за дальнейшей инструкцией.</i>")

            inline = InlineKeyboardMarkup()
            inline.add(InlineKeyboardButton("Поддержка 👩‍💻", url="https://t.me/pleasureclub_support"))

    class FindModel:
        text = "<b>🔍 Введите код девушки</b>"

        inline = InlineKeyboardMarkup()
        inline.add(InlineKeyboardButton("Отменить поиск", callback_data="drop_model_code"))

        class Model:
            text = ("<b>💘 {name} ({age}) ({city})</b>\n\n"
                    "🌇 Час - {hour} руб\n"
                    "🏙 3 часа - {three_hours} руб\n"
                    "🌃 Ночь - {night} руб\n\n"
                    "Возраст: {age}\n"
                    "Рост: {height}\n"
                    "Размер груди: {boobs_size}\n\n"
                    "✅ Для оформления нажмите на кнопку \"Оформить\"")

            class Formalize:
                agreement = ("Здравствуйте,\n\n"
                             "Хотелось бы поделиться важной информацией, чтобы гарантировать вашу безопасность "
                             "в сотрудничестве с нами. Мы настоятельно рекомендуем избегать использования сторонних "
                             "банковских реквизитов, которые могут быть предоставлены вам моделями. Это поможет "
                             "избежать потенциальных случаев мошенничества.\n\n"
                             "Пожалуйста, используйте только те платежные реквизиты, которые указаны в нашем боте."
                             " Наша единственная учетная запись для технической поддержки имеет следующие"
                             " данные: @pleasureclub_support. Это гарантирует вам надежное взаимодействие с нами.\n\n"
                             "После оформления заказа с моделью, не забудьте связаться с нашей службой поддержки"
                             " через диалог, чтобы уточнить детали встречи, связанные с оплаченным заказом."
                             " Мы всегда готовы помочь вам и обеспечить гладкое и безопасное взаимодействие.\n\n"
                             "Спасибо за понимание и сотрудничество. В случае любых вопросов, не стесняйтесь"
                             " обращаться к нам.\n\n"
                             "С наилучшими пожеланиями,\n"
                             "Команда технической поддержки агентства Pleasure Club.")

                text = "💘 Выберите время на которое вы хотите оформить модель:"

                add = "💘 Выберите дополнительные услуги, если нужны, и нажмите кнопку \"Далее\""

                final = ("💘 Вы успешно оформили модель.\n\n"
                         "▶️ <i>Пожалуйста, напишите в поддержку за дальнейшей инструкцией.</i>")

                inline = InlineKeyboardMarkup()
                inline.add(InlineKeyboardButton("Поддержка 👩‍💻", url="https://t.me/pleasureclub_support"))

            class Services:
                text = ("<b>💘 {name} ({city})</b>\n\n"
                        "Дополнительные услуги:\n"
                        "{additional}")

    class Profile:
        text = ("<b>🖥 Личный кабинет</b>\n\n"
                "Ваш айди: <code>{id_telegram}</code>\n"
                # "Баланс: <b>{balance} руб</b>\n"
                "Дата регистрации: <b>{date}</b>\n"
                "Подписка: <b>{subscription}</b>")

        inline = InlineKeyboardMarkup()
        # inline.add(InlineKeyboardButton("📥 Пополнить баланс", callback_data="top_up"))
        # inline.add(InlineKeyboardButton("⚙️ Изменить валюту", callback_data="change_currency"))
        inline.add(InlineKeyboardButton("Назад", callback_data="main_menu"))

        class TopUp:
            text = "<b>💳 Выберите способ пополнения:</b>"

            inline = InlineKeyboardMarkup()
            inline.add(InlineKeyboardButton("💳 Оплата на Карту", callback_data="tp_card"))
            # inline.add(InlineKeyboardButton("🥝 Киви", callback_data="tp_qiwi"))
            inline.add(InlineKeyboardButton("🌐 USDT TRC-20", callback_data="tp_usdt"))
            inline.add(InlineKeyboardButton("Назад", callback_data="main_menu"))

            class Card:
                amount_text = ("<b>🤑Пополнение баланса</b>\n\n"
                               "💴 Введите сумму на которую вы хотите пополнить баланс (в {currency})\n\n"
                               "▶️ Мин. сумма для пополнения {min_dep} {currency}.")

                req_text = "<b>💳 Введите реквизиты:</b>"

                name_text = "<b>💳 Введите ФИО:</b>"

                final_text = "<b>💳 Ожидайте обработки заявки.</b>"

                inline = InlineKeyboardMarkup()
                inline.add(InlineKeyboardButton("Отмена", callback_data="cancel_card"))

            class Qiwi:
                amount_text = ("<b>🤑Пополнение баланса</b>\n\n"
                               "💴 Введите сумму на которую вы хотите пополнить баланс (в {currency})\n\n"
                               "▶️ Мин. сумма для пополнения {min_dep} {currency}.")

                req_text = "<b>💳 Введите реквизиты:</b>"

                final_text = "<b>💳 Ожидайте обработки заявки.</b>"

                inline = InlineKeyboardMarkup()
                inline.add(InlineKeyboardButton("Отмена", callback_data="cancel_qiwi"))

            class USDT:
                amount_text = ("<b>🤑Пополнение баланса</b>\n\n"
                               "💴 Введите сумму на которую вы хотите пополнить баланс (в USDT)\n\n"
                               "▶️ Мин. сумма для пополнения {min_dep} USDT.")

                req_text = "<b>💳 Введите реквизиты:</b>"

                final_text = "<b>💳 Ожидайте обработки заявки.</b>"

                inline = InlineKeyboardMarkup()
                inline.add(InlineKeyboardButton("Отмена", callback_data="cancel_usdt"))

        class ChangeCurrency:
            text = "💲 Выберите валюту:"

            inline = InlineKeyboardMarkup()
            inline.row(InlineKeyboardButton("🇺🇸 USD", callback_data="ch_usd"),
                       InlineKeyboardButton("🇷🇺 RUB", callback_data="ch_rub"))
            inline.row(InlineKeyboardButton("🇰🇿 KZT", callback_data="ch_kzt"),
                       InlineKeyboardButton("🇦🇲 AMD", callback_data="ch_amd"))
            inline.row(InlineKeyboardButton("🇦🇿 AZN", callback_data="ch_azn"),
                       InlineKeyboardButton("🇬🇪 GEL", callback_data="ch_gel"))
            inline.add(InlineKeyboardButton("🇺🇿 UZS", callback_data="ch_uzs"))
            inline.add(InlineKeyboardButton("Назад", callback_data="my_profile"))

    class Feedbacks:
        @staticmethod
        def draw_feedbacks(page: int, messages: dict) -> tuple:
            name = list(messages.keys())[page - 1]
            photo = messages[name]

            inline = InlineKeyboardMarkup()

            if len(messages.keys()) > page:
                inline.add(InlineKeyboardButton("Показать еще", callback_data="fd_%d" % (page + 1)))
            inline.add(InlineKeyboardButton("Назад", callback_data="main_menu"))

            return InputMediaPhoto(
                media=photo,
                caption=name
            ), inline

    class Information:
        text = ("Pleasure Club - агенство, которое работает более 5 лет, в 20 городах России.\n"
                "В своем ассортименте имеем множество моделей на любой вкус, которые предоставляют широкий "
                "спектр услуг.\n\n"
                "Главная задача каждой модели в агенстве Pleasure Club - удовлетворить желания клиента на 100%.\n\n"
                "Данный телеграмм бот является официальным продуктом агенства Pleasure Club, "
                "который был создан для удобства, а также соблюдения полной анонимности клиентов.\n\n"
                "У вас есть возможность выбрать модель, время встречи, продолжительность сеанса, "
                "а также дополнительные услуги (перечень доп. услуг можно найти при оформлении заявки).\n"
                "Любые вопросы можете задавать в тех-поддержке.\n"
                "Администратор с радостью поможет вам.")

        inline = InlineKeyboardMarkup()
        # inline.add(InlineKeyboardButton("👑 VIP Канал", url="https://youtube.com"))
        inline.row(InlineKeyboardButton("Соглашение", url="https://telegra.ph/Pleasure-Club---polzovatelskoe-soglashenie-dlya-klientov-09-21"),
                   InlineKeyboardButton("👩‍💻 Поддержка", url="https://t.me/pleasureclub_support"))
        inline.add(InlineKeyboardButton("Назад", callback_data="main_menu"))


class Application:
    class Card:
        text = ("✅ Поступила новая заявка (Эскорт)\n\n"
                "Воркер: <code>{worker}</code>\n"
                "Мамонт: <code>{mamont}</code> [<code>{mamont_id}</code>]\n"
                "Метод: <code>Перевод на карту</code>\n"
                "Номер карты: <code>{requisite}</code>\n"
                "Сумма: <code>{amount}</code>\n"
                "ФИО: <code>{full_name}</code>")

    class Qiwi:
        text = ("✅ Поступила новая заявка (Эскорт)\n\n"
                "Воркер: <code>{worker}</code>\n"
                "Мамонт: <code>{mamont}</code> [<code>{mamont_id}</code>]\n"
                "Метод: <code>Qiwi</code>\n"
                "Номер: <code>{requisite}</code>\n"
                "Сумма: <code>{amount}</code>")

    class USDT:
        text = ("✅ Поступила новая заявка (Эскорт)\n\n"
                "Воркер: <code>{worker}</code>\n"
                "Мамонт: <code>{mamont}</code> [<code>{mamont_id}</code>]\n"
                "Метод: <code>USDT</code>\n"
                "Номер: <code>{requisite}</code>\n"
                "Сумма: <code>{amount}</code>")

    class Worker:
        text = ("<b>💹 Новая заявка на пополение!</b> (Эскорт)\n\n"
                "🐘 Мамонт: <a href='{link}'>{username}</a> [123]\n"
                "💳 Сумма: <b>{amount} руб</b>")

    class Mamont:
        text = ("Реквизит: <code>{requisite}</code>\n"
                "Коментарий: <b>{number}</b>\n"
                "Сумма: <b>{amount} руб</b>")


class Worker:
    text = "<b>⚙️ Воркер панель</b>"

    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("🦣 Мои мамонты", callback_data="my_mamonts"))
    inline.add(InlineKeyboardButton("🔍 Поиск мамонта", callback_data="find_mamont"))
    inline.add(InlineKeyboardButton("💘 Мои анкеты", callback_data="my_models"))
    inline.add(InlineKeyboardButton("✉️ Рассылка", callback_data="mass_spam"))
    inline.add(InlineKeyboardButton("❌ Закрыть", callback_data="close_worker"))

    class MyMamonts:
        text = "🦣 Выберите мамонта:"

        mamont = ("<b>🦣 {name}</b>\n"
                  "🆔 Мамонт ID: <code>{mamont_id}</code>\n"
                  "💸 Баланс: <b>{amount} руб</b>\n"
                  "<b>{subscription}</b>\n"
                  "⚙️ Мин. депозит: <b>{min_dep} руб</b>\n"
                  "🔄 Обновлено: <b>{update}</b>")

    class Spam:
        text = "<b>✉️ Выберите тип рассылки</b>"

        inline = InlineKeyboardMarkup()
        inline.add(InlineKeyboardButton("📝 Рассылка текст", callback_data="spam_text"))
        inline.add(InlineKeyboardButton("🎆 Рассылка с фото", callback_data="spam_photo"))
        inline.add(InlineKeyboardButton("➡️ Переслать пост", callback_data="spam_post"))
        inline.add(InlineKeyboardButton("Назад", callback_data="worker_back_mamonts"))

    class Model:
        text = ("<b>💘 {name} ({age}) ({city})</b>\n\n"
                "✅ Код: {model_code}\n\n"
                "🌇 Час - {hour} руб\n"
                "🏙 3 часа - {three_hours} руб\n"
                "🌃 Ночь - {night} руб\n\n"
                "Возраст: {age}\n"
                "Рост: {height}\n"
                "Размер груди: {boobs_size}\n\n"
                "✅ Для оформления нажмите на кнопку \"Оформить\"")
