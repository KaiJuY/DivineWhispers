# faq_pipeline.py
import json
import sqlite3
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import PendingFAQ, FAQChunk, ChunkType
from .unified_rag import UnifiedRAGHandler
from .config import SystemConfig
import hashlib
import logging

# Chain of Responsibility Pattern - Base handler
class FAQApprovalHandler(ABC):
    """Base class for FAQ approval chain handlers using Chain of Responsibility pattern."""
    
    def __init__(self):
        self._next_handler: Optional[FAQApprovalHandler] = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def set_next(self, handler: 'FAQApprovalHandler') -> 'FAQApprovalHandler':
        """Set the next handler in the chain."""
        self._next_handler = handler
        return handler
    
    @abstractmethod
    def handle(self, faq: PendingFAQ, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the FAQ approval step."""
        pass
    
    def _handle_next(self, faq: PendingFAQ, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pass to next handler in chain."""
        if self._next_handler:
            return self._next_handler.handle(faq, context)
        return context

class ContentValidationHandler(FAQApprovalHandler):
    """Validates FAQ content quality and appropriateness."""
    
    def handle(self, faq: PendingFAQ, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Validating content for FAQ: {faq.session_id}")
        
        issues = []
        
        # Check minimum length requirements
        if len(faq.question.strip()) < 5:
            issues.append("Question too short (minimum 5 characters)")
        
        if len(faq.answer.strip()) < 10:
            issues.append("Answer too short (minimum 10 characters)")
        
        # Check for inappropriate content (basic keywords)
        inappropriate_keywords = ['spam', 'hack', 'illegal', 'fraud']
        content_to_check = (faq.question + " " + faq.answer).lower()
        
        for keyword in inappropriate_keywords:
            if keyword in content_to_check:
                issues.append(f"Contains inappropriate content: {keyword}")
        
        # Check for duplicate questions (simplified)
        if len(faq.question.strip()) < 3:
            issues.append("Question appears to be incomplete")
        
        context["validation_issues"] = issues
        context["content_valid"] = len(issues) == 0
        
        if issues:
            self.logger.warning(f"Content validation failed: {issues}")
            context["approval_status"] = "rejected"
            context["rejection_reason"] = "Content validation failed: " + "; ".join(issues)
            return context
        
        self.logger.info("Content validation passed")
        return self._handle_next(faq, context)

class DuplicateCheckHandler(FAQApprovalHandler):
    """Checks for duplicate FAQs in the knowledge base."""
    
    def __init__(self, rag_handler: UnifiedRAGHandler):
        super().__init__()
        self.rag = rag_handler
    
    def handle(self, faq: PendingFAQ, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Checking for duplicates: {faq.session_id}")
        
        try:
            # Search for similar FAQs
            rag_result = self.rag.query(
                faq.question, 
                top_k=3, 
                chunk_types=[ChunkType.FAQ]
            )
            
            # Simple similarity check based on scores
            similar_faqs = [
                chunk for chunk, score in zip(rag_result.chunks, rag_result.scores)
                if score < 0.3  # Very similar (low distance)
            ]
            
            context["similar_faqs"] = similar_faqs
            context["duplicate_found"] = len(similar_faqs) > 0
            
            if similar_faqs:
                self.logger.warning(f"Found {len(similar_faqs)} similar FAQs")
                context["needs_manual_review"] = True
                context["review_reason"] = f"Similar FAQs found: {len(similar_faqs)}"
            
        except Exception as e:
            self.logger.error(f"Duplicate check failed: {e}")
            context["duplicate_check_error"] = str(e)
        
        return self._handle_next(faq, context)

class CategoryValidationHandler(FAQApprovalHandler):
    """Validates and potentially corrects FAQ categories."""
    
    VALID_CATEGORIES = ['love', 'career', 'health', 'wealth', 'general', 'family', 'education']
    
    def handle(self, faq: PendingFAQ, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Validating category for FAQ: {faq.session_id}")
        
        original_category = faq.category.lower()
        
        # Check if category is valid
        if original_category not in self.VALID_CATEGORIES:
            # Try to auto-correct common misspellings or synonyms
            category_mapping = {
                'romance': 'love',
                'relationship': 'love',
                'work': 'career',
                'job': 'career',
                'business': 'career',
                'money': 'wealth',
                'financial': 'wealth',
                'fortune': 'wealth',
                'medical': 'health',
                'illness': 'health'
            }
            
            corrected_category = category_mapping.get(original_category, 'general')
            context["category_corrected"] = True
            context["original_category"] = original_category
            context["corrected_category"] = corrected_category
            
            # Update the FAQ object
            faq.category = corrected_category
            
            self.logger.info(f"Category corrected: {original_category} -> {corrected_category}")
        else:
            context["category_corrected"] = False
            context["corrected_category"] = original_category
        
        context["category_valid"] = True
        return self._handle_next(faq, context)

class FinalApprovalHandler(FAQApprovalHandler):
    """Final approval step that creates the FAQ chunk."""
    
    def handle(self, faq: PendingFAQ, context: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Final approval for FAQ: {faq.session_id}")
        
        # Check if any previous handler rejected it
        if context.get("approval_status") == "rejected":
            return context
        
        # Check if manual review is needed
        if context.get("needs_manual_review", False):
            context["approval_status"] = "needs_review"
            context["final_decision"] = "Manual review required"
            return context
        
        # Auto-approve if all checks passed
        context["approval_status"] = "auto_approved"
        context["final_decision"] = "Automatically approved"
        
        self.logger.info(f"FAQ auto-approved: {faq.session_id}")
        return context

class FAQPipeline:
    """Main FAQ pipeline with approval workflow using Chain of Responsibility."""
    
    def __init__(self, db_path: str = None, rag_handler: UnifiedRAGHandler = None):
        self.config = SystemConfig()
        self.db_path = db_path or self.config.pending_faq_db_path
        self.rag = rag_handler
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_db()
        
        # Set up approval chain
        self._setup_approval_chain()
    
    def _init_db(self):
        """Initialize pending FAQ database."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_faqs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT,
                    language TEXT,
                    session_id TEXT UNIQUE,
                    created_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    approval_context TEXT,
                    approved_by TEXT,
                    approved_at TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            self.logger.info("FAQ database initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize FAQ database: {e}")
            raise
    
    def _setup_approval_chain(self):
        """Set up the Chain of Responsibility for FAQ approval."""
        # Create handlers
        content_validator = ContentValidationHandler()
        duplicate_checker = DuplicateCheckHandler(self.rag) if self.rag else None
        category_validator = CategoryValidationHandler()
        final_approver = FinalApprovalHandler()
        
        # Chain them together
        content_validator.set_next(category_validator)
        
        if duplicate_checker:
            category_validator.set_next(duplicate_checker)
            duplicate_checker.set_next(final_approver)
        else:
            category_validator.set_next(final_approver)
        
        self.approval_chain = content_validator
        self.logger.info("FAQ approval chain established")
    
    def capture_interaction(self, question: str, answer: str, category: str, 
                          language: str, session_id: str) -> int:
        """Capture user interaction for potential FAQ creation."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "INSERT INTO pending_faqs (question, answer, category, language, session_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (question, answer, category, language, session_id, datetime.now().isoformat())
            )
            faq_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            self.logger.info(f"Captured FAQ interaction: {session_id}")
            return faq_id
        except Exception as e:
            self.logger.error(f"Failed to capture FAQ interaction: {e}")
            return -1
    
    def get_pending_faqs(self, status: str = "pending") -> List[PendingFAQ]:
        """Get pending FAQs for review."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT question, answer, category, language, session_id, created_at, status FROM pending_faqs WHERE status = ?",
                (status,)
            )
            
            faqs = []
            for row in cursor.fetchall():
                faqs.append(PendingFAQ(
                    question=row[0],
                    answer=row[1],
                    category=row[2],
                    language=row[3],
                    session_id=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    status=row[6]
                ))
            
            conn.close()
            self.logger.info(f"Retrieved {len(faqs)} pending FAQs")
            return faqs
        except Exception as e:
            self.logger.error(f"Failed to get pending FAQs: {e}")
            return []
    
    def process_faq_approval(self, session_id: str) -> Dict[str, Any]:
        """Process FAQ through approval chain."""
        try:
            # Get the pending FAQ
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT question, answer, category, language, created_at FROM pending_faqs WHERE session_id = ? AND status = 'pending'",
                (session_id,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return {"error": "FAQ not found or already processed"}
            
            # Create PendingFAQ object
            faq = PendingFAQ(
                question=row[0],
                answer=row[1],
                category=row[2],
                language=row[3],
                session_id=session_id,
                created_at=datetime.fromisoformat(row[4])
            )
            
            # Process through approval chain
            context = {"session_id": session_id}
            result = self.approval_chain.handle(faq, context)
            
            # Update database with approval context
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "UPDATE pending_faqs SET approval_context = ? WHERE session_id = ?",
                (json.dumps(result), session_id)
            )
            conn.commit()
            conn.close()
            
            self.logger.info(f"Processed FAQ approval: {session_id} -> {result.get('approval_status')}")
            return result
            
        except Exception as e:
            self.logger.error(f"FAQ approval processing failed: {e}")
            return {"error": str(e)}
    
    def approve_faq(self, session_id: str, approved_by: str, 
                   edited_question: Optional[str] = None, 
                   edited_answer: Optional[str] = None) -> bool:
        """Manually approve a pending FAQ and add to RAG system."""
        try:
            # Get the pending FAQ
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT question, answer, category, language FROM pending_faqs WHERE session_id = ? AND status IN ('pending', 'needs_review')",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False
            
            question = edited_question or row[0]
            answer = edited_answer or row[1]
            category = row[2]
            language = row[3]
            
            # Create FAQ chunk
            content = f"Q: {question}\n\nA: {answer}"
            chunk_id = f"faq_{category}_{hashlib.md5(content.encode()).hexdigest()[:8]}"
            
            faq_chunk = FAQChunk(
                chunk_id=chunk_id,
                category=category,
                question=question,
                answer=answer,
                content=content,
                language=language,
                created_at=datetime.now(),
                approved_by=approved_by
            )
            
            # Add to RAG system
            if self.rag:
                success = self.rag.add_faq_chunk(faq_chunk)
                if not success:
                    conn.close()
                    return False
            
            # Update status in database
            conn.execute(
                "UPDATE pending_faqs SET status = 'approved', approved_by = ?, approved_at = ? WHERE session_id = ?",
                (approved_by, datetime.now().isoformat(), session_id)
            )
            conn.commit()
            conn.close()
            
            self.logger.info(f"FAQ approved and added to knowledge base: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"FAQ approval failed: {e}")
            return False
    
    def reject_faq(self, session_id: str, rejected_by: str = None, reason: str = None) -> bool:
        """Reject a pending FAQ."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Update with rejection info
            update_data = ["rejected", session_id]
            update_sql = "UPDATE pending_faqs SET status = ?"
            
            if rejected_by:
                update_sql += ", approved_by = ?"
                update_data.insert(-1, rejected_by)
            
            if reason:
                # Store reason in approval_context
                context = json.dumps({"rejection_reason": reason, "rejected_by": rejected_by})
                update_sql += ", approval_context = ?"
                update_data.insert(-1, context)
            
            update_sql += " WHERE session_id = ?"
            
            result = conn.execute(update_sql, update_data)
            conn.commit()
            conn.close()
            
            success = result.rowcount > 0
            if success:
                self.logger.info(f"FAQ rejected: {session_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"FAQ rejection failed: {e}")
            return False
    
    def get_faq_stats(self) -> Dict[str, Any]:
        """Get statistics about FAQ pipeline."""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get counts by status
            cursor = conn.execute(
                "SELECT status, COUNT(*) FROM pending_faqs GROUP BY status"
            )
            status_counts = dict(cursor.fetchall())
            
            # Get counts by category
            cursor = conn.execute(
                "SELECT category, COUNT(*) FROM pending_faqs GROUP BY category"
            )
            category_counts = dict(cursor.fetchall())
            
            conn.close()
            
            stats = {
                "status_counts": status_counts,
                "category_counts": category_counts,
                "total_faqs": sum(status_counts.values())
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get FAQ stats: {e}")
            return {"error": str(e)}