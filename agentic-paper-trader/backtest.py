"""Simple single-symbol OHLCV backtester using the same signal and cost assumptions.
Download public historical candles with --download or pass a CSV with timestamp,open,high,low,close,volume.
Conservative assumptions: next candle open entry after a signal; stop-first if stop and target hit in one candle.
"""
import argparse
import time
import pandas as pd
from market_data import MarketData
from strategy import buy_signal, enrich_candles

def resolve_exit(row, pos, i, max_hold_candles):
    """Return (exit_reason, reference_price) for one candle, or (None, None).

    OHLC data cannot reveal intrabar ordering when both stop and target are
    touched, so stop-first is used as the conservative assumption.
    """
    candle_open = float(row["open"])
    candle_low = float(row["low"])
    candle_high = float(row["high"])

    if candle_low <= pos["stop"]:
        return "stop_loss", min(pos["stop"], candle_open)
    if candle_high >= pos["target"]:
        return "take_profit", max(pos["target"], candle_open)
    if i - pos["entry_i"] >= max_hold_candles:
        return "max_hold", float(row["close"])
    return None, None


def run_backtest(df, initial_cash=100.0, fee_rate=0.001, slippage_rate=0.0005,
                 risk_fraction=0.005, position_fraction=0.25, stop_pct=0.012, target_pct=0.024, max_hold_candles=288, volume_multiplier=1.2):
    df=df.copy().reset_index(drop=True)
    if len(df)<50: raise ValueError("Need at least 50 candles for a useful smoke backtest")
    if max_hold_candles < 1: raise ValueError("max_hold_candles must be at least 1")
    cash=initial_cash; pos=None; trades=[]; equity_curve=[]; peak=initial_cash; max_dd=0.0
    for i in range(40,len(df)):
        row=df.iloc[i]; mark=float(row.close)
        exited_this_candle = False
        # Exit checks use current candle OHLC; stop-first if both levels touched.
        if pos:
            why, ref = resolve_exit(row, pos, i, max_hold_candles)
            if why:
                exit_fill=ref*(1-slippage_rate); gross=pos['qty']*exit_fill; exit_fee=gross*fee_rate
                cash+=gross-exit_fee
                pnl=gross-exit_fee-(pos['qty']*pos['entry']+pos['entry_fee'])
                trades.append({
                    'entry_index': pos['entry_i'],
                    'signal_index': pos['signal_i'],
                    'exit_index': i,
                    'entry': pos['entry'],
                    'exit': exit_fill,
                    'pnl': pnl,
                    'reason': why,
                    **pos['entry_indicators'],
                })
                pos=None
                exited_this_candle = True
        # Do not re-enter at this candle's open after detecting an intrabar exit.
        if pos is None and i>=1 and not exited_this_candle:
            signal_df = df.iloc[:i].copy()
            sig,_ = buy_signal(signal_df, volume_multiplier=volume_multiplier)
            entry_ref = float(row.open)
            equity = cash + (pos['qty']*mark if pos else 0)
            if sig and entry_ref > 0:
                signal_row = enrich_candles(signal_df).iloc[-1]
                ema_fast = float(signal_row["ema_fast"])
                ema_slow = float(signal_row["ema_slow"])
                signal_vwap = float(signal_row["vwap"])
                avg_volume = float(signal_row["volume_avg20"])

                entry_indicators = {
                    "signal_rsi": float(signal_row["rsi"]),
                    "signal_ema_fast": ema_fast,
                    "signal_ema_slow": ema_slow,
                    "signal_ema_separation_pct": (ema_fast / ema_slow - 1) * 100,
                    "signal_close_vwap_pct": (
                        float(signal_row["close"]) / signal_vwap - 1
                    ) * 100,
                    "signal_volume_ratio": (
                        float(signal_row["volume"]) / avg_volume
                    ),
                }
                fill=entry_ref*(1+slippage_rate)
                qty=min(equity*risk_fraction/(fill*stop_pct), equity*position_fraction/fill, cash/(fill*(1+fee_rate)))
                if qty>0:
                    fee=qty*fill*fee_rate; cash-=qty*fill+fee
                    pos={
                        'qty': qty,
                        'entry': fill,
                        'entry_fee': fee,
                        'stop': fill*(1-stop_pct),
                        'target': fill*(1+target_pct),
                        'entry_i': i,
                        'signal_i': i-1,
                        'entry_indicators': entry_indicators,
                    }
        equity=cash+(pos['qty']*mark if pos else 0)
        peak=max(peak,equity); max_dd=max(max_dd,(peak-equity)/peak if peak else 0)
        equity_curve.append({'timestamp':str(row.get('timestamp',i)),'equity':equity})
    if pos:
        last=float(df.iloc[-1].close)*(1-slippage_rate)
        gross=pos['qty']*last
        fee=gross*fee_rate
        cash+=gross-fee
        pnl=gross-fee-(pos['qty']*pos['entry']+pos['entry_fee'])
        trades.append({
            'entry_index': pos['entry_i'],
            'signal_index': pos['signal_i'],
            'exit_index': len(df)-1,
            'entry': pos['entry'],
            'exit': last,
            'pnl': pnl,
            'reason': 'end_of_data',
            **pos['entry_indicators'],
        })
        pos=None

        # Include final liquidation costs in the equity and drawdown calculation.
        final_equity=cash
        peak=max(peak,final_equity)
        max_dd=max(max_dd,(peak-final_equity)/peak if peak else 0)
        equity_curve.append({
            'timestamp':str(df.iloc[-1].get('timestamp',len(df)-1)),
            'equity':final_equity
        })
    pnls=[t['pnl'] for t in trades]; wins=sum(x>0 for x in pnls); losses=sum(x<=0 for x in pnls)
    gross_profit=sum(x for x in pnls if x>0); gross_loss=abs(sum(x for x in pnls if x<0))
    return {'initial_cash':initial_cash,'final_cash':cash,'net_return_pct':(cash/initial_cash-1)*100,
            'trades':len(trades),'wins':wins,'losses':losses,'win_rate_pct':(wins/len(trades)*100 if trades else 0),
            'profit_factor':(gross_profit/gross_loss if gross_loss else (float('inf') if gross_profit else 0)),
            'max_drawdown_pct':max_dd*100,'trade_log':trades,'equity_curve':equity_curve}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--csv',help='CSV containing timestamp,open,high,low,close,volume')
    p.add_argument('--download',action='store_true',help='Download public Binance history for a symbol')
    p.add_argument('--symbol', default='BTC/USDT')
    p.add_argument('--timeframe', default='5m')
    p.add_argument('--max-hold-candles', type=int, default=288,
                   help='Maximum holding period in candles; 288 = 24h at 5m')
    p.add_argument('--volume-multiplier', type=float, default=1.2,
                   help='Required volume / 20-candle average; default 1.2')
    p.add_argument('--limit', type=int, default=1000,
                   help='Maximum total candles to download')
    p.add_argument('--since', help='Start date/time in UTC, e.g. 2026-09-01')
    p.add_argument('--until', help='End date/time in UTC (exclusive), e.g. 2026-09-08')
    p.add_argument('--out',default='backtest_results'); args=p.parse_args()
    if args.csv: df=pd.read_csv(args.csv)
    elif args.download:
        if bool(args.since) != bool(args.until):
            p.error("Provide both --since and --until for a fixed date range")
        if args.limit < 1:
            p.error("--limit must be positive")

        md = MarketData()

        if args.since and args.until:
            start = pd.Timestamp(args.since)
            end = pd.Timestamp(args.until)
            start = start.tz_localize("UTC") if start.tzinfo is None else start.tz_convert("UTC")
            end = end.tz_localize("UTC") if end.tzinfo is None else end.tz_convert("UTC")
            if start >= end:
                p.error("--since must be earlier than --until")

            cursor = int(start.timestamp() * 1000)
            end_ms = int(end.timestamp() * 1000)
            step_ms = int(md.exchange.parse_timeframe(args.timeframe) * 1000)
            raw = []

            # Fetch sequential pages; avoid duplicate candle timestamps.
            while cursor < end_ms and len(raw) < args.limit:
                page_limit = min(1000, args.limit - len(raw))
                batch = md.exchange.fetch_ohlcv(
                    args.symbol, timeframe=args.timeframe,
                    since=cursor, limit=page_limit
                )
                if not batch:
                    break

                batch = [
                    candle for candle in batch
                    if cursor <= candle[0] < end_ms
                ]
                if raw:
                    batch = [candle for candle in batch if candle[0] > raw[-1][0]]
                if not batch:
                    break

                raw.extend(batch)
                next_cursor = batch[-1][0] + step_ms
                if next_cursor <= cursor:
                    break
                cursor = next_cursor

            if len(raw) >= args.limit and raw[-1][0] + step_ms < end_ms:
                print("WARNING: --limit reached before the requested end date; range is incomplete.")
            print(f"Downloaded {len(raw)} candles from {start} up to (exclusive) {end}.")
        else:
            # Preserve the original recent-candles mode.
            raw = md.exchange.fetch_ohlcv(
                args.symbol, timeframe=args.timeframe,
                limit=min(args.limit, 1000)
            )
            print(f"Downloaded {len(raw)} recent candles (single-page mode).")

        df = pd.DataFrame(
            raw, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    else: p.error('Provide --csv or --download')
    for c in ['open','high','low','close','volume']: df[c]=pd.to_numeric(df[c],errors='coerce')
    df=df.dropna(subset=['open','high','low','close','volume']).reset_index(drop=True)
    if args.volume_multiplier <= 0:
        p.error('--volume-multiplier must be positive')
    result=run_backtest(df, max_hold_candles=args.max_hold_candles,
                        volume_multiplier=args.volume_multiplier)
    pd.DataFrame(result['trade_log']).to_csv(args.out+'_trades.csv',index=False)
    pd.DataFrame(result['equity_curve']).to_csv(args.out+'_equity.csv',index=False)
    print('BACKTEST RESULTS (historical simulation, not a forecast)')
    for k in ['initial_cash','final_cash','net_return_pct','trades','wins','losses','win_rate_pct','profit_factor','max_drawdown_pct']:
        print(f'{k}: {result[k]}')
    print(f'Wrote {args.out}_trades.csv and {args.out}_equity.csv')
if __name__=='__main__': main()
