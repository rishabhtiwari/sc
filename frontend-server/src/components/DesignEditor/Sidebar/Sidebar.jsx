import React, { useState } from 'react';
import AIToolsPanel from './AIToolsPanel';
import SlidesPanel from './SlidesPanel';
import TextPanel from './TextPanel';
import ImagesPanel from './ImagesPanel';
import MediaPanel from './MediaPanel';
import ElementsPanel from './ElementsPanel';

/**
 * Sidebar Component - Tool Selection
 * Organized sections: AI, Slides, Text, Images, Audio, Video, Elements
 */
const Sidebar = ({
  selectedTool,
  onSelectTool,
  onAddElement,
  onAddMultiplePages,
  onAddAudioTrack,
  currentBackground,
  onBackgroundChange,
  audioTracks,
  onAudioSelect,
  onAudioDeleteRequest,
  videoTracks,
  onVideoDeleteRequest,
  uploadedAudio,
  onUploadedAudioChange,
  uploadedVideo,
  onUploadedVideoChange,
  onOpenAudioLibrary
}) => {
  const [expandedPanel, setExpandedPanel] = useState(null);

  const tools = [
    {
      id: 'ai-tools',
      name: 'AI',
      icon: '🤖',
      description: 'AI-powered tools',
      panel: AIToolsPanel
    },
    {
      id: 'slides',
      name: 'Slides',
      icon: '📊',
      description: 'Create slides from text',
      panel: SlidesPanel
    },
    {
      id: 'text',
      name: 'Text',
      icon: '📝',
      description: 'Add text elements',
      panel: TextPanel
    },
    {
      id: 'images',
      name: 'Images',
      icon: '🖼️',
      description: 'Add images',
      panel: ImagesPanel
    },
    {
      id: 'audio',
      name: 'Audio',
      icon: '🎵',
      description: 'Add audio',
      panel: MediaPanel
    },
    {
      id: 'video',
      name: 'Video',
      icon: '🎬',
      description: 'Add videos',
      panel: MediaPanel
    },
    {
      id: 'elements',
      name: 'Elements',
      icon: '⭐',
      description: 'Shapes & Icons',
      panel: ElementsPanel
    }
  ];

  const handleToolClick = (toolId) => {
    if (expandedPanel === toolId) {
      setExpandedPanel(null);
      onSelectTool(null);
    } else {
      setExpandedPanel(toolId);
      onSelectTool(toolId);
    }
  };

  const activeTool = tools.find(t => t.id === expandedPanel);
  const ActivePanel = activeTool?.panel;

  return (
    <div className="flex h-full bg-white border-r border-gray-200">
      {/* Tool Icons Bar */}
      <div className="w-20 bg-gray-50 border-r border-gray-200 flex flex-col items-center py-4 gap-2">
        {tools.map((tool) => (
          <button
            key={tool.id}
            onClick={() => handleToolClick(tool.id)}
            className={`
              w-14 h-14 rounded-lg flex flex-col items-center justify-center gap-1
              transition-all duration-200
              ${expandedPanel === tool.id
                ? 'bg-blue-100 text-blue-600 shadow-sm'
                : 'hover:bg-gray-100 text-gray-600'
              }
            `}
            title={tool.description}
          >
            <span className="text-2xl">{tool.icon}</span>
            <span className="text-xs font-medium">{tool.name.split(' ')[0]}</span>
          </button>
        ))}
      </div>

      {/* Expanded Tool Panel */}
      {expandedPanel && ActivePanel && (
        <div className="w-80 bg-white overflow-y-auto">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">{activeTool.name}</h2>
            <p className="text-sm text-gray-500 mt-1">{activeTool.description}</p>
          </div>
          <div className="p-4">
            <ActivePanel
              onAddElement={onAddElement}
              onAddMultiplePages={onAddMultiplePages}
              onAddAudioTrack={onAddAudioTrack}
              currentBackground={currentBackground}
              onBackgroundChange={onBackgroundChange}
              panelType={expandedPanel}
              audioTracks={audioTracks}
              onAudioSelect={onAudioSelect}
              onAudioDeleteRequest={onAudioDeleteRequest}
              videoTracks={videoTracks}
              onVideoDeleteRequest={onVideoDeleteRequest}
              uploadedMedia={expandedPanel === 'audio' ? uploadedAudio : uploadedVideo}
              onUploadedMediaChange={expandedPanel === 'audio' ? onUploadedAudioChange : onUploadedVideoChange}
              onOpenAudioLibrary={onOpenAudioLibrary}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;

