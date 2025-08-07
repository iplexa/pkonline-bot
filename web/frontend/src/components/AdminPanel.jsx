import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AdminPanel = () => {
  // --- Управление паролями сотрудников ---
  const [employees, setEmployees] = useState([]);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // --- Редактирование количества обработанных заявлений ---
  const [selectedDate, setSelectedDate] = useState('');
  const [workDay, setWorkDay] = useState(null);
  const [applicationsValue, setApplicationsValue] = useState('');
  const [applicationsLoading, setApplicationsLoading] = useState(false);
  const [applicationsMessage, setApplicationsMessage] = useState('');
  const [applicationsError, setApplicationsError] = useState('');

  useEffect(() => {
    axios.get('/dashboard/employees/status')
      .then(res => setEmployees(res.data))
      .catch(() => setEmployees([]));
  }, []);

  // Получить work_day по сотруднику и дате
  useEffect(() => {
    setWorkDay(null);
    setApplicationsValue('');
    setApplicationsMessage('');
    setApplicationsError('');
    if (selectedEmployeeId && selectedDate) {
      setApplicationsLoading(true);
      axios.get(`/dashboard/full_report?date=${selectedDate}`)
        .then(res => {
          const found = res.data.find(wd => String(wd.employee_id) === String(selectedEmployeeId) || String(wd.employee_tg_id) === String(selectedEmployeeId));
          setWorkDay(found);
          setApplicationsValue(found ? found.applications_processed : '');
        })
        .catch(() => setWorkDay(null))
        .finally(() => setApplicationsLoading(false));
    }
  }, [selectedEmployeeId, selectedDate]);

  const handleSetPassword = async () => {
    setPasswordLoading(true);
    setPasswordMessage('');
    setPasswordError('');
    try {
      await axios.post('/auth/set_password', {
        employee_id: selectedEmployeeId,
        new_password: newPassword
      });
      setPasswordMessage('Пароль успешно обновлен');
    } catch (err) {
      setPasswordError(err.response?.data?.detail || 'Ошибка при смене пароля');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleSaveApplications = async () => {
    if (!workDay || !workDay.workday_id) return;
    setApplicationsLoading(true);
    setApplicationsMessage('');
    setApplicationsError('');
    try {
      await axios.patch(`/dashboard/workday/${workDay.workday_id}/applications_processed`, {
        applications_processed: Number(applicationsValue)
      });
      setApplicationsMessage('Количество обработанных заявлений успешно обновлено');
    } catch (err) {
      setApplicationsError(err.response?.data?.detail || 'Ошибка при сохранении');
    } finally {
      setApplicationsLoading(false);
    }
  };

  // --- Остальные секции (заглушка) ---

  return (
    <div className="container mt-4">
      <h2>Админ-панель</h2>
      <div className="card mb-4">
        <div className="card-header">Управление паролями сотрудников</div>
        <div className="card-body">
          <div className="mb-3">
            <label className="form-label">Сотрудник</label>
            <select className="form-select" value={selectedEmployeeId} onChange={e => setSelectedEmployeeId(e.target.value)}>
              <option value="">Выберите сотрудника</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.fio}</option>
              ))}
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Новый пароль</label>
            <input type="text" className="form-control" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
          </div>
          {passwordMessage && <div className="alert alert-success">{passwordMessage}</div>}
          {passwordError && <div className="alert alert-danger">{passwordError}</div>}
          <button className="btn btn-primary" onClick={handleSetPassword} disabled={passwordLoading || !selectedEmployeeId || !newPassword}>
            {passwordLoading ? 'Сохраняем...' : 'Сменить пароль'}
          </button>
        </div>
      </div>
      <div className="card mb-4">
        <div className="card-header">Редактирование количества обработанных заявлений</div>
        <div className="card-body">
          <div className="mb-3">
            <label className="form-label">Сотрудник</label>
            <select className="form-select" value={selectedEmployeeId} onChange={e => setSelectedEmployeeId(e.target.value)}>
              <option value="">Выберите сотрудника</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.fio}</option>
              ))}
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Дата</label>
            <input type="date" className="form-control" value={selectedDate} onChange={e => setSelectedDate(e.target.value)} />
          </div>
          {workDay && (
            <div className="mb-3">
              <label className="form-label">Текущее количество</label>
              <input type="number" className="form-control" value={applicationsValue} onChange={e => setApplicationsValue(e.target.value)} />
            </div>
          )}
          {applicationsMessage && <div className="alert alert-success">{applicationsMessage}</div>}
          {applicationsError && <div className="alert alert-danger">{applicationsError}</div>}
          <button className="btn btn-primary" onClick={handleSaveApplications} disabled={applicationsLoading || !workDay || applicationsValue === ''}>
            {applicationsLoading ? 'Сохраняем...' : 'Сохранить'}
          </button>
        </div>
      </div>
      <div className="card mb-4">
        <div className="card-header">Редактирование рабочего времени сотрудников</div>
        <div className="card-body">
          {/* Здесь будет редактирование рабочего времени */}
          <p>Функция ручного изменения времени начала, окончания, перерывов и т.д.</p>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;