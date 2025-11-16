FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Clean install - npm will install both ajv v6 and v8 where needed
RUN npm install && \
    npm cache clean --force

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start the development server
CMD ["npm", "start"]
