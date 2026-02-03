# DesignEditor Refactoring Plan

## Problem
The DesignEditor.jsx file has grown to over 2100 lines, making it difficult to:
- Understand and maintain
- Make targeted changes
- Test individual features
- Collaborate on different features

## Solution
Break down the monolithic component into smaller, focused modules using custom hooks and utility functions.

---

## New Structure

```
DesignEditor/
├── DesignEditor.jsx (main orchestrator - ~300 lines)
├── hooks/
│   ├── useSessionStorage.js ✅ CREATED
│   ├── useElementManagement.js ✅ CREATED
│   ├── usePageManagement.js ✅ CREATED
│   ├── useMediaManagement.js (TODO)
│   ├── useProjectState.js (TODO)
│   └── useVideoPlayback.js (TODO)
├── utils/
│   ├── projectDataHelpers.js (TODO)
│   └── elementHelpers.js (TODO)
└── [existing folders: Canvas/, Sidebar/, Timeline/]
```

---

## Custom Hooks Created

### ✅ useSessionStorage.js
**Purpose**: Auto-save and restore in-memory state from sessionStorage

**Exports**:
- Auto-saves state on every change
- Restores state on mount (if < 1 hour old and no project URL)

**Usage**:
```javascript
useSessionStorage({
  pages, uploadedAudio, uploadedImage, uploadedVideo, audioTracks, currentProject,
  setPages, setUploadedAudio, setUploadedImage, setUploadedVideo, setAudioTracks, setCurrentProject
});
```

---

### ✅ useElementManagement.js
**Purpose**: Manage canvas elements (add, update, delete, select)

**Exports**:
- `selectedElement` - Currently selected element
- `handleAddElement(element)` - Add new element to current page
- `handleUpdateElement(elementId, updates)` - Update element properties
- `handleDeleteElement(elementId)` - Delete element
- `handleSelectElement(element)` - Select element
- `handleDeselectElement()` - Deselect element

**Usage**:
```javascript
const {
  selectedElement,
  handleAddElement,
  handleUpdateElement,
  handleDeleteElement,
  handleSelectElement,
  handleDeselectElement
} = useElementManagement(pages, setPages, currentPageIndex);
```

---

### ✅ usePageManagement.js
**Purpose**: Manage pages (add, delete, navigate, background)

**Exports**:
- `currentPageIndex` - Index of current page
- `currentPage` - Current page object
- `handleAddPage()` - Add new page
- `handleAddMultiplePages(count)` - Add multiple pages
- `handleDeletePage(pageIndex)` - Delete page
- `handleDuplicatePage(pageIndex)` - Duplicate page
- `handleBackgroundChange(background)` - Update page background
- `handlePageChange(pageIndex)` - Navigate to page
- `handleNextPage()` - Next page
- `handlePreviousPage()` - Previous page
- `setCurrentPageIndex` - Direct setter

**Usage**:
```javascript
const {
  currentPageIndex,
  currentPage,
  handleAddPage,
  handleDeletePage,
  handleBackgroundChange,
  handlePageChange
} = usePageManagement(pages, setPages);
```

---

## TODO: Remaining Hooks

### useMediaManagement.js
**Purpose**: Manage media uploads (audio, image, video)

**Should export**:
- `uploadedAudio`, `uploadedImage`, `uploadedVideo`
- `handleAddAudio()`, `handleAddImage()`, `handleAddVideo()`
- `handleDeleteAudio()`, `handleDeleteImage()`, `handleDeleteVideo()`
- Media upload handlers

---

### useProjectState.js
**Purpose**: Project save/load operations

**Should export**:
- `currentProject`, `isSaving`, `isLoading`
- `handleSaveProject()`
- `handleLoadProject(projectId)`
- `prepareProjectData()` - Convert in-memory state to API format
- `extractMediaFromProject()` - Extract media from loaded project

---

### useVideoPlayback.js
**Purpose**: Video playback control on canvas

**Should export**:
- `isPlaying`, `currentTime`
- `handlePlayPause()`
- `handleSeek(time)`
- `videoElementRefs`

---

## TODO: Utility Functions

### projectDataHelpers.js
**Purpose**: Helper functions for project data transformation

**Should export**:
- `prepareProjectData(pages, audioTracks, uploadedAudio, uploadedImage, uploadedVideo, currentProject)`
- `extractMediaFromProject(project)`
- `uploadBlobToAsset(blob, type, name)`

---

### elementHelpers.js
**Purpose**: Helper functions for element operations

**Should export**:
- `createDefaultPage(index)`
- `createDefaultElement(type)`
- `validateElement(element)`

---

## Migration Steps

1. ✅ Create custom hooks (useSessionStorage, useElementManagement, usePageManagement)
2. ✅ Create remaining hooks (useMediaManagement, useProjectState, useVideoPlayback)
3. ✅ Create utility functions (projectDataHelpers, elementHelpers)
4. ✅ Create new DesignEditor.refactored.jsx using all hooks
5. ⏳ Test the refactored version thoroughly
6. ⏳ Replace old DesignEditor.jsx with refactored version
7. ⏳ Delete backup files

---

## How to Test the Refactored Version

### Step 1: Temporarily switch to refactored version
```bash
# Backup original
mv frontend-server/src/components/DesignEditor/DesignEditor.jsx frontend-server/src/components/DesignEditor/DesignEditor.old.jsx

# Use refactored version
mv frontend-server/src/components/DesignEditor/DesignEditor.refactored.jsx frontend-server/src/components/DesignEditor/DesignEditor.jsx
```

### Step 2: Test all functionality
- [ ] Create new project
- [ ] Add text elements
- [ ] Add shapes (rectangle, circle, etc.)
- [ ] Add icons and stickers
- [ ] Add images from library
- [ ] Add videos from library
- [ ] Add audio from library
- [ ] Resize elements
- [ ] Move elements
- [ ] Delete elements
- [ ] Add multiple pages
- [ ] Navigate between pages
- [ ] Delete pages
- [ ] Save project
- [ ] Load project
- [ ] Navigate to image library and back (state should be preserved!)
- [ ] Navigate to video library and back (state should be preserved!)
- [ ] Navigate to audio library and back (state should be preserved!)

### Step 3: If all tests pass
```bash
# Delete old version
rm frontend-server/src/components/DesignEditor/DesignEditor.old.jsx
```

### Step 4: If tests fail
```bash
# Restore original
mv frontend-server/src/components/DesignEditor/DesignEditor.jsx frontend-server/src/components/DesignEditor/DesignEditor.refactored.jsx
mv frontend-server/src/components/DesignEditor/DesignEditor.old.jsx frontend-server/src/components/DesignEditor/DesignEditor.jsx
```

---

## Benefits

✅ **Maintainability**: Each hook focuses on one concern
✅ **Testability**: Hooks can be tested independently
✅ **Reusability**: Hooks can be reused in other components
✅ **Readability**: Main component becomes much cleaner
✅ **Collaboration**: Multiple developers can work on different hooks
✅ **Debugging**: Easier to isolate issues to specific modules

