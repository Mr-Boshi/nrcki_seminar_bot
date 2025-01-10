# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update -y && apt-get install -y --no-install-recommends wget xvfb unzip jq curl \
        libxss1 libappindicator1 libgconf-2-4 libgbm1 libatk-bridge2.0-0 libgtk-3-0 libxcb-dri3-0 \
        fonts-liberation libasound2 libnspr4 libnss3 libx11-xcb1 libxtst6 lsb-release xdg-utils
        
# Fetch the latest version numbers and URLs for Chrome and ChromeDriver and install them
RUN curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json > /tmp/versions.json && \
    CHROME_URL=$(jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
    CHROMEDRIVER_URL=$(jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
    wget -q --continue -O /tmp/chrome-linux64.zip $CHROME_URL && \
    unzip /tmp/chrome-linux64.zip -d /opt/chrome && \
    chmod +x /opt/chrome/chrome-linux64/chrome && \
    wget -q --continue -O /tmp/chromedriver-linux64.zip $CHROMEDRIVER_URL && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/chromedriver && \
    chmod +x /opt/chromedriver/chromedriver-linux64/chromedriver && \
    # Clean up temporary files
    rm /tmp/chrome-linux64.zip /tmp/chromedriver-linux64.zip /tmp/versions.json && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set up Environment variables for ChromeDriver and Telegram bot
ENV CHROMEDRIVER_DIR=/opt/chromedriver \
    PATH=$CHROMEDRIVER_DIR:$PATH \
    bot_token='changeme' \
    chat_id='changeme' \
    admin_id='changeme' \
    request_target='changeme' \
    timer=1 \
    rate_limit=3 \
    silent_mode=False \
    IN_DOCKER=1 \
    config_file=/app/config/config.yaml

RUN echo "Europe/Moscow" > /etc/timezone \
    dpkg-reconfigure -f noninteractive tzdata

# Create necessary directories
RUN mkdir -p /app/modules /app/bot /app/data /app/config

# Copy the Python requirements file
COPY requirements.txt .
COPY main.py .
COPY __init__.py .
COPY modules modules
COPY bot bot
COPY config.yaml /app/config/config.yaml

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot script when the container launches
CMD ["python", "main.py"]