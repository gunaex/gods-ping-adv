"""
Test Price Forecaster
"""
import asyncio
from app.market import get_candles
from app.price_forecaster import forecast_price_hourly, get_forecast_summary


async def test_forecast():
    """Test the price forecaster with real BTC/USDT data"""
    
    print("📊 Testing Price Forecaster...")
    print("=" * 60)
    
    # Get hourly candles
    symbol = "BTC/USDT"
    print(f"\n1. Fetching {symbol} hourly candles...")
    candles_data = await get_candles(symbol, timeframe='1h', limit=100)
    candles = candles_data.get('candles', [])
    print(f"   ✅ Got {len(candles)} candles")
    
    # Generate forecast
    print(f"\n2. Generating 6-hour forecast...")
    forecast = forecast_price_hourly(candles, forecast_hours=6)
    
    # Display results
    print(f"\n{get_forecast_summary(forecast)}")
    
    # Show detailed hourly predictions
    print("\n📈 Detailed Hourly Predictions:")
    print("-" * 60)
    for f in forecast['forecasts']:
        print(f"   Hour +{f['hour']}: ${f['predicted_price']:,.2f} (confidence: {f['confidence']*100:.0f}%)")
    
    print("\n✅ Forecast test completed!")


if __name__ == "__main__":
    asyncio.run(test_forecast())
