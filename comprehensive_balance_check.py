from binance.client import Client
import json

# API credentials
api_key = 'hEI0SE4toFiEgAVYmtaGK7uRC56yPZQGymEjN9jvxDiuFmG7cegyN9xWFsbTTXeK'
api_secret = 'pjp2rShx7XeHIDEp1NYLRlI8vdp55Go0jQCVxwlFKeQIENvksxmiyvlVq0oZNQwr'

client = Client(api_key, api_secret)

print("=" * 60)
print("COMPREHENSIVE BINANCE WALLET BALANCE CHECK")
print("=" * 60)

total_all_accounts = 0.0

# 1. SPOT ACCOUNT
print("\n1. SPOT ACCOUNT:")
print("-" * 30)
spot_total = 0.0
try:
    account = client.get_account()
    balances = account['balances']
    active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]

    if active_balances:
        for balance in active_balances:
            symbol = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked

            if symbol in ['USDT', 'BUSD']:
                spot_total += total
                total_all_accounts += total
                print(f"  {symbol}: {total:.8f} (Free: {free:.8f}, Locked: {locked:.8f})")
            else:
                try:
                    ticker = client.get_symbol_ticker(symbol=f'{symbol}USDT')
                    price = float(ticker['price'])
                    usd_value = total * price
                    spot_total += usd_value
                    total_all_accounts += usd_value
                    print(f"  {symbol}: {total:.8f} = ${usd_value:.2f} USD")
                except:
                    print(f"  {symbol}: {total:.8f} (price unavailable)")
    else:
        print("  No active balances")

    print(f"  SPOT TOTAL: ${spot_total:.2f} USDT")

except Exception as e:
    print(f"  SPOT ACCOUNT ERROR: {e}")

# 2. FUTURES ACCOUNT
print("\n2. FUTURES ACCOUNT:")
print("-" * 30)
futures_total = 0.0
try:
    futures_account = client.futures_account_balance()
    if futures_account:
        for asset in futures_account:
            balance = float(asset['balance'])
            if balance > 0:
                asset_name = asset['asset']
                if asset_name == 'USDT':
                    futures_total += balance
                    total_all_accounts += balance
                print(f"  {asset_name}: {balance:.8f}")
    print(f"  FUTURES TOTAL: ${futures_total:.2f} USDT")
except Exception as e:
    print(f"  FUTURES ACCOUNT ERROR: {e}")

# 3. FUTURES POSITIONS
print("\n3. FUTURES POSITIONS:")
print("-" * 30)
positions_value = 0.0
positions_pnl = 0.0
try:
    positions = client.futures_position_information()
    active_positions = [p for p in positions if float(p['positionAmt']) != 0]

    if active_positions:
        for position in active_positions:
            symbol = position['symbol']
            position_amt = float(position['positionAmt'])
            entry_price = float(position['entryPrice'])
            mark_price = float(position['markPrice'])
            leverage = float(position['leverage'])
            unrealized_pnl = float(position['unRealizedProfit'])

            notional_value = abs(position_amt) * mark_price / leverage
            positions_value += notional_value
            positions_pnl += unrealized_pnl

            print(f"  {symbol}: {position_amt:.4f} @ ${entry_price:.4f}")
            print(f"    Current: ${mark_price:.4f} | Leverage: {leverage}x")
            print(f"    Notional: ${notional_value:.2f} | P&L: ${unrealized_pnl:+.2f}")

        total_all_accounts += positions_value + positions_pnl
        print(f"  POSITIONS TOTAL VALUE: ${positions_value:.2f} USDT")
        print(f"  POSITIONS TOTAL P&L: ${positions_pnl:+.2f} USDT")
    else:
        print("  No active positions")

except Exception as e:
    print(f"  FUTURES POSITIONS ERROR: {e}")

# 4. FUNDING WALLET
print("\n4. FUNDING WALLET:")
print("-" * 30)
funding_total = 0.0
try:
    funding_account = client.futures_account()
    funding_balances = funding_account.get('assets', [])

    if funding_balances:
        for asset in funding_balances:
            wallet_balance = float(asset.get('walletBalance', 0))
            if wallet_balance > 0:
                asset_name = asset['asset']
                if asset_name == 'USDT':
                    funding_total += wallet_balance
                    total_all_accounts += wallet_balance
                print(f"  {asset_name}: {wallet_balance:.8f}")
    print(f"  FUNDING TOTAL: ${funding_total:.2f} USDT")
except Exception as e:
    print(f"  FUNDING WALLET ERROR: {e}")

# 5. CROSS MARGIN ACCOUNT
print("\n5. CROSS MARGIN ACCOUNT:")
print("-" * 30)
margin_total = 0.0
try:
    margin_account = client.get_margin_account()
    margin_balances = margin_account.get('userAssets', [])

    active_margin = [asset for asset in margin_balances if float(asset.get('free', 0)) > 0 or float(asset.get('locked', 0)) > 0]
    if active_margin:
        for asset in active_margin:
            free = float(asset.get('free', 0))
            locked = float(asset.get('locked', 0))
            total = free + locked
            asset_name = asset['asset']

            if asset_name in ['USDT', 'BUSD']:
                margin_total += total
                total_all_accounts += total
            print(f"  {asset_name}: {total:.8f} (Free: {free:.8f}, Locked: {locked:.8f})")
    else:
        print("  No active margin balances")

    print(f"  MARGIN TOTAL: ${margin_total:.2f} USDT")
except Exception as e:
    print(f"  CROSS MARGIN ERROR: {e}")

# 6. ISOLATED MARGIN ACCOUNTS
print("\n6. ISOLATED MARGIN ACCOUNTS:")
print("-" * 30)
isolated_total = 0.0
try:
    isolated_accounts = client.get_isolated_margin_account()
    assets = isolated_accounts.get('assets', [])

    if assets:
        for symbol_info in assets:
            base_asset = symbol_info['baseAsset']
            quote_asset = symbol_info['quoteAsset']

            base_total = float(symbol_info['baseAsset']['free']) + float(symbol_info['baseAsset']['locked'])
            quote_total = float(symbol_info['quoteAsset']['free']) + float(symbol_info['quoteAsset']['locked'])

            if base_total > 0:
                if base_asset in ['USDT', 'BUSD']:
                    isolated_total += base_total
                    total_all_accounts += base_total
                print(f"  {base_asset}: {base_total:.8f}")

            if quote_total > 0:
                if quote_asset in ['USDT', 'BUSD']:
                    isolated_total += quote_total
                    total_all_accounts += quote_total
                print(f"  {quote_asset}: {quote_total:.8f}")
    else:
        print("  No isolated margin accounts")

    print(f"  ISOLATED MARGIN TOTAL: ${isolated_total:.2f} USDT")
except Exception as e:
    print(f"  ISOLATED MARGIN ERROR: {e}")

# 7. EARN PRODUCTS (if accessible)
print("\n7. EARN/STAKING PRODUCTS:")
print("-" * 30)
try:
    # Try to get staking products
    staking = client.get_staking_product_list()
    if staking:
        print(f"  Found {len(staking)} staking products")
        for product in staking[:3]:  # Show first 3
            print(f"    {product.get('projectId', 'Unknown')}: {product.get('asset', 'Unknown')}")
    else:
        print("  No staking products found or not accessible")
except Exception as e:
    print(f"  STAKING PRODUCTS ERROR: {e}")

# 8. DUST LOGS (small amounts converted to BNB)
print("\n8. RECENT DUST LOGS:")
print("-" * 30)
try:
    dust_logs = client.get_dust_log()
    if dust_logs and 'results' in dust_logs:
        logs = dust_logs['results'][:3]  # Show last 3
        for log in logs:
            print(f"  {log.get('timestamp', 'Unknown')}: {log.get('totalServiceCharge', 'Unknown')} BNB")
    else:
        print("  No recent dust conversions")
except Exception as e:
    print(f"  DUST LOGS ERROR: {e}")

# FINAL SUMMARY
print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
print(f"Spot Account: ${spot_total:.2f} USDT")
print(f"Futures Account: ${futures_total:.2f} USDT")
print(f"Positions Value: ${positions_value:.2f} USDT")
print(f"Positions P&L: ${positions_pnl:+.2f} USDT")
print(f"Funding Wallet: ${funding_total:.2f} USDT")
print(f"Cross Margin: ${margin_total:.2f} USDT")
print(f"Isolated Margin: ${isolated_total:.2f} USDT")
print("-" * 60)
print(f"GRAND TOTAL (API ACCESSIBLE): ${total_all_accounts:.2f} USDT")
print("=" * 60)

# Check for potential missing balances
print("\nNOTE: This only shows balances accessible via API.")
print("Funds in Binance Earn, Locked Staking, or other products may not be included.")
print("If your actual balance is higher, check Binance app/website for complete view.")