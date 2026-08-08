from src.Domain.Interfaces.Llm.LlmInterface import LlmResponse, LlmInterface, LlmConfig
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

class GeminiLlm(LlmInterface):
    def __init__(self, config: LlmConfig, system_prompt: str):
        super().__init__(config, system_prompt)
        
        # Carrega o .env da raiz do projeto
        src_dir = Path(__file__).resolve().parents[2]
        project_root = src_dir.parent
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY não encontrada nas variáveis de ambiente!")
        self.client = genai.Client(api_key=api_key)

    async def process(self, message: str) -> LlmResponse:
        if not message:
            raise ValueError("Mensagem vazia não é permitida")
        try:
            full_prompt = f"{self.system_prompt}\n\n{message}"

            # Chamada compatível com a SDK
            response = await asyncio.to_thread(
                lambda: self.client.models.generate_content(
                    model=self.config.model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        max_output_tokens=self.config.max_completion_tokens
                    )
                )
            )

            content = (
                    response.text
                    or (response.candidates[0].content.parts[0].text if response.candidates else "")
                    ).strip()

            return LlmResponse(
                message=content
            )

        except Exception as e:
            self.logger.error(f"Erro no GeminiAgent: {str(e)}")
            raise RuntimeError(f"Erro ao processar mensagem com Gemini: {str(e)}")
