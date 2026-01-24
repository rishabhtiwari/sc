/**
 * Slide Generator Utility
 * Converts text + template into canvas pages
 */

import { getTemplate } from '../constants/slideTemplates';
import { splitTextIntoSlides } from './textSplitter';

/**
 * Generate unique ID
 */
function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Create canvas element from template element
 */
function createCanvasElement(templateElement, content, slideIndex) {
  const element = {
    id: generateId(),
    type: templateElement.type,
    fontSize: templateElement.fontSize,
    fontWeight: templateElement.fontWeight,
    color: templateElement.color,
    fontFamily: templateElement.fontFamily,
    textAlign: templateElement.textAlign || 'left',
    position: {
      x: templateElement.position.x,
      y: templateElement.position.y
    },
    width: templateElement.width,
    lineHeight: templateElement.lineHeight || 1.4
  };

  // Add content based on role
  if (templateElement.role === 'title') {
    element.text = content.title || 'Untitled';
  } else if (templateElement.role === 'body') {
    element.text = content.text || '';
  } else if (templateElement.role === 'bullets') {
    element.bullets = content.bullets || [];
    element.bulletStyle = templateElement.bulletStyle || '•';
    element.spacing = templateElement.spacing || 20;
  } else if (templateElement.role === 'quote') {
    element.text = content.text || content.title || '';
    element.fontStyle = templateElement.fontStyle || 'normal';
  } else if (templateElement.role === 'left' || templateElement.role === 'right') {
    // For two-column layout
    const textParts = (content.text || '').split('\n\n');
    const half = Math.ceil(textParts.length / 2);
    element.text = templateElement.role === 'left' 
      ? textParts.slice(0, half).join('\n\n')
      : textParts.slice(half).join('\n\n');
  }

  return element;
}

/**
 * Generate slides from text
 * @param {string} text - The text to convert
 * @param {string} templateId - Template ID to use (optional, auto-detects if not provided)
 * @param {object} options - Additional options
 * @returns {array} Array of canvas page objects
 */
export function generateSlidesFromText(text, templateId = null, options = {}) {
  console.log('🔧 slideGenerator: Starting with text length:', text?.length);
  console.log('🔧 slideGenerator: Template ID:', templateId);

  // Split text into slide data
  const slideData = splitTextIntoSlides(text, options);
  console.log('🔧 slideGenerator: Split into', slideData.length, 'slides');
  console.log('🔧 slideGenerator: Slide data:', slideData);

  if (slideData.length === 0) {
    console.warn('⚠️ slideGenerator: No slides generated from text');
    return [];
  }

  // Generate canvas pages
  const pages = slideData.map((slide, index) => {
    // Auto-detect template if not provided
    let template;
    if (templateId) {
      template = getTemplate(templateId);
    } else {
      // Auto-select template based on slide type
      if (slide.type === 'title') {
        template = getTemplate('title');
      } else if (slide.type === 'bullets') {
        template = getTemplate('bullets');
      } else {
        template = getTemplate('content');
      }
    }

    // Create background
    const background = {
      type: template.layout.background.type,
      color: template.layout.background.color,
      colors: template.layout.background.colors
    };

    // Create elements
    const elements = template.layout.elements.map(templateEl => 
      createCanvasElement(templateEl, slide, index)
    );

    return {
      id: `page-${generateId()}`,
      name: `Slide ${index + 1}`,
      background,
      elements,
      duration: 5, // Default 5 seconds per slide
      transition: 'fade'
    };
  });

  return pages;
}

/**
 * Apply template to existing slide
 * @param {object} slide - Existing slide data
 * @param {string} templateId - Template ID to apply
 * @returns {object} Updated slide
 */
export function applyTemplateToSlide(slide, templateId) {
  const template = getTemplate(templateId);
  
  // Extract text content from existing slide
  const textContent = {
    title: '',
    text: '',
    bullets: []
  };

  // Extract content from existing elements
  slide.elements.forEach(el => {
    if (el.type === 'text') {
      if (!textContent.title) {
        textContent.title = el.text;
      } else {
        textContent.text += (textContent.text ? '\n\n' : '') + el.text;
      }
    } else if (el.type === 'bullets') {
      textContent.bullets = el.bullets || [];
    }
  });

  // Create new elements with template
  const newElements = template.layout.elements.map(templateEl => 
    createCanvasElement(templateEl, textContent, 0)
  );

  return {
    ...slide,
    background: template.layout.background,
    elements: newElements
  };
}

