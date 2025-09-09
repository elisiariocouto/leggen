import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bell,
  MessageSquare,
  Send,
  Trash2,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Settings,
  TestTube
} from 'lucide-react';
import { apiClient } from '../lib/api';
import LoadingSpinner from './LoadingSpinner';
import type { NotificationSettings, NotificationService } from '../types/api';

export default function Notifications() {
  const [testService, setTestService] = useState('');
  const [testMessage, setTestMessage] = useState('Test notification from Leggen');
  const queryClient = useQueryClient();

  const {
    data: settings,
    isLoading: settingsLoading,
    error: settingsError,
    refetch: refetchSettings
  } = useQuery<NotificationSettings>({
    queryKey: ['notificationSettings'],
    queryFn: apiClient.getNotificationSettings,
  });

  const {
    data: services,
    isLoading: servicesLoading,
    error: servicesError,
    refetch: refetchServices
  } = useQuery<NotificationService[]>({
    queryKey: ['notificationServices'],
    queryFn: apiClient.getNotificationServices,
  });

  const testMutation = useMutation({
    mutationFn: apiClient.testNotification,
    onSuccess: () => {
      // Could show a success toast here
      console.log('Test notification sent successfully');
    },
    onError: (error) => {
      console.error('Failed to send test notification:', error);
    },
  });

  const deleteServiceMutation = useMutation({
    mutationFn: apiClient.deleteNotificationService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notificationSettings'] });
      queryClient.invalidateQueries({ queryKey: ['notificationServices'] });
    },
  });

  if (settingsLoading || servicesLoading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <LoadingSpinner message="Loading notifications..." />
      </div>
    );
  }

  if (settingsError || servicesError) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center text-center">
          <div>
            <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load notifications</h3>
            <p className="text-gray-600 mb-4">
              Unable to connect to the Leggen API. Make sure the server is running on localhost:8000.
            </p>
            <button
              onClick={() => {
                refetchSettings();
                refetchServices();
              }}
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleTestNotification = () => {
    if (!testService) return;

    testMutation.mutate({
      service: testService,
      message: testMessage,
    });
  };

  const handleDeleteService = (serviceName: string) => {
    if (confirm(`Are you sure you want to delete the ${serviceName} notification service?`)) {
      deleteServiceMutation.mutate(serviceName);
    }
  };

  return (
    <div className="space-y-6">
      {/* Test Notification Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <TestTube className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900">Test Notifications</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Service
            </label>
            <select
              value={testService}
              onChange={(e) => setTestService(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a service...</option>
              {services?.map((service) => (
                <option key={service.name} value={service.name}>
                  {service.name} {service.enabled ? '(Enabled)' : '(Disabled)'}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message
            </label>
            <input
              type="text"
              value={testMessage}
              onChange={(e) => setTestMessage(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Test message..."
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={handleTestNotification}
            disabled={!testService || testMutation.isPending}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="h-4 w-4 mr-2" />
            {testMutation.isPending ? 'Sending...' : 'Send Test Notification'}
          </button>
        </div>
      </div>

      {/* Notification Services */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Bell className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-medium text-gray-900">Notification Services</h3>
          </div>
          <p className="text-sm text-gray-600 mt-1">Manage your notification services</p>
        </div>

        {!services || services.length === 0 ? (
          <div className="p-6 text-center">
            <Bell className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No notification services configured</h3>
            <p className="text-gray-600">
              Configure notification services in your backend to receive alerts.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {services.map((service) => (
              <div key={service.name} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="p-3 bg-gray-100 rounded-full">
                      {service.name.toLowerCase().includes('discord') ? (
                        <MessageSquare className="h-6 w-6 text-gray-600" />
                      ) : service.name.toLowerCase().includes('telegram') ? (
                        <Send className="h-6 w-6 text-gray-600" />
                      ) : (
                        <Bell className="h-6 w-6 text-gray-600" />
                      )}
                    </div>
                    <div>
                      <h4 className="text-lg font-medium text-gray-900 capitalize">
                        {service.name}
                      </h4>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          service.enabled
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {service.enabled ? (
                            <CheckCircle className="h-3 w-3 mr-1" />
                          ) : (
                            <AlertCircle className="h-3 w-3 mr-1" />
                          )}
                          {service.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          service.configured
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {service.configured ? 'Configured' : 'Not Configured'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDeleteService(service.name)}
                      disabled={deleteServiceMutation.isPending}
                      className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md transition-colors"
                      title={`Delete ${service.name} service`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Notification Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Settings className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900">Notification Settings</h3>
        </div>

        {settings && (
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Filters</h4>
              <div className="bg-gray-50 rounded-md p-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Case Insensitive Filters
                    </label>
                    <p className="text-sm text-gray-900">
                      {settings.filters.case_insensitive.length > 0
                        ? settings.filters.case_insensitive.join(', ')
                        : 'None'
                      }
                    </p>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Case Sensitive Filters
                    </label>
                    <p className="text-sm text-gray-900">
                      {settings.filters.case_sensitive && settings.filters.case_sensitive.length > 0
                        ? settings.filters.case_sensitive.join(', ')
                        : 'None'
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="text-sm text-gray-600">
              <p>Configure notification settings through your backend API to customize filters and service configurations.</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
