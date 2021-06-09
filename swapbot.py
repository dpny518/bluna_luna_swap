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
import base64
import os
import json


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

    def get_exchange_rate_luna_bluna(self, amount_luna):
     result = self.terra.wasm.contract_query(
            self.terraSwapContract,
    {
                "simulation": {
                    "offer_asset": {
                        "amount": str(amount_luna * MILLION),
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
    def get_exchange_rate_bluna_luna(self, amount_bluna):

          # Bluna to Luna
        #query_msg = '{"simulation":{"offer_asset":{"amount":"'+str(amount_bluna)+'","info":{"token":{"'+str(self.terraSwapContract)+'":"'+str(self.bLunaContract)+'"}}}}}'
        result = self.terra.wasm.contract_query(
            self.terraSwapContract,
             {
                "simulation": {
                    "offer_asset": {
                        "amount": str(amount_bluna * MILLION),
                        "info": {
                            "token": {
                                "contract_addr": str(self.bLunaContract)
                            }
                        }
                    }
                }
            }
        )
        return result
    def swap_luna(self, amount,belief_price):
        print("luna amount: "+str(amount))
        print("bluna amount: "+str(belief_price))
        max_spread=.001
        if belief_price > 1:
            return_amount=int(belief_price * 1000000)
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
                        "belief_price": str(int(belief_price * 1000000)),
                        "max_spread": str(max_spread),
                        "offer_asset": {
                            "amount": str(amount * 1000000),
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
        else:
            return

    def swap_bluna(self, amount,belief_price):
        print("bluna amount: "+str(amount))
        print("luna amount: "+str(belief_price))
        if belief_price > 1:
            return_amount=belief_price
            max_spread=.001
            msg_json = {
            "swap": {
            "belief_price": str(int(belief_price * 1000000)),
            "max_spread": f"{max_spread}",
                        }
                  }

            json_string = json.dumps(msg_json)
            msg = base64.b64encode(json_string.encode("utf-8"))

            swap_bluna_to_luna = MsgExecuteContract(
                self.wallet.key.acc_address,
                self.bLunaContract,
                {
                "send": {
                "contract": "terra13e4jmcjnwrauvl2fnjdwex0exuzd8zrh5xk29v",
                "amount": str(amount * MILLION),
                "msg": f"{msg.decode('utf-8')}"
                  }
                }
      

                )
            tx = self.wallet.create_and_sign_tx(msgs=[swap_bluna_to_luna], gas_prices="0.15uusd", gas_adjustment=1.5)
            # fee = self.terra.tx.estimate_fee(tx)
            result = self.terra.tx.broadcast(tx)
            return [tx, result]
        else:
            return






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
luna_to_bluna_min_rate = 0
bluna_to_luna_min_rate = 0

coins = terra.bank.balance(wallet.key.acc_address)
pp("Native coins")
pp(coins)

num_Luna = coins.get('uluna').amount / MILLION
pp("number of luna")
pp(num_Luna)
# terra.tx.search()
swap_amount=500
while True:
    num_Luna = coins.get('uluna').amount / MILLION
    num_bLunaTokens = (int) (bLunaToken.get_balance()['balance']) / MILLION
    pp("Current coins before")
    pp("number of luna")
    pp(num_Luna)
    pp("number of bluna")
    pp(num_bLunaTokens)
    if num_Luna  > num_bLunaTokens:
        swap_amount=int(num_Luna)
        rate = swap.get_exchange_rate_luna_bluna(swap_amount)
        return_amount = (int) (rate['return_amount']) / MILLION
        lunas_to_blunas_diff = return_amount - swap_amount
        exchange_rate = (lunas_to_blunas_diff + swap_amount) / 1000000
        print('luna to Bluna')
        print(exchange_rate)
        print("we need to find a good time to switch luna to bluna")
        if(exchange_rate>luna_to_bluna_min_rate):
            print('swap Luna -> bLuna')
            swap_result = swap.swap_luna(swap_amount, return_amount)
            #print(swap_result[1].raw_log
            print("swapped"+str(swap_amount)+"luna for"+str(return_amount)+"bluna")
        else:
            print("not good rate to swap, current rate:"+ str(exchange_rate))
            print("We want a rate better than" + str(luna_to_bluna_min_rate))
    else:
        swap_amount=int(num_bLunaTokens)
        rate = swap.get_exchange_rate_bluna_luna(swap_amount)
        return_amount = (int) (rate['return_amount']) / MILLION
        lunas_to_blunas_diff = return_amount - swap_amount
        exchange_rate = (lunas_to_blunas_diff + swap_amount) / 1000000
        print('bluna to luna')
        print(exchange_rate)
        print("we need to find a good time to switch bluna to luna")
        if(exchange_rate>bluna_to_luna_min_rate):
            print('swap bluna -> Luna')
            swap_result = swap.swap_bluna(swap_amount,return_amount)
            #print(swap_result[1].raw_log
            print("swapped"+str(swap_amount)+"bluna for"+str(return_amount)+"luna")
        else:
            print("not good rate to swap, current rate:" +str(exchange_rate))
            print("We want a rate better than:"+ str(bluna_to_luna_min_rate))


    sleep(5)


