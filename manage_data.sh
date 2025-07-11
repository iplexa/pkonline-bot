#!/bin/bash

# 🐳 Скрипт для управления данными PK Online Bot
# Безопасное управление данными БД при работе с Docker Compose

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

# Создание бэкапа БД
create_backup() {
    print_info "Создание бэкапа базы данных..."
    
    if [ ! -d "backups" ]; then
        mkdir -p backups
    fi
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="backups/backup_${timestamp}.sql"
    
    docker-compose exec -T db pg_dump -U pkonline pkonline > "$backup_file"
    
    if [ $? -eq 0 ]; then
        print_success "Бэкап создан: $backup_file"
        print_info "Размер файла: $(du -h "$backup_file" | cut -f1)"
    else
        print_error "Ошибка при создании бэкапа"
        exit 1
    fi
}

# Восстановление из бэкапа
restore_backup() {
    if [ -z "$1" ]; then
        print_error "Укажите файл бэкапа для восстановления"
        echo "Использование: $0 restore <backup_file>"
        exit 1
    fi
    
    backup_file="$1"
    
    if [ ! -f "$backup_file" ]; then
        print_error "Файл бэкапа не найден: $backup_file"
        exit 1
    fi
    
    print_warning "Восстановление из бэкапа: $backup_file"
    print_warning "Это перезапишет все текущие данные!"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Останавливаем контейнеры..."
        docker-compose down
        
        print_info "Запускаем только БД..."
        docker-compose up -d db
        
        print_info "Ждем готовности БД..."
        sleep 10
        
        print_info "Восстанавливаем данные..."
        docker-compose exec -T db psql -U pkonline pkonline < "$backup_file"
        
        if [ $? -eq 0 ]; then
            print_success "Данные восстановлены успешно"
            print_info "Запускаем все сервисы..."
            docker-compose up -d
        else
            print_error "Ошибка при восстановлении данных"
            exit 1
        fi
    else
        print_info "Восстановление отменено"
    fi
}

# Безопасная пересборка
safe_rebuild() {
    print_info "Безопасная пересборка контейнеров..."
    
    print_info "1. Создаем бэкап..."
    create_backup
    
    print_info "2. Останавливаем контейнеры..."
    docker-compose down
    
    print_info "3. Пересобираем образы..."
    docker-compose build --no-cache
    
    print_info "4. Запускаем сервисы..."
    docker-compose up -d
    
    print_info "5. Проверяем статус..."
    sleep 5
    docker-compose ps
    
    print_success "Пересборка завершена успешно"
    print_info "Данные БД сохранены в volume pgdata"
}

# Просмотр информации о volumes
show_volumes() {
    print_info "Информация о volumes:"
    echo
    
    print_info "Список volumes:"
    docker volume ls | grep pkonline-bot || echo "Volumes не найдены"
    echo
    
    print_info "Детальная информация о pgdata:"
    docker volume inspect pkonline-bot_pgdata 2>/dev/null || print_warning "Volume pgdata не найден"
    echo
    
    print_info "Использование диска:"
    docker system df -v | grep -E "(pkonline-bot|pgdata)" || echo "Информация недоступна"
}

# Очистка старых бэкапов
cleanup_backups() {
    print_info "Очистка старых бэкапов..."
    
    if [ ! -d "backups" ]; then
        print_warning "Папка backups не существует"
        return
    fi
    
    # Удаляем бэкапы старше 30 дней
    find backups -name "backup_*.sql" -mtime +30 -delete
    
    print_success "Старые бэкапы удалены"
    print_info "Оставшиеся бэкапы:"
    ls -la backups/ 2>/dev/null || echo "Бэкапы не найдены"
}

# Проверка целостности БД
check_database() {
    print_info "Проверка целостности базы данных..."
    
    # Проверка подключения
    if docker-compose exec db pg_isready -U pkonline; then
        print_success "БД доступна"
    else
        print_error "БД недоступна"
        return 1
    fi
    
    # Проверка размера
    size=$(docker-compose exec -T db psql -U pkonline -t -c "SELECT pg_size_pretty(pg_database_size('pkonline'));" 2>/dev/null | tr -d ' ')
    if [ ! -z "$size" ]; then
        print_info "Размер БД: $size"
    fi
    
    # Проверка количества записей
    tables=$(docker-compose exec -T db psql -U pkonline -t -c "SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'public';" 2>/dev/null)
    if [ ! -z "$tables" ]; then
        print_info "Таблицы в БД:"
        echo "$tables" | sed 's/^/  - /'
    fi
}

# Показать справку
show_help() {
    echo "🐳 Скрипт управления данными PK Online Bot"
    echo
    echo "Использование: $0 <команда> [опции]"
    echo
    echo "Команды:"
    echo "  backup              - Создать бэкап БД"
    echo "  restore <file>      - Восстановить из бэкапа"
    echo "  rebuild             - Безопасная пересборка (с бэкапом)"
    echo "  volumes             - Показать информацию о volumes"
    echo "  cleanup             - Очистить старые бэкапы"
    echo "  check               - Проверить целостность БД"
    echo "  help                - Показать эту справку"
    echo
    echo "Примеры:"
    echo "  $0 backup"
    echo "  $0 restore backups/backup_20241201_120000.sql"
    echo "  $0 rebuild"
    echo
    echo "⚠️  ВАЖНО: Данные БД сохраняются в именованном volume pgdata"
    echo "   и НЕ удаляются при пересборке контейнеров"
}

# Основная логика
main() {
    check_docker_compose
    
    case "${1:-help}" in
        backup)
            create_backup
            ;;
        restore)
            restore_backup "$2"
            ;;
        rebuild)
            safe_rebuild
            ;;
        volumes)
            show_volumes
            ;;
        cleanup)
            cleanup_backups
            ;;
        check)
            check_database
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Запуск скрипта
main "$@" 