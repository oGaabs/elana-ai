import requests

class CodeAgent:
    def __init__(self, model="codellama"):
        self.model = model
        self.url = "http://localhost:11434/api/generate"  # Ollama server endpoint

    def run(self, query: str) -> str:
        """Send the query to Ollama and get the model's response."""
        payload = {
            "model": self.model,
            "prompt": query,
            "stream": False
        }
        response = requests.post(self.url, json=payload)
        
        # Check if the response is valid
        if response.status_code == 200:
            return response.json().get("response", "Erro ao obter resposta")
        else:
            return f"Error: {response.status_code} - {response.text}"

# Exemplo de uso
if __name__ == "__main__":
    agent = CodeAgent()
    resposta = agent.run("Escreva um código Python que imprime 'Olá, mundo!'")
    print(resposta)
