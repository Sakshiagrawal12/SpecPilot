import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq


load_dotenv()


# =========================================================
# LLM CONFIGURATION
# =========================================================

LLM_PROVIDER = os.getenv(
    "LLM_PROVIDER",
    "groq"
)

LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b"
)

LLM_TEMPERATURE = float(
    os.getenv(
        "LLM_TEMPERATURE",
        "0.2"
    )
)


# =========================================================
# GROQ PROVIDER
# =========================================================

class GroqProvider:

    def __init__(self):

        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:

            raise RuntimeError(
                "GROQ_API_KEY is not configured in the environment."
            )

        self.client = ChatGroq(

            model=LLM_MODEL,

            temperature=LLM_TEMPERATURE,

            reasoning_effort="low",

            api_key=api_key
        )

    def generate(
        self,
        prompt: str
    ) -> str:

        print("==========================================")
        print("LLM GENERATION")
        print("==========================================")

        print(
            "Provider:",
            "Groq"
        )

        print(
            "Model:",
            LLM_MODEL
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
                    "LLM returned an empty response."
                )

            print("==========================================")
            print("LLM RESPONSE RECEIVED")
            print("==========================================")

            print(
                "Response length:",
                len(content)
            )

            return content

        except Exception as e:

            print("==========================================")
            print("LLM ERROR")
            print("==========================================")

            print(
                str(e)
            )

            raise RuntimeError(
                f"LLM generation failed: {str(e)}"
            )


# =========================================================
# LLM FACTORY
# =========================================================

def create_llm():

    if LLM_PROVIDER.lower() == "groq":

        return GroqProvider()

    raise RuntimeError(
        f"Unsupported LLM provider: {LLM_PROVIDER}"
    )


# =========================================================
# APPLICATION LLM
# =========================================================

llm = create_llm()