# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 1138 available to the world outside this container
EXPOSE 1138

# Define environment variable
ENV FLASK_APP=config_ui.py

# Run config_ui.py when the container launches
CMD ["python", "config_ui.py"]

