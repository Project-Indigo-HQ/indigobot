# Chatbot for Social Services

**Portland State University | Computer Science capstone project | FW24: Sept 2024 - March 2025**

This project repo contains a branch for local usage, a branch tailored for the web UI, and a 
branch with code for Read the Docs. The main branch is for our API version on the code.

## Install

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

```bash
python3 -m indigobot
```

## API Keys

This program requires API key environment variables for:

- OpenAI (**required** for LLM engine)
- Google Places (Places lookup tool for supplementary info)

## Local Docker Usage

```bash
docker build -t example-name .
docker run -it -e OPENAI_API_KEY="your-api-key" example-name
```

### [Read the Docs](https://indigobot.readthedocs.io/en/latest/)

**Thanks to Professors Bruce Irvin and Wu-chang Feng**

Team Indigo is:
Melissa Shanks, JunFan Lin, Grace Trieu, Sam Nelson, Avesta Mirashrafi, Karl Rosenberg, Kyle Klein
