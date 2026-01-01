import React, { useState, useEffect } from 'react';
import { Card, Button, Input } from '../components/common';
import { useToast } from '../hooks/useToast';
import { useAudioLibrary } from '../hooks/useAudioLibrary';
import AudioCard from '../components/AudioStudio/AudioLibrary/AudioCard';

/**
 * Audio Library Page - Full page view of all audio files with modern, appealing design
 */
const AudioLibraryPage = () => {
  const { showToast } = useToast();
  const { audioFiles, loading, fetchAudioFiles, deleteAudio } = useAudioLibrary();

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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50">
        <div className="text-center">
          <div className="relative mb-6">
            <div className="w-20 h-20 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto"></div>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl">🎵</span>
            </div>
          </div>
          <p className="text-lg font-semibold text-gray-700">Loading your audio library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 relative overflow-hidden">
      {/* Animated Background Blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      {/* Content */}
      <div className="relative space-y-6 p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-500 via-blue-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg transform hover:scale-110 transition-transform">
                <span className="text-4xl">🎵</span>
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-pink-600 bg-clip-text text-transparent">
                  Audio Library
                </h1>
                <p className="text-gray-600 mt-1 font-medium">
                  Discover and manage your audio collection
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-purple-100 to-blue-100 px-6 py-3 rounded-xl border border-purple-200">
                <p className="text-sm font-semibold text-gray-700">
                  <span className="text-purple-600 text-xl">{filteredAudioFiles.length}</span>
                  <span className="text-gray-500 mx-1">/</span>
                  <span className="text-blue-600 text-xl">{audioFiles.length}</span>
                  <span className="text-gray-600 ml-2">files</span>
                </p>
              </div>
              <Button
                onClick={() => window.location.href = '/audio-studio'}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-xl hover:shadow-xl transition-all transform hover:scale-105 font-semibold"
              >
                🎙️ Audio Studio
              </Button>
            </div>
          </div>
        </div>

        {/* Filters Card */}
        <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-8 hover:shadow-2xl transition-shadow">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-2xl">🔍</span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900">Filters</h2>
            </div>
            {hasActiveFilters && (
              <button
                onClick={handleClearFilters}
                className="px-5 py-2.5 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl hover:shadow-lg transition-all transform hover:scale-105 font-semibold text-sm flex items-center space-x-2"
              >
                <span>✕</span>
                <span>Clear All</span>
              </button>
            )}
          </div>

          <div className="space-y-6">
            {/* Search */}
            <div className="group">
              <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center space-x-2">
                <span>🔎</span>
                <span>Search</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by name or text..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-5 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all bg-white/70 backdrop-blur-sm placeholder-gray-400 text-gray-900 font-medium"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <span className="text-xl">✕</span>
                  </button>
                )}
              </div>
            </div>

            {/* Filter Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Language Filter */}
              <div className="group">
                <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center space-x-2">
                  <span>🌍</span>
                  <span>Language</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full px-5 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all bg-white/70 backdrop-blur-sm appearance-none cursor-pointer text-gray-900 font-medium"
                  >
                    {languages.map(lang => (
                      <option key={lang} value={lang}>
                        {lang === 'all' ? 'All Languages' : getLanguageName(lang)}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Voice Filter */}
              <div className="group">
                <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center space-x-2">
                  <span>🎤</span>
                  <span>Voice / Speaker</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedVoice}
                    onChange={(e) => setSelectedVoice(e.target.value)}
                    className="w-full px-5 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all bg-white/70 backdrop-blur-sm appearance-none cursor-pointer text-gray-900 font-medium"
                  >
                    <option value="all">All Voices</option>
                    {voices.filter(v => v !== 'all').map(voice => (
                      <option key={voice} value={voice}>
                        {voice}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Type Filter */}
              <div className="group">
                <label className="block text-sm font-bold text-gray-700 mb-3 flex items-center space-x-2">
                  <span>🎼</span>
                  <span>Category / Type</span>
                </label>
                <div className="relative">
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full px-5 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all bg-white/70 backdrop-blur-sm appearance-none cursor-pointer text-gray-900 font-medium"
                  >
                    <option value="all">All Types</option>
                    {types.filter(t => t !== 'all').map(type => (
                      <option key={type} value={type}>
                        {getTypeIcon(type)} {type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')}
                      </option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none">
                    <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            <div className="bg-gradient-to-r from-purple-100 to-blue-100 px-6 py-3 rounded-xl border border-purple-200 flex items-center space-x-2">
              <span className="text-2xl">🔍</span>
              <span className="text-sm font-semibold text-purple-700">Filters Active</span>
            </div>
          </div>
        )}

        {/* Audio Grid */}
        {filteredAudioFiles.length === 0 ? (
          <div className="bg-white/80 backdrop-blur-lg rounded-3xl shadow-xl border border-white/50 p-16 text-center">
            <div className="max-w-md mx-auto">
              <div className="w-32 h-32 bg-gradient-to-br from-purple-100 via-blue-100 to-pink-100 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                <span className="text-6xl">🎵</span>
              </div>
              <h3 className="text-3xl font-bold text-gray-900 mb-3">
                {audioFiles.length === 0 ? 'Your library is empty' : 'No matching audio files'}
              </h3>
              <p className="text-gray-600 mb-8 text-lg">
                {audioFiles.length === 0
                  ? 'Start creating amazing audio content in the Audio Studio'
                  : 'Try adjusting your filters to discover more audio files'
                }
              </p>
              {audioFiles.length === 0 && (
                <button
                  onClick={() => window.location.href = '/audio-studio'}
                  className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl hover:shadow-2xl transition-all transform hover:scale-105 font-bold text-lg inline-flex items-center space-x-2"
                >
                  <span>✨</span>
                  <span>Create Your First Audio</span>
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredAudioFiles.map((audio, index) => (
              <div
                key={audio.audio_id}
                className="transform transition-all duration-300 hover:scale-105"
                style={{
                  animation: `fadeInUp 0.5s ease-out ${index * 0.05}s both`
                }}
              >
                <AudioCard
                  audio={audio}
                  onDelete={handleDelete}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Custom Animations */}
      <style jsx>{`
        @keyframes blob {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          33% {
            transform: translate(30px, -50px) scale(1.1);
          }
          66% {
            transform: translate(-20px, 20px) scale(0.9);
          }
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-blob {
          animation: blob 7s infinite;
        }

        .animation-delay-2000 {
          animation-delay: 2s;
        }

        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default AudioLibraryPage;

