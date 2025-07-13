# dummy_llm
A simple full-stack project that control user entitlement in LLM. The web app is built with Flask and the LLM model is provided by Ollama.
# How to run
## Installation
`pip install -r requirements.txt`
## Check run on local
`ollama serve`
## Run the app
`python app.py`
## Prompt example:
login with username: root/moshu/no_user:

Give moshu's age and height based on local knowledge.

Typical result that you should receive:

Based on the provided context: {"moshu": {"height": 177, "weight": 70}} {"moshu": {"height": 177, "weight": 70}} {"moshu": {"height": 177, "weight": 70}} According to local knowledge, Moshu's age is not specified. However, based on the provided context, his height is: 177
Response time: 454.00 seconds