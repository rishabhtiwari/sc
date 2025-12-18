import React, { useState, useEffect } from 'react';
import { getRoles, getPermissions, getUsers } from '../services/authService';

const RolesPermissionsPage = () => {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedRole, setSelectedRole] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [rolesRes, permsRes, usersRes] = await Promise.all([
        getRoles(),
        getPermissions(),
        getUsers()
      ]);
      
      setRoles(rolesRes.roles || []);
      setPermissions(permsRes.permissions || []);
      setUsers(usersRes.users || []);
      
      // Select first role by default
      if (rolesRes.roles && rolesRes.roles.length > 0) {
        setSelectedRole(rolesRes.roles[0]);
      }
      
      setError('');
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load roles and permissions. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Group permissions by category
  const groupedPermissions = permissions.reduce((acc, perm) => {
    const category = perm.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(perm);
    return acc;
  }, {});

  // Count users with selected role
  const getUserCountForRole = (roleId) => {
    return users.filter(user => user.role_id === roleId).length;
  };

  // Check if permission is in selected role
  const hasPermission = (permissionCode) => {
    return selectedRole?.permissions?.includes(permissionCode) || false;
  };

  // Category display names
  const categoryNames = {
    news: 'News Management',
    video: 'Video Management',
    audio: 'Audio Management',
    user: 'User Management',
    role: 'Role Management',
    customer: 'Customer Management',
    config: 'Configuration Management',
    dashboard: 'Dashboard & Analytics',
    youtube: 'YouTube Management',
    audit: 'Audit Logs',
    other: 'Other'
  };

  return (
    <div>
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-gray-600">Loading roles and permissions...</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="grid grid-cols-12 divide-x divide-gray-200">
            {/* Roles List */}
            <div className="col-span-3 bg-gray-50">
              <div className="p-4 border-b border-gray-200">
                <h3 className="font-semibold text-gray-900">Roles</h3>
              </div>
              <div className="divide-y divide-gray-200">
                {roles.map((role) => (
                  <button
                    key={role.role_id}
                    onClick={() => setSelectedRole(role)}
                    className={`
                      w-full text-left p-4 hover:bg-gray-100 transition-colors
                      ${selectedRole?.role_id === role.role_id ? 'bg-indigo-50 border-l-4 border-indigo-600' : ''}
                    `}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{role.name}</div>
                        <div className="text-xs text-gray-500 mt-1">
                          {getUserCountForRole(role.role_id)} users
                        </div>
                      </div>
                      {selectedRole?.role_id === role.role_id && (
                        <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Role Details */}
            <div className="col-span-9">
              {selectedRole ? (
                <div>
                  {/* Role Header */}
                  <div className="p-6 border-b border-gray-200">
                    <div className="flex items-start justify-between">
                      <div>
                        <h2 className="text-xl font-bold text-gray-900">{selectedRole.name}</h2>
                        <p className="text-gray-600 mt-1">{selectedRole.description}</p>
                        <div className="flex items-center gap-4 mt-3">
                          <span className="text-sm text-gray-500">
                            Users with this role: <span className="font-semibold">{getUserCountForRole(selectedRole.role_id)}</span>
                          </span>
                          {selectedRole.is_system_role && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">
                              System Role
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Permissions */}
                  <div className="p-6">
                    <h3 className="font-semibold text-gray-900 mb-4">
                      Permissions ({selectedRole.permissions?.length || 0})
                    </h3>
                    
                    <div className="space-y-6">
                      {Object.entries(groupedPermissions).map(([category, perms]) => (
                        <div key={category}>
                          <h4 className="font-medium text-gray-900 mb-3">
                            {categoryNames[category] || category}
                          </h4>
                          <div className="grid grid-cols-2 gap-3">
                            {perms.map((perm) => (
                              <div
                                key={perm.permission_id}
                                className={`
                                  flex items-start gap-3 p-3 rounded-lg border
                                  ${hasPermission(perm.code)
                                    ? 'bg-green-50 border-green-200'
                                    : 'bg-gray-50 border-gray-200'
                                  }
                                `}
                              >
                                <div className="flex-shrink-0 mt-0.5">
                                  {hasPermission(perm.code) ? (
                                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                    </svg>
                                  ) : (
                                    <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                    </svg>
                                  )}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm font-medium text-gray-900">
                                    {perm.code}
                                  </div>
                                  <div className="text-xs text-gray-500 mt-0.5">
                                    {perm.description}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-gray-500">
                  Select a role to view details
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RolesPermissionsPage;

