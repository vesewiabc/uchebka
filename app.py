import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class UserSupportSystem:
    def __init__(self, db_name: str = "support_system.db"):
        self.db_name = db_name
    
    def create_ticket(self, title: str, description: str, email: str, user_name: str, priority: str = "medium") -> int:
        """Создание нового тикета пользователем"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Проверяем существование столбца user_name
        cursor.execute("PRAGMA table_info(tickets)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_name' in columns:
            cursor.execute('''
                INSERT INTO tickets (title, description, priority, email, user_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, priority, email, user_name))
        else:
            cursor.execute('''
                INSERT INTO tickets (title, description, priority, email)
                VALUES (?, ?, ?, ?)
            ''', (title, description, priority, email))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_ticket_for_user(self, ticket_id: int, email: str) -> Optional[Dict]:
        """Получение информации о тикете для пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tickets WHERE id = ? AND email = ?', (ticket_id, email))
        ticket = cursor.fetchone()
        
        if ticket:
            columns = [description[0] for description in cursor.description]
            ticket_dict = dict(zip(columns, ticket))
            
            # Добавляем user_name, если его нет в результате
            if 'user_name' not in ticket_dict:
                ticket_dict['user_name'] = 'Пользователь'
            
            # Получаем только НЕ внутренние ответы
            cursor.execute('''
                SELECT * FROM ticket_responses 
                WHERE ticket_id = ? AND is_internal = 0 
                ORDER BY created_at
            ''', (ticket_id,))
            
            responses = cursor.fetchall()
            response_columns = [description[0] for description in cursor.description]
            ticket_dict['responses'] = [dict(zip(response_columns, response)) for response in responses]
        
        conn.close()
        return ticket_dict if ticket else None
    
    def get_user_tickets(self, email: str) -> List[Dict]:
        """Получение всех тикетов пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, status, priority, created_at, updated_at 
            FROM tickets 
            WHERE email = ? 
            ORDER BY created_at DESC
        ''', (email,))
        
        tickets = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        return [dict(zip(columns, ticket)) for ticket in tickets]
    
    def add_user_response(self, ticket_id: int, response_text: str, email: str):
        """Добавление ответа пользователя к тикету"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Проверяем, что тикет принадлежит пользователю
        cursor.execute('SELECT id FROM tickets WHERE id = ? AND email = ?', (ticket_id, email))
        if not cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute('''
            INSERT INTO ticket_responses (ticket_id, response_text, responded_by, is_internal)
            VALUES (?, ?, ?, 0)
        ''', (ticket_id, response_text, "Пользователь"))
        
        # Обновляем время изменения тикета
        cursor.execute('''
            UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (ticket_id,))
        
        conn.commit()
        conn.close()
        return True

def safe_get(dictionary, key, default='Не указано'):
    """Безопасное получение значения из словаря"""
    return dictionary.get(key, default)

def display_ticket_status(ticket):
    """Красивое отображение статуса тикета"""
    status_icons = {
        'open': '🔴',
        'in-progress': '🟡', 
        'closed': '🟢'
    }
    priority_icons = {
        'low': '⚪',
        'medium': '🟡',
        'high': '🔴'
    }
    
    status = safe_get(ticket, 'status', 'open')
    priority = safe_get(ticket, 'priority', 'medium')
    
    icon = status_icons.get(status, '⚫')
    priority_icon = priority_icons.get(priority, '⚫')
    
    return f"{icon} {status.upper()} {priority_icon} {priority.upper()}"

def main_user_version():
    """Главная функция для пользовательской версии"""
    system = UserSupportSystem()
    
    print("🐛" + "="*50)
    print("       СИСТЕМА ТЕХНИЧЕСКОЙ ПОДДЕРЖКИ")
    print("="*50)
    
    # Запрос email пользователя
    user_email = input("Введите ваш email: ").strip()
    user_name = input("Введите ваше имя: ").strip()
    
    if not user_email or not user_name:
        print("❌ Email и имя обязательны для работы с системой!")
        return
    
    print(f"\n👋 Добро пожаловать, {user_name}!")
    
    while True:
        print("\n" + "━"*50)
        print("🎯 ГЛАВНОЕ МЕНЮ")
        print("━"*50)
        print("1. 📋 Создать новый запрос в поддержку")
        print("2. 📂 Мои текущие запросы")
        print("3. 🔍 Просмотреть конкретный запрос")
        print("4. 💬 Добавить комментарий к запросу")
        print("0. ❌ Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            print("\n📝 СОЗДАНИЕ НОВОГО ЗАПРОСА")
            print("━"*30)
            
            title = input("Краткое описание проблемы: ")
            description = input("Подробное описание проблемы:\n")
            
            print("\n🚨 Уровень важности:")
            print("⚪ Низкий - не срочно")
            print("🟡 Средний - стандартная проблема") 
            print("🔴 Высокий - критическая проблема")
            
            priority = input("Выберите важность (low/medium/high): ").lower()
            if priority not in ['low', 'medium', 'high']:
                priority = 'medium'
            
            ticket_id = system.create_ticket(title, description, user_email, user_name, priority)
            
            print(f"\n✅ Запрос успешно создан!")
            print(f"📌 Номер вашего запроса: #{ticket_id}")
            print("💬 Мы свяжемся с вами в ближайшее время.")
        
        elif choice == "2":
            print("\n📂 ВАШИ ТЕКУЩИЕ ЗАПРОСЫ")
            print("━"*30)
            
            tickets = system.get_user_tickets(user_email)
            
            if not tickets:
                print("📭 У вас пока нет созданных запросов.")
                continue
            
            print(f"📊 Найдено запросов: {len(tickets)}\n")
            
            for ticket in tickets:
                status_display = display_ticket_status(ticket)
                print(f"#{ticket['id']} - {safe_get(ticket, 'title')}")
                print(f"   {status_display}")
                print(f"   📅 Создан: {safe_get(ticket, 'created_at')[:16]}")
                print(f"   🔄 Обновлен: {safe_get(ticket, 'updated_at')[:16]}")
                print()
        
        elif choice == "3":
            try:
                ticket_id = int(input("\n🔍 Введите номер запроса: "))
                ticket = system.get_ticket_for_user(ticket_id, user_email)
                
                if ticket:
                    print(f"\n" + "═"*60)
                    print(f"📄 ЗАПРОС #{ticket['id']}")
                    print("═"*60)
                    print(f"📌 Тема: {safe_get(ticket, 'title')}")
                    print(f"📝 Описание: {safe_get(ticket, 'description')}")
                    print(f"📊 Статус: {display_ticket_status(ticket)}")
                    print(f"👤 Создан: {safe_get(ticket, 'user_name', user_name)}")
                    print(f"📅 Дата создания: {safe_get(ticket, 'created_at')[:16]}")
                    print(f"🔄 Последнее обновление: {safe_get(ticket, 'updated_at')[:16]}")
                    
                    if ticket.get('responses'):
                        print(f"\n💬 ОТВЕТЫ СЛУЖБЫ ПОДДЕРЖКИ ({len(ticket['responses'])}):")
                        print("─" * 50)
                        for response in ticket['responses']:
                            print(f"👨‍💼 {safe_get(response, 'responded_by')} ({safe_get(response, 'created_at')[:16]}):")
                            print(f"   {safe_get(response, 'response_text')}")
                            print()
                    else:
                        print(f"\n📭 Ответов от поддержки пока нет.")
                        print("💤 Наш специалист рассмотрит ваш запрос в ближайшее время.")
                    
                    print("═"*60)
                else:
                    print("❌ Запрос не найден или у вас нет доступа к этому запросу.")
            
            except ValueError:
                print("❌ Неверный формат номера запроса!")
        
        elif choice == "4":
            try:
                ticket_id = int(input("\n💬 Введите номер запроса: "))
                response_text = input("Ваш комментарий: ")
                
                if system.add_user_response(ticket_id, response_text, user_email):
                    print("✅ Комментарий успешно добавлен!")
                else:
                    print("❌ Запрос не найден или у вас нет доступа к этому запросу.")
            
            except ValueError:
                print("❌ Неверный формат номера запроса!")
        
        elif choice == "0":
            print(f"\n👋 До свидания, {user_name}! Спасибо за обращение!")
            break
        
        else:
            print("❌ Неверный выбор! Попробуйте еще раз.")

if __name__ == "__main__":
    main_user_version()