# Этап сборки
FROM node:18-alpine as build

WORKDIR /app

# Копирование package.json
COPY package.json ./

# Установка зависимостей (создаст package-lock.json если его нет)
RUN npm install

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Этап продакшена
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/build /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 80

# Запуск nginx
CMD ["nginx", "-g", "daemon off;"] 