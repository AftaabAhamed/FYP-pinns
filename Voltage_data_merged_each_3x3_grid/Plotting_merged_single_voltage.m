% Read data from CSV file
filename = 'C:\Users\USER\Desktop\Normal__code_final_year__project\Voltage_data_merged_each_3x3_grid\sdf.csv';
data = readtable(filename);

% Extract columns
voltage = data.voltage;
time = data.time;
height = data.height;

% Initialize variables for processing
step_sequences = {}; % Cell array to hold sequences
sequence_times = {}; % Cell array for adjusted time
sequence_heights = {}; % Cell array for heights

% Maximum time limit for plotting
max_time = 1600; % Stop plotting beyond this time

% Process the data to extract step-up sequences
is_in_sequence = false; % Flag to track if we're in a sequence
sequence_start_idx = 1;

for i = 1:length(voltage) - 1
    if ~is_in_sequence && voltage(i) == 5 && voltage(i + 1) > 5
        % Start of a new sequence
        is_in_sequence = true;
        sequence_start_idx = i;
    elseif is_in_sequence && voltage(i) == 7 && voltage(i + 1) < 7
        % End of the sequence when voltage starts dropping from 7
        is_in_sequence = false;
        % Extract and adjust sequence data
        seq_time = time(sequence_start_idx:i) - time(sequence_start_idx);
        if seq_time(end) <= max_time
            step_sequences{end + 1} = voltage(sequence_start_idx:i); % Store voltage sequence
            sequence_times{end + 1} = seq_time; % Adjusted time
            sequence_heights{end + 1} = height(sequence_start_idx:i); % Store height sequence
        end
    end
end

% Create a 2x1 grid of subplots
figure;

% Plot voltage sequences in the upper grid
subplot(2, 1, 1);
hold on;
for i = 1:length(step_sequences)
    plot(sequence_times{i}, step_sequences{i}, 'b', 'LineWidth', 1.5);
end
hold off;
grid on;
title('Voltage vs. Time (Step-up Only)');
xlabel('Time (s)');
ylabel('Voltage (V)');

% Plot height sequences in the lower grid
subplot(2, 1, 2);
hold on;
for i = 1:length(sequence_heights)
    plot(sequence_times{i}, sequence_heights{i}, 'b', 'LineWidth', 1.5);
end
hold off;
grid on;
title('Height vs. Time (Step-up Only)');
xlabel('Time (s)');
ylabel('Height');
