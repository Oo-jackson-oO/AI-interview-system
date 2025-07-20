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
let currentCenter = 4; // 当前中心模块索引（默认第4个模块在中心）
const totalModules = 9; // 总共9个模块
let moduleData = {};
let isAnimating = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('面试结果页面初始化开始...');
    
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
        
        // 加载三个JSON文件
        const [summaryData, facialData, voiceData] = await Promise.all([
            loadJSONFile(`/uploads/${username}/interview_summary_report.json`),
            loadJSONFile(`/uploads/${username}/facial_analysis_report.json`),
            loadJSONFile(`/uploads/${username}/analysis_result.json`)
        ]);
        
        console.log('JSON文件加载完成:', { summaryData, facialData, voiceData });
        
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
        document.getElementById('totalEvaluation').textContent = '数据加载失败，请检查网络连接';
    }
}

// 获取当前用户名
function getCurrentUsername() {
    // 这里需要根据实际的用户认证系统获取用户名
    // 暂时返回一个测试用户名
    return 'alivin';
}

// 加载JSON文件
async function loadJSONFile(url) {
    try {
        const response = await fetch(url);
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
            mergedData.voice_tone = {
                score: normalizeScore(data.overall_score || 0, 5),
                maxScore: 5,
                evaluation: voiceData.fluency_analysis?.fluency_level || '暂无评价',
                suggestions: voiceData.recommendations?.speech_rate_advice + ' ' + 
                           voiceData.recommendations?.fluency_advice || '建议改善语音语调'
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
        
        if (scoreElement && data) {
            // 动画更新分数
            animateScore(scoreElement, 0, data.score);
            
            // 更新模块状态
            if (planetElement) {
                if (data.score > 0) {
                    planetElement.classList.add('active');
                    planetElement.classList.remove('inactive');
                } else {
                    planetElement.classList.add('inactive');
                    planetElement.classList.remove('active');
                }
            }
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