#!/bin/bash
# git_sync.sh - Безпечна синхронізація з GitHub

echo "🔄 СИНХРОНІЗАЦІЯ З GITHUB РЕПОЗИТОРІЄМ"
echo "======================================"

# Функція логування
log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

# Перевіряємо поточний статус
log "📋 Перевіряємо поточний статус Git..."
git status

echo
log "📥 Завантажуємо останні зміни з GitHub..."
git fetch origin

echo
log "🔍 Перевіряємо різниці між локальними та віддаленими змінами..."
echo "=== REMOTE COMMITS ==="
git log HEAD..origin/main --oneline
echo
echo "=== LOCAL COMMITS ==="
git log origin/main..HEAD --oneline

echo
echo "💡 ВАРІАНТИ СИНХРОНІЗАЦІЇ:"
echo "1. git pull --rebase  (рекомендовано - застосовує ваші зміни поверх віддалених)"
echo "2. git pull --merge   (створює merge commit)"
echo "3. git reset --hard origin/main  (⚠️ ВТРАТИТЬ локальні зміни)"
echo

read -p "Оберіть варіант (1/2/3) або 'q' для виходу: " -n 1 -r
echo

case $REPLY in
    1)
        log "🔄 Виконуємо rebase..."
        git pull --rebase origin main
        if [[ $? -eq 0 ]]; then
            log "✅ Rebase успішний"
        else
            log "❌ Конфлікти при rebase"
            echo "Вирішіть конфлікти та виконайте:"
            echo "git add ."
            echo "git rebase --continue"
            exit 1
        fi
        ;;
    2)
        log "🔄 Виконуємо merge..."
        git pull origin main
        if [[ $? -eq 0 ]]; then
            log "✅ Merge успішний"
        else
            log "❌ Конфлікти при merge"
            echo "Вирішіть конфлікти та виконайте:"
            echo "git add ."
            echo "git commit"
            exit 1
        fi
        ;;
    3)
        log "⚠️ УВАГА: Це видалить всі локальні зміни!"
        read -p "Ви впевнені? (yes/N): " confirm
        if [[ "$confirm" == "yes" ]]; then
            git reset --hard origin/main
            log "✅ Скинуто до віддаленої версії"
        else
            log "❌ Скасовано"
            exit 1
        fi
        ;;
    q|Q)
        log "❌ Вихід без змін"
        exit 0
        ;;
    *)
        log "❌ Невірний вибір"
        exit 1
        ;;
esac

echo
log "📤 Пушимо зміни на GitHub..."
git push origin main

if [[ $? -eq 0 ]]; then
    log "🎉 Синхронізація завершена успішно!"
else
    log "❌ Помилка при push"
    exit 1
fi

# Показуємо фінальний статус
echo
log "📊 Фінальний статус:"
git status
git log --oneline -5
