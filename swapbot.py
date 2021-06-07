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

from time import sleep
from pprint import pprint, pp


import os
SEED = os.environ.get("MNEMONIC")
MILLION = 1000000

class BondedLunaToken:
    bLunaContract = 'terra1kc87mu460fwkqte29rquh4hc20m54fxwtsx7gp'
    
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
    terraSwapContract = "terra1jxazgm67et0ce260kvrpfv50acuushpjsz2y0p"
    bLunaContract = 'terra1kc87mu460fwkqte29rquh4hc20m54fxwtsx7gp'

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

    def swap(self, amount, return_amount):
        

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

        swap_bluna = MsgExecuteContract(
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

        tx = self.wallet.create_and_sign_tx(msgs=[increase_allowance, swap_bluna], gas_prices="0.15uusd", gas_adjustment=1.5)
        # fee = self.terra.tx.estimate_fee(tx)
        result = self.terra.tx.broadcast(tx)
        return [tx, result]
        # return result
    


    

bot_token = 'xxxxxxxxx'

terra = LCDClient(chain_id="columbus-4", url="https://lcd.terra.dev")
mk = MnemonicKey(mnemonic=SEED)
wallet = terra.wallet(mk)
swap = TerraSwap(terra, wallet)
bLunaToken = BondedLunaToken(terra, wallet)
# pp(bLunaToken.get_balance())
num_bLunaTokens = (int) (bLunaToken.get_balance()['balance']) / MILLION
pp(num_bLunaTokens)

swap_amount = 5
buy_min_rate = 0.03
sell_max_rate = 0.01

coins = terra.bank.balance(wallet.key.acc_address)
pp(coins)

num_Luna = coins.get('uluna').amount / MILLION
pp(num_Luna)
# terra.tx.search()
while True:
    rate = swap.get_exchange_rate(swap_amount)
    rate['zProfit'] = int(rate['return_amount']) / MILLION - swap_amount
    rate['zzPR'] = '{:.2%}'.format(rate['zProfit'] / swap_amount)
    rate['zzzAPR'] = '{:.2%}'.format(rate['zProfit'] / swap_amount / 21 * 365)
    rate['zzzzAPY'] = '{:.2%}'.format((1 + rate['zProfit'] / swap_amount) ** 17 - 1)
    pprint(rate)

    if(rate['zProfit'] / swap_amount > buy_min_rate):
        print('swap Luna -> bLuna')
        if(num_Luna < swap_amount):
            print('not enough Luna to swap')
        else:
            print('go swap')
    #     swap_result = swap.swap(swap_amount, rate['return_amount'])
    #     pprint(swap_result)
    #     break
    elif(rate['zProfit'] / swap_amount < sell_max_rate):
        print('swap bLuna -> Luna')
        if(num_bLunaTokens < swap_amount):
            print('not enough bLuna to swap')
        else:
            print('go swap')

    # break
    sleep(5)

