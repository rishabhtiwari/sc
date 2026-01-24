/**
 * Slide Templates
 * Pre-designed layouts for different content types
 * Similar to Canva/Veed.io templates
 */

export const slideTemplates = {
  // 1. Title Slide - Large centered heading
  title: {
    id: 'title',
    name: 'Title Slide',
    icon: '📌',
    description: 'Large centered heading with optional subtitle',
    preview: 'https://via.placeholder.com/300x200/667eea/ffffff?text=Title+Slide',
    layout: {
      background: {
        type: 'gradient',
        colors: ['#667eea', '#764ba2']
      },
      elements: [
        {
          type: 'text',
          role: 'title',
          fontSize: 64,
          fontWeight: 'bold',
          color: '#ffffff',
          textAlign: 'center',
          position: { x: 50, y: 45 }, // percentage
          width: 80,
          fontFamily: 'Inter, sans-serif'
        }
      ]
    }
  },

  // 2. Content Slide - Title + Body text
  content: {
    id: 'content',
    name: 'Content Slide',
    icon: '📄',
    description: 'Title with body text content',
    preview: 'https://via.placeholder.com/300x200/4f46e5/ffffff?text=Content+Slide',
    layout: {
      background: {
        type: 'solid',
        color: '#ffffff'
      },
      elements: [
        {
          type: 'text',
          role: 'title',
          fontSize: 48,
          fontWeight: 'bold',
          color: '#1f2937',
          textAlign: 'left',
          position: { x: 10, y: 15 },
          width: 80,
          fontFamily: 'Inter, sans-serif'
        },
        {
          type: 'text',
          role: 'body',
          fontSize: 20,
          fontWeight: 'normal',
          color: '#4b5563',
          textAlign: 'left',
          position: { x: 10, y: 35 },
          width: 80,
          lineHeight: 1.6,
          fontFamily: 'Inter, sans-serif'
        }
      ]
    }
  },

  // 3. Bullet Points - Title + List
  bullets: {
    id: 'bullets',
    name: 'Bullet Points',
    icon: '📝',
    description: 'Title with bullet point list',
    preview: 'https://via.placeholder.com/300x200/10b981/ffffff?text=Bullet+Points',
    layout: {
      background: {
        type: 'solid',
        color: '#ffffff'
      },
      elements: [
        {
          type: 'text',
          role: 'title',
          fontSize: 48,
          fontWeight: 'bold',
          color: '#1f2937',
          textAlign: 'left',
          position: { x: 10, y: 15 },
          width: 80,
          fontFamily: 'Inter, sans-serif'
        },
        {
          type: 'bullets',
          role: 'bullets',
          fontSize: 24,
          fontWeight: 'normal',
          color: '#4b5563',
          textAlign: 'left',
          position: { x: 15, y: 35 },
          width: 75,
          bulletStyle: '•',
          spacing: 20,
          fontFamily: 'Inter, sans-serif'
        }
      ]
    }
  },

  // 4. Quote Slide - Large centered quote
  quote: {
    id: 'quote',
    name: 'Quote Slide',
    icon: '💬',
    description: 'Large centered quote with attribution',
    preview: 'https://via.placeholder.com/300x200/f59e0b/ffffff?text=Quote+Slide',
    layout: {
      background: {
        type: 'gradient',
        colors: ['#fbbf24', '#f59e0b']
      },
      elements: [
        {
          type: 'text',
          role: 'quote',
          fontSize: 36,
          fontWeight: '500',
          color: '#ffffff',
          textAlign: 'center',
          position: { x: 15, y: 40 },
          width: 70,
          fontStyle: 'italic',
          fontFamily: 'Georgia, serif'
        }
      ]
    }
  },

  // 5. Two Column - Split content
  twoColumn: {
    id: 'twoColumn',
    name: 'Two Column',
    icon: '⚖️',
    description: 'Split content into two columns',
    preview: 'https://via.placeholder.com/300x200/8b5cf6/ffffff?text=Two+Column',
    layout: {
      background: {
        type: 'solid',
        color: '#ffffff'
      },
      elements: [
        {
          type: 'text',
          role: 'title',
          fontSize: 48,
          fontWeight: 'bold',
          color: '#1f2937',
          textAlign: 'center',
          position: { x: 10, y: 10 },
          width: 80,
          fontFamily: 'Inter, sans-serif'
        },
        {
          type: 'text',
          role: 'left',
          fontSize: 20,
          fontWeight: 'normal',
          color: '#4b5563',
          textAlign: 'left',
          position: { x: 10, y: 30 },
          width: 35,
          fontFamily: 'Inter, sans-serif'
        },
        {
          type: 'text',
          role: 'right',
          fontSize: 20,
          fontWeight: 'normal',
          color: '#4b5563',
          textAlign: 'left',
          position: { x: 55, y: 30 },
          width: 35,
          fontFamily: 'Inter, sans-serif'
        }
      ]
    }
  }
};

// Get template by ID
export function getTemplate(templateId) {
  return slideTemplates[templateId] || slideTemplates.content;
}

// Get all templates as array
export function getAllTemplates() {
  return Object.values(slideTemplates);
}

