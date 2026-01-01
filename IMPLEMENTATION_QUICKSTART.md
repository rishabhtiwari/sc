# 🚀 Canva-Like Platform - Quick Start Implementation Guide

## 📋 Prerequisites

Before starting, ensure you have:
- ✅ Node.js 16+ and npm/yarn
- ✅ Python 3.9+
- ✅ MongoDB running
- ✅ Redis running (optional, for caching)
- ✅ S3/Minio for asset storage

---

## 🎯 Phase 1: Setup & Dependencies (Day 1)

### 1.1 Install Frontend Dependencies

```bash
cd frontend-server

# Core canvas library
npm install fabric

# State management
npm install @reduxjs/toolkit react-redux

# UI components
npm install react-color
npm install react-dropzone
npm install react-icons

# Audio visualization
npm install wavesurfer.js

# Utilities
npm install lodash
npm install uuid
npm install date-fns
```

### 1.2 Install Backend Dependencies

```bash
cd template-service

# Image processing
pip install Pillow==10.1.0
pip install cairosvg==2.7.1

# PDF generation
pip install reportlab==4.0.7

# Video processing (already installed)
# moviepy, opencv-python

# Utilities
pip install python-magic==0.4.27  # File type detection
```

### 1.3 Create Database Migrations

```bash
cd mongodb/migrations

# Create new migration file
touch 050_create_design_collections.js
```

---

## 📦 Phase 2: Database Schema (Day 2-3)

### 2.1 Create Design Collections

**File:** `mongodb/migrations/050_create_design_collections.js`

```javascript
// See CANVA_PLATFORM_PLAN.md for full schema
// Key collections:
// 1. designs - User design projects
// 2. categories - Design categories
// 3. assets - User uploaded assets
// 4. exports - Export history

db.createCollection('designs', { /* schema */ });
db.createCollection('categories', { /* schema */ });
db.createCollection('assets', { /* schema */ });
db.createCollection('exports', { /* schema */ });

// Create indexes
db.designs.createIndex({ customer_id: 1, user_id: 1 });
db.designs.createIndex({ category: 1, subcategory: 1 });
db.assets.createIndex({ customer_id: 1, type: 1 });
```

### 2.2 Seed Initial Categories

```javascript
// Seed 9 main categories
const categories = [
  {
    category_id: "for_you",
    name: "For You",
    icon: "⭐",
    order: 1,
    subcategories: []
  },
  {
    category_id: "presentation",
    name: "Presentation",
    icon: "📊",
    order: 2,
    subcategories: [
      { id: "pitch_deck", name: "Pitch Deck", dimensions: { width: 1920, height: 1080 } },
      { id: "business_presentation", name: "Business Presentation", dimensions: { width: 1920, height: 1080 } }
    ]
  },
  {
    category_id: "social_media",
    name: "Social Media",
    icon: "📱",
    order: 3,
    subcategories: [
      { id: "instagram_post", name: "Instagram Post", dimensions: { width: 1080, height: 1080 } },
      { id: "instagram_story", name: "Instagram Story", dimensions: { width: 1080, height: 1920 } },
      { id: "facebook_post", name: "Facebook Post", dimensions: { width: 1200, height: 630 } },
      { id: "twitter_post", name: "Twitter Post", dimensions: { width: 1200, height: 675 } }
    ]
  },
  // ... more categories
];

db.categories.insertMany(categories);
```

---

## 🎨 Phase 3: Category Selection UI (Day 4-7)

### 3.1 Create Homepage Component

**File:** `frontend-server/src/pages/DesignHomePage.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import CategoryGrid from '../components/DesignHome/CategoryGrid';
import RecentDesigns from '../components/DesignHome/RecentDesigns';

const DesignHomePage = () => {
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [recentDesigns, setRecentDesigns] = useState([]);

  useEffect(() => {
    fetchCategories();
    fetchRecentDesigns();
  }, []);

  const fetchCategories = async () => {
    const response = await fetch('/api/categories');
    const data = await response.json();
    setCategories(data.categories);
  };

  const handleCategoryClick = (categoryId) => {
    navigate(`/design/category/${categoryId}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            What will you design today?
          </h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Recent Designs */}
        {recentDesigns.length > 0 && (
          <RecentDesigns designs={recentDesigns} />
        )}

        {/* Category Grid */}
        <CategoryGrid 
          categories={categories} 
          onCategoryClick={handleCategoryClick}
        />
      </main>
    </div>
  );
};

export default DesignHomePage;
```

### 3.2 Create Category Grid Component

**File:** `frontend-server/src/components/DesignHome/CategoryGrid.jsx`

```jsx
import React from 'react';
import CategoryCard from './CategoryCard';

const CategoryGrid = ({ categories, onCategoryClick }) => {
  return (
    <div className="mt-8">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">
        Start creating
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories.map(category => (
          <CategoryCard
            key={category.category_id}
            category={category}
            onClick={() => onCategoryClick(category.category_id)}
          />
        ))}
      </div>
    </div>
  );
};

export default CategoryGrid;
```

---

## 🖼️ Phase 4: Canvas Editor Foundation (Day 8-14)

### 4.1 Setup Redux Store

**File:** `frontend-server/src/store/designSlice.js`

```javascript
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  currentDesign: null,
  canvasState: null,
  selectedObjects: [],
  clipboard: null,
  history: {
    past: [],
    future: []
  },
  ui: {
    leftSidebarTab: 'templates',
    rightSidebarVisible: true,
    zoom: 1.0,
    gridVisible: false,
    rulersVisible: false
  },
  saving: false,
  exporting: false
};

const designSlice = createSlice({
  name: 'design',
  initialState,
  reducers: {
    setCurrentDesign: (state, action) => {
      state.currentDesign = action.payload;
    },
    updateCanvasState: (state, action) => {
      state.canvasState = action.payload;
    },
    setSelectedObjects: (state, action) => {
      state.selectedObjects = action.payload;
    },
    addToHistory: (state, action) => {
      state.history.past.push(action.payload);
      state.history.future = [];
    },
    undo: (state) => {
      if (state.history.past.length > 0) {
        const previous = state.history.past.pop();
        state.history.future.push(state.canvasState);
        state.canvasState = previous;
      }
    },
    redo: (state) => {
      if (state.history.future.length > 0) {
        const next = state.history.future.pop();
        state.history.past.push(state.canvasState);
        state.canvasState = next;
      }
    },
    setLeftSidebarTab: (state, action) => {
      state.ui.leftSidebarTab = action.payload;
    },
    setZoom: (state, action) => {
      state.ui.zoom = action.payload;
    }
  }
});

export const {
  setCurrentDesign,
  updateCanvasState,
  setSelectedObjects,
  addToHistory,
  undo,
  redo,
  setLeftSidebarTab,
  setZoom
} = designSlice.actions;

export default designSlice.reducer;
```

### 4.2 Create Main Editor Component

**File:** `frontend-server/src/components/DesignEditor/DesignEditor.jsx`

```jsx
import React, { useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import TopToolbar from './TopToolbar/TopToolbar';
import LeftSidebar from './LeftSidebar/LeftSidebar';
import EditorCanvas from './EditorCanvas';
import RightSidebar from './RightSidebar/RightSidebar';
import BottomTimeline from './BottomTimeline/Timeline';

const DesignEditor = () => {
  const dispatch = useDispatch();
  const currentDesign = useSelector(state => state.design.currentDesign);
  const canvasRef = useRef(null);

  useEffect(() => {
    // Auto-save every 5 seconds
    const autoSaveInterval = setInterval(() => {
      if (currentDesign) {
        saveDesign();
      }
    }, 5000);

    return () => clearInterval(autoSaveInterval);
  }, [currentDesign]);

  const saveDesign = async () => {
    // Get canvas state from Fabric.js
    const canvasState = canvasRef.current?.toJSON();

    const response = await fetch('/api/designs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...currentDesign,
        canvas_state: canvasState
      })
    });
  };

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top Toolbar */}
      <TopToolbar onSave={saveDesign} />

      {/* Main Editor Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <LeftSidebar />

        {/* Center Canvas */}
        <div className="flex-1 flex flex-col">
          <EditorCanvas ref={canvasRef} />

          {/* Bottom Timeline (for video designs) */}
          {currentDesign?.template_type === 'video' && (
            <BottomTimeline />
          )}
        </div>

        {/* Right Sidebar */}
        <RightSidebar />
      </div>
    </div>
  );
};

export default DesignEditor;
```

### 4.3 Create Fabric.js Canvas Wrapper

**File:** `frontend-server/src/components/DesignEditor/EditorCanvas.jsx`

```jsx
import React, { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { fabric } from 'fabric';
import { useDispatch, useSelector } from 'react-redux';
import { updateCanvasState, setSelectedObjects, addToHistory } from '../../store/designSlice';

const EditorCanvas = forwardRef((props, ref) => {
  const canvasRef = useRef(null);
  const fabricCanvasRef = useRef(null);
  const dispatch = useDispatch();
  const currentDesign = useSelector(state => state.design.currentDesign);
  const zoom = useSelector(state => state.design.ui.zoom);

  useEffect(() => {
    // Initialize Fabric.js canvas
    const canvas = new fabric.Canvas(canvasRef.current, {
      width: currentDesign?.dimensions?.width || 1920,
      height: currentDesign?.dimensions?.height || 1080,
      backgroundColor: '#ffffff'
    });

    fabricCanvasRef.current = canvas;

    // Load existing design if available
    if (currentDesign?.canvas_state) {
      canvas.loadFromJSON(currentDesign.canvas_state, () => {
        canvas.renderAll();
      });
    }

    // Event listeners
    canvas.on('selection:created', handleSelection);
    canvas.on('selection:updated', handleSelection);
    canvas.on('selection:cleared', () => dispatch(setSelectedObjects([])));
    canvas.on('object:modified', handleObjectModified);

    return () => {
      canvas.dispose();
    };
  }, [currentDesign]);

  // Apply zoom
  useEffect(() => {
    if (fabricCanvasRef.current) {
      fabricCanvasRef.current.setZoom(zoom);
    }
  }, [zoom]);

  const handleSelection = (e) => {
    const selected = fabricCanvasRef.current.getActiveObjects();
    dispatch(setSelectedObjects(selected));
  };

  const handleObjectModified = (e) => {
    // Add to history for undo/redo
    const canvasState = fabricCanvasRef.current.toJSON();
    dispatch(addToHistory(canvasState));
    dispatch(updateCanvasState(canvasState));
  };

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    toJSON: () => fabricCanvasRef.current?.toJSON(),
    addText: (text) => {
      const textObj = new fabric.Text(text, {
        left: 100,
        top: 100,
        fontSize: 40,
        fill: '#000000'
      });
      fabricCanvasRef.current.add(textObj);
      fabricCanvasRef.current.setActiveObject(textObj);
    },
    addImage: (url) => {
      fabric.Image.fromURL(url, (img) => {
        img.scaleToWidth(300);
        fabricCanvasRef.current.add(img);
        fabricCanvasRef.current.setActiveObject(img);
      });
    },
    addShape: (type) => {
      let shape;
      if (type === 'rectangle') {
        shape = new fabric.Rect({
          left: 100,
          top: 100,
          width: 200,
          height: 150,
          fill: '#3498db'
        });
      } else if (type === 'circle') {
        shape = new fabric.Circle({
          left: 100,
          top: 100,
          radius: 75,
          fill: '#e74c3c'
        });
      }
      fabricCanvasRef.current.add(shape);
      fabricCanvasRef.current.setActiveObject(shape);
    },
    deleteSelected: () => {
      const activeObjects = fabricCanvasRef.current.getActiveObjects();
      fabricCanvasRef.current.remove(...activeObjects);
      fabricCanvasRef.current.discardActiveObject();
    },
    getCanvas: () => fabricCanvasRef.current
  }));

  return (
    <div className="flex-1 flex items-center justify-center bg-gray-200 p-8">
      <div className="bg-white shadow-2xl" style={{
        transform: `scale(${zoom})`,
        transformOrigin: 'center'
      }}>
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
});

export default EditorCanvas;
```

---

## 🎛️ Phase 5: Editor Toolbars & Panels (Day 15-21)

### 5.1 Top Toolbar

**File:** `frontend-server/src/components/DesignEditor/TopToolbar/TopToolbar.jsx`

```jsx
import React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { undo, redo } from '../../../store/designSlice';

const TopToolbar = ({ onSave }) => {
  const dispatch = useDispatch();
  const currentDesign = useSelector(state => state.design.currentDesign);
  const canUndo = useSelector(state => state.design.history.past.length > 0);
  const canRedo = useSelector(state => state.design.history.future.length > 0);

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center justify-between">
      {/* Left: File operations */}
      <div className="flex items-center gap-2">
        <button className="px-3 py-1 text-sm hover:bg-gray-100 rounded">
          File
        </button>
        <button
          className="px-3 py-1 text-sm hover:bg-gray-100 rounded disabled:opacity-50"
          onClick={() => dispatch(undo())}
          disabled={!canUndo}
        >
          ↶ Undo
        </button>
        <button
          className="px-3 py-1 text-sm hover:bg-gray-100 rounded disabled:opacity-50"
          onClick={() => dispatch(redo())}
          disabled={!canRedo}
        >
          ↷ Redo
        </button>
      </div>

      {/* Center: Design name */}
      <div className="flex-1 text-center">
        <input
          type="text"
          value={currentDesign?.name || 'Untitled Design'}
          className="text-lg font-medium border-none focus:outline-none text-center"
          style={{ width: '300px' }}
        />
      </div>

      {/* Right: Export */}
      <div className="flex items-center gap-2">
        <button
          onClick={onSave}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          💾 Save
        </button>
        <button className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">
          📤 Export
        </button>
      </div>
    </div>
  );
};

export default TopToolbar;
```

---

## 🔌 Phase 6: Backend API Endpoints (Day 22-28)

### 6.1 Create Design Service

**File:** `design-service/app.py` (NEW SERVICE)

```python
from flask import Flask, request, jsonify, g
from pymongo import MongoClient
import os
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['news_automation']
designs_collection = db['designs']

@app.route('/api/designs', methods=['POST'])
def create_or_update_design():
    """Create or update a design"""
    data = request.json
    customer_id = g.get('customer_id')
    user_id = g.get('user_id')

    design_id = data.get('design_id')

    design_doc = {
        'customer_id': customer_id,
        'user_id': user_id,
        'name': data.get('name', 'Untitled Design'),
        'category': data.get('category'),
        'subcategory': data.get('subcategory'),
        'canvas_state': data.get('canvas_state'),
        'dimensions': data.get('dimensions'),
        'timeline': data.get('timeline'),
        'assets': data.get('assets', []),
        'updated_at': datetime.utcnow(),
        'status': 'draft'
    }

    if design_id:
        # Update existing
        designs_collection.update_one(
            {'design_id': design_id, 'customer_id': customer_id},
            {'$set': design_doc}
        )
    else:
        # Create new
        import uuid
        design_id = str(uuid.uuid4())
        design_doc['design_id'] = design_id
        design_doc['created_at'] = datetime.utcnow()
        designs_collection.insert_one(design_doc)

    return jsonify({
        'status': 'success',
        'design_id': design_id
    }), 201

@app.route('/api/designs/<design_id>', methods=['GET'])
def get_design(design_id):
    """Get a design by ID"""
    customer_id = g.get('customer_id')

    design = designs_collection.find_one(
        {'design_id': design_id, 'customer_id': customer_id},
        {'_id': 0}
    )

    if not design:
        return jsonify({'error': 'Design not found'}), 404

    return jsonify(design)

@app.route('/api/designs', methods=['GET'])
def list_designs():
    """List all designs for current user"""
    customer_id = g.get('customer_id')
    user_id = g.get('user_id')

    designs = list(designs_collection.find(
        {'customer_id': customer_id, 'user_id': user_id},
        {'_id': 0}
    ).sort('updated_at', -1).limit(50))

    return jsonify({'designs': designs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5011, debug=True)
```

---

## 📝 Next Steps Checklist

### Week 1-2: Foundation
- [ ] Install all dependencies
- [ ] Create database migrations
- [ ] Seed initial categories
- [ ] Test database connections

### Week 3: Category UI
- [ ] Build DesignHomePage
- [ ] Build CategoryGrid component
- [ ] Build SubcategoryPage
- [ ] Test navigation flow

### Week 4-6: Canvas Editor
- [ ] Setup Redux store
- [ ] Build DesignEditor main component
- [ ] Integrate Fabric.js
- [ ] Build left sidebar panels
- [ ] Build right sidebar panels
- [ ] Implement undo/redo

### Week 7-8: Video Timeline
- [ ] Build Timeline component
- [ ] Implement drag-and-drop
- [ ] Add playback controls
- [ ] Integrate with video renderer

### Week 9: Audio Editor
- [ ] Integrate WaveSurfer.js
- [ ] Build audio controls
- [ ] Implement audio mixing

### Week 10: Asset Management
- [ ] Build upload component
- [ ] Integrate S3 storage
- [ ] Add stock asset search
- [ ] Build asset library

### Week 11: Export & Rendering
- [ ] Build export modal
- [ ] Implement image export
- [ ] Implement video export
- [ ] Add background job queue

---

## 🎯 Success Criteria

✅ User can select a category and template
✅ User can edit design in canvas (text, images, shapes)
✅ User can save design (auto-save every 5s)
✅ User can export design as image (PNG/JPG)
✅ User can export design as video (MP4)
✅ User can upload custom assets
✅ Design state persists in MongoDB
✅ Multi-tenant isolation works correctly

---

**Ready to start? Begin with Phase 1! 🚀**

