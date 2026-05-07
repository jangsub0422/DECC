import subprocess
import re
from .base import HostConnector

class LocalCliConnector(HostConnector):
    def __init__(self, command: str = "ollama", base_args: list[str] | None = None):
        self.command = command
        self.base_args = base_args or ["run", "qwen2.5-coder:0.5b"]

    @property
    def connector_name(self) -> str:
        arg_str = " ".join(self.base_args)
        return f"LocalCliConnector({self.command} {arg_str})"

    def cultivate(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                [self.command, *self.base_args, prompt],
                capture_output=True, text=True, encoding="utf-8", timeout=120
            )
            
            raw_output = result.stdout
            
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            cleaned_output = ansi_escape.sub('', raw_output)
            
            lines = cleaned_output.split('\n')
            in_code_block = False
            code_lines = []
            
            for line in lines:
                clean_line = line.strip()
                if clean_line.startswith('```python') or clean_line.startswith('``` python'):
                    in_code_block = True
                    continue
                elif clean_line.startswith('```') and in_code_block:
                    in_code_block = False
                    break
                    
                if in_code_block:
                    code_lines.append(line)
                    
            if not code_lines:
                final_code = cleaned_output.strip()
            else:
                final_code = '\n'.join(code_lines).strip()
                
            return final_code

        except FileNotFoundError:
            raise RuntimeError(f"[CONNECTOR ERROR] {self.command} not found.")
        except subprocess.TimeoutExpired:
            raise RuntimeError("[CONNECTOR ERROR] Cultivation timeout.")