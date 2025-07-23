FROM python:3.13
WORKDIR /bot

ENV TZ=Europe/Moscow

ENV TZ=Europe/Moscow
ENV LANG=ru_RU.UTF-8
ENV LANGUAGE=ru_RU
ENV LC_ALL=ru_RU.UTF-8

# Установка nano и обновление пакетов
RUN apt-get update && \
    apt-get install -y nano locales && \
    echo "ru_RU.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["python", "main.py", "--start"]