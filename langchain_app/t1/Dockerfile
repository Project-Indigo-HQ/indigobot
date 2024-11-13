#Start with a base image of Python 3.10
FROM python:3.10-slim

#Set working directory in the container
WORKDIR /app

#Copy requirements.txt to the working directory
COPY requirements.txt .

COPY . .
#Copy the rest of the application files
COPY OWASPtop10forLLMs.pdf /app/

#Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Command to run your app (adjust in future)
CMD ["python", "t1.py"]
