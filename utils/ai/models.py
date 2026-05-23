from pydantic import BaseModel


class ChannelAnalytics(BaseModel):
    topic: str
    tone: str
    audience: str
    confidence: int | float


class PostAnalytics(BaseModel):
    summary: str
    mood: str
    main_topic: str
    comment_length_style: str
    recommended_emotion: str
    is_provocative: str
    hidden_meaning: str
    key_entities: list[str]
    confidence: int | float

