import os
import subprocess
import requests
import telebot
from telebot import apihelper, BaseMiddleware, CancelUpdate, SkipHandler
from telebot import types
import shutil
import traceback as tb
import time
import yaml
from config import config
import threading
from logger import log
from server import Server

event_lock = threading.Lock()

cfg = config("config.yaml")

# Replace with your own bot token
TOKEN = 'token'

# Set the path to the Factorio server directory
FACTORIO_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'server')

# Create a bot instance
bot = telebot.TeleBot(TOKEN, use_class_middlewares=True)

server = None

# Define the commands that the bot will check authorization
allows = ['/auth', '/id', '/help','/start']

working = False

# Authorization Middleware
class Middleware(BaseMiddleware):
    def __init__(self):
        self.update_types = ['message']

    def pre_process(self, msg, data):
        global working
        if msg.text is not None:
            log.bot(f'User[{msg.from_user.username}]: Run Command "{msg.text}"')
            for allow in allows:
                if msg.text.startswith(allow):
                    return
        else:
            log.bot(f'User[{msg.from_user.username}]: Received File "{msg.document.file_name}"')
        if working:
            bot.send_message(msg.chat.id,"Processing other mission, please wait ...")
            return SkipHandler()
        working = True
        id = msg.from_user.id
        if cfg.config['auth_id'] is None or id not in cfg.config['auth_id']:
            bot.send_message(
                msg.from_user.id, "Not Authorized, use /auth [password] to get authorization")
            log.error(f"Unauthorized Requeest From:\n{msg}")
            for admin in cfg.config["admin"]:
                bot.send_message(
                    admin, f'{time.asctime( time.localtime(time.time()) )}:[ System ]: Unauthorized Request From:\n{msg.from_user}')
            return SkipHandler()

    def post_process(self, msg, data, e=None):
        global working
        working = False


bot.setup_middleware(Middleware())


# Message Handlers

@bot.message_handler(commands=['id'])
def status(msg):
    bot.send_message(msg.from_user.id)


@bot.message_handler(commands=['auth'])
def auth(msg):
    if len(msg.text.split()) != 2:
        bot.send_message(msg.chat.id, "/auth [password]")
        return
    if msg.text.split()[1] != cfg.config['password']:
        bot.send_message(msg.chat.id, "Wrong Password")
        return
    if cfg.config["auth_id"] is not None:
        cfg.config["auth_id"].append(msg.chat.id)
    else:
        cfg.config["auth_id"] = [msg.chat.id]
    cfg.save()
    bot.send_message(msg.chat.id, "Authorized")


@bot.message_handler(commands=['status'])
def status(msg):
    process = server is not None
    bot.send_message(msg.chat.id, "Running" if process else "Sleeping")
    


def start_server(id, port=34197):
    global server
    if server is not None:
        bot.send_message(id, 'Server is already running')
        return
    bot.send_message(id, 'Starting Factorio server...')
    server = Server(port)
    res = server.awake()
    if res == -1:
        bot.send_message(id, 'Server is already running')
    else:
        bot.send_message(id, 'Server Started')


def stop_server(id):
    global server
    print(server)
    if server is None:
        bot.send_message(id, 'Server is not running')
    else:
        bot.send_message(id, 'Server stopping ...')
        res = server.stop()
        if res == -1:
            bot.send_message(id, 'Server is not running')
        else:
            bot.send_message(id, 'Server Stopped')
        server = None


@bot.message_handler(commands=['server'])
def server_command(message):
    try:
        if message.text == '/server start':
            port = None
            if len(message.text.split()) > 2:
                port: str = message.text.split()[2]
                if not port.isdigit:
                    bot.send_message(message.chat.id, "Invalid Port!")
                    return
                start_server(message.chat.id, int(port))
            else:
                start_server(message.chat.id)
        elif message.text == '/server stop':
            stop_server(message.chat.id)
        else:
            bot.send_message(
                message.chat.id, '''server start [?port] : to start server\nserver stop : to stop server''')
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['ls'])
def ls_command(message):
    try:
        # List the save files in the saves directory
        saves = [s for s in os.listdir(os.path.join(
            FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        # Format the response message
        message_text = 'Saves list:\n'
        for i, save in enumerate(saves):
            message_text += f'slot #{i+1} - {save}\n'
        # Send a response to the user
        bot.send_message(message.chat.id, message_text)
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['export'])
def export(message):
    try:
        if len(message.text.split())!=2:
            bot.send_message(message.chat.id, "Invalid argument. try /export [slot]")
            return
        slot:str = message.text.split()[1]
        if not slot.isdigit():
            bot.send_message(message.chat.id, "slot must be a number")
            return
        slot = int(slot)
        saves = [s for s in os.listdir(os.path.join(
                FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        
        with open(os.path.join(
                FACTORIO_DIR, 'saves',saves[slot-1]), 'rb') as f:
            bot.send_document(message.chat.id, f)
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['reload'])
def reload(message):
    global server
    try:
        if len(message.text.split()) != 2:
            bot.send_message(message.chat.id,'Invalid argument. try /relaod [slot]')
        # Get the selected save file
        slot = message.text.split()[1]
        saves = [s for s in os.listdir(os.path.join(
            FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        if not slot.isdigit():
            bot.send_message(message.chat.id, f'slot should be num!')
            return
        slot = int(slot)
        if len(saves) < slot:
            bot.send_message(message.chat.id, f'Invalid slot: {slot}')
            return
        save_file = saves[slot-1]
        save_path = os.path.join(FACTORIO_DIR, 'saves', save_file)
        if server is not None:
            stop_server(message.chat.id)

            # Replace the current save file with the selected save file
            current_save_path = os.path.join(FACTORIO_DIR, 'saves', 'sss.zip')
            os.replace(save_path, current_save_path)
            shutil.copy(save_path,current_save_path)

            # Start the Factorio server subprocess
            start_server(message.chat.id)
        else:
            current_save_path = os.path.join(FACTORIO_DIR, 'saves', 'sss.zip')
            shutil.copy(save_path,current_save_path)
        # Send a response to the user
        bot.send_message(
            message.chat.id, f'Reload save file {save_file} successful')
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['save'])
def save(message):
    global server
    try:
        if len(message.text.split()) != 2:
            bot.send_message(message.chat.id, 'Invalid argument. try /save [filename]')
            return
        name = message.text.split()[1]
        if server is None:
            shutil.copyfile(os.path.join(FACTORIO_DIR, 'saves', 'sss.zip'), os.path.join(
                FACTORIO_DIR, 'saves', f'{name}.zip'))
            bot.send_message(message.chat.id, 'Saving complete')
            saves = [s for s in os.listdir(os.path.join(
                FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
            # Format the response message
            message_text = 'Saves list:\n'
            for i, save in enumerate(saves):
                message_text += f'slot #{i+1} - {save}\n'
            # Send a response to the user
            bot.send_message(message.chat.id, message_text)
            return
        bot.send_message(message.chat.id, 'Start saving ...')
        res = server.save()
        if res == -1:
            bot.send_message(
                message.chat.id, 'Other saving progress is running')
        else:
            shutil.copyfile(os.path.join(FACTORIO_DIR, 'saves', 'sss.zip'), os.path.join(
                FACTORIO_DIR, 'saves', f'{name}.zip'))
            bot.send_message(message.chat.id, 'Saving complete')
            saves = [s for s in os.listdir(os.path.join(
                FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
            # Format the response message
            message_text = 'Saves list:\n'
            for i, save in enumerate(saves):
                message_text += f'slot #{i+1} - {save}\n'
            # Send a response to the user
            bot.send_message(message.chat.id, message_text)
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['cp'])
def bk(message):
    try:
        if len(message.text.split()) != 3:
            bot.send_message(message.chat.id, f'Invalid argument. try /bk [slot] [newname]')
            return
        slot = message.text.split()[1]
        saves = [s for s in os.listdir(os.path.join(
            FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        if not slot.isdigit():
            bot.send_message(message.chat.id, f'slot should be num!')
            return
        slot = int(slot)
        if len(saves) < slot:
            bot.send_message(message.chat.id, f'Invalid slot: {slot}')
            return
        save_file = saves[slot-1]
        save_path = os.path.join(FACTORIO_DIR, 'saves', save_file)
        name = message.text.split()[2]
        shutil.copyfile(save_path, os.path.join(
            FACTORIO_DIR, 'saves', f'{name}.zip'))
        bot.send_message(message.chat.id, 'backup success')
        saves = [s for s in os.listdir(os.path.join(
            FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        # Format the response message
        message_text = 'Saves list:\n'
        for i, save in enumerate(saves):
            message_text += f'slot #{i+1} - {save}\n'
        # Send a response to the user
        bot.send_message(message.chat.id, message_text)
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['rm'])
def remove(message):
    try:
        if len(message.text.split()) != 2:
            bot.send_message(message.chat.id, f'Invalid argument. try /rm [slot]')
            return
        slot = message.text.split()[1]
        saves = [s for s in os.listdir(os.path.join(
            FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        if not slot.isdigit():
            bot.send_message(message.chat.id, f'slot should be num!')
            return
        slot = int(slot)
        if len(saves) < slot:
            bot.send_message(message.chat.id, f'Invalid slot: {slot}')
            return
        save_file = saves[slot-1]
        save_path = os.path.join(FACTORIO_DIR, 'saves', save_file)
        os.remove(save_path)
        bot.send_message(message.chat.id, "Delete success")
        saves = [s for s in os.listdir(os.path.join(
            FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
        # Format the response message
        message_text = 'Saves list:\n'
        for i, save in enumerate(saves):
            message_text += f'slot #{i+1} - {save}\n'
        # Send a response to the user
        bot.send_message(message.chat.id, message_text)
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")


@bot.message_handler(commands=['help'])
def common(msg):
    bot.send_message(msg.chat.id,
                     'Use this bot to manage your factorio server:\n'
                     'Command List:\n'
                     '/server\n'
                     '      start [?port] - Start server [port is optinal]\n'
                     '      stop - stop server\n'
                     '/ls - show saves list\n'
                     '/reload [slot] - reload saves in slot\n'
                     '/cp [slot] [name] - backup a slot with new name(no extension)\n'
                     '/rm [slot] - remove saves file in slot\n'
                     '/export [slot] - export saves file from slot\n'
                     '/save [name] - save current game save immediately'
                     '/auth [password] - get authorization\n'
                     '/help - show help menu\n'
                     '/id - get user id\n'
                     '/status - get server status\n'
                     '[file] - Upload your file')


@bot.message_handler(content_types=['document'])
def handle_zip_file(message):
    try:
        if message.document.mime_type == 'application/zip':
            bot.send_message(message.chat.id, f"Received {message.document.file_name}, processing ...")
            saves = [s for s in os.listdir(os.path.join(
                FACTORIO_DIR, 'saves')) if s.endswith('.zip')]
            if message.document.file_name in saves:
                bot.send_message(message.chat.id,"Dupelicate File Name")
                return
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path
            file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_path}'
            
            # download the ZIP file from the URL
            response = requests.get(file_url, stream=True)
            # copy the ZIP file to the destination path
            with open(os.path.join(FACTORIO_DIR, 'saves',message.document.file_name), 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            bot.send_message(message.chat.id, f'Saves received!')
            saves = [s for s in os.listdir(os.path.join(
                FACTORIO_DIR, 'saves')) if s.endswith('.zip') and s != "sss.zip"]
            # Format the response message
            message_text = 'Saves list:\n'
            for i, save in enumerate(saves):
                message_text += f'slot #{i+1} - {save}\n'
            # Send a response to the user
            bot.send_message(message.chat.id, message_text)
        else:
            bot.send_message(message.chat.id, f'File type not supported')
    except Exception as e:
        trace = ''.join(
            tb.format_exception(None, e, e.__traceback__))
        bot.send_message(message.chat.id, trace)
        log.error(f"bot: {trace}")

@bot.message_handler(commands=['start'])
def welcome(msg):
    bot.send_message(msg.chat.id,'welcome! try /help to get command list')
    if cfg.config['auth_id'] is None or msg.chat.id not in cfg.config['auth_id']:
        bot.send_message(msg.chat.id,'Not authorized, use /auth [password] to get authorization first')


@bot.message_handler()
def common(msg):
    bot.send_message(msg.chat.id,
                     "Unknow command, use /help to show command info")


# Start the bot

print("Bot Listening...")
bot.polling()
