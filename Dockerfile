FROM python:3.13
WORKDIR /bot

ENV TZ=Europe/Moscow

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["python", "main.py", "--start"]