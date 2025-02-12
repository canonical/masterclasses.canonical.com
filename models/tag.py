from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base

class TagCategory(Base):
    __tablename__ = "tag_category"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    # Relationships
    tags = relationship("Tag", back_populates="category")

    def __str__(self):
        return self.name

class Tag(Base):
    __tablename__ = "tag"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    tag_type_id = Column(Integer, ForeignKey('tag_category.id'), nullable=False)

    # Relationships
    category = relationship("TagCategory", back_populates="tags")
    videos = relationship(
        "Video", 
        secondary="video_tags", 
        back_populates="tags",
        cascade="all, delete"
    )

    def __str__(self):
        return self.name