import React, { useState } from 'react';
import { AIContentGenerator, MediaUploader, Button, Card } from '@/components/common';

/**
 * Example: Social Media Post Creation using Reusable Components
 * 
 * This shows how to use the components for social media content generation
 */
const SocialMediaExample = ({ onComplete }) => {
  const [platform, setPlatform] = useState('twitter');
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('professional');
  const [postContent, setPostContent] = useState('');
  const [mediaFiles, setMediaFiles] = useState([]);

  const platforms = [
    { id: 'twitter', name: 'Twitter/X', icon: '🐦', maxChars: 280 },
    { id: 'instagram', name: 'Instagram', icon: '📸', maxChars: 2200 },
    { id: 'linkedin', name: 'LinkedIn', icon: '💼', maxChars: 3000 },
    { id: 'facebook', name: 'Facebook', icon: '👥', maxChars: 63206 }
  ];

  const tones = [
    { id: 'professional', name: 'Professional', emoji: '💼' },
    { id: 'casual', name: 'Casual', emoji: '😊' },
    { id: 'humorous', name: 'Humorous', emoji: '😄' },
    { id: 'inspirational', name: 'Inspirational', emoji: '✨' },
    { id: 'educational', name: 'Educational', emoji: '📚' }
  ];

  const selectedPlatform = platforms.find(p => p.id === platform);

  const handlePost = () => {
    onComplete({
      platform,
      topic,
      tone,
      content: postContent,
      media_files: mediaFiles
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Platform Selection */}
      <Card title="Select Platform">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {platforms.map((p) => (
            <button
              key={p.id}
              onClick={() => setPlatform(p.id)}
              className={`p-4 border rounded-lg text-center transition-all ${
                platform === p.id
                  ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-500'
                  : 'border-gray-300 hover:border-indigo-300'
              }`}
            >
              <div className="text-3xl mb-2">{p.icon}</div>
              <div className="font-semibold">{p.name}</div>
              <div className="text-xs text-gray-500 mt-1">
                Max {p.maxChars} chars
              </div>
            </button>
          ))}
        </div>
      </Card>

      {/* Topic & Tone */}
      <Card title="Post Details">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Topic
            </label>
            <input
              type="text"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="What do you want to post about?"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tone
            </label>
            <div className="grid grid-cols-3 md:grid-cols-5 gap-2">
              {tones.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTone(t.id)}
                  className={`px-3 py-2 border rounded-lg text-sm ${
                    tone === t.id
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-300 hover:border-indigo-300'
                  }`}
                >
                  {t.emoji} {t.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* AI Content Generation */}
      <Card title="Generate Post">
        <AIContentGenerator
          endpoint="/api/social/generate-post"
          inputData={{
            platform,
            topic,
            tone,
            max_chars: selectedPlatform.maxChars
          }}
          initialContent={postContent}
          onContentGenerated={(content) => {
            setPostContent(content);
          }}
          label={`${selectedPlatform.name} Post`}
          placeholder={`Click 'Generate' to create a ${tone} post about ${topic || 'your topic'}`}
          showEditMode={true}
          showSections={false}
        />

        {/* Character Count */}
        {postContent && (
          <div className="mt-2 text-sm text-gray-600">
            {postContent.length} / {selectedPlatform.maxChars} characters
            {postContent.length > selectedPlatform.maxChars && (
              <span className="text-red-600 ml-2">⚠️ Exceeds limit!</span>
            )}
          </div>
        )}
      </Card>

      {/* Media Upload */}
      <Card title="Add Media (Optional)">
        <MediaUploader
          initialFiles={mediaFiles}
          onFilesChange={(files) => setMediaFiles(files)}
          uploadEndpoint="/api/upload"
          acceptedTypes={['image', 'video']}
          maxFiles={platform === 'twitter' ? 4 : 10}
          maxFileSize={platform === 'twitter' ? 5 : 100}
          showPreview={true}
        />
      </Card>

      {/* Preview */}
      {postContent && (
        <Card title="Preview">
          <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                👤
              </div>
              <div className="flex-1">
                <div className="font-semibold">Your Name</div>
                <div className="text-sm text-gray-600">@yourhandle</div>
                <div className="mt-2 whitespace-pre-wrap">{postContent}</div>
                
                {/* Media Preview */}
                {mediaFiles.length > 0 && (
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {mediaFiles.slice(0, 4).map((file, index) => (
                      <div key={index} className="aspect-square bg-gray-200 rounded">
                        {/* Media preview would go here */}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => window.history.back()}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handlePost}
          disabled={!postContent || !topic || postContent.length > selectedPlatform.maxChars}
        >
          📤 Post to {selectedPlatform.name}
        </Button>
      </div>
    </div>
  );
};

export default SocialMediaExample;

