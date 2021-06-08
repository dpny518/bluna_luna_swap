import http.client
import requests
import urllib3.exceptions
from terra_sdk.client.lcd import LCDClient
from terra_sdk.exceptions import LCDResponseError
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.core.auth import StdFee
from terra_sdk.core.bank import MsgSend
from terra_sdk.core.wasm import MsgExecuteContract
from terra_sdk.core.coins import Coins
from contact_addresses import contact_addresses_lookup
from time import sleep
from pprint import pprint, pp
from terraswap_swap_watch import run_terra_swap_price_watcher, get_luna_price_prices
import base64
import os
SEED = os.environ.get("MNEMONIC")
NETWORK = 'TESTNET'
MILLION = 1000000


if NETWORK == 'MAINNET':
    chain_id = 'columbus-4'
    public_node_url = 'https://lcd.terra.dev'
    contact_addresses = contact_addresses_lookup(network='MAINNET')
    tx_look_up = f'https://finder.terra.money/{chain_id}/tx/'

else:
    chain_id = 'tequila-0004'
    public_node_url = 'https://tequila-fcd.terra.dev'
    contact_addresses = contact_addresses_lookup(network='TESTNET')
    tx_look_up = f'https://finder.terra.money/{chain_id}/tx/'



class BondedLunaToken:
    bLunaContract = contact_addresses['bLunaToken']
    
    def __init__(self, terra, wallet=None) -> None:
        self.terra = terra
        self.wallet = wallet 

    def get_balance(self):
        result = self.terra.wasm.contract_query(
            self.bLunaContract,
            {
                "balance": {
                    "address": self.wallet.key.acc_address
                }
            }
        )
        return result   

class TerraSwap:
    terraSwapContract = contact_addresses['terraswapblunaLunaPair']
    bLunaContract = contact_addresses['bLunaToken']

    def __init__(self, terra, wallet=None) -> None:
        self.terra = terra
        self.wallet = wallet

    def get_exchange_rate(self, amount):
        result = self.terra.wasm.contract_query(
            self.terraSwapContract,
            {
                "simulation": {
                    "offer_asset": {
                        "amount": str(amount * MILLION),
                        "info": {
                            "native_token": {
                                "denom": "uluna"
                            }
                        }
                    }
                }
            }
        )
        return result

    def swap_luna(self, amount, return_amount):
        

        increase_allowance = MsgExecuteContract(
            self.wallet.key.acc_address,
            self.bLunaContract,
            {
                "increase_allowance": {
                    "amount": str(return_amount),
                    "spender": self.terraSwapContract
                }
            }
        )

      
        swap_luna_to_bluna = MsgExecuteContract(
            self.wallet.key.acc_address,
            self.terraSwapContract,
            {
                "swap": {
                    "offer_asset": {
                        "amount": str(amount * MILLION),
                        "info": {
                            "native_token": {
                                "denom": "uluna"
                            }
                        }
                    }
                }
            },
            {"uluna": amount * 1000000},
        )
        tx = self.wallet.create_and_sign_tx(msgs=[increase_allowance, swap_luna_to_bluna], gas_prices="0.15uusd", gas_adjustment=1.5)
        # fee = self.terra.tx.estimate_fee(tx)
        result = self.terra.tx.broadcast(tx)
        return [tx, result]
        # return result
    

    def swap_bluna(self, amount, return_amount):
        

        swap_bluna_to_luna = MsgExecuteContract(
            self.wallet.key.acc_address,
            self.bLunaContract,
  
{
  "send": {
    "contract": "terra13e4jmcjnwrauvl2fnjdwex0exuzd8zrh5xk29v",
    "amount": str(amount * MILLION),
    "msg": "eyJzd2FwIjp7fX0="
      }
    }
  

            )
        tx = self.wallet.create_and_sign_tx(msgs=[swap_bluna_to_luna], gas_prices="0.15uusd", gas_adjustment=1.5)
        # fee = self.terra.tx.estimate_fee(tx)
        result = self.terra.tx.broadcast(tx)
        return [tx, result]
        # return result
    






# Connect to Testnet
terra = LCDClient(chain_id=chain_id, url=public_node_url)    
mk = MnemonicKey(mnemonic=SEED)
wallet = terra.wallet(mk)
swap = TerraSwap(terra, wallet)
bLunaToken = BondedLunaToken(terra, wallet)
# pp(bLunaToken.get_balance())
num_bLunaTokens = (int) (bLunaToken.get_balance()['balance']) / MILLION
pp("number of bluna")
pp(num_bLunaTokens)

#swap_amount = 100
luna_to_bluna_min_rate = 1.03
bluna_to_luna_min_rate = .98

coins = terra.bank.balance(wallet.key.acc_address)
pp("number of native coins")
pp(coins)

num_Luna = coins.get('uluna').amount / MILLION
pp("number of luna")
pp(num_Luna)
# terra.tx.search()
swap_amount=500
while True:
    num_Luna = coins.get('uluna').amount / MILLION
    num_bLunaTokens = (int) (bLunaToken.get_balance()['balance']) / MILLION
    if num_Luna  > num_bLunaTokens:
        swap_amount=int(num_Luna)  
    else:
        swap_amount=int(num_bLunaTokens)
    rate = swap.get_exchange_rate(swap_amount)
    return_amount = int(swap.get_exchange_rate(swap_amount)['return_amount'])
    exchange_rate = round(return_amount * 100 / (swap_amount * 1000000) - 100, 3)

    terraswap_prices = run_terra_swap_price_watcher()
    print('luna to Bluna')
    luna_bluna_ratio=terraswap_prices[0]
    bluna_luna_ratio=terraswap_prices[1]
    print(luna_bluna_ratio)
    print('bluna to luna')
    print(bluna_luna_ratio)


    if num_Luna  > num_bLunaTokens:
        print("we need to find a good time to switch luna to bluna")
        if(luna_bluna_ratio>luna_to_bluna_min_rate):
            swap_amount=int(num_Luna)
            print('swap Luna -> bLuna')
            swap_result = swap.swap_luna(swap_amount, rate['return_amount'])
            print(swap_result)
        else:
            print("not good rate to swap, current rate:"+ str(luna_bluna_ratio))
            print("We want a rate better than:, current rate:" + str(luna_to_bluna_min_rate))
    else:
        print("we need to find a good time to switch bluna to luna")
        if(bluna_luna_ratio>bluna_to_luna_min_rate):
            print('swap bluna -> Luna')
            swap_amount=int(num_bLunaTokens)
            swap_result = swap.swap_bluna(swap_amount, rate['return_amount'])
            print(swap_result)
        else:
            print("not good rate to swap, current rate:" +str(bluna_luna_ratio))
            print("We want a rate better than:, current rate:"+ str(bluna_to_luna_min_rate))
    sleep(360)


