% File paths
files = { ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Exp_Raw_data\data_5-7.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Exp_Raw_data\data_4-6.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Exp_Raw_data\data_3.5-7.5.csv' ...
};

% Colors for each dataset
colors = {'b', 'g', 'r'}; % Blue, Green, Magenta

% Specific starting times for each file
start_times = [18, 81, 61];

% Ranges to exclude for each file (cell array of ranges)
exclude_ranges = {
    [1,1245; 194,541; 1340,1509; 4285,4503;5474,6859; 5370,5475; 8322,9513; 9676,10070], ... % Ranges for file 1
    [2740,3010; 4285,4389; 7230,7530], ...             % Ranges for file 2
    [1335, 1975; 5372,5911; 7213,7999; 8322,8795; 9676,10456; ]                 % Ranges for file 3
};

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

% Initialize arrays to store data for CSV
voltage_data = [];
height_data = [];

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

    % Apply exclusions for the current file
    for j = 1:size(exclude_ranges{i}, 1)
        range = exclude_ranges{i}(j, :);
        exclude_idx = (time >= range(1) & time <= range(2));

        % Remove the excluded range and shift the remaining time values
        if any(exclude_idx)
            time_diff = time(find(exclude_idx, 1, 'last')) - time(find(exclude_idx, 1, 'first'));
            time(find(exclude_idx, 1, 'last') + 1:end) = time(find(exclude_idx, 1, 'last') + 1:end) - time_diff;

            time(exclude_idx) = [];
            voltage(exclude_idx) = [];
        end
    end

    % Append data to voltage_data for CSV
    voltage_data = [voltage_data; time, voltage];

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

% Save voltage data to CSV
%writematrix(voltage_data, 'voltage_data.csv');

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

    % Apply exclusions for the current file
    for j = 1:size(exclude_ranges{i}, 1)
        range = exclude_ranges{i}(j, :);
        exclude_idx = (time >= range(1) & time <= range(2));

        % Remove the excluded range and shift the remaining time values
        if any(exclude_idx)
            time_diff = time(find(exclude_idx, 1, 'last')) - time(find(exclude_idx, 1, 'first'));
            time(find(exclude_idx, 1, 'last') + 1:end) = time(find(exclude_idx, 1, 'last') + 1:end) - time_diff;

            time(exclude_idx) = [];
            height(exclude_idx) = [];
        end
    end

    % Append data to height_data for CSV
    height_data = [height_data; time, height];

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

% Save height data to CSV
%writematrix(height_data, 'height_data.csv');
