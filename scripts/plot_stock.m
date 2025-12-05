function plot_stock(ticker, date_range)
% PLOT_STOCK 快速绘制指定股票的K线图
%
% 输入参数:
%   ticker      - 股票代码 (例如: 'AAPL', 'TSLA', 'GOOGL')
%   date_range  - (可选) 日期范围，格式: [开始日期, 结束日期]
%                 例如: [datetime(2024,1,1), datetime(2024,12,31)]
%                 如果不提供，则显示所有数据
%
% 示例:
%   plot_stock('AAPL')                     % 绘制苹果股票全部数据
%   plot_stock('TSLA')                     % 绘制特斯拉股票全部数据
%   plot_stock('AAPL', [datetime(2024,1,1), datetime(2024,12,31)])  % 指定日期范围
%   plot_stock('AAPL', [datetime(2025,1,1), datetime('today')])      % 2025年至今
%
% 说明:
%   此函数会自动查找 prices/<TICKER>.csv 文件并绘制K线图
%   如果指定了日期范围，会在绘图前筛选数据

    % 添加脚本路径
    addpath(fileparts(mfilename('fullpath')));

    % 构建数据文件路径
    data_file = fullfile('prices', [upper(ticker), '.csv']);

    % 检查文件是否存在
    if ~exist(data_file, 'file')
        error('数据文件不存在: %s\n请确保文件存在于 prices 目录下', data_file);
    end

    fprintf('正在读取 %s 的数据...\n', upper(ticker));

    % 如果提供了日期范围，需要先筛选数据
    if nargin > 1 && ~isempty(date_range)
        % 读取数据
        data = readtable(data_file);

        % 转换日期
        if iscell(data.date)
            dates = datetime(data.date, 'InputFormat', 'yyyy-MM-dd');
        elseif isdatetime(data.date)
            dates = data.date;
        else
            dates = datetime(data.date, 'ConvertFrom', 'datenum');
        end

        % 筛选日期范围
        if length(date_range) ~= 2
            error('日期范围必须包含两个日期: [开始日期, 结束日期]');
        end

        start_date = date_range(1);
        end_date = date_range(2);

        % 如果 end_date 是 'today'，转换为当前日期
        if ischar(end_date) && strcmpi(end_date, 'today')
            end_date = datetime('today');
        end

        % 筛选数据
        mask = (dates >= start_date) & (dates <= end_date);
        data = data(mask, :);

        fprintf('日期范围: %s 至 %s\n', datestr(start_date, 'yyyy-mm-dd'), datestr(end_date, 'yyyy-mm-dd'));
        fprintf('筛选后数据点: %d\n', height(data));

        if height(data) == 0
            error('指定日期范围内没有数据');
        end

        % 保存临时文件
        temp_file = tempname;
        temp_file = [temp_file, '.csv'];
        writetable(data, temp_file);

        % 绘制K线图
        plot_candlestick_chart(temp_file, upper(ticker));

        % 删除临时文件
        delete(temp_file);
    else
        % 直接绘制全部数据
        plot_candlestick_chart(data_file, upper(ticker));
    end

    fprintf('\n%s K线图绘制完成！\n', upper(ticker));
end
