import telebot
import logging

from database import create_customer_profile, get_customer_profile_instance, get_customer_profiles_all, \
    get_customer_profiles_is_banned, change_customer_profile_balance_field, change_customer_profile_is_banned_field

from pyqiwip2p import QiwiP2P
from telebot import types
from configparser import ConfigParser


# создание logger для уровней DEBUG и INFO
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

debug_info_logger = logging.getLogger('debug_info')
debug_info_logger.setLevel(logging.DEBUG)
handler1 = logging.FileHandler('debug_info.log', mode='a')
handler1.setFormatter(formatter)
debug_info_logger.addHandler(handler1)

# создание logger для уровней WARNING, ERROR и CRITICAL
warning_error_critical_logger = logging.getLogger('warning_error_critical')
warning_error_critical_logger.setLevel(logging.WARNING)
handler2 = logging.FileHandler('warning_error_critical.log', mode='a')
handler2.setFormatter(formatter)
warning_error_critical_logger.addHandler(handler2)

# данные из config.ini для доступа к telegram боту и admin панели
try:
    parser = ConfigParser()
    parser.read('config.ini')
    params = parser.items('telegram')
    my_bot = telebot.TeleBot(params[0][1])
    PASSWORD_FOR_ADMIN_PANEL = params[1][1]

    debug_info_logger.info('параметры для доступа к telegram боту успешно прочитаны')
except:
    warning_error_critical_logger.error('ошибка при чтении параметров из config.ini')

# данные для доступа к Qiwi
QIWI_PRIVATE_KEY = 'your_piv_key'


# функция для отлавливания команды 'start'
@my_bot.message_handler(commands=['start'])
def start_func(message):
    debug_info_logger.debug('функция start_func() начала работу')

    this_customer = get_customer_profile_instance(message.from_user.id)
    if this_customer == None:
        try:
            this_customer = create_customer_profile(message.from_user.id)

            debug_info_logger.info('новый экземпляр customer_profile успешно создан')
        except:
            warning_error_critical_logger.critical('ошибка при создании customer_profile')

    banned_users = get_customer_profiles_is_banned()

    if this_customer[1] in banned_users:
        my_bot.send_message(chat_id=message.chat.id,
                            text=f"{message.from_user.first_name} - вы заблокированы! Извините")
    else:
        my_bot.send_message(chat_id=message.chat.id, text=f"Привет, {message.from_user.first_name}!")

        inline_set = types.InlineKeyboardMarkup()
        top_up_qiwi_account_button = types.InlineKeyboardButton(text="Пополнить баланс", callback_data="0")
        inline_set.add(top_up_qiwi_account_button)

        my_bot.send_message(chat_id=message.chat.id,
                            text="Я - бот для пополнения баланса.\nНажмите на кнопку, чтобы пополнить баланc",
                            reply_markup=inline_set)

    debug_info_logger.debug('функция start_func() завершила работу')


# функция для запроса суммы для увеличения баланса
def make_qiwi_payment(message):
    debug_info_logger.debug('функция make_qiwi_payment() начала работу')

    new_message = my_bot.send_message(chat_id=message.chat.id,
                                      text="Введите сумму, на которую вы хотите пополнить баланс")

    my_bot.register_next_step_handler(new_message, make_qiwi_payment_2)

    debug_info_logger.debug('функция make_qiwi_payment() завершила работу')


# функция для формирования счета и предоставления кнопок: для оплаты счета и проверки его статуса
def make_qiwi_payment_2(message):
    debug_info_logger.debug('функция make_qiwi_payment_2() начала работу')

    try:
        p2p = QiwiP2P(auth_key=QIWI_PRIVATE_KEY)
        new_bill = p2p.bill(amount=float(message.text), lifetime=5)

        inline_set = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Оплатить счет', url=new_bill.pay_url)
        button2 = types.InlineKeyboardButton('Проверка статуса платежа', callback_data="5")
        inline_set.add(button1, button2)

        my_bot.send_message(chat_id=message.chat.id,
                            text="Счет на введенную сумму успешно создан",
                            reply_markup=inline_set)

        debug_info_logger.info('создание счета для оплаты на Qiwi прошло успешно')
    except:
        warning_error_critical_logger.error('ошибка при создании счета для оплаты на Qiwi')

    debug_info_logger.debug('функция make_qiwi_payment_2() завершила работу')


# проверяем статус счета p2p.check(bill_id=new_bill.bill_id).status и в зависимости от полученного значения:
# - либо прибавляем это значение к балансу пользователя в базе данных,
# - либо ввыводим сообщение о том, что платеж не прошел.
def check_status_func(message):
    debug_info_logger.debug('функция check_status_func() начала работу')
    debug_info_logger.warning('это недоделанная функция check_status_func() завершила работу')
    debug_info_logger.debug('функция check_status_func() завершила работу')
    # не смог реализовать, так как не смог разобраться с Qiwi)


# запрос пароля для предоставления доступа к admin panel
@my_bot.message_handler(commands=['admin'])
def login_to_admin_panel_func(message):
    debug_info_logger.debug('функция login_to_admin_panel_func() начала работу')

    my_message = my_bot.send_message(chat_id=message.chat.id, text="Пожалуйста, введите пароль")
    my_bot.register_next_step_handler(my_message, show_admin_panel_func)

    debug_info_logger.debug('функция login_to_admin_panel_func() завершила работу')


# проверка валидности пароля для доступа к admin panel и предоставления кнопок с действиями для администратора
def show_admin_panel_func(message):
    debug_info_logger.debug('функция show_admin_panel_func() начала работу')

    if message.text == PASSWORD_FOR_ADMIN_PANEL:
        debug_info_logger.info('успешная попытка доступа к admin panel - доступ разрешен')

        inline_set = types.InlineKeyboardMarkup(row_width=1)
        button1 = types.InlineKeyboardButton('Выгрузка пользователей', callback_data="1")
        button2 = types.InlineKeyboardButton('Выгрузка логов', callback_data="2")
        button3 = types.InlineKeyboardButton('Изменение баланса', callback_data="3")
        button4 = types.InlineKeyboardButton('Блокировка пользователя', callback_data="4")
        inline_set.add(button1, button2, button3, button4)

        my_bot.send_message(message.chat.id, f"{message.from_user.first_name}, пожалуйста, выберите действие "
                                             f"из нижеперечисленных", reply_markup=inline_set)
    else:
        debug_info_logger.info('неуспешная попытка доступа к admin panel - доступ запрещен')

        my_message = my_bot.send_message(chat_id=message.chat.id, text="Пароль введен неправильно!\n"
                                                                       "Попробуйте еще раз")
        my_bot.register_next_step_handler(my_message, show_admin_panel_func)

    debug_info_logger.debug('функция show_admin_panel_func() завершила работу')


# выгрузка списка пользователей с их балансами
def download_users_list_func(message):
    debug_info_logger.debug('функция download_users_list_func() начала работу')

    all_customer_profiles = get_customer_profiles_all()

    file = open("users_list.txt", "w")
    for customer in all_customer_profiles:
        file.write(f"Баланс пользователя с id = {customer[1]} равен {customer[2]}\n")
    file.close()

    try:
        my_bot.send_document(chat_id=message.chat.id,
                         document=open('users_list.txt', 'rb'),
                         caption='Это файл со списком пользователей и их балансами')

        debug_info_logger.info('файл со списком пользователей успешно отправлен')
    except:
        warning_error_critical_logger.error('ошибка при отправлении файла со списком пользователей')

    debug_info_logger.debug('функция download_users_list_func() завершила работу')


# выгрузка файлов с логами
def download_logs_func(message):
    debug_info_logger.debug('функция download_logs_func() начала работу')

    try:
        my_bot.send_document(chat_id=message.chat.id,
                         document=open('debug_info.log', 'rb'),
                         caption='Это файл с логами для уровней DEBUG и INFO')

        debug_info_logger.info('файл со списком логов со статусами DEBUG и INFO успешно отправлен')
    except:
        warning_error_critical_logger.error('ошибка при отправлении файла со списком логов со статусами DEBUG и INFO')
    try:
        my_bot.send_document(chat_id=message.chat.id,
                         document=open('warning_error_critical.log', 'rb'),
                         caption='Это файл с логами для уровней WARNING, ERROR и CRITICAL')

        debug_info_logger.info('файл со списком логов со статусами WARNING, ERROR и CRITICAL успешно отправлен')
    except:
        warning_error_critical_logger.error('ошибка при отправлении файла со списком логов '
                                            'со статусами WARNING, ERROR и CRITICAL')

    debug_info_logger.debug('функция download_logs_func() завершила работу')


# запрос id пользователя для последующего изменения баланса
def change_balance_func(message):
    debug_info_logger.debug('функция change_balance_func() начала работу')

    new_message = my_bot.send_message(chat_id=message.chat.id, text="Пожалуйста, введите id пользователя, "
                                                                    "которому необходимо поменять баланс")
    my_bot.register_next_step_handler(new_message, change_balance_func_2)

    debug_info_logger.debug('функция change_balance_func() завершила работу')


# запрос нового значения баланса для последующего изменения баланса
def change_balance_func_2(message):
    debug_info_logger.debug('функция change_balance_func_2() начала работу')

    global telegram_id
    telegram_id = message.text

    new_message = my_bot.send_message(chat_id=message.chat.id, text="Пожалуйста, введите значение баланса, "
                                                                    "на которое необходимо заменить (в формате 0.0)")
    my_bot.register_next_step_handler(new_message, change_balance_func_3)

    debug_info_logger.debug('функция change_balance_func_2() завершила работу')


# изменение баланса для пользователя
def change_balance_func_3(message):
    debug_info_logger.debug('функция change_balance_func_3() начала работу')

    customer_profile_instance = get_customer_profile_instance(telegram_id)
    try:
        updated_customer_profile = change_customer_profile_balance_field(float(message.text), int(telegram_id))

        debug_info_logger.info('успешное обновление баланса для пользователя')
    except:
        warning_error_critical_logger.error('ошибка при обновлении баланса для пользователя')

    my_bot.send_message(chat_id=message.chat.id, text=f"Изменен баланс пользователя с "
                                                      f"id = {customer_profile_instance[1]}.\n"
                                                      f"Старое значение: {customer_profile_instance[2]}\n"
                                                      f"Новое значение: {updated_customer_profile[2]}")

    debug_info_logger.debug('функция change_balance_func_3() завершила работу')


# запрос id пользователя для последующей блокировки
def block_user_func(message):
    debug_info_logger.debug('функция block_user_func() начала работу')

    new_message = my_bot.send_message(chat_id=message.chat.id, text="Пожалуйста, введите id пользователя, "
                                                                    "которого необходимо заблокировать")
    my_bot.register_next_step_handler(new_message, block_user_func_2)

    debug_info_logger.debug('функция block_user_func() завершила работу')


# блокировка пользователя
def block_user_func_2(message):
    debug_info_logger.debug('функция block_user_func_2() начала работу')

    try:
        change_customer_profile_is_banned_field(int(message.text))

        debug_info_logger.info('успешная блокировка пользователя')
    except:
        warning_error_critical_logger.error('ошибка при блокировке пользователя')

    my_bot.send_message(chat_id=message.chat.id, text=f"Заблокирован пользователь с id = {message.text}")

    debug_info_logger.debug('функция block_user_func_2() завершила работу')


# функция для callback вызовов
@my_bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message:
        if call.data == "0":
            make_qiwi_payment(call.message)
        if call.data == "1":
            download_users_list_func(call.message)
        if call.data == "2":
            download_logs_func(call.message)
        if call.data == "3":
            change_balance_func(call.message)
        if call.data == "4":
            block_user_func(call.message)
        if call.data == "5":
            check_status_func(call.message)


my_bot.polling(none_stop=True)
