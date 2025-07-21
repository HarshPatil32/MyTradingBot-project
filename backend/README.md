# MACD Trading Backend API

This is the backend API for the MACD Trading Strategy application, built with Flask.

## Deployment on Render

This backend is designed to be deployed on Render.com.

### Render Configuration:
- **Build Command**: `./build.sh`
- **Start Command**: `python app.py`
- **Environment**: Python 3.9+

## API Endpoints

- `GET /` - Health check
- `POST /webhookcallback` - Webhook callback  
- `GET /MACD-strategy` - MACD trading strategy backtest with optimization
- `GET /spy-investment` - SPY investment comparison

### MACD Strategy Parameters:
- `stocks` - Comma-separated stock symbols (e.g., "AAPL,MSFT")
- `start_date` - Start date in YYYY-MM-DD format
- `end_date` - End date in YYYY-MM-DD format  
- `initial_balance` - Initial investment amount (default: 100000)
- `optimize` - Whether to optimize parameters (default: true)

### SPY Investment Parameters:
- `start_date` - Start date in YYYY-MM-DD format
- `end_date` - End date in YYYY-MM-DD format
- `initial_balance` - Initial investment amount (default: 100000)

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

The server will start on `http://localhost:5001`

## Environment Variables

No environment variables required for basic functionality.
