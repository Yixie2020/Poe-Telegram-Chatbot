import os
import asyncio
import logging
import fastapi_poe as fp
from configparser import ConfigParser
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction
from telegram.error import BadRequest

# 读取配置文件
config = ConfigParser()
config.read('config.ini')

# 获取配置项
TELEGRAM_BOT_TOKEN = config.get('telegram', 'bot_token')
POE_API_KEY = config.get('poe', 'api_key')
ADMIN_ID = int(config.get('telegram', 'admin_id'))
WHITELIST_FILE = config.get('telegram', 'whitelist_file')

bot_names = {
    'gpt4': 'GPT-4',
    'claude3': 'Claude-3-Opus'
}
default_bot_name = bot_names['claude3']
user_tasks = {}
user_context = {}

# 加载白名单
whitelist = set()
if os.path.exists(WHITELIST_FILE):
    with open(WHITELIST_FILE, 'r') as f:
        whitelist = set(int(line.strip()) for line in f)
        
async def get_responses(api_key, messages, response_list, done, bot_name):
    async for chunk in fp.get_bot_response(messages=messages, bot_name=bot_name, api_key=api_key):
        response_list.append(chunk.text)
    done.set()
    
async def update_telegram_message(update, context, response_list, done, response_text, update_interval=1):
    response_message = None
    last_response_text = ""

    while not done.is_set():
        if response_list:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

            response_text[0] += "".join(response_list)
            response_list.clear()

            if response_text[0].strip() != last_response_text.strip():
                response_message = await send_response_message(context, update.effective_chat.id, response_text[0], response_message)
                last_response_text = response_text[0]

        await asyncio.sleep(update_interval)

    if response_list:
        response_text[0] += "".join(response_list)
        response_list.clear()

        if response_text[0].strip() != last_response_text.strip():
            await send_response_message(context, update.effective_chat.id, response_text[0], response_message)

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in whitelist:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="您没有权限使用此机器人,请联系管理员添加白名单。")
        return

    logging.info(f"开始处理用户 {user_id} 的请求")
    user_input = update.message.text
    message = {"role": "user", "content": user_input}

    # 获取用户上下文
    if user_id not in user_context:
        user_context[user_id] = {'messages': [message], 'bot_name': default_bot_name}
    else:
        user_context[user_id]['messages'].append(message)

    # 检查用户是否已有对应的任务,如果没有则创建一个新任务
    if user_id not in user_tasks or user_tasks[user_id].done():
        user_tasks[user_id] = asyncio.create_task(handle_user_request(user_id, update, context))

async def handle_user_request(user_id, update, context):
    if user_id in user_context and user_context[user_id]['messages']:
        response_list = []
        done = asyncio.Event()
        response_text = [""]
        
        try:
            api_task = asyncio.create_task(get_responses(POE_API_KEY, user_context[user_id]['messages'], response_list, done, user_context[user_id]['bot_name']))
            telegram_task = asyncio.create_task(update_telegram_message(update, context, response_list, done, response_text))

            await asyncio.gather(api_task, telegram_task)

            # Add the bot's response to the context
            user_context[user_id]['messages'].append({"role": "bot", "content": response_text[0]})
        except Exception as e:
            logging.exception(f"处理用户 {user_id} 请求时发生异常: {str(e)}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="很抱歉,处理您的请求时发生错误。")

async def send_response_message(context, chat_id, response_text, response_message=None):
    if response_text.strip():
        try:
            if response_message is None:
                response_message = await context.bot.send_message(chat_id=chat_id, text=response_text, parse_mode="Markdown")
            else:
                await response_message.edit_text(response_text, parse_mode="Markdown")
        except BadRequest:
            if response_message is None:
                response_message = await context.bot.send_message(chat_id=chat_id, text=response_text)
            else:
                await response_message.edit_text(response_text)
    return response_message

async def start(update: Update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="欢迎使用Poe AI助手! 请输入您的问题。[Write by Claude-3-Opus-200k]")

async def new_conversation(update: Update, context):
    user_id = update.effective_user.id
    bot_name = default_bot_name
    if user_id in user_context:
        bot_name = user_context[user_id]['bot_name']
        user_context[user_id] = {'messages': [], 'bot_name': bot_name}
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"====== 新的对话开始（{bot_name}） ======")

async def gpt4(update: Update, context):
    user_id = update.effective_user.id
    bot_name = bot_names['gpt4']
    await switch_model(user_id, bot_name, update, context)

async def claude3(update: Update, context):
    user_id = update.effective_user.id
    bot_name = bot_names['claude3']
    await switch_model(user_id, bot_name, update, context)

async def switch_model(user_id, bot_name, update, context):
    if user_id not in user_context or user_context[user_id]['bot_name'] != bot_name:
        user_context[user_id] = {'messages': [], 'bot_name': bot_name}
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"已切换到 {bot_name} 模型,并清空上下文。")
        await new_conversation(update, context)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"当前已经是 {bot_name} 模型。")

async def add_whitelist(update: Update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="您没有权限执行此操作。")
        return

    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="请提供要添加到白名单的用户ID。")
        return

    try:
        new_user_id = int(context.args[0])
        whitelist.add(new_user_id)
        with open(WHITELIST_FILE, 'a') as f:
            f.write(f"{new_user_id}\n")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"已将用户 {new_user_id} 添加到白名单。")
    except ValueError:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="无效的用户ID。")

async def del_whitelist(update: Update, context):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="您没有权限执行此操作。")
            return

        if not context.args:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="请提供要从白名单移除的用户ID，格式为add userid")
            return

        try:
            remove_user_id = int(context.args[0])
            if remove_user_id in whitelist:
                whitelist.remove(remove_user_id)
                with open(WHITELIST_FILE, 'w') as f:
                    f.write("\n".join(str(uid) for uid in whitelist))
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"已将用户 {remove_user_id} 从白名单移除。")
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"用户 {remove_user_id} 不在白名单中。")
        except ValueError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="无效的用户ID。")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    new_handler = CommandHandler('new', new_conversation)
    application.add_handler(new_handler)

    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    application.add_handler(message_handler)

    gpt4_handler = CommandHandler('gpt4', gpt4)
    application.add_handler(gpt4_handler)

    claude3_handler = CommandHandler('claude3', claude3)
    application.add_handler(claude3_handler)

    add_whitelist_handler = CommandHandler('add', add_whitelist)
    application.add_handler(add_whitelist_handler)

    del_whitelist_handler = CommandHandler('del', del_whitelist)
    application.add_handler(del_whitelist_handler)

    # 运行
    application.run_polling()

if __name__ == '__main__':
    main()
