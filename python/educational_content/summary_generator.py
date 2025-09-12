"""
Summary Generator for Educational Content

This module generates various types of summaries from document chunks
using Azure OpenAI GPT-5 for comprehensive educational content creation.
"""

from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
import asyncio
from openai import AsyncAzureOpenAI

logger = logging.getLogger(__name__)

class SummaryGenerator:
    """
    Generates educational summaries using Azure OpenAI GPT-5.
    
    Leverages GPT-5's massive context window (272K input tokens) for 
    comprehensive analysis and summary generation.
    """
    
    def __init__(self, 
                 azure_openai_client: AsyncAzureOpenAI,
                 model_name: str = "gpt-5-mini",
                 max_summary_length: int = 2000):
        """
        Initialize the summary generator.
        
        Args:
            azure_openai_client: Configured Azure OpenAI client
            model_name: GPT model to use (default: gpt-5-mini)
            max_summary_length: Maximum length for summaries in tokens
        """
        self.client = azure_openai_client
        self.model_name = model_name
        self.max_summary_length = max_summary_length
        
        # Summary templates for different types
        self.summary_templates = {
            "chapter": {
                "system_prompt": """You are an expert educational content creator. Generate a comprehensive chapter summary that helps students understand key concepts, main ideas, and important details. Focus on learning objectives and educational value.""",
                "user_template": """Please create a detailed chapter summary for the following content. Include:

1. **Main Topic/Theme**: What is this chapter about?
2. **Key Concepts**: List 3-5 most important concepts covered
3. **Main Points**: Detailed explanation of core ideas
4. **Important Details**: Supporting facts, examples, or data
5. **Learning Objectives**: What should students learn from this chapter?
6. **Connections**: How does this relate to broader topics?

Content to summarize:
{content}

Generate a comprehensive summary that would help a student understand and study this material effectively."""
            },
            
            "section": {
                "system_prompt": """You are an expert educational content creator. Generate a focused section summary that highlights the specific topic and its key points for effective studying.""",
                "user_template": """Please create a focused section summary for the following content. Include:

1. **Section Topic**: What specific topic does this section cover?
2. **Key Points**: 2-4 main points from this section
3. **Supporting Details**: Important examples, facts, or explanations
4. **Study Notes**: What should students pay special attention to?

Content to summarize:
{content}

Generate a clear, concise summary that captures the essential information from this section."""
            },
            
            "overview": {
                "system_prompt": """You are an expert educational content creator. Generate a high-level overview that provides context and big-picture understanding of the content.""",
                "user_template": """Please create a high-level overview for the following content. Include:

1. **Overall Theme**: What is the main subject or topic?
2. **Scope**: What areas or aspects are covered?
3. **Key Takeaways**: Most important insights or conclusions
4. **Context**: Where does this fit in the broader subject area?

Content to summarize:
{content}

Generate an overview that gives students a clear understanding of what this content covers and why it's important."""
            }
        }
    
    async def generate_summary(self, 
                              chunk_content: str, 
                              summary_type: str = "chapter",
                              custom_instructions: Optional[str] = None,
                              metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a summary for a content chunk.
        
        Args:
            chunk_content: The content to summarize
            summary_type: Type of summary ("chapter", "section", "overview")
            custom_instructions: Optional custom instructions for the summary
            metadata: Optional metadata about the content
            
        Returns:
            Dictionary containing the generated summary and metadata
        """
        try:
            # Get appropriate template
            template = self.summary_templates.get(summary_type, self.summary_templates["chapter"])
            
            # Prepare the prompt
            if custom_instructions:
                user_prompt = f"{custom_instructions}\n\nContent to summarize:\n{chunk_content}"
            else:
                user_prompt = template["user_template"].format(content=chunk_content)
            
            # Generate summary using Azure OpenAI
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": template["system_prompt"]},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_summary_length,
                temperature=0.3,  # Slightly creative but focused
                top_p=0.9
            )
            
            summary_text = response.choices[0].message.content
            
            # Create summary metadata
            summary_metadata = {
                "summary_id": f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "summary_type": summary_type,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
                "source_chunk_id": metadata.get("chunk_id") if metadata else "unknown",
                "source_document": metadata.get("source") if metadata else "unknown",
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "content_length": len(chunk_content),
                "summary_length": len(summary_text)
            }
            
            return {
                "summary": summary_text,
                "metadata": summary_metadata,
                "source_metadata": metadata or {}
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "metadata": {
                    "error": True,
                    "error_message": str(e),
                    "summary_type": summary_type,
                    "generated_at": datetime.now().isoformat()
                },
                "source_metadata": metadata or {}
            }
    
    async def generate_batch_summaries(self, 
                                     chunks: List[Dict[str, Any]], 
                                     summary_type: str = "chapter",
                                     max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple chunks concurrently.
        
        Args:
            chunks: List of content chunks to summarize
            summary_type: Type of summary to generate
            max_concurrent: Maximum concurrent API calls
            
        Returns:
            List of generated summaries
        """
        logger.info(f"Generating {len(chunks)} summaries of type '{summary_type}'")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(chunk):
            async with semaphore:
                return await self.generate_summary(
                    chunk["content"], 
                    summary_type, 
                    metadata=chunk["metadata"]
                )
        
        # Generate all summaries concurrently
        tasks = [generate_with_semaphore(chunk) for chunk in chunks]
        summaries = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        valid_summaries = []
        for i, summary in enumerate(summaries):
            if isinstance(summary, Exception):
                logger.error(f"Error in summary {i}: {str(summary)}")
                valid_summaries.append({
                    "summary": f"Error generating summary: {str(summary)}",
                    "metadata": {
                        "error": True,
                        "error_message": str(summary),
                        "chunk_index": i
                    }
                })
            else:
                valid_summaries.append(summary)
        
        logger.info(f"Successfully generated {len(valid_summaries)} summaries")
        return valid_summaries
    
    def create_summary_collection(self, 
                                summaries: List[Dict[str, Any]], 
                                document_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a structured collection of summaries with metadata.
        
        Args:
            summaries: List of generated summaries
            document_metadata: Optional metadata about the source document
            
        Returns:
            Structured summary collection
        """
        collection_metadata = {
            "collection_id": f"summary_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "created_at": datetime.now().isoformat(),
            "total_summaries": len(summaries),
            "document_source": document_metadata.get("source") if document_metadata else "unknown",
            "summary_types": list(set(s["metadata"]["summary_type"] for s in summaries if "metadata" in s)),
            "total_tokens_used": sum(
                s["metadata"].get("token_usage", {}).get("total_tokens", 0) 
                for s in summaries if "metadata" in s and not s["metadata"].get("error")
            )
        }
        
        return {
            "collection_metadata": collection_metadata,
            "document_metadata": document_metadata or {},
            "summaries": summaries
        }
    
    def get_summary_statistics(self, summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about generated summaries.
        
        Args:
            summaries: List of summaries to analyze
            
        Returns:
            Summary statistics
        """
        if not summaries:
            return {"error": "No summaries provided"}
        
        valid_summaries = [s for s in summaries if not s.get("metadata", {}).get("error")]
        error_count = len(summaries) - len(valid_summaries)
        
        if not valid_summaries:
            return {
                "total_summaries": len(summaries),
                "valid_summaries": 0,
                "error_count": error_count,
                "error_rate": 1.0
            }
        
        # Calculate statistics
        summary_lengths = [len(s["summary"]) for s in valid_summaries]
        token_usage = [
            s["metadata"].get("token_usage", {}).get("total_tokens", 0) 
            for s in valid_summaries
        ]
        
        summary_types = {}
        for summary in valid_summaries:
            summary_type = summary["metadata"]["summary_type"]
            summary_types[summary_type] = summary_types.get(summary_type, 0) + 1
        
        return {
            "total_summaries": len(summaries),
            "valid_summaries": len(valid_summaries),
            "error_count": error_count,
            "error_rate": error_count / len(summaries),
            "summary_types": summary_types,
            "content_length": {
                "min": min(summary_lengths),
                "max": max(summary_lengths),
                "average": sum(summary_lengths) / len(summary_lengths)
            },
            "token_usage": {
                "total": sum(token_usage),
                "average_per_summary": sum(token_usage) / len(token_usage) if token_usage else 0,
                "min": min(token_usage) if token_usage else 0,
                "max": max(token_usage) if token_usage else 0
            }
        }
