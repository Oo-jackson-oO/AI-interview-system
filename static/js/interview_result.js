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
        console.log('开始加载数据，用户:', currentUser);
        
        // 加载三个JSON文件
        const [summaryData, facialData, analysisData] = await Promise.all([
            fetch(`/uploads/${currentUser}/interview_summary_report.json`).then(r => r.json()).catch(e => {
                console.error('加载interview_summary_report.json失败:', e);
                return null;
            }),
            fetch(`/uploads/${currentUser}/facial_analysis_report.json`).then(r => r.json()).catch(e => {
                console.error('加载facial_analysis_report.json失败:', e);
                return null;
            }),
            fetch(`/uploads/${currentUser}/analysis_result.json`).then(r => r.json()).catch(e => {
                console.error('加载analysis_result.json失败:', e);
                return null;
            })
        ]);

        console.log('加载的原始数据:');
        console.log('summaryData:', summaryData);
        console.log('facialData:', facialData);
        console.log('analysisData:', analysisData);

        // 合并数据
        const combinedData = combineData(summaryData, facialData, analysisData);
        
        console.log('合并后的数据:', combinedData);
        
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
    if (summaryData && summaryData.section_evaluations) {
        // 个人介绍 - 满分10分，需要将0-100分转换为0-10分
        if (summaryData.section_evaluations['自我介绍']) {
            const data = summaryData.section_evaluations['自我介绍'];
            const maxScore = MODULE_CONFIG.self_introduction.maxScore;
            const realScore = Math.round((data.score || 0) * maxScore / 100);
            modules.self_introduction = {
                score: realScore,
                evaluation: data.evaluation || '',
                suggestions: data.suggestions || '',
                active: true
            };
        }
        
        // 简历深挖 - 满分15分，需要将0-100分转换为0-15分
        if (summaryData.section_evaluations['简历深挖']) {
            const data = summaryData.section_evaluations['简历深挖'];
            const maxScore = MODULE_CONFIG.resume_digging.maxScore;
            const realScore = Math.round((data.score || 0) * maxScore / 100);
            modules.resume_digging = {
                score: realScore,
                evaluation: data.evaluation || '',
                suggestions: data.suggestions || '',
                active: true
            };
        }
        
        // 岗位匹配 - 满分10分，需要将0-100分转换为0-10分
        if (summaryData.section_evaluations['岗位匹配度']) {
            const data = summaryData.section_evaluations['岗位匹配度'];
            const maxScore = MODULE_CONFIG.position_matching.maxScore;
            const realScore = Math.round((data.score || 0) * maxScore / 100);
            modules.position_matching = {
                score: realScore,
                evaluation: data.evaluation || '',
                suggestions: data.suggestions || '',
                active: true
            };
        }
        
        // 反问环节 - 满分5分，需要将0-100分转换为0-5分
        if (summaryData.section_evaluations['反问环节']) {
            const data = summaryData.section_evaluations['反问环节'];
            const maxScore = MODULE_CONFIG.reverse_question.maxScore;
            const realScore = Math.round((data.score || 0) * maxScore / 100);
            modules.reverse_question = {
                score: realScore,
                evaluation: data.evaluation || '',
                suggestions: data.suggestions || '',
                active: true
            };
        }
        
        // 能力评估 - 满分15分，基于自我介绍和简历深挖的综合评估
        const abilityScore = Math.round((modules.self_introduction?.score || 0) * 0.8);
        modules.ability_assessment = {
            score: abilityScore,
            evaluation: '基于自我介绍和简历深挖环节的综合评估',
            suggestions: '建议加强技术能力的展示和项目经验的详细描述',
            active: true
        };
        
        // 专业能力 - 满分20分，基于简历深挖的专业技能评估
        const professionalScore = Math.round((modules.resume_digging?.score || 0) * 1.2);
        modules.professional_skills = {
            score: professionalScore,
            evaluation: '基于简历深挖环节的专业技能评估',
            suggestions: '建议深入学习相关技术栈，提升项目经验的展示质量',
            active: true
        };
    } else {
        // 如果没有面试总结数据，设置默认值
        modules.self_introduction = {
            score: 0,
            evaluation: '暂无自我介绍数据',
            suggestions: '建议进行自我介绍环节',
            active: false
        };
        
        modules.resume_digging = {
            score: 0,
            evaluation: '暂无简历深挖数据',
            suggestions: '建议进行简历深挖环节',
            active: false
        };
        
        modules.position_matching = {
            score: 0,
            evaluation: '暂无岗位匹配数据',
            suggestions: '建议进行岗位匹配分析',
            active: false
        };
        
        modules.reverse_question = {
            score: 0,
            evaluation: '暂无反问环节数据',
            suggestions: '建议进行反问环节',
            active: false
        };
        
        modules.ability_assessment = {
            score: 0,
            evaluation: '暂无能力评估数据',
            suggestions: '建议进行能力评估',
            active: false
        };
        
        modules.professional_skills = {
            score: 0,
            evaluation: '暂无专业能力数据',
            suggestions: '建议进行专业能力评估',
            active: false
        };
    }
    
    // 从facial_analysis_report.json获取数据
    if (facialData && facialData.performance_summary) {
        // 神态分析 - 满分10分，微表情平均分是0-10分制，需要转换为0-10分
        const facialScore = facialData.performance_summary['微表情表现']?.平均分 || 0;
        const maxScore = MODULE_CONFIG.facial_analysis.maxScore;
        const realFacialScore = Math.round(facialScore * maxScore / 10);
        modules.facial_analysis = {
            score: realFacialScore,
            evaluation: facialData.performance_summary['微表情表现']?.表现评级 || '一般',
            suggestions: facialData.改进建议汇总?.微表情建议?.join(' ') || '建议保持自然的面部表情',
            active: true
        };
        
        // 肢体语言 - 满分10分，肢体动作平均分是0-10分制，需要转换为0-10分
        const bodyScore = facialData.performance_summary['肢体动作表现']?.平均分 || 0;
        const realBodyScore = Math.round(bodyScore * maxScore / 10);
        modules.body_language = {
            score: realBodyScore,
            evaluation: facialData.performance_summary['肢体动作表现']?.表现评级 || '一般',
            suggestions: facialData.改进建议汇总?.肢体动作建议?.join(' ') || '建议改善坐姿和手势',
            active: true
        };
    } else {
        // 如果没有微表情数据，设置默认值
        modules.facial_analysis = {
            score: 0,
            evaluation: '暂无微表情分析数据',
            suggestions: '建议进行微表情分析',
            active: false
        };
        
        modules.body_language = {
            score: 0,
            evaluation: '暂无肢体语言分析数据',
            suggestions: '建议进行肢体语言分析',
            active: false
        };
    }
    
    // 从analysis_result.json获取数据
    if (analysisData && analysisData.analysis_info) {
        // 语音语调 - 满分5分，overall_score是0-1分制，需要转换为0-5分
        const voiceScore = analysisData.analysis_info.overall_score || 0;
        const maxScore = MODULE_CONFIG.voice_tone.maxScore;
        const realVoiceScore = Math.round(voiceScore * maxScore);
        modules.voice_tone = {
            score: realVoiceScore,
            evaluation: analysisData.fluency_analysis?.fluency_level || '一般',
            suggestions: analysisData.recommendations?.speech_rate_advice + ' ' + 
                        analysisData.recommendations?.fluency_advice || '建议改善语音语调',
            active: true
        };
    } else {
        // 如果没有语音语调数据，设置默认值
        modules.voice_tone = {
            score: 0,
            evaluation: '暂无语音语调数据',
            suggestions: '建议进行语音语调分析',
            active: false
        };
    }
    
    // 计算总分 - 只计算有分数的部分
    const activeModules = Object.values(modules).filter(module => module.active && module.score > 0);
    const totalScore = activeModules.reduce((sum, module) => sum + module.score, 0);
    
    // 计算有分数的部分的总满分
    const totalMaxScore = activeModules.reduce((sum, module) => {
        const moduleKey = Object.keys(modules).find(key => modules[key] === module);
        return sum + (MODULE_CONFIG[moduleKey]?.maxScore || 0);
    }, 0);
    
    // 计算总分：有分数的分数之和除以有分数的模块的总分之和（限制在0-100范围内）
    const finalScore = totalMaxScore > 0 ? Math.min(100, Math.round((totalScore / totalMaxScore) * 100)) : 0;
    
    console.log('总分计算详情:');
    console.log('活跃模块:', activeModules.map(m => ({ score: m.score, active: m.active })));
    console.log('总分数:', totalScore);
    console.log('总满分:', totalMaxScore);
    console.log('最终分数:', finalScore);
    
    return {
        modules,
        totalScore: finalScore,
        totalEvaluation: summaryData?.overall_assessment?.recommendation || '面试表现良好，继续保持！',
        totalSuggestions: summaryData?.recommendations?.overall_suggestion || '建议继续提升专业技能和沟通能力。'
    };
}

// 更新页面显示
function updatePage(data) {
    analysisData = data;
    
    console.log('开始更新页面，数据:', data);
    
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
            const planetElement = document.querySelector(`[data-module="${moduleKey}"]`);
            
            console.log(`处理模块 ${moduleKey}:`, moduleData);
            
            if (moduleData && moduleData.active && moduleData.score > 0) {
                // 更新分数
                scoreElement.textContent = moduleData.score;
                
                // 添加活跃状态
                planetElement.classList.add('active');
                planetElement.classList.remove('inactive');
                console.log(`${moduleKey} 设置为活跃状态，分数: ${moduleData.score}`);
            } else {
                // 零分或非活跃状态 - 显示黯淡且不可交互
                scoreElement.textContent = '0';
                planetElement.classList.add('inactive');
                planetElement.classList.remove('active');
                console.log(`${moduleKey} 设置为黯淡状态，分数: ${moduleData?.score || 0}`);
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

    // 检查模块是否活跃且有分数
    if (!moduleData.active || moduleData.score <= 0) {
        showError('该模块暂无有效数据或分数为零');
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