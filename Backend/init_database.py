"""
Database initialization script for Divine Whispers
Creates tables and populates with sample data for development/testing
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models.user import User, UserRole, UserStatus
from app.models.chat_message import ChatSession, ChatMessage, MessageType
from app.models.faq import FAQ, FAQCategory, FAQFeedback
from app.models.wallet import Wallet
from app.core.security import SecurityManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database with tables and sample data"""
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True  # Set to False in production
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        # Create all tables
        logger.info("Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Tables created successfully")
        
        # Add sample data
        async with async_session() as session:
            await create_sample_users(session)
            await create_sample_faqs(session)
            await create_sample_chat_data(session)
            
            await session.commit()
            logger.info("Sample data added successfully")
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        await engine.dispose()


async def create_sample_users(session: AsyncSession):
    """Create sample users for testing"""
    
    # Check if admin user already exists
    admin_email = "admin@divinewhispers.com"
    existing_admin = await session.get(User, {"email": admin_email})
    
    if not existing_admin:
        # Create admin user
        admin_user = User(
            email=admin_email,
            password_hash=SecurityManager.hash_password("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            full_name="System Administrator",
            preferred_language="en"
        )
        session.add(admin_user)
        await session.flush()
        
        # Create wallet for admin
        admin_wallet = Wallet(
            user_id=admin_user.user_id,
            available_balance=1000,
            pending_amount=0
        )
        session.add(admin_wallet)
        
        logger.info(f"Created admin user: {admin_email}")
    
    # Create sample regular users
    sample_users = [
        {
            "email": "user1@example.com",
            "password": "user123",
            "full_name": "John Doe",
            "balance": 50
        },
        {
            "email": "user2@example.com", 
            "password": "user123",
            "full_name": "Jane Smith",
            "balance": 75
        },
        {
            "email": "tester@divinewhispers.com",
            "password": "test123",
            "full_name": "Test User",
            "balance": 100
        }
    ]
    
    for user_data in sample_users:
        existing_user = await session.get(User, {"email": user_data["email"]})
        
        if not existing_user:
            user = User(
                email=user_data["email"],
                password_hash=SecurityManager.hash_password(user_data["password"]),
                role=UserRole.USER,
                status=UserStatus.ACTIVE,
                full_name=user_data["full_name"],
                preferred_language="en"
            )
            session.add(user)
            await session.flush()
            
            # Create wallet
            wallet = Wallet(
                user_id=user.user_id,
                available_balance=user_data["balance"],
                pending_amount=0
            )
            session.add(wallet)
            
            logger.info(f"Created user: {user_data['email']}")


async def create_sample_faqs(session: AsyncSession):
    """Create sample FAQ entries"""
    
    sample_faqs = [
        {
            "category": FAQCategory.FORTUNE_READING,
            "question": "How accurate are the fortune readings?",
            "answer": "Our fortune readings are based on ancient wisdom and traditional interpretations from various temples. They are meant for guidance and reflection, not absolute predictions. The accuracy depends on how well you connect with the guidance provided and apply it to your specific situation.",
            "tags": "accuracy, reliability, divination",
            "display_order": 1
        },
        {
            "category": FAQCategory.TECHNICAL,
            "question": "How do I use the interactive chat feature?",
            "answer": "After receiving your fortune, click on the chat icon to start an interactive conversation. Ask specific questions about your reading, and our AI-powered assistant will provide personalized interpretations based on your fortune and the wisdom of the selected deity.",
            "tags": "chat, interactive, ai assistant",
            "display_order": 2
        },
        {
            "category": FAQCategory.ACCOUNT,
            "question": "How do points work?",
            "answer": "Points are used to access premium features like detailed fortune interpretations and interactive chat sessions. You can purchase points through our secure payment system in various packages. Points are deducted automatically when you use paid features.",
            "tags": "points, payment, premium features",
            "display_order": 3
        },
        {
            "category": FAQCategory.FORTUNE_READING,
            "question": "What's the difference between the different deities?",
            "answer": "Each deity specializes in different aspects of life: Guan Yin for compassion and general guidance, Mazu for protection and travel, Guan Yu for business and loyalty, Yue Lao for love and relationships, Zhu Sheng for education and career, Asakusa for spiritual enlightenment, and Erawan Shrine for comprehensive life guidance. Choose based on your specific question or area of concern.",
            "tags": "deities, specialization, guidance",
            "display_order": 4
        },
        {
            "category": FAQCategory.TECHNICAL,
            "question": "Can I save my fortune readings?",
            "answer": "Yes! All your fortune readings are automatically saved in your account profile under the 'Reports' section. You can access them anytime to review past guidance and track your spiritual journey over time.",
            "tags": "save, reports, history",
            "display_order": 5
        },
        {
            "category": FAQCategory.BILLING,
            "question": "What payment methods do you accept?",
            "answer": "We accept major credit cards, PayPal, Apple Pay, and Google Pay for coin purchases. All transactions are processed securely through encrypted payment gateways to protect your financial information.",
            "tags": "payment methods, security, billing",
            "display_order": 6
        },
        {
            "category": FAQCategory.SUPPORT,
            "question": "How can I contact customer support?",
            "answer": "You can reach our customer support team through the Contact form on our website, or email us directly at support@divinewhispers.com. We typically respond within 24-48 hours during business days.",
            "tags": "support, contact, help",
            "display_order": 7
        }
    ]
    
    # Get admin user for created_by
    admin_user = await session.get(User, {"email": "admin@divinewhispers.com"})
    admin_id = admin_user.user_id if admin_user else 1
    
    for faq_data in sample_faqs:
        # Generate slug
        import re
        slug = re.sub(r'[^\w\s-]', '', faq_data["question"].lower())
        slug = re.sub(r'[-\s]+', '-', slug)[:200]
        
        # Check if FAQ already exists
        existing_faq = await session.get(FAQ, {"slug": slug})
        
        if not existing_faq:
            faq = FAQ(
                category=faq_data["category"],
                question=faq_data["question"],
                answer=faq_data["answer"],
                slug=slug,
                tags=faq_data["tags"],
                display_order=faq_data["display_order"],
                is_published=True,
                created_by=admin_id
            )
            session.add(faq)
            
            logger.info(f"Created FAQ: {faq_data['question'][:50]}...")


async def create_sample_chat_data(session: AsyncSession):
    """Create sample chat sessions and messages for testing"""
    
    # Get test user
    test_user = await session.get(User, {"email": "tester@divinewhispers.com"})
    
    if test_user:
        # Create a sample chat session
        chat_session = ChatSession(
            user_id=test_user.user_id,
            session_name="Fortune Reading - Guan Yin",
            context_data={
                "deity_id": "guan_yin",
                "deity_name": "Guan Yin",
                "fortune_number": 42,
                "poem_title": "Compassionate Guidance",
                "conversation_type": "fortune_reading"
            },
            is_active=True
        )
        session.add(chat_session)
        await session.flush()
        
        # Add sample messages
        messages = [
            {
                "type": MessageType.USER,
                "content": "What does fortune number 42 mean for my career?"
            },
            {
                "type": MessageType.ASSISTANT,
                "content": "Based on your fortune reading with Guan Yin and the wisdom of fortune number 42, I can offer you guidance about your career path. The number 42 in Guan Yin's temple represents a time of compassionate transformation and wise decision-making in professional matters. This suggests that your career is entering a phase where your natural empathy and understanding of others will become valuable assets."
            },
            {
                "type": MessageType.USER,
                "content": "Should I take the new job offer I received?"
            },
            {
                "type": MessageType.ASSISTANT,
                "content": "The divine guidance suggests careful consideration of this opportunity. Guan Yin's wisdom indicates that you should examine not only the material benefits but also how this position aligns with your values and allows you to help others. Consider: Does this role allow you to express your compassionate nature? Will it contribute to your long-term growth and well-being? The fortune suggests that opportunities that align with your higher purpose will bring the most fulfillment."
            }
        ]
        
        for msg_data in messages:
            message = ChatMessage(
                session_id=chat_session.id,
                user_id=test_user.user_id,
                message_type=msg_data["type"],
                content=msg_data["content"],
                metadata={"sample_data": True}
            )
            session.add(message)
        
        logger.info(f"Created sample chat session for user: {test_user.email}")


if __name__ == "__main__":
    print("Initializing Divine Whispers Database...")
    print("This will create tables and add sample data for development/testing.")
    print("\nSample users that will be created:")
    print("- admin@divinewhispers.com (password: admin123) - Admin user")
    print("- user1@example.com (password: user123) - Regular user")
    print("- user2@example.com (password: user123) - Regular user") 
    print("- tester@divinewhispers.com (password: test123) - Test user with sample data")
    print("\nSample FAQs and chat data will also be created.")
    
    confirm = input("\nProceed with database initialization? (y/N): ")
    
    if confirm.lower() in ['y', 'yes']:
        asyncio.run(init_database())
        print("\n✅ Database initialization completed successfully!")
        print("\nYou can now start the application and test with the sample users.")
    else:
        print("Database initialization cancelled.")