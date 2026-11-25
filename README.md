# Whatsapp Bot

Bot de WhatsApp com RAG local: recebe mensagens pela Evolution API, consulta os documentos em `rag_files/` usando Chroma + Ollama e responde com um LLM da Groq. O histórico da conversa fica no Redis.

## O que o projeto faz

- Webhook FastAPI (`POST /webhook`) recebe os eventos `messages.upsert` da Evolution API.
- Mensagens são agrupadas por **debounce** (`message_buffer.py`) antes de serem respondidas.
- `chains.py` monta a cadeia: retriever (Chroma) + LLM (Groq) + histórico (Redis).
- A resposta volta para o WhatsApp por `sendText` da Evolution API.
- Mensagens duplicadas são descartadas pelo `key.id` no Redis.

## Pré-requisitos

- **Docker Desktop** rodando.
- **Ollama** instalado na máquina com o modelo de embedding:

  ```bash
  ollama pull nomic-embed-text
  ```

- Conta na **Groq** (chave de API).
- **Evolution API** (a chave `AUTHENTICATION_API_KEY` usada na instância).

## Como rodar

1. Clone o repositório e entre na pasta:

   ```bash
   git clone <url-do-repositorio>
   cd whatsapp_bot_ai
   ```

2. Copie o modelo de variáveis e preencha suas chaves:

   ```bash
   cp .env.example .env
   ```

   Edite `.env` e informe `GROQ_API_KEY` e `AUTHENTICATION_API_KEY`.

3. Suba os containers:

   ```bash
   docker compose up --build
   ```

   Ou em background:

   ```bash
   docker compose up --build -d
   docker compose logs -f bot
   ```

4. Conecte o WhatsApp na instância que você criou na Evolution API (o nome cadastrado em `EVOLUTION_INSTANCE_NAME` no `.env`):

   - Abra o manager da Evolution em `http://localhost:8080/manager`;
   - ou gere o QR pela API:

     ```bash
     curl -H "apikey: SUA_CHAVE" http://localhost:8080/instance/connect/SUA_INSTANCIA
     ```

   No celular: **WhatsApp → Dispositivos conectados → Adicionar dispositivo** e escaneie o QR.

5. Teste enviando uma mensagem de **outro número** (mensagens `fromMe` são ignoradas).

> No Linux, o container precisa acessar o Ollama da máquina. Se `host.docker.internal` não resolver, adicione em `docker-compose.yml`, dentro do serviço `bot`:
>
> ```yaml
> extra_hosts:
>   - "host.docker.internal:host-gateway"
> ```

## Comandos úteis

| Comando | O que faz |
|---|---|
| `docker compose ps` | Status dos containers |
| `docker compose logs -f bot` | Acompanhar o bot |
| `docker compose logs -f evolution-api` | Acompanhar a Evolution |
| `docker compose restart evolution-api` | Usar depois de recriar o bot (a Evolution guarda o IP antigo em cache) |
| `docker compose down` | Parar e remover os containers |
| `docker compose up -d` | Religar sem rebuild |

## Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Webhook FastAPI, filtros e dedupe |
| `message_buffer.py` | Debounce/agrupamento das mensagens e envio da resposta |
| `chains.py` | Cadeia RAG + histórico |
| `vectorstore.py` | Carrega PDF/TXT, divide em chunks e indexa no Chroma |
| `memory.py` | Histórico no Redis e dedupe por `key.id` |
| `prompts.py` | Prompt do sistema |
| `evolution_api.py` | Envio de mensagens via `sendText` |
| `config.py` | Leitura das variáveis de ambiente |
| `docker-compose.yml` | Serviços: bot, evolution-api, postgres, redis |
| `.env.example` | Modelo das variáveis de ambiente |

## Documentos (RAG)

Coloque arquivos `.pdf` ou `.txt` em `rag_files/` e reinicie o bot:

```bash
docker compose restart bot
```

Após indexar com sucesso, os arquivos são movidos para `rag_files/processed/`. Se trocar o modelo de embedding, apague `vectorstore_data/` antes de subir novamente.

## Variáveis de ambiente principais

| Variável | Descrição |
|---|---|
| `GROQ_API_KEY` | Chave da API Groq |
| `GROQ_MODEL_NAME` | Modelo usado (padrão do projeto: `qwen/qwen3.8-27b`) |
| `GROQ_MODEL_TEMPERATURE` | Temperatura do modelo |
| `AI_SYSTEM_PROMPT` | Instruções passadas ao LLM (use `{context}` para o RAG) |
| `EVOLUTION_API_URL` | URL interna da Evolution (`http://evolution-api:8080`) |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância |
| `AUTHENTICATION_API_KEY` | Chave da Evolution API |
| `CACHE_REDIS_URI` | URI do Redis (histórico e dedupe) |
| `EMBEDDING_MODEL` | Modelo do Ollama (`nomic-embed-text`) |
| `OLLAMA_BASE_URL` | Endereço do Ollama (`http://host.docker.internal:11434`) |
| `VECTOR_STORE_PATH` | Pasta de persistência do Chroma |
| `RAG_FILES_DIR` | Pasta dos documentos |
| `BUFFER_KEY_SUFIX`, `DEBOUNCE_SECONDS`, `BUFFER_TTL` | Configuração do agrupamento de mensagens |

`.env`, `venv`, `.venv`, `vectorstore_data`, `__pycache__` e `.DS_store` não são versionados (veja `.gitignore`). Nunca commite suas chaves.
