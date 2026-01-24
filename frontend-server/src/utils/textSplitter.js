/**
 * Text Splitter Utility
 * Intelligently splits long text into multiple slides
 * Similar to Canva/Veed.io approach
 */

/**
 * Detect if a paragraph is a heading
 */
function isHeading(text) {
  const trimmed = text.trim();
  
  // Check for markdown-style headings
  if (trimmed.startsWith('#')) return true;
  
  // Check for ALL CAPS (at least 3 words)
  const words = trimmed.split(/\s+/);
  if (words.length >= 2 && trimmed === trimmed.toUpperCase() && trimmed.length > 5) {
    return true;
  }
  
  // Check for short lines (likely titles)
  if (trimmed.length < 60 && !trimmed.endsWith('.') && !trimmed.endsWith(',')) {
    return true;
  }
  
  return false;
}

/**
 * Detect if text contains bullet points
 */
function hasBulletPoints(text) {
  const bulletPatterns = [
    /^[\-\*\•]\s+/m,  // - or * or • at start
    /^\d+\.\s+/m,     // 1. 2. 3.
    /^[a-z]\)\s+/m    // a) b) c)
  ];
  
  return bulletPatterns.some(pattern => pattern.test(text));
}

/**
 * Extract bullet points from text
 */
function extractBulletPoints(text) {
  const lines = text.split('\n');
  const bullets = [];
  let title = '';
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    
    // Check if it's a bullet point
    if (/^[\-\*\•]\s+/.test(trimmed)) {
      bullets.push(trimmed.replace(/^[\-\*\•]\s+/, ''));
    } else if (/^\d+\.\s+/.test(trimmed)) {
      bullets.push(trimmed.replace(/^\d+\.\s+/, ''));
    } else if (!title && bullets.length === 0) {
      title = trimmed;
    }
  }
  
  return { title, bullets };
}

/**
 * Main function: Split text into slides
 * @param {string} text - The text to split
 * @param {object} options - Configuration options
 * @returns {array} Array of slide objects
 */
export function splitTextIntoSlides(text, options = {}) {
  console.log('📄 textSplitter: Input text length:', text?.length);

  const {
    maxCharsPerSlide = 300,
    minCharsPerSlide = 50,
    preserveHeadings = true,
    detectBullets = true
  } = options;

  if (!text || !text.trim()) {
    console.warn('⚠️ textSplitter: Empty text provided');
    return [];
  }

  // Split by double newlines (paragraphs)
  const paragraphs = text.split(/\n\n+/).filter(p => p.trim());
  console.log('📄 textSplitter: Found', paragraphs.length, 'paragraphs');
  
  const slides = [];
  let currentSlide = { type: 'content', text: '', title: '' };
  
  for (let i = 0; i < paragraphs.length; i++) {
    const para = paragraphs[i].trim();
    
    // Skip empty paragraphs
    if (!para) continue;
    
    // Check if it's a heading
    if (preserveHeadings && isHeading(para)) {
      // Save current slide if it has content
      if (currentSlide.text.trim()) {
        slides.push({ ...currentSlide });
      }
      
      // Create title slide
      slides.push({
        type: 'title',
        title: para.replace(/^#+\s*/, ''), // Remove markdown #
        text: ''
      });
      
      currentSlide = { type: 'content', text: '', title: '' };
      continue;
    }
    
    // Check if it contains bullet points
    if (detectBullets && hasBulletPoints(para)) {
      // Save current slide if it has content
      if (currentSlide.text.trim()) {
        slides.push({ ...currentSlide });
      }
      
      const { title, bullets } = extractBulletPoints(para);
      slides.push({
        type: 'bullets',
        title: title || 'Key Points',
        bullets: bullets.slice(0, 5) // Max 5 bullets per slide
      });
      
      currentSlide = { type: 'content', text: '', title: '' };
      continue;
    }
    
    // Regular content paragraph
    const paraLength = para.length;
    const currentLength = currentSlide.text.length;
    
    // If adding this paragraph exceeds max chars, start new slide
    if (currentLength > 0 && currentLength + paraLength > maxCharsPerSlide) {
      slides.push({ ...currentSlide });
      currentSlide = { type: 'content', text: para, title: '' };
    } else {
      // Add to current slide
      currentSlide.text += (currentSlide.text ? '\n\n' : '') + para;
    }
  }
  
  // Add last slide if it has content
  if (currentSlide.text.trim()) {
    slides.push(currentSlide);
  }
  
  // If no slides were created, create one with all text
  if (slides.length === 0 && text.trim()) {
    console.log('📄 textSplitter: No slides created, adding single slide with all text');
    slides.push({
      type: 'content',
      text: text.trim(),
      title: ''
    });
  }

  console.log('✅ textSplitter: Returning', slides.length, 'slides');
  return slides;
}

