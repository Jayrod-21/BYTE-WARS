# BYTE Wars Frontend Dockerfile
# Builds the React/Vite development server.

FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["sh", "-c", "npm install && npx vite --host 0.0.0.0 --port 5173"]
