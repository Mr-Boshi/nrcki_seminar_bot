# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the Python requirements file
COPY requirements.txt .

# Install any needed dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot script into the container
COPY your_bot_script.py .

# Run the bot script when the container launches
CMD ["python", "your_bot_script.py"]