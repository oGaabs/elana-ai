class Thinker:
    def reason(self, problem: str) -> str:
        # Implementação de raciocínio passo a passo
        steps = f"Analisando o problema: {problem}\n"
        steps += "1. Compreender os requisitos.\n"
        steps += "2. Dividir o problema em sub-tarefas.\n"
        steps += "3. Desenvolver soluções para cada sub-tarefa.\n"
        steps += "4. Integrar as soluções para formar a resposta final.\n"
        return steps
