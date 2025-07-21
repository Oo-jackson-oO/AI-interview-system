// 面试结果页面JavaScript

// 高级粒子系统
class ParticleSystem {
    constructor() {
        this.canvas = document.getElementById('particles-canvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: 0, y: 0 };
        this.init();
    }

    init() {
        this.resize();
        this.createParticles();
        this.animate();
        this.addEventListeners();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    createParticles() {
        const particleCount = 100;
        for (let i = 0; i < particleCount; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2
            });
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        this.particles.forEach(particle => {
            // 更新位置
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // 边界检查
            if (particle.x < 0 || particle.x > this.canvas.width) particle.vx *= -1;
            if (particle.y < 0 || particle.y > this.canvas.height) particle.vy *= -1;
            
            // 绘制粒子
            this.ctx.beginPath();
            this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(255, 255, 255, ${particle.opacity})`;
            this.ctx.fill();
            
            // 鼠标交互
            const dx = particle.x - this.mouse.x;
            const dy = particle.y - this.mouse.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 100) {
                this.ctx.beginPath();
                this.ctx.moveTo(particle.x, particle.y);
                this.ctx.lineTo(this.mouse.x, this.mouse.y);
                this.ctx.strokeStyle = `rgba(255, 255, 255, ${0.1 * (1 - distance / 100)})`;
                this.ctx.stroke();
            }
        });
        
        requestAnimationFrame(() => this.animate());
    }

    addEventListeners() {
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
    }
}

// 星光系统
class StarSystem {
    constructor() {
        this.container = document.querySelector('.stars-container');
        this.stars = [];
        this.init();
    }

    init() {
        // 初始创建星星
        for (let i = 0; i < 50; i++) {
            this.createStar();
        }
        
        // 定期创建新星星
        setInterval(() => {
            this.createStar();
        }, 2000);
    }

    createStar() {
        const star = document.createElement('div');
        star.className = 'star';
        
        // 随机位置
        const x = Math.random() * window.innerWidth;
        const y = Math.random() * window.innerHeight;
        
        star.style.left = x + 'px';
        star.style.top = y + 'px';
        
        // 随机大小和类型
        const sizes = ['small', 'medium', 'large'];
        const size = sizes[Math.floor(Math.random() * sizes.length)];
        star.classList.add(size);
        
        // 随机添加彩色效果
        if (Math.random() > 0.7) {
            star.classList.add('colorful');
        }
        
        // 随机延迟
        star.style.animationDelay = Math.random() * 3 + 's';
        
        this.container.appendChild(star);
        this.stars.push(star);
        
        // 定期移除星星以控制数量
        setTimeout(() => {
            star.remove();
            this.stars = this.stars.filter(s => s !== star);
        }, 10000 + Math.random() * 5000);
    }
}

// 流星系统
class MeteorSystem {
    constructor() {
        this.container = document.querySelector('.meteor-container');
        this.meteors = [];
        this.init();
    }

    init() {
        // 初始创建流星
        for (let i = 0; i < 8; i++) {
            this.createMeteor();
        }
        
        // 定期创建新流星
        setInterval(() => {
            this.createMeteor();
        }, 800);
    }

    createMeteor() {
        const meteor = document.createElement('div');
        meteor.className = 'meteor';
        
        // 随机选择起始位置，让流星分布更自然
        const startPositions = [
            { x: -100, y: -100 },           // 左上角
            { x: -100, y: -50 },            // 左上偏中
            { x: -100, y: 0 },              // 左上
            { x: -50, y: -100 },            // 左上偏右
            { x: 0, y: -100 },              // 正上方
            { x: window.innerWidth * 0.2, y: -100 },  // 上方偏左
            { x: window.innerWidth * 0.4, y: -100 },  // 上方中左
            { x: window.innerWidth * 0.6, y: -100 },  // 上方中右
            { x: window.innerWidth * 0.8, y: -100 },  // 上方偏右
        ];
        
        const startPos = startPositions[Math.floor(Math.random() * startPositions.length)];
        const startX = startPos.x;
        const startY = startPos.y;
        
        // 计算结束位置，保持45度角移动
        const distance = Math.max(window.innerWidth, window.innerHeight) + 200;
        const endX = startX + distance;
        const endY = startY + distance;
        
        meteor.style.left = startX + 'px';
        meteor.style.top = startY + 'px';
        
        // 随机大小和速度
        const size = Math.random() * 2 + 3;
        const duration = Math.random() * 1 + 3; // 增加持续时间，降低频率
        
        meteor.style.width = size + 'px';
        meteor.style.height = size + 'px';
        
        // 创建自定义动画
        const animationName = 'meteor-' + Math.floor(Math.random() * 10000);
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes ${animationName} {
                0% {
                    transform: translate(0, 0) rotate(45deg);
                    opacity: 1;
                }
                70% {
                    opacity: 1;
                }
                100% {
                    transform: translate(${endX - startX}px, ${endY - startY}px) rotate(45deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
        
        meteor.style.animation = `${animationName} ${duration}s linear forwards`;
        
        this.container.appendChild(meteor);
        this.meteors.push(meteor);
        
        // 动画结束后移除流星
        setTimeout(() => {
            meteor.remove();
            this.meteors = this.meteors.filter(m => m !== meteor);
            style.remove();
        }, duration * 1000);
    }

    start() {
        // 降低流星生成频率：从每1-3秒改为每3-8秒
        this.interval = setInterval(() => {
            if (this.meteors.length < 3) { // 限制同时存在的流星数量
                this.createMeteor();
            }
        }, Math.random() * 5000 + 3000); // 3-8秒随机间隔
    }
}

// 火箭鼠标系统
class RocketCursorSystem {
    constructor() {
        this.cursor = document.getElementById('rocketCursor');
        this.isVisible = false;
        this.waveTimer = null;
        this.init();
    }

    init() {
        this.addEventListeners();
        this.startWaveTimer();
    }

    addEventListeners() {
        document.addEventListener('mousemove', (e) => {
            if (this.cursor) {
                this.cursor.style.left = e.clientX + 'px';
                this.cursor.style.top = e.clientY + 'px';
                
                if (!this.isVisible) {
                    this.cursor.style.opacity = '1';
                    this.isVisible = true;
                }
            }
        });

        document.addEventListener('mouseenter', () => {
            if (this.cursor) {
                this.cursor.style.opacity = '1';
                this.isVisible = true;
            }
        });

        document.addEventListener('mouseleave', () => {
            if (this.cursor) {
                this.cursor.style.opacity = '0';
                this.isVisible = false;
            }
        });

        // 点击时创建波动效果
        document.addEventListener('click', (e) => {
            this.createWave(e.clientX, e.clientY);
        });
    }

    startWaveTimer() {
        // 每3秒自动创建一个波动效果
        this.waveTimer = setInterval(() => {
            const x = Math.random() * window.innerWidth;
            const y = Math.random() * window.innerHeight;
            this.createWave(x, y);
        }, 3000);
    }

    createWave(x, y) {
        const wave = document.createElement('div');
        wave.className = 'rocket-wave';
        wave.style.left = x + 'px';
        wave.style.top = y + 'px';
        document.body.appendChild(wave);
        
        setTimeout(() => {
            wave.remove();
        }, 2000);
    }
}

// 黑洞转场系统
class BlackholeTransitionSystem {
    constructor() {
        this.transition = document.getElementById('blackholeTransition');
        this.init();
    }

    init() {
        // 检查是否从其他页面返回
        this.checkReturnFromOtherPage();
    }

    checkReturnFromOtherPage() {
        // 检查URL参数或sessionStorage中的标记
        const fromOtherPage = sessionStorage.getItem('fromOtherPage');
        if (fromOtherPage) {
            sessionStorage.removeItem('fromOtherPage');
            this.playReturnAnimation();
        }
    }

    playReturnAnimation() {
        if (this.transition) {
            this.transition.classList.add('active');
            this.transition.classList.add('enter');
            
            setTimeout(() => {
                this.transition.classList.remove('active');
                this.transition.classList.remove('enter');
            }, 500);
        }
    }

    static triggerReturnTransition() {
        sessionStorage.setItem('fromOtherPage', 'true');
    }
}

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
let currentCenter = 4; // 当前中心模块索引（默认第4个模块在中心）
const totalModules = 9; // 总共9个模块
let moduleData = {};
let isAnimating = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('面试结果页面初始化开始...');
    
    // 初始化背景系统
    new ParticleSystem();
    new StarSystem();
    new MeteorSystem();
    new RocketCursorSystem();
    new BlackholeTransitionSystem();
    
    // 初始化滑动控制器
    initCarousel();
    
    // 加载数据
    loadInterviewResultData();
    
    // 绑定事件监听器
    bindEventListeners();
});

// 初始化滑动控制器
function initCarousel() {
    console.log('初始化滑动控制器...');
    
    // 设置初始状态 - 第4个模块在中心
    setCenterModule(4);
    
    // 更新指示器状态
    updateIndicators();
    
    // 更新按钮状态
    updateControlButtons();
}

// 绑定事件监听器
function bindEventListeners() {
    // 绑定滑动按钮事件
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (!isAnimating) {
                slideToPrevious();
            }
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (!isAnimating) {
                slideToNext();
            }
        });
    }
    
    // 绑定指示器点击事件
    const indicators = document.querySelectorAll('.indicator');
    indicators.forEach((indicator, index) => {
        indicator.addEventListener('click', () => {
            if (!isAnimating) {
                setCenterModule(index);
            }
        });
    });
    
    // 绑定模块点击事件
    const modules = document.querySelectorAll('.module-planet');
    modules.forEach(module => {
        module.addEventListener('click', () => {
            const moduleName = module.getAttribute('data-module');
            if (moduleName && moduleData[moduleName]) {
                showModuleDetails(moduleName);
            }
        });
    });
    
    // 绑定模态框关闭事件
    const modal = document.getElementById('moduleModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    // 添加触摸滑动支持
    let startX = 0;
    let startY = 0;
    let isDragging = false;
    
    const carouselContainer = document.querySelector('.carousel-container');
    if (carouselContainer) {
        carouselContainer.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
            isDragging = true;
        });
        
        carouselContainer.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            
            const currentX = e.touches[0].clientX;
            const currentY = e.touches[0].clientY;
            const diffX = startX - currentX;
            const diffY = startY - currentY;
            
            // 如果水平滑动距离大于垂直滑动距离，阻止默认行为
            if (Math.abs(diffX) > Math.abs(diffY)) {
                e.preventDefault();
            }
        });
        
        carouselContainer.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            
            const endX = e.changedTouches[0].clientX;
            const diffX = startX - endX;
            const threshold = 50; // 滑动阈值
            
            if (Math.abs(diffX) > threshold) {
                if (diffX > 0) {
                    // 向左滑动，显示下一个模块
                    slideToNext();
                } else {
                    // 向右滑动，显示上一个模块
                    slideToPrevious();
                }
            }
            
            isDragging = false;
        });
    }
}

// 设置中心模块
function setCenterModule(centerIndex) {
    if (isAnimating || centerIndex < 0 || centerIndex >= totalModules) {
        return;
    }
    
    console.log(`设置中心模块: ${centerIndex}`);
    isAnimating = true;
    
    // 更新当前中心模块
    currentCenter = centerIndex;
    
    // 更新模块位置
    const modules = document.querySelectorAll('.module-planet');
    modules.forEach(module => {
        const index = parseInt(module.getAttribute('data-index'));
        module.className = `module-planet center-${centerIndex}`;
    });
    
    // 更新指示器
    updateIndicators();
    
    // 更新按钮状态
    updateControlButtons();
    
    // 动画完成后重置状态
    setTimeout(() => {
        isAnimating = false;
    }, 600);
}

// 滑动到下一个模块
function slideToNext() {
    const nextCenter = (currentCenter + 1) % totalModules;
    setCenterModule(nextCenter);
}

// 滑动到上一个模块
function slideToPrevious() {
    const prevCenter = (currentCenter - 1 + totalModules) % totalModules;
    setCenterModule(prevCenter);
}

// 更新指示器状态
function updateIndicators() {
    const indicators = document.querySelectorAll('.indicator');
    indicators.forEach((indicator, index) => {
        if (index === currentCenter) {
            indicator.classList.add('active');
        } else {
            indicator.classList.remove('active');
        }
    });
}

// 更新控制按钮状态
function updateControlButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    
    // 循环滑动，按钮始终可用
    if (prevBtn) {
        prevBtn.disabled = false;
    }
    
    if (nextBtn) {
        nextBtn.disabled = false;
    }
}

// 加载面试结果数据
async function loadInterviewResultData() {
    try {
        // 获取面试结果数据（包含所有文件的内容）
        const dataResponse = await fetch('/api/interview-result/data');
        if (!dataResponse.ok) {
            throw new Error(`获取数据失败: ${dataResponse.status}`);
        }
        
        const resultData = await dataResponse.json();
        console.log('面试结果数据:', resultData);
        
        if (!resultData.success) {
            throw new Error(resultData.message || '获取面试数据失败');
        }
        
        const fileData = resultData.file_data || {};
        const summaryData = resultData.summary_data || {};
        const configData = resultData.config_data || {};
        const resultDataFile = fileData['latest_interview_result.json'] || {};
        
        console.log('可用文件:', resultData.available_files);
        console.log('面试总结数据:', summaryData);
        console.log('面试配置数据:', configData);
        console.log('面试结果数据:', resultDataFile);
        
        // 优先使用面试总结报告数据
        if (summaryData && summaryData.section_evaluations) {
            console.log('✅ 使用面试总结报告数据');
            
            // 从面试总结报告中提取模块数据
            moduleData = extractModuleDataFromSummary(summaryData);
            
            // 补充其他分析数据
            if (fileData['facial_analysis_report.json']) {
                addFacialAnalysisData(moduleData, fileData['facial_analysis_report.json']);
            }
            
            if (fileData['voice_analysis_result.json']) {
                addVoiceAnalysisData(moduleData, fileData['voice_analysis_result.json']);
            }
            
        } else if (configData && configData.interview_config) {
            console.log('✅ 使用面试配置数据');
            
            // 从面试配置中提取模块数据
            moduleData = extractModuleDataFromConfig(configData, resultDataFile);
            
            // 补充分析数据
            if (fileData['facial_analysis_report.json']) {
                addFacialAnalysisData(moduleData, fileData['facial_analysis_report.json']);
            }
            
            if (fileData['voice_analysis_result.json']) {
                addVoiceAnalysisData(moduleData, fileData['voice_analysis_result.json']);
            }
            
        } else {
            console.log('⚠️ 使用传统数据结构');
            
            // 使用传统方式加载数据（向后兼容）
            const [facialData, voiceData] = await Promise.all([
                loadJSONFileFromData(fileData, 'facial_analysis_report.json'),
                loadJSONFileFromData(fileData, 'voice_analysis_result.json')
            ]);
            
            // 合并数据
            moduleData = mergeTraditionalData(facialData, voiceData);
        }
        
        console.log('最终模块数据:', moduleData);
        
        // 更新UI
        updateUI(moduleData);
        
    } catch (error) {
        console.error('加载面试结果数据失败:', error);
        
        // 显示错误信息
        const evaluationElement = document.getElementById('totalEvaluation');
        if (evaluationElement) {
            evaluationElement.textContent = '数据加载失败，请检查网络连接或稍后重试';
        }
    }
}

// 从面试总结报告中提取模块数据
function extractModuleDataFromSummary(summaryData) {
    const sectionEvaluations = summaryData.section_evaluations || {};
    const overallAssessment = summaryData.overall_assessment || {};
    
    // 板块名称映射
    const sectionMapping = {
        '自我介绍': 'self_introduction',
        '简历深挖': 'resume_digging', 
        '能力评估': 'ability_assessment',
        '岗位匹配度': 'position_matching',
        '专业能力测试': 'professional_skills',
        '反问环节': 'reverse_question'
    };
    
    const modules = {};
    
    // 处理面试板块数据
    Object.keys(sectionMapping).forEach(sectionName => {
        const moduleKey = sectionMapping[sectionName];
        const sectionData = sectionEvaluations[sectionName];
        
        if (sectionData) {
            // 正确提取分数，注意分数可能是0-100分制
            const rawScore = sectionData.score || 0;
            const maxScore = getMaxScoreForModule(moduleKey);
            
            // 如果原始分数是0-100分制，需要转换为模块对应的分数制
            let normalizedScore = rawScore;
            if (rawScore > maxScore) {
                // 如果分数超过模块最大分数，说明是0-100分制，需要转换
                normalizedScore = (rawScore / 100) * maxScore;
            }
            
            modules[moduleKey] = {
                score: Math.round(normalizedScore * 10) / 10, // 保留一位小数
                maxScore: maxScore,
                evaluation: sectionData.evaluation || '暂无评价',
                suggestions: sectionData.suggestions || '暂无建议',
                source: 'interview_summary',
                rawScore: rawScore, // 保存原始分数用于调试
                weightPercentage: sectionData.weight_percentage || 0
            };
            
            console.log(`${sectionName} 分数处理: 原始分数=${rawScore}, 转换后=${normalizedScore}, 最大分数=${maxScore}`);
        } else {
            // 如果没有数据，设置默认值
            modules[moduleKey] = {
                score: 0,
                maxScore: getMaxScoreForModule(moduleKey),
                evaluation: '该板块未参与面试',
                suggestions: '建议在下次面试中包含此板块',
                source: 'default'
            };
        }
    });
    
    // 其他模块设置默认值
    ['voice_tone', 'facial_analysis', 'body_language'].forEach(moduleKey => {
        modules[moduleKey] = {
            score: 0,
            maxScore: getMaxScoreForModule(moduleKey),
            evaluation: '该项分析数据未找到',
            suggestions: '建议启用相关分析功能',
            source: 'default'
        };
    });
    
    // 设置总分 - 使用面试总结报告中的最终分数
    const finalScore = overallAssessment.final_score || 0;
    modules.totalScore = finalScore;
    modules.totalMaxScore = 100;
    modules.grade = overallAssessment.grade || '未知';
    modules.recommendation = overallAssessment.recommendation || '暂无建议';
    
    console.log(`总分设置: ${finalScore}/100, 评级: ${modules.grade}`);
    
    return modules;
}

// 从面试配置和结果中提取模块数据
function extractModuleDataFromConfig(configData, resultData) {
    const modules = {};
    
    // 从面试配置中获取选择的板块
    const selectedSections = configData?.interview_config?.selected_sections || [];
    const candidateName = configData?.interview_config?.candidate_name || '未知';
    const position = configData?.interview_config?.position || '未知';
    
    console.log('面试配置信息:', {
        candidateName,
        position,
        selectedSections
    });
    
    // 为所有模块设置默认值
    const allModules = [
        'self_introduction', 'resume_digging', 'ability_assessment', 
        'position_matching', 'professional_skills', 'reverse_question',
        'voice_tone', 'facial_analysis', 'body_language'
    ];
    
    allModules.forEach(moduleKey => {
        const moduleName = getModuleDisplayName(moduleKey);
        const isSelected = selectedSections.includes(moduleName);
        
        modules[moduleKey] = {
            score: 0,
            maxScore: getMaxScoreForModule(moduleKey),
            evaluation: isSelected ? '该板块已参与面试，等待详细分析' : '该板块未参与面试',
            suggestions: isSelected ? '建议查看详细分析结果' : '建议在下次面试中包含此板块',
            source: isSelected ? 'config_selected' : 'default'
        };
    });
    
    // 如果有面试结果数据，尝试从中提取信息
    if (resultData && resultData.interview_data && resultData.interview_data.length > 0) {
        console.log('发现面试结果数据，包含', resultData.interview_data.length, '条记录');
        
        // 这里可以根据实际的面试数据结构来提取评分
        // 目前先设置为默认值，后续可以根据实际数据结构调整
        modules.totalScore = 0;
        modules.totalMaxScore = 100;
        modules.grade = '待评估';
        modules.recommendation = '面试已完成，建议查看详细分析';
    } else {
        modules.totalScore = 0;
        modules.totalMaxScore = 100;
        modules.grade = '未完成';
        modules.recommendation = '面试尚未完成或数据不完整';
    }
    
    return modules;
}

// 获取模块的显示名称
function getModuleDisplayName(moduleKey) {
    const displayNames = {
        'self_introduction': '自我介绍',
        'resume_digging': '简历深挖',
        'ability_assessment': '能力评估',
        'position_matching': '岗位匹配度',
        'professional_skills': '专业能力测试',
        'reverse_question': '反问环节'
    };
    
    return displayNames[moduleKey] || moduleKey;
}

// 获取模块的最大分数
function getMaxScoreForModule(moduleKey) {
    const maxScores = {
        'self_introduction': 10,
        'resume_digging': 15,
        'ability_assessment': 15,
        'position_matching': 10,
        'professional_skills': 20,
        'reverse_question': 5,
        'voice_tone': 5,
        'facial_analysis': 10,
        'body_language': 10
    };
    
    return maxScores[moduleKey] || 10;
}

// 添加微表情分析数据
function addFacialAnalysisData(moduleData, facialData) {
    console.log('添加微表情分析数据:', facialData);
    
    if (facialData && facialData.performance_summary) {
        const performanceSummary = facialData.performance_summary;
        
        // 微表情分析
        if (performanceSummary['微表情表现']) {
            const facialScore = performanceSummary['微表情表现']['平均分'] || 0;
            moduleData.facial_analysis = {
                score: Math.min(facialScore, 10),
                maxScore: 10,
                evaluation: `微表情综合得分 ${facialScore}/10，检测到 ${facialData.total_analysis_count || 0} 次表情变化`,
                suggestions: facialData['改进建议汇总']?.['微表情建议']?.join(' ') || '保持自然的面部表情，适当的微笑会增加亲和力',
                source: 'facial_analysis'
            };
            console.log(`微表情分析分数: ${facialScore}/10`);
        }
        
        // 肢体语言分析
        if (performanceSummary['肢体动作表现']) {
            const bodyScore = performanceSummary['肢体动作表现']['平均分'] || 0;
            moduleData.body_language = {
                score: Math.min(bodyScore, 10),
                maxScore: 10,
                evaluation: `肢体语言综合得分 ${bodyScore}/10，检测到 ${facialData.total_analysis_count || 0} 次动作变化`,
                suggestions: facialData['改进建议汇总']?.['肢体动作建议']?.join(' ') || '保持良好的坐姿和手势',
                source: 'facial_analysis'
            };
            console.log(`肢体语言分析分数: ${bodyScore}/10`);
        }
    }
}

// 添加语调分析数据
function addVoiceAnalysisData(moduleData, voiceData) {
    console.log('添加语调分析数据:', voiceData);
    
    if (voiceData && voiceData.analysis_info) {
        const analysisInfo = voiceData.analysis_info;
        const rawScore = analysisInfo.overall_score || 0;
        const score = rawScore * 5; // 转换为5分制
        
        moduleData.voice_tone = {
            score: Math.min(score, 5),
            maxScore: 5,
            evaluation: `语调综合得分 ${rawScore}/1.0 (${score}/5.0)，音调变化 ${analysisInfo.pitch_variation || 0}`,
            suggestions: '保持语调自然变化，避免过于单调',
            source: 'voice_analysis'
        };
        console.log(`语调分析分数: ${rawScore}/1.0 -> ${score}/5.0`);
    }
}

// 从数据中加载JSON文件
function loadJSONFileFromData(fileData, filename) {
    return new Promise((resolve) => {
        const data = fileData[filename];
        if (data) {
            console.log(`✅ 从缓存数据加载 ${filename}`);
            resolve(data);
        } else {
            console.log(`⚠️ 文件 ${filename} 不存在于缓存数据中`);
            resolve(null);
        }
    });
}

// 合并传统数据（向后兼容）
function mergeTraditionalData(facialData, voiceData) {
    const modules = {};
    
    // 设置默认的面试模块
    ['self_introduction', 'resume_digging', 'ability_assessment', 'position_matching', 'professional_skills', 'reverse_question'].forEach(moduleKey => {
        modules[moduleKey] = {
            score: 0,
            maxScore: getMaxScoreForModule(moduleKey),
            evaluation: '该板块数据未找到',
            suggestions: '请完成完整的面试流程',
            source: 'default'
        };
    });
    
    // 添加分析数据
    if (facialData) {
        addFacialAnalysisData(modules, facialData);
    }
    
    if (voiceData) {
        addVoiceAnalysisData(modules, voiceData);
    }
    
    // 设置肢体语言默认值
    if (!modules.body_language) {
        modules.body_language = {
            score: 0,
            maxScore: 10,
            evaluation: '肢体语言分析数据未找到',
            suggestions: '保持良好的坐姿和手势',
            source: 'default'
        };
    }
    
    // 计算总分（基于可用数据）
    let totalScore = 0;
    let availableModules = 0;
    
    Object.keys(modules).forEach(key => {
        if (modules[key].source !== 'default') {
            totalScore += (modules[key].score / modules[key].maxScore) * 100;
            availableModules++;
        }
    });
    
    modules.totalScore = availableModules > 0 ? totalScore / availableModules : 0;
    modules.totalMaxScore = 100;
    modules.grade = modules.totalScore >= 80 ? '良好' : modules.totalScore >= 60 ? '一般' : '待提升';
    modules.recommendation = modules.totalScore >= 80 ? '表现不错，继续保持' : '需要在某些方面加强练习';
    
    return modules;
}

// 标准化分数
function normalizeScore(rawScore, maxScore) {
    console.log(`标准化分数: 原始分数=${rawScore}, 最大分数=${maxScore}`);
    
    // 如果原始分数是0-100的百分比，转换为实际分数
    if (rawScore <= 100 && rawScore >= 0) {
        const normalizedScore = (rawScore / 100) * maxScore;
        console.log(`标准化后的分数: ${normalizedScore}`);
        return Math.round(normalizedScore * 10) / 10; // 保留一位小数
    }
    
    // 如果原始分数已经是实际分数，直接返回
    if (rawScore <= maxScore && rawScore >= 0) {
        console.log(`分数已经是标准格式: ${rawScore}`);
        return Math.round(rawScore * 10) / 10;
    }
    
    // 其他情况，返回0
    console.log(`无法识别的分数格式，返回0`);
    return 0;
}

// 统一的UI更新函数
function updateUI(moduleData) {
    console.log('开始更新UI，模块数据:', moduleData);
    
    // 更新总分
    updateTotalScore(moduleData);
    
    // 更新各模块分数
    updateModuleScores(moduleData);
    
    console.log('UI更新完成');
}

// 更新总分
function updateTotalScore(moduleData) {
    const totalScoreElement = document.getElementById('totalScore');
    const totalProgressElement = document.getElementById('totalProgress');
    const totalEvaluationElement = document.getElementById('totalEvaluation');
    
    if (totalScoreElement && totalProgressElement && totalEvaluationElement) {
        const totalScore = moduleData.totalScore || 0;
        const totalMaxScore = moduleData.totalMaxScore || 100;
        const grade = moduleData.grade || '未知';
        const recommendation = moduleData.recommendation || '暂无建议';
        
        // 更新分数显示
        totalScoreElement.textContent = Math.round(totalScore);
        
        // 更新进度条
        const progressPercentage = (totalScore / totalMaxScore) * 100;
        totalProgressElement.style.width = `${progressPercentage}%`;
        
        // 更新评价
        totalEvaluationElement.textContent = `${grade} - ${recommendation}`;
        
        console.log(`总分更新: ${totalScore}/${totalMaxScore} (${progressPercentage.toFixed(1)}%)`);
    }
}

// 更新各模块分数
function updateModuleScores(moduleData) {
    const moduleKeys = [
        'self_introduction', 'resume_digging', 'ability_assessment',
        'position_matching', 'professional_skills', 'reverse_question',
        'voice_tone', 'facial_analysis', 'body_language'
    ];
    
    moduleKeys.forEach(moduleKey => {
        const scoreElement = document.getElementById(`${moduleKey}_score`);
        if (scoreElement) {
            const moduleData_item = moduleData[moduleKey];
            if (moduleData_item) {
                scoreElement.textContent = Math.round(moduleData_item.score);
                console.log(`${moduleKey} 分数更新: ${moduleData_item.score}/${moduleData_item.maxScore}`);
            }
        }
    });
}

// 显示模块详情
function showModuleDetails(moduleKey) {
    console.log(`显示模块详情: ${moduleKey}`);
    
    const moduleData_item = moduleData[moduleKey];
    if (!moduleData_item) {
        console.warn(`未找到模块 ${moduleKey} 的数据`);
        return;
    }
    
    // 获取模块显示名称
    const displayName = getModuleDisplayName(moduleKey);
    
    // 更新模态框内容
    const modalTitle = document.getElementById('modalTitle');
    const modalScore = document.getElementById('modalScore');
    const modalMax = document.getElementById('modalMax');
    const modalEvaluation = document.getElementById('modalEvaluation');
    const modalSuggestions = document.getElementById('modalSuggestions');
    
    if (modalTitle) modalTitle.textContent = displayName;
    if (modalScore) modalScore.textContent = Math.round(moduleData_item.score);
    if (modalMax) modalMax.textContent = `/${moduleData_item.maxScore}`;
    if (modalEvaluation) modalEvaluation.textContent = moduleData_item.evaluation || '暂无评价';
    if (modalSuggestions) modalSuggestions.textContent = moduleData_item.suggestions || '暂无建议';
    
    // 显示模态框
    const modal = document.getElementById('moduleModal');
    modal.classList.add('active');
    
    console.log(`模块详情已更新: ${displayName} - ${moduleData_item.score}/${moduleData_item.maxScore}`);
}

// 关闭模态框
function closeModal() {
    console.log('关闭模态框');
    const modal = document.getElementById('moduleModal');
    modal.classList.remove('active');
} 