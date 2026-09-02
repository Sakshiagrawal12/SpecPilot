import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


class GroqClient:

    def __init__(self):

        self.model = "openai/gpt-oss-20b"

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GROQ_API_KEY is not configured in the environment."
            )

        self.client = ChatGroq(

            model=self.model,

            temperature=0.2,

            reasoning_effort="low",

            api_key=api_key
        )


    def generate(
        self,
        prompt: str
    ) -> str:

        print("==========================================")
        print("SENDING PROMPT TO GROQ")
        print("==========================================")

        print(
            "Model:",
            self.model
        )

        print(
            "Prompt length:",
            len(prompt)
        )

        try:

            response = self.client.invoke(
                prompt
            )

            content = response.content

            if not content:

                raise RuntimeError(
                    "Groq returned an empty response."
                )

            print("==========================================")
            print("GROQ RESPONSE RECEIVED")
            print("==========================================")

            print(
                "Response length:",
                len(content)
            )

            return content

        except Exception as e:

            print("==========================================")
            print("GROQ ERROR")
            print("==========================================")

            print(
                str(e)
            )

            raise RuntimeError(
                f"Groq generation failed: {str(e)}"
            )


llm = GroqClient()