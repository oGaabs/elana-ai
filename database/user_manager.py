from database.db_manager import DBManager

class UserManager:
    def __init__(self, db_manager=None):
        self.db_manager = db_manager if db_manager else DBManager()

    def add_user(self, email):
        """Adiciona um usuário novo, se não existir."""
        user_id = self.db_manager.get_user_id(email)
        if user_id is None:
            self.db_manager.add_user(email)

    def get_user_id(self, email):
        """Retorna o ID do usuário baseado no email."""
        return self.db_manager.get_user_id(email)

    def add_topic(self, user_email, topic_name):
        """Adiciona um tópico ao usuário."""
        user_id = self.get_user_id(user_email)
        if user_id is not None:
            self.db_manager.add_topic(user_id, topic_name)

    def get_topics(self, user_email):
        """Recupera os tópicos de um usuário."""
        user_id = self.get_user_id(user_email)
        return self.db_manager.get_topics(user_id) if user_id else []

    def add_interaction(self, user_email, topic_name, question, response):
        """Adiciona uma interação de código ao tópico."""
        user_id = self.get_user_id(user_email)
        if user_id:
            topics = self.db_manager.get_topics(user_id)
            if topic_name in topics:
                self.db_manager.add_interaction(topic_name, question, response)

    def get_interactions(self, user_email, topic_name):
        """Recupera as interações de um tópico."""
        user_id = self.get_user_id(user_email)
        if user_id:
            topics = self.db_manager.get_topics(user_id)
            return self.db_manager.get_interactions(topic_name) if topic_name in topics else []

        return []