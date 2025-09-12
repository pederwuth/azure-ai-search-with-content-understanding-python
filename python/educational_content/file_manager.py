"""
Educational File Manager

This module manages file storage and organization for educational content,
including summaries, chunks, and associated metadata.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class EducationalFileManager:
    """
    Manages file storage for educational content with organized structure.
    
    Directory structure:
    /output/educational/
    ├── documents/
    │   └── {document_id}/
    │       ├── metadata.json
    │       ├── chunks/
    │       │   ├── educational_chunks.json
    │       │   └── search_chunks.json
    │       ├── summaries/
    │       │   ├── chapter_summaries.json
    │       │   ├── section_summaries.json
    │       │   └── overview_summaries.json
    │       └── generated/
    │           ├── quizzes/
    │           ├── flashcards/
    │           └── glossaries/
    """
    
    def __init__(self, base_path: str = "/workspaces/azure-ai-search-with-content-understanding-python/output/educational"):
        """
        Initialize the file manager.
        
        Args:
            base_path: Base directory for educational content storage
        """
        self.base_path = Path(base_path)
        self.ensure_base_structure()
    
    def ensure_base_structure(self):
        """Create the base directory structure if it doesn't exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            (self.base_path / "documents").mkdir(exist_ok=True)
            logger.info(f"Educational content directory structure ready at {self.base_path}")
        except Exception as e:
            logger.error(f"Error creating base structure: {str(e)}")
            raise
    
    def create_document_structure(self, document_id: str) -> Path:
        """
        Create directory structure for a specific document.
        
        Args:
            document_id: Unique identifier for the document
            
        Returns:
            Path to the document directory
        """
        doc_path = self.base_path / "documents" / document_id
        
        try:
            # Create main document directory
            doc_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (doc_path / "chunks").mkdir(exist_ok=True)
            (doc_path / "summaries").mkdir(exist_ok=True)
            (doc_path / "generated").mkdir(exist_ok=True)
            (doc_path / "generated" / "quizzes").mkdir(exist_ok=True)
            (doc_path / "generated" / "flashcards").mkdir(exist_ok=True)
            (doc_path / "generated" / "glossaries").mkdir(exist_ok=True)
            
            logger.info(f"Created document structure for {document_id}")
            return doc_path
            
        except Exception as e:
            logger.error(f"Error creating document structure for {document_id}: {str(e)}")
            raise
    
    def save_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Save document metadata.
        
        Args:
            document_id: Document identifier
            metadata: Document metadata to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_path = self.create_document_structure(document_id)
            metadata_file = doc_path / "metadata.json"
            
            # Add timestamp
            metadata["saved_at"] = datetime.now().isoformat()
            metadata["document_id"] = document_id
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved metadata for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving metadata for {document_id}: {str(e)}")
            return False
    
    def save_educational_chunks(self, document_id: str, chunks: List[Dict[str, Any]]) -> bool:
        """
        Save educational chunks for a document.
        
        Args:
            document_id: Document identifier
            chunks: List of educational chunks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_path = self.create_document_structure(document_id)
            chunks_file = doc_path / "chunks" / "educational_chunks.json"
            
            chunk_data = {
                "document_id": document_id,
                "saved_at": datetime.now().isoformat(),
                "total_chunks": len(chunks),
                "chunks": chunks
            }
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(chunks)} educational chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving educational chunks for {document_id}: {str(e)}")
            return False
    
    def save_summaries(self, document_id: str, summaries: List[Dict[str, Any]], summary_type: str = "chapter") -> bool:
        """
        Save summaries for a document.
        
        Args:
            document_id: Document identifier
            summaries: List of generated summaries
            summary_type: Type of summaries (chapter, section, overview)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_path = self.create_document_structure(document_id)
            summary_file = doc_path / "summaries" / f"{summary_type}_summaries.json"
            
            summary_data = {
                "document_id": document_id,
                "summary_type": summary_type,
                "saved_at": datetime.now().isoformat(),
                "total_summaries": len(summaries),
                "summaries": summaries
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(summaries)} {summary_type} summaries for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving {summary_type} summaries for {document_id}: {str(e)}")
            return False
    
    def load_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Load document metadata.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Document metadata or None if not found
        """
        try:
            metadata_file = self.base_path / "documents" / document_id / "metadata.json"
            
            if not metadata_file.exists():
                logger.warning(f"Metadata file not found for document {document_id}")
                return None
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error loading metadata for {document_id}: {str(e)}")
            return None
    
    def load_educational_chunks(self, document_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load educational chunks for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of educational chunks or None if not found
        """
        try:
            chunks_file = self.base_path / "documents" / document_id / "chunks" / "educational_chunks.json"
            
            if not chunks_file.exists():
                logger.warning(f"Educational chunks not found for document {document_id}")
                return None
            
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
            
            return chunk_data.get("chunks", [])
            
        except Exception as e:
            logger.error(f"Error loading educational chunks for {document_id}: {str(e)}")
            return None
    
    def load_summaries(self, document_id: str, summary_type: str = "chapter") -> Optional[List[Dict[str, Any]]]:
        """
        Load summaries for a document.
        
        Args:
            document_id: Document identifier
            summary_type: Type of summaries to load
            
        Returns:
            List of summaries or None if not found
        """
        try:
            summary_file = self.base_path / "documents" / document_id / "summaries" / f"{summary_type}_summaries.json"
            
            if not summary_file.exists():
                logger.warning(f"{summary_type} summaries not found for document {document_id}")
                return None
            
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            return summary_data.get("summaries", [])
            
        except Exception as e:
            logger.error(f"Error loading {summary_type} summaries for {document_id}: {str(e)}")
            return None
    
    def list_documents(self) -> List[str]:
        """
        List all documents in the educational content directory.
        
        Returns:
            List of document IDs
        """
        try:
            documents_dir = self.base_path / "documents"
            if not documents_dir.exists():
                return []
            
            return [d.name for d in documents_dir.iterdir() if d.is_dir()]
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            return []
    
    def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            Dictionary with document information
        """
        doc_path = self.base_path / "documents" / document_id
        
        if not doc_path.exists():
            return {"error": f"Document {document_id} not found"}
        
        info = {
            "document_id": document_id,
            "path": str(doc_path),
            "exists": True,
            "created_at": datetime.fromtimestamp(doc_path.stat().st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(doc_path.stat().st_mtime).isoformat(),
            "contents": {}
        }
        
        # Check for metadata
        metadata_file = doc_path / "metadata.json"
        info["contents"]["metadata"] = metadata_file.exists()
        
        # Check for chunks
        chunks_dir = doc_path / "chunks"
        if chunks_dir.exists():
            info["contents"]["educational_chunks"] = (chunks_dir / "educational_chunks.json").exists()
            info["contents"]["search_chunks"] = (chunks_dir / "search_chunks.json").exists()
        
        # Check for summaries
        summaries_dir = doc_path / "summaries"
        if summaries_dir.exists():
            summary_files = list(summaries_dir.glob("*_summaries.json"))
            info["contents"]["summaries"] = [f.stem.replace("_summaries", "") for f in summary_files]
        else:
            info["contents"]["summaries"] = []
        
        # Check for generated content
        generated_dir = doc_path / "generated"
        if generated_dir.exists():
            info["contents"]["generated"] = {
                "quizzes": list((generated_dir / "quizzes").glob("*.json")) if (generated_dir / "quizzes").exists() else [],
                "flashcards": list((generated_dir / "flashcards").glob("*.json")) if (generated_dir / "flashcards").exists() else [],
                "glossaries": list((generated_dir / "glossaries").glob("*.json")) if (generated_dir / "glossaries").exists() else []
            }
        
        return info
    
    def cleanup_document(self, document_id: str) -> bool:
        """
        Remove all files for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_path = self.base_path / "documents" / document_id
            
            if doc_path.exists():
                import shutil
                shutil.rmtree(doc_path)
                logger.info(f"Cleaned up document {document_id}")
                return True
            else:
                logger.warning(f"Document {document_id} not found for cleanup")
                return False
                
        except Exception as e:
            logger.error(f"Error cleaning up document {document_id}: {str(e)}")
            return False
