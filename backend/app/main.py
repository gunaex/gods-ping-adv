"""
Gods Ping - FastAPI Backend
Main API endpoints for Shichi-Fukujin single-page trading platform
"""
import os
from fastapi import FastAPI, Depends, HTTPException, status, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
import time

from app.db import engine, get_db, Base
from app.models import User, Trade, BotConfig, ForecastSnapshot
from app.logging_models import Log, LogCategory, LogLevel
# Ensure all ORM models are imported before creating tables
from app.paper_trading_tracker import PaperTradingSnapshot
from app.auth import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    get_current_active_user, ensure_admin_exists, ADMIN_USERNAME,
    encrypt_api_key, decrypt_api_key
)

# Create database tables on startup (after all models are imported)

app = FastAPI(
    title="Gods Ping API",
    description="Shichi-Fukujin Trading Platform",
    version="1.0.0"
)

# Ensure DB tables exist once app starts
@app.on_event("startup")
def init_db():
    # Importing models above ensures SQLAlchemy knows all tables
    Base.metadata.create_all(bind=engine)

# CORS - Read from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug endpoint to verify active CORS configuration (remove in production later)
@app.get("/api/debug/cors")
def debug_cors():
    return {
        "allowed_origins": allowed_origins,
        "env_raw": os.getenv("CORS_ORIGINS"),
        "allow_origin_regex": r"https://.*\.vercel\.app",
        "note": "Remove /api/debug/cors in production once CORS verified."
    }


# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class CreateUserRequest(BaseModel):
    username: str
    password: str


class UpdateBotConfigRequest(BaseModel):
    symbol: Optional[str] = None
    fiat_currency: Optional[str] = None
    budget: Optional[float] = None
    paper_trading: Optional[bool] = None
    risk_level: Optional[str] = None
    min_confidence: Optional[float] = None
    position_size_ratio: Optional[float] = None
    max_daily_loss: Optional[float] = None
    entry_step_percent: Optional[float] = None
    exit_step_percent: Optional[float] = None
    trailing_take_profit_percent: Optional[float] = None
    hard_stop_loss_percent: Optional[float] = None
    grid_enabled: Optional[bool] = None
    grid_lower_price: Optional[float] = None
    grid_upper_price: Optional[float] = None
    grid_levels: Optional[int] = None
    dca_enabled: Optional[bool] = None
    dca_amount_per_period: Optional[float] = None
    dca_interval_days: Optional[int] = None
    gods_hand_enabled: Optional[bool] = None
    gods_mode_enabled: Optional[bool] = None
    tennis_mode_enabled: Optional[bool] = None
    kill_switch_cooldown_minutes: Optional[int] = None
    kill_switch_consecutive_breaches: Optional[int] = None
    notification_email: Optional[str] = None
    notify_on_action: Optional[bool] = None
    notify_on_position_size: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    gmail_user: Optional[str] = None
    gmail_app_password: Optional[str] = None


class UpdateAPIKeysRequest(BaseModel):
    binance_api_key: str
    binance_api_secret: str


class TradeRequest(BaseModel):
    symbol: str
    side: str  # BUY or SELL
    amount: float
    price: Optional[float] = None


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool
    created_at: Optional[str] = None


# Startup Event
@app.on_event("startup")
async def startup_event():
    """Initialize database with admin user"""
    from app.db import DATABASE_URL
    print(f"🚀 Startup: Connecting to DB (masked): {str(DATABASE_URL)[:15]}...")
    
    # Run schema migrations (add missing columns)
    from app.migration import run_db_migrations
    run_db_migrations()
    
    db = next(get_db())
    created = ensure_admin_exists(db)
    if created:
        print(f"✅ Admin user created: {ADMIN_USERNAME}")
    else:
        print(f"✅ Admin user exists: {ADMIN_USERNAME}")
    db.close()


# Health Check
@app.get("/")
async def root():
    """Root endpoint with server info"""
    return {
        "app": "Gods Ping (Shichi-Fukujin)",
        "status": "running",
        "version": "1.0.0",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "server_timezone": "UTC",
        "timestamp": int(time.time())
    }


# Authentication Endpoints
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with username and password"""
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token({"user_id": user.id, "username": user.username})
    refresh_token = create_refresh_token({"user_id": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@app.post("/api/auth/create-user")
async def create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin creates one additional user"""
    # Only admin can create users
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only admin can create users")
    
    # Check if user already exists
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check user count (max 2: admin + 1 user)
    user_count = db.query(User).count()
    if user_count >= 2:
        raise HTTPException(status_code=400, detail="Maximum user limit reached (1 additional user)")
    
    # Create new user
    new_user = User(
        username=request.username,
        hashed_password=get_password_hash(request.password),
        is_admin=False,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create default bot config for user
    bot_config = BotConfig(user_id=new_user.id)
    db.add(bot_config)
    db.commit()
    
    return {"message": "User created successfully", "user": new_user.to_dict()}


@app.get("/api/auth/users", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin-only: List users (minimal fields)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only admin can list users")

    users = db.query(User).order_by(User.id.asc()).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "username": u.username,
            "is_admin": bool(u.is_admin),
            "is_active": bool(u.is_active),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return result


@app.delete("/api/auth/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin-only: Delete a non-admin user and related data (trades, bot_config)."""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Only admin can delete users")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=400, detail="Cannot delete admin user")

    # Delete related entities first due to FK constraints (no cascade configured)
    # Delete trades
    trades_deleted = db.query(Trade).filter(Trade.user_id == user.id).delete()
    # Delete bot config
    bot_config_deleted = db.query(BotConfig).filter(BotConfig.user_id == user.id).delete()

    # Finally delete user
    db.delete(user)
    db.commit()

    return {
        "message": "User deleted",
        "user_id": user_id,
        "trades_deleted": trades_deleted,
        "bot_configs_deleted": bot_config_deleted,
    }


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user


# User Settings & API Keys
@app.post("/api/settings/api-keys")
async def update_api_keys(
    request: UpdateAPIKeysRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update Binance API keys"""
    user = db.query(User).filter(User.id == current_user["id"]).first()
    
    # Encrypt and store
    user.binance_api_key = encrypt_api_key(request.binance_api_key)
    user.binance_api_secret = encrypt_api_key(request.binance_api_secret)
    
    db.commit()
    
    return {"message": "API keys updated successfully"}


@app.get("/api/settings/validate-keys")
async def validate_api_keys(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Validate Binance TH API keys by calling account endpoint"""
    from app.binance_client import get_binance_th_client
    
    try:
        # Get user
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user or not user.binance_api_key or not user.binance_api_secret:
            return {
                "ok": False,
                "error": "API keys not configured",
                "hint": "Please configure your Binance TH API keys in Settings."
            }
        
        # Decrypt API keys
        api_key = decrypt_api_key(user.binance_api_key)
        api_secret = decrypt_api_key(user.binance_api_secret)
        
        # Create client and test connection
        client = get_binance_th_client(api_key, api_secret)
        account = client.get_account()
        can_trade = account.get('canTrade', True)
        
        return {
            "ok": True,
            "canTrade": can_trade,
            "msg": "API keys are valid for Binance TH",
        }
    except Exception as e:
        msg = str(e)
        hint = None
        if "-2008" in msg or "Invalid Api-Key" in msg:
            hint = "Invalid API key for Binance TH. Ensure you used Binance TH keys (not global) and enabled Read permission."
        elif "-1021" in msg or "Timestamp" in msg:
            hint = "Time sync error. Check your system clock."
        return {
            "ok": False,
            "error": msg,
            "hint": hint,
        }


@app.get("/api/settings/bot-config")
async def get_bot_config(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's bot configuration"""
    try:
        config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
        
        if not config:
            # Create default config
            config = BotConfig(user_id=current_user["id"])
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return config.to_dict()
    except Exception as e:
        print(f"❌ Error in get_bot_config: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get bot config: {str(e)}")


@app.put("/api/settings/bot-config")
async def update_bot_config(
    request: UpdateBotConfigRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update bot configuration (unified settings)"""
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
    
    if not config:
        config = BotConfig(user_id=current_user["id"])
        db.add(config)
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    
    # 🔍 DEBUG: Log Tennis/Gods Mode updates
    if 'tennis_mode_enabled' in update_data or 'gods_mode_enabled' in update_data:
        print(f"🔍 Config Update for user {current_user['id']}:")
        if 'gods_mode_enabled' in update_data:
            print(f"   Gods Mode: {update_data['gods_mode_enabled']}")
        if 'tennis_mode_enabled' in update_data:
            print(f"   Tennis Mode: {update_data['tennis_mode_enabled']}")
    
    for field, value in update_data.items():
        # Don't update password if it's the masked value
        if field == 'gmail_app_password' and value == '***':
            continue
        setattr(config, field, value)
    
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)

    # Log user action: config updated
    try:
        import json
        log = Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.USER,
            level=LogLevel.INFO,
            message="User updated bot configuration",
            details=json.dumps(update_data),
            user_id=current_user["id"],
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
    return config.to_dict()


# Trading Pairs
@app.get("/api/trading-pairs")
async def get_trading_pairs():
    """Get supported trading pairs"""
    return {
        "pairs": [
            {"symbol": "ETH/USDT", "name": "Ethereum"},
            {"symbol": "BTC/USDT", "name": "Bitcoin"},
            {"symbol": "BNB/USDT", "name": "Binance Coin"},
            {"symbol": "SOL/USDT", "name": "Solana"},
            {"symbol": "XRP/USDT", "name": "Ripple"},
            {"symbol": "USDC/USDT", "name": "USD Coin"},
            {"symbol": "ADA/USDT", "name": "Cardano"},
            {"symbol": "DOGE/USDT", "name": "Dogecoin"},
            {"symbol": "DOT/USDT", "name": "Polkadot"},
        ],
        "fiat_currencies": ["USD", "THB"]
    }


# Market Data (delegated to market.py)
@app.get("/api/market/ticker/{symbol}")
async def get_ticker(symbol: str):
    """Get current ticker price"""
    from app.market import get_current_price, convert_to_fiat
    
    try:
        price_data = await get_current_price(symbol)
        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/ticker/{base}/{quote}")
async def get_ticker_separated(base: str, quote: str):
    """Get current ticker price (separated format)"""
    symbol = f"{base}/{quote}"
    from app.market import get_current_price
    
    try:
        price_data = await get_current_price(symbol)
        return price_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/candles/{symbol}")
async def get_candles(symbol: str, timeframe: str = "1h", limit: int = 100):
    """Get candlestick data"""
    from app.market import get_candlestick_data
    
    try:
        candles = await get_candlestick_data(symbol, timeframe, limit)
        return {"symbol": symbol, "timeframe": timeframe, "candles": candles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/candles/{base}/{quote}")
async def get_candles_separated(base: str, quote: str, timeframe: str = "1h", limit: int = 100):
    """Get candlestick data (separated format)"""
    symbol = f"{base}/{quote}"
    from app.market import get_candlestick_data
    
    try:
        candles = await get_candlestick_data(symbol, timeframe, limit)
        return {"symbol": symbol, "timeframe": timeframe, "candles": candles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/orderbook/{symbol}")
async def get_orderbook(symbol: str, limit: int = 20):
    """Get orderbook depth"""
    from app.market import get_order_book
    
    try:
        orderbook = await get_order_book(symbol, limit)
        return orderbook
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/forecast/{symbol}")
async def get_price_forecast(
    symbol: str,
    forecast_hours: int = 6,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered price forecast for next N hours.
    Uses technical analysis, trend detection, and statistical models.
    """
    from app.market import get_candlestick_data
    from app.price_forecaster import forecast_price_hourly, get_forecast_summary
    
    try:
        # Get hourly candles (need at least 24 hours, get 100 for better analysis)
        candles = await get_candlestick_data(symbol, timeframe='1h', limit=100)
        
        if not candles:
            raise HTTPException(status_code=404, detail="No candle data available")
        
        # Generate forecast
        forecast = await forecast_price_hourly(candles, forecast_hours=forecast_hours)

        # Add summary text
        forecast['summary'] = get_forecast_summary(forecast)

        # Persist snapshot for historical comparison
        try:
            from app.models import ForecastSnapshot
            import json
            from datetime import timedelta
            snapshot = ForecastSnapshot(
                symbol=symbol,
                horizon_hours=forecast_hours,
                current_price=forecast.get('current_price', candles[-1]['close'] if candles else 0.0),
                summary=forecast.get('summary'),
                data_json=json.dumps({
                    'forecasts': forecast.get('forecasts') or forecast.get('forecast') or forecast.get('predictions') or [],
                    'risk_metrics': forecast.get('risk_metrics'),
                    'price_targets': forecast.get('price_targets'),
                })
            )
            db.add(snapshot)
            db.commit()

            # Retention pruning: delete snapshots older than 30 days
            try:
                cutoff = datetime.utcnow() - timedelta(days=30)
                db.query(ForecastSnapshot).filter(ForecastSnapshot.generated_at < cutoff).delete()
                db.commit()
            except Exception as prune_err:
                print(f"[WARN] Failed to prune old snapshots: {prune_err}")
        except Exception as persist_err:
            # Log but don't fail the main request
            print(f"[WARN] Failed to persist forecast snapshot: {persist_err}")

        return forecast
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/forecast/{base}/{quote}")
async def get_price_forecast_pair(
    base: str,
    quote: str,
    forecast_hours: int = 6,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get price forecast for a trading pair (e.g., BTC/USDT)"""
    symbol = f"{base}/{quote}"
    return await get_price_forecast(symbol, forecast_hours, current_user, db)


@app.get("/api/market/forecast/history/{symbol}")
async def get_forecast_history(
    symbol: str,
    limit: int = 5,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Return recent persisted forecast snapshots for a symbol (limited)."""
    from app.models import ForecastSnapshot
    import json
    from app.market import get_candlestick_data
    import math
    try:
        q = db.query(ForecastSnapshot).filter(ForecastSnapshot.symbol == symbol).order_by(ForecastSnapshot.generated_at.desc()).limit(limit)
        rows = q.all()
        history = []
        for r in rows:
            data = {}
            try:
                data = json.loads(r.data_json)
            except Exception:
                pass
            item = {
                'id': r.id,
                'symbol': r.symbol,
                'generated_at': r.generated_at.isoformat() if r.generated_at else None,
                'horizon_hours': r.horizon_hours,
                'current_price': r.current_price,
                'summary': r.summary,
                'forecasts': data.get('forecasts', []),
                'price_targets': data.get('price_targets'),
                'risk_metrics': data.get('risk_metrics'),
            }

            # Compute evaluation metrics (MAE/MAPE) if horizon elapsed and data available
            try:
                forecasts = item['forecasts']
                if forecasts and r.generated_at and r.horizon_hours:
                    end_time = r.generated_at.timestamp() + r.horizon_hours * 3600
                    now_ts = datetime.utcnow().timestamp()
                    # Only evaluate if horizon fully elapsed and snapshot not too old (> 200h ago)
                    if now_ts >= end_time:
                        # Fetch last 200 hourly candles
                        candles = await get_candlestick_data(symbol, timeframe='1h', limit=200)
                        # Build map by hour timestamp (sec)
                        candle_map = { int(c['timestamp'] / 1000): c for c in candles }
                        abs_errors = []
                        pct_errors = []
                        for f in forecasts:
                            hour = f.get('hour')
                            pred = f.get('predicted_price') or f.get('value') or f.get('price')
                            if hour is None or pred is None:
                                continue
                            ts = int(r.generated_at.timestamp()) + int(hour) * 3600
                            # Find nearest candle within ±30min
                            candidates = [ts, ts-3600, ts+3600]
                            actual = None
                            for cand_ts in candidates:
                                c = candle_map.get(cand_ts)
                                if c:
                                    actual = c.get('close')
                                    break
                            if actual and actual > 0:
                                abs_errors.append(abs(pred - actual))
                                pct_errors.append(abs(pred - actual) / actual)
                        if abs_errors:
                            mae = sum(abs_errors) / len(abs_errors)
                            mape = sum(pct_errors) / len(pct_errors)
                            item['metrics'] = {
                                'mae': mae,
                                'mape': mape,
                                'n': len(abs_errors),
                                'evaluated': True,
                            }
                        else:
                            item['metrics'] = { 'evaluated': False }
                    else:
                        item['metrics'] = { 'evaluated': False }
                else:
                    item['metrics'] = { 'evaluated': False }
            except Exception as eval_err:
                print(f"[WARN] Forecast evaluation failed: {eval_err}")
                item['metrics'] = { 'evaluated': False }

            history.append(item)
        return {'symbol': symbol, 'count': len(history), 'history': history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market/forecast/history/{base}/{quote}")
async def get_forecast_history_pair(
    base: str,
    quote: str,
    limit: int = 5,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Pair form (BTC/USDT) convenience wrapper for history endpoint; avoids needing URL encoding of '/'."""
    symbol = f"{base}/{quote}"
    return await get_forecast_history(symbol, limit, current_user, db)


# Account Balance
@app.get("/api/account/balance")
async def get_balance(
    fiat_currency: str = "USD",
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account balance and P/L"""
    from app.market import get_account_balance
    
    try:
        balance = await get_account_balance(db, current_user['id'], fiat_currency)
        return balance
    except Exception as e:
        print(f"❌ Error in get_balance: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Temporary debug endpoint to inspect balance calculation internals
@app.get("/api/debug/balance")
async def debug_balance(
    fiat_currency: str = "USD",
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Debug version of balance API with detailed internal info"""
    from app.market import get_current_price
    from app.models import BotConfig
    from app.paper_trading_tracker import calculate_paper_performance

    debug_info = {"steps": []}

    try:
        user_id = current_user['id']
        debug_info["user_id"] = user_id
        debug_info["steps"].append("Got user ID")

        # Get config
        config = db.query(BotConfig).filter(BotConfig.user_id == user_id).first()
        if not config:
            debug_info["error"] = "No bot config found"
            return debug_info

        debug_info["config"] = {
            "budget": config.budget,
            "symbol": config.symbol,
            "paper_trading": bool(config.paper_trading)
        }
        debug_info["steps"].append("Got bot config")

        if config and config.paper_trading:
            budget = config.budget
            symbol = config.symbol

            # Parse symbol
            try:
                base_currency, quote_currency = symbol.split('/')
                debug_info["currencies"] = {"base": base_currency, "quote": quote_currency}
                debug_info["steps"].append("Parsed symbol")
            except Exception as e:
                base_currency, quote_currency = "BTC", "USDT"
                debug_info["currencies"] = {"base": base_currency, "quote": quote_currency}
                debug_info["steps"].append(f"Symbol parse failed, using defaults: {str(e)}")

            # Get current price
            try:
                ticker = await get_current_price(symbol)
                current_price = ticker.get('last', 0)
                debug_info["price_fetch"] = {"ticker": ticker, "current_price": current_price}

                if current_price == 0:
                    current_price = 42000.0
                    debug_info["steps"].append("Used fallback price (ticker returned 0)")
                else:
                    debug_info["steps"].append("Got valid price from ticker")
            except Exception as e:
                current_price = 42000.0
                debug_info["price_fetch"] = {"error": str(e), "current_price": current_price}
                debug_info["steps"].append(f"Price fetch failed, using fallback: {str(e)}")

            debug_info["final_current_price"] = current_price

            # Calculate performance
            try:
                perf = calculate_paper_performance(user_id, symbol, 'gods_hand', db)
                debug_info["performance"] = perf
                debug_info["steps"].append("Got performance calculation")
            except Exception as e:
                debug_info["performance"] = {"error": str(e)}
                debug_info["steps"].append(f"Performance calculation failed: {str(e)}")
                perf = None

            # Balance calculation logic
            if perf:
                debug_info["steps"].append("Performance data available")

                total_trades = perf.get('total_trades', 0)
                debug_info["total_trades"] = total_trades

                if total_trades > 0:
                    debug_info["steps"].append("Has trading history - using actual position")
                    quantity_held = perf.get('quantity_held', 0)
                    cash_balance = perf.get('cash_balance', budget / 2)
                    position_value = quantity_held * current_price if quantity_held > 0 else 0
                else:
                    debug_info["steps"].append("No trades - using 50/50 split from performance")
                    cash_balance = perf.get('cash_balance', budget / 2)
                    position_value = perf.get('position_value', budget / 2)
                    quantity_held = position_value / current_price if current_price > 0 else 0

            else:
                debug_info["steps"].append("No performance data - using fallback calculation")
                quantity_held = (budget / 2) / current_price
                cash_balance = budget / 2
                position_value = budget / 2

            debug_info["final_calculation"] = {
                "quantity_held": quantity_held,
                "cash_balance": cash_balance,
                "position_value": position_value,
                "total_balance": cash_balance + position_value
            }

            # Build assets
            assets = [
                {
                    "asset": quote_currency,
                    "free": cash_balance,
                    "locked": 0.0,
                    "total": cash_balance,
                    "usd_value": cash_balance,
                },
                {
                    "asset": base_currency,
                    "free": quantity_held,
                    "locked": 0.0,
                    "total": quantity_held,
                    "usd_value": position_value,
                }
            ]

            debug_info["assets"] = assets
            debug_info["steps"].append("Built assets array")

            return debug_info
        else:
            debug_info["error"] = "Not in paper trading mode or no config"
            return debug_info

    except Exception as e:
        debug_info["error"] = str(e)
        import traceback
        debug_info["traceback"] = traceback.format_exc()
        return debug_info



@app.get("/api/debug/dbinfo")
def debug_dbinfo(current_user: dict = Depends(get_current_active_user)):
    """Return DB connection info and simple table counts for debugging."""
    import os
    from app.db import DATABASE_URL, engine
    info = {
        "DATABASE_URL": str(DATABASE_URL),
        "cwd": os.getcwd(),
        "exists": None,
        "filesize": None,
        "tables": {}
    }

    try:
        # If using SQLite, check if file exists
        if str(DATABASE_URL).startswith('sqlite'):
            # Extract file path after sqlite:/// prefix
            path = str(DATABASE_URL).replace('sqlite:///', '')
            info['exists'] = os.path.exists(path)
            try:
                info['filesize'] = os.path.getsize(path) if info['exists'] else None
            except Exception:
                info['filesize'] = None

        # Get simple row counts for common tables
        with engine.connect() as conn:
            for t in ['bot_configs', 'trades', 'paper_trading_snapshots']:
                try:
                    res = conn.execute(f"SELECT COUNT(*) as c FROM {t}")
                    row = res.fetchone()
                    info['tables'][t] = int(row[0]) if row is not None else None
                except Exception as e:
                    info['tables'][t] = f"error: {str(e)}"

    except Exception as e:
        info['error'] = str(e)

    return info


# AI Recommendations
@app.get("/api/ai/recommendation/{symbol}")
async def get_ai_recommendation(
    symbol: str,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI trading recommendation"""
    from app.ai_engine import get_trading_recommendation
    
    try:
        config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
        recommendation = await get_trading_recommendation(symbol, config)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/recommendation/{base}/{quote}")
async def get_ai_recommendation_separated(
    base: str,
    quote: str,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI trading recommendation (separated symbol format)"""
    from app.ai_engine import get_trading_recommendation
    
    try:
        symbol = f"{base}/{quote}"
        config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
        recommendation = await get_trading_recommendation(symbol, config)
        return recommendation
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/analysis/{symbol}")
async def get_advanced_analysis(
    symbol: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get advanced AI market analysis"""
    from app.ai_engine import get_advanced_analysis
    
    try:
        analysis = await get_advanced_analysis(symbol)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai/analysis/{base}/{quote}")
async def get_advanced_analysis_separated(
    base: str,
    quote: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get advanced AI market analysis (separated symbol format)"""
    from app.ai_engine import get_advanced_analysis
    
    symbol = f"{base}/{quote}"
    try:
        analysis = await get_advanced_analysis(symbol)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Trading
@app.post("/api/trade/execute")
async def execute_trade(
    request: TradeRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Execute a trade (manual or bot)"""
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
    
    # Create trade record
    trade = Trade(
        user_id=current_user["id"],
        symbol=request.symbol,
        side=request.side,
        amount=request.amount,
        price=request.price,
        bot_type="manual",
        status="pending",
        timestamp=datetime.utcnow()
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    
    if config and config.paper_trading:
        # Paper trading
        trade.status = "completed_paper"
        trade.filled_price = request.price
        db.commit()
        return {"message": "Paper trade executed", "trade_id": trade.id, "status": "paper"}
    else:
        # Real trading (implement with ccxt)
        from app.market import execute_market_trade
        try:
            result = await execute_market_trade(
                current_user["id"], 
                request.symbol, 
                request.side, 
                request.amount,
                db
            )
            trade.status = "completed"
            trade.filled_price = result.get("price")
            db.commit()
            return {"message": "Trade executed", "trade_id": trade.id, "result": result}
        except Exception as e:
            trade.status = "failed"
            db.commit()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trade/history")
async def get_trade_history(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get user's trade history"""
    trades = db.query(Trade).filter(
        Trade.user_id == current_user["id"]
    ).order_by(Trade.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "side": t.side,
            "amount": t.amount,
            "price": t.price,
            "filled_price": t.filled_price,
            "status": t.status,
            "bot_type": t.bot_type,
            "timestamp": t.timestamp.isoformat() + 'Z' if t.timestamp and not t.timestamp.isoformat().endswith('Z') else t.timestamp.isoformat() if t.timestamp else None
        }
        for t in trades
    ]


# Bot Controls
@app.post("/api/bot/grid/start")
async def start_grid_bot(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start Grid Bot"""
    from app.bots import start_grid_bot as run_grid
    
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
    if not config or not config.grid_enabled:
        raise HTTPException(status_code=400, detail="Grid bot not configured")
    
    result = await run_grid(current_user["id"], config, db)
    return result


@app.post("/api/bot/dca/start")
async def start_dca_bot(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start DCA Bot"""
    from app.bots import start_dca_bot as run_dca
    
    config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
    if not config or not config.dca_enabled:
        raise HTTPException(status_code=400, detail="DCA bot not configured")
    
    result = await run_dca(current_user["id"], config, db)
    return result


@app.post("/api/bot/gods-hand/start")
async def start_gods_hand(
    request: Request,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    continuous: bool = True,
    interval_seconds: int = 60,
):
    """Start Gods Hand autonomous trading (continuous by default).
    Returns result of first run and continues in background if continuous=True.
    """
    from app.bots import start_gods_hand_entry
    import logging
    
    logger = logging.getLogger(__name__)
    origin = request.headers.get("origin")
    logger.info(f"Starting Gods Hand - origin={origin} continuous={continuous}, interval={interval_seconds}")

    # Validate interval bounds
    if interval_seconds < 10:
        interval_seconds = 10
    if interval_seconds > 3600:
        interval_seconds = 3600

    # Log user action: start request
    try:
        db.add(Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.USER,
            level=LogLevel.INFO,
            message=f"User started Gods Hand (continuous={continuous}, interval={interval_seconds}s)",
            user_id=current_user["id"],
        ))
        db.commit()
    except Exception:
        pass

    result = await start_gods_hand_entry(current_user["id"], db, continuous=continuous, interval_seconds=interval_seconds)
    logger.info(f"Gods Hand start result: {result}")
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Failed to start Gods Hand"))
    return result


@app.post("/api/bot/{bot_type}/stop")
async def stop_bot(
    bot_type: str,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Stop a running bot"""
    from app.bots import stop_bot as stop_running_bot
    
    # Log user action: stop request
    try:
        db.add(Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.USER,
            level=LogLevel.INFO,
            message=f"User stopped bot {bot_type}",
            user_id=current_user["id"],
        ))
        db.commit()
    except Exception:
        pass

    result = await stop_running_bot(bot_type, current_user["id"], db)
    return result


@app.get("/api/bot/status")
async def get_bot_status(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get status of all bots"""
    from app.bots import get_bot_status as check_status
    
    try:
        status = await check_status(current_user["id"], db)
        return status
    except Exception as e:
        print(f"❌ Error in get_bot_status: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get bot status: {str(e)}")


@app.post("/api/bot/gods-hand/reset-kill-switch")
async def reset_kill_switch_baseline(
    restart: bool = True,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Reset the kill-switch baseline to the current unrealized P/L percent.
    Optionally restarts Gods Hand.
    """
    from app.position_tracker import get_current_position, calculate_position_pl
    from app.market import get_current_price
    from app.bots import set_kill_switch_baseline, start_gods_hand_entry

    user_id = current_user["id"]
    config = db.query(BotConfig).filter(BotConfig.user_id == user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="No configuration found")

    # Compute current unrealized P/L
    current_pos = get_current_position(user_id, config.symbol, db)
    ticker = await get_current_price(config.symbol)
    current_price = ticker.get('last', 0.0)
    pl_data = calculate_position_pl(current_pos, current_price)
    pl_percent = pl_data['pl_percent']

    # Set baseline and log
    result = set_kill_switch_baseline(user_id, pl_percent, config.symbol, db, current_price=current_price)

    # Log user action
    try:
        db.add(Log(
            timestamp=datetime.utcnow(),
            category=LogCategory.USER,
            level=LogLevel.INFO,
            message=f"User reset kill-switch baseline (pl={pl_percent:.2f}%)",
            user_id=user_id,
        ))
        db.commit()
    except Exception:
        pass

    # Optionally restart Gods Hand loop
    restarted = False
    if restart:
        await start_gods_hand_entry(user_id, db, continuous=True, interval_seconds=60)
        restarted = True

    return {"ok": True, "baseline": result, "restarted": restarted}


@app.get("/api/bot/gods-hand/debug")
async def gods_hand_debug(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Debug Gods Hand bot - check status, recent logs, and position"""
    from app.bots import bot_status, bot_tasks
    from app.logging_models import Log
    from app.position_tracker import get_current_position
    from datetime import datetime, timedelta
    
    user_id = current_user["id"]
    bot_key = f"gods_hand_{user_id}"
    
    # Get config
    config = db.query(BotConfig).filter(BotConfig.user_id == user_id).first()
    if not config:
        return {"error": "No config found"}
    
    # Get current position
    position = get_current_position(user_id, config.symbol, db)
    
    # Get recent AI logs (last 10)
    recent_logs = db.query(Log).filter(
        Log.user_id == user_id,
        Log.bot_type == 'gods_hand'
    ).order_by(Log.timestamp.desc()).limit(10).all()
    
    # Get recent trades (last 5)
    recent_trades = db.query(Trade).filter(
        Trade.user_id == user_id,
        Trade.bot_type == 'gods_hand'
    ).order_by(Trade.timestamp.desc()).limit(5).all()
    
    return {
        "bot_status": bot_status.get(bot_key, "not_found"),
        "task_exists": bot_key in bot_tasks,
        "task_done": bot_tasks[bot_key].done() if bot_key in bot_tasks else None,
        "config": {
            "symbol": config.symbol,
            "gods_hand_enabled": config.gods_hand_enabled,
            "min_confidence": config.min_confidence,
            "entry_step_percent": config.entry_step_percent,
            "exit_step_percent": config.exit_step_percent,
            "paper_trading": config.paper_trading,
            "max_daily_loss": config.max_daily_loss
        },
        "position": position,
        "recent_logs": [
            {
                "timestamp": log.timestamp.isoformat(),
                "category": log.category.value if log.category else None,
                "level": log.level.value if log.level else None,
                "message": log.message,
                "ai_recommendation": log.ai_recommendation,
                "ai_confidence": log.ai_confidence,
                "ai_executed": log.ai_executed
            } for log in recent_logs
        ],
        "recent_trades": [
            {
                "timestamp": trade.timestamp.isoformat(),
                "side": trade.side,
                "amount": trade.amount,
                "price": trade.price,
                "status": trade.status
            } for trade in recent_trades
        ]
    }


@app.get("/api/bot/gods-hand/preview")
async def gods_hand_preview(
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Preview what Gods Hand would do without executing - shows exact calculation"""
    from app.ai_engine import get_trading_recommendation, calculate_risk_assessment
    from app.position_tracker import get_current_position, calculate_incremental_amount
    
    user_id = current_user["id"]
    
    # Get config
    config = db.query(BotConfig).filter(BotConfig.user_id == user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="No config found")
    
    symbol = config.symbol
    
    # Get AI recommendation
    recommendation = await get_trading_recommendation(symbol, config)
    risk_assessment = await calculate_risk_assessment(symbol, config)
    
    action = recommendation.get('action', 'HOLD')
    confidence = recommendation.get('confidence', 0.0)
    
    # Get current position
    current_position = get_current_position(user_id, symbol, db)
    
    # Apply 50/50 split if paper initial
    if current_position.get('_paper_initial'):
        budget = current_position.get('_budget', config.budget)
        current_price = risk_assessment['current_price']
        current_position['quantity'] = (budget / 2) / current_price
        current_position['cost_basis'] = budget / 2
        current_position['average_price'] = current_price
        current_position['position_value_usd'] = budget / 2
        current_position['trades_count'] = 0
        del current_position['_paper_initial']
        del current_position['_budget']
    
    # Calculate incremental step
    max_position_size = risk_assessment['recommended_position_size']
    confidence_multiplier = 0.5 + (confidence * 1.0) if confidence > 0 else 1.0
    base_step_percent = config.entry_step_percent if action == 'BUY' else config.exit_step_percent
    step_percent = min(base_step_percent * confidence_multiplier, 100.0)
    
    incremental_calc = calculate_incremental_amount(
        current_position,
        max_position_size,
        step_percent,
        action
    )
    
    # Determine if would execute
    would_execute = False
    block_reason = None
    
    if confidence < config.min_confidence:
        block_reason = f"Confidence {confidence:.2f} < minimum {config.min_confidence}"
    elif not incremental_calc['can_execute']:
        block_reason = incremental_calc['reason']
    elif action == 'HOLD':
        block_reason = "AI recommends HOLD"
    else:
        would_execute = True
    
    return {
        "symbol": symbol,
        "would_execute": would_execute,
        "action": action,
        "confidence": confidence,
        "block_reason": block_reason,
        "recommendation": recommendation,
        "risk_assessment": risk_assessment,
        "current_position": {
            "quantity": current_position['quantity'],
            "cost_basis": current_position['cost_basis'],
            "position_value_usd": current_position['position_value_usd'],
            "trades_count": current_position['trades_count']
        },
        "incremental_calculation": incremental_calc,
        "step_settings": {
            "base_step_percent": base_step_percent,
            "confidence_multiplier": confidence_multiplier,
            "effective_step_percent": step_percent
        }
    }


# ----------------------------------------------------------------------------
# Gods Hand Performance
# ----------------------------------------------------------------------------
@app.get("/api/bot/gods-hand/performance")
async def gods_hand_performance(
    days: int = 7,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compute performance metrics for Gods Hand trades over the last N days."""
    from datetime import datetime, timedelta

    if days < 1:
        days = 1
    if days > 365:
        days = 365

    since = datetime.utcnow() - timedelta(days=days)

    trades = (
        db.query(Trade)
        .filter(Trade.user_id == current_user["id"]) 
        .filter(Trade.bot_type == 'gods_hand')
        .filter(Trade.timestamp >= since)
        .order_by(Trade.timestamp.asc())
        .all()
    )

    # Aggregate by symbol using FIFO average cost method
    per_symbol = {}
    realized_profit = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    total_buys = 0
    total_sells = 0
    winning_trades = 0
    losing_trades = 0

    for t in trades:
        sym = t.symbol
        if sym not in per_symbol:
            per_symbol[sym] = {
                'position': 0.0,
                'total_cost': 0.0,
                'avg_cost': 0.0,
            }
        s = per_symbol[sym]

        price = float(t.filled_price or t.price or 0)
        amount = float(t.amount or 0)
        if amount <= 0 or price <= 0:
            continue

        if t.side == 'BUY':
            total_buys += 1
            # Increase position and cost
            s['total_cost'] += amount * price
            s['position'] += amount
            s['avg_cost'] = s['total_cost'] / s['position'] if s['position'] > 0 else 0.0
        elif t.side == 'SELL':
            total_sells += 1
            # Realize PnL based on average cost
            sell_amount = min(amount, s['position']) if s['position'] > 0 else 0.0
            if sell_amount > 0:
                pnl = (price - s['avg_cost']) * sell_amount
                realized_profit += pnl
                if pnl >= 0:
                    gross_profit += pnl
                    winning_trades += 1
                else:
                    gross_loss += abs(pnl)
                    losing_trades += 1
                # Reduce position and cost
                s['position'] -= sell_amount
                s['total_cost'] -= s['avg_cost'] * sell_amount
                s['avg_cost'] = s['total_cost'] / s['position'] if s['position'] > 0 else 0.0

    total_trades = total_buys + total_sells
    net_profit = realized_profit
    win_rate = (winning_trades / max(1, total_sells)) * 100.0
    avg_win = (gross_profit / max(1, winning_trades)) if winning_trades > 0 else 0.0
    avg_loss = (gross_loss / max(1, losing_trades)) if losing_trades > 0 else 0.0

    # Current positions per symbol
    positions = [
        {
            'symbol': sym,
            'position': round(s['position'], 8),
            'avg_cost': round(s['avg_cost'], 6)
        }
        for sym, s in per_symbol.items() if s['position'] > 0
    ]

    # Last trades (5 most recent)
    last_trades = [
        {
            'timestamp': t.timestamp.isoformat() + 'Z' if t.timestamp and not t.timestamp.isoformat().endswith('Z') else t.timestamp.isoformat() if t.timestamp else None,
            'symbol': t.symbol,
            'side': t.side,
            'amount': t.amount,
            'price': t.filled_price or t.price,
            'status': t.status,
        }
        for t in (
            db.query(Trade)
            .filter(Trade.user_id == current_user['id'])
            .filter(Trade.bot_type == 'gods_hand')
            .order_by(Trade.timestamp.desc())
            .limit(5)
            .all()
        )
    ]

    return {
        'since': since.isoformat(),
        'days': days,
        'summary': {
            'total_trades': total_trades,
            'buys': total_buys,
            'sells': total_sells,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'gross_profit': round(gross_profit, 4),
            'gross_loss': round(gross_loss, 4),
            'net_profit': round(net_profit, 4),
            'avg_win': round(avg_win, 4),
            'avg_loss': round(avg_loss, 4),
        },
        'positions': positions,
        'last_trades': last_trades,
    }


# Reset Paper Trading
# ----------------------------------------------------------------------------
@app.post("/api/bot/paper-trading/reset")
async def reset_paper_trading(
    symbol: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reset paper trading data for the current user.
    Clears all paper trades and snapshots.
    
    Args:
        symbol: Optional. If provided, only reset for this symbol.
    """
    from app.paper_trading_tracker import PaperTradingSnapshot
    
    try:
        # Count before deletion
        trades_query = db.query(Trade).filter(
            Trade.user_id == current_user["id"],
            Trade.status.in_(['completed_paper', 'simulated'])
        )
        snapshots_query = db.query(PaperTradingSnapshot).filter(
            PaperTradingSnapshot.user_id == current_user["id"]
        )
        
        # Filter by symbol if provided
        if symbol:
            trades_query = trades_query.filter(Trade.symbol == symbol)
            snapshots_query = snapshots_query.filter(PaperTradingSnapshot.symbol == symbol)
        
        trade_count = trades_query.count()
        snapshot_count = snapshots_query.count()
        
        # Delete trades
        trades_query.delete(synchronize_session=False)
        
        # Delete snapshots
        snapshots_query.delete(synchronize_session=False)
        
        db.commit()
        
        message = f"Reset complete for {symbol}" if symbol else "Reset complete for all symbols"
        
        return {
            "success": True,
            "message": message,
            "deleted_trades": trade_count,
            "deleted_snapshots": snapshot_count,
            "symbol": symbol
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LOGGING ENDPOINTS
# ============================================================================

@app.get("/api/logs")
async def get_logs(
    category: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get application logs with filtering. Non-admins only see their own logs."""
    query = db.query(Log)
    
    # Filter by user_id for non-admins
    if not current_user.get("is_admin"):
        query = query.filter(Log.user_id == current_user["id"])
    
    # Filter by category
    if category:
        try:
            query = query.filter(Log.category == LogCategory(category))
        except ValueError:
            pass
    
    # Filter by level
    if level:
        try:
            query = query.filter(Log.level == LogLevel(level))
        except ValueError:
            pass
    
    # Order by most recent first
    query = query.order_by(Log.timestamp.desc())
    
    # Apply pagination
    total = query.count()
    logs = query.offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "logs": [log.to_dict() for log in logs]
    }


@app.get("/api/logs/categories")
async def get_log_categories(
    current_user: dict = Depends(get_current_active_user)
):
    """Get available log categories with counts"""
    return {
        "categories": [
            {"value": cat.value, "label": cat.value.replace("_", " ").title()}
            for cat in LogCategory
        ]
    }


@app.get("/api/logs/ai-actions")
async def get_ai_action_comparison(
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI thinking vs actual actions comparison. Non-admins only see their own logs."""
    # Base queries
    thinking_query = db.query(Log).filter(Log.category == LogCategory.AI_THINKING)
    action_query = db.query(Log).filter(Log.category == LogCategory.AI_ACTION)
    
    # Filter by user_id for non-admins
    if not current_user.get("is_admin"):
        thinking_query = thinking_query.filter(Log.user_id == current_user["id"])
        action_query = action_query.filter(Log.user_id == current_user["id"])
    
    # Execute queries
    thinking_logs = thinking_query.order_by(Log.timestamp.desc()).limit(limit).all()
    action_logs = action_query.order_by(Log.timestamp.desc()).limit(limit).all()
    
    # Create comparison
    comparison = []
    for thinking in thinking_logs:
        # Find corresponding action within 1 minute
        matching_action = next(
            (a for a in action_logs 
             if a.symbol == thinking.symbol 
             and abs((a.timestamp - thinking.timestamp).total_seconds()) < 60),
            None
        )
        
        comparison.append({
            "timestamp": thinking.timestamp.isoformat() + 'Z' if thinking.timestamp and not thinking.timestamp.isoformat().endswith('Z') else thinking.timestamp.isoformat() if thinking.timestamp else None,
            "symbol": thinking.symbol,
            "ai_recommendation": thinking.ai_recommendation,
            "ai_confidence": thinking.ai_confidence,
            "thinking_message": thinking.message,
            "thinking_level": thinking.level.value if thinking.level else None,
            "action_taken": matching_action.ai_executed if matching_action else "unknown",
            "action_reason": matching_action.execution_reason if matching_action else None,
            "action_message": matching_action.message if matching_action else None,
            "action_level": matching_action.level.value if matching_action and matching_action.level else None,
        })
    
    return {
        "total": len(comparison),
        "comparisons": comparison
    }


@app.delete("/api/logs/clear")
async def clear_logs(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clear logs. Admins clear all, users clear their own."""
    query = db.query(Log)
    
    # Filter by user_id for non-admins
    if not current_user.get("is_admin"):
        query = query.filter(Log.user_id == current_user["id"])
    
    if category:
        try:
            query = query.filter(Log.category == LogCategory(category))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid category")
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    
    return {
        "message": f"Deleted {deleted_count} log entries",
        "category": category if category else "all"
    }


# Paper Trading Performance
@app.get("/api/paper-trading/performance")
async def get_paper_performance(
    symbol: Optional[str] = None,
    bot_type: str = "gods_hand",
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current paper trading performance"""
    from app.paper_trading_tracker import calculate_paper_performance
    
    # Get symbol from config if not provided
    if not symbol:
        config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
        symbol = config.symbol if config else "BTC/USDT"
    
    perf = calculate_paper_performance(current_user["id"], symbol, bot_type, db)
    return perf if perf else {"error": "No data available"}


@app.get("/api/paper-trading/history")
async def get_paper_history(
    symbol: Optional[str] = None,
    bot_type: str = "gods_hand",
    days: int = 7,
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get paper trading performance history (default 7 days)"""
    from app.paper_trading_tracker import get_paper_performance_history
    
    # Get symbol from config if not provided
    if not symbol:
        config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
        symbol = config.symbol if config else "BTC/USDT"
    
    history = get_paper_performance_history(current_user["id"], symbol, bot_type, days, db)
    return {"history": history, "symbol": symbol, "bot_type": bot_type, "days": days}


@app.post("/api/paper-trading/snapshot")
async def create_paper_snapshot(
    symbol: Optional[str] = None,
    bot_type: str = "gods_hand",
    current_user: dict = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually create a paper trading performance snapshot"""
    from app.paper_trading_tracker import save_paper_snapshot
    
    # Get symbol from config if not provided
    if not symbol:
        config = db.query(BotConfig).filter(BotConfig.user_id == current_user["id"]).first()
        symbol = config.symbol if config else "BTC/USDT"
    
    snapshot = save_paper_snapshot(current_user["id"], symbol, bot_type, db)
    return {"status": "success", "snapshot": snapshot}


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws/logs/{token}")
async def websocket_logs(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time log push.
    Client connects with auth token in URL path.
    """
    from app.websocket_manager import ws_manager
    from app.auth import verify_token
    
    user_id = None
    
    try:
        # Authenticate token
        try:
            payload = verify_token(token, "access")
            user_id = payload.get("user_id")
            if not user_id:
                await websocket.close(code=1008, reason="Invalid token")
                return
        except Exception as e:
            print(f"WebSocket authentication failed: {e}")
            await websocket.close(code=1008, reason="Authentication failed")
            return
        
        # Register connection
        await ws_manager.connect(websocket, user_id)
        print(f"✅ WebSocket authenticated and connected for user {user_id}")
        
        # Keep connection alive and handle ping/pong
        while True:
            try:
                # Wait for message with timeout to detect dead connections
                import asyncio
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # Handle ping/pong to keep connection alive
                if data == "ping":
                    await websocket.send_text("pong")
                    # print(f"🏓 Pong sent to user {user_id}")
                elif data == "pong":
                    # Client responding to our ping
                    pass
                else:
                    print(f"📨 Received unknown message from user {user_id}: {data}")
                    
            except WebSocketDisconnect:
                print(f"🔌 WebSocket client {user_id} disconnected normally")
                break
            except asyncio.TimeoutError:
                # No message received in 60 seconds, check if connection is still alive
                try:
                    await websocket.send_text("ping")
                except:
                    print(f"⚠️ WebSocket {user_id} appears dead, closing...")
                    break
            except Exception as msg_error:
                print(f"❌ WebSocket message error for user {user_id}: {msg_error}")
                break
                
    except Exception as e:
        print(f"❌ WebSocket connection error for user {user_id or 'unknown'}: {e}")
    finally:
        if user_id:
            await ws_manager.disconnect(websocket, user_id)
            print(f"🔌 WebSocket cleanup completed for user {user_id}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
