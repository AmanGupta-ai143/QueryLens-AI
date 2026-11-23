"""Orchestrates one chat turn: validate -> retrieve -> store -> track unanswered."""
from dataclasses import dataclass

from errors import DatabaseError
from nlp.chatbot_engine import ChatbotEngine, ChatResult
from services.conversation_service import ConversationService
from services.unanswered_service import UnansweredService


@dataclass
class ChatTurn:
    result: ChatResult
    conversation_id: int | None
    storage_error: str | None = None


class ChatService:
    def __init__(self, engine: ChatbotEngine, conversations: ConversationService,
                 unanswered: UnansweredService):
        self.engine = engine
        self.conversations = conversations
        self.unanswered = unanswered

    def ask(self, session_id: str, question: str, threshold: float | None = None) -> ChatTurn:
        """Raises ``ValidationError`` for empty/invalid input. A storage failure
        does not hide the answer - it is reported in ``storage_error``."""
        result = self.engine.answer(question, threshold)
        try:
            conversation_id = self.conversations.log(
                session_id, result.question, result.response,
                result.best.faq_id if result.answered else None,
                result.score, result.predicted_category,
            )
            if not result.answered and result.status != "empty_kb":
                self.unanswered.record(result.question)
        except DatabaseError as exc:
            return ChatTurn(result, None, str(exc))
        return ChatTurn(result, conversation_id)
