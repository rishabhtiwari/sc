#!/usr/bin/env python3
"""
Test script for YouTube Metadata Builder
Shows example output for different news categories
"""

from services.metadata_builder import YouTubeMetadataBuilder

# Sample news documents
sample_news = [
    {
        'title': 'Stock Market Hits All-Time High as Sensex Crosses 70,000 Mark',
        'short_summary': 'Indian stock markets reached a historic milestone today as the BSE Sensex crossed the 70,000 mark for the first time, driven by strong corporate earnings and positive global cues.',
        'description': 'The Indian stock market witnessed a historic moment as the BSE Sensex crossed the 70,000 mark for the first time in its history. The rally was led by banking and IT stocks, with investors showing strong confidence in the Indian economy.',
        'category': 'business',
        'source': {'name': 'Economic Times'},
        'publishedAt': '2024-11-24T10:30:00Z'
    },
    {
        'title': 'India Wins Cricket World Cup Final Against Australia',
        'short_summary': 'India clinched the Cricket World Cup title with a thrilling 6-wicket victory over Australia in the final match at Wankhede Stadium, Mumbai.',
        'description': 'In a nail-biting finish, Team India defeated Australia by 6 wickets to win the Cricket World Cup. Captain Rohit Sharma led from the front with a brilliant century.',
        'category': 'sports',
        'source': {'name': 'ESPN Cricinfo'},
        'publishedAt': '2024-11-24T18:45:00Z'
    },
    {
        'title': 'New AI Technology Revolutionizes Healthcare Diagnosis',
        'short_summary': 'Scientists develop groundbreaking AI system that can detect diseases with 99% accuracy, potentially transforming medical diagnostics worldwide.',
        'description': 'A team of researchers has developed an advanced AI system capable of diagnosing multiple diseases with unprecedented accuracy. The technology uses deep learning algorithms to analyze medical images and patient data.',
        'category': 'technology',
        'source': {'name': 'Tech Crunch'},
        'publishedAt': '2024-11-24T14:20:00Z'
    }
]


def test_metadata_builder():
    """Test the metadata builder with sample news"""
    builder = YouTubeMetadataBuilder()
    
    print("=" * 80)
    print("YOUTUBE METADATA BUILDER - TEST OUTPUT")
    print("=" * 80)
    print()
    
    for idx, news in enumerate(sample_news, 1):
        print(f"\n{'=' * 80}")
        print(f"EXAMPLE {idx}: {news['category'].upper()} NEWS")
        print(f"{'=' * 80}\n")
        
        # Build metadata
        metadata = builder.build_metadata(news)
        
        # Display results
        print(f"📌 ORIGINAL TITLE:")
        print(f"   {news['title']}")
        print()
        
        print(f"✨ OPTIMIZED TITLE ({len(metadata['title'])} chars):")
        print(f"   {metadata['title']}")
        print()
        
        print(f"📝 DESCRIPTION ({len(metadata['description'])} chars):")
        print("-" * 80)
        print(metadata['description'])
        print("-" * 80)
        print()
        
        print(f"🏷️  TAGS ({len(metadata['tags'])} tags):")
        for i, tag in enumerate(metadata['tags'], 1):
            print(f"   {i}. {tag}")
        print()
        
        print(f"📊 METADATA SUMMARY:")
        print(f"   - Title length: {len(metadata['title'])}/100 chars")
        print(f"   - Description length: {len(metadata['description'])}/5000 chars")
        print(f"   - Number of tags: {len(metadata['tags'])}")
        print(f"   - Total tags length: {sum(len(t) for t in metadata['tags'])} chars")
        print()


if __name__ == '__main__':
    test_metadata_builder()

