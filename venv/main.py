import telebot
from config import token
import db

telebot.apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(token)  # be sure to indicate your token in config.py
user_dict = {}  # here will be stored all current users


class User:
	"""
	Class stores information about user.
	"""
	def __init__(self, name):
		self.name = name
		self.orders = []  # temporarily stores orders in varius steps
		self.step = 'start'  # indicates current user step
		self.message = None  # stores default message object to pass it to some steps


for chat_id in db.chat_ids:  # sends message to all users who added the bot
	bot.send_message(chat_id, 'Бот был обновлён. Для начала пользования напишите /start')


@bot.message_handler(commands=['start', 'Выход'])
def start_message(message):
	if message.chat.id not in db.chat_ids:
		db.add_chat_id(message.chat.id)
	user = User('guest')
	user_dict[message.chat.id] = user
	keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
	key_auth = telebot.types.InlineKeyboardButton(text="Авторизация", callback_data='auth')
	key_reg = telebot.types.InlineKeyboardButton(text="Регистрация", callback_data='reg')
	keyboard.add(key_auth, key_reg)
	bot.send_message(message.from_user.id,
					 text='Добро пожаловать в наш онлайн-магазин! \n'
						  '\n'
						  'Пожалуйста авторизуйтесь, либо зарегестрируйте нового пользователя. \n'
						  '\n'
						  'У нас действует система скидок в зависимости от того, сколько вы уже потратили:\n'
						  '\n'
						  '- При покупках от 100: Скидка 1%\n'
						  '- При покупках от 1000: Скидка 5%\n'
						  '- При покупках от 5000: Скидка 10%\n'
						  '\n'
						  'Для возврата в главное меню, нажмите кнопку /Выход',
					 reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "reg")  # starts the process of registration
def registration(call: telebot.types.CallbackQuery):
	if user_dict[call.message.chat.id].step != 'start':  # this insures that user gets here in right moment
		return None
	markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	start_menu = telebot.types.KeyboardButton("/Выход")
	markup.add(start_menu)
	bot.send_message(chat_id=call.message.chat.id, text='Введите имя пользователя', reply_markup=markup)
	user_dict[call.message.chat.id].step = 'reg_name'
	bot.register_next_step_handler(call.message, get_name)


def get_name(message):
	if user_dict[message.chat.id].step != 'reg_name':
		return None
	if message.text.lower() == '/выход':  # returns user to start message
		start_message(message)
		return None
	name = message.text
	if not db.users.query("user == @name").empty:
		bot.send_message(message.from_user.id, 'Такой пользователь уже существует!')
		name = ''
		bot.register_next_step_handler(message, get_name)
	else:
		chat_id = message.chat.id
		user = User(name)
		user_dict[chat_id] = user
		bot.send_message(chat_id, 'Введите пароль')
		user_dict[message.chat.id].step = 'reg_pass'
		bot.register_next_step_handler(message, password_func)


def password_func(message):
	if user_dict[message.chat.id].step != 'reg_pass':
		return None
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	password = message.text
	user_id = db.users.sort_values(by='id', ascending=False).head(1).iloc[0]['id'] + 1
	new_user = {'id': user_id,
				'user': user_dict[message.chat.id].name,
				'password': password,
				'admin': 0,
				'discount': 0,
				'total': 0}
	db.add_user(new_user)
	user_dict[message.chat.id].step = 'user_menu'
	user_dict[message.chat.id].message = message
	user_menu(message, user_dict[message.chat.id].name)


@bot.callback_query_handler(func=lambda call: call.data == "auth")  # starts the process of authorization
def authorization(call: telebot.types.CallbackQuery):
	if user_dict[call.message.chat.id].step != 'start':
		return None
	markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	start_menu = telebot.types.KeyboardButton("/Выход")
	markup.add(start_menu)
	bot.send_message(chat_id=call.message.chat.id, text='Введите имя пользователя', reply_markup=markup)
	user_dict[call.message.chat.id].step = 'auth_name'
	bot.register_next_step_handler(call.message, auth_name)


def auth_name(message):
	if user_dict[message.chat.id].step != 'auth_name':
		return None
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	name = message.text
	if db.users.query("user == @name").empty:
		bot.send_message(message.from_user.id, 'Такого пользователя не существует!')
		name = ''
		bot.register_next_step_handler(message, auth_name)
	else:
		chat_id = message.chat.id
		user = User(name)
		user_dict[chat_id] = user
		bot.send_message(chat_id, 'Введите пароль')
		user_dict[message.chat.id].step = 'auth_pass'
		bot.register_next_step_handler(message, auth_pass)


def auth_pass(message):
	if user_dict[message.chat.id].step != 'auth_pass':
		return None
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	chat_id = message.chat.id
	password = message.text
	user = user_dict[chat_id].name
	if password != db.users.query("user == @user").iloc[0]['password']:
		bot.send_message(message.from_user.id, 'Пароль неверный!')
		user = ''
		bot.register_next_step_handler(message, auth_pass)
	else:
		if db.users.query("user == @user").iloc[0]['admin'] == 1:  # defines user rights
			user_dict[message.chat.id].step = 'admin_menu'
			user_dict[message.chat.id].message = message
			admin_menu(message, user)
		else:
			user_dict[message.chat.id].step = 'user_menu'
			user_dict[message.chat.id].message = message
			user_menu(message, user)


def user_menu(message, user):  # main menu for common users
	if user_dict[message.chat.id].step != 'user_menu':
		return None
	keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
	key_items = telebot.types.InlineKeyboardButton(text="Товары", callback_data='items')
	key_order = telebot.types.InlineKeyboardButton(text="Сделать заказ", callback_data='order')
	key_history = telebot.types.InlineKeyboardButton(text="История заказов", callback_data='history')
	keyboard.add(key_items, key_history,  key_order)
	discount = int(db.users.query("user == @user").iloc[0]['discount'] * 100)
	bot.send_message(message.from_user.id, f'Добро пожаловать, {user}! Ваша скидка {discount}%\n'
										   '\n'
										   'Для просмотра списка товаров нажмите кнопку "Товары"\n'
										   '\n'
										   'Если хотите посмотреть историю заказов, нажмите кнопку "История заказов"\n'
										   '\n'
										   'Если готовы сделать заказ, нажмите кнопку "Сделать заказ"',
					 reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "items")
def items_list(call: telebot.types.CallbackQuery):  # shows the item list
	if user_dict[call.message.chat.id].step != 'user_menu':
		return None
	bot.send_message(chat_id=call.message.chat.id, text='Список товаров (номер, название, цена):')
	response = ''
	data = db.items
	for index in data.index:
		item_id = data.loc[index]['id']
		item_title = data.loc[index]['item']
		price = data.loc[index]['price']
		response += f'{item_id} {item_title} {price}\n\n'
	bot.send_message(chat_id=call.message.chat.id, text=response)


@bot.callback_query_handler(func=lambda call: call.data == "order")
def order(call: telebot.types.CallbackQuery):  # starts the order procedure
	if user_dict[call.message.chat.id].step != 'user_menu':
		return None
	bot.send_message(chat_id=call.message.chat.id, text='Введите через пробел номер товара и его количество')
	user_dict[call.message.chat.id].step = 'order'
	bot.register_next_step_handler(call.message, conf)


@bot.callback_query_handler(func=lambda call: call.data == "history")
def history(call: telebot.types.CallbackQuery):  # shows the order history
	if user_dict[call.message.chat.id].step != 'user_menu':
		return None
	user = user_dict[call.message.chat.id].name
	user_id = db.users.query("user == @user").iloc[0]['id']
	if db.orders.query('user_id == @user_id').empty:
		bot.send_message(chat_id=call.message.chat.id, text='Вы ещё ничего не заказывали!')
	else:
		bot.send_message(chat_id=call.message.chat.id, text='Ваша история заказов (название, количество, цена):')
		h = db.orders.query('user_id == @user_id')
		for i in h.order_id.unique():
			a = h.query('order_id == @i & item_title != "prep"')
			if not a.empty:
				status = a['status'].unique()[0]
				status_dict = {'prep': 'Готовится', 'done': 'Доставлен'}
				order_status = status_dict[status]
				response = ''
				for index in a.index:
					item_title = a.loc[index]['item_title']
					amount = a.loc[index]['amount']
					price = a.loc[index]['total_price']
					response += f'{item_title} {amount} {price}\n\n'
				bot.send_message(chat_id=call.message.chat.id, text=f'Заказ номер {i}\n\n'+response+f'\n Статус: {order_status}')
		total = db.users.query("user == @user").iloc[0]['total']
		bot.send_message(chat_id=call.message.chat.id, text=f'Итого потрачено: {total}')


def conf(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'order':
		return None
	orders = user_dict[message.chat.id].orders
	user = user_dict[message.chat.id].name
	if orders == []:
		order_id = db.orders.sort_values(by='order_id', ascending=False).head(1).iloc[0]['order_id'] + 1
		user_id = db.users.query('user == @user').iloc[0]['id']
		db.add_order({"order_id": order_id,
					  'user_id': user_id,
					  "item_id": 0,
					  "item_title": 'prep',
					  "amount": 0,
					  "total_price": 0,
					  'status': 'prep'})  # reserves an order_id for the specific order
	else:
		order_id = orders[0]['order_id']  # this means that user adds another item to the current order
	try:
		item_id, amount = message.text.split()
	except:
		bot.send_message(message.from_user.id,
						 text='Заказ введён неправильно! Введите через пробел только номер товара и его количество')
		bot.register_next_step_handler(message, conf)
		return None
	try:
		item_id = abs(int(item_id))
		amount = abs(int(amount))
	except:
		bot.send_message(message.from_user.id,
						 text='Номер товара и количество должны быть целыми числами')
		bot.register_next_step_handler(message, conf)
		return None
	if db.items.query("id == @item_id").empty:
		bot.send_message(message.from_user.id, 'Такого товара не существует!')
		bot.register_next_step_handler(message, conf)
	elif db.items.query("id == @item_id").iloc[0]['amount'] - amount < 0:
		item_amount = db.items.query("id == @item_id").iloc[0]['amount']
		bot.send_message(message.from_user.id, f'К сожалению, на складе осталось только {item_amount} единиц данного товара. \n Пожалуйста укажите меньшее значение')
		bot.register_next_step_handler(message, conf)
	else:
		item_title = db.items.query("id == @item_id").iloc[0]['item']
		total_price = round(db.items.query("id == @item_id").iloc[0]['price'] * amount * (1 - db.users.query("user == @user").iloc[0]['discount']), 2)
		user_id = db.users.query("user == @user").iloc[0]['id']
		found = 0
		for order_dict in user_dict[message.chat.id].orders:  # checking whether the item was already ordered
			if order_dict['item_id'] == item_id and order_dict['order_id']:
				order_dict['amount'] += amount
				order_dict['total_price'] += total_price
				found = 1
		if found == 0:
			new_order = {"order_id": order_id,
						 'user_id': user_id,
						 "item_id": item_id,
						 "item_title": item_title,
						 "amount": amount,
						 "total_price": total_price,
						 'status': 'prep'}
			user_dict[message.chat.id].orders.append(new_order)
		keyboard = telebot.types.InlineKeyboardMarkup()
		key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='yes')
		keyboard.add(key_yes)
		key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='no')
		keyboard.add(key_no)
		user_dict[message.chat.id].step = 'order_conf'
		bot.send_message(message.from_user.id, text=f'В корзину добавлено {amount} {item_title}\n'
													'\n'
													'Хотите заказать что-то ещё?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'yes' or call.data == 'no')
def order_conf1(call):
	if user_dict[call.message.chat.id].step != 'order_conf':
		return None
	if call.data == "yes":
		bot.send_message(call.message.chat.id, 'Введите через пробел номер товара и его количество')
		user_dict[call.message.chat.id].step = 'order'
		bot.register_next_step_handler(call.message, conf)
	elif call.data == "no":
		user_dict[call.message.chat.id].step = 'order_conf1'
		order_conf2(call.message.chat.id)


def order_conf2(chat_id):
	if user_dict[chat_id].step != 'order_conf1':
		return None
	orders = user_dict[chat_id].orders
	keyboard = telebot.types.InlineKeyboardMarkup()
	key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='yes1')
	key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='no1')
	keyboard.add(key_yes, key_no)
	i = 0
	response = ''
	total = 0
	for position in orders:
		response += f'{i} {position["amount"]} {position["item_title"]} \n'
		total += position["total_price"]
		i += 1
	total = round(total, 2)
	bot.send_message(chat_id, text='Вы заказали:\n'
										   '\n'
										   f'{response}\n'
										   '\n'
										   f'Итоговая цена - {total} \n'
										   '\n'
										   'Хотите убрать какую-то позицию?\n', reply_markup=keyboard)
	user_dict[chat_id].step = 'order_conf2'


@bot.callback_query_handler(func=lambda call: call.data == 'yes1' or call.data == 'no1')
def order_conf3(call):
	if user_dict[call.message.chat.id].step != 'order_conf2':
		return None
	if call.data == "yes1":
		bot.send_message(call.message.chat.id, 'Введите номер позиции которую хотите убрать.\n'
											   '\n'
											   'Если вдруг передумали, введите "-1"')
		user_dict[call.message.chat.id].step = 'delete'
		bot.register_next_step_handler(call.message, delete_position)
	elif call.data == "no1":
		user_dict[call.message.chat.id].step = 'done'
		order_done(call.message.chat.id)


def delete_position(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'delete':
		return None
	orders = user_dict[message.chat.id].orders
	if orders == []:
		user_dict[message.chat.id].step = 'user_menu'
		bot.send_message(message.from_user.id, 'Ваша корзина пуста!')
		return None
	user = user_dict[message.chat.id].name
	try:
		i = int(message.text)
	except:
		bot.send_message(message.from_user.id, 'Пожалуйста, введите одно число!')
		bot.register_next_step_handler(message, delete_position)
		return None
	if i == -1:
		user_dict[message.chat.id].step = 'done'
		order_done(message.from_user.id)
	else:
		try:
			deleted = user_dict[message.chat.id].orders.pop(i)
			bot.send_message(message.from_user.id, f'Позиция {deleted["amount"]} {deleted["item_title"]} удалена')
			if user_dict[message.chat.id].orders != []:
				user_dict[message.chat.id].step = 'order_conf1'
				order_conf2(message.from_user.id)
			else:
				user_dict[message.chat.id].step = 'user_menu'
				bot.send_message(message.from_user.id, 'Ваша корзина пуста!')
				user_menu(user_dict[message.chat.id].message, user)
		except:
			bot.send_message(message.from_user.id, 'Такой позиции нет в заказе! Пожалуйста, введите номер позиции из списка выше')
			bot.register_next_step_handler(message, delete_position)
			return None


def order_done(chat_id):
	if user_dict[chat_id].step != 'done':
		return None
	orders = user_dict[chat_id].orders
	user = user_dict[chat_id].name
	total = 0
	for position in orders:
		total += position['total_price']
		db.add_order(position)
	total = round(total, 2)
	db.update_total(user, total)
	db.grant_discount(user)  # checks whether the user deserves a discount
	user_dict[chat_id].orders = []
	user_dict[chat_id].step = 'user_menu'
	bot.send_message(chat_id,
					 'Заказ успешно оформлен!')
	user_menu(user_dict[chat_id].message, user)


def admin_menu(message, user):  # the administrator main menu
	if user_dict[message.chat.id].step != 'admin_menu':
		return None
	keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
	key_items = telebot.types.InlineKeyboardButton(text="Склад", callback_data='storage')
	key_order = telebot.types.InlineKeyboardButton(text="Заказы", callback_data='orders')
	key_shipment = telebot.types.InlineKeyboardButton(text="Закупки", callback_data='shipment')
	key_delivered = telebot.types.InlineKeyboardButton(text="Доставка", callback_data='delivery')
	keyboard.add(key_items, key_order, key_shipment, key_delivered)
	bot.send_message(message.from_user.id, f'Здравствуйте, {user}!\n'
										   '\n'
										   'Для просмотра товаров на складе нажмите кнопку "Склад"\n'
										   '\n'
										   'Если хотите посмотреть активные заказы, нажмите кнопку "Заказы"\n'
										   '\n'
										   'Чтобы совершить закупку товаров, нажмите кнопку "Закупки"\n'
										   '\n'
										   'Для просмотра товаров ожидающих принятия на склад, нажмите кнопку "Доставка"',
					 reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "storage")
def storage(call: telebot.types.CallbackQuery):  # shows the item list
	if user_dict[call.message.chat.id].step != 'admin_menu':
		return None
	bot.send_message(chat_id=call.message.chat.id, text='Товары на складе (номер, название, количество):')
	response = ''
	data = db.items
	for index in data.index:
		item_id = data.loc[index]['id']
		item_title = data.loc[index]['item']
		amount = data.loc[index]['amount']
		response += f'{item_id} {item_title} {amount}\n\n'
	bot.send_message(chat_id=call.message.chat.id, text=response)


@bot.callback_query_handler(func=lambda call: call.data == "orders")
def orders_func(call: telebot.types.CallbackQuery):  # starts the process of order confirmation
	if user_dict[call.message.chat.id].step != 'admin_menu':
		return None
	if db.orders.query('item_title != "prep" & status == "prep"').empty:
		bot.send_message(chat_id=call.message.chat.id, text='Активных заказов нет')
	else:
		bot.send_message(chat_id=call.message.chat.id, text='Активные заказы (количество, название, цена):')
		orders = db.orders.query('item_title != "prep" & status == "prep"')
		for order_id in orders.order_id.unique():
			response = ''
			order = orders.query('order_id == @order_id')
			for index in order.index:
				item_title = order.loc[index]['item_title']
				amount = order.loc[index]['amount']
				total_price = order.loc[index]['total_price']
				response += f'{amount} {item_title} {total_price}\n\n'
			bot.send_message(chat_id=call.message.chat.id, text=f'Заказ номер {order_id}:\n\n'
																f'{response}')
		keyboard = telebot.types.InlineKeyboardMarkup()
		key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='orders_yes')
		keyboard.add(key_yes)
		key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='orders_no')
		keyboard.add(key_no)
		user_dict[call.message.chat.id].step = 'orders_func'
		bot.send_message(call.message.chat.id, text='Хотите подтвердить отправку заказа?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'orders_yes' or call.data == 'orders_no')
def orders_conf(call):
	if user_dict[call.message.chat.id].step != 'orders_func':
		return None
	if call.data == "orders_yes":
		bot.send_message(call.message.chat.id, 'Введите номер заказа')
		user_dict[call.message.chat.id].step = 'orders_conf'
		bot.register_next_step_handler(call.message, orders_conf1)
	elif call.data == "orders_no":
		user_dict[call.message.chat.id].step = 'admin_menu'
		admin_menu(user_dict[call.message.chat.id].message, user_dict[call.message.chat.id].name)


def orders_conf1(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'orders_conf':
		return None
	try:
		order_id = abs(int(message.text))
	except:
		bot.send_message(message.chat.id, text='Пожалуйста введите целое число')
		bot.register_next_step_handler(message, orders_conf1)
		return None
	data = db.orders.query('item_title != "prep" & status == "prep" & order_id == @order_id')
	if data.empty:
		bot.send_message(message.chat.id, text='Пожалуйста укажите номер заказа из списка выше')
		bot.register_next_step_handler(message, orders_conf1)
		return None
	else:
		for index in data.index:
			item_id = data.loc[index]['item_id']
			item_title = data.loc[index]['item_title']
			amount = -1 * data.loc[index]['amount']
			db.update_amount(item_title, amount)
			db.update_order_status(order_id, item_id, "done")
		bot.send_message(message.chat.id, text=f'Заказ {order_id} отправлен клиенту')
		user_dict[message.chat.id].step = 'admin_menu'
		admin_menu(user_dict[message.chat.id].message, user_dict[message.chat.id].name)


@bot.callback_query_handler(func=lambda call: call.data == "delivery")
def delivery(call: telebot.types.CallbackQuery):  # shows the list of items ready to be added to the storage
	if user_dict[call.message.chat.id].step != 'admin_menu':
		return None
	if db.shipment.query('status == "delivered"').empty:
		bot.send_message(chat_id=call.message.chat.id, text='Товаров ожидающих принятия на склад нет')
	else:
		bot.send_message(chat_id=call.message.chat.id, text='Товары ожидающие принятия (индекс, название, количество):')
		data = db.shipment.query('status == "delivered"')
		response = ''
		for index in data.index:
			item_title = data.loc[index]['item_title']
			amount = data.loc[index]['amount']
			response += f'{index} {item_title} {amount}\n\n'
		keyboard = telebot.types.InlineKeyboardMarkup()
		key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='delivery_yes')
		keyboard.add(key_yes)
		key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='delivery_no')
		keyboard.add(key_no)
		user_dict[call.message.chat.id].step = 'delivery'
		bot.send_message(call.message.chat.id, text=response + 'Хотите добавить товары на склад?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'delivery_yes' or call.data == 'delivery_no')
def delivery_conf(call):  # starts the process of delivery confirmation
	if user_dict[call.message.chat.id].step != 'delivery':
		return None
	if call.data == "delivery_yes":
		bot.send_message(call.message.chat.id, 'Введите индекс товара')
		user_dict[call.message.chat.id].step = 'delivery_conf'
		bot.register_next_step_handler(call.message, delivery_conf1)
	elif call.data == "delivery_no":
		user_dict[call.message.chat.id].step = 'admin_menu'
		admin_menu(user_dict[call.message.chat.id].message, user_dict[call.message.chat.id].name)


def delivery_conf1(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'delivery_conf':
		return None
	data = db.shipment.query('status == "delivered"')
	try:
		index = abs(int(message.text))
	except:
		bot.send_message(message.chat.id, text='Пожалуйста введите целое число')
		bot.register_next_step_handler(message, delivery_conf1)
		return None
	try:
		item_title = data.loc[index]['item_title']
		amount = data.loc[index]['amount']
		shipment_id = data.loc[index]['shipment_id']
	except:
		bot.send_message(message.chat.id, text='Пожалуйста выберите индекс из предложенных ранее')
		bot.register_next_step_handler(message, delivery_conf1)
		return None
	if db.items.query('item == @item_title').empty != True:
		db.update_amount(item_title, amount)
		db.update_shipment_status(shipment_id, item_title, "done")
		bot.send_message(message.chat.id, text=f'Товар {item_title} в количестве {amount} успешно добавлен на склад')
		user_dict[message.chat.id].step = 'admin_menu'
		admin_menu(user_dict[message.chat.id].message, user_dict[message.chat.id].name)
	else:
		bot.send_message(message.chat.id, text='Такого товара ещё нет на складе. Укажите цену по которой он будет продаваться')
		user_dict[message.chat.id].step = 'delivery_conf1'
		user_dict[message.chat.id].orders = [{'item': item_title, 'amount': amount}, shipment_id]
		bot.register_next_step_handler(message, delivery_price)


def delivery_price(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'delivery_conf1':
		return None
	try:
		price = round(abs(float(message.text)), 2)
	except:
		bot.send_message(message.chat.id, text='Пожалуйста введите десятичную дробь')
		bot.register_next_step_handler(message, delivery_price)
		return None
	item_id = db.items.sort_values(by='id', ascending=False).head(1).iloc[0]['id'] + 1
	item = user_dict[message.chat.id].orders
	new_item = item[0]
	new_item['price'] = price
	new_item['id'] = item_id
	db.add_item(new_item)
	db.update_shipment_status(item[1], new_item['item'], "done")
	user_dict[message.chat.id].orders = []
	bot.send_message(message.chat.id, text=f'Товар {new_item["item"]} в количестве {new_item["amount"]} по цене {price} успешно добавлен на склад')
	user_dict[message.chat.id].step = 'admin_menu'
	admin_menu(user_dict[message.chat.id].message, user_dict[message.chat.id].name)


@bot.callback_query_handler(func=lambda call: call.data == "shipment")
def shipment(call: telebot.types.CallbackQuery):  # starts the process of new shipment
	if user_dict[call.message.chat.id].step != 'admin_menu':
		return None
	bot.send_message(chat_id=call.message.chat.id, text='Введите через пробел название товара и его количество')
	user_dict[call.message.chat.id].step = 'shipment'
	bot.register_next_step_handler(call.message, shipment_conf)


def shipment_conf(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'shipment':
		return None
	orders = user_dict[message.chat.id].orders
	user = user_dict[message.chat.id].name
	if orders == []:
		shipment_id = db.shipment.sort_values(by='shipment_id', ascending=False).head(1).iloc[0]['shipment_id'] + 1
		user_id = db.users.query('user == @user').iloc[0]['id']
		db.add_shipment({"shipment_id": shipment_id,
						 'user_id': user_id,
						 "item_title": 'prep',
						 "amount": 0,
						 'status': 'prep'})  # reserves a shipment_id for the specific shipment
	else:
		shipment_id = orders[0]['shipment_id']  # this means that the administrator adds new item to the current shipment
	try:
		item_title, amount = message.text.rsplit(maxsplit=1)
	except:
		bot.send_message(message.from_user.id,
						 text='Заказ введён неправильно! Введите через пробел только название товара и его количество')
		bot.register_next_step_handler(message, shipment_conf)
		return None
	try:
		amount = abs(int(amount))
	except:
		bot.send_message(message.from_user.id,
						 text='Количество товара должно быть целым числами')
		bot.register_next_step_handler(message, shipment_conf)
		return None
	user_id = db.users.query("user == @user").iloc[0]['id']
	new_shipment = {"shipment_id": shipment_id,
					'user_id': user_id,
					"item_title": item_title,
					"amount": amount,
					'status': 'prep'}
	user_dict[message.chat.id].orders.append(new_shipment)
	keyboard = telebot.types.InlineKeyboardMarkup()
	key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='ship_yes')
	keyboard.add(key_yes)
	key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='ship_no')
	keyboard.add(key_no)
	user_dict[message.chat.id].step = 'shipment_conf'
	bot.send_message(message.from_user.id, text=f'В закупки добавлено {amount} {item_title}\n'
													'\n'
													'Хотите добавить что-то ещё?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'ship_yes' or call.data == 'ship_no')
def order_conf1(call):
	if user_dict[call.message.chat.id].step != 'shipment_conf':
		return None
	if call.data == "ship_yes":
		bot.send_message(call.message.chat.id, 'Введите через пробел название товара и его количество')
		user_dict[call.message.chat.id].step = 'shipment'
		bot.register_next_step_handler(call.message, shipment_conf)
	elif call.data == "ship_no":
		user_dict[call.message.chat.id].step = 'shipment_conf1'
		shipment_conf2(call.message.chat.id)


def shipment_conf2(chat_id):
	if user_dict[chat_id].step != 'shipment_conf1':
		return None
	orders = user_dict[chat_id].orders
	keyboard = telebot.types.InlineKeyboardMarkup()
	key_yes = telebot.types.InlineKeyboardButton(text='Да', callback_data='ship_yes1')
	key_no = telebot.types.InlineKeyboardButton(text='Нет', callback_data='ship_no1')
	keyboard.add(key_yes, key_no)
	i = 0
	response = ''
	for position in orders:
		response += f'{i} {position["amount"]} {position["item_title"]} \n'
		i += 1
	bot.send_message(chat_id, text='Вы заказали:\n'
										   '\n'
										   f'{response}\n'
										   '\n'
										   'Хотите убрать какую-то позицию?\n', reply_markup=keyboard)
	user_dict[chat_id].step = 'shipment_conf2'


@bot.callback_query_handler(func=lambda call: call.data == 'ship_yes1' or call.data == 'ship_no1')
def shipment_conf3(call):
	if user_dict[call.message.chat.id].step != 'shipment_conf2':
		return None
	if call.data == "ship_yes1":
		bot.send_message(call.message.chat.id, 'Введите номер позиции которую хотите убрать.\n'
											   '\n'
											   'Если вдруг передумали, введите "-1"')
		user_dict[call.message.chat.id].step = 'ship_delete'
		bot.register_next_step_handler(call.message, ship_delete_position)
	elif call.data == "ship_no1":
		user_dict[call.message.chat.id].step = 'ship_done'
		shipment_done(call.message.chat.id)


def ship_delete_position(message):
	if message.text.lower() == '/выход':
		start_message(message)
		return None
	if user_dict[message.chat.id].step != 'ship_delete':
		return None
	orders = user_dict[message.chat.id].orders
	if orders == []:
		user_dict[message.chat.id].step = 'admin_menu'
		bot.send_message(message.from_user.id, 'Все заказы удалены!')
		admin_menu(user_dict[message.chat.id].message, user)
		return None
	user = user_dict[message.chat.id].name
	try:
		i = int(message.text)
	except:
		bot.send_message(message.from_user.id, 'Пожалуйста, введите одно число!')
		bot.register_next_step_handler(message, ship_delete_position)
		return None
	if i == -1:
		user_dict[message.chat.id].step = 'ship_done'
		shipment_done(message.chat.id)
	else:
		try:
			deleted = user_dict[message.chat.id].orders.pop(i)
			bot.send_message(message.from_user.id, f'Позиция {deleted["amount"]} {deleted["item_title"]} удалена')
			if user_dict[message.chat.id].orders != []:
				user_dict[message.chat.id].step = 'shipment_conf1'
				shipment_conf2(message.from_user.id)
			else:
				user_dict[message.chat.id].step = 'admin_menu'
				bot.send_message(message.from_user.id, 'Все заказы удалены!')
				admin_menu(user_dict[message.chat.id].message, user)
		except:
			bot.send_message(message.from_user.id, 'Такой позиции нет в заказе! Пожалуйста, введите номер позиции из списка выше')
			bot.register_next_step_handler(message, ship_delete_position)
			return None


def shipment_done(chat_id):
	if user_dict[chat_id].step != 'ship_done':
		return None
	orders = user_dict[chat_id].orders
	user = user_dict[chat_id].name
	for position in orders:
		position['status'] = 'delivered'  # normally the status should be "shipment", but here we simulate an instant delivery
		db.add_shipment(position)
	user_dict[chat_id].orders = []
	user_dict[chat_id].step = 'admin_menu'
	bot.send_message(chat_id,
					 'Заказ успешно оформлен!')
	admin_menu(user_dict[chat_id].message, user)


bot.infinity_polling(none_stop=True, interval=1)
