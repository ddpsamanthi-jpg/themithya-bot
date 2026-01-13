from binance.client import Client
import json

# Test the API keys
api_key = 'hEI0SE4toFiEgAVYmtaGK7uRC56yPZQGymEjN9jvxDiuFmG7cegyN9xWFsbTTXeK'
api_secret = 'pjp2rShx7XeHIDEp1NYLRlI8vdp55Go0jQCVxwlFKeQIENvksxmiyvlVq0oZNQwr'

client = Client(api_key, api_secret)

print('=== COMPREHENSIVE BALANCE CHECK ===')

total_usdt = 0.0

# 1. SPOT ACCOUNT
print('\n1. SPOT ACCOUNT:')
account = client.get_account()
balances = account['balances']
active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
spot_total = 0.0

for balance in active_balances:
    symbol = balance['asset']
    free = float(balance['free'])
    locked = float(balance['locked'])
    total = free + locked

    if symbol == 'USDT':
        spot_total += total
        total_usdt += total
        print(f'  {symbol}: {total} (FREE: {free}, LOCKED: {locked})')
    elif symbol == 'BUSD':
        spot_total += total
        total_usdt += total
        print(f'  {symbol}: {total} (FREE: {free}, LOCKED: {locked})')
    else:
        try:
            ticker = client.get_symbol_ticker(symbol=f'{symbol}USDT')
            price = float(ticker['price'])
            usd_value = total * price
            spot_total += usd_value
            total_usdt += usd_value
            print(f'  {symbol}: {total} = ${usd_value:.2f} USD (FREE: {free}, LOCKED: {locked})')
        except:
            print(f'  {symbol}: {total} (price unavailable) (FREE: {free}, LOCKED: {locked})')

print(f'Spot Total: ${spot_total:.2f} USDT')

# 2. FUTURES ACCOUNT
print('\n2. FUTURES ACCOUNT:')
futures_total = 0.0
try:
    futures_account = client.futures_account_balance()
    for asset in futures_account:
        balance = float(asset['balance'])
        if balance > 0:
            asset_name = asset['asset']
            if asset_name == 'USDT':
                futures_total += balance
                total_usdt += balance
            print(f'  {asset_name}: {balance}')
    print(f'Futures Total: ${futures_total:.2f} USDT')
except Exception as e:
    print(f'Futures error: {e}')

# 3. FUTURES POSITIONS
print('\n3. FUTURES POSITIONS:')
positions_value = 0.0
positions_pnl = 0.0
try:
    positions = client.futures_position_information()
    active_positions = [p for p in positions if float(p['positionAmt']) != 0]
    for position in active_positions:
        symbol = position['symbol']
        position_amt = float(position['positionAmt'])
        mark_price = float(position['markPrice'])
        leverage = float(position['leverage'])
        unrealized_pnl = float(position['unRealizedProfit'])

        notional_value = abs(position_amt) * mark_price / leverage
        positions_value += notional_value
        positions_pnl += unrealized_pnl

        print(f'  {symbol}: {position_amt} @ ${mark_price:.2f}, Notional: ${notional_value:.2f}, P&L: ${unrealized_pnl:+.2f}')

    total_usdt += positions_value + positions_pnl
    print(f'Positions Total Value: ${positions_value:.2f} USDT')
    print(f'Positions Total P&L: ${positions_pnl:+.2f} USDT')
except Exception as e:
    print(f'Positions error: {e}')

# 4. FUNDING ACCOUNT
print('\n4. FUNDING ACCOUNT:')
funding_total = 0.0
try:
    funding_account = client.futures_account()
    funding_balances = funding_account.get('assets', [])
    for asset in funding_balances:
        wallet_balance = float(asset.get('walletBalance', 0))
        if wallet_balance > 0:
            asset_name = asset['asset']
            if asset_name == 'USDT':
                funding_total += wallet_balance
                total_usdt += wallet_balance
            print(f'  {asset_name}: {wallet_balance}')
    print(f'Funding Total: ${funding_total:.2f} USDT')
except Exception as e:
    print(f'Funding error: {e}')

# 5. CROSS MARGIN
print('\n5. CROSS MARGIN:')
margin_total = 0.0
try:
    margin_account = client.get_margin_account()
    margin_balances = margin_account.get('userAssets', [])
    for asset in margin_balances:
        free = float(asset.get('free', 0))
        locked = float(asset.get('locked', 0))
        total = free + locked
        if total > 0:
            asset_name = asset['asset']
            if asset_name == 'USDT':
                margin_total += total
                total_usdt += total
            print(f'  {asset_name}: {total} (FREE: {free}, LOCKED: {locked})')
    print(f'Margin Total: ${margin_total:.2f} USDT')
except Exception as e:
    print(f'Margin error: {e}')

# 6. ISOLATED MARGIN
print('\n6. ISOLATED MARGIN:')
isolated_total = 0.0
try:
    isolated_accounts = client.get_isolated_margin_account()
    for symbol_info in isolated_accounts.get('assets', []):
        base_asset = symbol_info['baseAsset']
        quote_asset = symbol_info['quoteAsset']

        base_total = float(symbol_info['baseAsset']['free']) + float(symbol_info['baseAsset']['locked'])
        quote_total = float(symbol_info['quoteAsset']['free']) + float(symbol_info['quoteAsset']['locked'])

        if base_total > 0:
            print(f'  {base_asset}: {base_total}')
            if base_asset == 'USDT':
                isolated_total += base_total
                total_usdt += base_total

        if quote_total > 0:
            print(f'  {quote_asset}: {quote_total}')
            if quote_asset == 'USDT':
                isolated_total += quote_total
                total_usdt += quote_total

    print(f'Isolated Margin Total: ${isolated_total:.2f} USDT')
except Exception as e:
    print(f'Isolated margin error: {e}')

print(f'\n{"="*50}')
print(f'GRAND TOTAL: ${total_usdt:.2f} USDT')
print(f'{"="*50}')