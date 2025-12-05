function plot_candlestick_chart(csv_file, ticker)
% PLOT_CANDLESTICK_CHART 绘制股票K线图及技术指标
%
% 输入参数:
%   csv_file - CSV数据文件路径
%   ticker   - 股票代码 (例如: 'AAPL')
%
% 示例:
%   plot_candlestick_chart('data/prices/AAPL_with_indicators.csv', 'AAPL')

    % 读取CSV数据
    fprintf('正在读取数据文件: %s\n', csv_file);
    data = readtable(csv_file);

    % 如果指定了ticker，筛选对应的数据
    if nargin > 1 && ~isempty(ticker)
        if ismember('tic', data.Properties.VariableNames)
            data = data(strcmp(data.tic, ticker), :);
        end
    end

    % 检查数据是否为空
    if isempty(data)
        error('没有找到股票 %s 的数据', ticker);
    end

    % 转换日期格式
    if iscell(data.date)
        dates = datetime(data.date, 'InputFormat', 'yyyy-MM-dd');
    elseif isdatetime(data.date)
        dates = data.date;
    else
        dates = datetime(data.date, 'ConvertFrom', 'datenum');
    end

    % 提取OHLCV数据
    open_prices = data.open;
    high_prices = data.high;
    low_prices = data.low;
    close_prices = data.close;
    volume = data.volume;

    % 创建图形窗口
    fig = figure('Position', [100, 100, 1400, 900], 'Color', 'w');
    fig.Name = sprintf('%s 股票K线图及技术指标', ticker);

    % ==================== 子图1: K线图 + 均线 ====================
    ax1 = subplot(4, 1, 1);
    hold on;

    % 绘制K线图
    plot_candles(ax1, dates, open_prices, high_prices, low_prices, close_prices);

    % 添加移动平均线
    if ismember('ema_5', data.Properties.VariableNames)
        plot(dates, data.ema_5, 'Color', [0.2, 0.6, 1], 'LineWidth', 1.5, 'DisplayName', 'EMA 5');
    end
    if ismember('ema_20', data.Properties.VariableNames)
        plot(dates, data.ema_20, 'Color', [1, 0.5, 0], 'LineWidth', 1.5, 'DisplayName', 'EMA 20');
    end
    if ismember('ema_50', data.Properties.VariableNames)
        plot(dates, data.ema_50, 'Color', [0.5, 0, 0.8], 'LineWidth', 1.5, 'DisplayName', 'EMA 50');
    end

    % 添加布林带
    if ismember('bb_upper_20', data.Properties.VariableNames) && ...
       ismember('bb_lower_20', data.Properties.VariableNames)
        plot(dates, data.bb_upper_20, '--', 'Color', [0.7, 0.7, 0.7], 'LineWidth', 1, 'DisplayName', 'BB Upper');
        plot(dates, data.bb_lower_20, '--', 'Color', [0.7, 0.7, 0.7], 'LineWidth', 1, 'DisplayName', 'BB Lower');

        % 填充布林带区域
        x_fill = [dates; flipud(dates)];
        y_fill = [data.bb_upper_20; flipud(data.bb_lower_20)];
        fill(x_fill, y_fill, [0.9, 0.9, 0.9], 'FaceAlpha', 0.3, 'EdgeColor', 'none', 'DisplayName', 'BB Band');
    end

    ylabel('价格 (USD)', 'FontSize', 11, 'FontWeight', 'bold');
    title(sprintf('%s 股票K线图', ticker), 'FontSize', 14, 'FontWeight', 'bold');
    legend('Location', 'northwest', 'FontSize', 9);
    grid on;
    set(ax1, 'XTickLabel', []);

    % ==================== 子图2: MACD ====================
    ax2 = subplot(4, 1, 2);
    hold on;

    if ismember('macd', data.Properties.VariableNames) && ...
       ismember('macds', data.Properties.VariableNames) && ...
       ismember('macdh', data.Properties.VariableNames)

        % 绘制MACD柱状图
        macd_hist = data.macdh;
        pos_idx = macd_hist >= 0;
        neg_idx = macd_hist < 0;

        bar(dates(pos_idx), macd_hist(pos_idx), 'FaceColor', [0.2, 0.8, 0.2], 'EdgeColor', 'none', 'DisplayName', 'MACD Hist+');
        bar(dates(neg_idx), macd_hist(neg_idx), 'FaceColor', [0.8, 0.2, 0.2], 'EdgeColor', 'none', 'DisplayName', 'MACD Hist-');

        % 绘制MACD线和信号线
        plot(dates, data.macd, 'Color', [0, 0.4, 0.8], 'LineWidth', 1.5, 'DisplayName', 'MACD');
        plot(dates, data.macds, 'Color', [0.8, 0.4, 0], 'LineWidth', 1.5, 'DisplayName', 'Signal');

        % 添加零线
        plot(dates([1, end]), [0, 0], 'k--', 'LineWidth', 0.5, 'HandleVisibility', 'off');
    end

    ylabel('MACD', 'FontSize', 11, 'FontWeight', 'bold');
    legend('Location', 'northwest', 'FontSize', 9);
    grid on;
    set(ax2, 'XTickLabel', []);

    % ==================== 子图3: RSI ====================
    ax3 = subplot(4, 1, 3);
    hold on;

    if ismember('rsi_14', data.Properties.VariableNames)
        % 绘制RSI
        plot(dates, data.rsi_14, 'Color', [0.5, 0, 0.8], 'LineWidth', 1.5, 'DisplayName', 'RSI 14');

        % 添加超买超卖线
        plot(dates([1, end]), [70, 70], 'r--', 'LineWidth', 1, 'DisplayName', '超买线(70)');
        plot(dates([1, end]), [30, 30], 'g--', 'LineWidth', 1, 'DisplayName', '超卖线(30)');
        plot(dates([1, end]), [50, 50], 'k--', 'LineWidth', 0.5, 'HandleVisibility', 'off');

        % 填充超买超卖区域
        x_fill = [dates(1); dates(end); dates(end); dates(1)];
        y_fill_over = [70; 70; 100; 100];
        y_fill_under = [0; 0; 30; 30];
        fill(x_fill, y_fill_over, [1, 0.8, 0.8], 'FaceAlpha', 0.2, 'EdgeColor', 'none', 'HandleVisibility', 'off');
        fill(x_fill, y_fill_under, [0.8, 1, 0.8], 'FaceAlpha', 0.2, 'EdgeColor', 'none', 'HandleVisibility', 'off');
    end

    ylabel('RSI', 'FontSize', 11, 'FontWeight', 'bold');
    ylim([0, 100]);
    legend('Location', 'northwest', 'FontSize', 9);
    grid on;
    set(ax3, 'XTickLabel', []);

    % ==================== 子图4: 成交量 ====================
    ax4 = subplot(4, 1, 4);
    hold on;

    % 根据价格涨跌设置成交量颜色
    vol_colors = zeros(length(volume), 3);
    for i = 2:length(volume)
        if close_prices(i) >= close_prices(i-1)
            vol_colors(i, :) = [0.2, 0.8, 0.2]; % 绿色（涨）
        else
            vol_colors(i, :) = [0.8, 0.2, 0.2]; % 红色（跌）
        end
    end
    vol_colors(1, :) = [0.5, 0.5, 0.5]; % 第一根为灰色

    % 绘制成交量柱状图
    for i = 1:length(volume)
        bar(dates(i), volume(i), 'FaceColor', vol_colors(i, :), 'EdgeColor', 'none');
    end

    % 添加成交量移动平均线
    if ismember('vol_ma_5', data.Properties.VariableNames)
        plot(dates, data.vol_ma_5, 'Color', [0, 0, 1], 'LineWidth', 1.5, 'DisplayName', 'Vol MA 5');
    end
    if ismember('vol_ma_20', data.Properties.VariableNames)
        plot(dates, data.vol_ma_20, 'Color', [1, 0.5, 0], 'LineWidth', 1.5, 'DisplayName', 'Vol MA 20');
    end

    ylabel('成交量', 'FontSize', 11, 'FontWeight', 'bold');
    xlabel('日期', 'FontSize', 11, 'FontWeight', 'bold');
    legend('Location', 'northwest', 'FontSize', 9);
    grid on;

    % 链接所有子图的X轴
    linkaxes([ax1, ax2, ax3, ax4], 'x');

    % 设置X轴格式
    ax4.XAxis.TickLabelFormat = 'yyyy-MM-dd';
    xtickangle(ax4, 45);

    % 调整子图间距
    set(ax1, 'Position', [0.08, 0.73, 0.88, 0.22]);
    set(ax2, 'Position', [0.08, 0.50, 0.88, 0.18]);
    set(ax3, 'Position', [0.08, 0.27, 0.88, 0.18]);
    set(ax4, 'Position', [0.08, 0.06, 0.88, 0.18]);

    % 添加整体标题
    sgtitle(sprintf('%s 技术分析图表', ticker), 'FontSize', 16, 'FontWeight', 'bold');

    fprintf('图表绘制完成！\n');
end

function plot_candles(ax, dates, open_prices, high_prices, low_prices, close_prices)
    % 绘制K线图
    % 参数:
    %   ax - 坐标轴句柄
    %   dates - 日期向量
    %   open_prices, high_prices, low_prices, close_prices - 价格数据

    hold(ax, 'on');

    % 计算K线宽度
    if length(dates) > 1
        date_nums = datenum(dates);
        avg_gap = mean(diff(date_nums));
        candle_width = avg_gap * 0.6;
    else
        candle_width = 0.6;
    end

    % 逐根绘制K线
    for i = 1:length(dates)
        date_num = datenum(dates(i));
        open_p = open_prices(i);
        high_p = high_prices(i);
        low_p = low_prices(i);
        close_p = close_prices(i);

        % 判断涨跌
        if close_p >= open_p
            % 阳线（绿色）
            body_color = [0.2, 0.8, 0.2];
            edge_color = [0.1, 0.6, 0.1];
            body_top = close_p;
            body_bottom = open_p;
        else
            % 阴线（红色）
            body_color = [0.8, 0.2, 0.2];
            edge_color = [0.6, 0.1, 0.1];
            body_top = open_p;
            body_bottom = close_p;
        end

        % 绘制上下影线
        plot(ax, [dates(i), dates(i)], [low_p, high_p], 'Color', edge_color, 'LineWidth', 1);

        % 绘制实体
        if body_top ~= body_bottom
            rectangle(ax, 'Position', [date_num - candle_width/2, body_bottom, candle_width, body_top - body_bottom], ...
                     'FaceColor', body_color, 'EdgeColor', edge_color, 'LineWidth', 1);
        else
            % 十字星
            plot(ax, [date_num - candle_width/2, date_num + candle_width/2], [body_top, body_top], ...
                'Color', edge_color, 'LineWidth', 2);
        end
    end

    hold(ax, 'off');
end
