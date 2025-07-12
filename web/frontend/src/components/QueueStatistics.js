import React, { useState, useEffect } from 'react';
import axios from 'axios';

const QueueStatistics = () => {
    const [statistics, setStatistics] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchStatistics = async () => {
        try {
            const response = await axios.get('/dashboard/queues/statistics');
            setStatistics(response.data);
        } catch (error) {
            console.error('Ошибка загрузки статистики:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatistics();
        const interval = setInterval(fetchStatistics, 30000);
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

    const getQueueIcon = (type) => {
        const icons = {
            'lk': 'fas fa-user',
            'epgu': 'fas fa-globe',
            'epgu_mail': 'fas fa-envelope',
            'epgu_problem': 'fas fa-exclamation-triangle'
        };
        return icons[type] || 'fas fa-list';
    };

    const getQueueColor = (type) => {
        const colors = {
            'lk': 'primary',
            'epgu': 'info',
            'epgu_mail': 'success',
            'epgu_problem': 'warning'
        };
        return colors[type] || 'secondary';
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

    return (
        <div className="queue-statistics">
            <div className="row g-3">
                {statistics.map((stat) => (
                    <div key={stat.queue_type} className="col-12">
                        <div className={`card border-${getQueueColor(stat.queue_type)} border-2`}>
                            <div className="card-body p-3">
                                <div className="d-flex align-items-center mb-3">
                                    <div className={`bg-${getQueueColor(stat.queue_type)} bg-opacity-10 rounded-circle p-2 me-3`}>
                                        <i className={`${getQueueIcon(stat.queue_type)} text-${getQueueColor(stat.queue_type)}`}></i>
                                    </div>
                                    <div>
                                        <h6 className="mb-0 fw-bold">{getQueueTypeName(stat.queue_type)}</h6>
                                        <small className="text-muted">Всего: {stat.total}</small>
                                    </div>
                                </div>

                                <div className="row g-2">
                                    <div className="col-6">
                                        <div className="d-flex align-items-center">
                                            <span className="badge bg-warning me-2">{stat.queued}</span>
                                            <small>В очереди</small>
                                        </div>
                                    </div>
                                    <div className="col-6">
                                        <div className="d-flex align-items-center">
                                            <span className="badge bg-info me-2">{stat.in_progress}</span>
                                            <small>В обработке</small>
                                        </div>
                                    </div>
                                    <div className="col-6">
                                        <div className="d-flex align-items-center">
                                            <span className="badge bg-success me-2">{stat.accepted}</span>
                                            <small>Принято</small>
                                        </div>
                                    </div>
                                    <div className="col-6">
                                        <div className="d-flex align-items-center">
                                            <span className="badge bg-danger me-2">{stat.rejected}</span>
                                            <small>Отклонено</small>
                                        </div>
                                    </div>
                                    {stat.problem > 0 && (
                                        <div className="col-12">
                                            <div className="d-flex align-items-center">
                                                <span className="badge bg-secondary me-2">{stat.problem}</span>
                                                <small>Проблемные</small>
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Progress bar */}
                                {stat.total > 0 && (
                                    <div className="mt-3">
                                        <div className="progress" style={{ height: '6px' }}>
                                            <div 
                                                className="progress-bar bg-success" 
                                                style={{ width: `${(stat.accepted / stat.total) * 100}%` }}
                                                title={`Принято: ${stat.accepted}`}
                                            ></div>
                                            <div 
                                                className="progress-bar bg-danger" 
                                                style={{ width: `${(stat.rejected / stat.total) * 100}%` }}
                                                title={`Отклонено: ${stat.rejected}`}
                                            ></div>
                                            <div 
                                                className="progress-bar bg-warning" 
                                                style={{ width: `${(stat.queued / stat.total) * 100}%` }}
                                                title={`В очереди: ${stat.queued}`}
                                            ></div>
                                            <div 
                                                className="progress-bar bg-info" 
                                                style={{ width: `${(stat.in_progress / stat.total) * 100}%` }}
                                                title={`В обработке: ${stat.in_progress}`}
                                            ></div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default QueueStatistics; 