import json
import math
import os
import sys
import urllib.request
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import test_weathernext

LOG_FILE = "paper_trading_log.md"
STATE_FILE = "portfolio_state.json"
CAPITAL_PER_TRADE = 10.00  # Fixed $10 per position

TICKER_TO_STATION = {
    "CHI": "CLIORD",
    "DEN": "CLIDEN",
    "LAX": "CLILAX",
    "LV": "CLILAS",
    "MIA": "CLIMIA",
    "NOLA": "CLIMSY",
    "NYC": "CLINYC",
    "PHIL": "CLIPHL",
    "SFO": "CLISFO",
    "TTN": "CLITTN",
    "ATL": "CLIATL",
    "AUS": "CLIAUS",
    "BOS": "CLIBOS",
    "DAL": "CLIDFW",
    "DC": "CLIDCA",
    "EWR": "CLIEWR",
    "HOU": "CLIHOU",
    "MIN": "CLIMSP",
    "OKC": "CLIOKC",
    "PHX": "CLIPHX",
    "SATX": "CLISAT",
    "SEA": "CLISEA",
}


def load_state():
    """Loads persistent portfolio balance and trade history."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default initial state
    return {
        "starting_balance": 100.00,
        "cash_balance": 100.00,
        "cumulative_realized_pnl": 0.00,
        "pending_trades": [],
        "settled_trades": [],
    }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def update_log_header(state):
    """Dynamically updates the top-of-file balance banner in paper_trading_log.md."""
    if not os.path.exists(LOG_FILE):
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        open_invested = sum(t.get("invested", 0.0) for t in state.get("pending_trades", []))
        equity = state["cash_balance"] + open_invested
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_banner = (
            "# Kalshi Weather Paper Trading Journal (Live Production Market Benchmarking)\n\n"
            f"> 💰 **Starting Paper Capital:** **${state['starting_balance']:.2f}**  \n"
            f"> 💵 **Available Cash Balance:** **${state['cash_balance']:.2f}**  \n"
            f"> 📈 **Total Account Equity:** **${equity:.2f}** (${state['cash_balance']:.2f} Cash + ${open_invested:.2f} in Active Trades)  \n"
            f"> 📊 **Cumulative Realized PnL:** **{state['cumulative_realized_pnl']:+.2f}**  \n"
            f"> 🕒 **Last Updated:** {timestamp}  \n"
            f"> **Strategy Rules:** Trade YES if Model > 75%, Trade NO if Model < 25%, Entry Ask Price < 80¢, Fixed $10/trade  \n\n"
            "---\n"
        )

        if "\n---\n" in content:
            parts = content.split("\n---\n", 1)
            content = new_banner + parts[1]
        elif "---" in content:
            parts = content.split("---", 1)
            content = new_banner + parts[1]
        else:
            content = new_banner + "\n" + content

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print(f"Error updating log header banner: {e}")


def fetch_settled_kalshi_markets():
    """Fetches settled markets from Kalshi public API."""
    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXRAIN&status=settled&limit=100"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    settled_map = {}
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            for m in data.get("markets", []):
                ticker = m.get("ticker", "")
                result = m.get("result", "").lower()  # 'yes' or 'no'
                if ticker and result:
                    settled_map[ticker] = result.upper()
    except Exception as e:
        print(f"Error fetching settled Kalshi markets: {e}")
    return settled_map


def resolve_pending_trades(state):
    """Checks settled Kalshi markets and resolves any open paper trades."""
    pending = state.get("pending_trades", [])
    if not pending:
        return 0

    settled_markets = fetch_settled_kalshi_markets()
    resolved_count = 0
    remaining_pending = []

    for trade in pending:
        ticker = trade["ticker"]
        actual_result = settled_markets.get(ticker)
        if actual_result:  # 'YES' or 'NO'
            trade["actual_resolution"] = actual_result
            won = (trade["position"] == actual_result)
            if won:
                payout = trade["potential_realized"]
                gain = trade["potential_net_profit"]
                state["cash_balance"] += payout
                state["cumulative_realized_pnl"] += gain
                trade["realized_gain"] = f"+${gain:.2f}"
            else:
                gain = -CAPITAL_PER_TRADE
                state["cumulative_realized_pnl"] += gain
                trade["realized_gain"] = f"-${CAPITAL_PER_TRADE:.2f}"

            state["settled_trades"].append(trade)
            resolved_count += 1
            print(f"Resolved {ticker}: Actual={actual_result}, Picked={trade['position']} -> Gain: {trade['realized_gain']}")
        else:
            remaining_pending.append(trade)

    state["pending_trades"] = remaining_pending
    save_state(state)
    if resolved_count > 0:
        update_log_header(state)
    return resolved_count


def fetch_live_kalshi_markets(target_date_str):
    """Fetches live production prices from public Kalshi API for target date."""
    dt = datetime.strptime(target_date_str, "%Y-%m-%d")
    date_code = dt.strftime("%y%b%d").upper()

    url = "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXRAIN&status=open&limit=200"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching live Kalshi prices: {e}")
        return {}

    markets = data.get("markets", [])
    kalshi_by_station = {}

    for m in markets:
        ticker = m.get("ticker", "")
        if date_code in ticker:
            suffix = ticker.split("-")[-1]
            station_code = TICKER_TO_STATION.get(suffix)
            if station_code:
                yes_ask = float(m.get("yes_ask_dollars") or 0.0)
                no_ask = float(m.get("no_ask_dollars") or 0.0)
                last_price = float(m.get("last_price_dollars") or 0.0)
                kalshi_by_station[station_code] = {
                    "ticker": ticker,
                    "yes_ask": yes_ask,
                    "no_ask": no_ask,
                    "last_price": last_price,
                    "kalshi_chance_yes": int(round(last_price * 100)),
                }

    return kalshi_by_station


def calculate_kalshi_trade(price):
    """Computes exact contracts, taker fee, and realized payouts for a $10 trade."""
    if price <= 0.0 or price >= 1.0:
        return None

    contracts = CAPITAL_PER_TRADE / price
    raw_fee = 0.07 * contracts * price * (1.0 - price)
    fee = math.ceil(raw_fee * 100.0) / 100.0

    gross_payout = contracts * 1.00
    net_payout = gross_payout - fee
    net_profit = net_payout - CAPITAL_PER_TRADE

    return {
        "contracts": round(contracts, 2),
        "fee": fee,
        "gross_payout": round(gross_payout, 2),
        "net_payout": round(net_payout, 2),
        "net_profit": round(net_profit, 2),
    }


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else "2026-09-30"
    state = load_state()

    print(f"=== Running Paper Trader for {target_date} ===")
    print(f"Initial Starting Capital: ${state['starting_balance']:.2f}")
    print(f"Current Available Cash: ${state['cash_balance']:.2f}")

    # 1. Check & Resolve any past pending trades first
    resolved = resolve_pending_trades(state)
    if resolved > 0:
        print(f"Updated {resolved} pending trades with official resolutions.")

    # 2. Fetch live production Kalshi markets
    kalshi_data = fetch_live_kalshi_markets(target_date)
    print(f"Found {len(kalshi_data)} matching live Kalshi markets for {target_date}.")

    # 3. Fetch WeatherNext forecasts concurrently
    forecast_results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_station = {
            executor.submit(test_weathernext.fetch_forecast, s, target_date): s
            for s in test_weathernext.STATIONS
        }
        for future in future_to_station:
            res = future.result()
            forecast_results[res["station_code"]] = res

    # 4. Apply Decision Rules & Build Log Table
    rows = []
    daily_invested = 0.0
    daily_potential_return = 0.0
    daily_trades_count = 0

    for station in test_weathernext.STATIONS:
        code = station["station_code"]
        city = station["city"]
        fc = forecast_results.get(code, {})
        km = kalshi_data.get(code, {})

        model_prob = fc.get("probability", 0.0)
        yes_ask = km.get("yes_ask", 0.0)
        no_ask = km.get("no_ask", 0.0)
        ticker = km.get("ticker", "")
        kalshi_chance = f"{km.get('kalshi_chance_yes', '--')}%" if km else "--"
        yes_ask_str = f"{int(yes_ask * 100)}¢" if yes_ask > 0 else "--"
        no_ask_str = f"{int(no_ask * 100)}¢" if no_ask > 0 else "--"

        position = "NO TRADE"
        chosen_price = 0.0
        reason = "Prob between 25-75%"

        if model_prob > 75.0:
            if 0.0 < yes_ask < 0.80:
                position = "YES"
                chosen_price = yes_ask
                reason = "Strong Rain Signal"
            elif yes_ask >= 0.80:
                reason = "YES price >= 80¢ (Low ROI/Fee Risk)"
            else:
                reason = "No YES Ask liquidity"

        elif model_prob < 25.0:
            if 0.0 < no_ask < 0.80:
                position = "NO"
                chosen_price = no_ask
                reason = "Strong Dry Signal"
            elif no_ask >= 0.80:
                reason = "NO price >= 80¢ (Low ROI/Fee Risk)"
            else:
                reason = "No NO Ask liquidity"

        trade_calc = calculate_kalshi_trade(chosen_price) if position in ["YES", "NO"] else None

        # Check if we have enough cash
        if trade_calc and state["cash_balance"] >= CAPITAL_PER_TRADE:
            state["cash_balance"] -= CAPITAL_PER_TRADE
            daily_invested += CAPITAL_PER_TRADE
            daily_potential_return += trade_calc["net_payout"]
            daily_trades_count += 1

            entry_price_str = f"{int(chosen_price * 100)}¢"
            contracts_str = f"{trade_calc['contracts']}"
            payout_str = f"${trade_calc['net_payout']:.2f} (+${trade_calc['net_profit']:.2f})"

            # Record in state pending
            state["pending_trades"].append({
                "date": target_date,
                "city": city,
                "station": code,
                "ticker": ticker,
                "position": position,
                "entry_price": chosen_price,
                "contracts": trade_calc["contracts"],
                "invested": CAPITAL_PER_TRADE,
                "potential_realized": trade_calc["net_payout"],
                "potential_net_profit": trade_calc["net_profit"],
            })
        elif trade_calc and state["cash_balance"] < CAPITAL_PER_TRADE:
            position = "SKIPPED (INSUFFICIENT FUNDS)"
            entry_price_str = "--"
            contracts_str = "--"
            payout_str = "--"
            reason = f"Cash ${state['cash_balance']:.2f} < $10.00"
        else:
            entry_price_str = "--"
            contracts_str = "--"
            payout_str = "--"

        rows.append({
            "city": city,
            "station": code,
            "kalshi_chance": kalshi_chance,
            "yes_no_price": f"{yes_ask_str} / {no_ask_str}",
            "model_prob": f"{model_prob:.1f}%",
            "decision": position,
            "entry_price": entry_price_str,
            "contracts": contracts_str,
            "invested": f"${CAPITAL_PER_TRADE:.2f}" if position in ["YES", "NO"] else "$0.00",
            "potential_realized": payout_str,
            "resolution": "Pending",
            "realized_gain": "Pending",
            "notes": reason,
        })

    save_state(state)

    # 5. Generate Markdown Entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = f"\n## Paper Trading Session: {target_date}\n"
    md_content += f"*Logged at: {timestamp} (Live Production Kalshi Prices & WeatherNext 63-Member Ensemble)*\n\n"
    md_content += f"- **Trades Placed Today:** {daily_trades_count}\n"
    md_content += f"- **Capital Deployed Today:** ${daily_invested:.2f}\n"
    md_content += f"- **Potential Return from Today's Trades:** ${daily_potential_return:.2f}\n\n"

    headers = [
        "City",
        "Station",
        "Kalshi Chance",
        "YES / NO Ask",
        "WeatherNext Prob",
        "Position",
        "Entry Price",
        "Contracts",
        "Invested",
        "Realized Return If Won",
        "Actual Resolution",
        "Realized Gain",
        "Notes",
    ]
    md_content += "| " + " | ".join(headers) + " |\n"
    md_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"

    for r in rows:
        md_content += (
            f"| **{r['city']}** | `{r['station']}` | {r['kalshi_chance']} | {r['yes_no_price']} | "
            f"{r['model_prob']} | **{r['decision']}** | {r['entry_price']} | {r['contracts']} | "
            f"{r['invested']} | {r['potential_realized']} | {r['resolution']} | {r['realized_gain']} | {r['notes']} |\n"
        )

    # Daily Portfolio Summary at the end of the table
    equity = state["cash_balance"] + sum(t["invested"] for t in state["pending_trades"])
    md_content += f"\n### 📊 Portfolio Status ({target_date})\n"
    md_content += f"* **Initial Bankroll:** ${state['starting_balance']:.2f}\n"
    md_content += f"* **Capital Invested Today:** ${daily_invested:.2f} ({daily_trades_count} positions @ ${CAPITAL_PER_TRADE:.2f})\n"
    md_content += f"* **Available Cash Remaining:** **${state['cash_balance']:.2f}**\n"
    md_content += f"* **Total Active Open Positions:** {len(state['pending_trades'])}\n"
    md_content += f"* **Potential Realized Payout:** ${daily_potential_return:.2f} (Potential Net Profit: +${(daily_potential_return - daily_invested):.2f})\n"
    md_content += f"* **Cumulative Realized PnL to Date:** **${state['cumulative_realized_pnl']:+.2f}**\n"
    md_content += f"* **Total Account Equity:** **${equity:.2f}** (${state['cash_balance']:.2f} Cash + ${sum(t['invested'] for t in state['pending_trades']):.2f} Open Positions)\n\n---\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(md_content)

    # Ensure top-of-file balance banner is refreshed
    update_log_header(state)

    print(f"\nExecution complete. Logged {daily_trades_count} trades. Cash remaining: ${state['cash_balance']:.2f}")


if __name__ == "__main__":
    main()
