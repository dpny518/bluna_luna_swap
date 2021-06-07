# Terraswap Luna:bluna exchange
## Swaps Luna to Bluna if % > buy_min_rate and Swaps back if % < sell_max_rate 


Edit Dockerfile, paste your seed phrase in the Dockerfile after ENV MNEMONIC "", where it says paste your seed phrase
Update buy and sell rates
```
buy_min_rate
sell_max_rate 
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
