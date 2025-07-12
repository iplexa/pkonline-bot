import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import Charts from './Charts';

const Dashboard = () => {
    const { isAuthenticated, user, logout } = useAuth();
    const [data, setData] = useState({
        employees: [],
        recentApplications: [],
        queueStats: {}
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedQueue, setSelectedQueue] = useState(null);
    const [queueApplications, setQueueApplications] = useState([]);

    useEffect(() => {
        if (isAuthenticated) {
            fetchData();
            const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
            return () => clearInterval(interval);
        }
    }, [isAuthenticated]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [employeesRes, applicationsRes, statsRes] = await Promise.all([
                axios.get('/dashboard/employees/status'),
                axios.get('/dashboard/applications/recent'),
                axios.get('/dashboard/queues/statistics')
            ]);

            setData({
                employees: employeesRes.data,
                recentApplications: applicationsRes.data,
                queueStats: statsRes.data
            });
        } catch (err) {
            console.error('Error fetching data:', err);
            if (err.response?.status === 401) {
                logout();
            } else {
                setError('Ошибка загрузки данных');
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchQueueApplications = async (queueType) => {
        try {
            const response = await axios.get(`/dashboard/queues/${queueType}/applications`);
            setQueueApplications(response.data);
            setSelectedQueue(queueType);
        } catch (err) {
            console.error('Error fetching queue applications:', err);
        }
    };

    const closeQueueView = () => {
        setSelectedQueue(null);
        setQueueApplications([]);
    };

    const handleLogout = () => {
        logout();
    };

    if (loading) {
        return (
            <div className="container mt-5">
                <div className="d-flex justify-content-center">
                    <div className="spinner-border text-primary" role="status">
                        <span className="visually-hidden">Загрузка...</span>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mt-5">
                <div className="alert alert-danger" role="alert">
                    {error}
                </div>
            </div>
        );
    }

    if (selectedQueue) {
        return (
            <div className="container mt-4">
                <div className="d-flex justify-content-between align-items-center mb-4">
                    <h1>Очередь: {data.queueStats.find(q => q.queue_type === selectedQueue)?.queue_name || selectedQueue}</h1>
                    <button onClick={closeQueueView} className="btn btn-outline-secondary">
                        <i className="fas fa-arrow-left me-2"></i>
                        Назад к дашборду
                    </button>
                </div>
                
                <div className="card">
                    <div className="card-header">
                        <h5>Заявления в очереди</h5>
                    </div>
                    <div className="card-body">
                        {queueApplications.length > 0 ? (
                            <div className="table-responsive">
                                <table className="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>ID</th>
                                            <th>ФИО</th>
                                            <th>Статус</th>
                                            <th>Время подачи</th>
                                            <th>Обработано</th>
                                            <th>Обработал</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {queueApplications.map((app, index) => (
                                            <tr key={index}>
                                                <td>{app.id}</td>
                                                <td>{app.fio}</td>
                                                <td>
                                                    <span className={`badge ${
                                                        app.status === 'accepted' ? 'bg-success' :
                                                        app.status === 'rejected' ? 'bg-danger' :
                                                        app.status === 'in_progress' ? 'bg-warning' :
                                                        app.status === 'queued' ? 'bg-secondary' :
                                                        'bg-info'
                                                    }`}>
                                                        {app.status}
                                                    </span>
                                                </td>
                                                <td>{new Date(app.submitted_at).toLocaleString('ru-RU')}</td>
                                                <td>{app.processed_at ? new Date(app.processed_at).toLocaleString('ru-RU') : '-'}</td>
                                                <td>{app.processed_by_fio || '-'}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p>Нет заявлений в очереди</p>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="container mt-4">
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h1>Панель управления</h1>
                <div className="d-flex align-items-center">
                    <span className="me-3">Пользователь: {user?.fio}</span>
                    <button onClick={handleLogout} className="btn btn-outline-danger">
                        Выйти
                    </button>
                </div>
            </div>
            
            <div className="row">
                <div className="col-md-6 mb-4">
                    <div className="card">
                        <div className="card-header">
                            <h5>Статус сотрудников</h5>
                        </div>
                        <div className="card-body">
                            {data.employees.length > 0 ? (
                                <ul className="list-group list-group-flush">
                                    {data.employees.map((employee, index) => (
                                        <li key={index} className="list-group-item">
                                            <div className="d-flex justify-content-between align-items-start">
                                                <div className="flex-grow-1">
                                                    <div className="d-flex align-items-center mb-1">
                                                        <strong>{employee.fio}</strong>
                                                        {employee.is_admin && <span className="badge bg-primary ms-2">Админ</span>}
                                                    </div>
                                                    {employee.current_task && (
                                                        <div className="small text-warning mb-1">
                                                            <i className="fas fa-tasks me-1"></i>
                                                            {employee.current_task}
                                                        </div>
                                                    )}
                                                    {employee.last_processed && (
                                                        <div className="small text-success mb-1">
                                                            <i className="fas fa-check-circle me-1"></i>
                                                            Последнее: {employee.last_processed}
                                                        </div>
                                                    )}
                                                    {employee.work_duration && (
                                                        <div className="small text-muted">
                                                            <i className="fas fa-clock me-1"></i>
                                                            {employee.work_duration}
                                                        </div>
                                                    )}
                                                </div>
                                                <span className={`badge ${
                                                    employee.status === 'На рабочем месте' ? 'bg-success' :
                                                    employee.status === 'На перерыве' ? 'bg-warning' :
                                                    employee.status === 'Рабочий день завершен' ? 'bg-info' :
                                                    'bg-secondary'
                                                }`}>
                                                    {employee.status}
                                                </span>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p>Нет данных о сотрудниках</p>
                            )}
                        </div>
                    </div>
                </div>

                <div className="col-md-6 mb-4">
                    <div className="card">
                        <div className="card-header">
                            <h5>Статистика очередей</h5>
                        </div>
                        <div className="card-body">
                            {data.queueStats.length > 0 ? (
                                <div>
                                    {data.queueStats.map((queue, index) => (
                                        <div key={index} className="mb-3 p-3 border rounded">
                                            <div className="d-flex justify-content-between align-items-center mb-2">
                                                <h6 className="mb-0">{queue.queue_name}</h6>
                                                <button 
                                                    onClick={() => fetchQueueApplications(queue.queue_type)}
                                                    className="btn btn-sm btn-outline-primary"
                                                >
                                                    <i className="fas fa-eye me-1"></i>
                                                    Просмотр
                                                </button>
                                            </div>
                                            <div className="row text-center">
                                                <div className="col-3">
                                                    <div className="small text-muted">Всего</div>
                                                    <div className="fw-bold">{queue.total}</div>
                                                </div>
                                                <div className="col-3">
                                                    <div className="small text-muted">В очереди</div>
                                                    <div className="fw-bold text-secondary">{queue.queued}</div>
                                                </div>
                                                <div className="col-3">
                                                    <div className="small text-muted">В работе</div>
                                                    <div className="fw-bold text-warning">{queue.in_progress}</div>
                                                </div>
                                                <div className="col-3">
                                                    <div className="small text-muted">Обработано</div>
                                                    <div className="fw-bold text-success">{queue.accepted + queue.rejected + queue.problem}</div>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p>Нет данных о очередях</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Диаграммы статистики */}
            <Charts />

            <div className="row">
                <div className="col-12">
                    <div className="card">
                        <div className="card-header">
                            <h5>Последние обработанные заявления</h5>
                        </div>
                        <div className="card-body">
                            {data.recentApplications.length > 0 ? (
                                <div className="table-responsive">
                                    <table className="table table-striped">
                                        <thead>
                                            <tr>
                                                <th>ID</th>
                                                <th>ФИО</th>
                                                <th>Очередь</th>
                                                <th>Статус</th>
                                                <th>Время обработки</th>
                                                <th>Обработал</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {data.recentApplications.map((app, index) => (
                                                <tr key={index}>
                                                    <td>{app.id}</td>
                                                    <td>{app.fio}</td>
                                                    <td>{app.queue_type}</td>
                                                    <td>
                                                        <span className={`badge ${
                                                            app.status === 'accepted' ? 'bg-success' :
                                                            app.status === 'rejected' ? 'bg-danger' :
                                                            'bg-warning'
                                                        }`}>
                                                            {app.status}
                                                        </span>
                                                    </td>
                                                    <td>{new Date(app.processed_at).toLocaleString('ru-RU')}</td>
                                                    <td>{app.processed_by_fio || '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            ) : (
                                <p>Нет обработанных заявлений</p>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard; 