import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import Charts from './Charts';

const Dashboard = () => {
    const { isAuthenticated, user, logout } = useAuth();
    const [data, setData] = useState({
        employees: [],
        queueStats: {}
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedQueue, setSelectedQueue] = useState(null);
    const [queueApplications, setQueueApplications] = useState([]);
    const [showReport, setShowReport] = useState(false);
    const [reportData, setReportData] = useState(null);
    const [reportLoading, setReportLoading] = useState(false);
    const [reportError, setReportError] = useState(null);
    const [showDatePicker, setShowDatePicker] = useState(false);
    const [selectedReportDate, setSelectedReportDate] = useState('');
    const [showSetPassword, setShowSetPassword] = useState(false);
    const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [setPasswordLoading, setSetPasswordLoading] = useState(false);
    const [setPasswordMessage, setSetPasswordMessage] = useState('');
    const [setPasswordError, setSetPasswordError] = useState('');

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
            const [employeesRes, statsRes] = await Promise.all([
                axios.get('/dashboard/employees/status'),
                axios.get('/dashboard/queues/statistics')
            ]);

            setData({
                employees: employeesRes.data,
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

    const fetchFullReport = async (date = null) => {
        setReportLoading(true);
        setReportError(null);
        try {
            let url = '/dashboard/full_report';
            if (date) {
                url += `?date=${date}`;
            }
            const response = await axios.get(url);
            setReportData(response.data);
            setShowReport(true);
        } catch (err) {
            setReportError('Ошибка загрузки отчета');
        } finally {
            setReportLoading(false);
        }
    };

    const handleTodayReport = () => {
        fetchFullReport();
    };

    const handleDateReport = () => {
        setShowDatePicker(true);
    };

    const handleDateChange = (e) => {
        setSelectedReportDate(e.target.value);
    };

    const handleDateSubmit = () => {
        if (selectedReportDate) {
            fetchFullReport(selectedReportDate);
            setShowDatePicker(false);
        }
    };

    const closeReport = () => {
        setShowReport(false);
        setReportData(null);
    };

    const openSetPassword = () => {
        setShowSetPassword(true);
        setSelectedEmployeeId('');
        setNewPassword('');
        setSetPasswordMessage('');
        setSetPasswordError('');
    };

    const closeSetPassword = () => {
        setShowSetPassword(false);
    };

    const handleSetPassword = async () => {
        setSetPasswordLoading(true);
        setSetPasswordMessage('');
        setSetPasswordError('');
        try {
            await axios.post('/auth/set_password', {
                employee_id: selectedEmployeeId,
                new_password: newPassword
            });
            setSetPasswordMessage('Пароль успешно обновлен');
        } catch (err) {
            setSetPasswordError(err.response?.data?.detail || 'Ошибка при смене пароля');
        } finally {
            setSetPasswordLoading(false);
        }
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
            
            {user?.is_admin && (
                <div className="mb-3">
                    <button className="btn btn-warning" onClick={openSetPassword}>
                        <i className="fas fa-key me-2"></i>Сменить пароль сотрудника
                    </button>
                </div>
            )}

            {showSetPassword && (
                <div className="modal show d-block" tabIndex="-1" role="dialog" style={{background: 'rgba(0,0,0,0.2)'}}>
                    <div className="modal-dialog" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Смена пароля сотрудника</h5>
                                <button type="button" className="btn-close" onClick={closeSetPassword}></button>
                            </div>
                            <div className="modal-body">
                                <div className="mb-3">
                                    <label className="form-label">Сотрудник</label>
                                    <select className="form-select" value={selectedEmployeeId} onChange={e => setSelectedEmployeeId(e.target.value)}>
                                        <option value="">Выберите сотрудника</option>
                                        {data.employees.map(emp => (
                                            <option key={emp.id} value={emp.id}>{emp.fio}</option>
                                        ))}
                                    </select>
                                </div>
                                <div className="mb-3">
                                    <label className="form-label">Новый пароль</label>
                                    <input type="text" className="form-control" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                                </div>
                                {setPasswordMessage && <div className="alert alert-success">{setPasswordMessage}</div>}
                                {setPasswordError && <div className="alert alert-danger">{setPasswordError}</div>}
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={closeSetPassword}>Отмена</button>
                                <button type="button" className="btn btn-primary" onClick={handleSetPassword} disabled={setPasswordLoading || !selectedEmployeeId || !newPassword}>
                                    {setPasswordLoading ? 'Сохраняем...' : 'Сохранить'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Кнопки отчетности */}
            <div className="mb-4 d-flex gap-2">
                <button className="btn btn-primary" onClick={handleTodayReport}>
                    📊 Полный отчет за сегодня
                </button>
                <button className="btn btn-outline-primary" onClick={handleDateReport}>
                    📅 Выбрать дату для отчета
                </button>
                {showDatePicker && (
                    <div className="ms-3 d-flex align-items-center gap-2">
                        <input type="date" value={selectedReportDate} onChange={handleDateChange} className="form-control" style={{maxWidth: 180}} />
                        <button className="btn btn-success btn-sm" onClick={handleDateSubmit}>Показать</button>
                        <button className="btn btn-secondary btn-sm" onClick={() => setShowDatePicker(false)}>Отмена</button>
                    </div>
                )}
            </div>

            {/* Модальное окно/блок для отчета */}
            {showReport && (
                <div className="modal show d-block" tabIndex="-1" role="dialog" style={{background: 'rgba(0,0,0,0.2)'}}>
                    <div className="modal-dialog modal-xl" role="document">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h5 className="modal-title">Полный отчет</h5>
                                <button type="button" className="btn-close" onClick={closeReport}></button>
                            </div>
                            <div className="modal-body">
                                {reportLoading ? (
                                    <div className="text-center p-4">
                                        <div className="spinner-border text-primary" role="status">
                                            <span className="visually-hidden">Загрузка...</span>
                                        </div>
                                    </div>
                                ) : reportError ? (
                                    <div className="alert alert-danger">{reportError}</div>
                                ) : reportData && reportData.length > 0 ? (
                                    <div className="table-responsive">
                                        <table className="table table-bordered">
                                            <thead>
                                                <tr>
                                                    <th>Сотрудник</th>
                                                    <th>Начало</th>
                                                    <th>Окончание</th>
                                                    <th>Время работы</th>
                                                    <th>Время перерывов</th>
                                                    <th>Заявлений</th>
                                                    <th>Перерывы</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {reportData.map((r, idx) => (
                                                    <tr key={idx}>
                                                        <td>{r.employee_fio}</td>
                                                        <td>{r.start_time ? new Date(r.start_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}) : '-'}</td>
                                                        <td>{r.end_time ? new Date(r.end_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}) : '-'}</td>
                                                        <td>{r.total_work_time != null ? `${Math.floor(r.total_work_time/3600).toString().padStart(2,'0')}:${Math.floor((r.total_work_time%3600)/60).toString().padStart(2,'0')}` : '-'}</td>
                                                        <td>{r.total_break_time != null ? `${Math.floor(r.total_break_time/3600).toString().padStart(2,'0')}:${Math.floor((r.total_break_time%3600)/60).toString().padStart(2,'0')}` : '-'}</td>
                                                        <td>{r.applications_processed}</td>
                                                        <td>
                                                            {r.breaks && r.breaks.length > 0 ? (
                                                                <ul className="mb-0 ps-3">
                                                                    {r.breaks.map((b, i) => (
                                                                        <li key={i}>
                                                                            {b.start_time ? new Date(b.start_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}) : '-'}
                                                                            {' - '}
                                                                            {b.end_time ? new Date(b.end_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'}) : 'активен'}
                                                                            {b.duration ? ` (${Math.floor(b.duration/60)} мин)` : ''}
                                                                        </li>
                                                                    ))}
                                                                </ul>
                                                            ) : '—'}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="alert alert-info">Нет данных за выбранную дату</div>
                                )}
                            </div>
                            <div className="modal-footer">
                                <button type="button" className="btn btn-secondary" onClick={closeReport}>Закрыть</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

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
                            {/* Секция последних обработанных заявлений удалена */}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard; 