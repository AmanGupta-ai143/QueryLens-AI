"""Builds all services once and keeps the NLP index in sync with the FAQ table."""
from config import DB_PATH, SAMPLE_FAQ_PATH
from database.db_manager import Database
from nlp.chatbot_engine import ChatbotEngine
from services.chat_service import ChatService
from services.conversation_service import ConversationService
from services.faq_service import FAQService
from services.feedback_service import FeedbackService
from services.unanswered_service import UnansweredService


class AppContext:
    def __init__(self, db_path=DB_PATH, seed: bool = True):
        self.db = Database(db_path)
        self.faqs = FAQService(self.db)
        if seed:
            self.faqs.seed_from_json(SAMPLE_FAQ_PATH)
        self.conversations = ConversationService(self.db)
        self.feedback = FeedbackService(self.db)
        self.unanswered = UnansweredService(self.db)
        self.engine = ChatbotEngine(self.faqs.list())
        self.chat = ChatService(self.engine, self.conversations, self.unanswered)

    def refresh_engine(self) -> None:
        """Rebuild the TF-IDF index after the FAQ table changed."""
        self.engine.load(self.faqs.list())

    # FAQ changes always go through these helpers so the index never goes stale.
    def add_faq(self, question, answer, category, keywords="") -> int:
        faq_id = self.faqs.add(question, answer, category, keywords)
        self.refresh_engine()
        return faq_id

    def update_faq(self, faq_id, question, answer, category, keywords="") -> None:
        self.faqs.update(faq_id, question, answer, category, keywords)
        self.refresh_engine()

    def delete_faq(self, faq_id) -> bool:
        deleted = self.faqs.delete(faq_id)
        self.refresh_engine()
        return deleted

    def import_faqs_csv(self, data: bytes, filename: str) -> dict:
        report = self.faqs.import_csv(data, filename)
        self.refresh_engine()
        return report

    def create_faq_from_unanswered(self, unanswered_id, question, answer, category, keywords="") -> int:
        """Admin turns an unanswered question into a real FAQ and resolves it."""
        faq_id = self.add_faq(question, answer, category, keywords)
        self.unanswered.mark_resolved(unanswered_id)
        return faq_id
