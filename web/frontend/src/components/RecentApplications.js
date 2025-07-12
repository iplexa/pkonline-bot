import React, { useState, useEffect } from 'react';
import axios from 'axios';

const RecentApplications = () => {
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchApplications = async () => {
        try {
            const response = await axios.get('/dashboard/applications/recent');
            setApplications(response.data);
        } catch (error) {
            console.error('Ошибка загрузки заявлений:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchApplications();
        const interval = setInterval(fetchApplications, 30000);
        return () => clearInterval(interval);
    }, []);

    const getQueueTypeName = (type) => {
        const names = {
            'lk': 'Личный кабинет',
            'epgu': 'ЕПГУ',
            'epgu_mail': 'Почта',
            'epgu_problem': 'Проблемные'
        };
        return names[type] || type;
    };

    const getStatusBadge = (status) => {
        const statusConfig = {
            'accepted': { bg: 'success', text: 'Принято', icon: 'fas fa-check' },
            'rejected': { bg: 'danger', text: 'Отклонено', icon: 'fas fa-times' },
            'problem': { bg: 'warning', text: 'Проблема', icon: 'fas fa-exclamation-triangle' }
        };
        
        const config = statusConfig[status] || { bg: 'secondary', text: status, icon: 'fas fa-question' };
        
        return (
            <span className={`badge bg-${config.bg}`}>
                <i className={`${config.icon} me-1`}></i>
                {config.text}
            </span>
        );
    };

    const getQueueTypeBadge = (type) => {
        const typeConfig = {
            'lk': { bg: 'primary', icon: 'fas fa-user' },
            'epgu': { bg: 'info', icon: 'fas fa-globe' },
            'epgu_mail': { bg: 'success', icon: 'fas fa-envelope' },
            'epgu_problem': { bg: 'warning', icon: 'fas fa-exclamation' }
        };
        
        const config = typeConfig[type] || { bg: 'secondary', icon: 'fas fa-list' };
        
        return (
            <span className={`badge bg-${config.bg}`}>
                <i className={`${config.icon} me-1`}></i>
                {getQueueTypeName(type)}
            </span>
        );
    };

    if (loading) {
        return (
            <div className="p-4 text-center">
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Загрузка...</span>
                </div>
            </div>
        );
    }

    if (applications.length === 0) {
        return (
            <div className="p-4 text-center text-muted">
                <i className="fas fa-inbox fa-3x mb-3"></i>
                <p>Нет обработанных заявлений</p>
            </div>
        );
    }

    return (
        <div className="recent-applications">
            <div className="table-responsive">
                <table className="table table-hover mb-0">
                    <thead className="table-light">
                        <tr>
                            <th>ID</th>
                            <th>ФИО</th>
                            <th>Очередь</th>
                            <th>Статус</th>
                            <th>Обработал</th>
                            <th>Дата обработки</th>
                        </tr>
                    </thead>
                    <tbody>
                        {applications.map((app) => (
                            <tr key={app.id} className="application-row">
                                <td>
                                    <span className="fw-bold text-primary">#{app.id}</span>
                                </td>
                                <td>
                                    <div className="fw-semibold">{app.fio}</div>
                                    <small className="text-muted">
                                        Подано: {new Date(app.submitted_at).toLocaleDateString('ru-RU')}
                                    </small>
                                </td>
                                <td>
                                    {getQueueTypeBadge(app.queue_type)}
                                </td>
                                <td>
                                    {getStatusBadge(app.status)}
                                </td>
                                <td>
                                    {app.processed_by_fio ? (
                                        <span className="fw-medium">{app.processed_by_fio}</span>
                                    ) : (
                                        <span className="text-muted">—</span>
                                    )}
                                </td>
                                <td>
                                    {app.processed_at ? (
                                        <div>
                                            <div className="fw-medium">
                                                {new Date(app.processed_at).toLocaleDateString('ru-RU')}
                                            </div>
                                            <small className="text-muted">
                                                {new Date(app.processed_at).toLocaleTimeString('ru-RU')}
                                            </small>
                                        </div>
                                    ) : (
                                        <span className="text-muted">—</span>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default RecentApplications; 