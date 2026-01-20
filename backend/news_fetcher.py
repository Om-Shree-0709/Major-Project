"""
News Fetcher Module
Fetches latest news and formats it beautifully for markdown output
"""

import os
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger("news_fetcher")


def get_sandbox_path() -> str:
    """Get the mcp_sandbox directory path"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    sandbox_dir = os.path.join(backend_dir, "mcp_sandbox")
    
    # Create if doesn't exist
    os.makedirs(sandbox_dir, exist_ok=True)
    
    logger.info(f"✅ Sandbox directory: {sandbox_dir}")
    return sandbox_dir


def format_news_as_markdown(news_items: List[Dict[str, Any]], title: str = "Latest News") -> str:
    """Format news items into beautiful markdown"""
    
    md = f"""# {title}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    
    for i, item in enumerate(news_items, 1):
        md += f"## #{i} {item.get('title', 'Untitled')}\n\n"
        
        if item.get('description'):
            md += f"**Summary:** {item['description']}\n\n"
        
        if item.get('source'):
            md += f"📰 **Source:** {item['source']}\n\n"
        
        if item.get('url'):
            md += f"🔗 **Link:** [{item['url']}]({item['url']})\n\n"
        
        if item.get('category'):
            md += f"📁 **Category:** `{item['category']}`\n\n"
        
        md += "---\n\n"
    
    return md


def fetch_bollywood_news() -> List[Dict[str, Any]]:
    """Fetch sample Bollywood and pop culture news"""
    # In a real scenario, this would call an API like NewsAPI or similar
    # For now, we return sample data that represents what would be fetched
    
    news = [
        {
            "title": "Bollywood Icons Shine at International Awards Ceremony",
            "description": "Several Bollywood celebrities took home prestigious international awards at a glittering ceremony, celebrating Indian cinema's global impact.",
            "source": "Entertainment Today",
            "category": "Bollywood",
            "url": "https://example.com/news/1"
        },
        {
            "title": "Upcoming Bollywood Blockbuster Breaks Pre-Release Records",
            "description": "A highly anticipated Bollywood movie starring A-list actors has broken pre-release ticket sale records, with audiences eager to catch the film on opening weekend.",
            "source": "Box Office India",
            "category": "Movies",
            "url": "https://example.com/news/2"
        },
        {
            "title": "Pop Icon Announces Major Collaboration with Bollywood Music Producer",
            "description": "A global pop star has announced a surprise collaboration with a renowned Bollywood music producer, blending Western pop with Indian classical elements.",
            "source": "Music Weekly",
            "category": "Music",
            "url": "https://example.com/news/3"
        },
        {
            "title": "Celebrity Couple Make Red Carpet Debut at Major Film Festival",
            "description": "Bollywood's hottest couple made a stunning appearance at a prestigious international film festival, sparking social media buzz.",
            "source": "Celebrity Gossip Central",
            "category": "Celebrity News",
            "url": "https://example.com/news/4"
        },
        {
            "title": "Bollywood Director to Helm Biggest Budget Film Ever",
            "description": "A renowned Bollywood director has been signed to direct an epic period drama with the biggest budget ever allocated to an Indian film.",
            "source": "Film Industry News",
            "category": "Production",
            "url": "https://example.com/news/5"
        },
        {
            "title": "Pop Culture Trends: Bollywood Fashion Takes Over Global Runways",
            "description": "International fashion designers are increasingly inspired by Bollywood aesthetics, incorporating traditional Indian elements into haute couture collections.",
            "source": "Fashion Forward",
            "category": "Fashion",
            "url": "https://example.com/news/6"
        },
        {
            "title": "Award-Winning Actress Launches New Production House",
            "description": "A celebrated Bollywood actress has launched her own production house, announcing plans to produce content that tells untold stories.",
            "source": "Entertainment News Daily",
            "category": "Bollywood",
            "url": "https://example.com/news/7"
        },
        {
            "title": "Bollywood vs Hollywood: The Box Office Battle Continues",
            "description": "As Bollywood films increasingly compete globally, industry analysts discuss the shifting dynamics between Indian and Hollywood productions.",
            "source": "Industry Analysis",
            "category": "Box Office",
            "url": "https://example.com/news/8"
        }
    ]
    
    logger.info(f"📰 Fetched {len(news)} news items")
    return news


def save_news_to_file(news_items: List[Dict[str, Any]], filename: str = "news.md", title: str = "Latest News") -> tuple[bool, str]:
    """
    Save news items to a markdown file in mcp_sandbox
    
    Returns:
        tuple: (success: bool, file_path: str)
    """
    try:
        sandbox_dir = get_sandbox_path()
        file_path = os.path.join(sandbox_dir, filename)
        
        # Format the news as markdown
        md_content = format_news_as_markdown(news_items, title)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"✅ News saved to: {file_path}")
        logger.info(f"📄 File size: {len(md_content)} bytes")
        
        return True, file_path
        
    except Exception as e:
        logger.error(f"❌ Failed to save news: {str(e)}")
        return False, str(e)
