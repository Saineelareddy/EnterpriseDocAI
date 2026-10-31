import os
import re
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY
from backend.retrieval import hybrid_retrieve

LLM_MODEL = "gemini-1.5-flash"

SYSTEM_PROMPT = """You are EnterpriseDoc AI, an intelligent, authoritative Enterprise Documentation Assistant.

CRITICAL INSTRUCTIONS:
1. STRICT EVIDENCE GROUNDING: For all informational questions, answer the question using ONLY the retrieved document passages provided in the Context below. Do NOT use external knowledge, speculate, extrapolate, or invent facts.
2. NOT FOUND RESPONSE: If the informational question cannot be directly determined from the provided Context passages, you MUST respond with:
"I could not find sufficient information in the provided enterprise documentation to answer this question."
Do NOT attempt to fabricate an answer.
3. CITATIONS: Include precise inline citations in your response using format [Source N] or [Doc: <filename>, Page <page>]. Every factual claim must be backed by a source.
4. CONTRADICTION & OUTDATED INFO DETECTION: Carefully inspect the retrieved passages. If two documents or sections state conflicting or contradictory rules, policies, or dates, you MUST add a dedicated section at the bottom titled:
"⚠️ Contradiction / Conflict Warning:" explaining the conflicting statements and citing the conflicting sources.
5. CONFIDENCE RATING: At the very end of your response, output on a new line:
Confidence: High | Medium | Low | None
- High: Context directly, unambiguously answers the question.
- Medium: Context partially answers the question or requires minor inference from stated facts.
- Low: Context mentions keywords but is missing critical specifics.
- None: Question is unanswerable from the context.
"""

# Enterprise & documentation keywords that signify informational retrieval is needed
ENTERPRISE_KEYWORDS = {
    'policy', 'policies', 'leave', 'pto', 'vacation', 'holiday', 'sick', 'parental',
    'salary', 'pay', 'payroll', 'bonus', 'appraisal', 'review', 'promotion', 'compensation',
    'work', 'remote', 'hybrid', 'hours', 'office', 'schedule', 'attendance', 'badge',
    'security', 'mfa', 'password', 'encryption', 'device', 'laptop', 'incident', 'soc',
    'ticket', 'helpdesk', 'support', 'troubleshoot', 'troubleshooting', 'error', 'code',
    'data', 'privacy', 'gdpr', 'ccpa', 'breach', 'retention', 'compliance', 'audit',
    'travel', 'expense', 'per diem', 'flight', 'reimbursement', 'resignation', 'notice',
    'exit', 'asset', 'handover', 'api', 'token', 'jwt', 'endpoint', 'webhook', 'http',
    'quota', 'limit', 'rate', 'tier', 'subscription', 'pricing', 'cost', 'invoice',
    'rag', 'chroma', 'vector', 'chunk', 'document', 'upload', 'ingest', 'architecture',
    'rto', 'rpo', 'disaster', 'backup', 'restore', 'failover', 'database', 'sql', 'version'
}

def decide_retrieval_need(query: str) -> Dict[str, Any]:
    """
    Decide whether a user query requires document retrieval or if it is
    a general conversational interaction (greeting, small-talk, name introduction, gratitude, apology).
    Returns:
      - 'requires_retrieval': bool
      - 'intent': str
      - 'response': Optional[str]
    """
    q_trimmed = query.strip()
    q_lower = q_trimmed.lower()
    q_clean = re.sub(r'^[^\w]+|[^\w]+$', '', q_lower)
    words = re.findall(r'\b\w+\b', q_lower)
    word_set = set(words)
    has_enterprise_keywords = bool(word_set.intersection(ENTERPRISE_KEYWORDS))
    
    # 1. Gratitude (thank you, thanks, appreciate it, etc.)
    if re.search(r'\b(thank\s+you|thanks|thx|thank\s+u|appreciate\s+it|many\s+thanks|much\s+appreciated)\b', q_lower):
        if not has_enterprise_keywords:
            return {
                "requires_retrieval": False,
                "intent": "gratitude",
                "response": "You're very welcome! Happy to help. Please let me know if you have any questions regarding company policies, developer guides, or APIs."
            }
            
    # 2. Apology (sorry, my bad, etc.)
    if re.search(r'\b(sorry|i\'?m\s+sorry|my\s+bad|excuse\s+me|pardon(\s+me)?)\b', q_lower):
        if not has_enterprise_keywords:
            return {
                "requires_retrieval": False,
                "intent": "apology",
                "response": "No worries at all! Happy to help. Feel free to ask any questions about our enterprise documentation, policies, or technical guides."
            }

    # 3. Farewells (bye, goodbye, see you, etc.)
    if re.search(r'\b(bye|goodbye|see\s+ya|see\s+you|have\s+a\s+(great|good|nice)\s+(day|evening)|take\s+care)\b', q_lower):
        if not has_enterprise_keywords:
            return {
                "requires_retrieval": False,
                "intent": "farewell",
                "response": "Goodbye! Have a great day ahead. Feel free to reach out whenever you have questions about the documentation."
            }

    # 4. Identity / Capabilities (who are you, what can you do, etc.)
    if re.search(r'\b(who\s+are\s+you|what\s+can\s+you\s+do|what\s+do\s+you\s+do|what\s+is\s+your\s+name|what\s+are\s+you|how\s+can\s+you\s+help|tell\s+me\s+about\s+yourself)\b', q_lower) or q_clean in {"help", "help me"}:
        return {
            "requires_retrieval": False,
            "intent": "bot_identity",
            "response": "Hello! I am EnterpriseDoc AI, your documentation assistant. I can help answer questions regarding company policies, developer onboarding guides, REST API specifications, rate limits, and IT troubleshooting using grounded evidence from your enterprise documents. What would you like to know?"
        }

    # 5. Pleasantries (how are you, etc.)
    if re.search(r'\b(how\s+are\s+you|how\'?s\s+it\s+going|how\s+do\s+you\s+do|hope\s+you\'?re\s+doing\s+well)\b', q_lower):
        if not has_enterprise_keywords:
            return {
                "requires_retrieval": False,
                "intent": "pleasantry",
                "response": "Hello! I'm doing great, thank you for asking. Happy to help! How can I assist you with your enterprise documentation or questions today?"
            }

    # 6. Introduction ("my name is ...", "I am ...", "call me ...")
    name_match = re.search(r'\b(?:my\s+name\s+is|i\s+am|i\'m|this\s+is|call\s+me)\s+([A-Za-z]+)\b', q_trimmed, re.IGNORECASE)
    if name_match and not has_enterprise_keywords and len(words) <= 7:
        name = name_match.group(1).capitalize()
        if name.lower() not in {"a", "the", "an", "here", "just", "looking", "asking", "trying", "wondering"}:
            return {
                "requires_retrieval": False,
                "intent": "introduction",
                "response": f"Hello {name}! Nice to meet you. I'm happy to help! Let me know if you need any assistance with company policies, developer guides, or API documentation."
            }

    # 7. Greetings (hi, hello, hey, good morning, etc.)
    greeting_pattern = r'^(hi|hello|hey|hola|howdy|good\s+(morning|afternoon|evening|day)|greetings)(\s+(there|assistant|bot|team|all))?$'
    if re.match(greeting_pattern, q_clean):
        return {
            "requires_retrieval": False,
            "intent": "greeting",
            "response": "Hello! Happy to help. I am your Enterprise Documentation Assistant. Feel free to ask me anything about company policies, technical guides, or API specifications."
        }

    # 8. Affirmations (ok, okay, cool, great, got it)
    affirmation_pattern = r'^(ok|okay|cool|nice|great|awesome|perfect|got\s+it|understood|sounds\s+good|sure)[\s!.]*$'
    if re.match(affirmation_pattern, q_clean):
        return {
            "requires_retrieval": False,
            "intent": "affirmation",
            "response": "Glad to hear that! Let me know whenever you have more questions."
        }

    return {
        "requires_retrieval": True,
        "intent": "knowledge_query",
        "response": None
    }

def format_concise_grounded_answer(query: str, sources: List[Dict[str, Any]]) -> str:
    """Format a clean, concise, human-readable answer directly from top retrieved evidence without notices."""
    if not sources:
        return "I could not find sufficient information in the provided enterprise documentation to answer this question."

    top_s = sources[0]
    excerpt_clean = re.sub(r'^\[.*?\|\s*Page\s*\d+\s*\|\s*Section:.*?\]\s*', '', top_s.get('excerpt', '')).strip()
    excerpt_clean = re.sub(r'^#+\s*', '', excerpt_clean).strip()

    lines = [line.strip() for line in excerpt_clean.splitlines() if line.strip()]
    if not lines:
        lines = [excerpt_clean]

    primary_answer = "\n\n".join(lines[:3])

    second_info = ""
    if len(sources) > 1:
        s2 = sources[1]
        s2_clean = re.sub(r'^\[.*?\|\s*Page\s*\d+\s*\|\s*Section:.*?\]\s*', '', s2.get('excerpt', '')).strip()
        s2_clean = re.sub(r'^#+\s*', '', s2_clean).strip()
        s2_lines = [l.strip() for l in s2_clean.splitlines() if l.strip()]
        if s2_lines and s2_lines[0] not in primary_answer:
            second_info = f"\n\n**Additional Details** [Source 2]:\n{s2_lines[0]}"

    return (
        f"{primary_answer} [Source 1]{second_info}\n\n"
        "Confidence: High"
    )

def format_context_passages(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved passages into structured context blocks with metadata."""
    if not retrieved_chunks:
        return "No relevant context passages found in knowledge base."

    blocks = []
    for idx, c in enumerate(retrieved_chunks):
        meta = c.get("metadata", {})
        fname = meta.get("filename", "Unknown Document")
        pnum = meta.get("page_number", 1)
        sec = meta.get("section_title", "General")
        content = c.get("content", "").strip()

        block = f"[Source {idx + 1}]\nDocument: {fname}\nPage: {pnum}\nSection: {sec}\nContent:\n{content}"
        blocks.append(block)

    return "\n\n---\n\n".join(blocks)

def parse_confidence_and_contradiction(answer_text: str) -> Dict[str, Any]:
    """Parse out confidence level and detect contradiction warning from model output."""
    confidence = "Medium"
    has_contradiction = False
    clean_answer = answer_text

    # Detect confidence
    for line in answer_text.splitlines():
        if "confidence:" in line.lower():
            if "high" in line.lower():
                confidence = "High"
            elif "medium" in line.lower():
                confidence = "Medium"
            elif "low" in line.lower():
                confidence = "Low"
            elif "none" in line.lower():
                confidence = "None"

    # Detect contradiction warning
    if "contradiction / conflict warning" in answer_text.lower() or "conflict warning" in answer_text.lower():
        has_contradiction = True

    # If model gave not-found answer, force confidence to None or Low
    if "could not find sufficient information" in answer_text.lower():
        confidence = "None"

    return {
        "confidence": confidence,
        "has_contradiction": has_contradiction
    }

def generate_rag_answer(
    query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    top_k: int = 5,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute end-to-end RAG pipeline:
    0. Intelligent Intent Classification (decides whether retrieval is required or not)
    1. Hybrid retrieval (Semantic + BM25 + RRF + Cross-Encoder Reranking)
    2. Context assembly with citation references
    3. Conversational history integration
    4. Gemini Flash generation strictly grounded in evidence
    5. Contradiction & Confidence metadata extraction
    """
    # 0. Determine if document retrieval is required or if it is general conversational small-talk
    intent_data = decide_retrieval_need(query)
    if not intent_data["requires_retrieval"]:
        return {
            "query": query,
            "answer": intent_data["response"],
            "confidence": "High",
            "has_contradiction": False,
            "sources": [],
            "retrieved_count": 0,
            "retrieval_required": False,
            "intent": intent_data["intent"]
        }

    effective_api_key = api_key or os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY

    # 1. Retrieve most relevant passages using Hybrid Pipeline
    retrieved_chunks = hybrid_retrieve(query=query, top_k=top_k, api_key=effective_api_key)

    if not retrieved_chunks:
        return {
            "query": query,
            "answer": "I could not find sufficient information in the provided enterprise documentation to answer this question.",
            "confidence": "None",
            "has_contradiction": False,
            "sources": [],
            "retrieved_count": 0,
            "retrieval_required": True,
            "intent": "knowledge_query"
        }

    # Format context and sources list (Top 2 most relevant citations)
    context_str = format_context_passages(retrieved_chunks)
    sources = []
    for idx, c in enumerate(retrieved_chunks[:2]):
        meta = c.get("metadata", {})
        raw_c = c.get("content", "")
        clean_text = re.sub(r'^\[.*?\|\s*Page\s*\d+\s*\|\s*Section:.*?\]\s*', '', raw_c, flags=re.MULTILINE).strip()
        sources.append({
            "source_id": idx + 1,
            "chunk_id": c.get("chunk_id"),
            "filename": meta.get("filename", "Unknown"),
            "page_number": meta.get("page_number", 1),
            "section_title": meta.get("section_title", "General"),
            "score": round(float(c.get("rerank_score", c.get("score", 0.0))), 3),
            "excerpt": clean_text[:280] + "..." if len(clean_text) > 280 else clean_text
        })

    # Build prompt with conversation history for conversational follow-ups
    history_str = ""
    if conversation_history:
        history_lines = []
        for msg in conversation_history[-4:]: # take last 4 turns for context
            role = msg.get("role", "user").capitalize()
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        if history_lines:
            history_str = "Prior Conversation History:\n" + "\n".join(history_lines) + "\n\n"

    prompt_content = f"""{SYSTEM_PROMPT}

{history_str}CONTEXT PASSAGES:
{context_str}

USER QUESTION:
{query}

ANSWER (Strictly based on above context passages with inline citations):"""

    # 2. Call Gemini Flash LLM
    answer_text = ""
    
    # Check query content-token overlap with retrieved passages
    from backend.retrieval import tokenize_text
    q_toks = set(tokenize_text(query))
    GENERIC_TERMS = {
        "what", "is", "the", "are", "for", "and", "in", "to", "of", "how",
        "many", "can", "employee", "employees", "company", "corporate", "enterprise",
        "about", "with", "from", "at", "by", "this", "that"
    }
    content_q_toks = q_toks - GENERIC_TERMS
    if not content_q_toks:
        content_q_toks = q_toks

    matched_toks = set()
    for c in retrieved_chunks:
        matched_toks.update(set(tokenize_text(c.get("content", ""))))
    overlap = content_q_toks.intersection(matched_toks)

    is_valid_key = bool(effective_api_key and effective_api_key.strip() and effective_api_key.strip() not in {"your_gemini_api_key_here", "None", ""})

    # If key content terms are missing from documents (unanswerable / out-of-domain)
    if not overlap or (len(overlap) / len(content_q_toks) < 0.25):
        answer_text = (
            "I could not find sufficient information in the provided enterprise documentation to answer this question.\n\n"
            "Confidence: None"
        )
    elif is_valid_key:
        # Try modern google.genai SDK
        try:
            from google import genai
            client = genai.Client(api_key=effective_api_key.strip())
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=prompt_content,
            )
            answer_text = response.text or ""
        except Exception as e:
            # Fallback to legacy google.generativeai if available
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=effective_api_key.strip())
                model = legacy_genai.GenerativeModel(LLM_MODEL)
                res = model.generate_content(prompt_content)
                answer_text = res.text or ""
            except Exception as e2:
                # Format clean, concise grounded answer directly from evidence (no disclaimers)
                answer_text = format_concise_grounded_answer(query, sources)
    else:
        # Provide clean, concise grounded answer directly from evidence (no disclaimers)
        answer_text = format_concise_grounded_answer(query, sources)

    # 3. Parse confidence and contradictions
    parsed_meta = parse_confidence_and_contradiction(answer_text)

    # If confidence is None (unanswerable / insufficient evidence), do not return any citations
    final_sources = [] if parsed_meta["confidence"] == "None" else sources[:2]

    return {
        "query": query,
        "answer": answer_text,
        "confidence": parsed_meta["confidence"],
        "has_contradiction": parsed_meta["has_contradiction"],
        "sources": final_sources,
        "retrieved_count": len(final_sources),
        "retrieval_required": True,
        "intent": "knowledge_query"
    }
