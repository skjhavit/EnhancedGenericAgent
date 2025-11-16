/**
 * Main App component
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@stores/authStore';
import { ChatContainer } from '@components/chat/ChatContainer';
import { Login } from '@components/auth/Login';
import { Register } from '@components/auth/Register';
import { Dashboard } from '@components/dashboard/Dashboard';
import { AdminPanel } from '@components/admin/AdminPanel';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};

const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAuthStore();
  return isAuthenticated && user?.role === 'admin' ? (
    <>{children}</>
  ) : (
    <Navigate to="/" />
  );
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/chat/:sessionId"
          element={
            <ProtectedRoute>
              <ChatContainer />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminPanel />
            </AdminRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
