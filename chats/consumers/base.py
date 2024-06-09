# import json
# import logging
# from datetime import datetime
# from typing import Union

# from asgiref.sync import sync_to_async
# from channels.generic.websocket import AsyncWebsocketConsumer
# from django.conf import settings
# from django.core.files.base import ContentFile
# from django.db import transaction
# from django.db.models import Q


# logger_error = logging.getLogger("error")


# # Базовый класс
# class BaseChatConsumer(AsyncWebsocketConsumer):
#     """Базовый класс чата"""

#     async def connect(self):
#         await self.accept()
#         try:
#             query_string = self.scope["query_string"].decode("utf-8")
#             self.chat_id_encrypted = query_string.split("&")[-1].split("id_base64=")[-1]

#             if type(self.chat_id) != int:
#                 raise ValueError("Неправильный тип")

#         except Exception:
#             self.chat_id = 1

#         self.room_group_name = self.get_room_group_name()
#         self.user = self.scope["user"]
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         # Проверка на то, что пользователь является участником чата
#         await self.check_user_in_chat()

#         await self.send_message_history()
#         await mark_as_read_await(self.user.id, self.channel_layer, self.room_group_name)
#         check_bool = await self.check_moder_join_notify()

#         if check_bool:
#             await self.channel_layer.group_send(
#                 self.room_group_name, {"type": "users_update"}
#             )

#     async def check_user_in_chat(self):
#         """Проверка на то, что пользователь присутствует в чате"""

#         chat = await get_chat_by_id(self.chat_id)
#         return await disconnect_or_connect_user(chat, self.user)

#     async def send_message_history(self):
#         """Вывод истории сообщений"""

#         chat = await get_chat_by_id(self.chat_id)
#         if chat:
#             messages = await self.get_message_chat_filter(chat)
#             message_history = []
#             for message in messages:
#                 # При создании заказа
#                 if message.text.startswith("Новый заказ"):
#                     order_data = message.json_data
#                     sender = await self.get_sender_username(message)
#                     message_data = {
#                         "message_id": message.id,
#                         "seller": order_data["seller"],
#                         "buyer": sender,
#                         "created_at": order_data["created_at"],
#                         "product": order_data["product"],
#                         "price": order_data["price"],
#                         "currency": order_data["currency"],
#                         "cryptocurrency": order_data.get("cryptocurrency", ""),
#                         "description": order_data["description"],
#                         "time_seconds": order_data["time_seconds"],
#                         "status": order_data["status"],
#                         "order_id": order_data["order_id"],
#                         "is_new_chat": order_data["is_new_chat"],
#                         "position": order_data["position"],
#                     }
#                 # При диспутах
#                 elif message.text == "dispute":
#                     order_data = message.json_data
#                     creator = await self.get_sender_username(message)
#                     message_data = {
#                         "message_id": message.id,
#                         "created_at": str(
#                             message.created_at.strftime("%Y-%m-%d %H:%M")
#                         ),
#                         "description": order_data["description"],
#                         "creator": creator,
#                         "status": order_data["status"],
#                         "dispute_id": order_data["dispute_id"],
#                         "action": "need_moderator",
#                         "position": message.position,
#                     }
#                 # При простом сообщение
#                 else:
#                     sender = await self.get_sender_username(message)
#                     reply_to = await get_reply_to_message(message)
#                     message_data = await get_message_data_for_chat_history(
#                         message=message, sender=sender, reply_to=reply_to
#                     )
#                 message_history.append(message_data)

#             await self.send(text_data=json.dumps(message_history))

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

#     async def receive(self, text_data):
#         text_data_json = json.loads(text_data)
#         action = text_data_json.get("action")
#         await mark_as_read_await(self.user.id, self.channel_layer, self.room_group_name)
#         if action == "delete_chat":
#             await self.delete_chat()

#         elif action == "send_message":
#             await self.send_message_receive(text_data_json)

#         elif action == "get_more_messages":
#             await self.get_more_messages(text_data_json)

#         elif action == "add_user":
#             await self.add_user_in_chat(text_data_json)

#         elif action == "delete_user":
#             await self.delete_user(text_data_json)

#         elif action == "pin_message":
#             await self.pin_message(text_data_json)

#         elif action == "unpin_all_messages":
#             await self.unpin_all_messages(text_data_json)

#         elif action == "delete_messages":
#             await self.delete_messages(text_data_json)

#         elif action == "edit_message":
#             await self.edit_message(text_data_json)

#         elif action == "add_reaction":
#             await self.add_reaction(text_data_json)

#         elif action == "forward_messages":
#             await self.forward_messages(text_data_json)

#     async def forward_messages(self, data):
#         """Перессылка сообщения в другой чат"""
#         try:
#             message_ids = data[
#                 "message_ids"
#             ]  # Получаем ids сообщений, которые надо переслать
#             chat = await get_chat_by_id(self.chat_id)  # Получаем чат с помощью id
#             messages = await self.proccess_forward_messages(
#                 chat=chat, message_ids=message_ids
#             )
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "forward_messages",
#                     "message": messages,
#                 },
#             )

#         except Exception as e:
#             logger_error.error(f"Ошибка пересылки сообщений: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "forward_messages",
#                         "error": "Не получилось переслать сообщения.",
#                     }
#                 )
#             )

#     async def delete_messages(self, data):
#         """Удаление сообщения в чатах"""
#         try:
#             message_ids = data["message_ids"]
#             chat = await get_chat_by_id(self.chat_id)
#             await self.proccess_delete_messages(chat, message_ids=message_ids)
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "delete_messages",
#                     "message": message_ids,
#                 },
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка удаления сообщения: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "delete_messages",
#                         "error": "Не получилось удалить сообщение.",
#                     }
#                 )
#             )

#     async def delete_user(self, data):
#         """Удаление пользователя из чата (только для модераторов) | пользователь не сможет просмотреть историю после удаления"""
#         try:
#             user_id = data["user_id"]
#             chat = await get_chat_by_id(self.chat_id)
#             message = await self.proccess_delete_user(chat, user_id=user_id)
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "delete_user",
#                     "message": message,
#                 },
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка удаления пользователя из чата: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "delete_user",
#                         "error": "Не получилось удалить пользователя из чата.",
#                     }
#                 )
#             )

#     async def add_reaction(self, data):
#         """Добавление реакции на сообщение"""
#         try:
#             message_id = data["message_id"]
#             emoji_name = data["emoji_name"]
#             chat = await get_chat_by_id(self.chat_id)
#             previous_emoji = await self.proccess_add_or_delete_reaction(
#                 chat=chat, message_id=message_id, emoji_name=emoji_name
#             )
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "add_reaction",
#                     "message": {
#                         "message_id": message_id,
#                         "emoji_name": emoji_name,
#                         "previous_emoji": previous_emoji,
#                         "user": self.user.username,
#                     },
#                 },
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка добавления реакции: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "add_reaction",
#                         "error": "Не получилось поставить реакцию.",
#                     }
#                 )
#             )

#     async def edit_message(self, data):
#         """Редактирование сообщения в чатах"""
#         try:
#             # Получение данных о сообщение
#             message_id = data["message_id"]
#             text = data.get("text")
#             reply_to = data.get("reply_to")
#             image_base64 = data.get("image_base64")

#             chat = await get_chat_by_id(self.chat_id)
#             message = await self.proccess_edit_message(
#                 chat,
#                 message_id=message_id,
#                 text=text,
#                 reply_to=reply_to,
#                 image_base64=image_base64,
#             )
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "edit_message",
#                     "message": message,
#                 },
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка редактирования сообщения: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "edit_message",
#                         "error": "Не получилось редактировать сообщение.",
#                     }
#                 )
#             )

#     async def add_user_in_chat(self, data):
#         """Добавление пользователя в чат (только для модераторов)"""

#         try:
#             # Получение пользователя
#             user = self.user

#             # Проверка на то, что пользователь модератора
#             if not (user.role == User.MODERATOR):
#                 raise ValueError("Ошибка добавления. Вы не модератор.")

#             user_username = data["username"]
#             chat = await get_chat_by_id(self.chat_id)
#             message = await self.add_user(chat, user_username)

#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "add_user",
#                     "message": message,
#                 },
#             )

#         except Exception as e:
#             logger_error.error(f"Ошибка добавления пользователя {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "add_user",
#                         "error": "Ошибка добавления пользователя",
#                     }
#                 )
#             )

#     async def get_more_messages(self, data):
#         """Получение новых 50 сообщений для истории сообщений"""

#         try:
#             last_message_position = data["position"]
#             chat = await get_chat_by_id(self.chat_id)
#             messages = await self.get_message_for_more_messages(
#                 chat, last_message_position
#             )
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "get_more_messages",
#                     "message": messages,
#                 },
#             )

#         except Exception as e:
#             logger_error.error(f"Ошибка получения пагинации сообщений {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "get_more_messages",
#                         "error": "Ошибка вывода сообщений",
#                     }
#                 )
#             )

#     async def get_message_for_more_messages(self, chat: Chat, position: int) -> list:
#         """Получение большего количества сообщений для истории сообщений"""

#         start_position = max(1, position - 50)
#         end_position = position
#         # Фильтрация сообщений с нужной позицией
#         messages = await get_filter_message_with_position(
#             start_position=start_position, end_position=end_position, chat=chat
#         )

#         # Заполнение списка сообщениями
#         messages_list = []
#         for message in messages:
#             # Получение данных
#             sender_id = await get_sender_id_from_message(message)
#             sender = await self.get_sender_username_and_photo_for_id(sender_id)
#             reply_to = await get_reply_to_message(message)

#             # Получение даты сообщения в json формате
#             data = await get_message_data_for_chat_history(
#                 message=message, sender=sender, reply_to=reply_to
#             )

#             messages_list.append(data)

#         return messages_list

#     @rate_limit_chat_to_pay_and_message(
#         rate=3, per=1, redis_key_prefix="message_create"
#     )
#     async def send_message_receive(self, text_data_json):
#         """Отправка сообщения в группу"""

#         # Получение данных
#         message = text_data_json.get("message")
#         reply_to_id = text_data_json.get("reply_to_id")
#         sender_id = text_data_json.get("sender_id")
#         image = text_data_json.get("image")
#         created_at = datetime.now()

#         # Проверка на чужие urls
#         message = await check_bad_url(message, self.chat_id)

#         # Проверка на ответ к сообщению
#         reply_to = None
#         if reply_to_id:
#             try:
#                 reply_to = await get_message_by_id_async(reply_to_id)
#                 reply_to_serializer = await self.get_serializer_reply(reply_to)
#             except Message.DoesNotExist:
#                 pass

#         # Проверка на фотографию
#         if image:
#             try:
#                 image = await self.get_image_for_base64(image)
#             except Exception as e:
#                 logger_error.error(f"Ошибка сериализации изображения {str(e)}")
#                 image = None

#         # Получение пользователя
#         sender = await self.get_sender_username_and_photo_for_id(sender_id)

#         # Сохранение сообщения
#         instance = await save_message(
#             self.chat_id, sender_id, message, reply_to_id, image
#         )
#         # Сериализатор изображения
#         image_serializer = await image_to_serializer(instance)

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat_message",
#                 "message_id": instance.id,
#                 "message": message,
#                 "sender": sender,
#                 "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
#                 "image": image_serializer if image else "",
#                 "viewed": False,
#                 "reply_to": reply_to_serializer if reply_to else "",
#                 "position": instance.position,
#                 "json": instance.json_data,
#             },
#         )

#     async def chat_message(self, event):
#         """Отправка сообщения в канал"""

#         # Получение данных
#         message_id = event["message_id"]
#         message = event["message"]
#         sender = event["sender"]
#         created_at = event["created_at"]
#         image = event["image"]
#         viewed = event["viewed"]
#         reply_to = event["reply_to"]
#         position = event["position"]
#         json_data = event["json"]

#         await self.send(
#             text_data=json.dumps(
#                 {
#                     "message_id": message_id,
#                     "message": message,
#                     "sender": sender,
#                     "created_at": created_at,
#                     "image": f"http://{settings.DOMAIN_NAME}{str(image)}"
#                     if image
#                     else "",  # Передача фотографии, если она есть
#                     "viewed": viewed,
#                     "reply_to": reply_to if reply_to else "",
#                     "position": position,
#                     "json": json_data,
#                 }
#             )
#         )

#     async def delete_chat(self):
#         try:
#             chat = await get_chat_by_id(self.chat_id)
#             await self.chat_delete(chat)
#         except Chat.DoesNotExist:
#             logger_error.error("Ошибка удаления чата.")
#             await self.send(
#                 text_data=json.dumps(
#                     {"action": "delete_chat", "message": "Чат успешно удален"}
#                 )
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка удаления чата {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "delete_chat",
#                         "error": "Ошибка удаления чата",
#                     }
#                 )
#             )

#     async def mark_as_read(self, event):
#         """Функция отметки о том что сообщение прочитано"""

#         await self.mark_messages_as_read()
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "action_message",
#                 "action": "mark_as_read",
#                 "message": self.user.username,
#             },
#         )

#     # Закрепление сообщения
#     async def pin_message(self, data):
#         """Закреп сообщения модератором"""
#         try:
#             message_id = data["message_id"]
#             chat = await get_chat_by_id(self.chat_id)
#             message = await self.proccess_pin_message(chat, message_id=message_id)
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "pin_message",
#                     "message": message,
#                 },
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка закрепа сообщения: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "pin_message",
#                         "error": "Не получилось закрепить сообщение.",
#                     }
#                 )
#             )

#     async def unpin_all_messages(self, data):
#         """Открепление всех сообщений разом"""

#         try:
#             chat = await get_chat_by_id(self.chat_id)
#             message = await self.proccess_uppin_all_messages(chat)
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "action_message",
#                     "action": "unpin_all_messages",
#                     "message": message,
#                 },
#             )
#         except Exception as e:
#             logger_error.error(f"Ошибка открепления всех сообщений: {str(e)}")
#             await self.send(
#                 text_data=json.dumps(
#                     {
#                         "action": "unpin_all_messages",
#                         "error": "Не получилось открепить все сообщения.",
#                     }
#                 )
#             )

#     async def users_update(self, event):
#         """Отправка в канал обновления пользователей"""
#         user = self.user
#         chat = await get_chat_by_id(self.chat_id)

#         if user.role == User.MODERATOR:
#             # Данные для сообщения
#             action = "update_user"
#             text = f"Модератор {user.username} присоединился к чату."
#             message = await sync_to_async(order_chat_create_message_for_history)(
#                 action=action, text=text, chat_instance=chat
#             )
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {"type": "action_message", "action": "update_user", "message": message},
#             )

#     async def action_message(self, event):
#         """Отправка в канал action сообщений"""

#         action = event["action"]
#         message = event["message"]
#         await self.send(
#             text_data=json.dumps(
#                 {
#                     "action": action,
#                     "message": message,
#                 }
#             )
#         )

#     @sync_to_async
#     @transaction.atomic
#     def mark_messages_as_read(self):
#         """Отметить сообщения как прочитанное"""

#         chat = get_chat_by_id_sync(chat_id=self.chat_id)
#         try:
#             if chat:
#                 Message.objects.filter(
#                     Q(chat=chat) & ~Q(sender=self.user) & Q(viewed=False)
#                 ).update(viewed=True)

#         except Exception as e:
#             logger_error.error(f"Ошибка обновления просмотренных сообщений: {str(e)}")

#     def get_room_group_name(self):
#         """Получение имени комнаты <надо определять в каждом дочернем классе>"""

#         pass

#     @sync_to_async
#     @transaction.atomic
#     def get_sender_username_and_photo_for_id(self, sender_id: str) -> dict:
#         """Получение имени и фото отправителя по id"""

#         # Получение отправителя
#         sender = get_user_by_id_sync(sender_id)

#         data = {
#             "id": sender.id,
#             "username": sender.username,
#             "photo": f"http://{settings.DOMAIN_NAME}/media/{sender.photo}",
#             "role": sender.role,
#         }

#         return data

#     @sync_to_async
#     def get_message_chat_filter(self, chat: Chat) -> list:
#         """Получение сообщений чата"""

#         return list(Message.objects.filter(chat=chat).order_by("-created_at")[:50])[
#             ::-1
#         ]

#     @sync_to_async
#     @transaction.atomic
#     def chat_delete(self, chat: Chat) -> None:
#         """Базовая функция удаления чата"""

#         try:
#             if chat.id == 1:
#                 raise ValueError("Общий чат нельзя удалить.")

#             chat.delete()
#         except Exception as e:
#             logger_error.error(f"Ошибка удаления чата {str(e)}")

#     @sync_to_async
#     def get_serializer_reply(self, reply_to: Message) -> MessageSerializer:
#         """Получение сериализатора ответа"""

#         return MessageSerializer(reply_to).data

#     @sync_to_async
#     def get_image_for_base64(self, image: str) -> ContentFile:
#         """Декодирование изображение из base64"""

#         compressed_data = image_base64_decode(image)
#         return compressed_data

#     @sync_to_async
#     def get_chat_moderator_boolean(self, chat: Chat) -> bool:
#         """Получение bool значения есть ли модератор в чате"""

#         return True if chat.moderator else False

#     @sync_to_async
#     def message_serializer(self, message: Message) -> dict:
#         """Сериализатор сообщения"""

#         data = {
#             "message_id": message.id,
#             "message": message.text,
#             "sender": {
#                 "id": message.sender.id,
#                 "username": message.sender.username,
#                 "photo": f"http://{settings.DOMAIN_NAME}/media/{message.sender.photo}",
#                 "role": message.sender.role,
#             },
#             "created_at": str(message.created_at.strftime("%Y-%m-%d %H:%M")),
#             "viewed": message.viewed,
#             "action": message.action,
#             "is_edited": message.is_edited,
#         }

#         return data

#     @sync_to_async
#     def get_sender_username(self, message: Message) -> UserShortSerializer:
#         return UserShortSerializer(message.sender).data

#     @sync_to_async
#     def add_user(self, chat: Chat, user_username: str) -> dict:
#         """Добавление пользователя в чат"""

#         # Получение пользователя
#         user = User.objects.filter(username__icontains=user_username).first()

#         if not user:
#             raise ValueError("Ошибка! Такого пользователя не существует")

#         # Обновление чата
#         chat.all_users.add(user)

#         text_for_message = f"Модератор {self.user.username} добавил пользователя {user.username} в чат."
#         action = "add_user"
#         message = order_chat_create_message_for_history(
#             text=text_for_message, action=action, chat_instance=chat
#         )

#         return message

#     @sync_to_async
#     def check_moder_join_notify(self) -> bool:
#         """Проверка надо ли отправлять сообщение о том что присоединился модератор"""

#         # Проверка на общий чат
#         if self.chat_id == 1:
#             return False

#         # Получение чата
#         chat = get_chat_by_id_sync(chat_id=self.chat_id)
#         chat_group = get_chat_group_by_chat(chat=chat)

#         if chat_group:
#             return False

#         # Добавление модератора к пользователям
#         if (
#             self.user.role == User.MODERATOR
#             and chat.moderator is None
#             and self.user != chat.user1
#         ):
#             chat.moderator = self.user
#             chat.save()
#             return True

#     @sync_to_async
#     def proccess_pin_message(self, chat: Chat, message_id: int) -> None:
#         """Добавления сообщения в закрепленные"""

#         # Проверка для общего чата
#         if chat.id == 1 and self.user.role != User.MODERATOR:
#             raise ValueError("Нельзя закрепить сообщение в чате")

#         # Проверка для закрепления если сообщества
#         chat_group = get_chat_group_by_chat(chat=chat)

#         if chat_group:
#             if self.user.username != chat_group.creator.username:
#                 raise ValueError("Ошибка! Вы не создатель сообщества.")

#         message = get_message_by_id(message_id=message_id)

#         if not message:
#             raise ValueError("Ошибка! Такого сообщения не существует")

#         # Добавление в закрепленные сообщения или открепления
#         message_text = message.text
#         if len(message_text) > 20:
#             message_text = f"{message_text[:20]}..."  # Ограничение сообщения, чтобы не спамило в чате

#         if message in chat.pinned_messages.all():
#             text = f'{self.user.username} открепил(а) "{message_text}".'
#             chat.pinned_messages.remove(message)
#         else:
#             text = f'{self.user.username} закрепил(а) "{message_text}".'
#             chat.pinned_messages.add(message)

#         action = "pin_message"
#         json_data = {"pinned_message_id": message.id}
#         # Создание сообщения о том, что сообщение закрепили
#         data = order_chat_create_message_for_history(
#             chat_instance=chat, text=text, action=action, json_data=json_data
#         )

#         return data

#     @sync_to_async
#     def decrypted_chat_id_encrypted(self, chat_id_encrypted) -> int:
#         """Расшифровка id чата"""

#         chat_id = decrypted_model_id(chat_id_encrypted)

#         return chat_id

#     @sync_to_async
#     def proccess_uppin_all_messages(self, chat: Chat) -> dict:
#         """Открепление всех сообщений в чате"""

#         # Проверка для общего чата
#         if chat.id == 1 and self.user.role != User.MODERATOR:
#             raise ValueError("Нельзя открепить все сообщения в чате")

#         # Проверка для закрепления если сообщества
#         chat_group = get_chat_group_by_chat(chat=chat)

#         if chat_group:
#             if self.user.username != chat_group.creator.username:
#                 raise ValueError("Ошибка! Вы не создатель сообщества.")

#         chat.pinned_messages.update(json_data={})
#         chat.pinned_messages.clear()

#         action = "unpin_all_messages"
#         text = f"Пользователь {self.user.username} открепил все сообщения"

#         # Создание сообщения о том, что сообщение закрепили
#         data = order_chat_create_message_for_history(
#             chat_instance=chat, text=text, action=action
#         )

#         return data

#     @sync_to_async
#     @transaction.atomic
#     def proccess_delete_messages(self, chat: Chat, message_ids: list) -> None:
#         """Удаление сообщения в публичном чате модератором"""

#         # Получение сообщений
#         messages = get_messages_by_ids_and_chat(ids=message_ids, chat=chat)

#         # Валидация сообщений
#         if messages == []:
#             raise ValueError("Такого сообщения не существует.")

#         # Проверка для общего чата
#         if chat.id == 1 and not (self.user.role == User.MODERATOR):
#             raise ValueError("Не получилось удалить сообщение, вы не модератор.")

#         # Проверка для сообщества
#         chat_group = get_chat_group_by_chat(chat=chat)

#         for message in messages:
#             if message.sender != self.user:
#                 if chat_group and self.user == chat_group.creator:
#                     message.delete()
#                 elif self.user.role == User.MODERATOR:
#                     message.delete()
#                 else:
#                     raise ValueError("Это не ваше сообщение")
#             else:
#                 message.delete()

#     @sync_to_async
#     def proccess_edit_message(
#         self,
#         chat: Chat,
#         message_id: int,
#         text: str,
#         reply_to: int,
#         image_base64: Union[str, None] = None,
#     ) -> None:
#         """Процесс редактирования сообщения"""

#         # Получение сообщения
#         message = get_message_by_id(message_id=message_id)

#         # Валидация сообщений
#         if not message:
#             raise ValueError("Такого сообщения не существует.")

#         # Проверка на то, что сообщение из нужного чата
#         if message.chat != chat:
#             raise ValueError("Сообщение не из этого чата.")

#         if message.sender != self.user:
#             raise ValueError("Это не ваше сообщение.")

#         if message.action is not None:
#             raise ValueError("Вы не можете менять служебные сообщения.")

#         message = proccess_update_message(
#             message=message, text=text, reply_to=reply_to, image_base64=image_base64
#         )

#         return MessageSerializer(message).data

#     @sync_to_async
#     def proccess_add_or_delete_reaction(
#         self, message_id: int, chat: Chat, emoji_name: str
#     ) -> None:
#         """Добавление или отмены реакции"""

#         # Получение сообщения
#         message = get_message_by_id(message_id=message_id)

#         if not message:
#             raise ValueError("Такого сообщения нет")

#         if message.chat != chat:
#             raise ValueError("Сообщение не из того чата")

#         # Получение эмодзи
#         emoji = Emoji.objects.filter(name=emoji_name).first()

#         # Если emoji нет то создаем
#         if not emoji:
#             emoji = Emoji.objects.create(name=emoji_name)

#         # Инициализация прошлой реакции
#         previous_emoji = ""

#         # Поиск такой реакции на этом сообщение
#         reaction = Reaction.objects.filter(
#             user=self.user, emoji=emoji, message=message
#         ).first()

#         if not reaction:
#             # Получение количества реакции на опрделенный эмодзи и сообщение
#             reactions_count = Reaction.objects.filter(
#                 message=message, emoji=emoji
#             ).count()

#             # Лимит на реакции
#             if reactions_count >= 50:
#                 raise ValueError("На сообщение максимальное количество реакций")

#             previous_user_reaction = Reaction.objects.filter(
#                 user=self.user, message=message
#             ).first()

#             if previous_user_reaction:
#                 previous_emoji = previous_user_reaction.emoji.name
#                 previous_user_reaction.delete()

#             reaction = Reaction.objects.create(
#                 user=self.user, emoji=emoji, message=message
#             )

#         else:
#             previous_emoji = reaction.emoji.name
#             reaction.delete()

#         return previous_emoji

#     @sync_to_async
#     def proccess_delete_user(self, chat: Chat, user_id: int):
#         """Удаление пользователя из любого чата (только для модеров)"""

#         if self.user.role != User.MODERATOR:
#             raise ValueError("Вы не можете удалить пользователя")

#         blocked_user = get_user_by_id_sync(user_id=user_id)

#         # Бан или разбан пользователя
#         if blocked_user in chat.blocked_users.all():
#             text = f"Пользователь {blocked_user.username} разблокирован."
#             chat.blocked_users.remove(blocked_user)
#             chat.all_users.remove(blocked_user)
#         else:
#             text = f"Пользователь {blocked_user.username} заблокирован."
#             chat.blocked_users.add(blocked_user)
#             chat.all_users.add(blocked_user)

#         action = "delete_user"

#         # Создание сообщения о том, что пользователя заблокали или отблокали
#         data = order_chat_create_message_for_history(
#             chat_instance=chat, text=text, action=action
#         )

#         return data

#     @sync_to_async
#     def proccess_forward_messages(self, chat: Chat, message_ids: list) -> None:
#         """Процесс пересылки сообщения"""

#         # Получение сообщений
#         messages = get_messages_by_ids_and_chat(ids=message_ids)
#         logger_error.error(messages)

#         from_chat = None
#         for message in messages:
#             logger_error.error(message.chat)
#             from_chat = message.chat  # Получение чата из которого пересылаем

#         logger_error.error(from_chat)

#         chat_group = get_chat_group_by_chat(
#             chat=chat
#         )  # Получение сообщества в которое пересылаем

#         if chat_group:  # Проверка на разрешение пересылки в сообщества
#             if not chat_group.can_forward_message:
#                 raise ValueError(
#                     "Вы не можете пересылать в сообщества, ведь пересылка запрещена."
#                 )

#         if not from_chat:
#             raise ValueError("Такого чата не существует")

#         if chat.id == 1:
#             raise ValueError("Нельзя пересылать в общий чат")

#         if self.user not in from_chat.all_users.all():
#             raise ValueError("Вас нет в этом чате")

#         from_chat_group = get_chat_group_by_chat(
#             chat=from_chat
#         )  # Получение сообщества из которое пересылаем

#         if from_chat_group:  # Проверка на разрешение пересылки из сообщества
#             if not from_chat_group.can_forward_message:
#                 raise ValueError(
#                     "Вы не можете пересылать из сообщества, ведь пересылка запрещена."
#                 )

#         msg_list = []
#         for message in messages:  # Создаем сообщения для нового чата
#             msg = create_message_chat(
#                 chat=chat,
#                 user=self.user,
#                 text=message.text,
#                 json_data=message.json_data,
#                 image=message.image,
#                 forward_from=message.sender,
#             )
#             msg_list.append(msg)

#         return MessageSerializer(msg_list, many=True).data
