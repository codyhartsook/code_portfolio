# Use an official Python runtime as a parent image
FROM python:3-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 13800 available to the world outside this container
EXPOSE 13800

# Define environment variable
ENV NAME CS_138

# Run app.py when the container launches
CMD ["python3", "app.py"]