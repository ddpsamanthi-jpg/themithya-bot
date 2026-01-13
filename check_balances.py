from binance.client import Client
import json

# Test the API keys
api_key = 'hEI0SE4toFiEgAVYmtaGK7uRC56yPZQGymEjN9jvxDiuFmG7cegyN9xWFsbTTXeK'
api_secret = 'pjp2rShx7XeHIDEp1NYLRlI8vdp55Go0jQCVxwlFKeQIENvksxmiyvlVq0oZNQwr'

client = Client(api_key, api_secret)

print('=== SPOT ACCOUNT ===')
account = client.get_account()
balances = account['balances']
active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
for balance in active_balances:
    print(f'{balance["asset"]}: {balance["free"]} free, {balance["locked"]} locked')

print('\n=== FUTURES ACCOUNT BALANCE ===')
try:
    futures_account = client.futures_account_balance()
    for asset in futures_account:
        balance = float(asset['balance'])
        if balance > 0:
            print(f'{asset["asset"]}: {balance}')
except Exception as e:
    print(f'Futures error: {e}')

print('\n=== FUTURES POSITIONS ===')
try:
    positions = client.futures_position_information()
    active_positions = [p for p in positions if float(p['positionAmt']) != 0]
    for position in active_positions:
        symbol = position['symbol']
        position_amt = float(position['positionAmt'])
        unrealized_pnl = float(position['unRealizedProfit'])
        print(f'{symbol}: {position_amt} @ P&L: {unrealized_pnl}')
except Exception as e:
    print(f'Positions error: {e}')

print('\n=== FUNDING ACCOUNT ===')
try:
    funding_account = client.futures_account()
    funding_balances = funding_account.get('assets', [])
    for asset in funding_balances:
        wallet_balance = float(asset.get('walletBalance', 0))
        if wallet_balance > 0:
            print(f'{asset["asset"]}: {wallet_balance}')
except Exception as e:
    print(f'Funding error: {e}')

print('\n=== CROSS MARGIN ACCOUNT ===')
try:
    margin_account = client.get_margin_account()
    margin_balances = margin_account.get('userAssets', [])
    for asset in margin_balances:
        free = float(asset.get('free', 0))
        locked = float(asset.get('locked', 0))
        total = free + locked
        if total > 0:
            print(f'{asset["asset"]}: {free} free, {locked} locked')
except Exception as e:
    print(f'Margin error: {e}')

print('\n=== ISOLATED MARGIN ACCOUNTS ===')
try:
    isolated_accounts = client.get_isolated_margin_account()
    for symbol_info in isolated_accounts.get('assets', []):
        base_asset = symbol_info['baseAsset']
        quote_asset = symbol_info['quoteAsset']
        base_balance = float(symbol_info['baseAsset']['free']) + float(symbol_info['baseAsset']['locked'])
        quote_balance = float(symbol_info['quoteAsset']['free']) + float(symbol_info['quoteAsset']['locked'])
        if base_balance > 0:
            print(f'{base_asset} (Isolated): {base_balance}')
        if quote_balance > 0:
            print(f'{quote_asset} (Isolated): {quote_balance}')
except Exception as e:
    print(f'Isolated margin error: {e}')