import React from 'react';
import { FaGraduationCap, FaExternalLinkAlt } from 'react-icons/fa';

const CompetitionLists = () => {
    const competitionLinks = [
        {
            name: "Банковское дело",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=d28208e8-e05f-11e5-80ee-005056a00b6e&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=70dd3c9b-4804-11ee-a2e8-149ecf4cb249@WTF~2024",
            color: "primary"
        },
        {
            name: "Землеустройство",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=f343c98a-34d4-11ed-a2dd-149ecf4cb249&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=561ddc08-4804-11ee-a2e8-149ecf4cb249@WTF~2024",
            color: "success"
        },
        {
            name: "Информационные системы и программирование",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=4ecdef8b-7658-11e9-80f4-005056a03e4f&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=f236a8f4-8f5c-11e9-80f8-005056a03e4f@WTF~2024",
            color: "info"
        },
        {
            name: "Операционная деятельность в логистике",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=2c9f0973-e9f2-11e5-80cc-005056a0072f&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=d3b6a56d-e11c-11ec-a2da-149ecf4cb24c@WTF~2024",
            color: "warning"
        },
        {
            name: "Сетевое и системное администрирование",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=dbde2699-720f-11ec-a2d8-149ecf4ca980&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=e17c5e7a-e1e6-11ec-a2da-149ecf4cb24c@WTF~2024",
            color: "secondary"
        },
        {
            name: "Страховое дело (по отраслям)",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=f1776800-e9f4-11e5-80cc-005056a0072f&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=d3b6a56c-e11c-11ec-a2da-149ecf4cb24c@WTF~2024",
            color: "danger"
        },
        {
            name: "Техническое обслуживание и ремонт автотранспортных средств",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=aae73cdd-0a42-11f0-9f95-00620bc81861&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=622acc67-3b11-11f0-9f9c-00620bc81861@WTF~2024",
            color: "dark"
        },
        {
            name: "Технология аналитического контроля химических соединений",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=bfcfd11a-00e2-11ed-a2da-149ecf4cb24c&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=70b3fa30-e1e6-11ec-a2da-149ecf4cb24c@WTF~2024",
            color: "primary"
        },
        {
            name: "Туризм и гостеприимство",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=378ab24a-34d5-11ed-a2dd-149ecf4cb249&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=412eb3e5-2340-11ef-a9fc-00620b9300d1@WTF~2024",
            color: "success"
        },
        {
            name: "Финансы",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=0c3b0980-a72e-11eb-a2d4-149ecf4ca97d&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=0d757dce-2341-11ef-a9fc-00620b9300d1",
            color: "info"
        },
        {
            name: "Экономика и бухгалтерский учет (по отраслям)",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=7be8c2fb-cdd0-11e5-80c3-00155d171400&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=f28b6600-480e-11ee-a2e8-149ecf4cb249@WTF~2024",
            color: "warning"
        },
        {
            name: "Электрические станции, сети, их релейная защита и автоматизация",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=22634d5a-1741-11ef-b306-6cfe5430e420&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=977dcdae-3b10-11f0-9f9c-00620bc81861@WTF~2024",
            color: "secondary"
        },
        {
            name: "Юриспруденция",
            url: "https://my.ranepa.ru/online/pk25/list/list.php?FT=2&FL=2&F1=d28d6cfc-36b6-11e6-80ca-005056a02ba9&F2=1760c581-34d5-11ed-a2dd-149ecf4cb249&F3=8bda13e8-9515-11ef-aa07-00620b9300d1&F4=cc82eb18-2340-11ef-a9fc-00620b9300d1@WTF~2024",
            color: "danger"
        }
    ];

    const handleButtonClick = (url) => {
        window.open(url, '_blank', 'noopener,noreferrer');
    };

    return (
        <div className="container mt-4">
            <div className="row">
                <div className="col-12">
                    <div className="card shadow-sm">
                        <div className="card-header bg-gradient-primary text-white" style={{background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'}}>
                            <h2 className="mb-0 d-flex align-items-center">
                                <FaGraduationCap className="me-3" />
                                Конкурсные списки
                            </h2>
                        </div>
                        <div className="card-body">
                            <p className="text-muted mb-4">
                                Выберите направление подготовки для просмотра конкурсного списка абитуриентов
                            </p>
                            
                            <div className="row g-3">
                                {competitionLinks.map((link, index) => (
                                    <div key={index} className="col-md-6 col-lg-4">
                                        <div 
                                            className={`card h-100 competition-card border-${link.color} shadow-sm`}
                                            style={{
                                                transition: 'all 0.3s ease',
                                                cursor: 'pointer',
                                                borderWidth: '2px'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.transform = 'translateY(-5px) scale(1.02)';
                                                e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                                                e.currentTarget.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                                            }}
                                            onClick={() => handleButtonClick(link.url)}
                                        >
                                                                                         <div className={`card-body text-center bg-${link.color} bg-opacity-10`}>
                                                 <div className="mb-2">
                                                     <FaGraduationCap 
                                                         className={`text-${link.color}`} 
                                                         style={{fontSize: '2rem'}}
                                                     />
                                                 </div>
                                                 <h6 className={`card-title text-${link.color} fw-bold mb-2`}>
                                                     {link.name}
                                                 </h6>
                                                                                                 <button 
                                                     className={`btn btn-${link.color} btn-sm w-100 d-flex align-items-center justify-content-center gap-1`}
                                                     style={{
                                                         transition: 'all 0.2s ease',
                                                         fontWeight: '600'
                                                     }}
                                                    onMouseEnter={(e) => {
                                                        e.currentTarget.style.transform = 'scale(1.05)';
                                                    }}
                                                    onMouseLeave={(e) => {
                                                        e.currentTarget.style.transform = 'scale(1)';
                                                    }}
                                                >
                                                    <FaExternalLinkAlt />
                                                    Открыть список
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CompetitionLists; 