FROM python:3.8
WORKDIR /app
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000


ENV MNEMONIC "paste your seed phrase"

CMD ["python", "swapbot.py"]
