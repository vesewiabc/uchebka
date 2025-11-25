import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class AdminSupportSystem:
    def __init__(self, db_name: str = "support_system.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_to TEXT,
                email TEXT,
                user_name TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                response_text TEXT NOT NULL,
                responded_by TEXT,
                is_internal BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_ticket(self, title: str, description: str, email: str, user_name: str, priority: str = "medium") -> int:
        """Создание нового тикета"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tickets (title, description, priority, email, user_name)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, description, priority, email, user_name))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """Получение информации о тикете"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
        ticket = cursor.fetchone()
        
        if ticket:
            columns = [description[0] for description in cursor.description]
            ticket_dict = dict(zip(columns, ticket))
            
            # Получаем ответы на тикет
            cursor.execute('SELECT * FROM ticket_responses WHERE ticket_id = ? ORDER BY created_at', (ticket_id,))
            responses = cursor.fetchall()
            response_columns = [description[0] for description in cursor.description]
            ticket_dict['responses'] = [dict(zip(response_columns, response)) for response in responses]
        
        conn.close()
        return ticket_dict if ticket else None
    
    def update_ticket_status(self, ticket_id: int, status: str, assigned_to: str = None):
        """Обновление статуса тикета"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if assigned_to:
            cursor.execute('''
                UPDATE tickets 
                SET status = ?, assigned_to = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, assigned_to, ticket_id))
        else:
            cursor.execute('''
                UPDATE tickets 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, ticket_id))
        
        conn.commit()
        conn.close()
    
    def add_response(self, ticket_id: int, response_text: str, responded_by: str, is_internal: bool = False):
        """Добавление ответа к тикету"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ticket_responses (ticket_id, response_text, responded_by, is_internal)
            VALUES (?, ?, ?, ?)
        ''', (ticket_id, response_text, responded_by, is_internal))
        
        # Обновляем время изменения тикета
        cursor.execute('''
            UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (ticket_id,))
        
        conn.commit()
        conn.close()
    
    def get_all_tickets(self, status: str = None) -> List[Dict]:
        """Получение всех тикетов (с фильтром по статусу)"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if status:
            cursor.execute('SELECT * FROM tickets WHERE status = ? ORDER BY created_at DESC', (status,))
        else:
            cursor.execute('SELECT * FROM tickets ORDER BY created_at DESC')
        
        tickets = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Безопасное преобразование в словари
        result = []
        for ticket in tickets:
            ticket_dict = dict(zip(columns, ticket))
            # Добавляем поле user_name, если его нет
            if 'user_name' not in ticket_dict:
                ticket_dict['user_name'] = 'Не указано'
            result.append(ticket_dict)
        
        return result
    
    def get_tickets_statistics(self) -> Dict:
        """Получение статистики по тикетам"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT status, COUNT(*) FROM tickets GROUP BY status')
        status_stats = dict(cursor.fetchall())
        
        cursor.execute('SELECT priority, COUNT(*) FROM tickets GROUP BY priority')
        priority_stats = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM tickets WHERE date(created_at) = date("now")')
        today_tickets = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'status_stats': status_stats,
            'priority_stats': priority_stats,
            'today_tickets': today_tickets,
            'total_tickets': sum(status_stats.values())
        }
    
    def search_tickets(self, query: str) -> List[Dict]:
        """Поиск тикетов по заголовку и описанию"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM tickets 
            WHERE title LIKE ? OR description LIKE ? OR email LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        tickets = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        
        # Безопасное преобразование в словари
        result = []
        for ticket in tickets:
            ticket_dict = dict(zip(columns, ticket))
            # Добавляем поле user_name, если его нет
            if 'user_name' not in ticket_dict:
                ticket_dict['user_name'] = 'Не указано'
            result.append(ticket_dict)
        
        return result

def safe_get(dictionary, key, default='Не указано'):
    """Безопасное получение значения из словаря"""
    return dictionary.get(key, default)

def main_admin_version():
    """Главная функция для административной версии"""
    system = AdminSupportSystem()
    
    while True:
        print("\n" + "="*50)
        print("=== АДМИНИСТРАТИВНАЯ СИСТЕМА ТЕХНИЧЕСКОЙ ПОДДЕРЖКИ ===")
        print("="*50)
        print("1. Просмотреть все тикеты")
        print("2. Поиск тикетов")
        print("3. Просмотреть тикет по ID")
        print("4. Обновить статус тикета")
        print("5. Добавить ответ к тикету")
        print("6. Статистика системы")
        print("7. Добавить внутренний комментарий")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            status_filter = input("Фильтр по статусу (open/in-progress/closed, Enter для всех): ")
            tickets = system.get_all_tickets(status_filter if status_filter else None)
            
            print(f"\nНайдено тикетов: {len(tickets)}")
            print("-" * 80)
            for ticket in tickets:
                print(f"ID: {ticket['id']:3} | Статус: {safe_get(ticket, 'status'):12} | Приоритет: {safe_get(ticket, 'priority'):6}")
                print(f"Заголовок: {safe_get(ticket, 'title')}")
                print(f"Пользователь: {safe_get(ticket, 'user_name')} ({safe_get(ticket, 'email')})")
                print(f"Создан: {safe_get(ticket, 'created_at')}")
                print("-" * 80)
        
        elif choice == "2":
            query = input("Введите поисковый запрос: ")
            tickets = system.search_tickets(query)
            
            print(f"\nРезультаты поиска ('{query}'): {len(tickets)} тикетов")
            for ticket in tickets:
                print(f"ID: {ticket['id']} | {safe_get(ticket, 'title')} | Статус: {safe_get(ticket, 'status')} | Email: {safe_get(ticket, 'email')}")
        
        elif choice == "3":
            try:
                ticket_id = int(input("Введите ID тикета: "))
                ticket = system.get_ticket(ticket_id)
                
                if ticket:
                    print(f"\n" + "="*60)
                    print(f"ТИКЕТ #{ticket['id']}")
                    print("="*60)
                    print(f"Заголовок: {safe_get(ticket, 'title')}")
                    print(f"Описание: {safe_get(ticket, 'description')}")
                    print(f"Статус: {safe_get(ticket, 'status')}")
                    print(f"Приоритет: {safe_get(ticket, 'priority')}")
                    print(f"Пользователь: {safe_get(ticket, 'user_name')} ({safe_get(ticket, 'email')})")
                    print(f"Назначен: {safe_get(ticket, 'assigned_to', 'Не назначен')}")
                    print(f"Создан: {safe_get(ticket, 'created_at')}")
                    print(f"Обновлен: {safe_get(ticket, 'updated_at')}")
                    
                    if ticket.get('responses'):
                        print("\nИСТОРИЯ ОБРАЩЕНИЙ:")
                        for response in ticket['responses']:
                            marker = "[ВНУТРЕННИЙ] " if response.get('is_internal') else ""
                            print(f"  {safe_get(response, 'created_at')} - {marker}{safe_get(response, 'responded_by')}:")
                            print(f"    {safe_get(response, 'response_text')}")
                    else:
                        print("\nОтветов пока нет.")
                else:
                    print("Тикет не найден!")
            
            except ValueError:
                print("Неверный формат ID!")
        
        elif choice == "4":
            try:
                ticket_id = int(input("Введите ID тикета: "))
                status = input("Новый статус (open/in-progress/closed): ")
                assigned_to = input("Назначить на (Enter чтобы пропустить): ") or None
                
                system.update_ticket_status(ticket_id, status, assigned_to)
                print("Статус обновлен!")
            
            except ValueError:
                print("Неверный формат ID!")
        
        elif choice == "5":
            try:
                ticket_id = int(input("Введите ID тикета: "))
                response_text = input("Текст ответа для пользователя: ")
                responded_by = input("Ваше имя: ")
                
                system.add_response(ticket_id, response_text, responded_by)
                print("Ответ добавлен!")
            
            except ValueError:
                print("Неверный формат ID!")
        
        elif choice == "6":
            stats = system.get_tickets_statistics()
            print(f"\n=== СТАТИСТИКА СИСТЕМЫ ===")
            print(f"Всего тикетов: {stats['total_tickets']}")
            print(f"Тикетов за сегодня: {stats['today_tickets']}")
            print("\nПо статусам:")
            for status, count in stats['status_stats'].items():
                print(f"  {status}: {count}")
            print("\nПо приоритетам:")
            for priority, count in stats['priority_stats'].items():
                print(f"  {priority}: {count}")
        
        elif choice == "7":
            try:
                ticket_id = int(input("Введите ID тикета: "))
                response_text = input("Внутренний комментарий: ")
                responded_by = input("Ваше имя: ")
                
                system.add_response(ticket_id, response_text, responded_by, is_internal=True)
                print("Внутренний комментарий добавлен!")
            
            except ValueError:
                print("Неверный формат ID!")
        
        elif choice == "0":
            print("Выход из административной системы...")
            break
        
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main_admin_version()