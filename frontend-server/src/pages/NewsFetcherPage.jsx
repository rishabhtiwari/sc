import React, { useState, useEffect } from 'react';
import { Card, Button } from '../components/common';
import { useApi } from '../hooks/useApi';
import { useToast } from '../hooks/useToast';
import { newsService } from '../services';
import StatsCards from '../components/NewsFetcher/StatsCards';
import NewsTable from '../components/NewsFetcher/NewsTable';
import SeedUrlsTable from '../components/NewsFetcher/SeedUrlsTable';
import SeedUrlModal from '../components/NewsFetcher/SeedUrlModal';
import NewsFilters from '../components/NewsFetcher/NewsFilters';

/**
 * News Fetcher Page - Manage news sources and view articles
 */
const NewsFetcherPage = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState({
    category: '',
    language: '',
    country: '',
    pageSize: 25,
    page: 1,
  });
  const [categories, setCategories] = useState({});
  const [languages, setLanguages] = useState({});
  const [countries, setCountries] = useState({});
  const [isSeedModalOpen, setIsSeedModalOpen] = useState(false);
  const [editingSeed, setEditingSeed] = useState(null);

  const { showToast } = useToast();

  // API hooks
  const { data: statsData, loading: statsLoading, execute: fetchStats } = useApi(newsService.getNewsStats);
  const { data: newsData, loading: newsLoading, execute: fetchNews } = useApi(newsService.getNews);
  const { data: seedsData, loading: seedsLoading, execute: fetchSeeds } = useApi(newsService.getSeedUrls);
  const { execute: runFetchJob, loading: fetchJobLoading } = useApi(newsService.runNewsFetchJob);

  // Load initial data
  useEffect(() => {
    fetchStats();
    loadFiltersData();
  }, []);

  // Load news when tab changes or filters change
  useEffect(() => {
    if (activeTab === 'news') {
      fetchNews(filters);
    }
  }, [activeTab, filters]);

  // Load seeds when tab changes
  useEffect(() => {
    if (activeTab === 'seeds') {
      fetchSeeds();
    }
  }, [activeTab]);

  const loadFiltersData = async () => {
    try {
      const [categoriesRes, filtersRes] = await Promise.all([
        newsService.getCategories(),
        newsService.getFilters(),
      ]);

      if (categoriesRes.data?.categories) {
        setCategories(categoriesRes.data.categories);
      }

      if (filtersRes.data) {
        setLanguages(filtersRes.data.languages || {});
        setCountries(filtersRes.data.countries || {});
      }
    } catch (error) {
      console.error('Failed to load filters:', error);
    }
  };

  const handleRunFetchJob = async () => {
    try {
      await runFetchJob();
      showToast('News fetch job started successfully!', 'success');
      setTimeout(() => fetchStats(), 2000);
    } catch (error) {
      showToast('Failed to start fetch job', 'error');
    }
  };

  const handleRefreshStats = () => {
    fetchStats();
    showToast('Statistics refreshed', 'success');
  };

  const handleViewArticle = (article) => {
    // TODO: Implement article detail view
    console.log('View article:', article);
    showToast('Article detail view coming soon', 'info');
  };

  const handleAddSeed = () => {
    setEditingSeed(null);
    setIsSeedModalOpen(true);
  };

  const handleEditSeed = (seed) => {
    setEditingSeed(seed);
    setIsSeedModalOpen(true);
  };

  const handleSaveSeed = async (seedData) => {
    try {
      if (editingSeed) {
        await newsService.updateSeedUrl(editingSeed.partner_id, seedData);
        showToast('Seed URL updated successfully', 'success');
      } else {
        await newsService.addSeedUrl(seedData);
        showToast('Seed URL added successfully', 'success');
      }
      fetchSeeds();
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to save seed URL');
    }
  };

  const handleToggleSeedStatus = async (partnerId, isActive) => {
    try {
      await newsService.updateSeedUrl(partnerId, { is_active: isActive });
      showToast(`Seed URL ${isActive ? 'enabled' : 'disabled'}`, 'success');
      fetchSeeds();
    } catch (error) {
      showToast('Failed to update seed URL status', 'error');
    }
  };

  const handleDeleteSeed = async (partnerId) => {
    if (!window.confirm('Are you sure you want to delete this seed URL?')) {
      return;
    }

    try {
      await newsService.deleteSeedUrl(partnerId);
      showToast('Seed URL deleted successfully', 'success');
      fetchSeeds();
    } catch (error) {
      showToast('Failed to delete seed URL', 'error');
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters({ ...newFilters, page: 1 });
  };

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage });
  };

  const stats = statsData?.data || statsData;
  const articles = newsData?.data?.articles || [];
  const pagination = newsData?.data?.pagination || {};
  const seedUrls = seedsData?.data?.seed_urls || seedsData?.seed_urls || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">📰 News Fetcher Management</h1>
        <p className="text-gray-600">Manage news sources, view articles, and monitor fetching status</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm p-2 flex gap-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
            activeTab === 'overview'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          📊 Overview
        </button>
        <button
          onClick={() => setActiveTab('news')}
          className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
            activeTab === 'news'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          📰 News Records
        </button>
        <button
          onClick={() => setActiveTab('seeds')}
          className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
            activeTab === 'seeds'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          🌱 Seed URLs
        </button>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <StatsCards stats={stats} loading={statsLoading} />

          <Card title="Quick Actions">
            <div className="flex flex-wrap gap-3">
              <Button
                variant="primary"
                icon="🚀"
                onClick={handleRunFetchJob}
                loading={fetchJobLoading}
              >
                Run Fetch Job Now
              </Button>
              <Button
                variant="success"
                icon="➕"
                onClick={handleAddSeed}
              >
                Add Seed URL
              </Button>
              <Button
                variant="warning"
                icon="🔄"
                onClick={handleRefreshStats}
              >
                Refresh Stats
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* News Records Tab */}
      {activeTab === 'news' && (
        <Card title="News Records">
          <NewsFilters
            filters={filters}
            categories={categories}
            languages={languages}
            countries={countries}
            onFilterChange={handleFilterChange}
            loading={newsLoading}
          />

          <NewsTable
            articles={articles}
            loading={newsLoading}
            onViewArticle={handleViewArticle}
          />

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(filters.page - 1)}
                disabled={filters.page === 1}
              >
                Previous
              </Button>
              <span className="px-4 py-2 text-sm text-gray-600">
                Page {filters.page} of {pagination.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(filters.page + 1)}
                disabled={filters.page === pagination.total_pages}
              >
                Next
              </Button>
            </div>
          )}
        </Card>
      )}

      {/* Seed URLs Tab */}
      {activeTab === 'seeds' && (
        <Card
          title="Seed URLs"
          actions={
            <Button variant="primary" icon="➕" onClick={handleAddSeed}>
              Add Seed URL
            </Button>
          }
        >
          <SeedUrlsTable
            seedUrls={seedUrls}
            loading={seedsLoading}
            onEdit={handleEditSeed}
            onToggleStatus={handleToggleSeedStatus}
            onDelete={handleDeleteSeed}
          />
        </Card>
      )}

      {/* Seed URL Modal */}
      <SeedUrlModal
        isOpen={isSeedModalOpen}
        onClose={() => setIsSeedModalOpen(false)}
        onSave={handleSaveSeed}
        seedUrl={editingSeed}
      />
    </div>
  );
};

export default NewsFetcherPage;

