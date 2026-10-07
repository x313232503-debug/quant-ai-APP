#!/usr/bin/env python3
# QuantAI 天勤 TqSdk 实时核验中继 · 容器/Paas 版（凭证走环境变量，不落库）
# 本地同机版见 quantai_tqsdk_relay.py（含内联账号，仅 127.0.0.1 用）。
# 部署：docker build + 运行，设置环境变量 TQ_USER / TQ_PASS / PORT。
# App 设置 → 天勤 TqSdk 中继 填： https://<你的公网地址>/verify

import os, json, time, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

TQ_USER = os.environ.get("TQ_USER", "")
TQ_PASS = os.environ.get("TQ_PASS", "")
PORT = int(os.environ.get("PORT", "8000"))

# 合约映射：App 主连代码(RB0/AU0/...) → TqSdk 主连符号(KQ.m@交易所.小写品种)
SYMBOL_MAP = {
    "AU0": "KQ.m@SHFE.au", "AG0": "KQ.m@SHFE.ag", "CU0": "KQ.m@SHFE.cu",
    "AL0": "KQ.m@SHFE.al", "ZN0": "KQ.m@SHFE.zn", "PB0": "KQ.m@SHFE.pb",
    "NI0": "KQ.m@SHFE.ni", "SN0": "KQ.m@SHFE.sn", "RB0": "KQ.m@SHFE.rb",
    "HC0": "KQ.m@SHFE.hc", "FU0": "KQ.m@SHFE.fu", "BU0": "KQ.m@SHFE.bu",
    "RU0": "KQ.m@SHFE.ru", "SP0": "KQ.m@SHFE.sp", "SS0": "KQ.m@SHFE.ss",
    "AO0": "KQ.m@SHFE.ao", "BR0": "KQ.m@SHFE.br",
    "SC0": "KQ.m@INE.sc", "NR0": "KQ.m@INE.nr", "BC0": "KQ.m@INE.bc", "LU0": "KQ.m@INE.lu",
    "A0": "KQ.m@DCE.a", "B0": "KQ.m@DCE.b", "M0": "KQ.m@DCE.m", "Y0": "KQ.m@DCE.y",
    "P0": "KQ.m@DCE.p", "C0": "KQ.m@DCE.c", "CS0": "KQ.m@DCE.cs", "JD0": "KQ.m@DCE.jd",
    "JM0": "KQ.m@DCE.jm", "J0": "KQ.m@DCE.j", "I0": "KQ.m@DCE.i", "L0": "KQ.m@DCE.l",
    "PP0": "KQ.m@DCE.pp", "V0": "KQ.m@DCE.v", "EG0": "KQ.m@DCE.eg", "EB0": "KQ.m@DCE.eb",
    "PG0": "KQ.m@DCE.pg", "LH0": "KQ.m@DCE.lh", "RR0": "KQ.m@DCE.rr",
    "CF0": "KQ.m@CZCE.cf", "SR0": "KQ.m@CZCE.sr", "OI0": "KQ.m@CZCE.oi", "RM0": "KQ.m@CZCE.rm",
    "TA0": "KQ.m@CZCE.ta", "MA0": "KQ.m@CZCE.ma", "FG0": "KQ.m@CZCE.fg", "SF0": "KQ.m@CZCE.sf",
    "SM0": "KQ.m@CZCE.sm", "UR0": "KQ.m@CZCE.ur", "SA0": "KQ.m@CZCE.sa", "PF0": "KQ.m@CZCE.pf",
    "PK0": "KQ.m@CZCE.pk", "SH0": "KQ.m@CZCE.sh", "PX0": "KQ.m@CZCE.px",
    "IF0": "KQ.m@CFFEX.if", "IH0": "KQ.m@CFFEX.ih", "IC0": "KQ.m@CFFEX.ic", "IM0": "KQ.m@CFFEX.im",
    "TF0": "KQ.m@CFFEX.tf", "T0": "KQ.m@CFFEX.t", "TS0": "KQ.m@CFFEX.ts", "TL0": "KQ.m@CFFEX.tl",
    "SI0": "KQ.m@GFEX.si", "LC0": "KQ.m@GFEX.lc",
    "SA_MAIN": "KQ.m@CZCE.sa", "SH_MAIN": "KQ.m@CZCE.sh",
    "SA_SEC": "KQ.m@CZCE.sa", "SH_SEC": "KQ.m@CZCE.sh",
}

cache = {}

def worker():
    from tqsdk import TqApi, TqAuth
    if not TQ_USER or not TQ_PASS:
        print("WARNING: TQ_USER/TQ_PASS 未设置，relay 不会出价")
        return
    api = TqApi(auth=TqAuth(TQ_USER, TQ_PASS))
    quotes = {a: api.get_quote(t) for a, t in SYMBOL_MAP.items()}
    while True:
        api.wait_update()
        for a, q in quotes.items():
            cache[a] = {"price": q.last_price, "ts": int(time.time() * 1000)}

threading.Thread(target=worker, daemon=True).start()

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p == "/health":
            return self._send(200, {"ok": True, "symbols": len(cache), "auth": bool(TQ_USER)})
        if p == "/verify" or p.startswith("/verify"):
            sym = parse_qs(urlparse(self.path).query).get("symbol", [""])[0]
            if sym not in SYMBOL_MAP:
                return self._send(404, {"error": "unknown_symbol", "symbol": sym})
            return self._send(200, cache.get(sym, {}))
        self.send_response(404); self.end_headers()
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    print(f"TqSdk relay container on 0.0.0.0:{PORT}")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
