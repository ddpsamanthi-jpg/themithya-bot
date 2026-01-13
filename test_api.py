from binance.client import Client
import json

# Test the API keys
api_key = 'hEI0SE4toFiEgAVYmtaGK7uRC56yPZQGymEjN9jvxDiuFmG7cegyN9xWFsbTTXeK'
api_secret = 'pjp2rShx7XeHIDEp1NYLRlI8vdp55Go0jQCVxwlFKeQIENvksxmiyvlVq0oZNQwr'

try:
    client = Client(api_key, api_secret)
    print('Client created successfully')

    # Test account access
    account = client.get_account()
    print('Account access successful')
    print(f'Account type: {account.get("accountType", "unknown")}')

    # Check balances
    balances = account['balances']
    active_balances = [b for b in balances if float(b['free']) > 0 or float(b['locked']) > 0]
    print(f'Active balances: {len(active_balances)}')
    for balance in active_balances[:5]:  # Show first 5
        print(f'  {balance["asset"]}: {balance["free"]} free, {balance["locked"]} locked')

except Exception as e:
    print(f'Error: {e}')