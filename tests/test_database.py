import unittest

import pandas as pd

from errors import NotFoundError, ValidationError
from services import analytics
from tests.helpers import ContextTestCase


class FAQTests(ContextTestCase):
    def test_seed_loaded(self):
        self.assertEqual(self.ctx.faqs.count(), 50)
        self.assertEqual(len(self.ctx.faqs.category_counts()), 10)

    def test_8_add_faq_and_engine_updates(self):
        q = "What is the dress code for students?"
        self.assertFalse(self.ctx.chat.ask("s", q).result.answered)
        faq_id = self.ctx.add_faq(q, "Students must wear the university ID card and neat attire.",
                                  "Admissions", "dress code, uniform, attire")
        self.assertEqual(self.ctx.faqs.get(faq_id)["keywords"], "dress code, uniform, attire")
        self.assertTrue(self.ctx.chat.ask("s", q).result.answered)

    def test_9_edit_faq(self):
        faq = self.ctx.faqs.list(search="library opening hours")[0]
        self.ctx.update_faq(faq["id"], faq["question"], "The library is open 24x7 during exams.",
                            "Library", "library hours")
        self.assertIn("24x7", self.ctx.faqs.get(faq["id"])["answer"])
        r = self.ctx.chat.ask("s", "What are the library opening hours?").result
        self.assertIn("24x7", r.response)
        with self.assertRaises(NotFoundError):
            self.ctx.update_faq(9999, "valid question?", "valid answer", "Library")

    def test_10_delete_faq(self):
        faq = self.ctx.faqs.list(search="How can I contact the IT helpdesk")[0]
        self.assertTrue(self.ctx.delete_faq(faq["id"]))
        self.assertIsNone(self.ctx.faqs.get(faq["id"]))
        self.assertEqual(self.ctx.faqs.count(), 49)
        self.assertFalse(self.ctx.delete_faq(faq["id"]))

    def test_faq_validation(self):
        with self.assertRaises(ValidationError):
            self.ctx.faqs.add("hi", "answer text", "Fees")                       # too short
        with self.assertRaises(ValidationError):
            self.ctx.faqs.add("A valid question?", "A valid answer", "Weather")  # bad category
        with self.assertRaises(ValidationError):
            self.ctx.faqs.add("how can i apply for ADMISSION?", "dup answer", "Admissions")  # duplicate

    def test_search_and_category_filter(self):
        self.assertTrue(all(f["category"] == "Fees" for f in self.ctx.faqs.list(category="Fees")))
        self.assertTrue(self.ctx.faqs.list(search="wi-fi"))
        self.assertEqual(self.ctx.faqs.list(search="100%_nothing"), [])  # wildcards are escaped

    def test_csv_import_is_validated(self):
        csv_ok = b"question,answer,category,keywords\nWhere is the gym located?,The gym is behind the library.,Hostel,gym\nbad,x,Nope,\n"
        report = self.ctx.import_faqs_csv(csv_ok, "faqs.csv")
        self.assertEqual((report["added"], report["skipped"]), (1, 1))
        for data, name in [(b"a,b\n1,2", "x.csv"), (b"q", "x.txt"), (b"x" * 1_000_001, "big.csv")]:
            with self.assertRaises(ValidationError):
                self.ctx.import_faqs_csv(data, name)


class ConversationTests(ContextTestCase):
    def test_11_conversation_history(self):
        t = self.ctx.chat.ask("sess1", "How can I apply for admission?")
        self.assertIsNotNone(t.conversation_id)
        rows = self.ctx.conversations.list()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["user_question"], "How can I apply for admission?")
        self.assertEqual(rows[0]["matched_question"], "How can I apply for admission?")
        self.assertGreater(rows[0]["similarity_score"], 0.5)
        self.assertEqual(len(self.ctx.conversations.list(search="admission")), 1)
        self.assertEqual(len(self.ctx.conversations.list(search="zzz")), 0)
        self.assertTrue(self.ctx.conversations.delete(t.conversation_id))
        self.assertEqual(self.ctx.conversations.count(), 0)

    def test_empty_question_is_rejected_and_not_stored(self):
        with self.assertRaises(ValidationError):
            self.ctx.chat.ask("s", "   ")
        self.assertEqual(self.ctx.conversations.count(), 0)

    def test_12_helpful_feedback(self):
        cid = self.ctx.chat.ask("s", "How can I apply for admission?").conversation_id
        self.ctx.feedback.submit(cid, "helpful", "Clear answer")
        fb = self.ctx.feedback.get(cid)
        self.assertEqual((fb["rating"], fb["feedback_comment"]), ("helpful", "Clear answer"))
        self.assertEqual(self.ctx.conversations.get(cid)["feedback_rating"], "helpful")

    def test_13_not_helpful_feedback_flags_faq_but_never_edits_it(self):
        before = self.ctx.faqs.list(search="How can I apply for admission")[0]
        cid = self.ctx.chat.ask("s", "How can I apply for admission?").conversation_id
        self.ctx.feedback.submit(cid, "not_helpful", "Missing the fee")
        review = self.ctx.feedback.faqs_needing_review()
        self.assertEqual(len(review), 1)
        self.assertEqual(review[0]["faq_id"], before["id"])
        self.assertEqual(self.ctx.faqs.get(before["id"])["answer"], before["answer"])  # unchanged

    def test_feedback_replaces_and_validates(self):
        cid = self.ctx.chat.ask("s", "How can I apply for admission?").conversation_id
        self.ctx.feedback.submit(cid, "helpful")
        self.ctx.feedback.submit(cid, "not_helpful")
        self.assertEqual(self.ctx.feedback.summary()["not_helpful"], 1)
        self.assertEqual(self.ctx.feedback.summary()["helpful"], 0)
        with self.assertRaises(ValidationError):
            self.ctx.feedback.submit(cid, "great")
        with self.assertRaises(NotFoundError):
            self.ctx.feedback.submit(9999, "helpful")

    def test_deleting_conversation_deletes_its_feedback(self):
        cid = self.ctx.chat.ask("s", "How can I apply for admission?").conversation_id
        self.ctx.feedback.submit(cid, "helpful")
        self.ctx.conversations.delete(cid)
        self.assertEqual(self.ctx.feedback.summary()["helpful"], 0)


class UnansweredTests(ContextTestCase):
    def test_14_unanswered_question_storage_and_frequency(self):
        t = self.ctx.chat.ask("s", "Is there a swimming pool on campus?")
        self.assertFalse(t.result.answered)
        self.ctx.chat.ask("s", "is there a   SWIMMING pool on campus??")
        rows = self.ctx.unanswered.list()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["frequency"], 2)
        self.assertEqual(rows[0]["status"], "open")
        self.assertIsNone(self.ctx.conversations.list()[0]["matched_faq_id"])

    def test_answered_questions_are_not_stored_as_unanswered(self):
        self.ctx.chat.ask("s", "How can I apply for admission?")
        self.assertEqual(self.ctx.unanswered.list(), [])

    def test_create_faq_from_unanswered_resolves_it(self):
        self.ctx.chat.ask("s", "Is there a swimming pool on campus?")
        item = self.ctx.unanswered.list()[0]
        self.ctx.create_faq_from_unanswered(item["id"], item["question"],
                                            "Yes, the sports complex has a swimming pool.",
                                            "Hostel", "swimming pool, sports")
        self.assertEqual(self.ctx.unanswered.get(item["id"])["status"], "resolved")
        self.assertTrue(self.ctx.chat.ask("s", "Is there a swimming pool on campus?").result.answered)

    def test_resolved_question_reopens_when_asked_again(self):
        self.ctx.chat.ask("s", "Do you have a drone club?")
        uid = self.ctx.unanswered.list()[0]["id"]
        self.ctx.unanswered.mark_resolved(uid)
        self.ctx.chat.ask("s", "Do you have a drone club?")
        self.assertEqual(self.ctx.unanswered.get(uid)["status"], "open")

    def test_delete(self):
        self.ctx.chat.ask("s", "Do you have a drone club?")
        uid = self.ctx.unanswered.list()[0]["id"]
        self.assertTrue(self.ctx.unanswered.delete(uid))
        with self.assertRaises(NotFoundError):
            self.ctx.unanswered.mark_resolved(uid)


class DashboardStatsTests(ContextTestCase):
    def test_15_dashboard_statistics_use_real_records(self):
        empty = analytics.overview(self.ctx.conversations.dataframe(), self.ctx.faqs.count())
        self.assertEqual(empty["total_questions"], 0)
        self.assertIsNone(empty["avg_similarity"])
        self.assertIsNone(empty["satisfaction"])

        ids = [self.ctx.chat.ask("s", q).conversation_id for q in
               ["How can I apply for admission?", "How can I apply for admission?",
                "library timings", "bitcoin price"]]
        self.ctx.feedback.submit(ids[0], "helpful")
        self.ctx.feedback.submit(ids[2], "not_helpful")

        df = self.ctx.conversations.dataframe()
        o = analytics.overview(df, self.ctx.faqs.count())
        self.assertEqual((o["total_questions"], o["answered"], o["unanswered"]), (4, 3, 1))
        self.assertEqual((o["helpful"], o["not_helpful"]), (1, 1))
        self.assertAlmostEqual(o["satisfaction"], 0.5)
        self.assertAlmostEqual(o["avg_similarity"], df["similarity_score"].mean())

        top = analytics.top_faqs(df)
        self.assertEqual(top.iloc[0]["question"], "How can I apply for admission?")
        self.assertEqual(int(top.iloc[0]["times_matched"]), 2)
        self.assertEqual(analytics.category_distribution(df)["Admissions"], 2)
        self.assertEqual(analytics.success_split(df).to_dict(), {"Answered": 3, "Unanswered": 1})
        self.assertEqual(analytics.feedback_split(df).to_dict(),
                         {"Helpful": 1, "Not helpful": 1, "No feedback": 2})
        for period in ("Daily", "Weekly", "Monthly"):
            self.assertEqual(int(analytics.activity_series(df, period).sum()), 4)

    def test_deleted_faq_keeps_history_consistent(self):
        self.ctx.chat.ask("s", "How can I apply for admission?")
        faq = self.ctx.faqs.list(search="How can I apply for admission")[0]
        self.ctx.delete_faq(faq["id"])
        df = self.ctx.conversations.dataframe()
        self.assertEqual(analytics.overview(df, 49)["answered"], 1)
        self.assertEqual(analytics.top_faqs(df).iloc[0]["question"], "(deleted FAQ)")


if __name__ == "__main__":
    unittest.main()
