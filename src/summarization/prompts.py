"""
LangChain prompts for book summarization.
Matches the exact prompts from book_summary_generator.ipynb
"""

from langchain.prompts import ChatPromptTemplate


CHAPTER_SUMMARY_PROMPT = ChatPromptTemplate.from_template("""
You are a professional book summarizer creating comprehensive chapter summaries for educational purposes.

CONTEXT FROM PREVIOUS CHAPTERS:
{previous_context}

CURRENT CHAPTER TO SUMMARIZE:
Chapter: {chapter_number}
Title: {chapter_title}
Content:
{chapter_content}

Create a detailed chapter summary that:
1. **Summarizes the main content** - Reference relevant concepts from earlier chapters
2. **Identifies key concepts** - Extract main ideas and important terms
3. **Explains relationships** - Show how this chapter connects to previous content
4. **Highlights progression** - Show how understanding is building

Format as JSON:
{{
    "chapter_summary": "Detailed 2-3 paragraph summary building on previous chapters",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "main_topics": ["topic1", "topic2", "topic3"],
    "connections_to_previous": "How this chapter relates to previous chapters",
    "new_insights": "What new understanding this chapter provides"
}}
""")


FINAL_SUMMARY_PROMPT = ChatPromptTemplate.from_template("""
You are a professional book summarizer creating a comprehensive book summary for educational purposes.

ALL CHAPTER SUMMARIES:
{all_chapter_summaries}

Create a comprehensive book summary that:
1. **Overall narrative** - Summarize the complete content of the book
2. **Key themes** - Identify major themes running through the book
3. **Learning progression** - Show how concepts build throughout
4. **Practical value** - What readers will gain from this book

Format as JSON:
{{
    "book_title": "Inferred or provided book title",
    "overall_summary": "Comprehensive 4-5 paragraph book summary",
    "key_themes": ["theme1", "theme2", "theme3"],
    "learning_objectives": ["objective1", "objective2", "objective3"],
    "book_structure": "How the book is organized and flows",
    "target_audience": "Who would benefit from this book",
    "practical_applications": "How readers can apply this knowledge"
}}
""")
