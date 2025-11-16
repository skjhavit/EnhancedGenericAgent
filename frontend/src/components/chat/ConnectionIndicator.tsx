/**
 * Connection status indicator
 */

import React from 'react';
import { ConnectionStatus } from '@types/index';

interface ConnectionIndicatorProps {
  status: ConnectionStatus;
}

export const ConnectionIndicator: React.FC<ConnectionIndicatorProps> = ({
  status,
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500',
          text: 'Connected',
          icon: '●',
        };
      case 'reconnecting':
        return {
          color: 'bg-yellow-500',
          text: 'Reconnecting...',
          icon: '●',
        };
      case 'disconnected':
        return {
          color: 'bg-red-500',
          text: 'Disconnected',
          icon: '●',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className="flex items-center space-x-2">
      <span className={`w-2 h-2 rounded-full ${config.color}`} />
      <span className="text-sm text-gray-600">{config.text}</span>
    </div>
  );
};
