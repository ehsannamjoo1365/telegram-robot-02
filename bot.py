#!/usr/bin/env python3
"""Independent Telegram bot. Configure BOT_TOKEN and OWNER_ID via environment."""
import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MODE = "automation"
API_BASE = "https://api.telegram.org/bot"
TOKEN = os.environ.get("BOT_TOKEN", "").strip()
OWNER_ID_RAW = os.environ.get("OWNER_ID", "").strip()
EXPECTED_USERNAME = os.environ.get("BOT_USERNAME", "").strip().lstrip("@")
STATE_FILE = Path(os.environ.get("BOT_STATE_FILE", "data/state.json"))
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("telegram-bot")

if not TOKEN:
    raise RuntimeError("Missing BOT_TOKEN environment variable.")
if not OWNER_ID_RAW.isdigit():
    raise RuntimeError("OWNER_ID must be your numeric Telegram user ID.")
OWNER_ID = int(OWNER_ID_RAW)


def api(method, payload=None):
    data = urllib.parse.urlencode(payload or {}).encode()
    request = urllib.request.Request(API_BASE + TOKEN + "/" + method, data=data)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Telegram API HTTP {exc.code}: {detail}") from exc
    if not result.get("ok"):
        raise RuntimeError("Telegram API error: " + str(result.get("description", "unknown error")))
    return result.get("result")


def send_message(chat_id, text, reply_to=None):
    payload = {"chat_id": str(chat_id), "text": str(text)[:4096]}
    if reply_to is not None:
        payload["reply_to_message_id"] = str(reply_to)
    return api("sendMessage", payload)


def parse_command(text, username):
    if not text or not text.startswith("/"):
        return None, ""
    parts = text.strip().split(maxsplit=1)
    command = parts[0][1:]
    if "@" in command:
        command, addressed_to = command.split("@", 1)
        if username and addressed_to.lower() != username.lower():
            return None, ""
    return command.lower(), parts[1] if len(parts) > 1 else ""


def load_state():
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        value = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {"destinations": []}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"destinations": []}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(STATE_FILE)


def is_owner(message):
    sender = message.get("from") or {}
    return sender.get("id") == OWNER_ID


def handle_robert(message, command, args, username):
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    if command == "start":
        send_message(chat_id, "سلام! من دستیار رابرت هستم. برای دیدن راهنما /help را بفرست.", message_id)
    elif command == "help":
        send_message(chat_id, "/start — شروع\n/about — معرفی ربات\n/support متن — ارسال درخواست پشتیبانی برای مدیر\n/id — شناسه گفتگو", message_id)
    elif command == "about":
        send_message(chat_id, "این ربات مستقلِ دستیار کاربران است. پاسخ‌های نسخه فعلی مبتنی بر فرمان‌های مشخص هستند و هنوز به مدل هوش مصنوعی متصل نیست.", message_id)
    elif command == "id":
        send_message(chat_id, f"شناسه این گفتگو: {chat_id}", message_id)
    elif command == "support":
        if not args.strip():
            send_message(chat_id, "لطفاً متن درخواست را بعد از /support بنویس.", message_id)
        else:
            api("sendMessage", {"chat_id": str(OWNER_ID), "text": f"درخواست پشتیبانی از کاربر {message.get('from', {}).get('id')}:\n{args[:3500]}"})
            send_message(chat_id, "درخواستت برای مدیر ارسال شد.", message_id)
    else:
        send_message(chat_id, "برای راهنمایی /help را بفرست. برای ارتباط با مدیر از /support متن استفاده کن.", message_id)


def handle_group(message, command, args):
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    if command == "start" or command == "help":
        send_message(chat_id, "ربات مدیریت گروه فعال است.\n/rules — قوانین گروه\n/id — شناسه گروه\n/start — راهنما", message_id)
    elif command == "rules":
        send_message(chat_id, "قوانین پایه: احترام متقابل، پرهیز از تبلیغات ناخواسته، عدم ارسال هرزنامه و رعایت قوانین گروه. مدیران گروه می‌توانند این متن را مطابق مقررات خود تغییر دهند.", message_id)
    elif command == "id":
        send_message(chat_id, f"شناسه گفتگو: {chat_id}", message_id)
    else:
        send_message(chat_id, "برای مشاهده فرمان‌ها /help را بفرست.", message_id)


def handle_automation(message, command, args):
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")
    if command in ("start", "help"):
        send_message(chat_id, "ربات اعلان و فرمان‌ها آماده است.\n/register_here — ثبت همین گروه (فقط مالک)\n/addchat CHAT_ID — افزودن مقصد (فقط مالک)\n/removechat CHAT_ID — حذف مقصد\n/destinations — فهرست مقصدها\n/notify متن — ارسال اعلان به مقصدهای ثبت‌شده", message_id)
        return
    if not is_owner(message):
        send_message(chat_id, "این فرمان فقط برای مالک ربات فعال است.", message_id)
        return
    state = load_state()
    targets = set(int(x) for x in state.get("destinations", []) if str(x).lstrip("-").isdigit())
    if command == "register_here":
        if (chat.get("type") not in ("group", "supergroup")):
            send_message(chat_id, "این فرمان را داخل گروه موردنظر اجرا کن.", message_id)
            return
        targets.add(int(chat_id))
        state["destinations"] = sorted(targets)
        save_state(state)
        send_message(chat_id, "این گروه به فهرست مقصدهای اعلان اضافه شد.", message_id)
    elif command == "addchat":
        if chat.get("type") != "private" or not args.strip():
            send_message(chat_id, "در گفت‌وگوی خصوصی از /addchat CHAT_ID استفاده کن.", message_id)
            return
        try:
            targets.add(int(args.strip().split()[0]))
            state["destinations"] = sorted(targets)
            save_state(state)
            send_message(chat_id, "مقصد ثبت شد. مطمئن شو ربات در آن گفتگو اجازه ارسال پیام دارد.", message_id)
        except ValueError:
            send_message(chat_id, "شناسه گفتگو باید عددی باشد.", message_id)
    elif command == "removechat":
        try:
            targets.discard(int(args.strip().split()[0]))
            state["destinations"] = sorted(targets)
            save_state(state)
            send_message(chat_id, "مقصد حذف شد.", message_id)
        except (ValueError, IndexError):
            send_message(chat_id, "فرمت: /removechat CHAT_ID", message_id)
    elif command == "destinations":
        send_message(chat_id, "مقصدهای ثبت‌شده:\n" + ("\n".join(map(str, sorted(targets))) if targets else "هیچ مقصدی ثبت نشده است."), message_id)
    elif command == "notify":
        if chat.get("type") != "private" or not args.strip():
            send_message(chat_id, "در گفت‌وگوی خصوصی از /notify متن اعلان استفاده کن.", message_id)
            return
        if not targets:
            send_message(chat_id, "هنوز مقصدی ثبت نشده است.", message_id)
            return
        sent, failed = 0, 0
        for target in sorted(targets):
            try:
                send_message(target, args[:4000])
                sent += 1
            except Exception:
                failed += 1
                log.exception("Notification failed for destination %s", target)
        send_message(chat_id, f"نتیجه ارسال: موفق {sent}، ناموفق {failed}.", message_id)
    elif command == "id":
        send_message(chat_id, f"شناسه گفتگو: {chat_id}", message_id)
    else:
        send_message(chat_id, "فرمان ناشناخته است. /help را ببین.", message_id)


def handle_update(update, username):
    message = update.get("message")
    if not message:
        return
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if MODE == "group" and message.get("new_chat_members"):
        names = [u.get("first_name", "دوست جدید") for u in message["new_chat_members"] if not u.get("is_bot")]
        if names:
            send_message(chat_id, "خوش آمدید " + "، ".join(names[:10]) + "! برای آشنایی با قوانین /rules را ببینید.")
        return
    text = message.get("text", "")
    command, args = parse_command(text, username)
    if not command:
        return
    if MODE == "robert":
        handle_robert(message, command, args, username)
    elif MODE == "group":
        handle_group(message, command, args)
    elif MODE == "automation":
        handle_automation(message, command, args)


def main():
    me = api("getMe")
    username = me.get("username", "")
    if EXPECTED_USERNAME and username.lower() != EXPECTED_USERNAME.lower():
        raise RuntimeError(f"BOT_USERNAME mismatch: token belongs to @{username}, but BOT_USERNAME is @{EXPECTED_USERNAME}.")
    log.info("Started independent %s bot as @%s (owner id configured)", MODE, username)
    offset = None
    while True:
        try:
            params = {"timeout": "30", "allowed_updates": json.dumps(["message"])}
            if offset is not None:
                params["offset"] = str(offset)
            updates = api("getUpdates", params)
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    handle_update(update, username)
                except Exception:
                    log.exception("Update %s failed", update.get("update_id"))
        except KeyboardInterrupt:
            log.info("Shutdown requested.")
            break
        except Exception:
            log.exception("Polling error; retrying in 5 seconds.")
            time.sleep(5)


if __name__ == "__main__":
    main()
