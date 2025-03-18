class UserManager:
    def __init__(self):
        self.users = {}

    def add_user(self, email: str):
        if email not in self.users:
            self.users[email] = {"topics": {}}

    def get_user(self, email: str):
        return self.users.get(email)

    def add_topic(self, email: str, topic_name: str):
        if email in self.users:
            self.users[email]["topics"][topic_name] = []
