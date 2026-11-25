from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import AI_SYSTEM_PROMPT


qa_prompt = ChatPromptTemplate.from_messages([
    ('system', AI_SYSTEM_PROMPT),
    MessagesPlaceholder('chat_history'),
    ('human', '{input}'),
])
