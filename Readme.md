# Terraswap Luna:bluna exchange
## Swaps Luna to Bluna based on minimum rate


Edit Dockerfile, paste your seed phrase in the Dockerfile after ENV MNEMONIC "", where it says paste your seed phrase
Update buy and sell rates
```
luna_to_bluna_min_rate = 1.03
bluna_to_luna_min_rate = .98
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
