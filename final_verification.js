// 最终验证脚本 - 用于确认笔记显示修复是否成功
// 在浏览器控制台中运行

(function() {
    console.log('=== 📝 每日看盘笔记显示修复最终验证 ===');
    
    // 1. 基础环境检查
    console.group('🔧 基础环境检查');
    
    const checks = {
        'localStorage支持': typeof Storage !== "undefined",
        'NotesManager存在': typeof NotesManager !== "undefined",
        'updateHistoryList方法': typeof NotesManager !== "undefined" && typeof NotesManager.updateHistoryList === "function",
        'isContentEmpty方法': typeof NotesManager !== "undefined" && typeof NotesManager.isContentEmpty === "function"
    };
    
    let allPassed = true;
    Object.entries(checks).forEach(([name, result]) => {
        const status = result ? '✅' : '❌';
        console.log(`${status} ${name}: ${result}`);
        if (!result) allPassed = false;
    });
    
    console.groupEnd();
    
    if (!allPassed) {
        console.error('❌ 基础环境检查失败，请刷新页面重试');
        return;
    }
    
    // 2. 功能测试
    console.group('🧪 功能测试');
    
    // 测试内容检测逻辑
    const testCases = [
        { content: '<p>正常内容测试</p>', expected: false, desc: '正常文本' },
        { content: '<p><br></p>', expected: true, desc: '空段落' },
        { content: '', expected: true, desc: '空字符串' },
        { content: '<p>\u00A0\u3000&nbsp;</p>', expected: true, desc: '空白字符' },
        { content: '<p><strong>格式化</strong>内容</p>', expected: false, desc: '格式化内容' },
        { content: '<div><p>多层嵌套</p><p>内容测试</p></div>', expected: false, desc: '多层HTML' }
    ];
    
    let passedTests = 0;
    testCases.forEach((testCase, index) => {
        try {
            const result = NotesManager.isContentEmpty(testCase.content);
            const passed = result === testCase.expected;
            const status = passed ? '✅' : '❌';
            console.log(`${status} 测试${index + 1} ${testCase.desc}: 期望${testCase.expected}, 实际${result}`);
            if (passed) passedTests++;
        } catch (error) {
            console.log(`❌ 测试${index + 1} ${testCase.desc}: 错误 - ${error.message}`);
        }
    });
    
    console.log(`测试通过率: ${passedTests}/${testCases.length}`);
    console.groupEnd();
    
    // 3. 实际数据检查
    console.group('🔍 实际数据检查');
    
    try {
        const indexKey = 'fund_notes_index_v2';
        const indexData = localStorage.getItem(indexKey);
        
        if (!indexData) {
            console.warn('⚠️ 未找到笔记索引数据');
        } else {
            const index = JSON.parse(indexData);
            console.log(`📝 找到 ${index.length} 条笔记记录`);
            
            index.forEach((note, i) => {
                console.log(`\n--- 笔记 ${i + 1} ---`);
                console.log('ID:', note.id);
                console.log('日期:', note.date);
                console.log('创建时间:', new Date(note.createTime).toLocaleString());
                
                // 检查实际内容
                const storageKey = `fund_notes_entry_${note.id}`;
                const storedContent = localStorage.getItem(storageKey);
                if (storedContent) {
                    try {
                        const noteData = JSON.parse(storedContent);
                        const isEmpty = NotesManager.isContentEmpty(noteData.content);
                        const preview = noteData.content ? noteData.content.replace(/<[^>]*>/g, '').substring(0, 30) : '';
                        console.log('内容状态:', isEmpty ? '空' : '有内容');
                        console.log('内容预览:', preview || '(无内容)');
                    } catch (e) {
                        console.error('解析笔记内容失败:', e);
                    }
                } else {
                    console.warn('⚠️ 未找到对应的内容数据');
                }
            });
        }
    } catch (error) {
        console.error('数据检查出错:', error);
    }
    
    console.groupEnd();
    
    // 4. 执行历史记录更新测试
    console.group('🔄 历史记录更新测试');
    
    try {
        console.log('调用 updateHistoryList 方法...');
        NotesManager.updateHistoryList();
        console.log('✅ updateHistoryList 执行完成');
        
        // 检查DOM更新结果
        setTimeout(() => {
            const historyList = document.getElementById('historyList');
            if (historyList) {
                const items = historyList.querySelectorAll('.history-item');
                console.log(`.DOM中找到 ${items.length} 个历史记录项`);
                
                items.forEach((item, i) => {
                    const contentDiv = item.querySelector('.history-content');
                    if (contentDiv) {
                        const content = contentDiv.innerHTML;
                        const isPlaceholder = content.includes('（空笔记）');
                        const status = isPlaceholder ? '空笔记占位符' : '有内容';
                        console.log(`  项目 ${i + 1}: ${status}`);
                    }
                });
            }
        }, 100);
        
    } catch (error) {
        console.error('执行历史记录更新时出错:', error);
    }
    
    console.groupEnd();
    
    // 5. 提供交互式测试工具
    console.group('🛠️ 交互式测试工具');
    
    window.DiagnosticTools = {
        // 强制刷新历史显示
        refreshHistory: function() {
            console.log('强制刷新历史记录显示...');
            NotesManager.updateHistoryList();
        },
        
        // 查看详细笔记数据
        showNoteDetails: function() {
            const indexKey = 'fund_notes_index_v2';
            const indexData = localStorage.getItem(indexKey);
            if (indexData) {
                const index = JSON.parse(indexData);
                console.table(index.map(note => ({
                    ID: note.id,
                    日期: note.date,
                    创建时间: new Date(note.createTime).toLocaleString(),
                    内容长度: note.content ? note.content.length : 0
                })));
            }
        },
        
        // 创建测试笔记
        createTestNote: function() {
            const noteId = 'debug_test_' + Date.now();
            const today = new Date().toISOString().split('T')[0];
            
            const testNote = {
                id: noteId,
                date: today,
                content: '<p>这是调试测试笔记，创建于 ' + new Date().toLocaleString() + '</p>',
                createTime: Date.now(),
                updateTime: Date.now()
            };
            
            localStorage.setItem(`fund_notes_entry_${noteId}`, JSON.stringify(testNote));
            
            const index = NotesManager.getNotesIndex();
            index.push(testNote);
            NotesManager.saveNotesIndex(index);
            
            console.log('✅ 已创建测试笔记:', noteId);
            this.refreshHistory();
        },
        
        // 清理测试数据
        cleanupTestNotes: function() {
            const index = NotesManager.getNotesIndex();
            const filteredIndex = index.filter(note => !note.id.startsWith('debug_test_'));
            NotesManager.saveNotesIndex(filteredIndex);
            
            // 清理localStorage中的测试笔记
            Object.keys(localStorage).forEach(key => {
                if (key.includes('debug_test_')) {
                    localStorage.removeItem(key);
                }
            });
            
            console.log('✅ 已清理测试笔记');
            this.refreshHistory();
        }
    };
    
    console.log('可用的调试工具:');
    console.log('- DiagnosticTools.refreshHistory()  // 刷新历史显示');
    console.log('- DiagnosticTools.showNoteDetails() // 显示笔记详情');
    console.log('- DiagnosticTools.createTestNote()   // 创建测试笔记');
    console.log('- DiagnosticTools.cleanupTestNotes()  // 清理测试笔记');
    
    console.groupEnd();
    
    console.log('\n=== 🎯 验证完成 ===');
    console.log('如仍有问题，请:');
    console.log('1. 检查控制台是否有错误信息');
    console.log('2. 使用上述调试工具进行进一步测试');
    console.log('3. 尝试手动切换到"历史"标签页观察效果');
    
})();