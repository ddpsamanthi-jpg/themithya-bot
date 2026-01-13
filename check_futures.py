from binance.client import Client

client = Client('hEI0SE4toFiEgAVYmtaGK7uRC56yPZQGymEjN9jvxDiuFmG7cegyN9xWFsbTTXeK', 'pjp2rShx7XeHIDEp1NYLRlI8vdp55Go0jQCVxwlFKeQIENvksxmiyvlVq0oZNQwr')

print('Futures Account Details:')
try:
    acc = client.futures_account()
    print(f'Available Balance: {acc.get("availableBalance", "N/A")}')
    print(f'Total Wallet Balance: {acc.get("totalWalletBalance", "N/A")}')
    print(f'Total Unrealized Profit: {acc.get("totalUnrealizedProfit", "N/A")}')

    assets = acc.get('assets', [])
    for asset in assets:
        if float(asset.get('walletBalance', 0)) > 0:
            print(f'  {asset["asset"]}: {asset["walletBalance"]} (margin: {asset.get("marginBalance", 0)})')
except Exception as e:
    print(f'Error: {e}')

print('\nChecking for Staking/Savings:')
try:
    staking = client.get_staking_product_list()
    print(f'Staking products: {len(staking)}')
except Exception as e:
    print(f'Staking check failed: {e}')