# QQ Bot Agent

基于 qq-botpy + LangGraph 的 QQ 机器人，支持群聊、私聊和上下文压缩。

## 功能

- 频道 @ 消息回复
- 频道私信回复
- QQ 一对一私聊 (C2C)
- QQ 群 @ 消息回复
- 多轮对话记忆
- 上下文自动压缩

## 安装

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，填写配置：

```env
QQ_APPID=your_appid
QQ_SECRET=your_secret
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

## 运行

```bash
python main.py
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `MAX_HISTORY` | 20 | 最大保留消息数 |
| `COMPRESS_THRESHOLD` | 15 | 触发压缩的阈值 |
| `COMPRESS_KEEP_RECENT` | 6 | 压缩时保留的最近消息数 |
