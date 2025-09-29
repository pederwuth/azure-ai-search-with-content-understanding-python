"""
Progressive book summarizer implementation.

Based on the logic from book_summary_generator.ipynb notebook.
Provides progressive chapter-by-chapter summarization with context building.
"""

import re
import json
import logging
import tiktoken
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from .models import BookChapter, ChapterSummary, BookSummary, SummarizationResult
from .prompts import CHAPTER_SUMMARY_PROMPT, BOOK_SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class ProgressiveBookSummarizer:
    """Progressive book summarization using sequential chapter analysis"""
    
    def __init__(self, llm: Optional[AzureChatOpenAI] = None):
        """Initialize the progressive book summarizer"""
        if llm is None:
            # Load Azure OpenAI configuration from environment variables
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
            api_version = os.getenv("AZURE_OPENAI_CHAT_API_VERSION", "2024-08-01-preview")
            
            # Log the configuration being used
            logger.info(f"🔧 Azure OpenAI Configuration:")
            logger.info(f"   Endpoint: {azure_endpoint}")
            logger.info(f"   Deployment: {azure_deployment}")
            logger.info(f"   API Version: {api_version}")
            
            if not azure_endpoint or not azure_deployment:
                logger.error("❌ Missing required Azure OpenAI configuration in environment variables")
                logger.error("   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
                raise ValueError("Missing Azure OpenAI configuration. Please check your .env file.")
            
            # Create Azure CLI token provider for authentication
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            
            self.llm = AzureChatOpenAI(
                azure_endpoint=azure_endpoint,
                azure_deployment=azure_deployment,
                api_version=api_version,
                azure_ad_token_provider=token_provider,
                # temperature=1 is default for GPT-5-mini (custom values not supported)
                model_kwargs={
                    "max_completion_tokens": 4000  # ✅ passed directly to OpenAI for GPT-5-mini
                }
            )
        else:
            self.llm = llm
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.chapter_summaries = []
        
        logger.info("✅ Progressive book summarizer initialized with Azure CLI authentication")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def split_into_chapters(self, markdown_content: str) -> List[BookChapter]:
        """Split markdown content into logical chapters"""
        logger.info("📖 Splitting document into chapters...")
        
        # This is a smart splitter that looks for natural chapter boundaries
        chapter_pattern = r'^(#{1,3})\s+(.+?)$'
        sections = re.split(chapter_pattern, markdown_content, flags=re.MULTILINE)
        
        chapters = []
        current_chapter = None
        chapter_number = 0
        
        i = 0
        while i < len(sections):
            if i + 2 < len(sections) and sections[i+1]:  # Found a header
                header_level = sections[i+1]
                title = sections[i+2].strip()
                content = sections[i+3] if i+3 < len(sections) else ""
                
                # Only treat as new chapter if it's a major header (# or ##)
                if len(header_level) <= 2:  # # or ##
                    if current_chapter:  # Save previous chapter
                        chapters.append(current_chapter)
                    
                    chapter_number += 1
                    current_chapter = BookChapter(
                        chapter_number=chapter_number,
                        title=title,
                        content=content.strip(),
                        token_count=self.count_tokens(content),
                        page_range=f"Chapter {chapter_number}"
                    )
                else:  # Subsection (###), add to current chapter
                    if current_chapter:
                        current_chapter.content += f"\n\n{header_level} {title}\n{content}"
                        current_chapter.token_count = self.count_tokens(current_chapter.content)
                
                i += 4
            else:
                i += 1
        
        # Add the last chapter
        if current_chapter:
            chapters.append(current_chapter)
        
        # If no clear chapters found, create artificial chapters by content length
        if not chapters:
            logger.warning("⚠️  No clear chapter structure found, creating artificial chapters...")
            chapters = self._create_artificial_chapters(markdown_content)
        
        logger.info(f"✅ Found {len(chapters)} chapters")
        for i, chapter in enumerate(chapters, 1):
            logger.info(f"   Chapter {i}: {chapter.title[:50]}... ({chapter.token_count:,} tokens)")
        
        return chapters
    
    def _create_artificial_chapters(self, content: str, target_tokens: int = 15000) -> List[BookChapter]:
        """Create artificial chapters based on content length"""
        words = content.split()
        chapters = []
        chapter_number = 0
        
        # Estimate words per chapter (roughly 4 tokens per word)
        words_per_chapter = target_tokens // 4
        
        for i in range(0, len(words), words_per_chapter):
            chapter_number += 1
            chapter_words = words[i:i + words_per_chapter]
            chapter_content = " ".join(chapter_words)
            
            # Try to find a good title from the first few sentences
            first_sentences = chapter_content[:200].split('. ')
            title = f"Section {chapter_number}: {first_sentences[0][:50]}..."
            
            chapters.append(BookChapter(
                chapter_number=chapter_number,
                title=title,
                content=chapter_content,
                token_count=self.count_tokens(chapter_content),
                page_range=f"Section {chapter_number}"
            ))
        
        return chapters
    
    def summarize_chapter_progressively(self, chapter: BookChapter, previous_summaries: List[ChapterSummary]) -> ChapterSummary:
        """Summarize a chapter with context from previous chapters"""
        
        logger.info(f"📝 Summarizing Chapter {chapter.chapter_number}: {chapter.title[:50]}...")
        
        # Build context from previous summaries
        previous_context = ""
        if previous_summaries:
            context_parts = []
            for prev_summary in previous_summaries:
                context_parts.append(f"**Chapter {prev_summary.chapter_number}**: {prev_summary.summary}")
            previous_context = "\n\n".join(context_parts)
        else:
            previous_context = "This is the first chapter - no previous context available."
        
        # Generate summary with progressive context
        summary_chain = CHAPTER_SUMMARY_PROMPT | self.llm | StrOutputParser()
        
        response = summary_chain.invoke({
            "previous_context": previous_context,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.title,
            "chapter_content": chapter.content
        })
        
        try:
            summary_data = json.loads(response)
            
            chapter_summary = ChapterSummary(
                chapter_number=chapter.chapter_number,
                chapter_title=chapter.title,
                summary=summary_data.get("chapter_summary", ""),
                key_concepts=summary_data.get("key_concepts", []),
                main_topics=summary_data.get("main_topics", []),
                connections_to_previous=summary_data.get("connections_to_previous", ""),
                new_insights=summary_data.get("new_insights", ""),
                token_count=self.count_tokens(summary_data.get("chapter_summary", "")),
                created_at=datetime.now()
            )
            
            logger.info(f"✅ Chapter {chapter.chapter_number} summarized ({chapter_summary.token_count} tokens)")
            logger.info(f"   Key concepts: {', '.join(chapter_summary.key_concepts[:3])}...")
            
            return chapter_summary
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  JSON parsing failed for Chapter {chapter.chapter_number}, using raw response")
            return ChapterSummary(
                chapter_number=chapter.chapter_number,
                chapter_title=chapter.title,
                summary=response,
                key_concepts=[],
                main_topics=[],
                token_count=self.count_tokens(response),
                created_at=datetime.now()
            )
    
    def create_final_book_summary(self, chapter_summaries: List[ChapterSummary]) -> BookSummary:
        """Create comprehensive book summary from all chapter summaries"""
        
        logger.info("📚 Creating final book summary from all chapters...")
        
        # Compile all chapter summaries
        all_summaries_text = "\n\n".join([
            f"**Chapter {cs.chapter_number}: {cs.chapter_title}**\n{cs.summary}\nKey Concepts: {', '.join(cs.key_concepts)}"
            for cs in chapter_summaries
        ])
        
        # Generate final book summary
        book_summary_chain = BOOK_SUMMARY_PROMPT | self.llm | StrOutputParser()
        
        response = book_summary_chain.invoke({
            "all_chapter_summaries": all_summaries_text
        })
        
        try:
            book_data = json.loads(response)
            
            book_summary = BookSummary(
                book_title=book_data.get("book_title", "Document Summary"),
                overall_summary=book_data.get("overall_summary", ""),
                chapter_summaries=chapter_summaries,
                key_themes=book_data.get("key_themes", []),
                learning_objectives=book_data.get("learning_objectives", []),
                book_structure=book_data.get("book_structure", ""),
                target_audience=book_data.get("target_audience", ""),
                practical_applications=book_data.get("practical_applications", ""),
                total_chapters=len(chapter_summaries),
                created_at=datetime.now()
            )
            
            logger.info(f"✅ Book summary created: {book_summary.book_title}")
            logger.info(f"   Total chapters: {book_summary.total_chapters}")
            logger.info(f"   Key themes: {len(book_summary.key_themes)}")
            
            return book_summary
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  JSON parsing failed for book summary, using raw response")
            return BookSummary(
                book_title="Document Summary",
                overall_summary=response,
                chapter_summaries=chapter_summaries,
                key_themes=[],
                learning_objectives=[],
                total_chapters=len(chapter_summaries),
                created_at=datetime.now()
            )
    
    def process_document_progressively(self, markdown_content: str, output_directory: Path, original_filename: str) -> SummarizationResult:
        """Complete progressive book summarization process"""
        
        start_time = datetime.now()
        logger.info("🚀 Starting Progressive Book Summarization")
        logger.info("=" * 60)
        
        # Step 1: Split into chapters
        chapters = self.split_into_chapters(markdown_content)
        
        # Step 2: Progressive chapter summarization
        logger.info("\n📝 Progressive Chapter Summarization")
        logger.info("-" * 40)
        
        chapter_summaries = []
        
        for chapter in chapters:
            # Summarize with context of all previous summaries
            chapter_summary = self.summarize_chapter_progressively(chapter, chapter_summaries)
            chapter_summaries.append(chapter_summary)
            
            logger.info(f"   Context now includes {len(chapter_summaries)} chapters")
        
        # Step 3: Create final book summary
        logger.info("\n📚 Final Book Summary Generation")
        logger.info("-" * 40)
        
        book_summary = self.create_final_book_summary(chapter_summaries)
        
        # Step 4: Save results
        logger.info("\n💾 Saving Results")
        logger.info("-" * 40)
        
        # Create output directory
        output_directory.mkdir(parents=True, exist_ok=True)
        
        # Save main summary file with same naming convention as folder
        folder_name = output_directory.name  # e.g., "venture_deals_(21)-book-summary-20250928_223659-0095c30d"
        summary_file = output_directory / f"{folder_name}.json"
        book_summary.save_to_file(summary_file)
        
        # Save metadata file
        metadata_file = output_directory / "metadata.json"
        processing_time = (datetime.now() - start_time).total_seconds()
        
        metadata = {
            "original_filename": original_filename,
            "processing_started_at": start_time.isoformat(),
            "processing_completed_at": datetime.now().isoformat(),
            "processing_time_seconds": processing_time,
            "total_chapters": len(chapters),
            "total_summaries": len(chapter_summaries),
            "output_directory": str(output_directory)
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"💾 Summary saved to: {summary_file}")
        logger.info(f"📄 Metadata saved to: {metadata_file}")
        
        logger.info("\n🎯 Progressive Summarization Complete!")
        logger.info("=" * 60)
        
        return SummarizationResult(
            book_summary=book_summary,
            output_directory=output_directory,
            summary_file=summary_file,
            metadata_file=metadata_file,
            processing_time_seconds=processing_time
        )