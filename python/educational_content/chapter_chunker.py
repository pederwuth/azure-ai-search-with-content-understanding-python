"""
Chapter Chunking Strategy for Educational Content

This module implements large chunk extraction for educational content generation,
leveraging GPT-5's massive 272K input token capacity for rich content analysis.
"""

from typing import List, Dict, Any, Optional
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

class ChapterChunker:
    """
    Advanced chunking strategy for educational content generation.
    
    Creates dual chunking approach:
    - Small chunks (512 chars) for search/retrieval
    - Large chunks (chapter-based) for educational content generation
    """
    
    def __init__(self, 
                 max_chapter_tokens: int = 200000,  # Conservative limit for GPT-5 input
                 overlap_ratio: float = 0.1):
        """
        Initialize the chapter chunker.
        
        Args:
            max_chapter_tokens: Maximum tokens per educational chunk (default: 200K for GPT-5)
            overlap_ratio: Overlap ratio between chunks (default: 10%)
        """
        self.max_chapter_tokens = max_chapter_tokens
        self.overlap_ratio = overlap_ratio
        
        # Configure header-based splitter for chapter detection
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
            ]
        )
        
        # Fallback character-based splitter for large chapters
        self.char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chapter_tokens * 4,  # Rough token-to-char conversion
            chunk_overlap=int(self.max_chapter_tokens * 4 * self.overlap_ratio),
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def create_educational_chunks(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Create large educational chunks from document content.
        
        Args:
            content: Enhanced markdown content from document processing
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of educational chunks with metadata
        """
        try:
            # First, split by headers to identify chapters/sections
            header_chunks = self.header_splitter.split_text(content)
            
            educational_chunks = []
            
            for i, chunk in enumerate(header_chunks):
                chunk_metadata = {
                    "chunk_id": f"edu_chunk_{i}",
                    "chunk_type": "educational",
                    "source": metadata.get("source", "unknown") if metadata else "unknown",
                    "headers": chunk.metadata if hasattr(chunk, 'metadata') else {},
                    "token_estimate": len(chunk.page_content) // 4 if hasattr(chunk, 'page_content') else len(str(chunk)) // 4
                }
                
                chunk_content = chunk.page_content if hasattr(chunk, 'page_content') else str(chunk)
                
                # If chunk is too large, split further
                if chunk_metadata["token_estimate"] > self.max_chapter_tokens:
                    logger.info(f"Large chunk detected ({chunk_metadata['token_estimate']} tokens), splitting further")
                    sub_chunks = self.char_splitter.split_text(chunk_content)
                    
                    for j, sub_chunk in enumerate(sub_chunks):
                        sub_metadata = chunk_metadata.copy()
                        sub_metadata["chunk_id"] = f"edu_chunk_{i}_{j}"
                        sub_metadata["token_estimate"] = len(sub_chunk) // 4
                        sub_metadata["is_sub_chunk"] = True
                        sub_metadata["parent_chunk"] = f"edu_chunk_{i}"
                        
                        educational_chunks.append({
                            "content": sub_chunk,
                            "metadata": sub_metadata
                        })
                else:
                    educational_chunks.append({
                        "content": chunk_content,
                        "metadata": chunk_metadata
                    })
            
            logger.info(f"Created {len(educational_chunks)} educational chunks")
            return educational_chunks
            
        except Exception as e:
            logger.error(f"Error creating educational chunks: {str(e)}")
            # Fallback to character-based chunking
            return self._fallback_chunking(content, metadata)
    
    def _fallback_chunking(self, content: str, metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Fallback chunking strategy using character-based splitting.
        
        Args:
            content: Document content
            metadata: Optional metadata
            
        Returns:
            List of educational chunks
        """
        logger.info("Using fallback chunking strategy")
        
        chunks = self.char_splitter.split_text(content)
        educational_chunks = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "chunk_id": f"edu_fallback_{i}",
                "chunk_type": "educational_fallback",
                "source": metadata.get("source", "unknown") if metadata else "unknown",
                "token_estimate": len(chunk) // 4,
                "is_fallback": True
            }
            
            educational_chunks.append({
                "content": chunk,
                "metadata": chunk_metadata
            })
        
        return educational_chunks
    
    def get_chunk_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get summary information about the chunks created.
        
        Args:
            chunks: List of educational chunks
            
        Returns:
            Summary statistics
        """
        total_chunks = len(chunks)
        total_tokens = sum(chunk["metadata"]["token_estimate"] for chunk in chunks)
        avg_tokens = total_tokens / total_chunks if total_chunks > 0 else 0
        
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk["metadata"]["chunk_type"]
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_estimated_tokens": total_tokens,
            "average_tokens_per_chunk": avg_tokens,
            "chunk_types": chunk_types,
            "max_tokens_per_chunk": max(chunk["metadata"]["token_estimate"] for chunk in chunks) if chunks else 0,
            "min_tokens_per_chunk": min(chunk["metadata"]["token_estimate"] for chunk in chunks) if chunks else 0
        }
