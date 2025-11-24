import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class SupportTicketSystem:
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
                email TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                response_text TEXT NOT NULL,
                responded_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tickets (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_ticket(self, title: str, description: str, email: str, priority: str = "medium") -> int:
        """Создание нового тикета"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tickets (title, description, priority, email)
            VALUES (?, ?, ?, ?)
        ''', (title, description, priority, email))
        
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
    
    def add_response(self, ticket_id: int, response_text: str, responded_by: str):
        """Добавление ответа к тикету"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ticket_responses (ticket_id, response_text, responded_by)
            VALUES (?, ?, ?)
        ''', (ticket_id, response_text, responded_by))
        
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
        return [dict(zip(columns, ticket)) for ticket in tickets]
    
    def get_tickets_by_email(self, email: str) -> List[Dict]:
        """Получение тикетов по email"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tickets WHERE email = ? ORDER BY created_at DESC', (email,))
        tickets = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        conn.close()
        return [dict(zip(columns, ticket)) for ticket in tickets]

def main_db_version():
    """Главная функция для версии с базой данных"""
    system = SupportTicketSystem()
    
    while True:
        print("\n=== Система технической поддержки ===")
        print("1. Создать новый тикет")
        print("2. Просмотреть все тикеты")
        print("3. Найти тикет по ID")
        print("4. Обновить статус тикета")
        print("5. Добавить ответ к тикету")
        print("6. Найти тикеты по email")
        print("0. Выход")
        
        choice = input("\nВыберите действие: ")
        
        if choice == "1":
            title = input("Заголовок проблемы: ")
            description = input("Описание проблемы: ")
            email = input("Ваш email: ")
            priority = input("Приоритет (low/medium/high, по умолчанию medium): ") or "medium"
            
            ticket_id = system.create_ticket(title, description, email, priority)
            print(f"Тикет создан! ID: {ticket_id}")
        
        elif choice == "2":
            status_filter = input("Фильтр по статусу (open/in-progress/closed, Enter для всех): ")
            tickets = system.get_all_tickets(status_filter if status_filter else None)
            
            print(f"\nНайдено тикетов: {len(tickets)}")
            for ticket in tickets:
                print(f"ID: {ticket['id']} | {ticket['title']} | Статус: {ticket['status']} | Создан: {ticket['created_at']}")
        
        elif choice == "3":
            try:
                ticket_id = int(input("Введите ID тикета: "))
                ticket = system.get_ticket(ticket_id)
                
                if ticket:
                    print(f"\n=== Тикет #{ticket['id']} ===")
                    print(f"Заголовок: {ticket['title']}")
                    print(f"Описание: {ticket['description']}")
                    print(f"Статус: {ticket['status']}")
                    print(f"Приоритет: {ticket['priority']}")
                    print(f"Email: {ticket['email']}")
                    print(f"Назначен: {ticket['assigned_to'] or 'Не назначен'}")
                    print(f"Создан: {ticket['created_at']}")
                    
                    if ticket['responses']:
                        print("\nОтветы:")
                        for response in ticket['responses']:
                            print(f"  {response['created_at']} - {response['responded_by']}: {response['response_text']}")
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
                response_text = input("Текст ответа: ")
                responded_by = input("Ваше имя: ")
                
                system.add_response(ticket_id, response_text, responded_by)
                print("Ответ добавлен!")
            
            except ValueError:
                print("Неверный формат ID!")
        
        elif choice == "6":
            email = input("Введите email: ")
            tickets = system.get_tickets_by_email(email)
            
            print(f"\nНайдено тикетов для {email}: {len(tickets)}")
            for ticket in tickets:
                print(f"ID: {ticket['id']} | {ticket['title']} | Статус: {ticket['status']}")
        
        elif choice == "0":
            print("Выход из системы...")
            break
        
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main_db_version()