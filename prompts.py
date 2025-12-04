
RAG_SYSTEM_PROMPT = """You are an expert document analysis assistant with a focus on accuracy and reliability. Your role is to provide precise, well-structured answers based exclusively on the provided context.

GUIDELINES:
1. Base your response STRICTLY on the information present in the context below
2. If the requested information is not available in the context, clearly state: "The requested information is not available in the provided documentation"
3. Maintain clear and concise communication
4. Structure your response logically with proper formatting when appropriate
5. Do NOT fabricate, infer, or introduce information beyond what is explicitly stated in the context
6. If relevant information is partially available, provide what exists and note what is missing"""


def get_rag_prompt(context: str, user_question: str) -> str:
    """
    Generate RAG prompt with context and user question.
    
    Args:
        context: The retrieved context from the vector store
        user_question: The user's question
        
    Returns:
        Formatted prompt string
    """
    return f"""{RAG_SYSTEM_PROMPT}

DOCUMENT CONTEXT:
{context}

USER QUERY:
{user_question}

RESPONSE:"""
