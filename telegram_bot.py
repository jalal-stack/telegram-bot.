from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetParticipantsRequest, JoinChannelRequest
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.types import Channel, Chat, User, ChannelParticipantsAdmins, InputPeerEmpty
from telegram.ext import Application, CommandHandler
import json
import os
from datetime import datetime
from googlesearch import search
import instaloader
import re

# Конфигурация
API_ID = "20971021"  # Замени на твой api_id
API_HASH = "c85636e36b5e7a72a84a5722887fa431"  # Замени на твой api_hash
BOT_TOKEN = "8044618810:AAGo808I1wrSmOOpUfpqTzx6UCm08GrfB90"  # Замени на токен бота
OUTPUT_DIR = os.path.expandvars(r"%USERPROFILE%\Desktop\telegram_data")

# Инициализация Telethon и Instaloader
client = TelegramClient('session', API_ID, API_HASH)
L = instaloader.Instaloader()

async def start(update, context):
    await update.message.reply_text(
        "Привет! Используй команды:\n"
        "/find <ID или username> — полный поиск данных\n"
        "/adminsearch <ID или username> — поиск чатов, где пользователь админ или владелец\n"
        "/adminbychat <chat_id или @username> — поиск админов и владельца в указанном чате"
    )

async def find(update, context):
    try:
        target = " ".join(context.args).strip()
        if not target:
            await update.message.reply_text("Укажи ID или username, например: /find @VictimUser")
            return

        await client.start()
        # Поиск Telegram-пользователя
        try:
            if target.isdigit():
                user = await client(GetFullUserRequest(id=int(target)))
            else:
                user = await client(GetFullUserRequest(id=target.lstrip('@')))
            user_data = user.users[0]
            target_id = user_data.id
            target_username = user_data.username or "нет"
            await update.message.reply_text(f"Найден Telegram-пользователь: ID={target_id}, Username=@{target_username}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка поиска Telegram-пользователя: {e}")
            return

        # Сбор данных
        chats_data = {
            "telegram_user": {
                "id": target_id,
                "username": f"@{target_username}",
                "first_name": user_data.first_name or "",
                "last_name": user_data.last_name or "",
                "phone": user_data.phone or "скрыт",
                "bio": user.full_user.about or "нет"
            },
            "public_channels": [],
            "private_channels": [],
            "public_groups": [],
            "private_groups": [],
            "supergroups": [],
            "potential_chats": [],
            "messages": [],
            "instagram": {},
            "email": [],
            "google_account": []
        }

        # 1. Telegram-чаты, где ты участник
        async for dialog in client.iter_dialogs():
            chat = dialog.entity
            chat_type = None
            is_private = False

            if isinstance(chat, Channel):
                if chat.megagroup:
                    chat_type = "supergroups"
                else:
                    chat_type = "public_channels" if not chat.access_hash else "private_channels"
                    is_private = bool(chat.access_hash)
            elif isinstance(chat, Chat):
                chat_type = "public_groups" if not chat.access_hash else "private_groups"
                is_private = bool(chat.access_hash)
            else:
                continue

            is_admin = False
            is_owner = False
            participant_count = getattr(chat, "participants_count", None) or "неизвестно"
            error = None

            try:
                async for participant in client.iter_participants(chat, limit=1000):
                    if participant.id == target_id:
                        if getattr(participant, "creator", False):
                            is_owner = True
                            is_admin = True
                        elif getattr(participant, "admin", False):
                            is_admin = True
                        break

                if not is_owner:
                    async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins):
                        if admin.id == target_id:
                            is_admin = True
                            is_owner = getattr(admin, "creator", False)
                            break

                chat_info = {
                    "title": chat.title,
                    "id": chat.id,
                    "username": getattr(chat, "username", None) or "нет",
                    "participants_count": participant_count,
                    "is_private": is_private,
                    "is_owner": is_owner,
                    "is_admin": is_admin,
                    "date_joined": "неизвестно"
                }
                chats_data[chat_type].append(chat_info)

                # Парсинг сообщений
                async for message in client.iter_messages(chat, from_user=target_id, limit=50):
                    chats_data["messages"].append({
                        "chat_title": chat.title,
                        "chat_id": chat.id,
                        "message_id": message.id,
                        "text": message.text or "нет текста",
                        "date": message.date.isoformat()
                    })

            except Exception as e:
                error = str(e)
                if "admin privileges" in error.lower():
                    chats_data["potential_chats"].append({
                        "title": chat.title,
                        "id": chat.id,
                        "username": getattr(chat, "username", None) or "нет",
                        "participants_count": participant_count,
                        "is_private": is_private,
                        "note": "Недостаточно прав для проверки участников",
                        "error": error
                    })
                else:
                    await update.message.reply_text(f"Ошибка проверки Telegram-чата {chat.title}: {e}")

        # 2. Публичные Telegram-чаты через поиск
        try:
            search_query = f"@{target_username}" if target_username != "нет" else str(target_id)
            async for message in client.iter_messages(SearchGlobalRequest(
                q=search_query,
                filter=None,
                limit=50,
                from_id=None,
                peer=InputPeerEmpty()
            )):
                if hasattr(message, "peer_id") and hasattr(message.peer_id, "channel_id"):
                    chat_id = message.peer_id.channel_id
                    try:
                        chat = await client.get_entity(chat_id)
                        if isinstance(chat, Channel):
                            chat_type = "public_channels" if not chat.access_hash else "private_channels"
                            is_private = bool(chat.access_hash)
                            if chat.megagroup:
                                chat_type = "supergroups"

                            is_admin = False
                            is_owner = False
                            try:
                                async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins, limit=10):
                                    if admin.id == target_id:
                                        is_admin = True
                                        is_owner = getattr(admin, "creator", False)
                                        break
                            except Exception:
                                pass

                            chat_info = {
                                "title": chat.title,
                                "id": chat.id,
                                "username": getattr(chat, "username", None) or "нет",
                                "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                                "is_private": is_private,
                                "is_owner": is_owner,
                                "is_admin": is_admin,
                                "date_joined": "неизвестно",
                                "source": "global_search"
                            }
                            if chat_info not in chats_data[chat_type]:
                                chats_data[chat_type].append(chat_info)
                    except Exception as e:
                        await update.message.reply_text(f"Ошибка обработки Telegram-чата из поиска: {e}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка глобального поиска Telegram: {e}")


        # 3. Приватные Telegram-чаты по ссылкам
        try:
            await update.message.reply_text(
                "Введите ссылки на приватные Telegram-чаты (t.me/+abc123), через пробел, или 'нет': ")
            invite_links = (await context.bot.wait_for('message', timeout=60)).text.split() if (await update.message.reply_text("Ожидаю ссылки...")).text != "нет" else []
            for link in invite_links:
                try:
                    await client(JoinChannelRequest(link))
                    chat = await client.get_entity(link)
                    is_private = bool(chat.access_hash)
                    chat_type = "private_channels"
                    if isinstance(chat, Channel) and chat.megagroup:
                        chat_type = "supergroups"
                    elif isinstance(chat, Chat):
                        chat_type = "private_groups"

                    is_present = False
                    is_admin = False
                    is_owner = False
                    try:
                        async for participant in client.iter_participants(chat, limit=1000):
                            if participant.id == target_id:
                                is_present = True
                                if getattr(participant, "creator", False):
                                    is_owner = True
                                    is_admin = True
                                elif getattr(participant, "admin", False):
                                    is_admin = True
                                break
                    except Exception as e:
                        chats_data["potential_chats"].append({
                            "title": chat.title,
                            "id": chat.id,
                            "username": getattr(chat, "username", None) or "нет",
                            "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                            "is_private": is_private,
                            "note": "Недостаточно прав для проверки участников",
                            "error": str(e)
                        })
                        continue

                    if is_present:
                        chat_info = {
                            "title": chat.title,
                            "id": chat.id,
                            "username": getattr(chat, "username", None) or "нет",
                            "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                            "is_private": is_private,
                            "is_owner": is_owner,
                            "is_admin": is_admin,
                            "date_joined": "неизвестно",
                            "source": "invite_link"
                        }
                        chats_data[chat_type].append(chat_info)
                except Exception as e:
                    await update.message.reply_text(f"Ошибка обработки Telegram-ссылки {link}: {e}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка обработки ссылок на чаты: {e}")

        # 4. Поиск Instagram-аккаунта
        instagram_data = {"username": "не найдено", "bio": "", "email": "", "is_business": False}
        if target_username != "нет":
            try:
                query = f"site:instagram.com @{target_username}"
                instagram_urls = []
                for url in search(query, num_results=5):
                    if "instagram.com" in url:
                        instagram_urls.append(url)
                if instagram_urls:
                    instagram_username = instagram_urls[0].split("instagram.com/")[1].split("/")[0]
                    instagram_data["username"] = instagram_username
                    try:
                        profile = instaloader.Profile.from_username(L.context, instagram_username)
                        instagram_data["bio"] = profile.biography or "нет"
                        instagram_data["is_business"] = profile.is_business_account
                        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                        emails = re.findall(email_pattern, profile.biography)
                        instagram_data["email"] = emails[0] if emails else "не найдено"
                    except Exception as e:
                        instagram_data["error"] = f"Ошибка парсинга Instagram: {e}"
                else:
                    instagram_data["error"] = "Instagram-аккаунт не найден"
            except Exception as e:
                instagram_data["error"] = f"Ошибка веб-поиска Instagram: {e}"
        chats_data["instagram"] = instagram_data

        # 5. Поиск email и Google-аккаунта
        if target_username != "нет":
            try:
                query = f"from:@{target_username} gmail.com"
                for url in search(query, num_results=5):
                    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
                    emails = re.findall(email_pattern, url)
                    if emails and emails not in chats_data["email"]:
                        chats_data["email"].extend(emails)

                if instagram_data["email"] != "не найдено" and instagram_data["email"] not in chats_data["email"]:
                    chats_data["email"].append(instagram_data["email"])

                query = f"@{target_username} site:youtube.com | site:linkedin.com"
                for url in search(query, num_results=5):
                    if "youtube.com" in url or "linkedin.com" in url:
                        chats_data["google_account"].append(url)
            except Exception as e:
                await update.message.reply_text(f"Ошибка поиска email/Google-аккаунта: {e}")

        # 6. Веб-поиск упоминаний Telegram-username
        if target_username != "нет":
            try:
                web_results = []
                for url in search(f"site:t.me @{target_username}", num_results=10):
                    web_results.append(url)
                chats_data["web_mentions"] = web_results
            except Exception as e:
                await update.message.reply_text(f"Ошибка веб-поиска Telegram: {e}")

        # Сохранение данных
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file = os.path.join(OUTPUT_DIR, f"{target_username or target_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chats_data, f, ensure_ascii=False, indent=2)
        await update.message.reply_text(f"Данные сохранены в {output_file}")
    except Exception as e:
        await update.message.reply_text(f"Общая ошибка в функции find: {e}")

async def adminsearch(update, context):
    try:
        target = " ".join(context.args).strip()
        if not target:
            await update.message.reply_text("Укажи ID или username, например: /adminsearch @VictimUser")
            return

        await client.start()
        # Поиск Telegram-пользователя
        try:
            if target.isdigit():
                user = await client(GetFullUserRequest(id=int(target)))
            else:
                user = await client(GetFullUserRequest(id=target.lstrip('@')))
            user_data = user.users[0]
            target_id = user_data.id
            target_username = user_data.username or "нет"
            await update.message.reply_text(f"Найден Telegram-пользователь: ID={target_id}, Username=@{target_username}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка поиска Telegram-пользователя: {e}")
            return

        # Сбор данных об админских чатах
        admin_chats_data = {
            "telegram_user": {
                "id": target_id,
                "username": f"@{target_username}",
                "first_name": user_data.first_name or "",
                "last_name": user_data.last_name or ""
            },
            "admin_chats": [],
            "potential_admin_chats": [],
            "web_admin_mentions": [],
            "bots": []
        }

        # 1. Проверка чатов, где ты участник
        async for dialog in client.iter_dialogs():
            chat = dialog.entity
            chat_type = None
            is_private = False

            if isinstance(chat, Channel):
                if chat.megagroup:
                    chat_type = "supergroup"
                else:
                    chat_type = "channel"
                    is_private = bool(chat.access_hash)
            elif isinstance(chat, Chat):
                chat_type = "group"
                is_private = bool(chat.access_hash)
            else:
                continue

            is_admin = False
            is_owner = False
            participant_count = getattr(chat, "participants_count", None) or "неизвестно"

            try:
                # Проверка админов
                async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins, limit=10):
                    if admin.id == target_id:
                        is_admin = True
                        is_owner = getattr(admin, "creator", False)
                        break

                if is_admin or is_owner:
                    admin_chats_data["admin_chats"].append({
                        "title": chat.title,
                        "id": chat.id,
                        "username": getattr(chat, "username", None) or "нет",
                        "type": chat_type,
                        "participants_count": participant_count,
                        "is_private": is_private,
                        "is_owner": is_owner,
                        "is_admin": is_admin,
                        "source": "direct"
                    })

                # Анализ закреплённого сообщения
                pinned_message = await client.get_messages(chat, ids=chat.pinned_message_id) if getattr(chat, "pinned_message_id", None) else None
                if pinned_message and pinned_message.text:
                    if f"@{target_username}" in pinned_message.text.lower() or "admin" in pinned_message.text.lower() or "owner" in pinned_message.text.lower():
                        admin_chats_data["potential_admin_chats"].append({
                            "title": chat.title,
                            "id": chat.id,
                            "username": getattr(chat, "username", None) or "нет",
                            "type": chat_type,
                            "participants_count": participant_count,
                            "is_private": is_private,
                            "note": "Упоминание в закреплённом сообщении",
                            "pinned_message_text": pinned_message.text[:200]
                        })

                # Анализ сообщений
                async for message in client.iter_messages(chat, limit=100):
                    if message.text and f"@{target_username}" in message.text.lower() and ("admin" in message.text.lower() or "owner" in message.text.lower()):
                        admin_chats_data["potential_admin_chats"].append({
                            "title": chartitle,
                            "id": chat.id,
                            "username": getattr(chat, "username", None) or "нет",
                            "type": chat_type,
                            "participants_count": participant_count,
                            "is_private": is_private,
                            "note": "Упоминание как админ/владелец в сообщениях",
                            "message_text": message.text[:200]
                        })

                # Проверка ботов
                async for participant in client.iter_participants(chat, limit=100):
                    if getattr(participant, "bot", False):
                        bot_user = await client(GetFullUserRequest(participant.id))
                        bot_info = {
                            "id": participant.id,
                            "username": f"@{bot_user.users[0].username}" if bot_user.users[0].username else "нет",
                            "first_name": bot_user.users[0].first_name or "",
                            "last_name": bot_user.users[0].last_name or "",
                            "bio": bot_user.full_user.about or "нет",
                            "is_possible_admin": f"@{target_username}" in (bot_user.full_user.about or "").lower() or "admin" in (bot_user.full_user.about or "").lower()
                        }
                        admin_chats_data["bots"].append(bot_info)

            except Exception as e:
                if "admin privileges" in str(e).lower():
                    admin_chats_data["potential_admin_chats"].append({
                        "title": chat.title,
                        "id": chat.id,
                        "username": getattr(chat, "username", None) or "нет",
                        "type": chat_type,
                        "participants_count": participant_count,
                        "is_private": is_private,
                        "note": "Недостаточно прав для проверки админов",
                        "error": str(e)
                    })

        # 2. Публичные чаты через поиск
        try:
            search_query = f"@{target_username}" if target_username != "нет" else str(target_id)
            async for message in client.iter_messages(SearchGlobalRequest(
                q=search_query,
                filter=None,
                limit=50,
                from_id=None,
                peer=InputPeerEmpty()
            )):
                if hasattr(message, "peer_id") and hasattr(message.peer_id, "channel_id"):
                    chat_id = message.peer_id.channel_id
                    try:
                        chat = await client.get_entity(chat_id)
                        if isinstance(chat, Channel):
                            chat_type = "channel" if not chat.megagroup else "supergroup"
                            is_private = bool(chat.access_hash)

                            is_admin = False
                            is_owner = False
                            try:
                                async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins, limit=10):
                                    if admin.id == target_id:
                                        is_admin = True
                                        is_owner = getattr(admin, "creator", False)
                                        break
                            except Exception:
                                if message.text and f"@{target_username}" in message.text.lower() and ("admin" in message.text.lower() or "owner" in message.text.lower()):
                                    admin_chats_data["potential_admin_chats"].append({
                                        "title": chat.title,
                                        "id": chat.id,
                                        "username": getattr(chat, "username", None) or "нет",
                                        "type": chat_type,
                                        "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                                        "is_private": is_private,
                                        "note": "Упоминание как админ/владелец в сообщениях",
                                        "message_text": message.text[:200]
                                    })
                                continue

                            if is_admin or is_owner:
                                admin_chats_data["admin_chats"].append({
                                    "title": chat.title,
                                    "id": chat.id,
                                    "username": getattr(chat, "username", None) or "нет",
                                    "type": chat_type,
                                    "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                                    "is_private": is_private,
                                    "is_owner": is_owner,
                                    "is_admin": is_admin,
                                    "source": "global_search"
                                })

                            # Анализ закреплённого сообщения
                            pinned_message = await client.get_messages(chat, ids=chat.pinned_message_id) if getattr(chat, "pinned_message_id", None) else None
                            if pinned_message and pinned_message.text:
                                if f"@{target_username}" in pinned_message.text.lower() or "admin" in pinned_message.text.lower() or "owner" in pinned_message.text.lower():
                                    admin_chats_data["potential_admin_chats"].append({
                                        "title": chat.title,
                                        "id": chat.id,
                                        "username": getattr(chat, "username", None) or "нет",
                                        "type": chat_type,
                                        "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                                        "is_private": is_private,
                                        "note": "Упоминание в закреплённом сообщении",
                                        "pinned_message_text": pinned_message.text[:200]
                                    })

                    except Exception:
                        pass
        except Exception as e:
            await update.message.reply_text(f"Ошибка поиска публичных чатов: {e}")

        # 3. Приватные чаты по ссылкам
        try:
            await update.message.reply_text("Введите ссылки на приватные Telegram-чаты (t.me/+abc123), через пробел, или 'нет': ")
            invite_links = (await context.bot.wait_for('message', timeout=60)).text.split() if (await update.message.reply_text("Ожидаю ссылки...")).text != "нет" else []
            for link in invite_links:
                try:
                    await client(JoinChannelRequest(link))
                    chat = await client.get_entity(link)
                    is_private = bool(chat.access_hash)
                    chat_type = "channel" if isinstance(chat, Channel) and not chat.megagroup else "supergroup" if isinstance(chat, Channel) else "group"

                    is_admin = False
                    is_owner = False
                    try:
                        async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins, limit=10):
                            if admin.id == target_id:
                                is_admin = True
                                is_owner = getattr(admin, "creator", False)
                                break
                    except Exception as e:
                        admin_chats_data["potential_admin_chats"].append({
                            "title": chat.title,
                            "id": chat.id,
                            "username": getattr(chat, "username", None) or "нет",
                            "type": chat_type,
                            "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                            "is_private": is_private,
                            "note": "Недостаточно прав для проверки админов",
                            "error": str(e)
                        })
                        continue

                    if is_admin or is_owner:
                        admin_chats_data["admin_chats"].append({
                            "title": chat.title,
                            "id": chat.id,
                            "username": getattr(chat, "username", None) or "нет",
                            "type": chat_type,
                            "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                            "is_private": is_private,
                            "is_owner": is_owner,
                            "is_admin": is_admin,
                            "source": "invite_link"
                        })

                    # Анализ закреплённого сообщения
                    pinned_message = await client.get_messages(chat, ids=chat.pinned_message_id) if getattr(chat, "pinned_message_id", None) else None
                    if pinned_message and pinned_message.text:
                        if f"@{target_username}" in pinned_message.text.lower() or "admin" in pinned_message.text.lower() or "owner" in pinned_message.text.lower():
                            admin_chats_data["potential_admin_chats"].append({
                                "title": chat.title,
                                "id": chat.id,
                                "username": getattr(chat, "username", None) or "нет",
                                "type": chat_type,
                                "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                                "is_private": is_private,
                                "note": "Упоминание в закреплённом сообщении",
                                "pinned_message_text": pinned_message.text[:200]
                            })

                    # Проверка ботов
                    async for participant in client.iter_participants(chat, limit=100):
                        if getattr(participant, "bot", False):
                            bot_user = await client(GetFullUserRequest(participant.id))
                            bot_info = {
                                "id": participant.id,
                                "username": f"@{bot_user.users[0].username}" if bot_user.users[0].username else "нет",
                                "first_name": bot_user.users[0].first_name or "",
                                "last_name": bot_user.users[0].last_name or "",
                                "bio": bot_user.full_user.about or "нет",
                                "is_possible_admin": f"@{target_username}" in (bot_user.full_user.about or "").lower() or "admin" in (bot_user.full_user.about or "").lower()
                            }
                            admin_chats_data["bots"].append(bot_info)

                except Exception as e:
                    await update.message.reply_text(f"Ошибка обработки Telegram-ссылки {link}: {e}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка обработки ссылок на чаты: {e}")

        # 4. Веб-поиск упоминаний как админа
        if target_username != "нет":
            try:
                query = f"site:t.me @{target_username} admin"
                for url in search(query, num_results=10):
                    admin_chats_data["web_admin_mentions"].append({
                        "url": url,
                        "note": "Возможное упоминание как админ/владелец"
                    })
            except Exception as e:
                await update.message.reply_text(f"Ошибка веб-поиска админских упоминаний: {e}")

        # Сохранение данных
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file = os.path.join(OUTPUT_DIR, f"admin_{target_username or target_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(admin_chats_data, f, ensure_ascii=False, indent=2)
        await update.message.reply_text(f"Данные админских чатов сохранены в {output_file}")
    except Exception as e:
        await update.message.reply_text(f"Общая ошибка в функции adminsearch: {e}")

async def adminbychat(update, context):
    try:
        chat_target = " ".join(context.args).strip()
        if not chat_target:
            await update.message.reply_text("Укажи ID или username чата, например: /adminbychat @TechNews или /adminbychat 987654321")
            return

        await client.start()
        # Поиск чата
        try:
            if chat_target.startswith('@'):
                chat = await client.get_entity(chat_target)
            elif chat_target.isdigit():
                chat = await client.get_entity(int(chat_target))
            else:
                await update.message.reply_text("Неправильный формат. Используй @username или ID чата.")
                return
            chat_id = chat.id
            chat_title = chat.title
            chat_username = getattr(chat, "username", None) or "нет"
            await update.message.reply_text(f"Найден чат: {chat_title}, ID={chat_id}, Username=@{chat_username}")
        except Exception as e:
            await update.message.reply_text(f"Ошибка поиска чата: {e}")
            return

        # Сбор данных об админах
        chat_admin_data = {
            "chat": {
                "title": chat_title,
                "id": chat_id,
                "username": chat_username,
                "type": "supergroup" if isinstance(chat, Channel) and chat.megagroup else "channel" if isinstance(chat, Channel) else "group",
                "participants_count": getattr(chat, "participants_count", None) or "неизвестно",
                "is_private": bool(chat.access_hash)
            },
            "admins": [],
            "potential_admins": [],
            "bots": []
        }

        # Проверка админов
        try:
            async for admin in client.iter_participants(chat, filter=ChannelParticipantsAdmins, limit=50):
                admin_user = await client(GetFullUserRequest(admin.id))
                admin_data = {
                    "id": admin.id,
                    "username": f"@{admin_user.users[0].username}" if admin_user.users[0].username else "нет",
                    "first_name": admin_user.users[0].first_name or "",
                    "last_name": admin_user.users[0].last_name or "",
                    "is_owner": getattr(admin, "creator", False),
                    "is_admin": True
                }
                chat_admin_data["admins"].append(admin_data)

            # Анализ закреплённого сообщения
            pinned_message = await client.get_messages(chat, ids=chat.pinned_message_id) if getattr(chat, "pinned_message_id", None) else None
            if pinned_message and pinned_message.text:
                username_pattern = r"@[a-zA-Z0-9_]+"
                usernames = re.findall(username_pattern, pinned_message.text)
                for username in usernames:
                    try:
                        user = await client(GetFullUserRequest(username.lstrip('@')))
                        chat_admin_data["potential_admins"].append({
                            "id": user.users[0].id,
                            "username": f"@{user.users[0].username}" if user.users[0].username else "нет",
                            "first_name": user.users[0].first_name or "",
                            "last_name": user.users[0].last_name or "",
                            "note": "Упоминание в закреплённом сообщении",
                            "pinned_message_text": pinned_message.text[:200]
                        })
                    except Exception:
                        pass

            # Анализ сообщений
            async for message in client.iter_messages(chat, limit=100):
                if message.text and ("admin" in message.text.lower() or "owner" in message.text.lower()):
                    username_pattern = r"@[a-zA-Z0-9_]+"
                    usernames = re.findall(username_pattern, message.text)
                    for username in usernames:
                        try:
                            user = await client(GetFullUserRequest(username.lstrip('@')))
                            chat_admin_data["potential_admins"].append({
                                "id": user.users[0].id,
                                "username": f"@{user.users[0].username}" if user.users[0].username else "нет",
                                "first_name": user.users[0].first_name or "",
                                "last_name": user.users[0].last_name or "",
                                "note": "Упоминание как админ/владелец в сообщениях",
                                "message_text": message.text[:200]
                            })
                        except Exception:
                            pass

            # Проверка ботов
            async for participant in client.iter_participants(chat, limit=100):
                if getattr(participant, "bot", False):
                    bot_user = await client(GetFullUserRequest(participant.id))
                    bot_info = {
                        "id": participant.id,
                        "username": f"@{bot_user.users[0].username}" if bot_user.users[0].username else "нет",
                        "first_name": bot_user.users[0].first_name or "",
                        "last_name": bot_user.users[0].last_name or "",
                        "bio": bot_user.full_user.about or "нет",
                        "is_possible_admin": "admin" in (bot_user.full_user.about or "").lower() or "owner" in (bot_user.full_user.about or "").lower()
                    }
                    chat_admin_data["bots"].append(bot_info)

        except Exception as e:
            if "admin privileges" in str(e).lower():
                chat_admin_data["potential_admins"].append({
                    "note": "Недостаточно прав для проверки админов",
                    "error": str(e)
                })
            else:
                await update.message.reply_text(f"Ошибка проверки админов в чате {chat_title}: {e}")

        # Веб-поиск упоминаний админов
        try:
            query = f"site:t.me @{chat_username} admin" if chat_username != "нет" else f"site:t.me {chat_id} admin"
            for url in search(query, num_results=10):
                chat_admin_data["potential_admins"].append({
                    "url": url,
                    "note": "Возможное упоминание админов в веб-источниках"
                })
        except Exception as e:
            await update.message.reply_text(f"Ошибка веб-поиска админов для чата: {e}")

        # Сохранение данных
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file = os.path.join(OUTPUT_DIR, f"chat_admins_{chat_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(chat_admin_data, f, ensure_ascii=False, indent=2)
        await update.message.reply_text(f"Данные админов чата сохранены в {output_file}")
    except Exception as e:
        await update.message.reply_text(f"Общая ошибка в функции adminbychat: {e}")

def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("find", find))
        application.add_handler(CommandHandler("adminsearch", adminsearch))
        application.add_handler(CommandHandler("adminbychat", adminbychat))
        application.run_polling()
    except Exception as e:
        print(f"Ошибка в главном блоке: {e}")

if __name__ == "__main__":
    main()