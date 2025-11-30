import React, { useState, useEffect, useRef } from 'react';
import { Card } from '../common';

/**
 * Audio Gallery Component - Display and play audio files
 */
const AudioGallery = ({ onLoadData, onLoadStats }) => {
  const [audioFiles, setAudioFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalFiles, setTotalFiles] = useState(0);
  const [stats, setStats] = useState({ total: 0, pending: 0, generated: 0 });
  const [playingAudio, setPlayingAudio] = useState(null);
  const audioRefs = useRef({});

  // Load stats separately
  const loadStats = async () => {
    try {
      const statsData = await onLoadStats();
      console.log('Audio Stats Data:', statsData);
      setStats({
        total: statsData.total || 0,
        pending: statsData.pending || 0,
        generated: statsData.generated || 0
      });
      console.log('Stats set to:', {
        total: statsData.total || 0,
        pending: statsData.pending || 0,
        generated: statsData.generated || 0
      });
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  // Load audio files
  const loadAudioFiles = async () => {
    setLoading(true);
    try {
      const data = await onLoadData(currentPage, statusFilter);
      setAudioFiles(data.audio_files || []);
      setTotalPages(data.pagination?.pages || 1);
      setTotalFiles(data.pagination?.total || 0);
    } catch (error) {
      console.error('Failed to load audio files:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  // Load data when page or filter changes
  useEffect(() => {
    loadAudioFiles();
  }, [currentPage, statusFilter]);

  // Handle audio play
  const handlePlay = (audioId) => {
    // Pause all other audio
    Object.keys(audioRefs.current).forEach(id => {
      if (id !== audioId && audioRefs.current[id]) {
        audioRefs.current[id].pause();
      }
    });
    setPlayingAudio(audioId);
  };

  // Handle audio pause
  const handlePause = () => {
    setPlayingAudio(null);
  };

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card title="Filters">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">All Audio ({stats.total})</option>
            <option value="pending">Pending ({stats.pending})</option>
            <option value="generated">Generated ({stats.generated})</option>
          </select>

          <div className="ml-auto text-sm text-gray-600">
            Showing {audioFiles.length} of {totalFiles} files
          </div>
        </div>
      </Card>

      {/* Audio Files Grid */}
      <Card title="Audio Files">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
              <p className="text-gray-700 font-semibold">Loading audio files...</p>
            </div>
          </div>
        ) : audioFiles.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎵</div>
            <p className="text-lg text-gray-600">No audio files found</p>
            <p className="text-sm text-gray-500 mt-2">Try changing the filter or generate more audio</p>
          </div>
        ) : (
          <>
            {/* Grid Layout - 3 cards per row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {audioFiles.map((audio) => (
                <div
                  key={audio.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white flex flex-col"
                >
                  {/* Header with Status Icon and Badge */}
                  <div className="flex items-start gap-3 mb-3">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center text-xl flex-shrink-0 ${
                        audio.status === 'generated'
                          ? 'bg-green-100'
                          : 'bg-gray-100'
                      }`}
                    >
                      {audio.status === 'generated' ? '🎵' : '⏳'}
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        audio.status === 'generated'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {audio.status === 'generated' ? '✓ Generated' : '⏳ Pending'}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="text-sm font-medium text-gray-900 mb-2 line-clamp-2 min-h-[2.5rem]" title={audio.title}>
                    {audio.title}
                  </h3>

                  {/* Metadata */}
                  <div className="flex flex-col gap-1 text-xs text-gray-500 mb-3">
                    {audio.voice && (
                      <span className="flex items-center gap-1">
                        <span>🎙️</span>
                        <span>{audio.voice}</span>
                      </span>
                    )}
                    {audio.generated_at && (
                      <span className="flex items-center gap-1">
                        <span>📅</span>
                        <span>{new Date(audio.generated_at).toLocaleDateString()}</span>
                      </span>
                    )}
                    {audio.created_at && !audio.generated_at && (
                      <span className="flex items-center gap-1">
                        <span>📅</span>
                        <span>{new Date(audio.created_at).toLocaleDateString()}</span>
                      </span>
                    )}
                  </div>

                  {/* Audio Player or Pending Message */}
                  <div className="mt-auto">
                    {audio.status === 'generated' && audio.audio_url ? (
                      <div className="bg-gray-50 rounded-lg p-2">
                        <audio
                          ref={(el) => {
                            if (el) audioRefs.current[audio.id] = el;
                          }}
                          controls
                          className="w-full h-8"
                          style={{ maxHeight: '32px' }}
                          onPlay={() => handlePlay(audio.id)}
                          onPause={handlePause}
                          onEnded={handlePause}
                          preload="metadata"
                        >
                          <source src={audio.audio_url} type="audio/wav" />
                          Your browser does not support the audio element.
                        </audio>
                      </div>
                    ) : (
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-2">
                        <p className="text-xs text-blue-800">
                          ℹ️ Audio not yet generated
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ← Previous
                </button>

                <span className="text-sm text-gray-700">
                  Page {currentPage} of {totalPages}
                </span>

                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
};

export default AudioGallery;

