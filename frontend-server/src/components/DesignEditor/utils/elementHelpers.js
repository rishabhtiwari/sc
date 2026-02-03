/**
 * Helper to create a default page
 */
export const createDefaultPage = (index = 0) => ({
  id: `page-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  name: `Page ${index + 1}`,
  elements: [],
  background: { type: 'solid', color: '#ffffff' },
  duration: 5,
  startTime: index * 5
});

/**
 * Helper to create a default element based on type
 */
export const createDefaultElement = (type, overrides = {}) => {
  const baseElement = {
    id: `element-${Date.now()}`,
    type,
    x: 100,
    y: 100,
    ...overrides
  };

  // Type-specific defaults
  switch (type) {
    case 'text':
      return {
        ...baseElement,
        width: 300,
        height: 100,
        text: 'Add a heading',
        fontSize: 32,
        fontFamily: 'Arial',
        color: '#000000',
        fontWeight: 'bold'
      };

    case 'video':
      return {
        ...baseElement,
        width: 640,
        height: 360,
        duration: 0,
        trimStart: 0,
        trimEnd: null,
        volume: 100,
        muted: false
      };

    case 'image':
      return {
        ...baseElement,
        width: 400,
        height: 300
      };

    case 'shape':
      return {
        ...baseElement,
        width: 150,
        height: 150,
        shapeType: 'rectangle',
        fill: '#3B82F6',
        stroke: '#1E40AF',
        strokeWidth: 2
      };

    case 'icon':
      return {
        ...baseElement,
        width: 64,
        height: 64,
        fontSize: 48,
        color: '#000000'
      };

    case 'sticker':
      return {
        ...baseElement,
        width: 80,
        height: 80,
        fontSize: 64
      };

    default:
      return {
        ...baseElement,
        width: 200,
        height: 100
      };
  }
};

/**
 * Validate element has required properties
 */
export const validateElement = (element) => {
  if (!element.id) {
    console.error('Element missing id:', element);
    return false;
  }

  if (!element.type) {
    console.error('Element missing type:', element);
    return false;
  }

  if (element.x === undefined || element.y === undefined) {
    console.error('Element missing position:', element);
    return false;
  }

  return true;
};

/**
 * Compute video tracks from pages
 */
export const computeVideoTracks = (pages) => {
  console.log('🔄 Computing video tracks from pages...');
  const videoTracks = [];
  let currentTime = 0;

  pages.forEach((page, pageIndex) => {
    const videoElements = page.elements.filter(el => el.type === 'video');
    console.log(`  📄 Page ${pageIndex} (${page.name}): ${videoElements.length} video(s)`);

    videoElements.forEach((videoEl, videoIndex) => {
      const track = {
        id: videoEl.id,
        name: videoEl.name || `Video ${videoIndex + 1}`,
        src: videoEl.src,
        duration: videoEl.duration || 0,
        startTime: currentTime,
        trimStart: videoEl.trimStart || 0,
        trimEnd: videoEl.trimEnd || videoEl.duration,
        volume: videoEl.volume !== undefined ? videoEl.volume : 100,
        muted: videoEl.muted || false
      };

      console.log(`    🎬 Video ${videoIndex}: ${track.name} (${track.duration}s at ${track.startTime}s)`);
      videoTracks.push(track);
    });

    currentTime += page.duration || 5;
  });

  console.log(`✅ Computed ${videoTracks.length} video track(s) from pages`);
  return videoTracks;
};

