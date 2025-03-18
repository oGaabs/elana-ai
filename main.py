from users.user_manager import UserManager
from topics.topic_manager import TopicManager
from agents.code_agent import CodeAgent

def main():
    user_manager = UserManager()
    topic_manager = TopicManager()
    code_agent = CodeAgent()

    # Adiciona um usuário
    user_email = "gabriel04.ok@gmail.com"
    user_manager.add_user(user_email)

    # Cria dois tópicos para o usuário
    topic_manager.create_topic(user_email, "Tópico 1")
    topic_manager.create_topic(user_email, "Tópico 2")

    # Interage com o primeiro tópico
    topic_name = "Tópico 1"
    user_message = "Qual é a capital da França?"
    topic_manager.add_message_to_topic(user_email, topic_name, user_message)
    
    # Agente responde ao primeiro tópico
    response = code_agent.run(user_message)
    topic_manager.add_message_to_topic(user_email, topic_name, response)

    # Exibe as mensagens do primeiro tópico
    print(f"Mensagens de {topic_name}:")
    for msg in topic_manager.get_topics(user_email)[topic_name]:
        print(msg)

    # Interage com o segundo tópico
    topic_name = "Tópico 2"
    user_message = "Escreva um código em Python para calcular a soma de 2 números."
    topic_manager.add_message_to_topic(user_email, topic_name, user_message)
    
    # Agente responde ao segundo tópico
    response = code_agent.run(user_message)
    topic_manager.add_message_to_topic(user_email, topic_name, response)

    # Exibe as mensagens do segundo tópico
    print(f"Mensagens de {topic_name}:")
    for msg in topic_manager.get_topics(user_email)[topic_name]:
        print(msg)

if __name__ == "__main__":
    main()
