import unittest, tempfile, os
from backtest import resolve_exit
import pandas as pd
from risk_manager import RiskManager
from strategy import buy_signal, enrich_candles
from paper_broker import PaperBroker
from journal import Journal
from config import Config

class BacktestExitTests(unittest.TestCase):
    def setUp(self):
        self.pos = {"stop": 98.0, "target": 104.0, "entry_i": 1}

    def test_stop_gap_uses_worse_open(self):
        row = {"open": 90.0, "low": 89.0, "high": 101.0, "close": 95.0}
        reason, price = resolve_exit(row, self.pos, 2, 288)
        self.assertEqual(reason, "stop_loss")
        self.assertEqual(price, 90.0)

    def test_take_profit_gap_uses_open_above_target(self):
        row = {"open": 106.0, "low": 105.0, "high": 108.0, "close": 107.0}
        reason, price = resolve_exit(row, self.pos, 2, 288)
        self.assertEqual(reason, "take_profit")
        self.assertEqual(price, 106.0)

    def test_both_levels_touched_uses_stop_first(self):
        row = {"open": 100.0, "low": 97.0, "high": 105.0, "close": 101.0}
        reason, price = resolve_exit(row, self.pos, 2, 288)
        self.assertEqual(reason, "stop_loss")
        self.assertEqual(price, 98.0)

    def test_normal_stop_without_gap_uses_stop_price(self):
        row = {"open": 100.0, "low": 97.0, "high": 102.0, "close": 99.0}
        reason, price = resolve_exit(row, self.pos, 2, 288)
        self.assertEqual(reason, "stop_loss")
        self.assertEqual(price, 98.0)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.risk=RiskManager(.005,.02,.25,3,.012)
    def test_max_positions_veto(self):
        q,why=self.risk.position_quantity(100,100,10,3,100,100)
        self.assertEqual(q,0); self.assertEqual(why,'max_open_positions')
    def test_daily_loss_veto(self):
        q,why=self.risk.position_quantity(98,98,10,0,100,98)
        self.assertEqual(q,0); self.assertEqual(why,'daily_loss_limit_reached')
    def test_quantity_caps_notional(self):
        q,why=self.risk.position_quantity(100,100,10,0,100,100)
        self.assertGreater(q,0); self.assertLessEqual(q*10,25.01)
    def test_short_data_no_signal(self):
        df=pd.DataFrame({'timestamp':pd.date_range('2026-01-01',periods=10,freq='5min',tz='UTC'),
          'open':[1.]*10,'high':[1.1]*10,'low':[.9]*10,'close':[1.]*10,'volume':[100.]*10})
        self.assertEqual(buy_signal(df),(False,'insufficient_candles'))
    def test_config_rejects_live_mode(self):
        c=Config(trading_mode='live')
        with self.assertRaises(ValueError): c.validate()
    def test_paper_broker_round_trip(self):
        with tempfile.TemporaryDirectory() as td:
            j=Journal(os.path.join(td,'test.db'))
            b=PaperBroker(100,.001,0,j)
            self.assertTrue(b.enter_long('BTC/USDT',.1,100,0.01,0.02,'test'))
            self.assertIn('BTC/USDT',b.positions)
            p=b.positions['BTC/USDT']
            self.assertTrue(b.evaluate_exit('BTC/USDT',{'low':p.stop_price-0.01,'high':p.stop_price,'close':p.stop_price}))
            self.assertNotIn('BTC/USDT',b.positions)
            self.assertEqual(b.closed_trades,1)


    def _run_broker_exit(self, candle):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "test.db")
            journal = Journal(db_path)
            broker = PaperBroker(100, 0.001, 0, journal)

            self.assertTrue(
                broker.enter_long("BTC/USDT", 0.1, 100, 0.01, 0.02, "test")
            )
            self.assertTrue(broker.evaluate_exit("BTC/USDT", candle))

            import sqlite3
            con = sqlite3.connect(db_path)
            try:
                return con.execute(
                    "SELECT exit_price, reason FROM trades"
                ).fetchone()
            finally:
                con.close()

    def test_paper_broker_stop_gap_uses_worse_open(self):
        price, reason = self._run_broker_exit({
            "open": 95.0, "low": 94.0, "high": 100.0, "close": 96.0
        })
        self.assertEqual(reason, "stop_loss")
        self.assertEqual(price, 95.0)

    def test_paper_broker_target_gap_uses_better_open(self):
        price, reason = self._run_broker_exit({
            "open": 105.0, "low": 104.0, "high": 106.0, "close": 105.5
        })
        self.assertEqual(reason, "take_profit")
        self.assertEqual(price, 105.0)

    def test_paper_broker_both_levels_touched_uses_stop_first(self):
        price, reason = self._run_broker_exit({
            "open": 100.0, "low": 98.0, "high": 103.0, "close": 101.0
        })
        self.assertEqual(reason, "stop_loss")
        self.assertEqual(price, 99.0)


    def test_paper_broker_restores_open_position_after_restart(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "restart.db")

            first = PaperBroker(100, 0.001, 0, Journal(db_path))
            self.assertTrue(
                first.enter_long("BTC/USDT", 0.1, 100, 0.01, 0.02, "test")
            )

            second = PaperBroker(100, 0.001, 0, Journal(db_path))

            self.assertAlmostEqual(second.cash, first.cash)
            self.assertIn("BTC/USDT", second.positions)
            restored = second.positions["BTC/USDT"]
            original = first.positions["BTC/USDT"]

            self.assertEqual(restored.trade_id, original.trade_id)
            self.assertAlmostEqual(restored.qty, original.qty)
            self.assertAlmostEqual(restored.entry_price, original.entry_price)
            self.assertAlmostEqual(restored.stop_price, original.stop_price)
            self.assertAlmostEqual(restored.target_price, original.target_price)

    def test_recovered_position_can_close_and_restore_statistics(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = os.path.join(td, "close_restart.db")

            first = PaperBroker(100, 0.001, 0, Journal(db_path))
            self.assertTrue(
                first.enter_long("BTC/USDT", 0.1, 100, 0.01, 0.02, "test")
            )

            recovered = PaperBroker(100, 0.001, 0, Journal(db_path))
            position = recovered.positions["BTC/USDT"]

            self.assertTrue(recovered.evaluate_exit("BTC/USDT", {
                "open": 98.0,
                "low": 98.0,
                "high": 100.0,
                "close": 98.5
            }))

            self.assertNotIn("BTC/USDT", recovered.positions)
            self.assertEqual(recovered.closed_trades, 1)
            self.assertEqual(recovered.losses, 1)
            self.assertEqual(recovered.wins, 0)
            self.assertAlmostEqual(recovered.cash, 99.7802, places=6)

            # A third broker instance must recover the closed-trade statistics.
            third = PaperBroker(100, 0.001, 0, Journal(db_path))
            self.assertAlmostEqual(third.cash, recovered.cash, places=8)
            self.assertEqual(third.closed_trades, 1)
            self.assertEqual(third.losses, 1)
            self.assertAlmostEqual(third.realized_pnl, -0.2198, places=6)
            self.assertEqual(len(third.positions), 0)


if __name__=='__main__': unittest.main()


