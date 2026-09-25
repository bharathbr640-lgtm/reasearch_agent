from openai import OpenAI

class OllamaLLM:
    def __init__(self, api_key, base_url="https://ollama.com"):
        self.client = OpenAI(
            api_key=api_key,
            base_url=f"{base_url}/v1" # Ollama's OpenAI-compatible endpoint
        )

    def chat(self, messages, model="gpt-oss:120b"):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    def generate_follow_ups(self, user_idea, history):
        messages = [
            {"role": "system", "content": "You are a research agent. Your goal is to gather deep context about a project idea. Do NOT provide a solution. Instead, ask 3-5 targeted follow-up questions to understand the target audience, core problem, and desired features. If you have enough information to define a clear problem statement, start your response with 'READY'."},
            {"role": "user", "content": f"Idea: {user_idea}"}
        ]
        messages.extend(history)
        return self.chat(messages)

    def synthesize_problem(self, history):
        messages = [
            {"role": "system", "content": "Synthesize the previous conversation into a concise, professional problem statement that describes what the user wants to build, why, and for whom. End with a request for confirmation."},
        ]
        messages.extend(history)
        return self.chat(messages)

    def analyze_research(self, problem_statement, research_data):
        messages = [
            {"role": "system", "content": f"You are an expert market researcher. Analyze the following web research data against the confirmed problem statement: {problem_statement}. Identify if the project exists, what approaches have been taken, and where the gap for innovation lies. Provide a structured report in Markdown."},
            {"role": "user", "content": f"Research Data: {research_data}"}
        ]
        return self.chat(messages)
