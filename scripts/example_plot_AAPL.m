% 苹果股票K线图示例脚本
% 该脚本演示如何使用 plot_candlestick_chart 函数绘制K线图

% 清除工作空间和命令窗口
clear;
clc;
close all;

% 添加脚本路径
addpath(fileparts(mfilename('fullpath')));

fprintf('======================================\n');
fprintf('  苹果(AAPL)股票K线图示例\n');
fprintf('======================================\n\n');

% 设置数据文件路径
% 优先使用 prices/AAPL.csv，如果不存在则使用生成的示例数据
data_file = 'prices/AAPL.csv';
if ~exist(data_file, 'file')
    data_file = fullfile('data', 'prices', 'AAPL_with_indicators.csv');
    if ~exist(data_file, 'file')
        error('数据文件不存在: %s\n请确保 prices/AAPL.csv 文件存在', data_file);
    end
    fprintf('使用示例数据: %s\n', data_file);
else
    fprintf('使用真实数据: %s\n', data_file);
end

% 绘制K线图
fprintf('正在绘制K线图...\n\n');
plot_candlestick_chart(data_file, 'AAPL');

fprintf('\n======================================\n');
fprintf('  图表已生成！\n');
fprintf('======================================\n');
fprintf('\n提示: 你可以使用以下功能:\n');
fprintf('  - 缩放: 使用鼠标滚轮或工具栏的放大镜工具\n');
fprintf('  - 平移: 点击工具栏的手型工具，然后拖动图表\n');
fprintf('  - 保存: 点击 文件 > 另存为... 保存图表\n\n');
