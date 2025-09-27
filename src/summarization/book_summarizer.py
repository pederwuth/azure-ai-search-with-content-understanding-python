"""
Progressive book summarization using sequential chapter analysis.

This module provides the core business logic for creating comprehensive 
book summaries through progressive chapter-by-chapter analysis.
Matches the exact implementation from book_summary_generator.ipynb
"""

import logging
import re
import json
import tiktoken
from typing import List, Dict, Any
from datetime import datetime
import time

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

from .models import BookChapter, ChapterSummary, BookSummary
from .prompts import CHAPTER_SUMMARY_PROMPT, FINAL_SUMMARY_PROMPT

logger = logging.getLogger(__name__)


class ProgressiveBookSummarizer:
    """Progressive book summarization using sequential chapter analysis."""

    def __init__(self, llm=None):
        """Initialize the summarizer with LLM and tokenizer."""
        if llm is None:
            # Initialize Azure OpenAI LLM if not provided
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            import os

            # Get Azure credentials
            azure_credential = DefaultAzureCredential()
            azure_ad_token_provider = get_bearer_token_provider(
                azure_credential, "https://cognitiveservices.azure.com/.default"
            )

            self.llm = AzureChatOpenAI(
                azure_deployment=os.getenv(
                    "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-5-mini"),
                api_version=os.getenv(
                    "AZURE_OPENAI_CHAT_API_VERSION", "2024-08-01-preview"),
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                azure_ad_token_provider=azure_ad_token_provider
            )
        else:
            self.llm = llm

        # Initialize tokenizer for GPT models
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.chapter_summaries: List[ChapterSummary] = []

        # Setup LangChain prompts
        self.chapter_summary_prompt = CHAPTER_SUMMARY_PROMPT
        self.book_summary_prompt = FINAL_SUMMARY_PROMPT

        logger.info("ProgressiveBookSummarizer initialized")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        return len(self.tokenizer.encode(text))

    def split_into_chapters(self, markdown_content: str) -> List[BookChapter]:
        """Split markdown content into logical chapters.

        This improved implementation properly extracts clean chapter titles.
        """
        print("📖 Splitting document into chapters...")

        # Find all headers using regex that captures both level and content
        header_pattern = r'^(#+)\s+(.+?)(?:\n|$)'
        headers = list(re.finditer(
            header_pattern, markdown_content, flags=re.MULTILINE))

        chapters = []
        chapter_number = 0

        # If no headers found, create artificial chapters
        if not headers:
            print("⚠️  No clear chapter structure found, creating artificial chapters...")
            return self._create_artificial_chapters(markdown_content)

        # Process each header and extract content between headers
        for i, header_match in enumerate(headers):
            header_level = len(header_match.group(1))  # Count # symbols
            raw_title = header_match.group(2).strip()

            # Clean the title by removing HTML comments, figure content, etc.
            clean_title = self._clean_chapter_title(raw_title)

            # Only treat as new chapter if it's a major header (# or ##)
            if header_level <= 2 and clean_title:
                chapter_number += 1

                # Extract content between this header and the next major header
                content_start = header_match.end()

                # Find the end of this chapter (next major header or end of document)
                content_end = len(markdown_content)
                for j in range(i + 1, len(headers)):
                    next_header = headers[j]
                    next_level = len(next_header.group(1))
                    next_clean_title = self._clean_chapter_title(
                        next_header.group(2).strip())

                    if next_level <= 2 and next_clean_title:
                        content_end = next_header.start()
                        break

                # Extract and clean content
                content = markdown_content[content_start:content_end].strip()

                chapter = BookChapter(
                    chapter_number=chapter_number,
                    title=clean_title,
                    content=content,
                    token_count=self.count_tokens(content),
                    page_range=f"Chapter {chapter_number}"
                )
                chapters.append(chapter)

        # If no clear chapters found, create artificial chapters by content length
        if not chapters:
            print("⚠️  No clear chapter structure found, creating artificial chapters...")
            chapters = self._create_artificial_chapters(markdown_content)

        print(f"✅ Found {len(chapters)} chapters")
        for i, chapter in enumerate(chapters, 1):
            print(
                f"   Chapter {i}: {chapter.title[:50]}... ({chapter.token_count:,} tokens)")

        return chapters

    def _clean_chapter_title(self, raw_title: str) -> str:
        """Clean chapter title by removing HTML comments, figure content, and formatting artifacts."""
        if not raw_title:
            return ""

        # Remove HTML comments (<!-- ... -->)
        title = re.sub(r'<!--.*?-->', '', raw_title, flags=re.DOTALL)

        # Remove figure content patterns
        title = re.sub(r'FigureContent=".*?"', '', title, flags=re.DOTALL)

        # Remove common markdown artifacts
        title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
        # Remove bold formatting
        title = re.sub(r'\*\*([^*]+)\*\*', r'\1', title)
        # Remove italic formatting
        title = re.sub(r'\*([^*]+)\*', r'\1', title)
        title = re.sub(r'`([^`]+)`', r'\1', title)  # Remove code formatting

        # Clean up whitespace and newlines
        title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
        title = title.strip()

        # Skip titles that are too short or look like artifacts
        if len(title) < 2:
            return ""

        # Skip titles that are just numbers, page references, or common artifacts
        if re.match(r'^\d+$', title):  # Just numbers
            return ""
        if title.lower() in ['pagebreak', 'pageheader', 'pagefooter', 'pagenumber']:
            return ""
        if title.startswith('www.') or 'http' in title.lower():
            return ""

        # Limit title length to reasonable bounds
        if len(title) > 100:
            # Try to find a natural break point
            sentences = title.split('.')
            if len(sentences[0]) < 80:
                title = sentences[0].strip()
            else:
                title = title[:80].strip()

        return title

    def _create_artificial_chapters(self, content: str, target_tokens: int = 15000) -> List[BookChapter]:
        """Create artificial chapters based on content length."""
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
        """Summarize a single chapter with progressive context.

        This matches the exact notebook implementation.
        """
        print(
            f"📝 Summarizing Chapter {chapter.chapter_number}: {chapter.title}")

        # Build context from previous chapters
        previous_context = ""
        if previous_summaries:
            # Use last 2-3 chapters for context to avoid token overflow
            recent_summaries = previous_summaries[-3:]
            previous_context = "\n\n".join([
                f"Chapter {cs.chapter_number}: {cs.summary[:300]}..."
                for cs in recent_summaries
            ])

        # Create the prompt chain
        chapter_summary_chain = self.chapter_summary_prompt | self.llm | StrOutputParser()

        # Generate summary
        response = chapter_summary_chain.invoke({
            "previous_context": previous_context,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.title,
            "chapter_content": chapter.content
        })

        try:
            # Parse JSON response
            chapter_data = json.loads(response)

            chapter_summary = ChapterSummary(
                chapter_number=chapter.chapter_number,
                chapter_title=chapter.title,
                summary=chapter_data.get("chapter_summary", ""),
                key_concepts=chapter_data.get("key_concepts", []),
                main_topics=chapter_data.get("main_topics", []),
                token_count=self.count_tokens(response),
                created_at=datetime.now()
            )

            print(f"✅ Chapter {chapter.chapter_number} summarized")
            return chapter_summary

        except json.JSONDecodeError as e:
            print(
                f"⚠️  JSON parsing failed for Chapter {chapter.chapter_number}, using raw response")
            return ChapterSummary(
                chapter_number=chapter.chapter_number,
                chapter_title=chapter.title,
                summary=response,
                key_concepts=[],
                main_topics=[],
                token_count=self.count_tokens(response),
                created_at=datetime.now()
            )

    def create_final_book_summary(self, chapter_summaries: List[ChapterSummary], book_title: str = "Document Summary") -> BookSummary:
        """Create comprehensive book summary from all chapter summaries.

        This matches the exact notebook implementation.
        """
        print("📚 Creating final book summary from all chapters...")

        # Compile all chapter summaries
        all_summaries_text = "\n\n".join([
            f"**Chapter {cs.chapter_number}: {cs.chapter_title}**\n{cs.summary}\nKey Concepts: {', '.join(cs.key_concepts)}"
            for cs in chapter_summaries
        ])

        # Generate final book summary
        book_summary_chain = self.book_summary_prompt | self.llm | StrOutputParser()

        response = book_summary_chain.invoke({
            "all_chapter_summaries": all_summaries_text
        })

        try:
            book_data = json.loads(response)

            book_summary = BookSummary(
                book_title=book_data.get("book_title", book_title),
                overall_summary=book_data.get("overall_summary", ""),
                chapter_summaries=chapter_summaries,
                key_themes=book_data.get("key_themes", []),
                learning_objectives=book_data.get("learning_objectives", []),
                total_chapters=len(chapter_summaries),
                created_at=datetime.now()
            )

            print(f"✅ Book summary created: {book_summary.book_title}")
            print(f"   Total chapters: {book_summary.total_chapters}")
            print(f"   Key themes: {len(book_summary.key_themes)}")

            return book_summary

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parsing failed for book summary, using raw response")
            return BookSummary(
                book_title=book_title,
                overall_summary=response,
                chapter_summaries=chapter_summaries,
                key_themes=[],
                learning_objectives=[],
                total_chapters=len(chapter_summaries),
                created_at=datetime.now()
            )

    def process_document_progressively(self, markdown_content: str, book_title: str = "Document Summary") -> BookSummary:
        """Process entire book with progressive summarization.

        This is the main method that matches the notebook workflow.
        """
        print("🚀 Starting progressive book summarization...")
        start_time = time.time()

        # Step 1: Split into chapters
        chapters = self.split_into_chapters(markdown_content)

        # Step 2: Progressive summarization
        chapter_summaries = []

        for chapter in chapters:
            chapter_summary = self.summarize_chapter_progressively(
                chapter, chapter_summaries)
            chapter_summaries.append(chapter_summary)

        # Step 3: Create final book summary
        book_summary = self.create_final_book_summary(
            chapter_summaries, book_title)

        processing_time = time.time() - start_time
        print(
            f"🎉 Progressive summarization completed in {processing_time:.2f}s")

        return book_summary
