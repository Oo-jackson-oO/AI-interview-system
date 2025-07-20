// 调试数据加载脚本
console.log('开始调试数据加载...');

// 模拟数据加载
async function debugDataLoading() {
    try {
        // 模拟三个JSON文件的数据
        const summaryData = {
            "section_evaluations": {
                "自我介绍": {
                    "score": 65,
                    "evaluation": "自我介绍内容简略，缺乏逻辑结构",
                    "suggestions": "建议采用STAR结构优化表达"
                },
                "简历深挖": {
                    "score": 60,
                    "evaluation": "面试者在简历深挖环节表现较差",
                    "suggestions": "应认真对待每个问题"
                },
                "岗位匹配度": {
                    "score": 0,
                    "evaluation": "面试者未提供有效回答",
                    "suggestions": "请确保回答内容与问题相关"
                },
                "反问环节": {
                    "score": 20,
                    "evaluation": "面试者在反问环节表现较差",
                    "suggestions": "应提前准备与岗位相关的高质量问题"
                }
            }
        };

        const facialData = {
            "performance_summary": {
                "微表情表现": {
                    "平均分": 4.5,
                    "表现评级": "较差"
                },
                "肢体动作表现": {
                    "平均分": 3.5,
                    "表现评级": "较差"
                }
            },
            "改进建议汇总": {
                "微表情建议": ["尝试放松面部表情"],
                "肢体动作建议": ["改善坐姿"]
            }
        };

        const analysisData = {
            "analysis_info": {
                "overall_score": 0.68
            },
            "fluency_analysis": {
                "fluency_level": "不流利"
            },
            "recommendations": {
                "speech_rate_advice": "建议调整语速",
                "fluency_advice": "流利度需要改善"
            }
        };

        console.log('原始数据:');
        console.log('summaryData:', summaryData);
        console.log('facialData:', facialData);
        console.log('analysisData:', analysisData);

        // 模拟数据合并逻辑
        const modules = {};
        
        // 从interview_summary_report.json获取数据
        if (summaryData && summaryData.section_evaluations) {
            // 个人介绍
            if (summaryData.section_evaluations['自我介绍']) {
                const data = summaryData.section_evaluations['自我介绍'];
                modules.self_introduction = {
                    score: data.score || 0,
                    evaluation: data.evaluation || '',
                    suggestions: data.suggestions || '',
                    active: true
                };
            }
            
            // 简历深挖
            if (summaryData.section_evaluations['简历深挖']) {
                const data = summaryData.section_evaluations['简历深挖'];
                modules.resume_digging = {
                    score: data.score || 0,
                    evaluation: data.evaluation || '',
                    suggestions: data.suggestions || '',
                    active: true
                };
            }
            
            // 岗位匹配
            if (summaryData.section_evaluations['岗位匹配度']) {
                const data = summaryData.section_evaluations['岗位匹配度'];
                modules.position_matching = {
                    score: data.score || 0,
                    evaluation: data.evaluation || '',
                    suggestions: data.suggestions || '',
                    active: true
                };
            }
            
            // 反问环节
            if (summaryData.section_evaluations['反问环节']) {
                const data = summaryData.section_evaluations['反问环节'];
                modules.reverse_question = {
                    score: data.score || 0,
                    evaluation: data.evaluation || '',
                    suggestions: data.suggestions || '',
                    active: true
                };
            }
            
            // 能力评估
            modules.ability_assessment = {
                score: Math.round((modules.self_introduction?.score || 0) * 0.8),
                evaluation: '基于自我介绍和简历深挖环节的综合评估',
                suggestions: '建议加强技术能力的展示和项目经验的详细描述',
                active: true
            };
            
            // 专业能力
            modules.professional_skills = {
                score: Math.round((modules.resume_digging?.score || 0) * 1.2),
                evaluation: '基于简历深挖环节的专业技能评估',
                suggestions: '建议深入学习相关技术栈，提升项目经验的展示质量',
                active: true
            };
        }
        
        // 从facial_analysis_report.json获取数据
        if (facialData && facialData.performance_summary) {
            // 神态分析
            const facialScore = facialData.performance_summary['微表情表现']?.平均分 || 0;
            modules.facial_analysis = {
                score: Math.round(facialScore * 10), // 转换为0-100分制
                evaluation: facialData.performance_summary['微表情表现']?.表现评级 || '一般',
                suggestions: facialData.改进建议汇总?.微表情建议?.join(' ') || '建议保持自然的面部表情',
                active: true
            };
            
            // 肢体语言
            const bodyScore = facialData.performance_summary['肢体动作表现']?.平均分 || 0;
            modules.body_language = {
                score: Math.round(bodyScore * 10), // 转换为0-100分制
                evaluation: facialData.performance_summary['肢体动作表现']?.表现评级 || '一般',
                suggestions: facialData.改进建议汇总?.肢体动作建议?.join(' ') || '建议改善坐姿和手势',
                active: true
            };
        }
        
        // 从analysis_result.json获取数据
        if (analysisData && analysisData.analysis_info) {
            // 语音语调
            const voiceScore = analysisData.analysis_info.overall_score || 0;
            modules.voice_tone = {
                score: Math.round(voiceScore * 100), // 转换为0-100分制
                evaluation: analysisData.fluency_analysis?.fluency_level || '一般',
                suggestions: analysisData.recommendations?.speech_rate_advice + ' ' + 
                            analysisData.recommendations?.fluency_advice || '建议改善语音语调',
                active: true
            };
        }

        console.log('合并后的模块数据:');
        console.log(modules);

        // 检查每个模块的状态
        Object.keys(modules).forEach(moduleKey => {
            const module = modules[moduleKey];
            console.log(`${moduleKey}: score=${module.score}, active=${module.active}, should_be_active=${module.active && module.score > 0}`);
        });

        // 计算总分
        const activeModules = Object.values(modules).filter(module => module.active && module.score > 0);
        const totalScore = activeModules.reduce((sum, module) => sum + module.score, 0);
        
        console.log('活跃模块数量:', activeModules.length);
        console.log('总分:', totalScore);

    } catch (error) {
        console.error('调试出错:', error);
    }
}

// 运行调试
debugDataLoading(); 