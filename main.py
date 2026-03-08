import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

def get_risk_score(warnings):
    return max(100 - len(warnings) * 20, 10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to RugGuard Bot!\n\n"
        "Send any Ethereum token contract address to scan it.\n\n"
        "Example:\n0xdAC17F958D2ee523a2206206994597C13D831ec7"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()

    if not address.startswith("0x") or len(address) < 40:
        await update.message.reply_text("Please send a valid contract address starting with 0x")
        return

    await update.message.reply_text("Scanning token... please wait")

    try:
        url = "https://api.gopluslabs.io/api/v1/token_security/1?contract_addresses=" + address
        response = requests.get(url, timeout=10)
        data = response.json()
        token = data.get("result", {}).get(address.lower())

        if not token:
            await update.message.reply_text("Token not found. Make sure it is an Ethereum contract.")
            return

        warnings = []
        if token.get("is_honeypot") == "1":
            warnings.append("Honeypot detected")
        if float(token.get("buy_tax") or 0) > 10:
            warnings.append("High buy tax")
        if float(token.get("sell_tax") or 0) > 10:
            warnings.append("High sell tax")
        if token.get("lp_locked") == "0":
            warnings.append("Liquidity not locked")
        if float(token.get("owner_percent") or 0) > 20:
            warnings.append("Dev holds large supply")

        score = get_risk_score(warnings)
        verdict = "SAFE" if score > 60 else "RISKY"

        reply = (
            "RugGuard Scan Result\n\n"
            "Token: " + token.get("token_name", "Unknown") + " (" + token.get("token_symbol", "?") + ")\n"
            "Risk Score: " + str(score) + "/100\n"
            "Verdict: " + verdict + "\n\n"
            "Honeypot: " + ("Yes" if token.get("is_honeypot") == "1" else "No") + "\n"
            "Buy Tax: " + str(token.get("buy_tax", "0")) + "%\n"
            "Sell Tax: " + str(token.get("sell_tax", "0")) + "%\n"
            "Liquidity Locked: " + ("No" if token.get("lp_locked") == "0" else "Yes") + "\n"
            "Dev Wallet: " + str(token.get("owner_percent", "0")) + "%\n"
        )

        if warnings:
            reply += "\nWarnings:\n" + "\n".join(warnings)
        else:
            reply += "\nNo major risks detected"

        reply += "\n\nPowered by RugGuard"

        await update.message.reply_text(reply)

    except Exception:
        await update.message.reply_text("Scan failed. Please try again.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, scan))

print("RugGuard Bot is running...")
app.run_polling()
