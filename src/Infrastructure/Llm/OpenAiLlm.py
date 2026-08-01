from src.Domain.Interfaces.Llm.LlmInterface import LlmInterface, LlmResponse, LlmConfig
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


class OpenAILlm(LlmInterface):
    def __init__(self, config: LlmConfig, system_prompt: str):
        super().__init__(config, system_prompt)
        
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            # Carrega o .env da raiz do projeto somente se necessário
            src_dir = Path(__file__).resolve().parents[2]
            project_root = src_dir.parent
            env_path = project_root / ".env"

            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=False)
                api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente!")

        self.client = OpenAI(api_key=api_key)

    async def process(self, message: str) -> LlmResponse:
        if not message:
            raise ValueError("Mensagem vazia não é permitida")

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.config.model,
                max_completion_tokens=self.config.max_completion_tokens,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message},
                ],
            )

            content = response.choices[0].message.content.strip()

            return LlmResponse(message=content)

        except OpenAIError as exc:
            self.logger.error(f"Erro no OpenAIAgent: {str(exc)}", exc_info=True)
            raise
        except Exception as exc:
            self.logger.error(f"Erro inesperado no OpenAIAgent: {str(exc)}", exc_info=True)
            raise RuntimeError("Erro ao processar mensagem com OpenAI") from exc
