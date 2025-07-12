import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const EmployeeStatus = ({ detailed = false }) => {
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    const fetchEmployees = useCallback(async () => {
        try {
            setError(null);
            const response = await axios.get('/dashboard/employees/status');
            setEmployees(response.data);
            setLastUpdate(new Date());
        } catch (error) {
            console.error('Ошибка загрузки статуса сотрудников:', error);
            setError('Ошибка загрузки данных');
            // Не обновляем состояние при ошибке, чтобы не терять предыдущие данные
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchEmployees();
        // Увеличиваем интервал до 60 секунд для снижения нагрузки
        const interval = setInterval(fetchEmployees, 60000);
        return () => clearInterval(interval);
    }, [fetchEmployees]);

    const getStatusIcon = (status) => {
        switch (status) {
            case 'На рабочем месте':
                return <i className="fas fa-circle text-success me-2"></i>;
            case 'На перерыве':
                return <i className="fas fa-circle text-warning me-2"></i>;
            case 'Рабочий день завершен':
                return <i className="fas fa-circle text-info me-2"></i>;
            default:
                return <i className="fas fa-circle text-secondary me-2"></i>;
        }
    };

    const getStatusClass = (status) => {
        switch (status) {
            case 'На рабочем месте':
                return 'border-start border-success border-4';
            case 'На перерыве':
                return 'border-start border-warning border-4';
            case 'Рабочий день завершен':
                return 'border-start border-info border-4';
            default:
                return 'border-start border-secondary border-4';
        }
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

    if (error) {
        return (
            <div className="p-4 text-center">
                <div className="alert alert-warning" role="alert">
                    <i className="fas fa-exclamation-triangle me-2"></i>
                    {error}
                    <button 
                        className="btn btn-sm btn-outline-warning ms-3"
                        onClick={fetchEmployees}
                    >
                        <i className="fas fa-sync-alt me-1"></i>
                        Повторить
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="employee-status">
            {employees.length === 0 ? (
                <div className="p-4 text-center text-muted">
                    <i className="fas fa-users fa-2x mb-3"></i>
                    <p>Нет данных о сотрудниках</p>
                </div>
            ) : (
                <>
                    {employees.map((employee) => (
                        <div 
                            key={employee.id} 
                            className={`employee-item p-3 ${getStatusClass(employee.status)}`}
                        >
                            <div className="d-flex justify-content-between align-items-start">
                                <div className="flex-grow-1">
                                    <div className="d-flex align-items-center mb-2">
                                        <h6 className="mb-0 fw-semibold">
                                            {employee.fio}
                                            {employee.is_admin && (
                                                <span className="badge bg-danger ms-2">Админ</span>
                                            )}
                                        </h6>
                                    </div>
                                    
                                    <div className="d-flex align-items-center mb-2">
                                        {getStatusIcon(employee.status)}
                                        <span className="fw-medium">{employee.status}</span>
                                    </div>

                                    {employee.current_task && (
                                        <div className="mb-2">
                                            <small className="text-muted">
                                                <i className="fas fa-tasks me-1"></i>
                                                <strong>Текущая задача:</strong> {employee.current_task}
                                            </small>
                                        </div>
                                    )}

                                    {employee.work_duration && (
                                        <div className="mb-2">
                                            <small className="text-muted">
                                                <i className="fas fa-clock me-1"></i>
                                                <strong>Время работы:</strong> {employee.work_duration}
                                            </small>
                                        </div>
                                    )}

                                    {detailed && employee.start_time && (
                                        <div className="mb-2">
                                            <small className="text-muted">
                                                <i className="fas fa-play me-1"></i>
                                                <strong>Начало:</strong> {new Date(employee.start_time).toLocaleTimeString('ru-RU')}
                                            </small>
                                        </div>
                                    )}
                                </div>

                                {detailed && (
                                    <div className="text-end">
                                        <button 
                                            className="btn btn-sm btn-outline-primary"
                                            onClick={fetchEmployees}
                                            title="Обновить"
                                        >
                                            <i className="fas fa-sync-alt"></i>
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    
                    {lastUpdate && (
                        <div className="text-center mt-3">
                            <small className="text-muted">
                                <i className="fas fa-clock me-1"></i>
                                Последнее обновление: {lastUpdate.toLocaleTimeString('ru-RU')}
                            </small>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default EmployeeStatus; 