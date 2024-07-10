#!/bin/sh

# Define the path to the .env file
ENV_FILE=".env"

# Write the environment variables to the .env file
echo "bot_token=$bot_token" >> $ENV_FILE
echo "chat_id=$chat_id" >> $ENV_FILE
echo "admin_id=$admin_id" >> $ENV_FILE
echo "timer=$timer" >> $ENV_FILE
echo "rate_limit=$rate_limit" >> $ENV_FILE
echo "silent_start=$silent_start" >> $ENV_FILE
echo "ssl_sert=$ssl_sert" >> $ENV_FILE
echo "ssl_privkey=$ssl_privkey" >> $ENV_FILE
echo "webhook_port=$webhook_port" >> $ENV_FILE