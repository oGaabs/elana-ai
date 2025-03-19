import os
from agents.code_agent import CodeAgent
from users.user_manager import UserManager
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

console = Console()

def clear_screen():
    """Limpa a tela do terminal."""
    os.system("cls" if os.name == "nt" else "clear")

def display_banner():
    """Exibe um banner estilizado."""
    banner_text = Text("💻 Code Assistant CLI", style="bold cyan")
    console.print(Panel(banner_text, title="Welcome", expand=False, style="blue"))

def load_topic_history(user_manager, user_email, selected_topic):
    """
    Carrega e exibe o histórico do tópico selecionado.
    Retorna as interações para a construção do contexto.
    """
    clear_screen()
    display_banner()
    
    console.print(f"\n[bold cyan]Tópico: {selected_topic}[/bold cyan]")
    console.print("[bold yellow]Carregando histórico...[/bold yellow]\n")
    
    interactions = user_manager.get_interactions(user_email, selected_topic)
    if interactions:
        for entry in interactions:
            console.print(f"[bold yellow]➜ Pergunta:[/bold yellow] {entry['question']}")
            console.print(f"[bold green]✔ Resposta:[/bold green] {entry['response']}\n")
    else:
        console.print("[italic]Nenhuma interação anterior encontrada.[/italic]\n")
    return interactions

def build_topic_context(interactions):
    """
    Constrói uma string de contexto a partir das interações anteriores.
    Cada interação é concatenada para formar o contexto do tópico.
    """
    context = ""
    for entry in interactions:
        context += f"Pergunta: {entry['question']}\nResposta: {entry['response']}\n\n"
    return context

def main():
    clear_screen()
    display_banner()
    
    user_manager = UserManager()
    code_agent = CodeAgent()

    # Solicitar email do usuário
    user_email = Prompt.ask("[bold green]Digite seu e-mail[/bold green]")
    user_manager.add_user(user_email)

    while True:
        clear_screen()
        display_banner()

        # Selecionar ou criar um tópico
        console.print("\n[bold cyan]Escolha um tópico ou crie um novo:[/bold cyan]")
        topics = user_manager.get_topics(user_email)
        
        if topics:
            console.print("[bold yellow]Tópicos existentes:[/bold yellow]")
            for idx, topic in enumerate(topics, 1):
                console.print(f"[bold magenta]{idx}.[/bold magenta] {topic}")

        console.print(f"[bold green]{len(topics) + 1}.[/bold green] Criar novo tópico")
        console.print(f"[bold red]0.[/bold red] Sair")
        topic_choice = Prompt.ask(f"Escolha o tópico (0-{len(topics)+1})", choices=[str(i) for i in range(0, len(topics)+2)])

        if topic_choice == "0":
            console.print("[bold cyan]Fechando o programa... Até logo![/bold cyan]")
            break

        if int(topic_choice) == len(topics) + 1:
            selected_topic = Prompt.ask("Digite o nome do novo tópico")
            user_manager.add_topic(user_email, selected_topic)
        else:
            selected_topic = topics[int(topic_choice) - 1]

        while True:
            # Carregar histórico e construir contexto
            interactions = load_topic_history(user_manager, user_email, selected_topic)
            topic_context = build_topic_context(interactions)
            
            # Exibir menu de interação dentro do tópico
            console.print("\n[bold cyan]Selecione o tipo de pergunta:[/bold cyan]")
            console.print("[bold green]1.[/bold green] Pergunta sobre código")
            console.print("[bold green]2.[/bold green] Pergunta simples")
            console.print("[bold red]3.[/bold red] Voltar ao menu principal")
            console.print("[bold red]0.[/bold red] Sair")
            choice = Prompt.ask("\n[bold yellow]Digite a opção (0-3)[/bold yellow]", choices=["0", "1", "2", "3"])

            if choice == "0":
                console.print("[bold cyan]Fechando o programa... Até logo![/bold cyan]")
                return  # Fecha o programa imediatamente

            if choice == "3":
                break  # Volta ao menu principal para escolher outro tópico

            # Captura a nova pergunta
            if choice == "1":
                problem_statement = Prompt.ask("[bold yellow]Digite o problema relacionado a código[/bold yellow]")
            else:
                problem_statement = Prompt.ask("[bold yellow]Digite sua pergunta[/bold yellow]")
            
            # Se houver contexto, o anexa à nova pergunta
            if topic_context:
                new_prompt = f"{topic_context}\nUsuário: {problem_statement}"
            else:
                new_prompt = problem_statement
            
            # Processa a requisição com o agente
            if choice == "1":
                resposta = code_agent.handle_request(new_prompt, is_code_request=True)
            else:
                resposta = code_agent.handle_request(new_prompt, is_code_request=False)
            
            # Salva a nova interação
            user_manager.add_interaction(user_email, selected_topic, problem_statement, resposta)
            
            console.print(Panel(f"[bold cyan]Resposta:[/bold cyan]\n\n[italic green]{resposta}[/italic green]", title="Resposta", style="blue"))
            input("\nPressione ENTER para continuar perguntando...")

if __name__ == "__main__":
    main()
