在参考了提供的 README 文件后,我对其进行了一些修改和扩充,以更好地描述你的 Poe AI Telegram 机器人的功能和使用方法。下面是修改后的 README 文件:

# Poe AI Telegram 机器人

这是一个与 Poe AI API 集成的 Telegram 机器人,允许用户通过 Telegram 与 GPT-4 和 Claude-3-Opus 等 AI 模型进行交互。该机器人支持多个用户,并为每个用户维护对话上下文。

## 功能特点

- 与 GPT-4 和 Claude-3-Opus AI 模型进行对话
- 为每个用户维护对话上下文,实现连续对话
- 使用命令在不同的 AI 模型之间切换
- 用户白名单以进行访问控制
- 管理员命令以管理白名单
- 支持 Docker 容器化部署

## 安装与运行

### 前置要求

- Python 3.7+ (经过测试)
- `python-telegram-bot` 库
- `fastapi_poe` 库
- [Poe API 密钥](https://poe.com/api_key)
- Telegram 机器人令牌 (通过 BotFather 获取)

### 本地运行

1. 克隆此仓库:
   ```bash
   git clone https://github.com/yourusername/poe-ai-telegram-bot.git
   cd poe-ai-telegram-bot
   ```

2. 安装依赖:
   ```bash
   pip3 install -r requirements.txt
   ```

3. 修改 `config.ini` 文件,内容如下:
   ```
   [telegram]
   bot_token = YOUR_TELEGRAM_BOT_TOKEN  ## 创建的Telegram Bot的Token
   admin_id = YOUR_TELEGRAM_USER_ID  ## 管理员用户ID
   whitelist_file = whitelist.txt

   [poe]
   api_key = YOUR_POE_API_KEY  ## Poe的api key
   ```

   将 `YOUR_TELEGRAM_BOT_TOKEN`、`YOUR_TELEGRAM_USER_ID` 和 `YOUR_POE_API_KEY` 替换为您的实际值。

4. 运行机器人:
   ```bash 
   python3 bot.py
   ```

### Docker 运行

1. 修改 `config.ini` 文件,内容如下:
   ```
   [telegram]
   bot_token = YOUR_TELEGRAM_BOT_TOKEN  ## 创建的Telegram Bot的Token
   admin_id = YOUR_TELEGRAM_USER_ID  ## 管理员用户ID
   whitelist_file = whitelist.txt

   [poe]
   api_key = YOUR_POE_API_KEY  ## Poe的api key
   ```

   将 `YOUR_TELEGRAM_BOT_TOKEN`、`YOUR_TELEGRAM_USER_ID` 和 `YOUR_POE_API_KEY` 替换为您的实际值。

2. 运行 Docker 容器:
   ```bash
   docker run -d --name poebot \
     -e TELEGRAM_BOT_TOKEN="your_telegram_bot_token" \
     -e POE_API_KEY="your_poe_api_key" \
     -v /path/to/whitelist.txt:/app/whitelist.txt \
     yourusername/poe-ai-telegram-bot
   ```

   注意将 `your_telegram_bot_token` 和 `your_poe_api_key` 替换为你自己的令牌和 API 密钥,并将 `/path/to/whitelist.txt` 替换为主机上白名单文件的实际路径。

## 使用方法

- `/start` - 开始与机器人对话
- `/new` - 开始一个新的对话,清空上下文 
- `/gpt4` - 切换到 GPT-4 模型
- `/claude3` - 切换到 Claude-3-Opus 模型

直接在聊天界面输入问题,机器人就会自动回复。

## 管理员命令

- 将用户添加到白名单: `/add USER_ID`
- 从白名单中删除用户: `/del USER_ID`  
