
# Use the official Python image.
FROM python

# Install Node.js and npm.
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    apt-get clean

# Install playwright.
RUN npx playwright install

# Install carbon-now-cli globally.
RUN npm install -g carbon-now-cli

# Set the working directory.
WORKDIR /app

# Copy Python app requirements and install with pip.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create sub-directories.
RUN mkdir code_files
RUN mkdir images

# Copy configuration and code.
COPY config-*.json .
COPY run_carbon_cli.py .

# Define the default command.
CMD ["bash"]
