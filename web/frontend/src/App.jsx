import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login.jsx';
import Dashboard from './components/Dashboard.jsx';
import './App.css';
import { useAuth } from './contexts/AuthContext';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import QueueViewer from './components/QueueViewer.jsx';

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <AppContent />
      </div>
    </AuthProvider>
  );
}

function AppContent() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Загрузка...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) return <Login />;

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-light bg-light mb-4">
        <div className="container-fluid">
          <Link className="navbar-brand fw-bold" to="/dashboard">PKOnline</Link>
          <div className="collapse navbar-collapse">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              <li className="nav-item">
                <Link className="nav-link" to="/dashboard">Дашборд</Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link" to="/processing">Обработка заявлений</Link>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/processing" element={<QueueViewer />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App; 