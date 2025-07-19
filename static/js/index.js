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
        
        // 随机起始位置（主要在左右两侧）
        const side = Math.random() > 0.5 ? 'left' : 'right';
        let startX, startY;
        
        if (side === 'left') {
            startX = -50;
            startY = Math.random() * window.innerHeight * 0.8;
        } else {
            startX = window.innerWidth + 50;
            startY = Math.random() * window.innerHeight * 0.8;
        }
        
        // 随机结束位置
        const endX = startX + (Math.random() * 800 + 400) * (side === 'left' ? 1 : -1);
        const endY = startY + Math.random() * 400 + 200;
        
        meteor.style.left = startX + 'px';
        meteor.style.top = startY + 'px';
        
        // 随机大小和速度
        const size = Math.random() * 3 + 2;
        const duration = Math.random() * 2 + 1.5;
        
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
        
        meteor.style.animation = `${animationName} ${duration}s linear`;
        
        this.container.appendChild(meteor);
        this.meteors.push(meteor);
        
        // 动画结束后清理
        setTimeout(() => {
            meteor.remove();
            style.remove();
            this.meteors = this.meteors.filter(m => m !== meteor);
        }, duration * 1000);
    }
}

// 连接线系统
class ConnectorSystem {
    constructor() {
        this.svg = document.querySelector('.connectors');
        this.bubbles = [
            document.querySelector('.bubble-1-wrapper'),
            document.querySelector('.bubble-2-wrapper'),
            document.querySelector('.bubble-3-wrapper')
        ];
        this.init();
    }

    init() {
        this.updateConnectors();
        window.addEventListener('resize', () => this.updateConnectors());
    }

    updateConnectors() {
        // 保留defs，清空其他元素
        const defs = this.svg.querySelector('defs');
        this.svg.innerHTML = '';
        if (defs) this.svg.appendChild(defs);
        
        // 连接泡泡1和泡泡2
        if (this.bubbles[0] && this.bubbles[1]) {
            this.createConnector(this.bubbles[0], this.bubbles[1]);
        }
        
        // 连接泡泡2和泡泡3
        if (this.bubbles[1] && this.bubbles[2]) {
            this.createConnector(this.bubbles[1], this.bubbles[2]);
        }
    }

    createConnector(bubble1, bubble2) {
        const rect1 = bubble1.getBoundingClientRect();
        const rect2 = bubble2.getBoundingClientRect();
        const containerRect = this.svg.getBoundingClientRect();
        
        const x1 = rect1.left + rect1.width/2 - containerRect.left;
        const y1 = rect1.top + rect1.height/2 - containerRect.top;
        const x2 = rect2.left + rect2.width/2 - containerRect.left;
        const y2 = rect2.top + rect2.height/2 - containerRect.top;
        
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('class', 'connector-line');
        line.setAttribute('x1', x1);
        line.setAttribute('y1', y1);
        line.setAttribute('x2', x2);
        line.setAttribute('y2', y2);
        line.setAttribute('marker-end', 'url(#arrowhead)');
        
        this.svg.appendChild(line);
    }
}

// 高级泡泡交互系统
class AdvancedBubbleInteractionSystem {
    constructor() {
        this.bubbles = document.querySelectorAll('.bubble');
        this.cards = document.querySelectorAll('.bubble-card');
        this.init();
    }

    init() {
        this.bubbles.forEach(bubble => {
            this.addBubbleEffects(bubble);
        });
        
        this.cards.forEach(card => {
            this.addCardEffects(card);
        });
    }

    addBubbleEffects(bubble) {
        let animationId;
        let isHovering = false;
        
        bubble.addEventListener('mouseenter', () => {
            isHovering = true;
            
            // 停止之前的动画
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
            
            // 开始增强的浮动动画
            let startTime = Date.now();
            const floatBubble = () => {
                if (!isHovering) return;
                
                const elapsed = Date.now() - startTime;
                const amplitude = 15;
                const speed = 1500;
                const y = Math.sin(elapsed / speed) * amplitude;
                const x = Math.sin(elapsed / (speed * 2)) * 3;
                
                bubble.style.transform = `scale(1.1) translate(${x}px, ${y - 10}px)`;
                
                if (isHovering) {
                    animationId = requestAnimationFrame(floatBubble);
                }
            };
            
            floatBubble();
        });
        
        bubble.addEventListener('mouseleave', () => {
            isHovering = false;
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
            bubble.style.transform = 'scale(1)';
        });
        
        // 添加点击波纹效果
        bubble.addEventListener('click', (e) => {
            this.createRippleEffect(e, bubble);
        });
        
        // 添加轻微的持续浮动效果
        this.addGentleFloat(bubble);
    }

    addCardEffects(card) {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.transition = 'all 0.3s ease';
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
        });
    }

    addGentleFloat(bubble) {
        let floatId;
        let startTime = Date.now();
        
        const gentleFloat = () => {
            const elapsed = Date.now() - startTime;
            const amplitude = 3;
            const speed = 3000;
            const y = Math.sin(elapsed / speed) * amplitude;
            
            if (!bubble.matches(':hover')) {
                bubble.style.transform = `translateY(${y}px)`;
            }
            
            floatId = requestAnimationFrame(gentleFloat);
        };
        
        floatId = requestAnimationFrame(gentleFloat);
        
        const observer = new MutationObserver(() => {
            if (!document.contains(bubble)) {
                cancelAnimationFrame(floatId);
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    createRippleEffect(event, bubble) {
        const ripple = document.createElement('div');
        ripple.className = 'ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(102, 126, 234, 0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
            z-index: 10;
        `;
        
        const rect = bubble.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = size + 'px';
        ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        
        const style = document.createElement('style');
        style.innerHTML = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
        
        bubble.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
            style.remove();
        }, 600);
    }
}



// 火箭鼠标系统
class RocketCursorSystem {
    constructor() {
        this.rocket = document.getElementById('rocketCursor');
        this.isVisible = false;
        this.lastWaveTime = 0;
        this.init();
    }

    init() {
        this.addEventListeners();
        this.startWaveTimer();
    }

    addEventListeners() {
        // 鼠标移动事件
        document.addEventListener('mousemove', (e) => {
            if (this.rocket) {
                this.rocket.style.left = e.clientX + 'px';
                this.rocket.style.top = e.clientY + 'px';
                
                // 添加轻微的倾斜效果
                const tiltX = (e.clientX - window.innerWidth / 2) / window.innerWidth * 5;
                this.rocket.style.transform = `translate(-50%, -50%) rotate(${tiltX}deg)`;
            }
        });

        // 鼠标进入页面
        document.addEventListener('mouseenter', () => {
            this.isVisible = true;
            if (this.rocket) {
                this.rocket.style.opacity = '1';
            }
        });

        // 鼠标离开页面
        document.addEventListener('mouseleave', () => {
            this.isVisible = false;
            if (this.rocket) {
                this.rocket.style.opacity = '0';
            }
        });

        // 点击事件 - 添加点击波动效果
        document.addEventListener('click', (e) => {
            this.createWave(e.clientX, e.clientY);
        });
    }

    startWaveTimer() {
        // 每5秒自动发出波动
        setInterval(() => {
            if (this.isVisible) {
                const x = parseFloat(this.rocket.style.left) || window.innerWidth / 2;
                const y = parseFloat(this.rocket.style.top) || window.innerHeight / 2;
                this.createWave(x, y);
            }
        }, 5000);
    }

    createWave(x, y) {
        const wave = document.createElement('div');
        wave.className = 'rocket-wave';
        wave.style.left = x + 'px';
        wave.style.top = y + 'px';
        
        document.body.appendChild(wave);
        
        // 动画结束后移除元素
        setTimeout(() => {
            if (wave.parentNode) {
                wave.parentNode.removeChild(wave);
            }
        }, 2000);
    }
}

// 高级加载系统
class LoadingSystem {
    constructor() {
        this.overlay = document.getElementById('loadingOverlay');
        this.init();
    }

    init() {
        // 模拟加载过程
        setTimeout(() => {
            this.hideLoading();
        }, 2000);
    }

    hideLoading() {
        this.overlay.style.opacity = '0';
        setTimeout(() => {
            this.overlay.style.display = 'none';
        }, 500);
    }
}

// 导航栏切换系统
class NavigationToggleSystem {
    constructor() {
        this.navToggleBtn = document.getElementById('navToggleBtn');
        this.sidebarNav = document.getElementById('sidebarNav');
        this.mainContainer = document.querySelector('.main-container');
        this.isNavOpen = false;
        this.init();
    }

    init() {
        this.addEventListeners();
    }

    addEventListeners() {
        // 点击导航栏切换按钮
        this.navToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleNav();
        });

        // 点击右侧空白处收起导航栏
        document.addEventListener('click', (e) => {
            if (this.isNavOpen && !this.sidebarNav.contains(e.target) && !this.navToggleBtn.contains(e.target)) {
                this.closeNav();
            }
        });

        // 阻止导航栏内部点击事件冒泡
        this.sidebarNav.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    toggleNav() {
        if (this.isNavOpen) {
            this.closeNav();
        } else {
            this.openNav();
        }
    }

    openNav() {
        this.isNavOpen = true;
        this.sidebarNav.classList.add('active');
        this.mainContainer.classList.add('nav-open');
        this.navToggleBtn.classList.add('active');
    }

    closeNav() {
        this.isNavOpen = false;
        this.sidebarNav.classList.remove('active');
        this.mainContainer.classList.remove('nav-open');
        this.navToggleBtn.classList.remove('active');
    }
}

// 黑洞转场系统
class BlackholeTransitionSystem {
    constructor() {
        this.blackholeTransition = document.getElementById('blackholeTransition');
        this.blackholeCircle = this.blackholeTransition.querySelector('.blackhole-circle');
        this.mainContainer = document.querySelector('.main-container');
        this.init();
    }

    init() {
        // 检查是否是从其他页面返回
        this.checkReturnFromOtherPage();
        // 主页离开转场
        this.setupLeaveTransition();
    }

    checkReturnFromOtherPage() {
        // 检查URL参数或sessionStorage来判断是否从其他页面返回
        const isReturning = sessionStorage.getItem('returningToHome');
        if (isReturning) {
            sessionStorage.removeItem('returningToHome');
            this.playReturnAnimation();
        }
    }

    playReturnAnimation() {
        // 首先隐藏主页内容
        this.mainContainer.classList.add('fade-out');
        
        // 激活黑洞转场，从四周到中心扩散黑色
        this.blackholeTransition.classList.add('active', 'enter');
        
        // 等待黑色扩散完成
        setTimeout(() => {
            this.blackholeTransition.classList.remove('enter');
            
            // 启动流光动画，绕中心旋转
            this.startStreamAnimation();
            
            // 等待流光效果播放
            setTimeout(() => {
                // 从中心向外褪去黑色，同时流光继续旋转
                this.blackholeTransition.classList.add('exit');
                
                // 等待黑色褪去完成
                setTimeout(() => {
                    this.blackholeTransition.classList.remove('active', 'exit');
                    
                    // 主页内容淡入
                    this.mainContainer.classList.remove('fade-out');
                    this.mainContainer.classList.add('fade-in');
                    
                    // 移除淡入类
                    setTimeout(() => {
                        this.mainContainer.classList.remove('fade-in');
                    }, 1000);
                }, 1200); // 黑色褪去时间
            }, 4000); // 流光效果持续4秒
        }, 1200); // 黑色扩散时间
    }

    startStreamAnimation() {
        // 确保粒子动画在黑洞转场期间播放，绕中心旋转并靠近泡泡
        const particles = this.blackholeTransition.querySelectorAll('.particle');
        particles.forEach((particle, index) => {
            particle.style.animation = `particleOrbit 8s linear infinite`;
            particle.style.animationDelay = `${index * 0.2}s`;
        });
    }

    // 离开主页时的黑洞转场动画
    playLeaveAnimation(targetUrl) {
        // 主页内容淡出
        this.mainContainer.classList.add('fade-out');
        // 激活黑洞转场，中心黑洞扩散到全屏
        this.blackholeTransition.classList.add('active', 'enter');
        setTimeout(() => {
            this.blackholeTransition.classList.remove('enter');
            this.startStreamAnimation();
            setTimeout(() => {
                // 跳转到目标页面
                window.location.href = targetUrl;
            }, 1200); // 黑色扩散后直接跳转
        }, 1200);
    }

    setupLeaveTransition() {
        // 注意：这个函数现在由主页模板中的checkLoginAndNavigate函数处理
        // 不再在这里拦截点击事件，因为需要先检查登录状态
    }

    // 为其他页面提供转场方法
    static triggerReturnTransition() {
        sessionStorage.setItem('returningToHome', 'true');
    }
}

// 页面加载完成后初始化所有系统
document.addEventListener('DOMContentLoaded', function() {
    // 初始化火箭鼠标系统
    new RocketCursorSystem();
    
    // 初始化高级粒子系统
    new ParticleSystem();
    
    // 初始化星光系统
    new StarSystem();
    
    // 初始化流星系统
    new MeteorSystem();
    
    // 初始化连接线系统
    new ConnectorSystem();
    
    // 初始化高级泡泡交互系统
    new AdvancedBubbleInteractionSystem();
    
    // 初始化加载系统
    new LoadingSystem();
    
    // 初始化导航栏切换系统
    new NavigationToggleSystem();
    
    // 初始化黑洞转场系统
    new BlackholeTransitionSystem();
    
    // 添加页面加载动画
    const bubbles = document.querySelectorAll('.bubble-wrapper');
    bubbles.forEach((bubble, index) => {
        bubble.style.opacity = '0';
        bubble.style.transform = 'translateY(50px) scale(0.8)';
        
        setTimeout(() => {
            bubble.style.transition = 'all 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            bubble.style.opacity = '1';
            bubble.style.transform = 'translateY(0) scale(1)';
        }, index * 200);
    });
    
    // 标题加载动画
    const title = document.querySelector('.title');
    const subtitle = document.querySelector('.subtitle');
    title.style.opacity = '0';
    title.style.transform = 'translateY(-30px)';
    subtitle.style.opacity = '0';
    subtitle.style.transform = 'translateY(-20px)';
    
    setTimeout(() => {
        title.style.transition = 'all 1s ease-out';
        title.style.opacity = '1';
        title.style.transform = 'translateY(0)';
        
        setTimeout(() => {
            subtitle.style.transition = 'all 0.8s ease-out';
            subtitle.style.opacity = '1';
            subtitle.style.transform = 'translateY(0)';
        }, 200);
    }, 500);
    
    // 导航项动画
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            item.style.transition = 'all 0.6s ease-out';
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, 1000 + index * 100);
    });
});

// 添加键盘导航支持
document.addEventListener('keydown', function(e) {
    const bubbles = document.querySelectorAll('.bubble');
    
    switch(e.key) {
        case '1':
            bubbles[0]?.click();
            break;
        case '2':
            bubbles[1]?.click();
            break;
        case '3':
            bubbles[2]?.click();
            break;
    }
});

