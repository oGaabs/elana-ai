import subprocess

class CodeExecutor:
    def execute(self, code: str) -> str:
        # Salva o código em um arquivo temporário
        with open("temp_code.py", "w") as file:
            file.write(code)
        # Executa o código e captura a saída
        result = subprocess.run(['python', 'temp_code.py'], capture_output=True, text=True)
        return result.stdout.strip()
