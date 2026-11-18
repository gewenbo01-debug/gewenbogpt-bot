# GewenboGPT Bot

Psychonaut Community 语言选择 bot（2026-11-18 重建，原宿主机丢失后重写）。

## 功能
- `[中文]` / `[English]` 持久按钮 → 分配对应语言身份组（互斥切换）
- `/welcome` — 在当前频道发布欢迎消息（需管理权限）
- `/langroles` — 列出服务器身份组（配 ZH_ROLE_NAME / EN_ROLE_NAME 用）
- `/ping` — 健康检查

## 部署
GitHub Actions 推镜像到 `ghcr.io/<owner>/gewenbogpt-bot:latest`，
Claw Cloud Run 容器拉取运行。环境变量：

| 变量 | 说明 |
|---|---|
| `DISCORD_TOKEN` | bot token（Claw secret，不入库） |
| `ZH_ROLE_NAME` | 中文身份组名，默认 `中文` |
| `EN_ROLE_NAME` | 英文身份组名，默认 `English` |
| `WELCOME_CHANNEL_ID` | 欢迎频道 ID，0=用命令所在频道 |
