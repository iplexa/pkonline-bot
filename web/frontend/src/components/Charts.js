import React, { useState, useEffect } from 'react';
import { Card, Row, Col } from 'react-bootstrap';
import { Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import axios from 'axios';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend
);

const Charts = () => {
  const [lkChart, setLkChart] = useState(null);
  const [epguChart, setEpguChart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    console.log('Charts component mounted');
    fetchChartData();
    const interval = setInterval(fetchChartData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchChartData = async () => {
    try {
      console.log('Fetching chart data...');
      const token = localStorage.getItem('token');
      console.log('Token:', token ? 'exists' : 'missing');
      
      const headers = { Authorization: `Bearer ${token}` };

      const [lkRes, epguRes] = await Promise.all([
        axios.get('/api/dashboard/charts/lk', { headers }),
        axios.get('/api/dashboard/charts/epgu', { headers })
      ]);

      console.log('LK chart data:', lkRes.data);
      console.log('EPGU chart data:', epguRes.data);

      setLkChart(lkRes.data);
      setEpguChart(epguRes.data);
      setLoading(false);
      setError(null);
    } catch (error) {
      console.error('Ошибка загрузки данных диаграмм:', error);
      setError(error.message);
      setLoading(false);
    }
  };

  console.log('Charts render - loading:', loading, 'error:', error, 'lkChart:', lkChart, 'epguChart:', epguChart);

  if (loading) {
    return (
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body className="text-center">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Загрузка диаграмм...</span>
              </div>
              <p className="mt-2">Загрузка диаграмм...</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    );
  }

  if (error) {
    return (
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body className="text-center">
              <div className="alert alert-danger">
                Ошибка загрузки диаграмм: {error}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    );
  }

  if (!lkChart || !epguChart) {
    return (
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Body className="text-center">
              <div className="alert alert-warning">
                Нет данных для диаграмм
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    );
  }

  const lkChartData = {
    labels: lkChart?.labels || [],
    datasets: [
      {
        data: lkChart?.data || [],
        backgroundColor: lkChart?.colors || [],
        borderColor: lkChart?.colors || [],
        borderWidth: 2,
      },
    ],
  };

  const epguChartData = {
    labels: epguChart?.labels || [],
    datasets: [
      {
        data: epguChart?.data || [],
        backgroundColor: epguChart?.colors || [],
        borderColor: epguChart?.colors || [],
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    },
  };

  console.log('Rendering charts with data:', { lkChartData, epguChartData });

  return (
    <Row className="mb-4">
      <Col lg={6} className="mb-3">
        <Card>
          <Card.Header>
            <h5 className="mb-0">Личный кабинет</h5>
          </Card.Header>
          <Card.Body>
            <div style={{ height: '300px' }}>
              <Doughnut data={lkChartData} options={chartOptions} />
            </div>
          </Card.Body>
        </Card>
      </Col>
      
      <Col lg={6} className="mb-3">
        <Card>
          <Card.Header>
            <h5 className="mb-0">ЕПГУ</h5>
          </Card.Header>
          <Card.Body>
            <div style={{ height: '300px' }}>
              <Doughnut data={epguChartData} options={chartOptions} />
            </div>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
};

export default Charts; 