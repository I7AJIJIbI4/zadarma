#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_bot_admin.py - Скрипт для додавання функцій адміна в bot.py
"""

import os
import shutil
from datetime import datetime

def backup_bot_file():
    """Створює резервну копію bot.py"""
    bot_file = '/home/gomoncli/zadarma/bot.py'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'/home/gomoncli/zadarma/bot.py.backup.{timestamp}'
    
    try:
        shutil.copy2(bot_file, backup_file)
        print(f"✅ Резервна копія створена: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Помилка створення резервної копії: {e}")
        return False

def fix_syntax_error():
    """Виправляє синтаксичну помилку в bot.py"""
    bot_file = '/home/gomoncli/zadarma/bot.py'
    
    try:
        with open(bot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Виправляємо синтаксичну помилку
        content = content.replace("if **name** == '__main__':", "if __name__ == '__main__':")
        
        with open(bot_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("✅ Синтаксична помилка виправлена")
        return True
        
    except Exception as e:
        print(f"❌ Помилка виправлення синтаксису: {e}")
        return False

def add_admin_functions():
    """Додає функції адміна в bot.py"""
    bot_file = '/home/gomoncli/zadarma/bot.py'
    
    try:
        with open(bot_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Перевіряємо чи функції вже додані
        if 'def help_command(' in content and 'def stats_detail_command(' in content:
            print("✅ Функції адміна вже додані")
            return True
        
        # Нові функції для додавання
        admin_functions = '''
def help_command(bot, update):
    """Команда /help - показує всі доступні команди"""
    user_id = update.effective_user.id
    logger.info(f"❓ /help викликано користувачем: {user_id}")
    
    try:
        if user_id == ADMIN_USER_ID:
            # Розширена довідка для адміна
            help_message = (
                "🤖 **ДОВІДКА ДЛЯ АДМІНІСТРАТОРА**\\n\\n"
                
                "👥 **КОРИСТУВАЦЬКІ КОМАНДИ:**\\n"
                "🚪 /hvirtka - Відкрити хвіртку\\n"
                "🏠 /vorota - Відкрити ворота\\n"
                "📞 /call - Телефон лікаря Вікторії\\n"
                "🗺️ /map - Карта розташування\\n"
                "📋 /scheme - Схема проходу в ЖК\\n"
                "🧪 /test - Тест роботи бота\\n"
                "📊 /status - Статус користувача\\n\\n"
                
                "👑 **АДМІНІСТРАТИВНІ КОМАНДИ:**\\n"
                "📈 /stats - Загальна статистика дзвінків\\n"
                "📊 /stats_detail - Детальна статистика\\n"
                "🔄 /sync - Ручна синхронізація клієнтів\\n"
                "🔄 /restart - Перезапуск бота\\n"
                "❓ /help - Ця довідка\\n\\n"
                
                "🔧 **СИСТЕМНІ ФУНКЦІЇ:**\\n"
                "• Автоматичні сповіщення про проблеми\\n"
                "• Моніторинг статусів дзвінків\\n"
                "• Статистика успішності системи\\n"
                "• Контроль авторизації користувачів\\n\\n"
                
                "📱 **КОНТАКТИ ПІДТРИМКИ:**\\n"
                "+380733103110"
            )
        elif is_authenticated(user_id):
            # Довідка для авторизованих користувачів
            help_message = (
                "🤖 **ДОВІДКА ПО КОМАНДАХ**\\n\\n"
                
                "🔓 **ДОСТУПНІ ДІЇ:**\\n"
                "🚪 /hvirtka - Відкрити хвіртку для проходу\\n"
                "🏠 /vorota - Відкрити ворота для авто\\n"
                "📞 /call - Зателефонувати лікарю Вікторії\\n"
                "🗺️ /map - Подивитись розташування на мапі\\n"
                "📋 /scheme - Схема розташування в ЖК Графський\\n\\n"
                
                "ℹ️ **ІНФОРМАЦІЙНІ:**\\n"
                "🧪 /test - Перевірити роботу бота\\n"
                "📊 /status - Ваш статус в системі\\n"
                "❓ /help - Ця довідка\\n\\n"
                
                "💡 **ПІДКАЗКИ:**\\n"
                "• Використовуйте меню ☰ для швидкого доступу\\n"
                "• При проблемах з відкриттям спробуйте ще раз\\n"
                "• Для підтримки дзвоніть: +380733103110"
            )
        else:
            # Довідка для неавторизованих користувачів
            help_message = (
                "🤖 **ДОВІДКА**\\n\\n"
                
                "❌ **Ви не авторизовані в системі**\\n\\n"
                
                "📱 **Для авторизації:**\\n"
                "1. Натисніть /start\\n"
                "2. Поділіться номером телефону\\n"
                "3. Дочекайтеся підтвердження доступу\\n\\n"
                
                "🔓 **ДОСТУПНІ КОМАНДИ:**\\n"
                "📞 /call - Зателефонувати лікарю\\n"
                "🗺️ /map - Подивитись розташування\\n"
                "📋 /scheme - Схема проходу\\n"
                "❓ /help - Ця довідка\\n\\n"
                
                "📞 **ДЛЯ РЕЄСТРАЦІЇ ЗВЕРНІТЬСЯ:**\\n"
                "+380733103110\\n"
                "Instagram: @dr.gomon"
            )
        
        bot.send_message(
            chat_id=update.message.chat_id,
            text=help_message,
            parse_mode='Markdown'
        )
        logger.info(f"❓ Довідка відправлена користувачу {user_id}")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в help_command: {e}")
        bot.send_message(
            chat_id=update.message.chat_id,
            text="❌ **Помилка отримання довідки**",
            parse_mode='Markdown'
        )

def stats_detail_command(bot, update):
    """Детальна статистика для адміна"""
    user_id = update.effective_user.id
    logger.info(f"📊 /stats_detail викликано користувачем: {user_id}")
    
    if user_id != ADMIN_USER_ID:
        bot.send_message(
            chat_id=update.message.chat_id,
            text="❌ Ця команда доступна тільки адміністратору"
        )
        return
    
    try:
        # Імпортуємо функції статистики
        try:
            from zadarma_api_webhook import get_call_statistics
        except ImportError:
            # Fallback якщо функції ще не додані
            bot.send_message(
                chat_id=update.message.chat_id,
                text="⚠️ Функції статистики ще не встановлені. Використовуйте /stats для базової статистики."
            )
            return
        
        # Отримуємо статистику
        stats_today = get_call_statistics(1)
        stats_week = get_call_statistics(7)
        
        message = "📊 **ДЕТАЛЬНА СТАТИСТИКА СИСТЕМИ**\\n\\n"
        
        # За сьогодні
        message += "📅 **СЬОГОДНІ:**\\n"
        if stats_today and stats_today['total_calls'] > 0:
            message += f"• Дзвінків: {stats_today['total_calls']}\\n"
            message += f"• Успішність: {stats_today['success_rate']}%\\n"
            message += f"• Хвіртка: {stats_today['by_action']['hvirtka']}\\n"
            message += f"• Ворота: {stats_today['by_action']['vorota']}\\n"
        else:
            message += "• Дзвінків сьогодні не було\\n"
        
        message += "\\n"
        
        # За тиждень
        message += "📅 **ЗА ТИЖДЕНЬ:**\\n"
        if stats_week and stats_week['total_calls'] > 0:
            message += f"• Всього дзвінків: {stats_week['total_calls']}\\n"
            message += f"• Успішність: {stats_week['success_rate']}%\\n"
            message += f"• Хвіртка: {stats_week['by_action']['hvirtka']}\\n"
            message += f"• Ворота: {stats_week['by_action']['vorota']}\\n\\n"
            
            # Розподіл по статусах
            message += "📋 **Розподіл по статусах:**\\n"
            status_names = {
                'success': '✅ Успішно',
                'busy': '📞 Зайнято',
                'no_answer': '📵 Не відповідає',
                'answered': '⚠️ Прийнято (помилка)',
                'failed': '❌ Невдача',
                'timeout': '⏰ Таймаут',
                'pending': '🔄 В очікуванні'
            }
            
            for status, count in sorted(stats_week['by_status'].items(), key=lambda x: x[1], reverse=True):
                name = status_names.get(status, status)
                percentage = round((count / stats_week['total_calls']) * 100, 1)
                message += f"• {name}: {count} ({percentage}%)\\n"
        else:
            message += "• Дзвінків за тиждень не було\\n"
        
        # Попередження про проблеми
        if stats_week:
            problem_statuses = ['answered', 'failed', 'timeout']
            problem_count = sum(stats_week['by_status'].get(status, 0) for status in problem_statuses)
            
            if problem_count > 0:
                problem_percentage = round((problem_count / stats_week['total_calls']) * 100, 1)
                message += f"\\n⚠️ **УВАГА**: {problem_count} дзвінків ({problem_percentage}%) мали проблеми!"
                
                if stats_week['by_status'].get('answered', 0) > 0:
                    message += f"\\n🚨 Дзвінків ПРИЙНЯТО: {stats_week['by_status']['answered']} - ПЕРЕВІРТЕ НАЛАШТУВАННЯ!"
        
        bot.send_message(
            chat_id=update.message.chat_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"📊 Детальна статистика відправлена адміну")
        
    except Exception as e:
        logger.exception(f"❌ Помилка в stats_detail_command: {e}")
        bot.send_message(
            chat_id=update.message.chat_id,
            text="❌ Помилка отримання детальної статистики"
        )

def send_admin_alert(message, priority="normal"):
    """Відправляє сповіщення адміну"""
    try:
        priority_emoji = {
            'low': 'ℹ️',
            'normal': '📢',
            'high': '⚠️',
            'critical': '🚨'
        }
        
        emoji = priority_emoji.get(priority, '📢')
        formatted_message = f"{emoji} **СИСТЕМНЕ СПОВІЩЕННЯ** ({priority.upper()})\\n\\n{message}"
        
        import time
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        formatted_message += f"\\n\\n🕐 Час: {timestamp}"
        
        from zadarma_api_webhook import send_telegram_message
        success = send_telegram_message(ADMIN_USER_ID, formatted_message)
        
        if success:
            logger.info(f"📤 Сповіщення адміна відправлено: {priority} - {message[:50]}...")
        else:
            logger.error(f"❌ Не вдалося відправити сповіщення адміна")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Помилка відправки сповіщення адміна: {e}")
        return False

'''
        
        # Знаходимо місце для вставки (перед функцією main)
        main_function_pos = content.find('def main():')
        if main_function_pos == -1:
            print("❌ Не знайдено функцію main()")
            return False
        
        # Вставляємо нові функції
        new_content = content[:main_function_pos] + admin_functions + '\n' + content[main_function_pos:]
        
        # Додаємо обробники команд у функцію main
        # Знаходимо місце додавання обробників
        handlers_pos = new_content.find('dp.add_handler(CommandHandler("stats", handle_admin_stats_command))')
        if handlers_pos != -1:
            # Додаємо після існуючого stats обробника
            insert_pos = new_content.find('\n', handlers_pos) + 1
            new_handlers = '''    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("stats_detail", stats_detail_command))
'''
            new_content = new_content[:insert_pos] + new_handlers + new_content[insert_pos:]
        
        # Записуємо файл
        with open(bot_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("✅ Функції адміна додані в bot.py")
        return True
        
    except Exception as e:
        print(f"❌ Помилка додавання функцій адміна: {e}")
        return False

def add_statistics_functions():
    """Додає функції статистики в zadarma_api_webhook.py"""
    webhook_file = '/home/gomoncli/zadarma/zadarma_api_webhook.py'
    
    try:
        with open(webhook_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Перевіряємо чи функції вже додані
        if 'def get_call_statistics(' in content:
            print("✅ Функції статистики вже додані")
            return True
        
        # Функції статистики
        stats_functions = '''

def get_call_statistics(days=7):
    """Отримує статистику дзвінків за вказаний період"""
    try:
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 3600)
        
        cursor = call_tracker.conn.cursor()
        
        # Загальна статистика
        cursor.execute("""
            SELECT 
                status,
                action_type,
                COUNT(*) as count
            FROM call_tracking 
            WHERE timestamp > ?
            GROUP BY status, action_type
            ORDER BY count DESC
        """, (cutoff_time,))
        
        stats = {
            'total_calls': 0,
            'success_rate': 0,
            'by_status': {},
            'by_action': {'hvirtka': 0, 'vorota': 0},
            'by_status_detailed': [],
            'period_days': days
        }
        
        for row in cursor.fetchall():
            status, action_type, count = row
            stats['total_calls'] += count
            
            if status not in stats['by_status']:
                stats['by_status'][status] = 0
            stats['by_status'][status] += count
            
            if action_type in stats['by_action']:
                stats['by_action'][action_type] += count
            
            stats['by_status_detailed'].append({
                'status': status,
                'action_type': action_type,
                'count': count
            })
        
        # Розрахунок успішності
        success_count = stats['by_status'].get('success', 0)
        if stats['total_calls'] > 0:
            stats['success_rate'] = round((success_count / stats['total_calls']) * 100, 1)
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Помилка отримання статистики: {e}")
        return None

def format_statistics_message(stats):
    """Форматує статистику для повідомлення"""
    if not stats:
        return "❌ Не вдалося отримати статистику"
    
    message = f"📊 **СТАТИСТИКА** ({stats['period_days']} днів)\\n\\n"
    message += f"📈 Всього дзвінків: {stats['total_calls']}\\n"
    message += f"✅ Успішність: {stats['success_rate']}%\\n\\n"
    
    if stats['total_calls'] > 0:
        message += "🎯 **По типах:**\\n"
        message += f"🚪 Хвіртка: {stats['by_action']['hvirtka']}\\n"
        message += f"🏠 Ворота: {stats['by_action']['vorota']}\\n"
    
    return message
'''
        
        # Додаємо в кінець файлу
        new_content = content + stats_functions
        
        # Записуємо файл
        with open(webhook_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("✅ Функції статистики додані в zadarma_api_webhook.py")
        return True
        
    except Exception as e:
        print(f"❌ Помилка додавання функцій статистики: {e}")
        return False

def main():
    """Головна функція виправлення bot.py"""
    print("🔧 ВИПРАВЛЕННЯ БОТА ТА ДОДАВАННЯ ФУНКЦІЙ АДМІНА")
    print("=" * 50)
    
    # 1. Створюємо резервну копію
    print("1️⃣ Створення резервної копії...")
    if not backup_bot_file():
        print("❌ Не вдалося створити резервну копію. Зупиняємо.")
        return
    
    # 2. Виправляємо синтаксичну помилку
    print("2️⃣ Виправлення синтаксичної помилки...")
    if not fix_syntax_error():
        print("❌ Не вдалося виправити синтаксичну помилку.")
        return
    
    # 3. Додаємо функції адміна
    print("3️⃣ Додавання функцій адміна...")
    if not add_admin_functions():
        print("❌ Не вдалося додати функції адміна.")
        return
    
    # 4. Додаємо функції статистики
    print("4️⃣ Додавання функцій статистики...")
    if not add_statistics_functions():
        print("❌ Не вдалося додати функції статистики.")
        return
    
    print("\n✅ ВСЕ ГОТОВО!")
    print("\n📋 Додані команди:")
    print("• /help - Довідка по командах")
    print("• /stats_detail - Детальна статистика для адміна")
    print("\n🔄 Перезапустіть бота для застосування змін:")
    print("sudo systemctl restart telegram-bot")

if __name__ == "__main__":
    main()