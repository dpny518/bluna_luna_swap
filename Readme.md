# Terraswap Luna:bluna exchange
## Swaps Luna to Bluna based on minimum rate


Edit Dockerfile, paste your seed phrase in the Dockerfile after ENV MNEMONIC "", where it says paste your seed phrase
Update buy and sell rates
```
luna_to_bluna_min_rate = 3
bluna_to_luna_min_rate = -1
```
Update NETWORK = 'TESTNET' or NETWORK = 'MAINNET' in swapbot.py
If you are using testnet, then you can get some coins for your account at 
```
https://faucet.terra.money/
```
Run the docker
```
docker build -t bluna_luna .
docker run -d bluna_luna:latest
```
Have it restart unless stopped
get your docker id
```
docker ps
```
after you have your docker id
```
docker update --restart unless-stopped [docker id]
```
