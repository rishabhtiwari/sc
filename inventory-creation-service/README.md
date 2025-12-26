# Inventory Creation Service

**Formerly:** E-commerce Service  
**Purpose:** Generic content generation service with reusable base classes for multiple use cases

## 🎯 Architecture Overview

This service provides a **reusable, extensible framework** for AI-powered content generation across different use cases (products, social media, blogs, etc.).

### Key Design Principles

1. **Base Class Pattern**: Common functionality in `BaseContentGenerator`
2. **Workflow Inheritance**: Specific use cases extend the base class
3. **Prompt Templates**: Centralized, reusable prompt management
4. **Shared Utilities**: Common functions used across all workflows

## 📁 Directory Structure

```
inventory-creation-service/
├── common/                      # Shared base classes & utilities
│   ├── __init__.py
│   ├── base_content_generator.py   # Abstract base class
│   └── utils.py                    # Shared utility functions
│
├── workflows/                   # Specific implementations
│   ├── __init__.py
│   ├── product_workflow.py         # Product video generation
│   ├── social_media_workflow.py    # Future: Social media posts
│   └── blog_workflow.py            # Future: Blog articles
│
├── prompts/                     # Prompt templates
│   ├── __init__.py
│   ├── product_prompts.py          # Product-specific prompts
│   ├── social_media_prompts.py     # Future
│   └── blog_prompts.py             # Future
│
├── app.py                       # Flask application & routes
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🏗️ Base Class: `BaseContentGenerator`

The foundation for all content generation workflows.

### Provides Default Implementations For:

- ✅ **AI Summary Generation** - Calls LLM service with prompts
- ✅ **Summary Parsing** - Converts AI text into structured sections
- ✅ **Audio Generation** - Generates TTS audio for each section
- ✅ **Template Selection** - Selects appropriate video templates
- ✅ **Video Orchestration** - Coordinates video generation

### Abstract Methods (Must Override):

```python
def get_default_prompt_template(self) -> str:
    """Return the prompt template for this content type"""
    
def get_content_type(self) -> str:
    """Return content type identifier (e.g., 'product_video')"""
    
def build_prompt_context(self, content_id) -> dict:
    """Build context data for prompt formatting"""
```

### Optional Methods (Can Override):

```python
def parse_summary_to_sections(self, summary_text):
    """Custom parsing logic if needed"""
    
def get_audio_config_for_section(self, section_title, index, total):
    """Custom audio configuration"""
```

## 🎨 Example: Product Workflow

```python
from workflows import ProductWorkflow
from pymongo import MongoClient

# Initialize
db = MongoClient()['news']
product_workflow = ProductWorkflow(
    db_collection=db['products'],
    config={
        'llm_service_url': 'http://llm-service:8083',
        'audio_service_url': 'http://audio-service:3000'
    }
)

# Generate AI summary
result = product_workflow.generate_ai_summary(
    content_id='product_123',
    custom_prompt=None,  # Uses default product prompt
    regenerate=False
)

# Generate audio for sections
audio_result = product_workflow.generate_audio_for_sections(
    content_id='product_123',
    audio_config={
        'voice': 'am_adam',
        'model': 'kokoro-82m',
        'language': 'en'
    }
)
```

## 🚀 Adding New Use Cases

To add a new content type (e.g., Social Media Posts):

### 1. Create Prompt Template

```python
# prompts/social_media_prompts.py
SOCIAL_POST_PROMPT = """Create an engaging social media post about:
Topic: {topic}
Platform: {platform}
Tone: {tone}
..."""
```

### 2. Create Workflow Class

```python
# workflows/social_media_workflow.py
from common.base_content_generator import BaseContentGenerator
from prompts.social_media_prompts import SOCIAL_POST_PROMPT

class SocialMediaWorkflow(BaseContentGenerator):
    def get_content_type(self):
        return "social_post"
    
    def get_default_prompt_template(self):
        return SOCIAL_POST_PROMPT
    
    def build_prompt_context(self, post_id):
        post = self.collection.find_one({'_id': post_id})
        return {
            'topic': post['topic'],
            'platform': post['platform'],
            'tone': post.get('tone', 'professional')
        }
```

### 3. Use in Flask Routes

```python
# app.py
from workflows import SocialMediaWorkflow

social_workflow = SocialMediaWorkflow(db['social_posts'])

@app.route('/api/social/<post_id>/generate', methods=['POST'])
def generate_social_post(post_id):
    result = social_workflow.generate_ai_summary(post_id)
    return jsonify(result)
```

**That's it!** All the base functionality (AI generation, audio, etc.) is inherited automatically.

## 🔄 Migration from Old Service

The old `ecommerce-service` has been refactored into this new structure:

- ✅ All utility functions moved to `common/utils.py`
- ✅ Product-specific logic moved to `workflows/product_workflow.py`
- ✅ Prompts extracted to `prompts/product_prompts.py`
- ✅ Base functionality abstracted to `common/base_content_generator.py`

## 🎯 Benefits

1. **Code Reuse**: Write once, use for products, social media, blogs, etc.
2. **Consistency**: Same AI generation logic across all use cases
3. **Easy Extension**: Add new use cases in minutes, not hours
4. **Maintainability**: Fix bugs in one place, benefits all workflows
5. **Testability**: Test base class once, all workflows inherit reliability

## 📝 Next Steps

- [ ] Migrate Flask routes to use new workflow classes
- [ ] Update Docker configuration
- [ ] Update frontend API calls
- [ ] Add Social Media workflow
- [ ] Add Blog workflow
- [ ] Add comprehensive tests

