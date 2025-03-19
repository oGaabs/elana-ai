import requests
from execution.code_executor import CodeExecutor
from reasoning.thinker import Thinker

class CodeAgent:
    def __init__(self, api_url="http://localhost:11434/api/generate", model="codellama"):
        self.model = model
        self.api_url = api_url
        self.executor = CodeExecutor()
        self.thinker = Thinker()

    def generate_response(self, prompt: str) -> str:
        # Envia uma requisição POST para a API com o prompt do usuário
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(self.api_url, json=payload)
        
        if response.status_code == 200:
            return response.json().get("response", "Erro ao obter resposta")
        else:
            return f"Erro: {response.status_code}"

    def execute_code(self, prompt: str) -> str:
        # Para perguntas sobre código, gera o código, raciocina e executa
        reasoning = self.think(prompt)
        code = self.generate_response(prompt)
        execution_result = self.executor.execute(code)
        return f"Raciocínio:\n{reasoning}\n\nCódigo Gerado:\n{code}\n\nResultado da Execução:\n{execution_result}"

    def think(self, problem: str) -> str:
        # Raciocínio passo a passo sobre o problema
        return self.thinker.reason(problem)

    def handle_request(self, prompt: str, is_code_request: bool = False) -> str:
        if is_code_request:
            return self.execute_code(prompt)
        else:
            return self.generate_response(prompt)
