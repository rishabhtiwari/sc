# Design Editor - Text Feature Implementation Plan
## Canva-Style Text-to-Slides Workflow

## 🎯 Goal
Enable users to create professional text-based slides in Design Editor with:
1. Multiple text input methods (Upload, Paste, AI Generate)
2. Auto-split text into multiple slides
3. Pre-designed text slide templates
4. Rich formatting options (fonts, colors, styles)
5. Multi-page management

---

## 📊 Current Architecture Analysis

### ✅ Existing Services We Can Reuse

1. **Text Studio** (`frontend-server/src/components/DesignEditor/TextStudio/TextStudio.jsx`)
   - ✅ AI text generation
   - ✅ Template-based generation
   - ✅ Text library management
   - **Reuse:** Open as modal from Design Editor

2. **Asset Service** (`asset-service/routes/asset_routes.py`)
   - ✅ File upload endpoint (`POST /api/assets/upload`)
   - ✅ Text preview extraction (lines 142-156)
   - ✅ Document storage in MinIO
   - **Reuse:** Upload .txt files

3. **Design Editor Canvas** (`frontend-server/src/components/DesignEditor/`)
   - ✅ Canvas rendering
   - ✅ Element manipulation
   - ✅ Multi-page support
   - **Extend:** Add text slide templates

---

## 🏗️ Architecture Design

### Component Structure
```
DesignEditor/
├── Sidebar/
│   ├── TextPanel.jsx (NEW) ← Main text panel
│   └── AIToolsPanel.jsx (existing)
├── TextStudio/ (existing, reuse as modal)
├── Canvas/
│   ├── TextSlideTemplates/ (NEW)
│   │   ├── TitleSlide.jsx
│   │   ├── BulletPointSlide.jsx
│   │   ├── QuoteSlide.jsx
│   │   └── TwoColumnSlide.jsx
│   └── TextFormatting/ (NEW)
│       ├── FontSelector.jsx
│       ├── ColorPicker.jsx
│       └── StylePanel.jsx
└── Utils/
    ├── textSplitter.js (NEW) ← Split text into slides
    └── slideGenerator.js (NEW) ← Generate slides from text
```

---

## 🎨 User Flow

### Flow 1: Upload Text File
```
1. User clicks "Text" in left sidebar
2. Clicks "Upload Text File" button
3. Selects .txt file
4. File uploaded to asset-service
5. Text content extracted
6. User chooses template
7. Text auto-split into slides
8. Slides added to canvas
```

### Flow 2: Paste Text
```
1. User clicks "Text" in left sidebar
2. Clicks "Paste Text" button
3. Modal opens with textarea
4. User pastes text
5. User chooses template
6. Text auto-split into slides
7. Slides added to canvas
```

### Flow 3: Generate with AI
```
1. User clicks "Text" in left sidebar
2. Clicks "Generate with AI" button
3. Text Studio modal opens
4. User generates text
5. Clicks "Add to Canvas"
6. User chooses template
7. Text auto-split into slides
8. Slides added to canvas
```

---

## 🛠️ Implementation Plan

### Phase 1: Text Panel UI (Day 1)
**File:** `frontend-server/src/components/DesignEditor/Sidebar/TextPanel.jsx`

**Features:**
- Upload text file button
- Paste text button
- Generate with AI button
- Recent texts from library
- Quick text templates

**Reuses:**
- Asset service upload endpoint
- Text Studio component
- Text library API

---

### Phase 2: Text Splitter Utility (Day 1)
**File:** `frontend-server/src/utils/textSplitter.js`

**Algorithm:**
```javascript
export function splitTextIntoSlides(text, options = {}) {
  const {
    maxCharsPerSlide = 300,
    splitBy = 'paragraph', // 'paragraph', 'sentence', 'heading'
    preserveHeadings = true
  } = options;

  // Split by paragraphs
  const paragraphs = text.split(/\n\n+/);
  
  const slides = [];
  let currentSlide = { type: 'content', text: '' };
  
  paragraphs.forEach(para => {
    // Detect headings (lines starting with #, or ALL CAPS)
    if (isHeading(para)) {
      if (currentSlide.text) slides.push(currentSlide);
      slides.push({ type: 'title', text: para });
      currentSlide = { type: 'content', text: '' };
    } else if (currentSlide.text.length + para.length > maxCharsPerSlide) {
      slides.push(currentSlide);
      currentSlide = { type: 'content', text: para };
    } else {
      currentSlide.text += (currentSlide.text ? '\n\n' : '') + para;
    }
  });
  
  if (currentSlide.text) slides.push(currentSlide);
  return slides;
}
```

---

### Phase 3: Slide Templates (Day 2)
**File:** `frontend-server/src/constants/slideTemplates.js`

**Templates:**

1. **Title Slide**
   - Large centered heading
   - Optional subtitle
   - Gradient background

2. **Bullet Points**
   - Title at top
   - 3-5 bullet points
   - Icons optional

3. **Quote Slide**
   - Large centered quote
   - Attribution
   - Decorative elements

4. **Two Column**
   - Title
   - Left: text, Right: text
   - Good for comparisons

5. **Image + Text**
   - Left: image placeholder
   - Right: text content

**Template Structure:**
```javascript
export const slideTemplates = {
  title: {
    name: 'Title Slide',
    icon: '📌',
    layout: {
      background: { type: 'gradient', colors: ['#667eea', '#764ba2'] },
      elements: [
        {
          type: 'text',
          content: '{title}',
          fontSize: 72,
          fontWeight: 'bold',
          color: '#ffffff',
          position: { x: '50%', y: '40%' },
          align: 'center'
        }
      ]
    }
  },
  // ... more templates
};
```

---

### Phase 4: Template Selector Modal (Day 2)
**File:** `frontend-server/src/components/DesignEditor/Modals/TemplateSelectorModal.jsx`

**UI:**
```
┌─────────────────────────────────────┐
│  Choose Slide Template              │
├─────────────────────────────────────┤
│  [Title]  [Bullets]  [Quote]  [2Col]│
│    📌       📝         💬       ⚖️   │
│                                     │
│  Preview:                           │
│  ┌─────────────────────┐           │
│  │                     │           │
│  │   Template Preview  │           │
│  │                     │           │
│  └─────────────────────┘           │
│                                     │
│  [Cancel]  [Apply to All Slides]   │
└─────────────────────────────────────┘
```

---

### Phase 5: Slide Generator (Day 3)
**File:** `frontend-server/src/utils/slideGenerator.js`

```javascript
export function generateSlidesFromText(text, templateId) {
  // 1. Split text into slides
  const slideData = splitTextIntoSlides(text);
  
  // 2. Get template
  const template = slideTemplates[templateId];
  
  // 3. Generate canvas pages
  const pages = slideData.map((slide, index) => {
    const elements = template.layout.elements.map(el => ({
      ...el,
      id: generateId(),
      content: el.content.replace('{title}', slide.text)
    }));
    
    return {
      id: `page-${index}`,
      name: `Slide ${index + 1}`,
      background: template.layout.background,
      elements
    };
  });
  
  return pages;
}
```

---

## 📁 Files to Create/Modify

### New Files (6 files)
1. `frontend-server/src/components/DesignEditor/Sidebar/TextPanel.jsx`
2. `frontend-server/src/utils/textSplitter.js`
3. `frontend-server/src/utils/slideGenerator.js`
4. `frontend-server/src/constants/slideTemplates.js`
5. `frontend-server/src/components/DesignEditor/Modals/TemplateSelectorModal.jsx`
6. `frontend-server/src/components/DesignEditor/Modals/PasteTextModal.jsx`

### Modified Files (2 files)
1. `frontend-server/src/components/DesignEditor/DesignEditor.jsx` - Add TextPanel to sidebar
2. `frontend-server/src/components/DesignEditor/Sidebar/Sidebar.jsx` - Add "Text" tab

---

## 🔄 Service Reuse Strategy

### 1. Asset Service (Existing)
**Endpoint:** `POST /api/assets/upload`
**Usage:** Upload .txt files
**No changes needed** ✅

### 2. Text Studio (Existing)
**Component:** `TextStudio.jsx`
**Usage:** Open as modal with `mode="modal"`
**Already supports this** ✅

### 3. Text Library (Existing)
**Endpoint:** `GET /api/assets?asset_type=document&folder=text-library`
**Usage:** Show recent texts in TextPanel
**No changes needed** ✅

---

## 🎯 Next Steps

**Would you like me to:**
1. ✅ Start with Phase 1 - Create TextPanel component
2. ✅ Implement text splitter utility
3. ✅ Create slide templates
4. ✅ Build the complete flow

**Or would you prefer a different approach?**

