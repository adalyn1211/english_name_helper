// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function() {
    console.log("页面加载完成，准备就绪！");
    
    const form = document.getElementById('name-form');
    const resultContainer = document.getElementById('result-container');
    const suggestionsContainer = document.getElementById('suggestions');
    const loadingIndicator = document.getElementById('loading');
    
    // 处理文本内容，确保正确解析Unicode和换行符
    function processContent(content) {
        try {
            // 解码可能的Unicode编码
            let decodedContent = content;
            try {
                decodedContent = JSON.parse(`"${content.replace(/"/g, '\\"')}"`);
            } catch (e) {
                console.log("Unicode解码失败，使用原始内容");
            }
            
            // 处理各种可能的换行符格式
            return decodedContent.replace(/\\n\\n|\\n|\n\n|\n/g, '\n').split('\n');
        } catch (e) {
            console.error("内容处理错误:", e);
            return [content];
        }
    }
    
    // 创建名字卡片
    function createNameCard(nameInfo) {
        const template = document.getElementById('name-card-template');
        const card = template.content.cloneNode(true);
        
        // 设置名字
        card.querySelector('.name-title').textContent = nameInfo.name;
        
        // 设置音标和发音指导
        const phoneticDiv = card.querySelector('.phonetic');
        const guideDiv = card.querySelector('.guide-steps');
        
        // 格式化音标显示
        if (nameInfo.phonetic) {
            phoneticDiv.textContent = nameInfo.phonetic;
        }
        
        // 格式化发音指导（限制在50字符内）
        if (nameInfo.pronunciation) {
            guideDiv.textContent = nameInfo.pronunciation.length > 50 
                ? nameInfo.pronunciation.substring(0, 47) + '...' 
                : nameInfo.pronunciation;
        }
        
        // 设置名字解释
        const meaningP = card.querySelector('.name-meaning p');
        if (nameInfo.explanation) {
            // 首先按照换行符分段
            const paragraphs = nameInfo.explanation.split(/\n\s*\n/).map(p => p.trim());
            
            // 如果没有明确的换行符，尝试通过内容特征分段
            if (paragraphs.length === 1) {
                const text = paragraphs[0];
                // 寻找第二段的开始位置（通常包含"呼应"、"寓意"等关键词）
                const matches = text.match(/([^。！？]+[。！？])\s*([^。！？]*(?:呼应|寓意|契合|对应|象征)[^。！？]*[。！？].*)/);
                
                if (matches) {
                    // 找到了自然分段点
                    paragraphs[0] = matches[1].trim();
                    paragraphs[1] = matches[2].trim();
                } else {
                    // 没有找到自然分段点，尝试在句子中间分段
                    const sentences = text.split(/(?<=[。！？])\s*/);
                    const midPoint = Math.ceil(sentences.length / 2);
                    paragraphs[0] = sentences.slice(0, midPoint).join('').trim();
                    paragraphs[1] = sentences.slice(midPoint).join('').trim();
                }
            }
            
            // 确保每段都以标点符号结尾，且第一段前面没有空格
            const formattedParagraphs = paragraphs.map((p, index) => {
                p = p.trim();
                if (!/[。！？]$/.test(p)) {
                    p += '。';
                }
                return p;
            });
            
            // 使用双换行符连接段落，确保第一段前面没有空格和换行
            meaningP.innerHTML = formattedParagraphs.join('<br><br>');
            meaningP.style.textIndent = '0'; // 移除首行缩进
        }
        
        // 添加发音功能
        const pronounceBtn = card.querySelector('.pronounce-btn');
        pronounceBtn.addEventListener('click', function() {
            const guide = this.closest('.name-card').querySelector('.pronunciation-guide');
            guide.classList.toggle('hidden');
            
            // 朗读名字
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(nameInfo.name);
                utterance.lang = 'en-US';
                utterance.rate = 0.8;
                window.speechSynthesis.speak(utterance);
            }
        });
        
        return card;
    }
    
    // 切换发音指导显示
    function togglePronunciation(button) {
        const card = button.closest('.name-card');
        const guide = card.querySelector('.pronunciation-guide');
        guide.classList.toggle('hidden');
    }
    
    // 解析名字信息
    function parseNameInfo(text) {
        console.log("解析文本:", text);
        const names = [];
        let currentName = null;
        
        // 将文本按名字分块
        const nameBlocks = text.split(/\n\s*-\s*/).filter(block => block.trim());
        
        nameBlocks.forEach(block => {
            const lines = block.split('\n').map(line => line.trim()).filter(line => line);
            if (lines.length === 0) return;
            
            // 第一行是名字
            const name = lines[0];
            if (!name) return;
            
            currentName = {
                name: name,
                phonetic: '',
                pronunciation: '',
                explanation: ''
            };
            
            // 处理剩余的行
            let isExplanation = false;
            
            lines.slice(1).forEach(line => {
                // 清理行内容
                line = line.trim();
                if (!line) return;
                
                // 检测音标
                if (line.includes('/') || line.includes('[音标]')) {
                    // 提取音标内容
                    const phoneticMatch = line.match(/\/[^/]+\//);
                    if (phoneticMatch) {
                        currentName.phonetic = phoneticMatch[0];
                    } else {
                        // 尝试其他格式的音标
                        const altPhoneticMatch = line.replace(/[\[\]音标]/g, '').trim();
                        if (altPhoneticMatch) {
                            currentName.phonetic = altPhoneticMatch;
                        }
                    }
                }
                // 检测发音指导
                else if (line.includes('[发音指导]') || line.includes('读作') || line.includes('发音')) {
                    let pronGuide = line.replace(/[\[\]发音指导]/g, '').trim();
                    // 如果发音指导中包含音标，提取出实际的发音指导部分
                    const phoneticInGuide = pronGuide.match(/\/[^/]+\//);
                    if (phoneticInGuide) {
                        if (!currentName.phonetic) {
                            currentName.phonetic = phoneticInGuide[0];
                        }
                        pronGuide = pronGuide.replace(/\/[^/]+\//, '').trim();
                    }
                    currentName.pronunciation = pronGuide;
                }
                // 其他内容作为解释
                else if (!line.startsWith('[')) {
                    if (currentName.explanation) {
                        currentName.explanation += ' ' + line;
                    } else {
                        currentName.explanation = line;
                    }
                }
            });
            
            // 确保所有必要的信息都存在
            if (!currentName.phonetic) {
                currentName.phonetic = `/${currentName.name.toLowerCase()}/`;
            }
            if (!currentName.pronunciation) {
                currentName.pronunciation = `请读作"${currentName.name}"`;
            }
            
            // 清理并格式化内容
            currentName.explanation = currentName.explanation.replace(/\s+/g, ' ').trim();
            currentName.pronunciation = currentName.pronunciation.replace(/\s+/g, ' ').trim();
            
            names.push(currentName);
        });
        
        console.log("解析结果:", names);
        return names;
    }
    
    // 显示名字建议
    function displaySuggestions(container, suggestions) {
        // 清空容器
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
        
        // 解析API返回的文本
        const names = parseNameInfo(suggestions);
        
        // 创建名字卡片
        names.forEach(nameInfo => {
            const card = createNameCard(nameInfo);
            if (card) {
                container.appendChild(card);
            }
        });
    }
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const chineseName = document.getElementById('chinese-name').value.trim();
        const gender = document.querySelector('input[name="gender"]:checked').value;
        
        if (!chineseName) {
            alert('请输入中文名字');
            return;
        }
        
        // 显示加载指示器
        loadingIndicator.style.display = 'block';
        resultContainer.style.display = 'none';
        
        console.log("=== 开始生成名字 ===");
        console.log("用户输入的名字:", chineseName);
        console.log("用户选择的性别:", gender);
        
        // 发送请求到后端
        fetch('/api/suggest_names', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chinese_name: chineseName,
                gender: gender
            })
        })
        .then(response => {
            console.log("=== 收到后端响应 ===");
            console.log("响应状态码:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("=== 解析后的响应数据 ===");
            console.log(data);
            
            // 隐藏加载指示器
            loadingIndicator.style.display = 'none';
            resultContainer.style.display = 'block';
            
            if (data.error) {
                const errorP = document.createElement('p');
                errorP.className = 'error';
                errorP.textContent = `错误: ${data.error}`;
                suggestionsContainer.innerHTML = '';
                suggestionsContainer.appendChild(errorP);
                return;
            }
            
            // 处理并显示内容
            const content = processContent(data.suggestions).join('\n');
            displaySuggestions(suggestionsContainer, content);
            console.log("=== 显示结果 ===");
        })
        .catch(error => {
            console.error('错误:', error);
            loadingIndicator.style.display = 'none';
            resultContainer.style.display = 'block';
            const errorP = document.createElement('p');
            errorP.className = 'error';
            errorP.textContent = `发生错误: ${error.message}`;
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.appendChild(errorP);
        });
    });
});
