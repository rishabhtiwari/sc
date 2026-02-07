import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '../hooks/useToast';
import projectService from '../services/projectService';
import { ConfirmDialog, PreviewUploadModal } from '../components/common';

/**
 * Projects Page - Full page view of all design projects
 */
const ProjectsPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { showToast } = useToast();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialog, setDeleteDialog] = useState({ isOpen: false, project: null });
  const [previewModal, setPreviewModal] = useState({ isOpen: false, project: null });

  // Check if opened from Design Editor
  const fromEditor = location.state?.fromEditor || false;

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const data = await projectService.listProjects();
      setProjects(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      showToast('Failed to load projects', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (project) => {
    setDeleteDialog({ isOpen: true, project });
  };

  const confirmDelete = async () => {
    if (!deleteDialog.project) return;

    try {
      await projectService.deleteProject(deleteDialog.project.project_id);
      showToast('Project deleted successfully', 'success');
      setDeleteDialog({ isOpen: false, project: null });
      fetchProjects(); // Refresh list
    } catch (error) {
      console.error('Failed to delete project:', error);
      showToast('Failed to delete project', 'error');
      setDeleteDialog({ isOpen: false, project: null });
    }
  };

  const handleOpenProject = (projectId) => {
    navigate(`/design-editor?project=${projectId}`);
  };

  const handleCreateNew = () => {
    navigate('/design-editor');
  };

  const handlePreviewClick = (project, e) => {
    e.stopPropagation();

    // Get the latest export
    const latestExport = project.exports && project.exports.length > 0
      ? project.exports[project.exports.length - 1]
      : null;

    if (!latestExport) {
      showToast('No exported video found. Please export the project first.', 'warning');
      return;
    }

    setPreviewModal({ isOpen: true, project, export: latestExport });
  };

  // Filter projects based on search query
  const filteredProjects = projects.filter(project => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return project.name?.toLowerCase().includes(query) ||
           project.description?.toLowerCase().includes(query);
  });

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-14 h-14 bg-blue-600 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-3xl">📁</span>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
                <p className="text-gray-600 mt-1">
                  Manage your design projects
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {fromEditor && (
                <button
                  onClick={() => navigate('/design-editor')}
                  className="px-6 py-3 bg-gray-600 text-white rounded-lg font-medium hover:bg-gray-700 transition-colors shadow-sm flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Editor
                </button>
              )}
              <button
                onClick={handleCreateNew}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors shadow-sm flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create New Project
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search and Stats */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex-1 max-w-md">
            <div className="relative">
              <input
                type="text"
                placeholder="Search projects..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <svg
                className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          <div className="text-sm text-gray-600">
            <span className="font-semibold text-gray-900">{filteredProjects.length}</span> of{' '}
            <span className="font-semibold text-gray-900">{projects.length}</span> projects
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-lg font-medium">No projects found</p>
            <p className="text-sm mt-1">
              {searchQuery ? 'Try adjusting your search' : 'Create your first project to get started'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredProjects.map((project) => (
              <div
                key={project.project_id}
                className="group bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-2xl hover:border-blue-300 transition-all duration-300 transform hover:-translate-y-1"
              >
                {/* Thumbnail */}
                <div
                  className="aspect-video bg-gradient-to-br from-blue-50 to-purple-50 relative cursor-pointer overflow-hidden"
                  onClick={() => handleOpenProject(project.project_id)}
                >
                  {project.thumbnail ? (
                    <img
                      src={project.thumbnail}
                      alt={project.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <div className="text-center">
                        <svg className="w-16 h-16 text-blue-200 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-xs text-gray-400">No Preview</p>
                      </div>
                    </div>
                  )}

                  {/* Hover Overlay with Actions */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <div className="absolute bottom-0 left-0 right-0 p-3 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenProject(project.project_id);
                          }}
                          className="px-3 py-1.5 bg-white/90 hover:bg-white text-gray-900 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          Open
                        </button>
                        {(project.exports && project.exports.length > 0) && (
                          <button
                            onClick={(e) => handlePreviewClick(project, e)}
                            className="px-3 py-1.5 bg-blue-500/90 hover:bg-blue-600 text-white rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5"
                            title="Preview and Upload to Platform"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                            Upload
                          </button>
                        )}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteClick(project);
                        }}
                        className="w-8 h-8 bg-red-500/90 hover:bg-red-600 text-white rounded-lg transition-colors flex items-center justify-center"
                        title="Delete project"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {/* Status Badges */}
                  <div className="absolute top-2 left-2 flex flex-col gap-1.5">
                    {project.status && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        project.status === 'published'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {project.status}
                      </span>
                    )}
                    {project.exports && project.exports.length > 0 && (
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 flex items-center gap-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Exported
                      </span>
                    )}
                  </div>
                </div>

                {/* Project Info */}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 truncate mb-1.5 group-hover:text-blue-600 transition-colors">
                    {project.name || 'Untitled Project'}
                  </h3>

                  {/* Stats Row */}
                  <div className="flex items-center gap-3 text-xs text-gray-500 mb-2">
                    <div className="flex items-center gap-1">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {formatDate(project.updated_at || project.created_at)}
                    </div>
                    {project.pages?.length > 0 && (
                      <div className="flex items-center gap-1">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                        </svg>
                        {project.pages.length} slides
                      </div>
                    )}
                  </div>

                  {/* Template Tag */}
                  {project.template_id && (
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs text-gray-600 bg-gradient-to-r from-blue-50 to-purple-50 px-2.5 py-1 rounded-full border border-blue-100">
                        📐 {project.template_id.replace('_', ' ')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        title="Delete Project"
        message={`Are you sure you want to delete "${deleteDialog.project?.name || 'this project'}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={confirmDelete}
        onClose={() => setDeleteDialog({ isOpen: false, project: null })}
        variant="danger"
      />

      {/* Preview and Upload Modal */}
      <PreviewUploadModal
        isOpen={previewModal.isOpen}
        onClose={() => setPreviewModal({ isOpen: false, project: null, export: null })}
        asset={previewModal.project && previewModal.export ? {
          name: previewModal.project.name || 'Untitled Project',
          description: previewModal.project.description || '',
          preview_url: previewModal.export.output_url,
          url: previewModal.export.output_url,
          video_url: previewModal.export.output_url,
          type: 'video',
          project_id: previewModal.project.project_id,
          export_id: previewModal.export.export_id,
          duration: previewModal.export.duration,
          file_size: previewModal.export.file_size
        } : null}
      />
    </div>
  );
};

export default ProjectsPage;

