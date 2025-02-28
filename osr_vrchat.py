import asyncio
import yaml, uuid, os, sys, traceback, time
from threading import Thread
from loguru import logger
import traceback
# import copy

from flask import Flask

from src.connector.osr_connector import OSRConnector
from src.handler.stroke_handler import StrokeHandler

from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher

app = Flask(__name__)

CONFIG_FILE_VERSION  = 'v0.1.0'
CONFIG_FILENAME = f'settings-advanced-{CONFIG_FILE_VERSION}.yaml'
CONFIG_FILENAME_BASIC = f'settings-{CONFIG_FILE_VERSION}.yaml'
connector = None

SETTINGS = {
    'SERVER_IP': None,
    'osr2':{     
        'objective': 'inserting_self', #self or others (inserting_self, inserting_others, inserted_pussy, inserted_ass)
        'max_pos':900,
        'min_pos':100,
        'max_velocity': 300,
        'updates_per_second': 40,
        'com_port':'COM4',
        'inserting_self': "/avatar/parameters/OGB/Pen/Dick/PenSelf",
        'inserting_others': "/avatar/parameters/OGB/Pen/Dick/PenOthers",
        'inserted_ass':"/avatar/parameters/OGB/Orf/Ass/PenOthers",
        'inserted_pussy': "/avatar/parameters/OGB/Orf/Pussy/PenOthers"
    },
    'version': CONFIG_FILE_VERSION,
    'ws':{
        'master_uuid': None,
        'listen_host': '0.0.0.0',
        'listen_port': 28846 
    },
    'osc':{
        'listen_host': '127.0.0.1',
        'listen_port': 9000,
    },
    'web_server':{
        'listen_host': '127.0.0.1',
        'listen_port': 8800
    },
    'log_level': 'INFO',
    'general': {
        'auto_open_qr_web_page': True,
        'local_ip_detect': {
            'host': '223.5.5.5',
            'port': 80,
        }
    }
}
SERVER_IP = None



async def async_main():
    global connector
    try:
        connector = OSRConnector(port=SETTINGS['osr2']['com_port'])
        await connector.connect()
        await connector.async_write_to_serial("L0100I500")
        time.sleep(1)
        await connector.async_write_to_serial("L0500I500")
        time.sleep(1)
        await connector.async_write_to_serial("L0900I500")
        logger.success("OSR设备自检成功")
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error("OSR设备连接失败，请检查串口地址是否正确，设备是否插紧")
        return

    for handler in handlers:
        handler.set_connector(connector)
    try: 
        server = AsyncIOOSCUDPServer((SETTINGS["osc"]["listen_host"], SETTINGS["osc"]["listen_port"]), dispatcher, asyncio.get_event_loop())
        logger.success(f'OSC Listening: {SETTINGS["osc"]["listen_host"]}:{SETTINGS["osc"]["listen_port"]}')
        transport, protocol = await server.create_serve_endpoint()
        await asyncio.Future()
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error("OSC UDP Recevier listen failed.")
        logger.error("OSC监听失败，可能存在端口冲突")
        return

    transport.close()

def async_main_wrapper():
    """Not async Wrapper around async_main to run it as target function of Thread"""
    asyncio.run(async_main())

def config_save():
    with open(CONFIG_FILENAME, 'w', encoding='utf-8') as fw:
        yaml.safe_dump(SETTINGS, fw, allow_unicode=True)
    
class ConfigFileInited(Exception):
    pass

def config_init():
    logger.info(f'Init settings..., Config filename: {CONFIG_FILENAME}, Config version: {CONFIG_FILE_VERSION}.')
    global SETTINGS, SETTINGS_BASIC, SERVER_IP
    if not (os.path.exists(CONFIG_FILENAME)):
        SETTINGS['ws']['master_uuid'] = str(uuid.uuid4())
        config_save()
        raise ConfigFileInited()

    with open(CONFIG_FILENAME, 'r', encoding='utf-8') as fr:
        SETTINGS = yaml.safe_load(fr)

    if SETTINGS.get('version', None) != CONFIG_FILE_VERSION:# or SETTINGS_BASIC.get('version', None) != CONFIG_FILE_VERSION:
        logger.error(f"Configuration file version mismatch! Please delete the {CONFIG_FILENAME} files and run the program again to generate the latest version of the configuration files.")
        raise Exception(f'配置文件版本不匹配！请删除 {CONFIG_FILENAME} 文件后再次运行程序，以生成最新版本的配置文件。')
    if SETTINGS['ws']['master_uuid'] is None:
        SETTINGS['ws']['master_uuid'] = str(uuid.uuid4())
        config_save()
    SERVER_IP = SETTINGS['SERVER_IP']# or get_current_ip()

    logger.remove()
    logger.add(sys.stderr, level=SETTINGS['log_level'])
    logger.success("The configuration file initialization is complete. The WebSocket service needs to listen for incoming connections. If a firewall prompt appears, please click Allow Access.")
    logger.success("配置文件初始化完成，Websocket服务需要监听外来连接，如弹出防火墙提示，请点击允许访问。")


def main():
    global dispatcher, handlers
    dispatcher = Dispatcher()
    handlers = []

    insert_params = SETTINGS['osr2'][SETTINGS['osr2']['objective']]

    stroke_handler = StrokeHandler(SETTINGS=SETTINGS)
    handlers.append(stroke_handler)

    target_param = insert_params#[SETTINGS['osr2']['objective']]
    logger.success(f"Listening：{target_param}")
    dispatcher.map(target_param, handlers[0].osc_handler)

    if SETTINGS['osr2']['objective'] not in ['inserting_others','inserting_self','inserted_ass','inserted_pussy']:
        logger.error("Wrong objective type!")


    th = Thread(target=async_main_wrapper, daemon=True)
    th.start()

    app.run(SETTINGS['web_server']['listen_host'], SETTINGS['web_server']['listen_port'], debug=False)

if __name__ == "__main__":
    try:
        config_init()
        main()
    except ConfigFileInited:
        logger.success('The configuration file initialization is complete. Please modify it as needed and restart the program.')
        logger.success('配置文件初始化完成，请按需修改后重启程序。')
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error("Unexpected Error.")
    
    logger.info('Exiting in 1 seconds ... Press Ctrl-C to exit immediately')
    logger.info('退出等待1秒 ... 按Ctrl-C立即退出')
    connector.disconnect()
    time.sleep(1)