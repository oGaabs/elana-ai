import os
import requests
import git
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.progress import Progress

# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Default Ollama API endpoint

# Model variations
INSTRUCT_MODEL = "codellama:7b-instruct"  # For natural language reasoning and explanations

# Initialize Rich Console
console = Console()

# Set up logging
log_filename = f"logs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

class CodeAgent:
    def __init__(self, project_root: str):
        """Initialize the agent with the project root directory, resetting model context."""
        self.project_root = Path(project_root).resolve()
        self.git_repo = self._init_git()
        self.context = self._build_project_context()
        console.print("[cyan]✓ Model context reset and initialized with fresh project state[/cyan]")
        logger.info("CodeAgent initialized with project root: %s and model context reset", self.project_root)

    def _init_git(self) -> Optional[git.Repo]:
        """Initialize Git repository if available."""
        try:
            repo = git.Repo(self.project_root)
            console.print("[green]✓ Git repository initialized[/green]")
            logger.info("Git repository initialized successfully")
            return repo
        except git.InvalidGitRepositoryError:
            console.print("[yellow]⚠ No Git repository found. Changes won't be committed.[/yellow]")
            logger.warning("No Git repository found")
            return None

    def _build_project_context(self) -> str:
        """Build context by reading readme.md and scanning all files."""
        context = []
        readme_path = self.project_root / "readme.md"
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                context.append(f"README.md:\n{f.read()}\n")
            logger.info("Included readme.md in context")

        for root, _, files in os.walk(self.project_root):
            if ".git" in root or "__pycache__" in root or "venv" in root:
                continue
            for file in files:
                if file.endswith((".py", ".md", ".txt", ".json")):
                    file_path = Path(root) / file
                    with open(file_path, "r", encoding="utf-8") as f:
                        context.append(f"{file_path.relative_to(self.project_root)}: content='\n{f.read()}'\n")
                    logger.info("Added file to context: %s", file_path)
        console.print(f"[cyan]✓ Built project context with {len(context)} files[/cyan]")
        logger.info("Project context built with %d files", len(context))
        return "\n".join(context)

    def _call_ollama(self, prompt: str, model: str) -> Dict[str, List[str]]:
        """Call Ollama API with the specified Code Llama model."""
        logger.info("Calling Ollama API with model %s and prompt: %s", model, prompt[:100] + "..." if len(prompt) > 100 else prompt)
        with Progress(transient=True) as progress:
            task = progress.add_task(f"[cyan]Processing with {model}...", total=100)
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            progress.update(task, advance=100)

        result = response.json()
        full_text = result.get("response", "")
        logger.info("Ollama response received from %s: %s", model, full_text[:100] + "..." if len(full_text) > 100 else full_text)
        
        thinking = []
        text = []
        lines = full_text.split("\n")
        in_thinking = False
        for line in lines:
            if line.strip().startswith("Thinking:"):
                in_thinking = True
                thinking.append(line.replace("Thinking:", "").strip())
            elif line.strip().startswith("Final:"):
                in_thinking = False
                text.append(line.replace("Final:", "").strip())
            elif in_thinking:
                thinking.append(line.strip())
            else:
                text.append(line.strip())
        
        return {"thinking": thinking, "text": text}

    def _parse_tool_calls(self, response_text: List[str]) -> List[Dict[str, str]]:
        """Parse response for tool calls (CREATE, MODIFY, DELETE)."""
        tool_calls = []
        current_action = None
        current_path = None
        current_content = []

        for line in response_text:
            line = line.strip()
            if "CREATE:" in line:
                if current_action:
                    tool_calls.append({"action": current_action, "path": current_path, "content": "\n".join(current_content)})
                current_action = "create"
                current_path = line.split(":", 1)[1].strip()
                current_content = []
            elif "MODIFY:" in line:
                if current_action:
                    tool_calls.append({"action": current_action, "path": current_path, "content": "\n".join(current_content)})
                current_action = "modify"
                current_path = line.split(":", 1)[1].strip()
                current_content = []
            elif "DELETE:" in line:
                if current_action:
                    tool_calls.append({"action": current_action, "path": current_path, "content": "\n".join(current_content)})
                current_action = "delete"
                current_path = line.split(":", 1)[1].strip()
                current_content = []
            elif current_action and line:
                current_content.append(line)

        if current_action:
            tool_calls.append({"action": current_action, "path": current_path, "content": "\n".join(current_content)})
        logger.info("Parsed %d tool calls", len(tool_calls))
        return tool_calls

    def _execute_tool_calls(self, tool_calls: List[Dict[str, str]]):
        """Execute file operations based on tool calls."""
        console.print(Panel("Executing Planned Changes", style="bold magenta"))
        for call in tool_calls:
            file_path = self.project_root / call["path"]
            action = call["action"]
            content = call["content"].strip().replace("```", "")
            if action == "create":
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                console.print(f"[green]✓ Created: {file_path}[/green]")
                console.print(Syntax(call["content"], "python", theme="monokai"))
                logger.info("Created file: %s with content: %s", file_path, call["content"][:50] + "..." if len(call["content"]) > 50 else call["content"])
            elif action == "modify":
                if file_path.exists():
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    console.print(f"[blue]✓ Modified: {file_path}[/blue]")
                    console.print(Syntax(call["content"], "python", theme="monokai"))
                    logger.info("Modified file: %s with content: %s", file_path, call["content"][:50] + "..." if len(call["content"]) > 50 else call["content"])
                else:
                    console.print(f"[red]✗ File not found for modification: {file_path}[/red]")
                    logger.error("File not found for modification: %s", file_path)
            elif action == "delete":
                if file_path.exists():
                    file_path.unlink()
                    console.print(f"[yellow]✓ Deleted: {file_path}[/yellow]")
                    logger.info("Deleted file: %s", file_path)
                else:
                    console.print(f"[red]✗ File not found for deletion: {file_path}[/red]")
                    logger.error("File not found for deletion: %s", file_path)

    def _commit_changes(self, message: str):
        """Commit changes to Git if available."""
        if self.git_repo:
            self.git_repo.git.add(all=True)
            self.git_repo.index.commit(message)
            console.print(Panel(f"✓ Committed changes: {message}", style="green"))
            logger.info("Committed changes with message: %s", message)

    def process_prompt(self, prompt: str):
        """Process user prompt using advanced prompt engineering and appropriate Code Llama models."""
        console.print(Panel(f"Processing Prompt: {prompt}", title="Code Agent", style="bold cyan"))
        logger.info("Processing prompt: %s", prompt)

        # Few-Shot Prompting Examples for Instruct and Code Models
        few_shot_examples = """
        Example 1 (Instruct Model):
        Prompt: "Create a function to reverse a string in utils.py"
        Response:
        Thinking: Let's break this into steps:
        1. Check if utils.py exists - it doesn't in this context
        2. Create utils.py with the reverse function
        Final:
        CREATE: utils.py
        def reverse_string(s):
            return s[::-1]

        Example 2 (Code Model):
        Prompt: "Add logging to main.py"
        Response:
        Thinking: Let's plan:
        1. Assume main.py exists or create it if it doesn't
        2. Add logging import and configuration
        3. Modify the main function to include logging
        Final:
        MODIFY: main.py
        import logging
        logging.basicConfig(level=logging.INFO)
        def main():
            logging.info("Starting main")
            print("Hello")
        """

        # Step 1: Reflection and Chain-of-Thought (CoT) for Subtasks
        # Use Instruct model for natural language reasoning and planning
        console.print(Text("Step 1: Reflecting and Planning", style="bold underline"))
        reflection_prompt = f"""
        Given the project context:
        {self.context}

        User Request: "{prompt}"

        You are an expert software enginner that writes simple, concise code and explanations.
        Reflect on the task and use Chain-of-Thought and reasoning to break it into subtasks:
        1. Analyze the prompt and project context.
        2. Identify required changes (files to create, modify, or delete).
        3. Plan the implementation step-by-step.
        Provide your reasoning with "Thinking:" prefix and final plan with "Final:" prefix.

        So the output have to be like this:
        - A brief summary of your thought process prefixed with "Thinking:".
        - A concise final plan of subtasks prefixed with "Final:".
        """
        MAX_ATTEMPTS = 3
        reflection = None
        subtasks = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                reflection = self._call_ollama(reflection_prompt, INSTRUCT_MODEL)
                console.print(Panel("\n".join(reflection["thinking"]), title="Reflection", style="cyan"))
                subtasks = "\n".join(reflection["text"])
                console.print(Panel(subtasks, title="Planned Subtasks", style="green"))
                logger.info("Reflection completed with subtasks: %s", subtasks)
                break  # Sai do loop se não houver erro
            except Exception as e:
                logger.error("Attempt %d failed: %s", attempt, e)
                if attempt == MAX_ATTEMPTS:
                    logger.critical("Max attempts reached. Failing gracefully.")
                    console.print(Panel("Failed to reflect and plan subtasks. Reflecting to a new prompt.", style="bold red"))
            
        # Step 2: Automatic Reasoning and Tool-use (ART) with Tool Calling
        # Use Python model for Python-specific code generation
        console.print(Text("Step 2: Generating Solution", style="bold underline"))
        solution_prompt = f"""
        Given the project context:
        {self.context}
        Given the prompt: "{prompt}"
        Given the subtasks, generated by the Code Agent AI:
        {subtasks}
        Given the Code Agent AI reasoning and planning:
        {reflection["thinking"]}

        You are an expert software engineer that writes simple, concise code and explanations.
        Generate a complete solution with:
        1. Step-by-step reasoning about how to implement the changes
        2. The actual code implementation, with the code blocks (```) and final code, not a example of code.
        3. Any necessary imports or dependencies

        Provide your reasoning with "Thinking:" prefix and solution with "Final:" prefix.
        """

        MAX_ATTEMPTS = 3
        solution = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                solution = self._call_ollama(solution_prompt, INSTRUCT_MODEL)
                console.print(Panel("\n".join(solution["thinking"]), title="Solution Reasoning", style="cyan"))
                console.print(Panel("\n".join(solution["text"]), title="Generated Solution", style="green"))
                logger.info("Solution generated successfully")
                break
            except Exception as e:
                logger.error("Attempt %d failed: %s", attempt, e)
                if attempt == MAX_ATTEMPTS:
                    logger.critical("Max attempts reached. Failing gracefully.")
                    console.print(Panel("Failed to generate solution. Reflecting to a new prompt.", style="bold red"))
                    return

        # Convert solution to tool calls
        console.print(Text("Step 3: Converting to Tool Calls", style="bold underline"))
        tool_prompt = f"""
        Given this solution:
        {solution["text"]}

        Convert the solution into tool calls using Automatic Reasoning and Tool-use (ART).
        Use only these commands:
        CREATE: <path> - Create a new file
        MODIFY: <path> - Modify an existing file
        DELETE: <path> - Delete a file

        {few_shot_examples}

        Instructions:
        1. Analyze the solution and determine required file changes
        2. Convert each change into appropriate tool calls
        3. Format output exactly as:
           CREATE: path/to/file
           <content>
           MODIFY: path/to/file
           <content>
           DELETE: path/to/file
        4. No explanations or code blocks outside tool calls
        5. Ensure paths and content are complete

        Provide reasoning with "Thinking:" prefix and tool calls with "Final:" prefix.
        """

        execution = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                execution = self._call_ollama(tool_prompt, INSTRUCT_MODEL)
                console.print(Panel("\n".join(execution["thinking"]), title="Tool Call Reasoning", style="cyan"))
                console.print(Panel("\n".join(execution["text"]), title="Tool Calls", style="magenta"))
                logger.info("Tool calls generated: %s", "\n".join(execution["text"]))
                
                # Execute Tool Calls
                tool_calls = self._parse_tool_calls(execution["text"])
                self._execute_tool_calls(tool_calls)
                break
            except Exception as e:
                logger.error("Attempt %d failed: %s", attempt, e)
                if attempt == MAX_ATTEMPTS:
                    logger.critical("Max attempts reached. Failing gracefully.")
                    console.print(Panel("Failed to convert to tool calls. Reflecting to a new prompt.", style="bold red"))
            


        # Step 4: Reflexion - Review and Adjust
        # Use Instruct model for code review and natural language reflection
        console.print(Text("Step 3: Reviewing Changes", style="bold underline"))
        reflexion_prompt = f"""
        Review the changes made:
        {execution['text']}

        You are an expert programmer that writes simple, concise code and explanations.
        Reflect on:
        1. Did the changes fully address the prompt "{prompt}"?
        2. Are there any improvements or errors to fix? (e.g., bugs, edge cases, or missing imports)
        3. If adjustments are needed, provide new tool calls.
        Provide reasoning with "Thinking:" prefix and adjustments with "Final:" prefix using the same tool call format:
        CREATE: path/to/file
        <content>
        MODIFY: path/to/file
        <content>
        DELETE: path/to/file
        """
        MAX_ATTEMPTS = 3
        reflexion = None
        adjustment_calls = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                reflexion = self._call_ollama(reflexion_prompt, INSTRUCT_MODEL)
                console.print(Panel("\n".join(reflexion["thinking"]), title="Reflexion", style="cyan"))
                
                if reflexion["text"]:
                    console.print(Panel("\n".join(reflexion["text"]), title="Adjustments", style="yellow"))
                    adjustment_calls = self._parse_tool_calls(reflexion["text"])
                    self._execute_tool_calls(adjustment_calls)
                    logger.info("Adjustments applied: %s", "\n".join(reflexion["text"]))
                else:
                    console.print("[green]✓ No adjustments needed[/green]")
                    logger.info("No adjustments needed")
                
                break  # Sai do loop se não houver erro
            except Exception as e:
                logger.error("Attempt %d failed: %s", attempt, e)
                if attempt == MAX_ATTEMPTS:
                    logger.critical("Max attempts reached. Failing gracefully.")
                    console.print(Panel("Failed to Review and new Tool Calling if needed. Reflecting to a new prompt.", style="bold red"))
            
        # Step 5: Commit Changes
        console.print(Text("Step 4: Finalizing", style="bold underline"))
        self._commit_changes(f"Implemented: {prompt}")
        console.print(Panel("Task Completed Successfully!", style="bold green"))
        logger.info("Task completed successfully for prompt: %s", prompt)

def main():
    project_root = "D:\\Coding\\elana-ai\\tetris_game"  # Adjust as needed
    agent = CodeAgent(project_root)
    user_prompt = "With the readme.md, create a copy of game Tetris in Python and html file"
    agent.process_prompt(user_prompt)

if __name__ == "__main__":
    main()
    exit(0)