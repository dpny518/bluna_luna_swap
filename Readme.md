# Terraswap Luna:bluna exchange
## Swaps Luna to Bluna based on minimum rate


Edit Dockerfile, paste your seed phrase in the Dockerfile after ENV MNEMONIC "", where it says paste your seed phrase
Update belief prices, so how many luna you want per bluna, and how many bluna you want per luna
```
luna_to_bluna_belief_price = 3
bluna_to_luna_belief_price = .2
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
