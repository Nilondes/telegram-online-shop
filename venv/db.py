"""
This module imitates the app database.
"""
import pandas as pd
import csv


users = pd.read_csv('users.csv')
items = pd.read_csv('items.csv')
orders = pd.read_csv('orders.csv')
shipment = pd.read_csv('shipment.csv')
chat_ids = []

with open('chat_id.txt', 'r') as f:  # initiating ids of all known users
    for row in f:
        chat_ids.append(int(row))


def add_chat_id(chat_id):  # adds new chat id
    with open('chat_id.txt', 'a') as f:
        f.write(str(chat_id)+'\n')
    chat_ids.append(chat_id)


def add_user(new_user):  # adds new user to the database
    with open('users.csv', 'a') as f:
        writer = csv.DictWriter(f, quoting=csv.QUOTE_NONNUMERIC,
                                fieldnames=['id', 'user', 'password', 'admin', 'discount', 'total'])
        writer.writerow(new_user)
    global users
    users = pd.read_csv('users.csv')


def add_item(new_item):  # adds new item to the database
    with open('items.csv', 'a') as f:
        writer = csv.DictWriter(f, quoting=csv.QUOTE_NONNUMERIC, fieldnames=["id", "item", "amount", "price"])
        writer.writerow(new_item)
    global items
    items = pd.read_csv('items.csv')


def print_items():  # prints items from database to file.
    df = items[['id', 'item', 'price']]
    df.columns = ['Номер товара', 'Название товара', 'Цена']
    with open('items.txt', 'w') as f:
        print(df, file=f)


def add_order(new_order):  # adds new order to the database
    with open('orders.csv', 'a') as f:
        writer = csv.DictWriter(f, quoting=csv.QUOTE_NONNUMERIC, fieldnames=["order_id", "user_id", "item_id", 'item_title', "amount", "total_price", 'status'])
        writer.writerow(new_order)
    global orders
    orders = pd.read_csv('orders.csv')


def print_from_db(data, columns=[], rename=[]):  # prints something from database with the desired column names
    df = data[columns]
    df.columns = rename
    with open('db_print.txt', 'w') as f:
        print(df, file=f)


def update_total(user, total):  # updates the user total expenses
    global users
    index = users[users['user'] == user].index[0]
    users.loc[index, 'total'] += total
    users.to_csv(r'users.csv', index=False)


def grant_discount(user):  # grants a discount for a user
    global users
    index = users[users['user'] == user].index[0]
    if users.loc[index, 'total'] > 5000:
        users.loc[index, 'discount'] = 0.1
    elif users.loc[index, 'total'] > 1000:
        users.loc[index, 'discount'] = 0.05
    elif users.loc[index, 'total'] > 100:
        users.loc[index, 'discount'] = 0.01
    users.to_csv(r'users.csv', index=False)


def add_shipment(new_shipment):  # adds new shipment to the database
    with open('shipment.csv', 'a') as f:
        writer = csv.DictWriter(f, quoting=csv.QUOTE_NONNUMERIC, fieldnames=["shipment_id", "user_id", "item_title", "amount", 'status'])
        writer.writerow(new_shipment)
    global shipment
    shipment = pd.read_csv('shipment.csv')


def update_amount(item_title, amount):  # updates the current amount of the item in storage
    global items
    index = items[items['item'] == item_title].index[0]
    items.loc[index, 'amount'] += amount
    items.to_csv(r'items.csv', index=False)


def update_shipment_status(shipment_id, item_title, new_status):  # updates the shipment status for the item
    global shipment
    index = shipment[shipment['shipment_id'] == shipment_id][shipment['item_title'] == item_title].index[0]
    shipment.loc[index, 'status'] = new_status
    shipment.to_csv(r'shipment.csv', index=False)


def update_order_status(order_id, item_id, new_status):  # updates the order status for the item
    global orders
    index = orders[orders['order_id'] == order_id][orders['item_id'] == item_id].index[0]
    orders.loc[index, 'status'] = new_status
    orders.to_csv(r'orders.csv', index=False)
