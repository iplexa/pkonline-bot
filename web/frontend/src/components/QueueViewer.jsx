import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Modal, Button, Form } from 'react-bootstrap';
import { useAuth } from '../contexts/AuthContext.jsx';

const QueueViewer = () => {
    const { user } = useAuth();
    const [selectedQueue, setSelectedQueue] = useState('lk');
    const [statusFilter, setStatusFilter] = useState('all');
    const [applications, setApplications] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [showModal, setShowModal] = useState(false);
    const [modalType, setModalType] = useState(null);
    const [modalApp, setModalApp] = useState(null);
    const [modalReason, setModalReason] = useState('');
    const [actionLoading, setActionLoading] = useState(false);
    const [searchMode, setSearchMode] = useState(false);
    const [searchResults, setSearchResults] = useState([]);
    const [searchLoading, setSearchLoading] = useState(false);

    const queueTypes = [
        { value: 'lk', name: 'Личный кабинет', icon: 'fas fa-user' },
        { value: 'epgu', name: 'ЕПГУ', icon: 'fas fa-globe' },
        { value: 'epgu_mail', name: 'Почта', icon: 'fas fa-envelope' },
        { value: 'epgu_problem', name: 'Проблемные', icon: 'fas fa-exclamation-triangle' }
    ];

    const statusOptions = [
        { value: 'all', name: 'Все', icon: 'fas fa-list' },
        { value: 'queued', name: 'В очереди', icon: 'fas fa-clock' },
        { value: 'in_progress', name: 'В обработке', icon: 'fas fa-spinner' },
        { value: 'accepted', name: 'Принято', icon: 'fas fa-check' },
        { value: 'rejected', name: 'Отклонено', icon: 'fas fa-times' },
        { value: 'problem', name: 'Проблема', icon: 'fas fa-exclamation-triangle' }
    ];

    const handleAction = (app, action) => {
        setModalApp(app);
        setModalType(action);
        setShowModal(true);
        setModalReason('');
    };
    const handleModalClose = () => {
        setShowModal(false);
        setModalType(null);
        setModalApp(null);
        setModalReason('');
    };
    const processApplication = async () => {
        if (!modalApp) return;
        setActionLoading(true);
        try {
            await axios.patch(`/dashboard/applications/${modalApp.id}/process`, {
                action: modalType,
                reason: modalType === 'reject' || modalType === 'to_problem' ? modalReason : undefined
            });
            setShowModal(false);
            fetchApplications();
        } catch (e) {
            alert('Ошибка обработки: ' + (e.response?.data?.detail || e.message));
        } finally {
            setActionLoading(false);
        }
    };

    const handleTakeNext = async () => {
        setActionLoading(true);
        try {
            await axios.post(`/dashboard/queues/${selectedQueue}/next`);
            fetchApplications();
        } catch (e) {
            alert('Нет доступных заявлений или ошибка: ' + (e.response?.data?.detail || e.message));
        } finally {
            setActionLoading(false);
        }
    };

    const handleSearch = async () => {
        if (!searchTerm) return;
        setSearchLoading(true);
        setSearchMode(true);
        try {
            const res = await axios.get(`/dashboard/queues/${selectedQueue}/search`, { params: { fio: searchTerm } });
            setSearchResults(res.data);
        } catch (e) {
            alert('Ошибка поиска: ' + (e.response?.data?.detail || e.message));
        } finally {
            setSearchLoading(false);
        }
    };

    const handleClearSearch = () => {
        setSearchMode(false);
        setSearchResults([]);
    };

    const fetchApplications = async () => {
        try {
            setLoading(true);
            const response = await axios.get(`/dashboard/queues/${selectedQueue}/applications`);
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
    }, [selectedQueue]);

    const getStatusBadge = (status) => {
        const statusConfig = {
            'queued': { bg: 'warning', text: 'В очереди', icon: 'fas fa-clock' },
            'in_progress': { bg: 'info', text: 'В обработке', icon: 'fas fa-spinner' },
            'accepted': { bg: 'success', text: 'Принято', icon: 'fas fa-check' },
            'rejected': { bg: 'danger', text: 'Отклонено', icon: 'fas fa-times' },
            'problem': { bg: 'secondary', text: 'Проблема', icon: 'fas fa-exclamation-triangle' }
        };
        
        const config = statusConfig[status] || { bg: 'secondary', text: status, icon: 'fas fa-question' };
        
        return (
            <span className={`badge bg-${config.bg}`}>
                <i className={`${config.icon} me-1`}></i>
                {config.text}
            </span>
        );
    };

    const getPriorityBadge = (isPriority) => {
        if (isPriority) {
            return <span className="badge bg-danger me-2"><i className="fas fa-star me-1"></i>Приоритет</span>;
        }
        return null;
    };

    const filteredApplications = applications.filter(app => {
        const matchesStatus = statusFilter === 'all' || app.status === statusFilter;
        const matchesSearch = searchTerm === '' || 
            app.fio.toLowerCase().includes(searchTerm.toLowerCase()) ||
            app.id.toString().includes(searchTerm);
        return matchesStatus && matchesSearch;
    });

    // Only show queues/actions if user has rights
    const allowedQueues = queueTypes.filter(q => {
        if (!user) return false;
        if (user.is_admin) return true;
        // Пример: только определённые очереди для обычных сотрудников
        if (q.value === 'lk' && user.can_process_lk) return true;
        if (q.value === 'epgu' && user.can_process_epgu) return true;
        if (q.value === 'epgu_mail' && user.can_process_epgu_mail) return true;
        if (q.value === 'epgu_problem' && user.can_process_epgu_problem) return true;
        return false;
    });

    return (
        <div className="queue-viewer">
            {/* Queue Selection */}
            <div className="card border-0 shadow-sm mb-4">
                <div className="card-header bg-primary text-white">
                    <h5 className="card-title mb-0">
                        <i className="fas fa-list-alt me-2"></i>
                        Просмотр очередей
                    </h5>
                </div>
                <div className="card-body">
                    <div className="row g-3">
                        <div className="col-md-6">
                            <label className="form-label fw-semibold">Выберите очередь:</label>
                            <div className="btn-group w-100" role="group">
                                {allowedQueues.map((queue) => (
                                    <button
                                        key={queue.value}
                                        type="button"
                                        className={`btn ${selectedQueue === queue.value ? 'btn-primary' : 'btn-outline-primary'}`}
                                        onClick={() => setSelectedQueue(queue.value)}
                                    >
                                        <i className={`${queue.icon} me-1`}></i>
                                        {queue.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="col-md-6">
                            <label className="form-label fw-semibold">Фильтр по статусу:</label>
                            <select 
                                className="form-select"
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                            >
                                {statusOptions.map((status) => (
                                    <option key={status.value} value={status.value}>
                                        {status.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                    
                    <div className="row mt-3">
                        <div className="col-md-6">
                            <label className="form-label fw-semibold">Поиск:</label>
                            <div className="input-group">
                                <span className="input-group-text">
                                    <i className="fas fa-search"></i>
                                </span>
                                <input
                                    type="text"
                                    className="form-control"
                                    placeholder="Поиск по ФИО или ID..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="col-md-6 d-flex align-items-end">
                            <button 
                                className="btn btn-outline-primary me-2"
                                onClick={fetchApplications}
                                disabled={loading}
                            >
                                <i className={`fas fa-sync-alt ${loading ? 'fa-spin' : ''}`}></i>
                                Обновить
                            </button>
                            <button
                                className="btn btn-success me-2"
                                onClick={handleTakeNext}
                                disabled={actionLoading}
                            >
                                <i className="fas fa-hand-paper"></i> Взять заявление
                            </button>
                            <button
                                className="btn btn-info"
                                onClick={handleSearch}
                                disabled={searchLoading || !searchTerm}
                            >
                                <i className="fas fa-search"></i> Поиск
                            </button>
                            {searchMode && (
                                <button className="btn btn-secondary ms-2" onClick={handleClearSearch}>Сбросить</button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Applications List */}
            <div className="card border-0 shadow-sm">
                <div className="card-header bg-light">
                    <div className="d-flex justify-content-between align-items-center">
                        <h6 className="mb-0">
                            {searchMode ? `Результаты поиска: ${searchResults.length}` : `Заявления в очереди: ${filteredApplications.length}`}
                        </h6>
                        <small className="text-muted">
                            Всего в очереди: {applications.length}
                        </small>
                    </div>
                </div>
                <div className="card-body p-0">
                    {loading || searchLoading ? (
                        <div className="p-4 text-center">
                            <div className="spinner-border text-primary" role="status">
                                <span className="visually-hidden">Загрузка...</span>
                            </div>
                        </div>
                    ) : (searchMode ? searchResults : filteredApplications).length === 0 ? (
                        <div className="p-4 text-center text-muted">
                            <i className="fas fa-inbox fa-3x mb-3"></i>
                            <p>Нет заявлений в выбранной очереди</p>
                        </div>
                    ) : (
                        <div className="table-responsive">
                            <table className="table table-hover mb-0">
                                <thead className="table-light">
                                    <tr>
                                        <th>ID</th>
                                        <th>ФИО</th>
                                        <th>Статус</th>
                                        <th>Обработал</th>
                                        <th>Дата подачи</th>
                                        <th>Действия</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(searchMode ? searchResults : filteredApplications).map((app) => (
                                        <tr key={app.id}>
                                            <td>
                                                <span className="fw-bold text-primary">#{app.id}</span>
                                                {getPriorityBadge(app.is_priority)}
                                            </td>
                                            <td>
                                                <div className="fw-semibold">{app.fio}</div>
                                                <small className="text-muted">
                                                    Очередь: {queueTypes.find(q => q.value === app.queue_type)?.name}
                                                </small>
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
                                                <div>
                                                    <div className="fw-medium">
                                                        {new Date(app.submitted_at).toLocaleDateString('ru-RU')}
                                                    </div>
                                                    <small className="text-muted">
                                                        {new Date(app.submitted_at).toLocaleTimeString('ru-RU')}
                                                    </small>
                                                </div>
                                            </td>
                                            <td>
                                                {/* Кнопки действий для заявлений, только если у пользователя есть права */}
                                                {user && (user.is_admin || user.can_process_epgu || user.can_process_epgu_mail || user.can_process_lk) && [
                                                    ['epgu', 'epgu_mail', 'lk'].includes(app.queue_type) && app.status === 'queued' && (
                                                        <>
                                                            <button className="btn btn-sm btn-success me-1" title="Принять" onClick={() => handleAction(app, 'accept')}><i className="fas fa-check"></i></button>
                                                            <button className="btn btn-sm btn-danger me-1" title="Отклонить" onClick={() => handleAction(app, 'reject')}><i className="fas fa-times"></i></button>
                                                            {app.queue_type === 'epgu' && (
                                                                <>
                                                                    <button className="btn btn-sm btn-warning me-1" title="На подпись (почта)" onClick={() => handleAction(app, 'to_mail')}><i className="fas fa-envelope"></i></button>
                                                                    <button className="btn btn-sm btn-secondary me-1" title="Проблемное" onClick={() => handleAction(app, 'to_problem')}><i className="fas fa-exclamation-triangle"></i></button>
                                                                </>
                                                            )}
                                                            {app.queue_type === 'epgu_mail' && (
                                                                <>
                                                                    <button className="btn btn-sm btn-info me-1" title="Подтвердить сканы" onClick={() => handleAction(app, 'confirm_scans')}><i className="fas fa-file-alt"></i></button>
                                                                    <button className="btn btn-sm btn-primary me-1" title="Подтвердить подпись" onClick={() => handleAction(app, 'confirm_signature')}><i className="fas fa-pen"></i></button>
                                                                </>
                                                            )}
                                                        </>
                                                    ),
                                                    <button 
                                                        className="btn btn-sm btn-outline-info"
                                                        title="Подробности"
                                                    >
                                                        <i className="fas fa-eye"></i>
                                                    </button>
                                                ]}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Модальное окно для подтверждения действия или ввода причины */}
            <Modal show={showModal} onHide={handleModalClose} centered>
                <Modal.Header closeButton>
                    <Modal.Title>
                        {modalType === 'accept' && 'Подтвердить принятие заявления?'}
                        {modalType === 'reject' && 'Отклонить заявление'}
                        {modalType === 'to_mail' && 'Отправить на подпись (почта)?'}
                        {modalType === 'to_problem' && 'Перевести в проблемные'}
                        {modalType === 'confirm_scans' && 'Подтвердить сканы?'}
                        {modalType === 'confirm_signature' && 'Подтвердить подпись?'}
                    </Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {(modalType === 'reject' || modalType === 'to_problem') ? (
                        <Form.Group>
                            <Form.Label>Укажите причину:</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={2}
                                value={modalReason}
                                onChange={e => setModalReason(e.target.value)}
                                disabled={actionLoading}
                            />
                        </Form.Group>
                    ) : (
                        <p>Вы уверены, что хотите выполнить это действие?</p>
                    )}
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={handleModalClose} disabled={actionLoading}>Отмена</Button>
                    <Button variant="primary" onClick={processApplication} disabled={actionLoading || ((modalType === 'reject' || modalType === 'to_problem') && !modalReason)}>
                        {actionLoading ? 'Выполняется...' : 'Подтвердить'}
                    </Button>
                </Modal.Footer>
            </Modal>
        </div>
    );
};

export default QueueViewer; 