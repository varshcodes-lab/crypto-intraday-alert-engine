import time, logging
from datetime import datetime, timezone
from config import CFG
from market_data import MarketData
from agents import MarketScannerAgent, StrategyAnalystAgent, RiskSupervisorAgent, PerformanceAgent
from risk_manager import RiskManager
from journal import Journal
from paper_broker import PaperBroker

def utc_now(): return datetime.now(timezone.utc)

def main():
    CFG.validate()
    logging.basicConfig(level=getattr(logging,CFG.log_level,logging.INFO),
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[logging.StreamHandler(),logging.FileHandler('bot.log',encoding='utf-8')])
    logging.warning('PAPER MODE ONLY: this program has no authenticated exchange client or live-order path.')
    data=MarketData(); journal=Journal(CFG.database_path)
    broker=PaperBroker(CFG.initial_cash,CFG.fee_rate,CFG.slippage_rate,journal)
    logging.info(
        'Recovered paper portfolio: cash=%.4f open_positions=%d '
        'realized_pnl=%.4f closed_trades=%d',
        broker.cash, len(broker.positions), broker.realized_pnl,
        broker.closed_trades
    )
    risk=RiskManager(CFG.risk_per_trade,CFG.max_daily_loss,CFG.max_position_fraction,CFG.max_open_positions,CFG.stop_loss_pct)
    scanner=MarketScannerAgent(data,CFG.min_quote_volume,CFG.max_symbols)
    analyst=StrategyAnalystAgent(data,CFG.timeframe,CFG.candle_limit)
    supervisor=RiskSupervisorAgent(risk); evaluator=PerformanceAgent()
    seen={}; day=utc_now().date(); marks={}; day_start=broker.equity(marks)
    while True:
        started=time.time()
        try:
            now=utc_now()
            if now.date()!=day:
                day=now.date(); day_start=broker.equity(marks)
                logging.info('UTC daily reference equity reset: %.4f',day_start)
            symbols=scanner.run()
            # Continue managing any open simulated positions even if a pair falls out of the liquid universe.
            symbols=list(dict.fromkeys(symbols + list(broker.positions.keys())))
            logging.info('Scanning %d liquid USDT Spot pairs (including open positions)',len(symbols))
            for symbol in symbols:
                try:
                    signal,df=analyst.analyze(symbol)
                    if df.empty or signal is None: continue
                    last=df.iloc[-1]; candle_key=signal.candle_time; price=signal.price
                    marks[symbol]=price
                    candle={'timestamp':candle_key,'open':float(last.open),'high':float(last.high),'low':float(last.low),'close':price,'volume':float(last.volume)}
                    broker.evaluate_exit(symbol,candle)
                    if seen.get(symbol)==candle_key: continue
                    seen[symbol]=candle_key
                    if symbol in broker.positions:
                        logging.info('HOLD %s: position already open', symbol)
                        continue
                    if not signal.should_buy:
                        logging.info('NO SIGNAL %s | price=%.8f | reason=%s', symbol, price, signal.reason)
                        continue
                    equity=broker.equity(marks)
                    qty,why=supervisor.approve(equity=equity,cash=broker.cash,
                        entry_price=price*(1+CFG.slippage_rate),open_positions=len(broker.positions),
                        daily_start_equity=day_start,current_equity=equity)
                    if qty<=0:
                        logging.info('Risk veto %s: %s',symbol,why); continue
                    broker.enter_long(symbol,qty,price,CFG.stop_loss_pct,CFG.take_profit_pct,signal.reason)
                except Exception as exc: logging.warning('Skipping %s: %s',symbol,exc)
            equity=broker.equity(marks); journal.snapshot(utc_now().isoformat(),broker.cash,equity)
            logging.info('equity=%.4f cash=%.4f open=%d realized_pnl=%.4f performance=%s',
                equity,broker.cash,len(broker.positions),broker.realized_pnl,evaluator.summary(broker))
        except KeyboardInterrupt:
            logging.info('Stopped by user. Paper positions are only in the local simulator; inspect journal before restarting.'); break
        except Exception: logging.exception('Cycle failed; retrying.')
        time.sleep(max(1,CFG.scan_interval-(time.time()-started)))
if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: print('Stopped. Paper trading only.')
