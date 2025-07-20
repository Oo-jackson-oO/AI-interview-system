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
    loadInterviewData();
    
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

// 加载面试数据
async function loadInterviewData() {
    console.log('开始加载面试数据...');
    
    try {
        // 获取当前用户名（这里需要根据实际登录状态获取）
        const username = getCurrentUsername();
        if (!username) {
            console.error('未找到用户名');
            return;
        }
        
        console.log(`加载用户 ${username} 的面试数据...`);
        
        // 首先检查用户是否有可用的数据文件
        const dataCheckResponse = await fetch('/api/interview-result/data');
        if (!dataCheckResponse.ok) {
            throw new Error(`检查数据文件失败: ${dataCheckResponse.status}`);
        }
        
        const dataCheck = await dataCheckResponse.json();
        console.log('数据文件检查结果:', dataCheck);
        
        if (!dataCheck.success) {
            throw new Error(dataCheck.message || '检查数据文件失败');
        }
        
        // 加载三个JSON文件
        const [summaryData, facialData, voiceData] = await Promise.all([
            loadJSONFile(`/uploads/${username}/interview_summary_report.json`),
            loadJSONFile(`/uploads/${username}/facial_analysis_report.json`),
            loadJSONFile(`/uploads/${username}/analysis_result.json`)
        ]);
        
        console.log('JSON文件加载完成:');
        console.log('summaryData:', summaryData);
        console.log('facialData:', facialData);
        console.log('voiceData:', voiceData);
        
        // 合并数据
        moduleData = mergeModuleData(summaryData, facialData, voiceData);
        console.log('合并后的模块数据:', moduleData);
        
        // 更新UI
        updateModuleScores();
        updateTotalScore();
        
        console.log('数据加载和UI更新完成');
        
    } catch (error) {
        console.error('加载面试数据时出错:', error);
        // 显示错误信息
        const evaluationElement = document.getElementById('totalEvaluation');
        if (evaluationElement) {
            evaluationElement.textContent = '数据加载失败，请检查网络连接或登录状态';
        }
    }
}

// 获取当前用户名
function getCurrentUsername() {
    // 尝试从URL参数获取用户名
    const urlParams = new URLSearchParams(window.location.search);
    const userFromUrl = urlParams.get('user');
    
    if (userFromUrl) {
        console.log(`从URL参数获取用户名: ${userFromUrl}`);
        return userFromUrl;
    }
    
    // 尝试从session或localStorage获取
    try {
        const sessionUser = sessionStorage.getItem('currentUser');
        if (sessionUser) {
            console.log(`从sessionStorage获取用户名: ${sessionUser}`);
            return sessionUser;
        }
    } catch (e) {
        console.warn('无法从sessionStorage获取用户信息:', e);
    }
    
    // 默认返回测试用户名
    console.log('使用默认测试用户名: alivin');
    return 'alivin';
}

// 加载JSON文件
async function loadJSONFile(url) {
    try {
        console.log(`尝试加载文件: ${url}`);
        const response = await fetch(url);
        console.log(`响应状态: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`成功加载 ${url}:`, data);
        return data;
    } catch (error) {
        console.warn(`加载 ${url} 失败:`, error);
        return null;
    }
}

// 合并模块数据
function mergeModuleData(summaryData, facialData, voiceData) {
    const mergedData = {};
    
    // 定义模块配置
    const moduleConfigs = {
        self_introduction: { maxScore: 10, key: 'self_introduction' },
        resume_digging: { maxScore: 15, key: 'resume_digging' },
        ability_assessment: { maxScore: 15, key: 'ability_assessment' },
        position_matching: { maxScore: 10, key: 'position_matching' },
        professional_skills: { maxScore: 20, key: 'professional_skills' },
        reverse_question: { maxScore: 5, key: 'reverse_question' },
        voice_tone: { maxScore: 5, key: 'voice_tone' },
        facial_analysis: { maxScore: 10, key: 'facial_analysis' },
        body_language: { maxScore: 10, key: 'body_language' }
    };
    
    // 处理面试总结数据
    if (summaryData) {
        console.log('处理面试总结数据...');
        
        // 个人介绍
        if (summaryData.section_evaluations && summaryData.section_evaluations['自我介绍']) {
            const data = summaryData.section_evaluations['自我介绍'];
            mergedData.self_introduction = {
                score: normalizeScore(data.score || 0, 10),
                maxScore: 10,
                evaluation: data.evaluation || '暂无评价',
                suggestions: data.suggestions || '暂无建议'
            };
        }
        
        // 简历深挖
        if (summaryData.section_evaluations && summaryData.section_evaluations['简历深挖']) {
            const data = summaryData.section_evaluations['简历深挖'];
            mergedData.resume_digging = {
                score: normalizeScore(data.score || 0, 15),
                maxScore: 15,
                evaluation: data.evaluation || '暂无评价',
                suggestions: data.suggestions || '暂无建议'
            };
        }
        
        // 能力评估 - 基于自我介绍和简历深挖的综合评估
        const selfIntroScore = mergedData.self_introduction?.score || 0;
        const resumeScore = mergedData.resume_digging?.score || 0;
        const abilityScore = Math.round((selfIntroScore + resumeScore) * 0.75);
        mergedData.ability_assessment = {
            score: abilityScore,
            maxScore: 15,
            evaluation: '基于自我介绍和简历深挖环节的综合评估',
            suggestions: '建议加强技术能力的展示和项目经验的详细描述'
        };
        
        // 岗位匹配
        if (summaryData.section_evaluations && summaryData.section_evaluations['岗位匹配度']) {
            const data = summaryData.section_evaluations['岗位匹配度'];
            mergedData.position_matching = {
                score: normalizeScore(data.score || 0, 10),
                maxScore: 10,
                evaluation: data.evaluation || '暂无评价',
                suggestions: data.suggestions || '暂无建议'
            };
        }
        
        // 专业能力 - 基于简历深挖的专业技能评估
        const professionalScore = Math.round((mergedData.resume_digging?.score || 0) * 1.33);
        mergedData.professional_skills = {
            score: professionalScore,
            maxScore: 20,
            evaluation: '基于简历深挖环节的专业技能评估',
            suggestions: '建议深入学习相关技术栈，提升项目经验的展示质量'
        };
        
        // 反问环节
        if (summaryData.section_evaluations && summaryData.section_evaluations['反问环节']) {
            const data = summaryData.section_evaluations['反问环节'];
            mergedData.reverse_question = {
                score: normalizeScore(data.score || 0, 5),
                maxScore: 5,
                evaluation: data.evaluation || '暂无评价',
                suggestions: data.suggestions || '暂无建议'
            };
        }
    }
    
    // 处理面部分析数据
    if (facialData) {
        console.log('处理面部分析数据...');
        
        // 神态分析
        if (facialData.performance_summary && facialData.performance_summary['微表情表现']) {
            const data = facialData.performance_summary['微表情表现'];
            mergedData.facial_analysis = {
                score: normalizeScore(data.平均分 || 0, 10),
                maxScore: 10,
                evaluation: data.表现评级 || '暂无评价',
                suggestions: facialData.改进建议汇总?.微表情建议?.join(' ') || '建议保持自然的面部表情'
            };
        }
        
        // 肢体语言
        if (facialData.performance_summary && facialData.performance_summary['肢体动作表现']) {
            const data = facialData.performance_summary['肢体动作表现'];
            mergedData.body_language = {
                score: normalizeScore(data.平均分 || 0, 10),
                maxScore: 10,
                evaluation: data.表现评级 || '暂无评价',
                suggestions: facialData.改进建议汇总?.肢体动作建议?.join(' ') || '建议改善坐姿和手势'
            };
        }
    }
    
    // 处理语音语调数据
    if (voiceData) {
        console.log('处理语音语调数据...');
        
        // 语音语调
        if (voiceData.analysis_info) {
            const data = voiceData.analysis_info;
            // 将0-1的分数转换为0-5分
            const voiceScore = (data.overall_score || 0) * 5;
            mergedData.voice_tone = {
                score: normalizeScore(voiceScore, 5),
                maxScore: 5,
                evaluation: voiceData.fluency_analysis?.fluency_level || '暂无评价',
                suggestions: (voiceData.recommendations?.speech_rate_advice || '') + ' ' + 
                           (voiceData.recommendations?.fluency_advice || '') || '建议改善语音语调'
            };
        }
    }
    
    // 为缺失的模块设置默认值
    Object.keys(moduleConfigs).forEach(moduleName => {
        if (!mergedData[moduleName]) {
            mergedData[moduleName] = {
                score: 0,
                maxScore: moduleConfigs[moduleName].maxScore,
                evaluation: '暂无数据',
                suggestions: '暂无建议'
            };
        }
    });
    
    console.log('数据合并完成:', mergedData);
    return mergedData;
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

// 更新模块分数
function updateModuleScores() {
    console.log('更新模块分数...');
    
    Object.keys(moduleData).forEach(moduleName => {
        const data = moduleData[moduleName];
        const scoreElement = document.getElementById(`${moduleName}_score`);
        const planetElement = document.querySelector(`[data-module="${moduleName}"]`);
        
        console.log(`更新模块 ${moduleName}:`, data);
        
        if (scoreElement && data) {
            // 动画更新分数
            animateScore(scoreElement, 0, data.score);
            
            // 更新模块状态
            if (planetElement) {
                if (data.score > 0) {
                    planetElement.classList.add('active');
                    planetElement.classList.remove('inactive');
                    console.log(`${moduleName} 设置为活跃状态，分数: ${data.score}`);
                } else {
                    planetElement.classList.add('inactive');
                    planetElement.classList.remove('active');
                    console.log(`${moduleName} 设置为黯淡状态，分数: ${data.score}`);
                }
            }
        } else {
            console.warn(`未找到模块 ${moduleName} 的分数元素或数据`);
        }
    });
}

// 动画更新分数
function animateScore(element, startValue, endValue) {
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // 使用缓动函数
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        const currentValue = startValue + (endValue - startValue) * easeOutQuart;
        
        element.textContent = currentValue.toFixed(1);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = endValue.toFixed(1);
        }
    }
    
    requestAnimationFrame(update);
}

// 更新总分
function updateTotalScore() {
    console.log('更新总分...');
    
    const activeModules = Object.values(moduleData).filter(module => module.score > 0);
    
    console.log('活跃模块:', activeModules);
    
    if (activeModules.length === 0) {
        console.log('没有活跃模块，总分设为0');
        document.getElementById('totalScore').textContent = '0';
        document.getElementById('totalProgress').style.width = '0%';
        document.getElementById('totalEvaluation').textContent = '暂无有效数据';
        return;
    }
    
    const totalScore = activeModules.reduce((sum, module) => sum + module.score, 0);
    const totalMaxScore = activeModules.reduce((sum, module) => sum + module.maxScore, 0);
    const percentage = (totalScore / totalMaxScore) * 100;
    
    console.log(`总分计算: ${totalScore}/${totalMaxScore} = ${percentage.toFixed(1)}%`);
    
    // 动画更新总分
    const totalScoreElement = document.getElementById('totalScore');
    const progressElement = document.getElementById('totalProgress');
    
    animateScore(totalScoreElement, 0, totalScore);
    
    // 动画更新进度条
    setTimeout(() => {
        progressElement.style.width = `${percentage}%`;
    }, 500);
    
    // 更新评价
    let evaluation = '';
    if (percentage >= 90) {
        evaluation = '优秀！您的面试表现非常出色，展现了扎实的专业能力和良好的沟通技巧。';
    } else if (percentage >= 80) {
        evaluation = '良好！您的面试表现不错，在大部分方面都有很好的表现。';
    } else if (percentage >= 70) {
        evaluation = '中等！您的面试表现尚可，但还有提升空间。';
    } else if (percentage >= 60) {
        evaluation = '及格！您的面试表现基本合格，建议加强薄弱环节。';
    } else {
        evaluation = '需要改进！建议您针对性地提升面试技巧和专业知识。';
    }
    
    document.getElementById('totalEvaluation').textContent = evaluation;
}

// 显示模块详情
function showModuleDetails(moduleName) {
    console.log(`显示模块详情: ${moduleName}`);
    
    const data = moduleData[moduleName];
    if (!data) {
        console.warn(`模块 ${moduleName} 没有数据`);
        return;
    }
    
    // 更新模态框内容
    document.getElementById('modalTitle').textContent = getModuleDisplayName(moduleName);
    document.getElementById('modalScore').textContent = data.score.toFixed(1);
    document.getElementById('modalMax').textContent = `/${data.maxScore}`;
    document.getElementById('modalEvaluation').textContent = data.evaluation;
    document.getElementById('modalSuggestions').textContent = data.suggestions;
    
    // 显示模态框
    const modal = document.getElementById('moduleModal');
    modal.classList.add('active');
    
    console.log('模态框已显示');
}

// 关闭模态框
function closeModal() {
    console.log('关闭模态框');
    const modal = document.getElementById('moduleModal');
    modal.classList.remove('active');
}

// 获取模块显示名称
function getModuleDisplayName(moduleName) {
    const displayNames = {
        'self_introduction': '个人介绍',
        'resume_digging': '简历深挖',
        'ability_assessment': '能力评估',
        'position_matching': '岗位匹配',
        'professional_skills': '专业能力',
        'reverse_question': '反问环节',
        'voice_tone': '语音语调',
        'facial_analysis': '神态分析',
        'body_language': '肢体语言'
    };
    
    return displayNames[moduleName] || moduleName;
} 