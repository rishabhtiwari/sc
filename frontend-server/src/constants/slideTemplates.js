/**
 * Slide Templates
 * Pre-designed layouts for different content types
 * Similar to Canva/Veed.io templates
 */

export const slideTemplates = {
  // 1. Modern Title Slide - Professional gradient with large heading
  title: {
    id: 'title',
    name: 'Modern Title',
    icon: '🎯',
    description: 'Bold title with modern gradient background',
    preview: 'https://via.placeholder.com/300x200/667eea/ffffff?text=Title+Slide',
    layout: {
      background: {
        type: 'gradient',
        colors: ['#667eea', '#764ba2'],
        angle: 135
      },
      elements: [
        {
          type: 'text',
          role: 'title',
          fontSize: 72,
          fontWeight: '800',
          color: '#ffffff',
          textAlign: 'center',
          position: { x: 10, y: 40 }, // percentage
          width: 80,
          fontFamily: 'Inter, -apple-system, sans-serif',
          lineHeight: 1.2,
          letterSpacing: '-0.02em'
        }
      ]
    }
  },

  // 2. Clean Content Slide - Professional white background with accent
  content: {
    id: 'content',
    name: 'Clean Content',
    icon: '📄',
    description: 'Professional layout with title and body text',
    preview: 'https://via.placeholder.com/300x200/4f46e5/ffffff?text=Content+Slide',
    layout: {
      background: {
        type: 'solid',
        color: '#f8fafc'
      },
      elements: [
        {
          type: 'shape',
          role: 'accent',
          shapeType: 'rectangle',
          fill: '#667eea',
          position: { x: 0, y: 0 },
          width: 100,
          height: 2
        },
        {
          type: 'text',
          role: 'title',
          fontSize: 56,
          fontWeight: '700',
          color: '#1e293b',
          textAlign: 'left',
          position: { x: 8, y: 12 },
          width: 84,
          fontFamily: 'Inter, -apple-system, sans-serif',
          lineHeight: 1.2,
          letterSpacing: '-0.02em'
        },
        {
          type: 'text',
          role: 'body',
          fontSize: 28,
          fontWeight: '400',
          color: '#475569',
          textAlign: 'left',
          position: { x: 8, y: 32 },
          width: 84,
          lineHeight: 1.7,
          fontFamily: 'Inter, -apple-system, sans-serif'
        }
      ]
    }
  },

  // 3. Professional Bullet Points - Clean list layout
  bullets: {
    id: 'bullets',
    name: 'Key Points',
    icon: '✓',
    description: 'Highlight key points with professional styling',
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
          fontSize: 52,
          fontWeight: '700',
          color: '#0f172a',
          textAlign: 'left',
          position: { x: 8, y: 10 },
          width: 84,
          fontFamily: 'Inter, -apple-system, sans-serif',
          lineHeight: 1.2
        },
        {
          type: 'bullets',
          role: 'bullets',
          fontSize: 32,
          fontWeight: '400',
          color: '#334155',
          textAlign: 'left',
          position: { x: 10, y: 28 },
          width: 80,
          bulletStyle: '✓',
          spacing: 32,
          fontFamily: 'Inter, -apple-system, sans-serif',
          lineHeight: 1.5
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

