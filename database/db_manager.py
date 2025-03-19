import sqlite3

class DBManager:
    def __init__(self, db_name="app_data.db"):
        self.db_name = db_name
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        """Cria as tabelas necessárias no banco de dados."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic_name TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            question TEXT NOT NULL,
            response TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
        """)
        self.connection.commit()

    def add_user(self, email):
        """Adiciona um novo usuário ao banco de dados."""
        self.cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
        self.connection.commit()

    def get_user_id(self, email):
        """Recupera o ID de um usuário a partir do seu email."""
        self.cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        user_id = self.cursor.fetchone()
        return user_id[0] if user_id else None

    def add_topic(self, user_id, topic_name):
        """Adiciona um novo tópico para o usuário."""
        self.cursor.execute("INSERT INTO topics (user_id, topic_name) VALUES (?, ?)", (user_id, topic_name))
        self.connection.commit()

    def get_topics(self, user_id):
        """Recupera todos os tópicos de um usuário."""
        self.cursor.execute("SELECT topic_name FROM topics WHERE user_id = ?", (user_id,))
        topics = self.cursor.fetchall()
        return [topic[0] for topic in topics]

    def add_interaction(self, topic_id, question, response):
        """Adiciona uma nova interação de código ao tópico."""
        self.cursor.execute("INSERT INTO interactions (topic_id, question, response) VALUES (?, ?, ?)",
                            (topic_id, question, response))
        self.connection.commit()

    def get_interactions(self, topic_id):
        """Recupera todas as interações de um tópico."""
        self.cursor.execute("SELECT question, response FROM interactions WHERE topic_id = ?", (topic_id,))
        interactions = self.cursor.fetchall()
        return [{"question": question, "response": response} for question, response in interactions]

    def close(self):
        """Fecha a conexão com o banco de dados."""
        self.connection.close()