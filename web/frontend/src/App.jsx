import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import Login from './components/Login.jsx';
import Dashboard from './components/Dashboard.jsx';
import './App.css';
import { useAuth } from './contexts/AuthContext';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import QueueViewer from './components/QueueViewer.jsx';
import CompetitionLists from './components/CompetitionLists.jsx';
import { FaUserCircle, FaSignOutAlt, FaTachometerAlt, FaClipboardList, FaGraduationCap } from 'react-icons/fa';

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
  const { isAuthenticated, loading, user, logout } = useAuth();

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
      <nav className="navbar navbar-expand-lg navbar-dark bg-gradient-primary shadow-sm mb-4" style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}}>
        <div className="container-fluid">
          <Link className="navbar-brand fw-bold d-flex align-items-center" to="/dashboard">
            <FaTachometerAlt className="me-2" /> PKOnline
          </Link>
          <div className="collapse navbar-collapse">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              <li className="nav-item">
                <Link className="nav-link d-flex align-items-center" to="/dashboard">
                  <FaTachometerAlt className="me-1" /> Дашборд
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link d-flex align-items-center" to="/processing">
                  <FaClipboardList className="me-1" /> Обработка заявлений
                </Link>
              </li>
              <li className="nav-item">
                <Link className="nav-link d-flex align-items-center" to="/competition-lists">
                  <FaGraduationCap className="me-1" /> Конкурсные списки
                </Link>
              </li>
            </ul>
            <div className="d-flex align-items-center ms-auto">
              <span className="text-white fw-semibold me-3 d-flex align-items-center">
                <FaUserCircle className="me-1" style={{fontSize: '1.5rem'}} />
                {user?.fio || user?.username || 'Пользователь'}
              </span>
              <button className="btn btn-outline-light btn-sm d-flex align-items-center" onClick={logout}>
                <FaSignOutAlt className="me-1" /> Выйти
              </button>
            </div>
          </div>
        </div>
      </nav>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/processing" element={<QueueViewer />} />
        <Route path="/competition-lists" element={<CompetitionLists />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </>
  );
}

export default App; 