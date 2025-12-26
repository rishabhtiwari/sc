# Content Generation Components

Reusable React components for AI-powered content generation workflows.

## Components

### 1. AIContentGenerator

Generic component for AI content generation (summaries, articles, social posts, etc.)

**Props:**
- `endpoint` (string, required): API endpoint for content generation
- `inputData` (object): Data to send to the endpoint
- `initialContent` (string): Initial content value
- `onContentGenerated` (function): Callback when content is generated
- `onContentChange` (function): Callback when content is edited
- `label` (string): Label for the content area
- `placeholder` (string): Placeholder text
- `showEditMode` (boolean): Show edit/preview toggle
- `showSections` (boolean): Parse and show content as sections (uses default markdown parser)
- `parseContent` (function): Custom parser for content sections (optional - uses default if not provided)

**Default Section Parser:**
The component includes a built-in parser that handles markdown-style sections:
```
## Section Title 1
Content for section 1...

## Section Title 2
Content for section 2...
```

**Example (Basic):**
```jsx
import { AIContentGenerator } from '@/components/common';

<AIContentGenerator
  endpoint="/api/products/123/generate-summary"
  inputData={{ regenerate: false }}
  initialContent={product.ai_summary}
  onContentGenerated={(content) => setAiSummary(content)}
  label="Product Summary"
  showEditMode={true}
/>
```

**Example (With Sections - Default Parser):**
```jsx
<AIContentGenerator
  endpoint="/api/products/123/generate-summary"
  initialContent={product.ai_summary}
  onContentGenerated={(content) => setAiSummary(content)}
  label="Product Summary"
  showEditMode={true}
  showSections={true}  // Automatically uses default markdown parser
/>
```

**Example (With Custom Parser):**
```jsx
<AIContentGenerator
  endpoint="/api/articles/generate"
  onContentGenerated={(content) => setContent(content)}
  showSections={true}
  parseContent={(text) => {
    // Custom parser for different format
    return text.split('\n\n').map(section => ({
      title: section.split('\n')[0],
      content: section.split('\n').slice(1).join('\n')
    }));
  }}
/>
```

### 2. AudioSelector

Component for TTS audio generation with model/voice selection

**Props:**
- `endpoint` (string, required): API endpoint for audio generation
- `text` (string): Text to convert to speech
- `initialAudioUrl` (string): Initial audio URL
- `initialConfig` (object): Initial audio config (model, language, voice)
- `onAudioGenerated` (function): Callback when audio is generated
- `onConfigChange` (function): Callback when config changes
- `autoDetectLanguage` (boolean): Auto-detect language from text
- `showAdvancedOptions` (boolean): Show advanced options

**Example:**
```jsx
import { AudioSelector } from '@/components/common';

<AudioSelector
  endpoint="/api/products/123/generate-audio"
  text={aiSummary}
  initialAudioUrl={product.audio_url}
  initialConfig={{
    model: 'kokoro-82m',
    language: 'en',
    voice: 'am_adam'
  }}
  onAudioGenerated={(url, config) => {
    setAudioUrl(url);
    setAudioConfig(config);
  }}
  autoDetectLanguage={true}
/>
```

### 3. TemplateSelector

Component for template selection and variable configuration

**Props:**
- `initialTemplateId` (string): Initial selected template ID
- `initialVariables` (object): Initial template variables
- `onTemplateSelected` (function): Callback when template is selected
- `onVariablesChange` (function): Callback when variables change
- `showVariables` (boolean): Show variable configuration
- `showPreview` (boolean): Show template preview
- `filterCategory` (string): Filter templates by category

**Example:**
```jsx
import { TemplateSelector } from '@/components/common';

<TemplateSelector
  initialTemplateId={product.template_id}
  initialVariables={product.template_variables}
  onTemplateSelected={(templateId, template) => {
    setSelectedTemplate(templateId);
  }}
  onVariablesChange={(variables) => {
    setTemplateVariables(variables);
  }}
  showVariables={true}
  showPreview={true}
  filterCategory="ecommerce"
/>
```

### 4. MediaUploader

Component for image/video uploads with preview

**Props:**
- `initialFiles` (array): Initial media files
- `onFilesChange` (function): Callback when files change
- `uploadEndpoint` (string): API endpoint for file upload
- `acceptedTypes` (array): Accepted file types ['image', 'video']
- `maxFiles` (number): Maximum number of files
- `maxFileSize` (number): Maximum file size in MB
- `showPreview` (boolean): Show file previews

**Example:**
```jsx
import { MediaUploader } from '@/components/common';

<MediaUploader
  initialFiles={product.media_files}
  onFilesChange={(files) => setMediaFiles(files)}
  uploadEndpoint="/api/upload"
  acceptedTypes={['image', 'video']}
  maxFiles={10}
  maxFileSize={100}
  showPreview={true}
/>
```

## Hooks

### useContentGeneration

Hook for AI content generation

**Returns:**
- `generating` (boolean): Whether content is being generated
- `content` (string): Generated content
- `error` (string): Error message
- `generate` (function): Generate content
- `generateWithLLM` (function): Generate content directly with LLM
- `reset` (function): Reset hook state
- `setContent` (function): Set content manually

**Example:**
```jsx
import { useContentGeneration } from '@/hooks/useContentGeneration';

const { generating, content, generate } = useContentGeneration();

const handleGenerate = async () => {
  await generate({
    endpoint: '/api/llm/generate',
    data: { query: 'Write a product description' },
    onSuccess: (content) => console.log(content),
    onError: (error) => console.error(error)
  });
};
```

### useTemplates

Hook for template management

**Returns:**
- `templates` (array): All templates
- `selectedTemplate` (string): Selected template ID
- `selectedTemplateDetails` (object): Selected template details
- `loading` (boolean): Whether templates are loading
- `error` (string): Error message
- `selectTemplate` (function): Select a template
- `getTemplateVariables` (function): Get template variables
- `getTemplateSections` (function): Get template sections

### useAudioGeneration

Hook for audio generation

**Returns:**
- `generating` (boolean): Whether audio is being generated
- `audioUrl` (string): Generated audio URL
- `audioConfig` (object): Audio configuration
- `error` (string): Error message
- `generate` (function): Generate audio
- `previewVoice` (function): Preview a voice
- `detectLanguage` (function): Auto-detect language from text

## Complete Example: Product Video Wizard

See `examples/ProductVideoWizardRefactored.jsx` for a complete example of using all components together.

