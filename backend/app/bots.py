"""
Trading Bots Service
Grid Bot, DCA Bot, and Gods Hand Autonomous Trading
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models import BotConfig, Trade
from app.market import get_current_price, execute_market_trade
from app.ai_engine import get_trading_recommendation, calculate_risk_assessment
from app.logging_models import Log, LogCategory, LogLevel
from app.position_tracker import get_current_position, calculate_incremental_amount, calculate_position_pl
import json
from app.db import get_db
from app.email_utils import send_gmail, format_trade_email
from app.notification_limiter import can_send_notification, mark_notification_sent


# Bot status tracking (in-memory, use Redis in production)
bot_status = {}
bot_tasks = {}


async def start_grid_bot(user_id: int, config: BotConfig, db: Session) -> dict:
    """
    Start Grid Trading Bot
    Places buy/sell orders at predefined price levels
    """
    if f"grid_{user_id}" in bot_status:
        return {"status": "error", "message": "Grid bot already running"}
    
    bot_status[f"grid_{user_id}"] = "running"
    
    try:
        symbol = config.symbol
        lower_price = config.grid_lower_price
        upper_price = config.grid_upper_price
        levels = config.grid_levels
        budget = config.budget
        
        # Calculate grid levels
        price_step = (upper_price - lower_price) / levels
        grid_levels_prices = [lower_price + i * price_step for i in range(levels + 1)]
        
        # Calculate amount per level
        amount_per_level = budget / levels
        
        # Get current price
        ticker = await get_current_price(symbol)
        current_price = ticker['last']
        
        # Paper trading simulation
        if config.paper_trading:
            trades_placed = []
            
            # Place buy orders below current price
            for price in grid_levels_prices:
                if price < current_price:
                    trade = Trade(
                        user_id=user_id,
                        symbol=symbol,
                        side="BUY",
                        amount=amount_per_level / price,
                        price=price,
                        filled_price=price,
                        status="completed_paper",
                        bot_type="grid",
                        timestamp=datetime.utcnow()
                    )
                    db.add(trade)
                    trades_placed.append({"side": "BUY", "price": price})
                
                # Place sell orders above current price
                elif price > current_price:
                    trade = Trade(
                        user_id=user_id,
                        symbol=symbol,
                        side="SELL",
                        amount=amount_per_level / price,
                        price=price,
                        filled_price=price,
                        status="completed_paper",
                        bot_type="grid",
                        timestamp=datetime.utcnow()
                    )
                    db.add(trade)
                    trades_placed.append({"side": "SELL", "price": price})
            
            db.commit()
            
            return {
                "status": "success",
                "mode": "paper",
                "symbol": symbol,
                "grid_levels": grid_levels_prices,
                "trades_placed": len(trades_placed),
                "message": f"Grid bot started (paper trading) with {levels} levels"
            }
        
        else:
            # Real trading (simplified - full implementation requires order monitoring)
            return {
                "status": "success",
                "mode": "live",
                "symbol": symbol,
                "message": "Grid bot started (live trading)",
                "note": "Full implementation requires continuous order monitoring"
            }
            
    except Exception as e:
        bot_status[f"grid_{user_id}"] = "error"
        return {"status": "error", "message": str(e)}


async def start_dca_bot(user_id: int, config: BotConfig, db: Session) -> dict:
    """
    Start DCA (Dollar Cost Averaging) Bot
    Buys at regular intervals regardless of price
    """
    if f"dca_{user_id}" in bot_status:
        return {"status": "error", "message": "DCA bot already running"}
    
    bot_status[f"dca_{user_id}"] = "running"
    
    try:
        symbol = config.symbol
        amount_per_period = config.dca_amount_per_period
        interval_days = config.dca_interval_days
        
        # Get current price
        ticker = await get_current_price(symbol)
        current_price = ticker['last']
        
        # Calculate buy amount
        buy_amount = amount_per_period / current_price
        
        if config.paper_trading:
            # Execute paper trade
            trade = Trade(
                user_id=user_id,
                symbol=symbol,
                side="BUY",
                amount=buy_amount,
                price=current_price,
                filled_price=current_price,
                status="completed_paper",
                bot_type="dca",
                timestamp=datetime.utcnow()
            )
            db.add(trade)
            db.commit()
            
            next_buy = datetime.utcnow() + timedelta(days=interval_days)
            
            return {
                "status": "success",
                "mode": "paper",
                "symbol": symbol,
                "amount": buy_amount,
                "price": current_price,
                "next_buy": next_buy.isoformat(),
                "message": f"DCA buy executed (paper). Next buy in {interval_days} days"
            }
        else:
            # Real trading
            result = await execute_market_trade(user_id, symbol, "BUY", buy_amount, db)
            
            return {
                "status": "success",
                "mode": "live",
                "result": result,
                "message": "DCA buy executed (live)"
            }
            
    except Exception as e:
        bot_status[f"dca_{user_id}"] = "error"
        return {"status": "error", "message": str(e)}


async def gods_hand_once(user_id: int, config: BotConfig, db: Session) -> dict:
    """Execute one Gods Hand iteration with incremental position building."""
    symbol = config.symbol

    # Get AI recommendation and risk
    recommendation = await get_trading_recommendation(symbol, config)
    risk_assessment = await calculate_risk_assessment(symbol, config)

    action = recommendation.get('action', 'HOLD')
    confidence = recommendation.get('confidence', 0.0)

    # Get current position including fees
    current_position = get_current_position(user_id, symbol, db)

    # If paper trading and action is SELL, allow sell even if never bought (simulate as owned)
    if config.paper_trading and action == 'SELL' and current_position['quantity'] == 0:
        # Simulate owning the asset using the configured budget
        simulated_budget = (config.budget or 10000.0)
        current_position['quantity'] = simulated_budget / risk_assessment['current_price']
        current_position['cost_basis'] = simulated_budget
    
    # Profit protection: trailing take-profit and hard stop-loss
    current_price = risk_assessment['current_price']
    pl_data = calculate_position_pl(current_position, current_price)
    
    # Check hard stop-loss (force SELL if loss exceeds threshold)
    if current_position['quantity'] > 0 and pl_data['pl_percent'] < -config.hard_stop_loss_percent:
        action = 'SELL'
        confidence = 1.0  # Override with high confidence
        step_percent = 100.0  # Close entire position
        recommendation['action'] = 'SELL'
        recommendation['reasoning'] = [f"STOP LOSS: P/L {pl_data['pl_percent']:.2f}% < -{config.hard_stop_loss_percent}%"]
    
    # Check trailing take-profit (force partial SELL if profit is good but declining)
    elif current_position['quantity'] > 0 and pl_data['pl_percent'] >= config.trailing_take_profit_percent:
        # If we're in profit and AI says HOLD or confidence is weak, take partial profit
        if action == 'HOLD' or confidence < 0.65:
            action = 'SELL'
            confidence = 0.85
            step_percent = config.exit_step_percent
            recommendation['action'] = 'SELL'
            recommendation['reasoning'] = [f"TRAILING TP: P/L {pl_data['pl_percent']:.2f}% >= {config.trailing_take_profit_percent}%"]

    # Calculate incremental step amount (after any profit protection overrides)
    max_position_size = risk_assessment['recommended_position_size']
    
    # 🔍 DEBUG: Position calculation
    print(f"🔍 Position Debug for {symbol}:")
    print(f"   Current position value: ${current_position['position_value_usd']:.2f}")
    print(f"   Max position size (from AI): ${max_position_size:.2f}")
    print(f"   Budget: ${config.budget:.2f}")
    print(f"   Position Size Ratio: {config.position_size_ratio * 100:.1f}%")
    print(f"   Expected max: ${config.budget * config.position_size_ratio:.2f}")
    current_fill = (current_position['position_value_usd'] / max_position_size * 100) if max_position_size > 0 else 0
    print(f"   Current fill: {current_fill:.1f}% of max_position_size")
    
    # Dynamic step sizing: scale by confidence (0.5-1.0 confidence → 0.5x-1.5x step)
    confidence_multiplier = 0.5 + (confidence * 1.0) if confidence > 0 else 1.0
    base_step_percent = config.entry_step_percent if action == 'BUY' else config.exit_step_percent
    step_percent = min(base_step_percent * confidence_multiplier, 100.0)

    incremental_calc = calculate_incremental_amount(
        current_position,
        max_position_size,
        step_percent,
        action
    )

    # Helper: send notification email with rate limiting
    def maybe_send_notification(subject, body, trigger, notification_type=None, cooldown_hours=1):
        if not config.notification_email:
            return
        
        # Apply rate limiting for failure and position_size notifications
        if notification_type and cooldown_hours > 0:
            if not can_send_notification(user_id, notification_type, cooldown_hours):
                from app.notification_limiter import get_time_until_next
                remaining = get_time_until_next(user_id, notification_type, cooldown_hours)
                print(f"⏳ Notification '{notification_type}' rate limited. Can send again in {remaining:.1f} hours")
                return
        
        sent = False
        if trigger == 'action' and config.notify_on_action:
            sent = send_gmail(config.notification_email, subject, body, config.gmail_user, config.gmail_app_password)
        elif trigger == 'position_size' and config.notify_on_position_size:
            sent = send_gmail(config.notification_email, subject, body, config.gmail_user, config.gmail_app_password)
        elif trigger == 'failure' and config.notify_on_failure:
            sent = send_gmail(config.notification_email, subject, body, config.gmail_user, config.gmail_app_password)
        
        # Mark notification as sent if successful and rate limited
        if sent and notification_type:
            mark_notification_sent(user_id, notification_type)

    # Format AI decision calculation summary for message
    signal_breakdown = recommendation.get('signal_breakdown', [])
    buy_signals = sum(1 for s in signal_breakdown if 'BUY' in s)
    sell_signals = sum(1 for s in signal_breakdown if 'SELL' in s)
    hold_signals = sum(1 for s in signal_breakdown if 'HOLD' in s and 'BUY' not in s and 'SELL' not in s)

    # Derive position metrics safely (keys may not exist yet in early cycles)
    max_pos = float(max_position_size or 0.0)
    current_val = float(current_position.get('position_value_usd', 0.0))
    fill_percent = (current_val / max_pos * 100) if max_pos > 0 else 0.0
    available_to_add = max(0.0, max_pos - current_val)
    step_amount = float(incremental_calc.get('step_amount_usd', incremental_calc.get('suggested_amount_usd', 0.0)))

    decision_summary = (
        f"AI DECISION CALCULATION for {symbol}\n\n"
        f"-- AI Recommendation: {action} @{confidence:.2f}\n"
        f"   Signals analyzed: {len(signal_breakdown)}\n"
        + ("".join([f"   • {s}\n" for s in signal_breakdown[:5]]) or "   • (no signals logged)\n")
        + f"\n-- Confidence: BUY={buy_signals}, SELL={sell_signals}, HOLD={hold_signals}\n"
        f"   - Confidence: {confidence:.3f} (average of {len(signal_breakdown)} factors)\n\n"
        f"Final Decision: {action} @ {confidence:.0%} confidence\n\n"
        f"-- Position Setup for {symbol}:\n"
        f"   - Max Position Size: ${max_pos:.2f}\n"
        f"   - Current Held (cost basis value): ${current_val:.2f} ({fill_percent:.1f}%)\n"
        f"   - Available Capacity: ${available_to_add:.2f}\n"
        f"   - Incremental Trade (step): ${step_amount:.2f}\n"
    )

    # Log AI thinking with position info
    thinking_log = Log(
        timestamp=datetime.utcnow(),
        category=LogCategory.AI_THINKING,
        level=LogLevel.INFO,
        message=decision_summary,
        details=json.dumps({
            "recommendation": recommendation,
            "risk_assessment": risk_assessment,
            "signal_breakdown": signal_breakdown,
            "confidence_calculation": f"Average of {len(signal_breakdown)} indicator signals",
            "current_position": current_position,
            "incremental_calculation": incremental_calc,
            "step_settings": {
                "entry_step_percent": config.entry_step_percent,
                "exit_step_percent": config.exit_step_percent
            }
        }, indent=2),
        user_id=user_id,
        symbol=symbol,
        bot_type="gods_hand",
        ai_recommendation=action,
        ai_confidence=str(confidence),
    )
    db.add(thinking_log)
    db.commit()

    # Confidence gate
    if confidence < config.min_confidence:
        action_log = Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.AI_ACTION,
            level=LogLevel.INFO,
            message=f"Gods Hand HOLD: confidence {confidence} < min {config.min_confidence}",
            details=json.dumps({
                "reason": "low_confidence",
                "min_confidence": config.min_confidence,
                "current_position_fill": f"{incremental_calc['current_fill_percent']:.1f}%"
            }),
            user_id=user_id,
            symbol=symbol,
            bot_type="gods_hand",
            ai_recommendation=action,
            ai_confidence=str(confidence),
            ai_executed="no",
            execution_reason=f"Confidence {confidence} below minimum {config.min_confidence}"
        )
        db.add(action_log)
        db.commit()
        # Notify on AI failure/skipped action (once per hour)
        maybe_send_notification(
            subject=f"Gods Hand: AI Skipped Action for {symbol}",
            body=f"AI recommended HOLD due to low confidence ({confidence} < {config.min_confidence}).",
            trigger='failure',
            notification_type='failure',
            cooldown_hours=1
        )
        return {
            "status": "hold",
            "mode": "paper" if config.paper_trading else "live",
            "symbol": symbol,
            "action": "HOLD",
            "confidence": confidence,
            "reason": f"Confidence {confidence} below minimum {config.min_confidence}",
            "recommendation": recommendation,
            "risk_assessment": risk_assessment,
            "current_position": current_position
        }

    # Check if incremental trade can execute
    if not incremental_calc['can_execute']:
        action_log = Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.AI_ACTION,
            level=LogLevel.WARNING,
            message=f"Gods Hand HOLD: {incremental_calc['reason']}",
            details=json.dumps({
                "reason": "position_limit",
                "incremental_calculation": incremental_calc,
                "current_position": current_position
            }),
            user_id=user_id,
            symbol=symbol,
            bot_type="gods_hand",
            ai_recommendation=action,
            ai_confidence=str(confidence),
            ai_executed="no",
            execution_reason=incremental_calc['reason']
        )
        db.add(action_log)
        db.commit()
        # Notify on AI failure/skipped action (once per hour)
        maybe_send_notification(
            subject=f"Gods Hand: Position Limit for {symbol}",
            body=f"AI recommended HOLD due to position limit: {incremental_calc['reason']}",
            trigger='failure',
            notification_type='failure',
            cooldown_hours=1
        )
        return {
            "status": "hold",
            "mode": "paper" if config.paper_trading else "live",
            "symbol": symbol,
            "action": "HOLD",
            "confidence": confidence,
            "reason": incremental_calc['reason'],
            "recommendation": recommendation,
            "risk_assessment": risk_assessment,
            "current_position": current_position,
            "incremental_calculation": incremental_calc
        }

    # Execute incremental trade
    if action in ['BUY', 'SELL']:
        step_amount_usd = incremental_calc['step_amount_usd']
        current_price = risk_assessment['current_price']
        
        # Calculate crypto amount for this step
        if action == 'BUY':
            crypto_amount = step_amount_usd / current_price
        else:  # SELL
            # For sell, calculate crypto amount from current holdings
            sell_percent = config.exit_step_percent / 100
            crypto_amount = current_position['quantity'] * sell_percent

        if config.paper_trading:
            trade = Trade(
                user_id=user_id,
                symbol=symbol,
                side=action,
                amount=crypto_amount,
                price=current_price,
                filled_price=current_price,
                status="completed_paper",
                bot_type="gods_hand",
                timestamp=datetime.utcnow()
            )
            db.add(trade)
            db.commit()

            action_log = Log(
                timestamp=datetime.utcnow(),
                category=LogCategory.AI_ACTION,
                level=LogLevel.INFO,
                message=f"Gods Hand executed {action} {step_percent}% step (paper)",
                details=json.dumps({
                    "crypto_amount": crypto_amount,
                    "usd_value": step_amount_usd,
                    "price": current_price,
                    "position_before": f"{incremental_calc['current_fill_percent']:.1f}%",
                    "position_after": f"{incremental_calc['after_fill_percent']:.1f}%",
                    "incremental_reason": incremental_calc['reason'],
                    "fees_info": "Fees included in position tracking (0.1%)"
                }),
                user_id=user_id,
                symbol=symbol,
                bot_type="gods_hand",
                ai_recommendation=action,
                ai_confidence=str(confidence),
                ai_executed="yes",
            )
            db.add(action_log)
            db.commit()
            
            # Calculate P/L and account balance for email
            updated_position = get_current_position(user_id, symbol, db)
            pl_data = calculate_position_pl(updated_position, current_price)
            
            # Calculate account balance (position value + remaining budget)
            account_balance_usd = updated_position['cost_basis'] + (config.budget - updated_position['cost_basis'])
            
            # Convert to fiat if needed
            from app.market import convert_to_fiat
            if config.fiat_currency == 'THB':
                trade_value_fiat = await convert_to_fiat(step_amount_usd, 'THB')
                account_balance_fiat = await convert_to_fiat(account_balance_usd, 'THB')
            else:
                trade_value_fiat = step_amount_usd
                account_balance_fiat = account_balance_usd
            
            # Send formatted email notification
            if config.notification_email and config.notify_on_action:
                subject, body = format_trade_email(
                    action=action,
                    trade_value_fiat=trade_value_fiat,
                    confidence=confidence,
                    pl_percent=pl_data['pl_percent'] if action == 'SELL' else None,
                    account_balance_fiat=account_balance_fiat,
                    fiat_currency=config.fiat_currency,
                    timezone='Asia/Bangkok'
                )
                send_gmail(config.notification_email, subject, body, config.gmail_user, config.gmail_app_password)
            
            # Notify if position size ratio reached (once per day)
            if config.notify_on_position_size and incremental_calc['after_fill_percent'] >= config.position_size_ratio * 100:
                maybe_send_notification(
                    subject=f"Gods Hand: Position Size Ratio Reached for {symbol}",
                    body=f"Position size ratio reached {incremental_calc['after_fill_percent']:.1f}% (target: {config.position_size_ratio*100:.1f}%)",
                    trigger='position_size',
                    notification_type='position_size',
                    cooldown_hours=24
                )
            return {
                "status": "success",
                "mode": "paper",
                "action": action,
                "symbol": symbol,
                "crypto_amount": crypto_amount,
                "usd_value": step_amount_usd,
                "price": current_price,
                "confidence": confidence,
                "position_fill_before": incremental_calc['current_fill_percent'],
                "position_fill_after": incremental_calc['after_fill_percent'],
                "recommendation": recommendation,
                "risk_assessment": risk_assessment,
                "current_position": current_position,
                "message": f"Gods Hand executed {action} {step_percent}% step (paper trading)"
            }
        else:
            # Live trading
            result = await execute_market_trade(user_id, symbol, action, crypto_amount, db)

            action_log = Log(
                timestamp=datetime.utcnow(),
                category=LogCategory.AI_ACTION,
                level=LogLevel.INFO,
                message=f"Gods Hand executed {action} {step_percent}% step (live)",
                details=json.dumps({
                    "crypto_amount": crypto_amount,
                    "usd_value": step_amount_usd,
                    "result": result,
                    "position_before": f"{incremental_calc['current_fill_percent']:.1f}%",
                    "position_after": f"{incremental_calc['after_fill_percent']:.1f}%",
                    "incremental_reason": incremental_calc['reason']
                }),
                user_id=user_id,
                symbol=symbol,
                bot_type="gods_hand",
                ai_recommendation=action,
                ai_confidence=str(confidence),
                ai_executed="yes",
            )
            db.add(action_log)
            db.commit()
            
            # Persist live trade record for performance stats
            try:
                live_trade = Trade(
                    user_id=user_id,
                    symbol=symbol,
                    side=action,
                    amount=crypto_amount,
                    price=result.get('price') or current_price,
                    filled_price=(result.get('price') or current_price),
                    status=result.get('status') or 'completed_live',
                    bot_type='gods_hand',
                    timestamp=datetime.utcnow()
                )
                db.add(live_trade)
                db.commit()
            except Exception:
                # Do not fail loop if persisting trade fails
                pass

            return {
                "status": "success",
                "mode": "live",
                "action": action,
                "symbol": symbol,
                "crypto_amount": crypto_amount,
                "usd_value": step_amount_usd,
                "price": result.get('price') or current_price,
                "confidence": confidence,
                "position_fill_before": incremental_calc['current_fill_percent'],
                "position_fill_after": incremental_calc['after_fill_percent'],
                "recommendation": recommendation,
                "risk_assessment": risk_assessment,
                "current_position": current_position,
                "trade_result": result,
                "message": f"Gods Hand executed {action} {step_percent}% step (live trading)"
            }
    else:
        action_log = Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.AI_ACTION,
            level=LogLevel.INFO,
            message="Gods Hand HOLD recommendation",
            user_id=user_id,
            symbol=symbol,
            bot_type="gods_hand",
            ai_recommendation="HOLD",
            ai_confidence=str(confidence),
            ai_executed="no",
            execution_reason="Recommendation HOLD"
        )
        db.add(action_log)
        db.commit()
        # Notify on AI failure/skipped action (once per hour)
        maybe_send_notification(
            subject=f"Gods Hand: AI HOLD for {symbol}",
            body=f"AI recommended HOLD. No action taken.",
            trigger='failure',
            notification_type='failure',
            cooldown_hours=1
        )
        return {
            "status": "hold",
            "mode": "paper" if config.paper_trading else "live",
            "symbol": symbol,
            "action": "HOLD",
            "confidence": confidence,
            "recommendation": recommendation,
            "risk_assessment": risk_assessment,
            "current_position": current_position,
            "message": "Gods Hand recommends HOLD"
        }


async def _gods_hand_loop(user_id: int, interval_seconds: int):
    """Background loop to run Gods Hand periodically until stopped."""
    import logging
    logger = logging.getLogger(__name__)
    
    key = f"gods_hand_{user_id}"
    bot_status[key] = "running"
    print(f"🚀 _gods_hand_loop STARTED for user {user_id}, interval={interval_seconds}s")
    logger.info(f"_gods_hand_loop started for user {user_id}, interval={interval_seconds}s")
    snapshot_counter = 0  # Track iterations for periodic snapshots
    iteration = 0
    try:
        while bot_status.get(key) == "running":
            iteration += 1
            print(f"🔄 Gods Hand loop iteration {iteration} for user {user_id} - status: {bot_status.get(key)}")
            logger.info(f"Gods Hand loop iteration {iteration} for user {user_id}")
            # Fresh DB session each iteration
            dbi = next(get_db())
            try:
                config = dbi.query(BotConfig).filter(BotConfig.user_id == user_id).first()
                if not config or not config.gods_hand_enabled:
                    print(f"⚠️ Config not found or gods_hand disabled for user {user_id}")
                    logger.warning(f"Config not found or gods_hand disabled for user {user_id}")
                    await asyncio.sleep(interval_seconds)
                    continue
                
                print(f"📊 Checking daily P/L for user {user_id}...")
                # Daily kill-switch: check realized P/L for today
                today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                today_trades = dbi.query(Trade).filter(
                    Trade.user_id == user_id,
                    Trade.symbol == config.symbol,
                    Trade.bot_type == 'gods_hand',
                    Trade.timestamp >= today_start,
                    Trade.status.in_(['completed_paper', 'completed_live', 'completed'])
                ).all()
                
                # Calculate today's realized P/L (only counts completed sell trades)
                daily_pl_percent = 0.0
                if today_trades:
                    buys_cost = sum(t.amount * (t.filled_price or t.price) for t in today_trades if t.side == 'BUY')
                    sells_revenue = sum(t.amount * (t.filled_price or t.price) for t in today_trades if t.side == 'SELL')
                    
                    # Only calculate P/L if we have both buys and sells (realized P/L)
                    # If we only have buys, P/L is 0 (unrealized, not a loss yet)
                    if buys_cost > 0 and sells_revenue > 0:
                        daily_pl_percent = ((sells_revenue - buys_cost) / buys_cost) * 100
                    else:
                        # No sells yet, so no realized loss
                        daily_pl_percent = 0.0
                
                print(f"💰 Daily P/L: {daily_pl_percent:.2f}% (limit: {config.max_daily_loss}%)")
                
                # Kill-switch: stop if daily loss exceeds max_daily_loss
                if daily_pl_percent < -config.max_daily_loss:
                    print(f"🚨 KILL-SWITCH TRIGGERED! Daily loss {daily_pl_percent:.2f}% exceeds limit {config.max_daily_loss}%")
                    bot_status[key] = "stopped"
                    err_log = Log(
                        timestamp=datetime.utcnow(),
                        category=LogCategory.BOT,
                        level=LogLevel.WARNING,
                        message=f"Gods Hand KILL-SWITCH: Daily loss {daily_pl_percent:.2f}% exceeds limit {config.max_daily_loss}%",
                        user_id=user_id,
                        bot_type="gods_hand",
                    )
                    dbi.add(err_log)
                    dbi.commit()
                    break
                
                print(f"🤖 Calling gods_hand_once...")
                await gods_hand_once(user_id, config, dbi)
                print(f"✅ gods_hand_once completed")
                
                # Save paper trading snapshot every 10 iterations (if paper trading)
                if config.paper_trading:
                    snapshot_counter += 1
                    if snapshot_counter >= 10:
                        print(f"📸 Saving paper trading snapshot...")
                        from app.paper_trading_tracker import save_paper_snapshot
                        save_paper_snapshot(user_id, config.symbol, 'gods_hand', dbi)
                        snapshot_counter = 0
                        print(f"✅ Snapshot saved")
                        
            except Exception as e:
                # Log loop error
                print(f"❌ Gods Hand loop error for user {user_id}: {str(e)}")
                import traceback
                traceback.print_exc()
                err_log = Log(
                    timestamp=datetime.utcnow(),
                    category=LogCategory.BOT,
                    level=LogLevel.ERROR,
                    message=f"Gods Hand loop error: {str(e)}",
                    user_id=user_id,
                    bot_type="gods_hand",
                )
                dbi.add(err_log)
                dbi.commit()
            finally:
                dbi.close()

            print(f"💤 Sleeping for {interval_seconds}s...")
            await asyncio.sleep(interval_seconds)
            print(f"⏰ Woke up! Checking status... bot_status[{key}] = {bot_status.get(key)}")
        
        # If we exit the loop, print why
        print(f"🔚 Exiting while loop. Final status: {bot_status.get(key)}")
    except asyncio.CancelledError:
        print(f"🛑 Gods Hand loop cancelled for user {user_id}")
        pass
    except Exception as e:
        print(f"💥 Gods Hand loop fatal error for user {user_id}: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"⏹️ Gods Hand loop STOPPED for user {user_id}")
        bot_status[key] = "stopped"


async def start_gods_hand_entry(user_id: int, db: Session, continuous: bool = True, interval_seconds: int = 60) -> dict:
    """Entry point: runs once and optionally starts background loop."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"start_gods_hand_entry called - user_id={user_id}, continuous={continuous}, interval={interval_seconds}")
    
    # Ensure not already running
    key = f"gods_hand_{user_id}"
    if continuous and key in bot_tasks:
        # Check if task is still alive
        if not bot_tasks[key].done():
            logger.info(f"Gods Hand already running for user {user_id}")
            return {"status": "running", "message": "Gods Hand already running"}
        else:
            # Clean up dead task
            logger.warning(f"Cleaning up dead Gods Hand task for user {user_id}")
            del bot_tasks[key]
            bot_status[key] = "stopped"

    config = db.query(BotConfig).filter(BotConfig.user_id == user_id).first()
    if not config:
        logger.error(f"No config found for user {user_id}")
        return {"status": "error", "message": "No configuration found"}
    
    # Enable gods_hand if not already enabled
    if not config.gods_hand_enabled:
        logger.info(f"Enabling gods_hand for user {user_id}")
        config.gods_hand_enabled = True
        db.commit()

    # Immediate one-off run to provide UI feedback
    logger.info(f"Running gods_hand_once for user {user_id}")
    result = await gods_hand_once(user_id, config, db)
    logger.info(f"gods_hand_once result: {result.get('status', 'unknown')}")

    # Start background loop if requested
    if continuous:
        logger.info(f"Starting continuous Gods Hand loop for user {user_id}")
        # Set status BEFORE creating task to avoid race condition
        bot_status[key] = "running"
        task = asyncio.create_task(_gods_hand_loop(user_id, interval_seconds))
        bot_tasks[key] = task
        logger.info(f"Background task created and stored. bot_status[{key}] = {bot_status[key]}")
        result["continuous_mode"] = True
        result["interval_seconds"] = interval_seconds
    else:
        logger.info(f"One-time execution only for user {user_id}")
        result["continuous_mode"] = False

    return result


async def stop_bot(bot_type: str, user_id: int, db: Session) -> dict:
    """Stop a running bot"""
    # Normalize bot type to internal key format (use underscores)
    normalized = bot_type.replace('-', '_') if bot_type else bot_type
    bot_key = f"{normalized}_{user_id}"
    
    if bot_key in bot_status:
        bot_status[bot_key] = "stopped"
        
        # Cancel any background tasks
        if bot_key in bot_tasks:
            bot_tasks[bot_key].cancel()
            del bot_tasks[bot_key]
        
        return {
            "status": "success",
            "message": f"{normalized} bot stopped"
        }
    else:
        return {
            "status": "info",
            "message": f"{normalized} bot is not running"
        }


async def get_bot_status(user_id: int, db: Session) -> dict:
    """Get status of all bots for user"""
    return {
        "grid": bot_status.get(f"grid_{user_id}", "stopped"),
        "dca": bot_status.get(f"dca_{user_id}", "stopped"),
        "gods_hand": bot_status.get(f"gods_hand_{user_id}", "stopped"),
        "timestamp": datetime.utcnow().isoformat()
    }
