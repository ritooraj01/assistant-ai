"""
Paper Trading Engine for Testing Strategies
Simulates live trading with virtual money
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


PAPER_TRADING_DIR = Path(__file__).parent / "paper_trading"
HISTORY_FILE = PAPER_TRADING_DIR / "history.json"
POSITIONS_FILE = PAPER_TRADING_DIR / "positions.json"


class PaperTradingEngine:
    """Manages virtual positions with SL/TP"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: List[Dict] = []
        self.history: List[Dict] = []
        
        # Create directory if not exists
        PAPER_TRADING_DIR.mkdir(exist_ok=True)
        
        # Load existing data
        self._load_state()
    
    def _load_state(self):
        """Load positions and history from disk"""
        if POSITIONS_FILE.exists():
            with open(POSITIONS_FILE, 'r') as f:
                data = json.load(f)
                self.positions = data.get('positions', [])
                self.capital = data.get('capital', self.initial_capital)
        
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r') as f:
                self.history = json.load(f)
    
    def _save_state(self):
        """Save positions and history to disk"""
        with open(POSITIONS_FILE, 'w') as f:
            json.dump({
                'capital': self.capital,
                'positions': self.positions,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
        
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def open_position(
        self,
        symbol: str,
        action: str,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        take_profit: float,
        signal_confidence: float = 0.0,
        ml_score: Optional[float] = None
    ) -> Dict:
        """Open a new paper trading position"""
        
        direction = 1 if action in ["BUY", "LONG"] else -1
        position_value = entry_price * quantity
        
        if position_value > self.capital:
            return {
                "success": False,
                "error": f"Insufficient capital: need ₹{position_value}, have ₹{self.capital}"
            }
        
        position = {
            "id": len(self.history) + len(self.positions) + 1,
            "symbol": symbol,
            "action": action,
            "direction": direction,
            "entry_price": entry_price,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "entry_time": datetime.now().isoformat(),
            "signal_confidence": signal_confidence,
            "ml_score": ml_score,
            "status": "OPEN"
        }
        
        self.positions.append(position)
        self.capital -= position_value
        self._save_state()
        
        return {
            "success": True,
            "position": position,
            "remaining_capital": self.capital
        }
    
    def update_positions(self, current_price: float, symbol: str):
        """Check all open positions and close if SL/TP hit"""
        
        closed_positions = []
        
        for pos in self.positions[:]:  # Iterate over copy
            if pos["symbol"] != symbol:
                continue
            
            direction = pos["direction"]
            entry = pos["entry_price"]
            sl = pos["stop_loss"]
            tp = pos["take_profit"]
            
            should_close = False
            exit_reason = None
            exit_price = current_price
            
            if direction == 1:  # LONG
                if current_price <= sl:
                    should_close = True
                    exit_reason = "STOP_LOSS"
                    exit_price = sl
                elif current_price >= tp:
                    should_close = True
                    exit_reason = "TAKE_PROFIT"
                    exit_price = tp
            else:  # SHORT
                if current_price >= sl:
                    should_close = True
                    exit_reason = "STOP_LOSS"
                    exit_price = sl
                elif current_price <= tp:
                    should_close = True
                    exit_reason = "TAKE_PROFIT"
                    exit_price = tp
            
            if should_close:
                pnl = (exit_price - entry) * direction * pos["quantity"]
                pnl_pct = (exit_price - entry) / entry * direction * 100
                
                pos["exit_price"] = exit_price
                pos["exit_time"] = datetime.now().isoformat()
                pos["exit_reason"] = exit_reason
                pos["pnl"] = pnl
                pos["pnl_pct"] = pnl_pct
                pos["status"] = "CLOSED"
                
                self.capital += (entry * pos["quantity"] + pnl)
                self.history.append(pos)
                self.positions.remove(pos)
                closed_positions.append(pos)
        
        if closed_positions:
            self._save_state()
        
        return closed_positions
    
    def close_position(self, position_id: int, current_price: float, reason: str = "MANUAL") -> Optional[Dict]:
        """Manually close a position"""
        
        for pos in self.positions:
            if pos["id"] == position_id:
                direction = pos["direction"]
                entry = pos["entry_price"]
                
                pnl = (current_price - entry) * direction * pos["quantity"]
                pnl_pct = (current_price - entry) / entry * direction * 100
                
                pos["exit_price"] = current_price
                pos["exit_time"] = datetime.now().isoformat()
                pos["exit_reason"] = reason
                pos["pnl"] = pnl
                pos["pnl_pct"] = pnl_pct
                pos["status"] = "CLOSED"
                
                self.capital += (entry * pos["quantity"] + pnl)
                self.history.append(pos)
                self.positions.remove(pos)
                self._save_state()
                
                return pos
        
        return None
    
    def get_stats(self) -> Dict:
        """Get paper trading statistics"""
        
        if not self.history:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "avg_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0,
                "capital": self.capital,
                "roi": 0
            }
        
        df = pd.DataFrame(self.history)
        wins = (df["pnl"] > 0).sum()
        total = len(df)
        
        return {
            "total_trades": total,
            "open_positions": len(self.positions),
            "win_rate": wins / total * 100 if total > 0 else 0,
            "total_pnl": df["pnl"].sum(),
            "avg_pnl": df["pnl"].mean(),
            "avg_pnl_pct": df["pnl_pct"].mean(),
            "best_trade": df["pnl"].max(),
            "worst_trade": df["pnl"].min(),
            "capital": self.capital,
            "initial_capital": self.initial_capital,
            "roi": (self.capital - self.initial_capital) / self.initial_capital * 100
        }
    
    def reset(self):
        """Reset paper trading (start fresh)"""
        self.capital = self.initial_capital
        self.positions = []
        self.history = []
        self._save_state()


# Global instance
_paper_engine = None

def get_paper_engine() -> PaperTradingEngine:
    """Get or create paper trading engine"""
    global _paper_engine
    if _paper_engine is None:
        _paper_engine = PaperTradingEngine()
    return _paper_engine
