import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")

def get_risk_score(warnings):
    return max(100 - len(warnings) * 20, 10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Welcome to RugGuard Bot!\n\n"
        "Send any Ethereum token contract address and I'll instantly scan it for:\n"
        "• Honeypot detection\n"
        "• Buy/Sell tax\n"
        "• Liquidity lock status\n"
        "• Dev wallet %\n"
        "• Risk score\n\n"
        "Example:\n0xdAC17F958D2ee523a2206206994597C13D831ec7"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()

    if not address.startswith("0x") or len(address) < 40:
        await update.message.reply_text("❌ Please send a valid contract address starting with 0x")
        return

    await update.message.reply_text("🔍 Scanning token... please wait")

    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/1?contract_addresses={address}"
        response = requests.get(url, timeout=10)
        data = response.json()
        token = data.get("result", {}).get(address.lower())

        if not token:
            await update.message.reply_text("⚠️ Token not found. Make sure it's an Ethereum contract.")
            return

        warnings = []
        if token.get("is_honeypot") == "1":
            warnings.append("🚨 Honeypot detected")
        if float(token.get("buy_tax") or 0) > 10:
            warnings.append("💸 High buy tax")
        if float(token.get("sell_tax") or 0) > 10:
            warnings.append("💸 High sell tax")
        if token.get("lp_locked") == "0":
            warnings.append("🔓 Liquidity not locked")
        if float(token.get("owner_percent") or 0) > 20:
            warnings.append("👛 Dev holds large supply")

        score = get_risk_score(warnings)
        verdict = "✅ SAFE" if score > 60 else "🔴 RISKY"

        reply = (
            f"🛡️ *RugGuard Scan Result*\n\n"
            f"📌 *Token:* {token.get('token_name', 'Unknown')} (${token.get('token_symbol', '?')})\n"
            f"📊 *Risk Score:* {score}/100\n"
            f"🏁 *Verdict:* {verdict}\n\n"
            f"🍯 *Honeypot:* {'Yes 🚨' if token.get('is_honeypot') == '1' else 'No ✅'}\n"
            f"💰 *Buy Tax:* {token.get('buy_tax', '0')}%\n"
            f"💰 *Sell Tax:* {token.get('sell_tax', '0')}%\n"
            f"🔒 *Liquidity Locked:* {'No 🔓' if token.get('lp_locked') == '0' else 'Yes ✅'}\n"
            f"👛 *Dev Wallet:* {token.get('owner_percent', '0')}%\n"
        )

        if warnings:
            reply += "\n⚠️ *Warnings:*\n" + "\n".join(warnings)
        else:
            reply += "\n✅ No major risks detected"

        reply += "\n\n🔗 Powered by RugGuard"

        await update.message.reply_text(reply, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("❌ Scan failed. Please try again.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, scan))

print("RugGuard Bot is running...")
app.run_polling()
```

---

**Step 2 — Create a file called `requirements.txt` and paste this:**
```
python-telegram-bot==20.7
requests
