import React, { useState } from 'react';
import { AIContentGenerator, AudioSelector, Button, Card } from '@/components/common';

/**
 * Example: News Article Summary & Audio using Reusable Components
 * 
 * This shows how to use the same components for a different use case:
 * generating summaries and audio for news articles
 */
const NewsArticleExample = ({ article, onComplete }) => {
  const [summary, setSummary] = useState(article?.summary || '');
  const [audioUrl, setAudioUrl] = useState(article?.audio_url || null);
  const [audioConfig, setAudioConfig] = useState(article?.audio_config || {});

  const handleGenerateSummary = async () => {
    // Summary will be generated via AIContentGenerator
  };

  const handleGenerateAudio = async () => {
    // Audio will be generated via AudioSelector
  };

  const handleSave = () => {
    onComplete({
      article_id: article._id,
      summary,
      audio_url: audioUrl,
      audio_config: audioConfig
    });
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Article Info */}
      <Card title="Article Information">
        <div className="space-y-2">
          <div>
            <span className="font-semibold">Title:</span> {article.title}
          </div>
          <div>
            <span className="font-semibold">Source:</span> {article.source}
          </div>
          <div>
            <span className="font-semibold">Published:</span>{' '}
            {new Date(article.published_at).toLocaleDateString()}
          </div>
        </div>
      </Card>

      {/* AI Summary Generation */}
      <Card title="Generate Summary">
        <AIContentGenerator
          endpoint={`/api/news/${article._id}/generate-summary`}
          inputData={{
            article_title: article.title,
            article_content: article.content,
            article_source: article.source
          }}
          initialContent={summary}
          onContentGenerated={(content) => {
            setSummary(content);
          }}
          label="Article Summary"
          placeholder="Click 'Generate' to create an AI summary of this article"
          showEditMode={true}
          showSections={false}
        />
      </Card>

      {/* Audio Generation (Optional) */}
      <Card title="Generate Audio (Optional)">
        <p className="text-sm text-gray-600 mb-4">
          Generate an audio version of the summary for accessibility or podcast use
        </p>

        <AudioSelector
          endpoint={`/api/news/${article._id}/generate-audio`}
          text={summary}
          initialAudioUrl={audioUrl}
          initialConfig={audioConfig}
          onAudioGenerated={(url, config) => {
            setAudioUrl(url);
            setAudioConfig(config);
          }}
          autoDetectLanguage={true}
        />
      </Card>

      {/* Actions */}
      <div className="flex justify-end gap-4">
        <Button variant="outline" onClick={() => window.history.back()}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={!summary}
        >
          💾 Save Article
        </Button>
      </div>
    </div>
  );
};

export default NewsArticleExample;

