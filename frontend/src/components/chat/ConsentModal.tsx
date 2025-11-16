/**
 * Consent modal for Human-in-the-Loop approvals
 */

import React from 'react';
import { ConsentRequest } from '@types/index';
import { websocketService } from '@services/websocket';

interface ConsentModalProps {
  request: ConsentRequest;
}

export const ConsentModal: React.FC<ConsentModalProps> = ({ request }) => {
  const handleApprove = () => {
    websocketService.sendConsentResponse(true);
  };

  const handleReject = () => {
    websocketService.sendConsentResponse(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">
          🔒 Approval Required
        </h2>

        <div className="mb-6">
          <h3 className="font-semibold text-gray-700 mb-2">
            Tool: {request.tool_name}
          </h3>
          <p className="text-gray-600 mb-4">{request.tool_description}</p>

          <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
            <p className="text-sm text-yellow-800">
              <strong>Impact:</strong> {request.action_impact}
            </p>
          </div>

          <div className="bg-gray-50 rounded p-4">
            <h4 className="font-semibold text-gray-700 mb-2">Parameters:</h4>
            <pre className="text-sm text-gray-600 overflow-auto">
              {JSON.stringify(request.parameters, null, 2)}
            </pre>
          </div>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            onClick={handleReject}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Reject
          </button>
          <button
            onClick={handleApprove}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  );
};
