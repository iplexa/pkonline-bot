#!/bin/bash

# 🔍 Скрипт проверки подключения к базе данных PK Online Bot

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка наличия docker-compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose не установлен"
        exit 1
    fi
}

# Проверка статуса контейнеров
check_containers() {
    print_info "Проверка статуса контейнеров..."
    
    if ! docker-compose ps | grep -q "Up"; then
        print_error "Контейнеры не запущены"
        print_info "Запустите: docker-compose up -d"
        exit 1
    fi
    
    print_success "Контейнеры запущены"
}

# Проверка подключения к БД
check_db_connection() {
    print_info "Проверка подключения к базе данных..."
    
    if docker-compose exec db pg_isready -U pkonline; then
        print_success "База данных доступна"
    else
        print_error "База данных недоступна"
        return 1
    fi
}

# Проверка переменных окружения
check_env_vars() {
    print_info "Проверка переменных окружения..."
    
    # Проверяем наличие .env файла
    if [ ! -f ".env" ]; then
        print_warning "Файл .env не найден"
        return 1
    fi
    
    # Проверяем переменные БД
    source .env
    
    if [ -z "$POSTGRES_DB" ]; then
        print_warning "POSTGRES_DB не установлен"
    else
        print_success "POSTGRES_DB: $POSTGRES_DB"
    fi
    
    if [ -z "$POSTGRES_USER" ]; then
        print_warning "POSTGRES_USER не установлен"
    else
        print_success "POSTGRES_USER: $POSTGRES_USER"
    fi
    
    if [ -z "$POSTGRES_PASSWORD" ]; then
        print_warning "POSTGRES_PASSWORD не установлен"
    else
        print_success "POSTGRES_PASSWORD: установлен"
    fi
}

# Проверка порта
check_port() {
    print_info "Проверка порта 5432..."
    
    if netstat -tulpn 2>/dev/null | grep -q ":5432 "; then
        print_success "Порт 5432 доступен"
    else
        print_warning "Порт 5432 не найден в netstat"
        print_info "Попробуйте: docker-compose logs db"
    fi
}

# Тестовый запрос к БД
test_query() {
    print_info "Выполнение тестового запроса..."
    
    result=$(docker-compose exec -T db psql -U pkonline -d pkonline -t -c "SELECT version();" 2>/dev/null | tr -d ' ')
    
    if [ ! -z "$result" ]; then
        print_success "Тестовый запрос выполнен успешно"
        print_info "PostgreSQL версия: $result"
    else
        print_error "Ошибка выполнения тестового запроса"
        return 1
    fi
}

# Показать информацию о подключении
show_connection_info() {
    print_info "Информация для подключения:"
    echo
    echo "📊 Параметры подключения:"
    echo "   Хост: localhost"
    echo "   Порт: 5432"
    echo "   База данных: pkonline"
    echo "   Пользователь: pkonline"
    echo "   Пароль: pkonline"
    echo "   SSL: Отключен"
    echo
    echo "🔗 Строка подключения:"
    echo "   postgresql://pkonline:pkonline@localhost:5432/pkonline"
    echo
    echo "📖 Подробная инструкция: DATABASE_ACCESS.md"
}

# Проверка таблиц
check_tables() {
    print_info "Проверка таблиц базы данных..."
    
    tables=$(docker-compose exec -T db psql -U pkonline -d pkonline -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null)
    
    if [ ! -z "$tables" ]; then
        print_success "Таблицы найдены:"
        echo "$tables" | sed 's/^/  - /'
    else
        print_warning "Таблицы не найдены"
        print_info "Возможно, миграции не применены"
    fi
}

# Основная функция
main() {
    echo "🔍 Проверка подключения к базе данных PK Online Bot"
    echo "=================================================="
    echo
    
    check_docker_compose
    check_containers
    check_env_vars
    check_port
    check_db_connection
    test_query
    check_tables
    
    echo
    echo "=================================================="
    print_success "Проверка завершена"
    echo
    
    show_connection_info
}

# Запуск скрипта
main "$@" 