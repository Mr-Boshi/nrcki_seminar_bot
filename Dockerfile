# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update -y && apt-get install -y wget xvfb unzip jq curl

# Install Google Chrome dependencies
RUN apt-get install -y libxss1 libappindicator1 libgconf-2-4 \
    fonts-liberation libasound2 libnspr4 libnss3 libx11-xcb1 libxtst6 lsb-release xdg-utils \
    libgbm1 libnss3 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 libxcb-dri3-0


# Fetch the latest version numbers and URLs for Chrome and ChromeDriver
RUN curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json > /tmp/versions.json

RUN CHROME_URL=$(jq -r '.channels.Stable.downloads.chrome[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
    wget -q --continue -O /tmp/chrome-linux64.zip $CHROME_URL && \
    unzip /tmp/chrome-linux64.zip -d /opt/chrome

RUN chmod +x /opt/chrome/chrome-linux64/chrome


RUN CHROMEDRIVER_URL=$(jq -r '.channels.Stable.downloads.chromedriver[] | select(.platform=="linux64") | .url' /tmp/versions.json) && \
    wget -q --continue -O /tmp/chromedriver-linux64.zip $CHROMEDRIVER_URL && \
    unzip /tmp/chromedriver-linux64.zip -d /opt/chromedriver && \
    chmod +x /opt/chromedriver/chromedriver-linux64/chromedriver

# Set up Chromedriver Environment variables
ENV CHROMEDRIVER_DIR /opt/chromedriver
ENV PATH $CHROMEDRIVER_DIR:$PATH

# Clean upa
RUN rm /tmp/chrome-linux64.zip /tmp/chromedriver-linux64.zip /tmp/versions.json

# Set your environment variables using the ENV instruction
ENV bot_token  = 'changeme'
ENV chat_id    = 'changeme'
ENV admin_id   = 'changeme'
ENV timer      = 1
ENV rate_limit = 3

# Set the working directory in the container
WORKDIR /app
RUN mkdir /modules
RUN mkdir /news

# Copy the Python requirements file
COPY requirements.txt .
COPY bot.py .
COPY __init__.py .
COPY modules modules
COPY set_env.sh set_env.sh

# Run the script to generate the .env file
RUN chmod +x set_env.sh
RUN sh set_env.sh

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the bot script when the container launches
CMD ["python", "bot.py"]