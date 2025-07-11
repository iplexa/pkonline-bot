import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Badge, Button, Navbar } from 'react-bootstrap';
import { FaUsers, FaClipboardList, FaChartBar, FaSignOutAlt, FaSync } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

function Dashboard() {
  const { logout } = useAuth();
  const [employees, setEmployees] = useState([]);
  const [applications, setApplications] = useState([]);
  const [queueStats, setQueueStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchData = async () => {
    try {
      const [employeesRes, applicationsRes, statsRes] = await Promise.all([
        axios.get('/dashboard/employees/status'),
        axios.get('/dashboard/applications/recent'),
        axios.get('/dashboard/queues/statistics')
      ]);

      setEmployees(employeesRes.data);
      setApplications(applicationsRes.data);
      setQueueStats(statsRes.data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Обновление каждые 30 секунд
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status) => {
    const statusConfig = {
      'На рабочем месте': { variant: 'success', icon: '🟢' },
      'На перерыве': { variant: 'warning', icon: '🟡' },
      'Не работает': { variant: 'secondary', icon: '⚫' }
    };
    
    const config = statusConfig[status] || { variant: 'secondary', icon: '❓' };
    return (
      <Badge bg={config.variant} className="status-badge">
        {config.icon} {status}
      </Badge>
    );
  };

  const getQueueTypeName = (type) => {
    const names = {
      'lk': 'Личный кабинет',
      'epgu': 'ЕПГУ',
      'epgu_mail': 'Почта',
      'epgu_problem': 'Проблемные'
    };
    return names[type] || type;
  };

  const getStatusColor = (status) => {
    const colors = {
      'queued': 'warning',
      'in_progress': 'info',
      'accepted': 'success',
      'rejected': 'danger',
      'problem': 'secondary'
    };
    return colors[status] || 'secondary';
  };

  const getEmployeeCardClass = (status) => {
    if (status === 'На рабочем месте') return 'working';
    if (status === 'На перерыве') return 'break';
    return 'offline';
  };

  return (
    <div>
      {/* Навигационная панель */}
      <Navbar bg="dark" variant="dark" className="mb-4">
        <Container fluid>
          <Navbar.Brand>
            <FaUsers className="me-2" />
            PK Online Dashboard
          </Navbar.Brand>
          <div className="d-flex align-items-center">
            <small className="text-light me-3">
              Обновлено: {lastUpdate.toLocaleTimeString()}
            </small>
            <Button 
              variant="outline-light" 
              size="sm" 
              className="me-2"
              onClick={fetchData}
              disabled={loading}
            >
              <FaSync className={loading ? 'fa-spin' : ''} />
            </Button>
            <Button variant="outline-light" size="sm" onClick={logout}>
              <FaSignOutAlt />
            </Button>
          </div>
        </Container>
      </Navbar>

      <Container fluid>
        {/* Статистика очередей */}
        <Row className="mb-4">
          <Col>
            <Card className="queue-statistics">
              <Card.Body>
                <Card.Title className="text-white">
                  <FaChartBar className="me-2" />
                  Статистика очередей
                </Card.Title>
                <Row>
                  {queueStats.map((stat) => (
                    <Col key={stat.queue_type} md={3} className="mb-2">
                      <div className="text-center">
                        <h4 className="text-white mb-1">{stat.total}</h4>
                        <small className="text-white-50">{getQueueTypeName(stat.queue_type)}</small>
                        <div className="mt-2">
                          <Badge bg="warning" className="me-1">{stat.queued}</Badge>
                          <Badge bg="info" className="me-1">{stat.in_progress}</Badge>
                          <Badge bg="success" className="me-1">{stat.accepted}</Badge>
                          <Badge bg="danger" className="me-1">{stat.rejected}</Badge>
                          <Badge bg="secondary">{stat.problem}</Badge>
                        </div>
                      </div>
                    </Col>
                  ))}
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        <Row>
          {/* Сотрудники */}
          <Col lg={6} className="mb-4">
            <Card className="dashboard-card h-100">
              <Card.Header>
                <FaUsers className="me-2" />
                Сотрудники ({employees.length})
              </Card.Header>
              <Card.Body className="p-0">
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {employees.map((employee) => (
                    <div 
                      key={employee.id} 
                      className={`employee-card p-3 border-bottom ${getEmployeeCardClass(employee.status)}`}
                    >
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <h6 className="mb-1">
                            {employee.fio}
                            {employee.is_admin && (
                              <Badge bg="danger" className="ms-2">Админ</Badge>
                            )}
                          </h6>
                          {getStatusBadge(employee.status)}
                          {employee.current_task && (
                            <div className="mt-2">
                              <small className="text-muted">
                                <strong>Текущая задача:</strong> {employee.current_task}
                              </small>
                            </div>
                          )}
                          {employee.work_duration && (
                            <div className="mt-1">
                              <small className="text-muted">
                                Время работы: {employee.work_duration}
                              </small>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card.Body>
            </Card>
          </Col>

          {/* Последние заявления */}
          <Col lg={6} className="mb-4">
            <Card className="dashboard-card h-100">
              <Card.Header>
                <FaClipboardList className="me-2" />
                Последние обработанные заявления
              </Card.Header>
              <Card.Body className="p-0">
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {applications.map((app) => (
                    <div key={app.id} className="application-item p-3 border-bottom">
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <h6 className="mb-1">Заявление #{app.id}</h6>
                          <p className="mb-1"><strong>{app.fio}</strong></p>
                          <div className="mb-2">
                            <Badge bg="primary" className="me-2">
                              {getQueueTypeName(app.queue_type)}
                            </Badge>
                            <Badge bg={getStatusColor(app.status)}>
                              {app.status}
                            </Badge>
                          </div>
                          {app.processed_by_fio && (
                            <small className="text-muted">
                              Обработал: {app.processed_by_fio}
                            </small>
                          )}
                        </div>
                        <div className="text-end">
                          <small className="text-muted">
                            {new Date(app.submitted_at).toLocaleDateString()}
                          </small>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default Dashboard; 