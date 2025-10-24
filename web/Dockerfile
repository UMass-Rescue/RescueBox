# Start of a Dockerfile for frontend container

#Use an official node image as the base (Node version 20)
FROM node:20-alpine

# Set the working directory
WORKDIR /rescuebox-desktop

# Copy the package.json and package-lock.json files
COPY RescueBox-Desktop/package*.json ./

# Install the dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the application port
EXPOSE 1212

# Start the application
CMD ["npm", "start"]