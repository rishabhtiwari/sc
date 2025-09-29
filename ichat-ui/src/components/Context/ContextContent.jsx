import React, { useState, useEffect } from 'react';
import apiService from '../../services/apiService';

const ContextContent = () => {
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newRepo, setNewRepo] = useState({
    name: '',
    url: '',
    branch: 'main',
    accessToken: ''
  });

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      setLoading(true);
      const response = await apiService.getRepositories();
      setRepositories(response.repositories || []);
    } catch (error) {
      console.error('Failed to load repositories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRepository = async (e) => {
    e.preventDefault();
    try {
      const response = await apiService.addRepository(newRepo);
      if (response.status === 'success') {
        await loadRepositories();
        setShowAddForm(false);
        setNewRepo({ name: '', url: '', branch: 'main', accessToken: '' });
      }
    } catch (error) {
      console.error('Failed to add repository:', error);
    }
  };

  const handleRemoveRepository = async (repoId) => {
    try {
      const response = await apiService.removeRepository(repoId);
      if (response.status === 'success') {
        await loadRepositories();
      }
    } catch (error) {
      console.error('Failed to remove repository:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-gray-400 mb-4"></i>
          <p className="text-gray-500">Loading repositories...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-green-500 to-blue-600 flex items-center justify-center">
                <i className="fas fa-cog text-white"></i>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-800">Context Setup</h2>
                <p className="text-gray-600">Repository context management</p>
              </div>
            </div>
            <button
              onClick={() => setShowAddForm(true)}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <i className="fas fa-plus"></i>
              Add Repository
            </button>
          </div>

          {showAddForm && (
            <div className="mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50">
              <h3 className="text-lg font-medium text-gray-800 mb-4">Add New Repository</h3>
              <form onSubmit={handleAddRepository} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Repository Name
                    </label>
                    <input
                      type="text"
                      value={newRepo.name}
                      onChange={(e) => setNewRepo({ ...newRepo, name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="my-awesome-project"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Repository URL
                    </label>
                    <input
                      type="url"
                      value={newRepo.url}
                      onChange={(e) => setNewRepo({ ...newRepo, url: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="https://github.com/user/repo.git"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Branch
                    </label>
                    <input
                      type="text"
                      value={newRepo.branch}
                      onChange={(e) => setNewRepo({ ...newRepo, branch: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="main"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Access Token (optional)
                    </label>
                    <input
                      type="password"
                      value={newRepo.accessToken}
                      onChange={(e) => setNewRepo({ ...newRepo, accessToken: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="ghp_xxxxxxxxxxxx"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                  >
                    Add Repository
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="mt-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Connected Repositories</h3>
            {repositories.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <i className="fas fa-code-branch text-4xl mb-4"></i>
                <p>No repositories connected yet</p>
                <p className="text-sm">Connect your first repository to get started</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {repositories.map((repo) => (
                  <div key={repo.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <i className="fas fa-code-branch text-xl text-gray-600"></i>
                        <div>
                          <h4 className="font-medium text-gray-800">{repo.name}</h4>
                          <p className="text-sm text-gray-500">{repo.url}</p>
                          <p className="text-xs text-gray-400">Branch: {repo.branch}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveRepository(repo.id)}
                        className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContextContent;
