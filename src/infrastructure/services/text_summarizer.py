import os
from anthropic import Anthropic

class TextSummarizer:
    def __init__(self):
        self.client = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    def summarize(self, text: str) -> str:
        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": f"Resume el siguiente texto de manera concisa y clara, manteniendo los puntos más importantes:\n\n{text}"
                }]
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Error al resumir el texto: {str(e)}")