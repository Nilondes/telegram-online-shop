# telegram-online-shop

## Description

This project represents an example of telgrambot API usage as an imitation of online-shop.

Multi-branch dialog allows users to registrate, authenticate and make orders. User also can authenticate as admin to confirm orders, make shipments and confirm shipments delivery.

The project also shows how pandas module can imitate interaction with database.

## File description

### main.py

Contains main code for telegrambot API

### db.py

Contains interaction with database.

### config.py

Contains token to access the bot api.

### items.csv

Contains list of current items in the store (id, item, amount, price).

### users.csv

Contains current user list (id, user, password, admin, discount, total).

The "admin" column indicates whether the user has admin rights.
The "discount" column indicates whether the user has a discount which is defined by the amount of his total expenses.
The "total" column indicates user total expenses.

### order.csv

Contains list of all orders made by users (order_id, user_id, item_id, item_title, amount, total_price, status).

The "status" column indicates whether the order is preparing, delivering or delivered ('done')

### shipment.csv

Contains lis of all shipments made by admin (shipment_id, user_id, item_title, amount, status)

The "status" column indicates whether the shipment is preparing, delivering ('shipment'), waiting to be put in storage ('delivered') or has been put in storage ('done')

### chat_id.txt

Contains all ids of users chat who used the bot.
