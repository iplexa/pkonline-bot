import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext.jsx';

const Login = () => {
    const [fio, setFio] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (!fio.trim() || !password) {
            setError('Пожалуйста, введите ФИО и пароль');
            setLoading(false);
            return;
        }

        const result = await login(fio.trim(), password);
        if (!result.success) {
            setError(result.error);
        }
        setLoading(false);
    };

    return (
        <div className="login-container">
            <div className="login-background">
                <div className="login-card">
                    <div className="login-header text-center mb-4">
                        <div className="login-logo mb-3">
                            <i className="fas fa-shield-alt fa-3x text-primary"></i>
                        </div>
                        <h2 className="fw-bold text-dark mb-2">PK Online Dashboard</h2>
                        <p className="text-muted mb-0">Войдите в систему для доступа к панели управления</p>
                    </div>

                    <form onSubmit={handleSubmit} className="login-form">
                        <div className="mb-3">
                            <label htmlFor="fio" className="form-label fw-semibold">
                                <i className="fas fa-user me-2 text-primary"></i>
                                ФИО
                            </label>
                            <input
                                type="text"
                                className={`form-control ${error ? 'is-invalid' : ''}`}
                                id="fio"
                                placeholder="Введите ваше ФИО"
                                value={fio}
                                onChange={(e) => setFio(e.target.value)}
                                disabled={loading}
                            />
                        </div>
                        <div className="mb-4">
                            <label htmlFor="password" className="form-label fw-semibold">
                                <i className="fas fa-lock me-2 text-primary"></i>
                                Пароль
                            </label>
                            <input
                                type="password"
                                className={`form-control ${error ? 'is-invalid' : ''}`}
                                id="password"
                                placeholder="Введите пароль"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                disabled={loading}
                            />
                            {error && (
                                <div className="invalid-feedback d-block">
                                    <i className="fas fa-exclamation-triangle me-1"></i>
                                    {error}
                                </div>
                            )}
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary w-100 py-3 fw-semibold"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner-border spinner-border-sm me-2" role="status"></span>
                                    Вход в систему...
                                </>
                            ) : (
                                <>
                                    <i className="fas fa-sign-in-alt me-2"></i>
                                    Войти
                                </>
                            )}
                        </button>
                    </form>

                    <div className="login-footer text-center mt-4">
                        <small className="text-muted">
                            <i className="fas fa-info-circle me-1"></i>
                            Для получения доступа обратитесь к администратору
                        </small>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login; 