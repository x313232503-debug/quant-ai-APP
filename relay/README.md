# QuantAI 天勤 TqSdk 中继（PaaS 一键部署）

容器版中继，凭证走环境变量（TQ_USER / TQ_PASS / PORT），不含任何内联账号。

## 部署（零终端）
1. 在 Render/Railway/Koyeb 用 GitHub 登录，连本仓库，选 Blueprint / Deploy。
2. 设置环境变量 TQ_USER、TQ_PASS（天勤账号），PORT 默认 8000。
3. 平台给公网 https 地址，填 App 设置 → 天勤 TqSdk 中继：`<地址>/verify`。

## 本地验证
```
pip install tqsdk
TQ_USER=xxx TQ_PASS=yyy python relay_server.py
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/verify?symbol=RB0"
```

完整说明见仓库内 quantai_relay_deploy/README.md
