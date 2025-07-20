// 面试结果页面JavaScript

// 模块配置
const MODULE_CONFIG = {
    self_introduction: { name: '个人介绍', maxScore: 10 },
    resume_digging: { name: '简历深挖', maxScore: 15 },
    ability_assessment: { name: '能力评估', maxScore: 15 },
    position_matching: { name: '岗位匹配', maxScore: 10 },
    professional_skills: { name: '专业能力', maxScore: 20 },
    reverse_question: { name: '反问环节', maxScore: 5 },
    voice_tone: { name: '语音语调', maxScore: 5 },
    facial_analysis: { name: '神态分析', maxScore: 10 },
    body_language: { name: '肢体语言', maxScore: 10 }
};

// 全局变量
let analysisData = {};
let currentUser = '';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 从URL获取用户名参数
    const urlParams = new URLSearchParams(window.location.search);
    currentUser = urlParams.get('user') || 'alivin'; // 默认使用alivin作为测试
    
    // 加载数据
    loadAnalysisData();
    
    // 绑定事件
    bindEvents();
});

// 加载分析数据
async function loadAnalysisData() {
    try {
        // 加载三个JSON文件
        const [summaryData, facialData, analysisData] = await Promise.all([
            fetch(`/uploads/${currentUser}/interview_summary_report.json`).then(r => r.json()).catch(() => null),
            fetch(`/uploads/${currentUser}/facial_analysis_report.json`).then(r => r.json()).catch(() => null),
            fetch(`/uploads/${currentUser}/analysis_result.json`).then(r => r.json()).catch(() => null)
        ]);

        // 合并数据
        const combinedData = combineData(summaryData, facialData, analysisData);
        
        // 更新页面
        updatePage(combinedData);
        
    } catch (error) {
        console.error('加载数据失败:', error);
        showError('数据加载失败，请检查文件是否存在');
    }
}

// 合并三个JSON文件的数据
function combineData(summaryData, facialData, analysisData) {
    const modules = {};
    
    // 从interview_summary_report.json获取数据
    if (summaryData) {
        // 个人介绍
        if (summaryData.self_introduction) {
            modules.self_introduction = {
                score: summaryData.self_introduction.score || 0,
                evaluation: summaryData.self_introduction.evaluation || '',
                suggestions: summaryData.self_introduction.suggestions || '',
                active: true
            };
        }
        
        // 简历深挖
        if (summaryData.resume_digging) {
            modules.resume_digging = {
                score: summaryData.resume_digging.score || 0,
                evaluation: summaryData.resume_digging.evaluation || '',
                suggestions: summaryData.resume_digging.suggestions || '',
                active: true
            };
        }
        
        // 能力评估
        if (summaryData.ability_assessment) {
            modules.ability_assessment = {
                score: summaryData.ability_assessment.score || 0,
                evaluation: summaryData.ability_assessment.evaluation || '',
                suggestions: summaryData.ability_assessment.suggestions || '',
                active: true
            };
        }
        
        // 岗位匹配
        if (summaryData.position_matching) {
            modules.position_matching = {
                score: summaryData.position_matching.score || 0,
                evaluation: summaryData.position_matching.evaluation || '',
                suggestions: summaryData.position_matching.suggestions || '',
                active: true
            };
        }
        
        // 专业能力
        if (summaryData.professional_skills) {
            modules.professional_skills = {
                score: summaryData.professional_skills.score || 0,
                evaluation: summaryData.professional_skills.evaluation || '',
                suggestions: summaryData.professional_skills.suggestions || '',
                active: true
            };
        }
        
        // 反问环节
        if (summaryData.reverse_question) {
            modules.reverse_question = {
                score: summaryData.reverse_question.score || 0,
                evaluation: summaryData.reverse_question.evaluation || '',
                suggestions: summaryData.reverse_question.suggestions || '',
                active: true
            };
        }
    }
    
    // 从facial_analysis_report.json获取数据
    if (facialData) {
        // 神态分析
        modules.facial_analysis = {
            score: facialData.score || 0,
            evaluation: facialData.evaluation || '',
            suggestions: facialData.suggestions || '',
            active: true
        };
        
        // 肢体语言（如果有的话）
        if (facialData.body_language) {
            modules.body_language = {
                score: facialData.body_language.score || 0,
                evaluation: facialData.body_language.evaluation || '',
                suggestions: facialData.body_language.suggestions || '',
                active: true
            };
        }
    }
    
    // 从analysis_result.json获取数据
    if (analysisData) {
        // 语音语调
        modules.voice_tone = {
            score: analysisData.score || 0,
            evaluation: analysisData.evaluation || '',
            suggestions: analysisData.suggestions || '',
            active: true
        };
    }
    
    // 计算总分
    const totalScore = Object.values(modules).reduce((sum, module) => sum + module.score, 0);
    
    return {
        modules,
        totalScore,
        totalEvaluation: summaryData?.total_evaluation || '面试表现良好，继续保持！',
        totalSuggestions: summaryData?.total_suggestions || '建议继续提升专业技能和沟通能力。'
    };
}

// 更新页面显示
function updatePage(data) {
    analysisData = data;
    
    // 更新总分
    document.getElementById('totalScore').textContent = data.totalScore;
    document.getElementById('totalEvaluation').textContent = data.totalEvaluation;
    
    // 更新进度条
    const progressFill = document.getElementById('totalProgress');
    const progressPercent = (data.totalScore / 100) * 100;
    progressFill.style.width = `${progressPercent}%`;
    
    // 更新各个模块
    Object.keys(MODULE_CONFIG).forEach(moduleKey => {
        const moduleData = data.modules[moduleKey];
        const scoreElement = document.getElementById(`${moduleKey}_score`);
        
        if (moduleData && moduleData.active) {
            // 更新分数
            scoreElement.textContent = moduleData.score;
            
            // 添加活跃状态
            const planetElement = document.querySelector(`[data-module="${moduleKey}"]`);
            planetElement.classList.add('active');
        } else {
            // 非活跃状态
            const planetElement = document.querySelector(`[data-module="${moduleKey}"]`);
            planetElement.classList.add('inactive');
        }
    });
    
    // 添加动画效果
    setTimeout(() => {
        animateScores();
    }, 500);
}

// 分数动画效果
function animateScores() {
    const scoreElements = document.querySelectorAll('.score-number');
    
    scoreElements.forEach(element => {
        const finalScore = parseInt(element.textContent);
        animateNumber(element, 0, finalScore, 1000);
    });
}

// 数字动画
function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * progress);
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// 绑定事件
function bindEvents() {
    // 绑定星球点击事件
    const planets = document.querySelectorAll('.module-planet');
    planets.forEach(planet => {
        planet.addEventListener('click', function() {
            const moduleKey = this.getAttribute('data-module');
            showModuleDetails(moduleKey);
        });
    });
    
    // 绑定模态框关闭事件
    const modal = document.getElementById('moduleModal');
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
    
    // ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// 显示模块详情
function showModuleDetails(moduleType) {
    const config = MODULE_CONFIG[moduleType];
    if (!config || !analysisData.modules[moduleType]) {
        showError('暂无该模块的详细数据');
        return;
    }

    const moduleData = analysisData.modules[moduleType];

    // 检查模块是否活跃
    if (!moduleData.active) {
        showError('该模块暂无有效数据');
        return;
    }

    // 更新模态框内容
    document.getElementById('modalTitle').textContent = config.name;
    document.getElementById('modalScore').textContent = moduleData.score;
    document.getElementById('modalMax').textContent = `/${config.maxScore}`;
    document.getElementById('modalEvaluation').textContent = moduleData.evaluation || '暂无评价';
    document.getElementById('modalSuggestions').textContent = moduleData.suggestions || '暂无建议';

    // 显示模态框
    document.getElementById('moduleModal').classList.add('active');
}

// 关闭模态框
function closeModal() {
    document.getElementById('moduleModal').classList.remove('active');
}

// 显示错误信息
function showError(message) {
    alert(message); // 简单使用alert，也可以改为更美观的提示
}

// 添加星球悬停效果
document.addEventListener('DOMContentLoaded', function() {
    const planets = document.querySelectorAll('.module-planet');
    
    planets.forEach(planet => {
        planet.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-15px) scale(1.1)';
        });
        
        planet.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});

// 添加星空动画
function createStars() {
    const starsContainer = document.querySelector('.stars-container');
    const starCount = 50;
    
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.className = `star ${Math.random() > 0.7 ? 'large' : Math.random() > 0.4 ? 'medium' : 'small'}`;
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        star.style.animationDelay = `${Math.random() * 3}s`;
        starsContainer.appendChild(star);
    }
}

// 初始化星空
createStars(); 