class TopicManager:
    def __init__(self):
        self.topics = {}

    def create_topic(self, user_email: str, topic_name: str):
        """Cria um novo tópico para um usuário."""
        self.topics[user_email] = self.topics.get(user_email, {})
        self.topics[user_email][topic_name] = []

    def get_topics(self, user_email: str):
        """Obtém os tópicos de um usuário."""
        return self.topics.get(user_email, {})

    def add_message_to_topic(self, user_email: str, topic_name: str, message: str):
        """Adiciona uma mensagem a um tópico de um usuário."""
        if user_email in self.topics and topic_name in self.topics[user_email]:
            self.topics[user_email][topic_name].append(message)
