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
  const [applicationsDate, setApplicationsDate] = useState('');
  const [applicationsRows, setApplicationsRows] = useState([]);
  const [applicationsLoading, setApplicationsLoading] = useState(false);
  const [applicationsMessage, setApplicationsMessage] = useState('');
  const [applicationsError, setApplicationsError] = useState('');
  const [applicationsSaving, setApplicationsSaving] = useState({});

  // --- Редактирование рабочего времени ---
  const [workTimeEmployeeId, setWorkTimeEmployeeId] = useState('');
  const [workTimeDate, setWorkTimeDate] = useState('');
  const [workDay, setWorkDay] = useState(null);
  const [workTimeFields, setWorkTimeFields] = useState({ start_time: '', end_time: '', status: '', breaks: [] });
  const [workTimeLoading, setWorkTimeLoading] = useState(false);
  const [workTimeMessage, setWorkTimeMessage] = useState('');
  const [workTimeError, setWorkTimeError] = useState('');

  useEffect(() => {
    axios.get('/dashboard/employees/status')
      .then(res => setEmployees(res.data))
      .catch(() => setEmployees([]));
  }, []);

  // --- Получение данных по заявлениям за дату ---
  useEffect(() => {
    setApplicationsRows([]);
    setApplicationsMessage('');
    setApplicationsError('');
    if (applicationsDate) {
      setApplicationsLoading(true);
      axios.get(`/dashboard/full_report?date=${applicationsDate}`)
        .then(res => {
          setApplicationsRows(res.data.map(row => ({ ...row, editValue: row.applications_processed })));
        })
        .catch(() => setApplicationsRows([]))
        .finally(() => setApplicationsLoading(false));
    }
  }, [applicationsDate]);

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

  const handleApplicationsEdit = (idx, value) => {
    setApplicationsRows(rows => rows.map((row, i) => i === idx ? { ...row, editValue: value } : row));
  };

  const handleSaveApplications = async (row, idx) => {
    setApplicationsSaving(s => ({ ...s, [row.workday_id]: true }));
    setApplicationsMessage('');
    setApplicationsError('');
    try {
      await axios.patch(`/dashboard/workday/${row.workday_id}/applications_processed`, {
        applications_processed: Number(row.editValue)
      });
      setApplicationsMessage(`Сохранено для ${row.employee_fio}`);
    } catch (err) {
      setApplicationsError(err.response?.data?.detail || 'Ошибка при сохранении');
    } finally {
      setApplicationsSaving(s => ({ ...s, [row.workday_id]: false }));
    }
  };

  // --- Получение и редактирование рабочего времени ---
  useEffect(() => {
    setWorkDay(null);
    setWorkTimeFields({ start_time: '', end_time: '', status: '', breaks: [] });
    setWorkTimeMessage('');
    setWorkTimeError('');
    if (workTimeEmployeeId && workTimeDate) {
      setWorkTimeLoading(true);
      axios.get(`/dashboard/full_report?date=${workTimeDate}`)
        .then(res => {
          const found = res.data.find(wd => String(wd.employee_id) === String(workTimeEmployeeId) || String(wd.employee_tg_id) === String(workTimeEmployeeId));
          setWorkDay(found);
          setWorkTimeFields({
            start_time: found?.start_time ? found.start_time.substring(0, 16) : '',
            end_time: found?.end_time ? found.end_time.substring(0, 16) : '',
            status: found?.status || '',
            breaks: found?.breaks ? found.breaks.map(b => ({
              start_time: b.start_time ? b.start_time.substring(0, 16) : '',
              end_time: b.end_time ? b.end_time.substring(0, 16) : '',
              duration: b.duration || 0
            })) : []
          });
        })
        .catch(() => setWorkDay(null))
        .finally(() => setWorkTimeLoading(false));
    }
  }, [workTimeEmployeeId, workTimeDate]);

  const handleWorkTimeFieldChange = (field, value) => {
    setWorkTimeFields(prev => ({ ...prev, [field]: value }));
  };
  const handleBreakChange = (idx, field, value) => {
    setWorkTimeFields(prev => ({
      ...prev,
      breaks: prev.breaks.map((b, i) => i === idx ? { ...b, [field]: value } : b)
    }));
  };
  const handleAddBreak = () => {
    setWorkTimeFields(prev => ({ ...prev, breaks: [...prev.breaks, { start_time: '', end_time: '', duration: 0 }] }));
  };
  const handleRemoveBreak = (idx) => {
    setWorkTimeFields(prev => ({ ...prev, breaks: prev.breaks.filter((_, i) => i !== idx) }));
  };
  const handleSaveWorkTime = async () => {
    if (!workDay || !workDay.workday_id) return;
    setWorkTimeLoading(true);
    setWorkTimeMessage('');
    setWorkTimeError('');
    try {
      await axios.patch(`/dashboard/workday/${workDay.workday_id}/work_time`, {
        start_time: workTimeFields.start_time,
        end_time: workTimeFields.end_time,
        status: workTimeFields.status,
        breaks: workTimeFields.breaks
      });
      setWorkTimeMessage('Рабочее время успешно обновлено');
    } catch (err) {
      setWorkTimeError(err.response?.data?.detail || 'Ошибка при сохранении');
    } finally {
      setWorkTimeLoading(false);
    }
  };

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
            <label className="form-label">Дата</label>
            <input type="date" className="form-control" value={applicationsDate} onChange={e => setApplicationsDate(e.target.value)} />
          </div>
          {applicationsLoading && <div>Загрузка...</div>}
          {applicationsRows.length > 0 && (
            <div className="table-responsive">
              <table className="table table-bordered">
                <thead>
                  <tr>
                    <th>Сотрудник</th>
                    <th>Количество обработанных заявлений</th>
                    <th>Сохранить</th>
                  </tr>
                </thead>
                <tbody>
                  {applicationsRows.map((row, idx) => (
                    <tr key={row.workday_id}>
                      <td>{row.employee_fio}</td>
                      <td>
                        <input type="number" className="form-control" value={row.editValue} onChange={e => handleApplicationsEdit(idx, e.target.value)} />
                      </td>
                      <td>
                        <button className="btn btn-primary btn-sm" onClick={() => handleSaveApplications(row, idx)} disabled={applicationsSaving[row.workday_id] || row.editValue === ''}>
                          {applicationsSaving[row.workday_id] ? 'Сохраняем...' : 'Сохранить'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {applicationsMessage && <div className="alert alert-success mt-2">{applicationsMessage}</div>}
          {applicationsError && <div className="alert alert-danger mt-2">{applicationsError}</div>}
        </div>
      </div>
      <div className="card mb-4">
        <div className="card-header">Редактирование рабочего времени сотрудников</div>
        <div className="card-body">
          <div className="mb-3">
            <label className="form-label">Сотрудник</label>
            <select className="form-select" value={workTimeEmployeeId} onChange={e => setWorkTimeEmployeeId(e.target.value)}>
              <option value="">Выберите сотрудника</option>
              {employees.map(emp => (
                <option key={emp.id} value={emp.id}>{emp.fio}</option>
              ))}
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Дата</label>
            <input type="date" className="form-control" value={workTimeDate} onChange={e => setWorkTimeDate(e.target.value)} />
          </div>
          {workDay && (
            <>
              <div className="mb-3">
                <label className="form-label">Время начала</label>
                <input type="datetime-local" className="form-control" value={workTimeFields.start_time} onChange={e => handleWorkTimeFieldChange('start_time', e.target.value)} />
              </div>
              <div className="mb-3">
                <label className="form-label">Время окончания</label>
                <input type="datetime-local" className="form-control" value={workTimeFields.end_time} onChange={e => handleWorkTimeFieldChange('end_time', e.target.value)} />
              </div>
              <div className="mb-3">
                <label className="form-label">Статус</label>
                <select className="form-select" value={workTimeFields.status} onChange={e => handleWorkTimeFieldChange('status', e.target.value)}>
                  <option value="">Выберите статус</option>
                  <option value="active">Активен</option>
                  <option value="paused">Пауза</option>
                  <option value="finished">Завершён</option>
                </select>
              </div>
              <div className="mb-3">
                <label className="form-label">Перерывы</label>
                {workTimeFields.breaks.map((br, idx) => (
                  <div key={idx} className="d-flex align-items-center mb-2 gap-2">
                    <input type="datetime-local" className="form-control" style={{maxWidth: 200}} value={br.start_time} onChange={e => handleBreakChange(idx, 'start_time', e.target.value)} />
                    <input type="datetime-local" className="form-control" style={{maxWidth: 200}} value={br.end_time} onChange={e => handleBreakChange(idx, 'end_time', e.target.value)} />
                    <input type="number" className="form-control" style={{maxWidth: 120}} value={br.duration} onChange={e => handleBreakChange(idx, 'duration', e.target.value)} placeholder="Длительность (сек)" />
                    <button className="btn btn-danger btn-sm" onClick={() => handleRemoveBreak(idx)}>&times;</button>
                  </div>
                ))}
                <button className="btn btn-outline-primary btn-sm mt-2" onClick={handleAddBreak}>Добавить перерыв</button>
              </div>
              {workTimeMessage && <div className="alert alert-success">{workTimeMessage}</div>}
              {workTimeError && <div className="alert alert-danger">{workTimeError}</div>}
              <button className="btn btn-primary" onClick={handleSaveWorkTime} disabled={workTimeLoading || !workDay}>
                {workTimeLoading ? 'Сохраняем...' : 'Сохранить'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;