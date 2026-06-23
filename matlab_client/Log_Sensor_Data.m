function status = Log_Sensor_Data(sensor_vector, sensor_names, sample_rate_hz, tstamp, health_state)
% Log_Sensor_Data  Append one sensor sample row to a CSV log file.
%
% Intended for use from a MATLAB Function block or Simulink callback.
% Each call appends a single row: timestamp, health_state, sensor values, sample_rate.
%
% INPUTS:
%   sensor_vector  - numeric row vector [1 x N]  (required)
%   sensor_names   - cell array of strings, length N (optional — used for header)
%   sample_rate_hz - scalar, sampling rate in Hz (optional, default 0)
%   tstamp         - POSIX seconds or datetime (optional, default = now)
%   health_state   - string label: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'UNKNOWN'
%                    (optional, default 'UNKNOWN')
%
% OUTPUT:
%   status  - 0 on success, -1 on error
%
% EXAMPLE:
%   Log_Sensor_Data([0.1,0.2,0.3], {'Ia','Ib','Ic'}, 12000, posixtime(datetime('now')), 'NORMAL')
%
% NOTE: MATLAB Function block file I/O may require that this is called as
%   coder.extrinsic('Log_Sensor_Data') inside the block, or as a Simulink
%   callback (Start/Stop/Pause). Alternatively, use a Simulink "To File" block.

persistent fid filepath header_written

% Set defaults for missing persistent vars
if isempty(header_written)
    header_written = false;
end

status = -1;  % pessimistic default

try
    % ------------------------------------------------------------------
    % 1. Resolve output file path (created once, reused across calls)
    % ------------------------------------------------------------------
    if isempty(filepath)
        log_dir = fullfile(pwd, 'sim_logs');
        if ~exist(log_dir, 'dir')
            mkdir(log_dir);
        end
        % Use datetime instead of deprecated datestr()
        ts_str   = char(datetime('now', 'Format', 'yyyyMMdd_HHmmss'));
        filepath = fullfile(log_dir, ['sensor_log_', ts_str, '.csv']);
    end

    % ------------------------------------------------------------------
    % 2. Open file handle (append mode, reuse across calls)
    % ------------------------------------------------------------------
    if isempty(fid) || fid == -1
        fid = fopen(filepath, 'a');
        if fid == -1
            error('Log_Sensor_Data:FileOpen', 'Cannot open: %s', filepath);
        end
    end

    % ------------------------------------------------------------------
    % 3. Parse inputs
    % ------------------------------------------------------------------
    sensor_vector = double(sensor_vector(:)');   % enforce row vector

    if nargin < 3 || isempty(sample_rate_hz),  sample_rate_hz = 0;         end
    if nargin < 4 || isempty(tstamp)
        tstamp = posixtime(datetime('now', 'TimeZone', 'UTC'));
    elseif isa(tstamp, 'datetime')
        tstamp = posixtime(tstamp);
    end
    if nargin < 5 || isempty(health_state)
        health_state = 'UNKNOWN';
    end
    health_state = upper(strtrim(char(health_state)));

    % ------------------------------------------------------------------
    % 4. Write header on first call
    % ------------------------------------------------------------------
    if ~header_written
        N   = numel(sensor_vector);
        hdr = 'timestamp,health_state';
        if nargin >= 2 && ~isempty(sensor_names) && numel(sensor_names) == N
            for i = 1:N
                hdr = [hdr, ',', strtrim(char(sensor_names{i}))]; %#ok<AGROW>
            end
        else
            for i = 1:N
                hdr = [hdr, sprintf(',S%d', i)]; %#ok<AGROW>
            end
        end
        hdr = [hdr, ',sample_rate_hz'];
        fprintf(fid, '%s\n', hdr);
        header_written = true;
    end

    % ------------------------------------------------------------------
    % 5. Build and write data row
    % ------------------------------------------------------------------
    row = sprintf('%.6f,%s', double(tstamp), health_state);
    for v = sensor_vector
        row = [row, sprintf(',%.6f', double(v))]; %#ok<AGROW>
    end
    row = [row, sprintf(',%d', int32(double(sample_rate_hz)))];
    fprintf(fid, '%s\n', row);

    % Older MATLAB releases may not support fflush(fid). Closing and
    % reopening the append handle guarantees the row is flushed to disk.
    fclose(fid);
    fid = [];

    status = 0;

catch ME
    % Close file handle on error so subsequent calls can re-open
    if ~isempty(fid) && fid ~= -1
        try, fclose(fid); catch; end
        fid = -1; %#ok<NASGU>
    end
    warning('Log_Sensor_Data:Error', '%s', ME.message);
    status = -1;
end
end
