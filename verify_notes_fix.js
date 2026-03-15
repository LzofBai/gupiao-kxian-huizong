// 验证笔记显示修复的脚本
// 在浏览器控制台中运行此脚本进行验证

console.log('=== 笔记显示修复验证 ===');

// 1. 检查是否存在NotesManager对象
if (typeof NotesManager !== 'undefined') {
    console.log('✓ NotesManager 对象存在');
    
    // 2. 测试isContentEmpty方法
    const testCases = [
        { content: '<p>正常内容</p>', expected: false, desc: '正常文本内容' },
        { content: '<p><br></p>', expected: true, desc: '空段落' },
        { content: '', expected: true, desc: '空字符串' },
        { content: null, expected: true, desc: 'null值' },
        { content: '<p>\u00A0\u3000&nbsp;</p>', expected: true, desc: '只包含空白字符' },
        { content: '<p><strong>格式化内容</strong></p>', expected: false, desc: '带格式的内容' }
    ];
    
    console.log('\n--- 内容空值检测测试 ---');
    let passedTests = 0;
    testCases.forEach((testCase, index) => {
        try {
            const result = NotesManager.isContentEmpty(testCase.content);
            const passed = result === testCase.expected;
            console.log(`${passed ? '✓' : '✗'} 测试 ${index + 1}: ${testCase.desc}`);
            console.log(`   输入: ${JSON.stringify(testCase.content)}`);
            console.log(`   期望: ${testCase.expected}, 实际: ${result}`);
            if (passed) passedTests++;
        } catch (error) {
            console.log(`✗ 测试 ${index + 1}: ${testCase.desc} - 发生错误:`, error);
        }
    });
    
    console.log(`\n测试通过率: ${passedTests}/${testCases.length}`);
    
    // 3. 检查历史记录更新方法
    if (typeof NotesManager.updateHistoryList === 'function') {
        console.log('✓ updateHistoryList 方法存在');
        console.log('建议手动切换到"历史"标签页，观察笔记显示是否正常');
    } else {
        console.log('✗ updateHistoryList 方法不存在');
    }
    
} else {
    console.log('✗ NotesManager 对象不存在，请确保页面已完全加载');
}

console.log('\n=== 验证完成 ===');
console.log('如果仍有问题，请检查:');
console.log('1. 控制台是否有相关错误信息');
console.log('2. localStorage 中的笔记数据是否完整');
console.log('3. 网络请求是否正常');