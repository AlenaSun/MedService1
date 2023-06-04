import telebot
import webbrowser
from telebot import types
import datetime
import threading
import re
from config import TOKEN
from database import create_connection, close_connection, create_table, insert_user_info
from mail import send_emails, send_emails_cancel

bot = telebot.TeleBot(TOKEN)

user_data = {}  # Словарь для хранения данных

db_lock = threading.Lock()

@bot.message_handler(commands=['start'])
def main_key(message):
    bot.send_message(message.chat.id, f'{message.from_user.username}, добро пожаловать в стоматологическую клинику "Медсеривс"!',reply_markup=main())
def main():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Записаться на приём')
    markup.row(btn1)
    btn2 = types.KeyboardButton("Мои записи")
    btn6 = types.KeyboardButton("Информация о врачах")
    markup.row(btn2, btn6)
    btn3 = types.KeyboardButton("Адреса клиник")
    btn4 = types.KeyboardButton("Контактные данные")
    btn5 = types.KeyboardButton("Посетить веб-сайт")
    markup.row(btn3, btn4, btn5)
    return markup

@bot.message_handler(func=lambda message: True)
def on_click(message):
    if message.text == "Посетить веб-сайт":
        webbrowser.open('http://medservis72.ru')
        bot.send_message(message.chat.id, "Страница была успешно открыта.✅\n\nСсылка на наш сайт:\n\nhttp://medservis72.ru",
                         parse_mode='html')
    elif message.text == "Адреса клиник":
        markup2 = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('г.Тюмень', callback_data='tumen_adress')
        btn2 = types.InlineKeyboardButton('г.Когалым', callback_data='kogalym_adress')
        btn3 = types.InlineKeyboardButton('г.Урай', callback_data='uray_adress')
        markup2.row(btn1, btn2, btn3)
        bot.reply_to(message, 'Выберите город, в котором Вы находитесь:', reply_markup=markup2)
    elif message.text == "Информация о врачах":
        bot.send_photo(message.chat.id, open('photo.jpg', 'rb'))
    elif message.text == "Контактные данные":
        markup3 = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('г.Тюмень', callback_data='text1')
        btn2 = types.InlineKeyboardButton('г.Когалым', callback_data='text2')
        btn3 = types.InlineKeyboardButton('г.Урай', callback_data='text3')
        markup3.row(btn1, btn2, btn3)
        bot.reply_to(message, 'Выберите город, для которого хотите получить информацию:', reply_markup=markup3)
    elif message.text == "Записаться на приём":
        bot.send_message(message.chat.id, "Для записи введите Ваше ФИО:", reply_markup=create_cancel_button())
        bot.register_next_step_handler(message, process_name_step)
    elif message.text == "Мои записи":
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('г.Тюмень', callback_data='tumen')
            btn2 = types.InlineKeyboardButton('г.Когалым', callback_data='kogalym')
            btn3 = types.InlineKeyboardButton('г.Урай', callback_data='uray')
            markup.row(btn1, btn2, btn3)
            bot.send_message(message.chat.id, 'Выберите город, в котором необходимо узнать предстоящие приёмы:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['tumen_adress', 'kogalym_adress', 'uray_adress'])
def handle_callback_query(call):
    if call.data == 'tumen_adress':
        tumen = f"Адрес в г.Тюмень:\n\n" \
                f"📍ул.Кремлевская, д.112, корп. 4\n"
        bot.send_message(call.message.chat.id, tumen)
        bot.send_location(call.message.chat.id, latitude=57.133480,longitude=65.472254)
    elif call.data == 'kogalym_adress':
        kogalum = f"Адрес в г.Когалым:\n\n" \
                f"📍ул.Нефтяников д.5\n"
        bot.send_message(call.message.chat.id, kogalum)
        bot.send_location(call.message.chat.id, latitude=62.244657,longitude=74.53215)
    elif call.data == 'uray_adress':
        uray = f"Адрес в г.Урай:\n\n" \
            f"📍м-он 1-А, дом 74\n"
        bot.send_message(call.message.chat.id, uray)
        bot.send_location(call.message.chat.id, latitude=60.123685, longitude=64.781072)

def check_callback_for_records(call):
        return call.data.startswith(('tumen', 'kogalym', 'uray', 'otmena', 'yes', 'no'))

@bot.callback_query_handler(func=check_callback_for_records)
def callback_inline(call):
    if call.message:
        if call.data in ['tumen', 'kogalym', 'uray']:
            data = get_user_info(call.data, call.message.chat.id)
            if data:
                current_date = datetime.datetime.now().date()  # Текущая дата
                upcoming_records = []  # Список предстоящих записей
                bot.send_message(call.message.chat.id, 'Предстоящие записи на прием к нам:')

                for row in data:
                    row_id, user_id, name, phone, email, date, time = row
                    record_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

                    if record_date >= current_date:
                        upcoming_records.append(row)

                if upcoming_records:
                    # Сортировка записей по возрастанию даты
                    upcoming_records.sort(key=lambda r: datetime.datetime.strptime(r[5], "%Y-%m-%d"))

                    for row in upcoming_records:
                        row_id, user_id, name, phone, email, date, time = row
                        formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
                        formatted_time = time[:5]  # Извлекаем только часы и минуты
                        message = f'👤Имя: {name}\n\n🗓️Дата приёма: {formatted_date}\n\n⌚Время приёма: {formatted_time}'

                        # Создаем инлайн кнопку для отмены записи
                        markup = types.InlineKeyboardMarkup()
                        cancel_button = types.InlineKeyboardButton(text="Отменить запись",callback_data=f'otmena_{call.data}_{row_id}')
                        markup.add(cancel_button)

                        bot.send_message(call.message.chat.id, message, reply_markup=markup)

                else:
                    bot.send_message(call.message.chat.id, 'У вас нет предстоящих записей в этом городе.')
            else:
                bot.send_message(call.message.chat.id, 'У вас нет записей в этом городе.')

        elif call.data.startswith('otmena'):
            _, city, row_id = call.data.split('_')

            # Создаем инлайн кнопки для подтверждения
            markup = types.InlineKeyboardMarkup()
            yes_button = types.InlineKeyboardButton(text="Да", callback_data=f'yes_{city}_{row_id}')
            no_button = types.InlineKeyboardButton(text="Нет", callback_data=f'no_{city}_{row_id}')
            markup.row(yes_button, no_button)

            # Удаляем сообщение с запросом на подтверждение отмены записи
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='Вы уверены, что хотите отменить запись?', reply_markup=markup)
        # Обработка нажатия на кнопку "Да"
        elif call.data.startswith('yes_'):
            _, city, row_id = call.data.split('_')
            user_data = get_user_info(city, call.message.chat.id)
            if user_data:
                name = user_data[0][2]
                phone = user_data[0][3]
                time = user_data[0][6]
                date = user_data[0][5]

            send_emails_cancel(name, phone, city, date, time)
            delete_user_info(city, int(row_id))
            bot.send_message(call.message.chat.id, 'Ваша запись была успешно отменена.\n\nМы рекомендуем планировать свое время заранее, чтобы быть уверенными в наличии свободных мест.\n\nС уважением,\nМедсервис ')



            # Удаляем сообщение с удаленной записью
            bot.delete_message(call.message.chat.id, call.message.message_id)

        # Обработка нажатия на кнопку "Нет"
        elif call.data.startswith('no_'):
            _, city, row_id = call.data.split('_')

            data = get_user_info(city, call.message.chat.id)
            if data:
                for row in data:
                    if row[0] == int(row_id):  # ищем строку с нужным row_id
                        row_id, user_id, name, phone, email, date, time = row
                        formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
                        formatted_time = time[:5]  # Извлекаем только часы и минуты
                        message = f'👤Имя: {name}\n\n🗓️Дата приёма: {formatted_date}\n\n⌚Время приёма: {formatted_time}'

                        # Создаем инлайн кнопку для отмены записи
                        markup = types.InlineKeyboardMarkup()
                        cancel_button = types.InlineKeyboardButton(text="Отменить запись",callback_data=f'otmena_{city}_{row_id}')
                        markup.add(cancel_button)

                        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                              text=f'Ваша запись была сохранена. Ждем Вас на приём!\n\n{message}',
                                              reply_markup=markup)
                        break


def get_user_info(city, user_id):
    conn, cursor = create_connection()
    cursor.execute(f"SELECT id, user_id, name, phone, email, date, time FROM users_info_{city} WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()
    close_connection(conn)
    return data

def delete_user_info(city, id):
    conn, cursor = create_connection()
    cursor.execute(f"DELETE FROM users_info_{city} WHERE id = ?", (id,))
    conn.commit()
    close_connection(conn)

def create_cancel_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_cancel = types.KeyboardButton('Отмена')
    markup.add(btn_cancel)
    return markup

def process_name_step(message):
    if message.text == 'Отмена':
        cancel_registration(message)
        return
    name = message.text
    name_pattern = r'^[a-zA-Zа-яА-ЯёЁ\s]+$'
    if re.match(name_pattern, name):
        user_data[message.from_user.id] = {'name': name}
        bot.send_message(message.chat.id, "Для записи введите Ваш номер телефона:", reply_markup=create_cancel_button())
        bot.register_next_step_handler(message, get_phone)
    else:
        bot.send_message(message.chat.id, "Некорректный ввод имени. Пожалуйста, введите корректное значение.")
        bot.register_next_step_handler(message, process_name_step)

def cancel_registration(message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        bot.send_message(message.chat.id, "Запись отменена. Ваши данные были удалены.", reply_markup=main())
    else:
        bot.send_message(message.chat.id, "Запись отменена. Ваши данные были удалены.", reply_markup=main())

def get_phone(message):
    if message.text == 'Отмена':
        cancel_registration(message)
        return

    phone = message.text
    # Проверка корректности номера телефона с помощью регулярного выражения
    phone_pattern = r'^\+?[1-9]\d{1,14}$'  # Пример паттерна для номера телефона
    if re.match(phone_pattern, phone):
        user_data[message.from_user.id]['phone'] = phone
        bot.send_message(message.chat.id, "Для записи введите Ваш адрес электронной почты:", reply_markup=create_cancel_button())
        bot.register_next_step_handler(message, get_email)
    else:
        bot.send_message(message.chat.id, "Некорректный номер телефона. Пожалуйста, введите корректный номер.")
        bot.register_next_step_handler(message, get_phone)

def get_email(message):
    if message.text == 'Отмена':
        cancel_registration(message)
        return
    email = message.text
    # Проверка корректности адреса электронной почты с помощью регулярного выражения
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Пример паттерна для адреса почты
    if re.match(email_pattern, email):
        user_data[message.from_user.id]['email'] = email
        bot.send_message(message.chat.id, "Выберите город, в котором Вы хотите записаться:", reply_markup=create_city_markup())
    else:
        bot.send_message(message.chat.id, "Некорректный адрес электронной почты. Пожалуйста, введите корректный адрес.")
        bot.register_next_step_handler(message, get_email)

def create_city_markup():
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('г.Тюмень', callback_data='city_tumen')
    btn2 = types.InlineKeyboardButton('г.Когалым', callback_data='city_kogalym')
    btn3 = types.InlineKeyboardButton('г.Урай', callback_data='city_uray')
    btn4 = types.InlineKeyboardButton('Отмена', callback_data='cancel_city')
    markup.row(btn1, btn2, btn3)
    markup.row(btn4)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_city')
def handle_cancel_appointment(call):
    user_id = call.from_user.id
    del user_data[user_id]['name']
    del user_data[user_id]['phone']
    del user_data[user_id]['email']
    bot.send_message(call.message.chat.id, "Запись отменена. Ваши данные были удалены.", reply_markup=main())
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('city_'))
def handle_city_callback(call):
    city = call.data.split('_')[1]
    user_id = call.from_user.id
    user_data[user_id]['city'] = city
    bot.send_message(call.message.chat.id, "Выберите тип записи:", reply_markup=create_type_markup())
    bot.delete_message(call.message.chat.id, call.message.message_id)

def create_type_markup():
    markup = types.InlineKeyboardMarkup()
    inspection_button = types.InlineKeyboardButton('Консультация/осмотр', callback_data='type_inspection')
    treatment_button = types.InlineKeyboardButton('Лечение', callback_data='type_treatment')
    cancel_button = types.InlineKeyboardButton('Отмена', callback_data='cancel_type')
    markup.row(inspection_button)
    markup.row(treatment_button)
    markup.row(cancel_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_type')
def handle_cancel_appointment(call):
    user_id = call.from_user.id
    del user_data[user_id]['name']
    del user_data[user_id]['phone']
    del user_data[user_id]['email']
    del user_data[user_id]['city']
    bot.send_message(call.message.chat.id, "Запись отменена. Ваши данные были удалены.", reply_markup=main())
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def handle_type_callback(call):
    type = call.data.split('_')[1]
    user_id = call.from_user.id
    user_data[user_id]['type'] = type
    date_message = "Выберите дату приёма:"
    bot.send_message(call.message.chat.id, date_message, reply_markup=create_date())
    bot.delete_message(call.message.chat.id, call.message.message_id)

def create_date():
    markup = types.InlineKeyboardMarkup()
    today = datetime.date.today()
    for i in range(7): # Добавляем кнопки для выбора даты на ближайшие 7 дней
        date = today + datetime.timedelta(days=i)
        callback_data = f"date_{date}"
        btn = types.InlineKeyboardButton(date.strftime("%d.%m.%Y"), callback_data=callback_data)
        markup.add(btn)
    cancel_button = types.InlineKeyboardButton("Отмена", callback_data="cancel_date")
    markup.add(cancel_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_date')
def handle_cancel_appointment(call):
    user_id = call.from_user.id
    del user_data[user_id]['name']
    del user_data[user_id]['phone']
    del user_data[user_id]['email']
    del user_data[user_id]['city']
    del user_data[user_id]['type']
    bot.send_message(call.message.chat.id, "Запись отменена. Ваши данные были удалены.", reply_markup=main())    # Дополнительный код для выполнения действий после отмены записи
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
def handle_date_callback(call):
    date = call.data.split('_')[1]
    user_id = call.from_user.id
    user_data[user_id]['date'] = date
    formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
    current_time = datetime.datetime.now().time()  # Получение текущего времени
    message = f"Выберите время приёма для записи на {formatted_date}:"
    bot.send_message(call.message.chat.id, message, reply_markup=create_time_markup(user_id, current_time))
    bot.delete_message(call.message.chat.id, call.message.message_id)

def create_time_markup(user_id, current_time):
    markup = types.InlineKeyboardMarkup()
    date = user_data[user_id]['date']
    city = user_data[user_id]['city']
    type = user_data[user_id]['type']

    time_range = None  # Инициализация переменной 'time_range'

    if type == 'inspection':  # Консультация/осмотр
        if city == 'kogalym':
            time_range = range(8, 10)
        elif city in ['tyumen', 'uray']:
            time_range = range(9, 11)
        minute_steps = [0, 15, 30, 45]
        col_num = 3
    else:  # Лечение
        if city in ['tyumen', 'kogalym']:
            time_range = range(11, 21)
        elif city == 'uray':
            time_range = range(10, 20)
        minute_steps = [0, 30]
        col_num = 2

    button_cols = [[] for _ in range(col_num)]
    for hour in time_range:
        for i, minutes in enumerate(minute_steps):
            time_i = datetime.time(hour, minutes)
            if datetime.date.today() == datetime.datetime.strptime(date, "%Y-%m-%d").date() and current_time >= time_i:
                continue  # Пропустить это временное окно, если оно раньше текущего времени
            callback_data_i = f"time_{time_i}"
            if check_availability(city, date, str(time_i)):  # Проверить доступность этого временного окна
                button_i = types.InlineKeyboardButton(time_i.strftime("%H:%M"), callback_data=callback_data_i)
                button_cols[i % col_num].append(button_i)

    for button_rows in zip(*button_cols):
        markup.row(*button_rows)

    back_button = types.InlineKeyboardButton("Назад", callback_data="back_to_date_selection")
    cancel_button = types.InlineKeyboardButton("Отмена", callback_data="cancel_time")
    markup.add(back_button)
    markup.add(cancel_button)
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'cancel_time')
def handle_cancel_appointment(call):
    user_id = call.from_user.id
    # Удалите данные пользователя, связанные с записью
    del user_data[user_id]['name']
    del user_data[user_id]['phone']
    del user_data[user_id]['email']
    del user_data[user_id]['city']
    del user_data[user_id]['date']
    bot.send_message(call.message.chat.id, "Запись отменена. Ваши данные были удалены.", reply_markup=main())    # Дополнительный код для выполнения действий после отмены записи
    bot.delete_message(call.message.chat.id, call.message.message_id)

def check_availability(city, date, time):
    conn, cursor = create_connection()
    cursor.execute(f"SELECT * FROM users_info_{city} WHERE date = ? AND time = ?", (date, time))
    rows = cursor.fetchall()
    close_connection(conn)
    return len(rows) == 0  # Если нет записей с указанной датой и временем, вернуть True

@bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
def handle_time_callback(call):
    if call.data == 'back_to_date_selection':
        # Обрабатываем нажатие кнопки "Назад" для возврата к выбору даты
        bot.send_message(call.message.chat.id, "Выберите дату приёма:", reply_markup=create_date())
        bot.delete_message(call.message.chat.id, call.message.message_id)
    else:
        time = call.data.split('_')[1]
        user_id = call.from_user.id
        user_data[user_id]['time'] = time
        date = user_data[user_id]['date']

    name = user_data[user_id]['name']
    phone = user_data[user_id]['phone']
    email = user_data[user_id]['email']
    date = user_data[user_id]['date']
    city = user_data[user_id]['city']

    with db_lock:
        try:
            if check_availability(city, date, time):
                insert_user_info(city, user_id, name, phone, email, date, time)
                datetime_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
                date = user_data[user_id]['date']
                formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
                formatted_time = time[:5]  # Извлекаем только часы и минуты
                datetime_str = f"{formatted_date} в {formatted_time}"

                # Отправка сообщения для подтверждения
                confirmation_message = f"Ваши введенные данные были приняты!\n\nИнформация о записи:\n\n" \
                                       f"Дата и время: {datetime_str}\n" \
                                       f"Имя: {name}\n" \
                                       f"Телефон: {phone}\n" \
                                       f"Email: {email}\n\n" \
                                       f"Проверьте правильность введенных данных.Данные введены верно?"
                markup = types.InlineKeyboardMarkup()
                yes_button = types.InlineKeyboardButton('Да', callback_data='confirm')
                no_button = types.InlineKeyboardButton('Нет', callback_data='cancel')
                markup.row(yes_button, no_button)

                bot.send_message(call.message.chat.id, confirmation_message, reply_markup=markup)
                bot.delete_message(call.message.chat.id, call.message.message_id)
            else:
                bot.send_message(call.message.chat.id, "Данное время/дата уже занято. Выберите другое время или дату.")
        except Exception as e:
            print(f"Произошла ошибка при записи в базу данных: {e}")
            bot.send_message(call.message.chat.id, "Произошла ошибка при записи в базу данных.")
            bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_date_selection')
def handle_back_to_date_selection(call):
    user_id = call.from_user.id
    del user_data[user_id]['date']  # Удаляем выбранную дату из данных пользователя
    bot.send_message(call.message.chat.id, "Выберите дату приёма:", reply_markup=create_date())
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'confirm')
def handle_confirmation(call):
    user_id = call.from_user.id

    name = user_data[user_id]['name']
    phone = user_data[user_id]['phone']
    email = user_data[user_id]['email']
    city = user_data[user_id]['city']
    type = user_data[user_id]['type']
    date = user_data[user_id]['date']
    time = user_data[user_id]['time']

    address = ""
    if city == 'tumen':
        address = "ул.Кремлевская, д.112, корп. 4"
        recipient = 'alenastud23@mail.ru'
    elif city == 'kogalym':
        address = "ул. Нефтяников д.5"
        recipient = 'alenastud23@mail.ru'
    elif city == 'uray':
        address = "м-он 1-А, дом 74"
        recipient = 'alenastud23@mail.ru'
    formatted_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
    formatted_time = time[:5]  # Извлекаем только часы и минуты
    datetime_str = f"{formatted_date} в {formatted_time}"
    if type == 'inspection':
        type1 = "консультация/осмотр"
        type_emoji = '🔍'
    else:
        type1 = "лечение"
        type_emoji = '🦷'
    confirmation_message = f"Ваша запись на прием успешно подтверждена!\n\n" \
                           f"{type_emoji}Тип записи: {type1}\n" \
                           f"📅Дата и время: {datetime_str}\n" \
                           f"📍Адрес: {address}\n\n" \
                            f"Не забудьте взять с собой полис и паспорт."

    bot.send_message(call.message.chat.id, confirmation_message, reply_markup=main())
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_emails(name, phone, email, city, type, date, time)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def handle_cancel(call):
    user_id = call.from_user.id
    if user_id in user_data:
        # Получение данных пользователя
        date = user_data[user_id]['date']
        time = user_data[user_id]['time']
        city = user_data[user_id]['city']

        # Удалить запись из базы данных
        conn, cursor = create_connection()
        cursor.execute(f"DELETE FROM users_info_{city} WHERE user_id = ? AND date = ? AND time = ?", (user_id, date, time))
        bot.send_message(call.message.chat.id, "Ваша запись была успешно отменена. Для повторной записи повторите попытку.", reply_markup=main())
        conn.commit()
        close_connection(conn)
    else:
        bot.send_message(call.message.chat.id, "Ошибка: Данные пользователя не найдены.")
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == 'text1':
        confirmation_message = f"☎️Контактный телефон:\n\n" \
                           f"8(3452) 39-02-62\n" \
                           f"8(3452)44-09-47\n\n" \
                           f"✉️Электронная почта:\n\n" \
                            f"medservistmn@yandex.ru"

        bot.send_message(call.message.chat.id, confirmation_message, reply_markup=main())
    elif call.data == 'text2':
        confirmation_message = f"☎️Контактный телефон:\n\n" \
                               f"8 (34667) 55-300\n" \
                               f"8(34667) 55-196\n\n" \
                               f"✉️Электронная почта:\n\n" \
                               f"medservistmn@yandex.ru"
        bot.send_message(call.message.chat.id, confirmation_message, reply_markup=main())
    elif call.data == 'text3':
        confirmation_message = f"☎️Контактный телефон:\n\n" \
                               f"8 (34676)3-16-12\n\n" \
                               f"✉️Электронная почта:\n\n" \
                               f"medservistmn@yandex.ru"
        bot.send_message(call.message.chat.id, confirmation_message, reply_markup=main())

bot.polling(none_stop=True)
