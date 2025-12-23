import React, { useState } from 'react';
import ProductVideoPage from './ProductVideoPage';

const EcommercePage = () => {
  const [activeTab, setActiveTab] = useState('products');

  const tabs = [
    { id: 'products', label: 'Products', icon: '📦' },
    // Future tabs can be added here
    // { id: 'orders', label: 'Orders', icon: '📋' },
    // { id: 'customers', label: 'Customers', icon: '👥' },
    // { id: 'analytics', label: 'Analytics', icon: '📊' },
  ];

  return (
    <div className="h-full flex flex-col bg-neutral-50">
      {/* Page Header */}
      <div className="bg-white border-b border-neutral-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">E-commerce</h1>
            <p className="text-sm text-neutral-600 mt-1">
              Manage your e-commerce products, videos, and content
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="mt-6 flex gap-2 border-b border-neutral-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center gap-2 px-4 py-2.5 font-medium text-sm transition-all
                border-b-2 -mb-px
                ${activeTab === tab.id
                  ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                  : 'border-transparent text-neutral-600 hover:text-neutral-900 hover:bg-neutral-50'
                }
              `}
            >
              <span className="text-lg">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'products' && <ProductVideoPage embedded={true} />}
        {/* Future tab content */}
        {/* {activeTab === 'orders' && <OrdersPage />} */}
        {/* {activeTab === 'customers' && <CustomersPage />} */}
        {/* {activeTab === 'analytics' && <AnalyticsPage />} */}
      </div>
    </div>
  );
};

export default EcommercePage;

