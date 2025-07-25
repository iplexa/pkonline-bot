# 1. Сборка фронта
FROM node:18-slim AS build

WORKDIR /app

# Копируем только package.json и lock для кэширования зависимостей
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Копируем исходники
COPY . .

# Отключаем sourcemap для ускорения
ENV GENERATE_SOURCEMAP=false

RUN npm run build

# 2. Сервер для статики
FROM nginx:alpine AS production

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 