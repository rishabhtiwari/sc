import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useToast } from '../hooks/useToast';
import projectService from '../services/projectService';
import ConfirmDialog from '../components/common/ConfirmDialog';

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
                className="group bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-lg transition-all"
              >
                {/* Thumbnail */}
                <div
                  className="aspect-video bg-gray-100 relative cursor-pointer"
                  onClick={() => handleOpenProject(project.project_id)}
                >
                  {project.thumbnail ? (
                    <img
                      src={project.thumbnail}
                      alt={project.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <svg className="w-12 h-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                  )}
                  {/* Delete Button Overlay */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteClick(project);
                    }}
                    className="absolute top-2 right-2 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-all shadow flex items-center justify-center"
                    title="Delete project"
                  >
                    ✕
                  </button>
                </div>

                {/* Project Info */}
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 truncate mb-1">
                    {project.name || 'Untitled Project'}
                  </h3>
                  <p className="text-xs text-gray-500 mb-2">
                    {formatDate(project.updated_at || project.created_at)}
                  </p>
                  {project.template_id && (
                    <div className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded inline-block">
                      {project.template_id.replace('_', ' ')}
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
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={confirmDelete}
        onCancel={() => setDeleteDialog({ isOpen: false, project: null })}
        variant="danger"
      />
    </div>
  );
};

export default ProjectsPage;

