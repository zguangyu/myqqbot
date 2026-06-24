"""QQ机器人主程序 - 使用qq-botpy + LangGraph"""
import os
import re
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv
import botpy
from botpy.message import Message, DirectMessage, C2CMessage, GroupMessage
from chat_agent import ChatAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

load_dotenv()

QQ_APPID = os.getenv("QQ_APPID")
QQ_SECRET = os.getenv("QQ_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")


def handle_command(content: str, agent: ChatAgent) -> str:
    if not content.startswith("/"):
        return None

    parts = content.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        model_list = "\n".join([f"  - {m}" for m in agent.get_model_list()])
        return (
            "可用命令：\n"
            "/help - 显示此帮助\n"
            "/model - 列出可用模型\n"
            "/model <模型名> - 切换模型\n"
            f"\n当前模型：{agent.get_current_model()}\n"
            f"可用模型：\n{model_list}"
        )

    elif cmd == "/model":
        if not args:
            models = agent.get_model_list()
            current = agent.get_current_model()
            model_list = "\n".join([f"  - {'✓ ' if m == current else ''}{m}" for m in models])
            return f"当前模型：{current}\n可用模型：\n{model_list}"

        if agent.switch_model(args):
            return f"已切换到模型：{args}"
        else:
            return f"未找到模型：{args}\n可用模型：{', '.join(agent.get_model_list())}"

    return None


class MyClient(botpy.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = ChatAgent(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            model_name=MODEL_NAME,
        )

    async def on_ready(self):
        print(f"机器人 [{self.robot.name}] 已上线!")

    async def _handle_message(self, message, msg_type: str):
        content = message.content.strip()
        content = re.sub(r"<@!?\d+>", "", content).strip()

        logger.info(f"收到{msg_type}消息 | 频道:{message.channel_id} | 发送者:{message.author} | 内容:{content}")

        if not content:
            await message.reply(content="请输入消息内容")
            return

        # 处理命令
        cmd_reply = handle_command(content, self.agent)
        if cmd_reply:
            await message.reply(content=cmd_reply)
            return

        thread_id = f"{msg_type}_{message.channel_id}"
        try:
            reply = await self.agent.chat(content, thread_id)
            logger.info(f"发送回复 | 频道:{message.channel_id} | 回复:{reply[:100]}...")
            await message.reply(content=reply)
        except Exception as e:
            logger.error(f"处理消息出错: {e}")
            await message.reply(content="处理消息时出错，请稍后重试")

    async def on_at_message_create(self, message: Message):
        await self._handle_message(message, "guild")

    async def on_direct_message_create(self, message: DirectMessage):
        await self._handle_message(message, "dms")

    async def on_c2c_message_create(self, message: C2CMessage):
        content = message.content.strip()
        logger.info(f"收到C2C消息 | 发送者:{message.author} | 内容:{content}")

        # 处理命令
        cmd_reply = handle_command(content, self.agent)
        if cmd_reply:
            await message.reply(content=cmd_reply)
            return
        
        thread_id = f"c2c_{message.author.user_openid}"
        try:
            reply = await self.agent.chat(content, thread_id)
            logger.info(f"发送C2C回复 | 回复:{reply[:100]}...")
            await message.reply(content=reply)
        except Exception as e:
            logger.error(f"处理C2C消息出错: {type(e).__name__}: {e}", exc_info=True)
            await message.reply(content="处理消息时出错，请稍后重试")

    async def on_group_at_message_create(self, message: GroupMessage):
        content = message.content.strip()
        content = re.sub(r"<@!?\d+>", "", content).strip()
        logger.info(f"收到群消息 | 群:{message.group_openid} | 内容:{content}")

        # 处理命令
        cmd_reply = handle_command(content, self.agent)
        if cmd_reply:
            await message.reply(content=cmd_reply)
            return
        
        thread_id = f"group_{message.group_openid}"
        try:
            reply = await self.agent.chat(content, thread_id)
            await message.reply(content=reply)
        except Exception as e:
            logger.error(f"处理群消息出错: {e}")


def main():
    if not all([QQ_APPID, QQ_SECRET, OPENAI_API_KEY, OPENAI_BASE_URL]):
        raise ValueError("请在.env文件中配置必要的环境变量")

    intents = botpy.Intents(public_messages=True, guild_messages=True, direct_message=True)
    client = MyClient(intents=intents)
    client.run(appid=QQ_APPID, secret=QQ_SECRET)


if __name__ == "__main__":
    main()
