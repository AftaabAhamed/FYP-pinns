% File paths
files = { ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Finalized\file1.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Finalized\file2.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Finalized\file3.csv' ...

};

% Colors for each dataset
colors = {'b', 'g', 'm'}; % Blue, Green, Magenta

% Specific starting times for each file
start_times = [18, 81, 61];

% Voltage labels for the legend
voltage_labels = {
    'U_i (5-7 V)', ...
    'U_i (4-6 V)', ...
    'U_i (3.5-7.5 V)'
};
height_labels = {
    'Y_i (5-7 V)', ...
    'Y_i (4-6 V)', ...
    'Y_i (3.5-7.5 V)'
};

% Create a figure window
figure;

% Top subplot: Voltage vs Time
subplot(2, 1, 1); % Create a 2-row, 1-column grid, and select the 1st subplot
hold on;
for i = 1:length(files)
    % Read the CSV file
    data = readtable(files{i});

    % Extract columns from the table
    time = data.time;
    voltage = data.voltage;

    % Find the index where time is closest to the specific starting time
    [~, idx_start] = min(abs(time - start_times(i)));
    
    % Slice the data starting from the specific starting point
    time = time(idx_start:end);
    voltage = voltage(idx_start:end);

    % Plot voltage vs time
    plot(time, voltage, '-', 'LineWidth', 1.5, 'Color', colors{i}, ...
        'DisplayName', voltage_labels{i});
end
xlabel('Time (s)');
ylabel('Voltage (V)');
title('Voltage vs Time');
legend;
grid on;
hold off;

% Bottom subplot: Height vs Time
subplot(2, 1, 2); % Create a 2-row, 1-column grid, and select the 2nd subplot
hold on;
for i = 1:length(files)
    % Read the CSV file
    data = readtable(files{i});

    % Extract columns from the table
    time = data.time;
    height = data.height;

    % Find the index where time is closest to the specific starting time
    [~, idx_start] = min(abs(time - start_times(i)));
    
    % Slice the data starting from the specific starting point
    time = time(idx_start:end);
    height = height(idx_start:end);

    % Plot height vs time
    plot(time, height, '--', 'LineWidth', 1.5, 'Color', colors{i}, ...
        'DisplayName', height_labels{i});
end
xlabel('Time (s)');
ylabel('Height (m)');
title('Height vs Time');
legend;
grid on;
hold off;
