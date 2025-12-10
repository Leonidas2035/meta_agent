import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from env_crypto import EnvCryptoError, load_decrypted_env


def _bootstrap_env() -> None:
    """
    Prefer encrypted env, fallback to plaintext .env.
    Does not override existing process env values.
    """
    decrypted_loaded = False
    if os.path.exists(".env.enc"):
        try:
            load_decrypted_env()
            decrypted_loaded = True
        except EnvCryptoError as exc:
            print(f"[WARN] Could not decrypt .env.enc: {exc}")

    # Only override values if nothing was loaded yet.
    load_dotenv(override=not decrypted_loaded)


class CodexClient:
    def __init__(self):
        _bootstrap_env()

        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not found")

        self.client = OpenAI(api_key=self.api_key)

        # more stable model for long prompts
        self.model = "gpt-4.1"   # or "gpt-5.1"

        # max chunk size to avoid 400 errors
        self.chunk_size = 12000

    def _chunk_prompt(self, text: str) -> List[str]:
        """Split large prompts into smaller chunks."""
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def send(self, prompt: str) -> str:
        """
        Sends prompt to Codex with safe chunking and stable formatting.
        Avoids invalid_request_error and ensures compatibility with chat models.
        """

        # Build message list with chunking
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an autonomous code-generation and refactoring agent "
                    "inside a Meta-Agent pipeline. Follow instructions precisely, "
                    "output only code or patches when required."
                )
            }
        ]

        for chunk in self._chunk_prompt(prompt):
            messages.append({"role": "user", "content": chunk})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"[ERROR] CodexClient failed: {str(e)}"
