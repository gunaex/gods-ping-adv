"""
Paper Trading Performance Tracker
Tracks balance, P/L, and trade performance over time for paper trading mode
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.db import Base
from app.models import Trade, BotConfig
import json


class PaperTradingSnapshot(Base):
    """Daily snapshot of paper trading performance"""
    __tablename__ = "paper_trading_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    symbol = Column(String, index=True)
    bot_type = Column(String)  # 'gods_hand', 'grid', 'dca'
    
    # Snapshot timing
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Balance tracking
    starting_balance = Column(Float, default=0.0)  # Initial paper balance
    current_balance = Column(Float, default=0.0)   # Current paper balance
    
    # Position tracking
    quantity_held = Column(Float, default=0.0)     # Amount of asset held
    avg_buy_price = Column(Float, default=0.0)     # Average buy price
    current_price = Column(Float, default=0.0)     # Current market price
    
    # P/L tracking
    realized_pl = Column(Float, default=0.0)       # Closed position P/L
    unrealized_pl = Column(Float, default=0.0)     # Open position P/L
    total_pl = Column(Float, default=0.0)          # Total P/L
    pl_percent = Column(Float, default=0.0)        # % return
    
    # Trade statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)      # Max % loss from peak
    sharpe_ratio = Column(Float, default=0.0)       # Risk-adjusted return


def calculate_paper_performance(user_id: int, symbol: str, bot_type: str, db: Session) -> dict:
    """Calculate current paper trading performance"""
    # Get config
    config = db.query(BotConfig).filter(BotConfig.user_id == user_id).first()
    if not config:
        return None
    
    starting_balance = config.budget
    
    # Get all paper trades for this symbol
    trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.symbol == symbol,
        Trade.bot_type == bot_type,
        Trade.status.in_(['completed_paper', 'simulated'])
    ).order_by(Trade.timestamp).all()
    
    if not trades:
        return {
            'starting_balance': starting_balance,
            'current_balance': starting_balance,
            'quantity_held': 0.0,
            'avg_buy_price': 0.0,
            'current_price': 0.0,
            'realized_pl': 0.0,
            'unrealized_pl': 0.0,
            'total_pl': 0.0,
            'pl_percent': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0
        }
    
    # Calculate position
    quantity_held = 0.0
    total_cost = 0.0
    cash_balance = starting_balance
    realized_pl = 0.0
    
    buy_trades = []
    sell_trades = []
    
    for trade in trades:
        price = trade.filled_price or trade.price
        amount = trade.amount
        cost = amount * price
        
        if trade.side == 'BUY':
            quantity_held += amount
            total_cost += cost
            cash_balance -= cost
            buy_trades.append(trade)
        elif trade.side == 'SELL':
            # Calculate realized P/L for this sale
            if quantity_held > 0:
                avg_cost = total_cost / quantity_held if quantity_held > 0 else 0
                sale_pl = (price - avg_cost) * amount
                realized_pl += sale_pl
                
                # Update position
                quantity_held -= amount
                if quantity_held > 0:
                    total_cost = quantity_held * avg_cost
                else:
                    total_cost = 0
                
                cash_balance += cost
                sell_trades.append((trade, sale_pl))
    
    # Get current market price
    current_price = trades[-1].filled_price or trades[-1].price
    
    # Calculate unrealized P/L on remaining position
    avg_buy_price = total_cost / quantity_held if quantity_held > 0 else 0
    unrealized_pl = (current_price - avg_buy_price) * quantity_held if quantity_held > 0 else 0
    
    # Total balance
    position_value = quantity_held * current_price
    current_balance = cash_balance + position_value
    total_pl = current_balance - starting_balance
    pl_percent = (total_pl / starting_balance * 100) if starting_balance > 0 else 0
    
    # Win/loss statistics
    winning_trades = len([t for t, pl in sell_trades if pl > 0])
    losing_trades = len([t for t, pl in sell_trades if pl <= 0])
    total_closed_trades = len(sell_trades)
    win_rate = (winning_trades / total_closed_trades * 100) if total_closed_trades > 0 else 0
    
    return {
        'starting_balance': starting_balance,
        'current_balance': current_balance,
        'cash_balance': cash_balance,
        'position_value': position_value,
        'quantity_held': quantity_held,
        'avg_buy_price': avg_buy_price,
        'current_price': current_price,
        'realized_pl': realized_pl,
        'unrealized_pl': unrealized_pl,
        'total_pl': total_pl,
        'pl_percent': pl_percent,
        'total_trades': len(trades),
        'buy_trades': len(buy_trades),
        'sell_trades': total_closed_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate
    }


def save_paper_snapshot(user_id: int, symbol: str, bot_type: str, db: Session):
    """Save current paper trading performance as a snapshot"""
    perf = calculate_paper_performance(user_id, symbol, bot_type, db)
    if not perf:
        return
    
    snapshot = PaperTradingSnapshot(
        user_id=user_id,
        symbol=symbol,
        bot_type=bot_type,
        timestamp=datetime.utcnow(),
        starting_balance=perf['starting_balance'],
        current_balance=perf['current_balance'],
        quantity_held=perf['quantity_held'],
        avg_buy_price=perf['avg_buy_price'],
        current_price=perf['current_price'],
        realized_pl=perf['realized_pl'],
        unrealized_pl=perf['unrealized_pl'],
        total_pl=perf['total_pl'],
        pl_percent=perf['pl_percent'],
        total_trades=perf['total_trades'],
        winning_trades=perf['winning_trades'],
        losing_trades=perf['losing_trades'],
        win_rate=perf['win_rate']
    )
    
    db.add(snapshot)
    db.commit()
    return snapshot


def get_paper_performance_history(user_id: int, symbol: str, bot_type: str, days: int, db: Session) -> list:
    """Get paper trading performance history for the last N days"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    snapshots = db.query(PaperTradingSnapshot).filter(
        PaperTradingSnapshot.user_id == user_id,
        PaperTradingSnapshot.symbol == symbol,
        PaperTradingSnapshot.bot_type == bot_type,
        PaperTradingSnapshot.timestamp >= cutoff
    ).order_by(PaperTradingSnapshot.timestamp).all()
    
    return [{
        'timestamp': s.timestamp.isoformat(),
        'current_balance': s.current_balance,
        'total_pl': s.total_pl,
        'pl_percent': s.pl_percent,
        'total_trades': s.total_trades,
        'win_rate': s.win_rate
    } for s in snapshots]
