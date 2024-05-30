# 🚀 Chat assistant for Linux, A step towards LLM OS. 

Llama-index + OpenAI Agent + Streamlit

You can ask it questions or give it tasks like running commands and fixing problems with a simple interface. Thanks to the OpenAI framework, which helps it understand and plan what to do next.

Ask it things like:
1. Why aren't pods running in the xyz namespace?
2. Which service is using most amount of CPU?
3. How much space does the <path> folder take up?

When user asks a question, it forms a step-by-step plan to solve it, generates the necessary bash commands, executes them and looks at the output to decide whether to run more commands or to summarize the output.

[Blog post which explains the code](https://www.linkedin.com/pulse/bash-mate-your-linux-command-assistant-yeshwanth-sadum-slvdc/?trackingId=3%2BZU0%2F%2BDSpO%2FShVKJ7PxeA%3D%3D)

-------------------------------
Steps:
1. Install requirements
`pip install streamlit llama-index openai python-dotenv`

2. Go to the folder where "bash_assistant.py" is present and run
`streamlit run bash_assistant.py`
