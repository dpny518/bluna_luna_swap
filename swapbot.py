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
import base64
import os
import json


SEED = os.environ.get("MNEMONIC")
NETWORK = 'TESTNET'
MILLION = 1000000
TWOHUNDREDANDFIFTYTHOUSAND=250000
HUNDREDTHOUSAND=100000

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

    # Run simulation to get return amount
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
    def get_fee_estimation(self):
        estimation = terra.treasury.tax_cap('uusd')

        return estimation.to_data().get('amount')

    # Swap function
    def swap_luna(self, amount,return_amount, belief_price, max_spread):
        print("luna amount: "+str(amount))
        print("bluna amount: "+str(return_amount))
        print("belief price, bluna per luna "+str(belief_price))
        if return_amount> 1:
            increase_allowance = MsgExecuteContract(
                self.wallet.key.acc_address,
                self.bLunaContract,
                {
                    "increase_allowance": {
                        "amount": str(int(return_amount* MILLION)),
                        "spender": self.terraSwapContract
                    }
                }
            )

          
            swap_luna_to_bluna = MsgExecuteContract(
                self.wallet.key.acc_address,
                self.terraSwapContract,
                {
                    "swap": {
                        "belief_price": str(int(belief_price* MILLION)),
                        "max_spread": str(max_spread),
                        "offer_asset": {
                            "amount": str(int(amount * MILLION)),
                            "info": {
                                "native_token": {
                                    "denom": "uluna"
                                }
                            }
                        }
                    }
                },
                {"uluna": int(amount * MILLION)},
            )
            fee_estimation = self.get_fee_estimation()
            fee = str(int(fee_estimation) + TWOHUNDREDANDFIFTYTHOUSAND) + 'uusd'
            #tx = self.wallet.create_and_sign_tx(msgs=[swap_luna_to_bluna],fee=StdFee(MILLION, fee))
            tx = self.wallet.create_and_sign_tx(msgs=[swap_luna_to_bluna], gas_prices="0.15uusd", gas_adjustment=1.5)
            result = self.terra.tx.broadcast(tx)
            return [tx, result]
        # return result
        else:
            return

    def swap_bluna(self, amount,return_amount, belif_price,max_spread):
        print("luna amount: "+str(amount))
        print("bluna amount: "+str(return_amount))
        print("belief price, luna rate per bluna "+str(belief_price))
        if return_amount> 1:
            msg_json = {
            "swap": {
            "belief_price": str(belief_price* MILLION),
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
                "contract": self.terraSwapContract,
                "amount": str(amount * MILLION),
                "msg": f"{msg.decode('utf-8')}"
                  }
                }
      

                )
            fee_estimation = self.get_fee_estimation()
            fee = str(int(fee_estimation) + TWOHUNDREDANDFIFTYTHOUSAND) + 'uusd'
            #tx = self.wallet.create_and_sign_tx(msgs=[swap_bluna_to_luna],fee=StdFee(MILLION, fee))
            tx = self.wallet.create_and_sign_tx(msgs=[swap_bluna_to_luna], gas_prices="0.15uusd", gas_adjustment=1.5)
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
# print(bLunaToken.get_balance())
num_bLunaTokens = (int) (bLunaToken.get_balance()['balance']) / MILLION
print("Start of Bot")
print("number of bluna")
print(num_bLunaTokens)

#Minimum exchange rate, how many coins do you get for your input
luna_to_bluna_belief_price = 3
bluna_to_luna_belief_price = .2
print("1 luna will become "+str(luna_to_bluna_belief_price)+" bluna")
print("1 bluna will become "+str(bluna_to_luna_belief_price)+" luna")

coins = terra.bank.balance(wallet.key.acc_address)

print("Native coins")
print(coins)


num_Luna = coins.get('uluna').amount / MILLION
print("number of luna")
print(num_Luna)
# terra.tx.search()
swap_amount=500
while True:
    # Check new balance of bluna and luna each time
    max_spread=.001
    bLunaToken = BondedLunaToken(terra, wallet)
    coins = terra.bank.balance(wallet.key.acc_address)
    num_Luna = coins.get('uluna').amount / MILLION
    num_bLunaTokens = (int) (bLunaToken.get_balance()['balance']) / MILLION
    print("Current coins before swap")
    print("number of luna")
    print(num_Luna)
    print("number of bluna")
    print(num_bLunaTokens)
    # Decide which coin to check rate to swap based on which one you have more of
    if num_Luna  > num_bLunaTokens:
        swap_amount=int(num_Luna)
        # Run simulation to get exchange rate and amount
        rate = swap.get_exchange_rate_luna_bluna(swap_amount)
        return_amount = (int) (rate['return_amount']) / MILLION
        # Calcualte exchange rate
        lunas_to_blunas_diff = return_amount - swap_amount
        belief_price = (return_amount/swap_amount)
        print("Number of bluna we get for each luna")
        print(belief_price)
        print("we need to find a good time to switch luna to bluna, we want to get better than "+str(belief_price)+"bluna for each luna")
        # Swap if exchange rate is met
        if(belief_price > bluna_to_luna_belief_price):
            print('swap Luna -> bLuna')
            # Actual swap
            swap_result = swap.swap_luna(swap_amount, return_amount, belief_price, max_spread)
            print(swap_result)
            print("swapped"+str(swap_amount)+"luna for"+str(return_amount)+"bluna")
        else:
            print("not good rate to swap, current rate:"+ str(exchange_rate))
            print("We want a rate better than" + str(luna_to_bluna_min_rate))
    # Same logic as luna to bluna just with bluna
    else:
        swap_amount=int(num_bLunaTokens)
        rate = swap.get_exchange_rate_bluna_luna(swap_amount)
        return_amount = (int) (rate['return_amount']) / MILLION
        belief_price = (return_amount/swap_amount)
        print("Number of luna we get for each bluna")
        print(belief_price)
        print("we need to find a good time to switch bluna to luna, we want to get better than "+str(belief_price)+"luna for each bluna")
        if(belief_price > bluna_to_luna_belief_price):
            print('swap bluna -> Luna')
            # Actual swap
            swap_result = swap.swap_bluna(swap_amount, return_amount, belief_price, max_spread)
            print(swap_result)
            print("swapped"+str(swap_amount)+"bluna for"+str(return_amount)+"luna")
        else:
            print("not good rate to swap, current rate:" +str(exchange_rate))
            print("We want a rate better than:"+ str(bluna_to_luna_min_rate))

# Time between checking for swap
    sleep(5)


