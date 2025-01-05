% Filepaths for the three CSV files
filenames = {
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Voltage_data_merged_each_3x3_grid\sdf.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Voltage_data_merged_each_3x3_grid\sdf_4-7.csv', ...
    'C:\Users\USER\Desktop\Normal__code_final_year__project\Voltage_data_merged_each_3x3_grid\sdf_3.5-7.5.csv'
};

% Configuration for each file
configs = {
    struct('max_time', 1600, 'step_start', 5, 'step_end', 7, 'color', 'b'), ...
    struct('max_time', 1400, 'step_start', 4, 'step_end', 6, 'color', 'g'), ...
    struct('max_time', 1800, 'step_start', 3.5, 'step_end', 7.5, 'color', 'r')
};

% Initialize figure and setup 3x3 grid
figure;

% Process each file
for file_idx = 1:length(filenames)
    % Load data from file
    data = readtable(filenames{file_idx});
    voltage = data.voltage;
    time = data.time;
    height = data.height;

    % Extract configuration
    max_time = configs{file_idx}.max_time;
    step_start = configs{file_idx}.step_start;
    step_end = configs{file_idx}.step_end;
    color = configs{file_idx}.color;

    % Initialize variables for processing
    step_sequences = {};
    sequence_times = {};
    sequence_heights = {};

    % Process the data to extract step-up sequences
    is_in_sequence = false;
    sequence_start_idx = 1;

    for i = 1:length(voltage) - 1
        if ~is_in_sequence && voltage(i) == step_start && voltage(i + 1) > step_start
            is_in_sequence = true;
            sequence_start_idx = i;
        elseif is_in_sequence && voltage(i) == step_end && voltage(i + 1) < step_end
            is_in_sequence = false;
            seq_time = time(sequence_start_idx:i) - time(sequence_start_idx);
            if seq_time(end) <= max_time
                step_sequences{end + 1} = voltage(sequence_start_idx:i);
                sequence_times{end + 1} = seq_time;
                sequence_heights{end + 1} = height(sequence_start_idx:i);
            end
        end
    end

    % Plot voltage sequences
    subplot(3, 3, file_idx);
    hold on;
    for i = 1:length(step_sequences)
        plot(sequence_times{i}, step_sequences{i}, color, 'LineWidth', 1.5);
    end
    hold off;
    grid on;
    title(['Voltage vs. Time (' num2str(step_start) '-' num2str(step_end) ' V)']);
    xlabel('Time (s)');
    ylabel('Voltage (V)');

    % Plot height sequences
    subplot(3, 3, file_idx + 3);
    hold on;
    for i = 1:length(sequence_heights)
        plot(sequence_times{i}, sequence_heights{i}, color, 'LineWidth', 1.5);
    end
    hold off;
    grid on;
    title(['Height vs. Time (' num2str(step_start) '-' num2str(step_end) ' V)']);
    xlabel('Time (s)');
    ylabel('Height (m)');
end

% Add legends and adjust layout for clarity
sgtitle('Voltage and Height Step-Up Sequences for All Files');
