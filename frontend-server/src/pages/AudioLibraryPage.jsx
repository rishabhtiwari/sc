import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, Button, Input } from '../components/common';
import { useToast } from '../hooks/useToast';
import { useAudioLibrary } from '../hooks/useAudioLibrary';
import AudioCard from '../components/AudioStudio/AudioLibrary/AudioCard';

/**
 * Audio Library Page - Full page view of all audio files with modern, appealing design
 */
const AudioLibraryPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const { audioFiles, loading, fetchAudioFiles, deleteAudio } = useAudioLibrary();

  // Check if opened from Design Editor
  const fromEditor = location.state?.fromEditor || false;
  const returnPath = location.state?.returnPath || '/design-editor';

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('all');
  const [selectedVoice, setSelectedVoice] = useState('all');
  const [selectedType, setSelectedType] = useState('all');

  // Load audio files on mount
  useEffect(() => {
    fetchAudioFiles();
  }, []);

  // Extract unique values for filters
  const languages = ['all', ...new Set(audioFiles.map(a => a.language || 'en'))];
  const voices = ['all', ...new Set(audioFiles.map(a => a.generation_config?.voice).filter(Boolean))];
  const types = ['all', ...new Set(audioFiles.map(a => a.type).filter(Boolean))];

  // Filter audio files
  const filteredAudioFiles = audioFiles.filter(audio => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesName = audio.name?.toLowerCase().includes(query);
      const matchesText = audio.generation_config?.text?.toLowerCase().includes(query);
      if (!matchesName && !matchesText) return false;
    }

    // Language filter
    if (selectedLanguage !== 'all' && (audio.language || 'en') !== selectedLanguage) {
      return false;
    }

    // Voice filter
    if (selectedVoice !== 'all' && audio.generation_config?.voice !== selectedVoice) {
      return false;
    }

    // Type filter
    if (selectedType !== 'all' && audio.type !== selectedType) {
      return false;
    }

    return true;
  });

  const handleDelete = async (audioId) => {
    if (!window.confirm('Are you sure you want to delete this audio?')) {
      return;
    }

    try {
      await deleteAudio(audioId);
      showToast('Audio deleted successfully', 'success');
    } catch (error) {
      showToast(error.message || 'Failed to delete audio', 'error');
    }
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedLanguage('all');
    setSelectedVoice('all');
    setSelectedType('all');
  };

  const handleAddToCanvas = (audioData) => {
    if (fromEditor) {
      // Split returnPath into pathname and search to preserve query params
      const [pathname, search] = returnPath.split('?');
      const fullPath = search ? `${pathname}?${search}` : pathname;

      // Navigate back to editor with selected audio, preserving the return path and tool
      navigate(fullPath, {
        state: {
          addAsset: {
            type: 'audio',
            title: audioData.title || audioData.name,
            url: audioData.url,
            audio_url: audioData.audio_url,
            duration: audioData.duration,
            audio_id: audioData.audio_id,  // Include audio_id from library
            libraryId: audioData.audio_id,  // Also set as libraryId
            assetId: audioData.audio_id     // And as assetId for consistency
          },
          returnTool: location.state?.returnTool  // Preserve the selected tool
        }
      });
      showToast('Opening in Design Editor', 'success');
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'voiceover': return '🎙️';
      case 'music': return '🎵';
      case 'sound_effect': return '🔊';
      default: return '🎵';
    }
  };

  const getLanguageName = (code) => {
    const languageNames = {
      'en': 'English',
      'hi': 'Hindi',
      'zh': 'Chinese',
      'ja': 'Japanese',
      'ko': 'Korean',
      'ar': 'Arabic',
      'bn': 'Bengali'
    };
    return languageNames[code] || code.toUpperCase();
  };

  const hasActiveFilters = searchQuery || selectedLanguage !== 'all' || selectedVoice !== 'all' || selectedType !== 'all';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-16 h-16 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-2xl">🎵</span>
            </div>
          </div>
          <p className="text-gray-700">Loading your audio library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Content */}
      <div className="space-y-6 p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-2xl">🎵</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Audio Library
                </h1>
                <p className="text-gray-600 text-sm mt-1">
                  Discover and manage your audio collection
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gray-50 px-4 py-2 rounded-lg border border-gray-200">
                <p className="text-sm text-gray-700">
                  <span className="font-semibold text-gray-900">{filteredAudioFiles.length}</span>
                  <span className="text-gray-500 mx-1">/</span>
                  <span className="font-semibold text-gray-900">{audioFiles.length}</span>
                  <span className="text-gray-600 ml-1">files</span>
                </p>
              </div>
              {fromEditor ? (
                <Button
                  onClick={() => navigate(returnPath)}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Editor
                </Button>
              ) : (
                <Button
                  onClick={() => navigate('/audio-studio')}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  🎙️ Audio Studio
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Filters Card */}
        <div className="bg-white rounded-lg shadow border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                <span className="text-xl">🔍</span>
              </div>
              <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
            </div>
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="px-3 py-1.5 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium flex items-center space-x-1"
              >
                <span>✕</span>
                <span>Clear All</span>
              </button>
            )}
          </div>

          <div className="space-y-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1">
                <span>🔎</span>
                <span>Search</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by name or text..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white placeholder-gray-400 text-gray-900"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <span className="text-lg">✕</span>
                  </button>
                )}
              </div>
            </div>

            {/* Filter Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Language Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1">
                  <span>🌍</span>
                  <span>Language</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white appearance-none cursor-pointer text-gray-900"
                  >
                    {languages.map(lang => (
                      <option key={lang} value={lang}>
                        {lang === 'all' ? 'All Languages' : getLanguageName(lang)}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Voice Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1">
                  <span>🎤</span>
                  <span>Voice / Speaker</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white appearance-none cursor-pointer text-gray-900"
                  >
                    <option value="all">All Voices</option>
                    {voices.filter(v => v !== 'all').map(voice => (
                      <option key={voice} value={voice}>
                        {voice}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Type Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-1">
                  <span>🎼</span>
                  <span>Category / Type</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white appearance-none cursor-pointer text-gray-900"
                  >
                    <option value="all">All Types</option>
                    {types.filter(t => t !== 'all').map(type => (
                      <option key={type} value={type}>
                        {getTypeIcon(type)} {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Active Filters Badge */}
        {hasActiveFilters && (
          <div className="flex items-center justify-center">
            <div className="bg-blue-50 px-4 py-2 rounded-lg border border-blue-200 flex items-center space-x-2">
              <span className="text-lg">🔍</span>
              <span className="text-sm font-medium text-blue-700">Filters Active</span>
            </div>
          </div>
        )}

        {/* Audio Grid */}
        {filteredAudioFiles.length === 0 ? (
          <div className="bg-white rounded-lg shadow border border-gray-200 p-16 text-center">
            <div className="max-w-md mx-auto">
              <div className="text-6xl mb-4 opacity-40">🎵</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                {audioFiles.length === 0 ? 'Your library is empty' : 'No matching audio files'}
              </h3>
              <p className="text-gray-600 mb-6">
                {audioFiles.length === 0
                  ? 'Start creating amazing audio content in the Audio Studio'
                  : 'Try adjusting your filters to discover more audio files'
                }
              </p>
              {audioFiles.length === 0 && (
                <button
                  onClick={() => window.location.href = '/audio-studio'}
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium inline-flex items-center space-x-2"
                >
                  <span>✨</span>
                  <span>Create Your First Audio</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredAudioFiles.map((audio) => (
              <AudioCard
                key={audio.audio_id}
                audio={audio}
                onDelete={handleDelete}
                onAddToCanvas={fromEditor ? handleAddToCanvas : undefined}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AudioLibraryPage;

