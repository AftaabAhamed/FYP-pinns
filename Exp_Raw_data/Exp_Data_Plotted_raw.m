% File paths
files = { ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Exp_Raw_data\data_5-7.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Exp_Raw_data\data_4-6.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Exp_Raw_data\data_3.5-7.5.csv' ...
};

% Colors for each dataset
colors = {'b', 'g', 'r'}; % Blue, Green, Magenta

% Specific starting times for each file
start_times = [1633, 81, 61];

% Offset for the first and second files to shift their plots to the left
time_shifts = [-1574, -30, 0]; % Shifts for first, second, and third files

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

    % Apply time shift for each file
    time = time + time_shifts(i);

    % Plot voltage vs time
    plot(time, voltage, '-', 'LineWidth', 1.5, 'Color', colors{i}, ...
        'DisplayName', sprintf('Voltage (File %d)', i));
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

    % Apply time shift for each file
    time = time + time_shifts(i);

    % Plot height vs time
    plot(time, height, '--', 'LineWidth', 1.5, 'Color', colors{i}, ...
        'DisplayName', sprintf('Height (File %d)', i));
end
xlabel('Time (s)');
ylabel('Height (units)');
title('Height vs Time');
legend;
grid on;
hold off;
