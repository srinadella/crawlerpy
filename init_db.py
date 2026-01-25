"""Database initialization with sample data."""

from app.models import Base, engine, SessionLocal, User, CrawlerConfig
from app.auth import hash_password
from datetime import datetime


def init_db():
    """Initialize database and create sample data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if sample users already exist
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Database already initialized with sample data")
            return
        
        # Create sample users
        users = [
            User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                roles=["admin", "editor", "viewer"],
                is_active=True
            ),
            User(
                username="editor",
                email="editor@example.com",
                hashed_password=hash_password("editor123"),
                roles=["editor", "viewer"],
                is_active=True
            ),
            User(
                username="viewer",
                email="viewer@example.com",
                hashed_password=hash_password("viewer123"),
                roles=["viewer"],
                is_active=True
            ),
        ]
        
        for user in users:
            db.add(user)
        
        db.commit()
        print(f"Created {len(users)} sample users")
        
        # Create sample crawler configurations
        crawlers = [
            CrawlerConfig(
                name="Example Site",
                description="Example website crawler",
                enabled=True,
                seed_urls=["https://example.com"],
                allow_domains=["example.com"],
                url_patterns_include=[],
                url_patterns_exclude=[".*login.*", ".*logout.*"],
                follow_sitemap=True,
                respect_robots_txt=True,
                max_depth=2,
                download_timeout=30,
                concurrent_requests=16,
                concurrent_requests_per_domain=8,
                download_delay=1,
                extract_pdfs=True,
                extract_docx=True,
                opensearch_index_name="crawler_example_site",
                enable_indexing=True,
                create_json_collection=True
            ),
            CrawlerConfig(
                name="Documentation Site",
                description="Documentation website crawler",
                enabled=True,
                seed_urls=["https://docs.example.com"],
                allow_domains=["docs.example.com"],
                url_patterns_include=[".*docs.*"],
                url_patterns_exclude=[],
                follow_sitemap=True,
                respect_robots_txt=True,
                max_depth=3,
                download_timeout=30,
                concurrent_requests=16,
                concurrent_requests_per_domain=8,
                download_delay=1,
                extract_pdfs=True,
                extract_docx=True,
                opensearch_index_name="crawler_documentation_site",
                enable_indexing=True,
                create_json_collection=True
            ),
        ]
        
        for crawler in crawlers:
            db.add(crawler)
        
        db.commit()
        print(f"Created {len(crawlers)} sample crawler configurations")
        
        print("Database initialization complete!")
    
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
