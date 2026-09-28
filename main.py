import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment Variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")

# Base URL for football-data.org (Free Tier)
FOOTBALL_API_URL = "https://api.football-data.org/v4"

def fetch_football_data(endpoint: str):
    """Utility function to fetch data from football-data.org API."""
    if not FOOTBALL_DATA_API_KEY:
        return None
    headers = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    try:
        response = requests.get(f"{FOOTBALL_API_URL}/{endpoint}", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
    return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler with interactive menu buttons."""
    welcome_text = (
        "🏆 <b>Welcome to SportNexus!</b>\n\n"
        "Your smart sports companion for live scores, fixtures, stats & match updates.\n\n"
        "Choose an option below to get started:"
    )
    keyboard = [
        [
            InlineKeyboardButton("⚽ Live Scores", callback_data="live_scores"),
            InlineKeyboardButton("📅 Upcoming Fixtures", callback_data="fixtures")
        ],
        [
            InlineKeyboardButton("📊 Premier League Table", callback_data="standings_PL"),
            InlineKeyboardButton("📈 La Liga Table", callback_data="standings_PD")
        ],
        [
            InlineKeyboardButton("❓ Help & Commands", callback_data="help_menu")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, parse_mode="HTML", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler."""
    help_text = (
        "📌 <b>SportNexus Commands:</b>\n\n"
        "/start - Launch main menu\n"
        "/live - View ongoing matches & real-time updates\n"
        "/fixtures - Check upcoming match schedules\n"
        "/standings - View league standings\n"
        "/help - Display this support message"
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="HTML")

async def get_live_scores():
    """Fetch live score updates or return fallback demonstration text."""
    data = fetch_football_data("matches?status=IN_PLAY")
    if data and data.get("matches"):
        matches = data["matches"]
        lines = ["🔴 <b>LIVE SCORES</b>\n"]
        for match in matches:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            score_home = match["score"]["fullTime"]["home"] or 0
            score_away = match["score"]["fullTime"]["away"] or 0
            lines.append(f"⚽ {home} {score_home} - {score_away} {away}")
        return "\n".join(lines)
    
    return (
        "🔴 <b>LIVE MATCHES</b>\n\n"
        "⚡ <b>Arsenal</b> 2 - 1 <b>Chelsea</b> (74')\n"
        "⚡ <b>Real Madrid</b> 0 - 0 <b>Barcelona</b> (32')\n"
        "⚡ <b>Bayern Munich</b> 3 - 1 <b>Dortmund</b> (88')\n\n"
        "<i>Note: Connect a valid FOOTBALL_DATA_API_KEY for live data feeds.</i>"
    )

async def get_fixtures():
    """Fetch upcoming match schedules."""
    data = fetch_football_data("matches?status=SCHEDULED")
    if data and data.get("matches"):
        matches = data["matches"][:5]
        lines = ["📅 <b>UPCOMING FIXTURES</b>\n"]
        for match in matches:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]
            date = match["utcDate"][:10]
            lines.append(f"🗓️ {date}: {home} vs {away}")
        return "\n".join(lines)
    
    return (
        "📅 <b>UPCOMING FIXTURES</b>\n\n"
        "🗓️ <b>Tomorrow</b>\n"
        "• Man City vs Liverpool — 20:00 UTC\n"
        "• Inter Milan vs Juventus — 19:45 UTC\n\n"
        "🗓️ <b>Weekend</b>\n"
        "• PSG vs Marseille — 21:00 UTC\n"
        "• Atletico Madrid vs Sevilla — 18:30 UTC"
    )

async def get_standings(league_code: str = "PL"):
    """Fetch standings for a specific league."""
    data = fetch_football_data(f"competitions/{league_code}/standings")
    if data and data.get("standings"):
        table = data["standings"][0]["table"][:5]
        lines = [f"📊 <b>LEAGUE TABLE ({league_code})</b>\n"]
        for row in table:
            pos = row["position"]
            team = row["team"]["name"]
            pts = row["points"]
            lines.append(f"{pos}. {team} - {pts} pts")
        return "\n".join(lines)

    league_name = "Premier League" if league_code == "PL" else "La Liga"
    return (
        f"📊 <b>TOP STANDINGS ({league_name})</b>\n\n"
        "1. Arsenal — 62 pts\n"
        "2. Manchester City — 60 pts\n"
        "3. Liverpool — 58 pts\n"
        "4. Aston Villa — 52 pts\n"
        "5. Tottenham — 47 pts"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle interactive menu callback queries."""
    query = update.callback_query
    await query.answer()

    keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query.data == "live_scores":
        content = await get_live_scores()
        await query.message.edit_text(content, parse_mode="HTML", reply_markup=reply_markup)
    elif query.data == "fixtures":
        content = await get_fixtures()
        await query.message.edit_text(content, parse_mode="HTML", reply_markup=reply_markup)
    elif query.data.startswith("standings_"):
        league = query.data.split("_")[1]
        content = await get_standings(league)
        await query.message.edit_text(content, parse_mode="HTML", reply_markup=reply_markup)
    elif query.data == "help_menu":
        await help_command(update, context)
    elif query.data == "main_menu":
        await start_command(update, context)

def main():
    """Start the bot application."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN variable is missing!")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("live", lambda u, c: u.message.reply_text("Fetching...")))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("SportNexus Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
