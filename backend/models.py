from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    url_norm = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    publisher = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary_text = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=True)


class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True)
    headline = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackgroundLink(Base):
    __tablename__ = "background_links"

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False)


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True)
    story_id = Column(Integer, ForeignKey("stories.id"), unique=True, nullable=False)
    input_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    overview = Column(String, nullable=True)
    agreement = Column(String, nullable=True)
    uncertainty = Column(String, nullable=True)
    perspectives_json = Column(JSON, nullable=True)
    citations_json = Column(JSON, nullable=True)
    model = Column(String, nullable=True)
    prompt_version = Column(Integer, nullable=True)
    generated_at = Column(DateTime, nullable=True)


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="running")
    trigger = Column(String, nullable=False)
    articles_fetched = Column(Integer, nullable=False, default=0)
    articles_new = Column(Integer, nullable=False, default=0)
    articles_expired = Column(Integer, nullable=False, default=0)
    ai_calls = Column(Integer, nullable=False, default=0)
    errors_json = Column(JSON, nullable=True)
