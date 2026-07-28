classdef PredictiveMaintenanceClient < handle
    % PredictiveMaintenanceClient: Connect Simulink to Predictive Maintenance API
    %
    % Usage:
    %   client = PredictiveMaintenanceClient('ws://127.0.0.1:8000');
    %   prediction = client.predict(sensor_data, sensor_names);
    %   client.sendGroundTruth(actual_failure, days_to_failure);
    %   client.close();
    %
    % Data Flow Paths:
    %   SIMULINK → API Path: ws://host:port/ws/simulink/{client_id}
    %   API → SIMULINK responds with prediction probability and alert level
    %
    % Created: February 12, 2026
    % Version: 1.0.0
    
    properties
        server_url          % WebSocket server URL (e.g., 'ws://127.0.0.1:8000')
        client_id           % Unique client ID (UUID format)
        machine_id          % Machine identifier
        ws                  % WebSocket connection object
        is_connected        % Connection status
        last_prediction     % Last prediction result
        samples_sent        % Counter: samples sent to API
        predictions_received % Counter: predictions received from API
        connection_log      % Log of all messages
        use_http_fallback = false % Flag for older MATLAB versions
        http_options        % Web options for REST calls
        config              % Configuration struct
    end
    
    methods
        % ====================================================================
        % CONSTRUCTOR
        % ====================================================================
        
        function obj = PredictiveMaintenanceClient(server_url, machine_id)
            % Create connection to API
            %
            % INPUTS:
            %   server_url - WebSocket server URL (required)
            %                Example: 'ws://192.168.1.100:8001'
            %   machine_id - Machine identifier (optional, default: 'MOTOR-001')
            
            if nargin < 1 || isempty(server_url)
                % Provide a sensible default for local development
                server_url = 'ws://127.0.0.1:8000';
                fprintf('[INFO] server_url not provided — defaulting to %s\n', server_url);
            end

            if nargin < 2 || isempty(machine_id)
                machine_id = 'MOTOR-001';
            end
            
            % Initialize properties
            obj.server_url = server_url;
            obj.machine_id = machine_id;
            obj.is_connected = false;
            obj.samples_sent = 0;
            obj.predictions_received = 0;
            obj.connection_log = {};
            
            % Generate unique client ID
            obj.client_id = obj.generateClientID();
            
            % Default configuration
            obj.config = struct(...
                'max_retries', 3, ...
                'timeout_sec', 30, ...
                'auto_reconnect', true, ...
                'log_messages', true, ...
                'prediction_timeout_ms', 30000 ...
            );
            
            % Initialize last prediction — all fields present so isfield() checks
            % in handleMessage never see missing keys on the first message.
            obj.last_prediction = struct(...
                'type',             '', ...
                'timestamp',        '', ...
                'fault_code',       0,  ...   % 0=None 1=Bearing 2=Rotor 3=Shaft 4=Thermal
                'prediction',       0, ...
                'alert_level',      'UNKNOWN', ...
                'model_used',       '', ...
                'confidence',       0, ...
                'uncertainty',      0, ...
                'rul_hours',        -1, ...   % -1 = not yet determined
                'inference_time_ms', 0 ...
            );
        end
        
        
        % ====================================================================
        % CONNECTION MANAGEMENT
        % ====================================================================
        
        function connect(obj)
            % Connect to API WebSocket server
            %
            % PATH: ws://host:port/ws/simulink/{client_id}
            %
            % Example:
            %   client.connect()  % Connects to ws://server_url/ws/simulink/ABC123...
            
            if obj.is_connected
                fprintf('[INFO] Already connected\n');
                return;
            end
            
            try
                % Construct WebSocket URL
                ws_url = sprintf('%s/ws/simulink/%s', obj.server_url, obj.client_id);
                fprintf('[CONNECTING] %s\n', ws_url);
                
                % Create WebSocket connection
                % Using MATLAB's websocket function (requires R2020b+)
                % If not available, provide fallback to tcp/http
                
                try
                    obj.ws = websocket(ws_url);

                    % Set message callbacks using correct MATLAB R2022a+ property names.
                    % The anonymous wrapper forwards (src, event) so the private method
                    % receives the expected three arguments (obj, src, event).
                    obj.ws.MessageReceivedFcn = @(src,evt) obj.handleMessage(src,evt);
                    obj.ws.ErrorFcn           = @(src,evt) obj.handleError(src,evt);
                    obj.ws.ClosedFcn          = @(src,evt) obj.handleClosing(src,evt);

                    % Do NOT set is_connected = true here — wait for the
                    % 'connection_confirmed' handshake from the server instead.
                    % This prevents predict() calls racing before the server is ready.
                    fprintf('[CONNECTING] Waiting for server handshake...\n');
                    tic;
                    while toc < 10
                        if obj.is_connected
                            break;
                        end
                        drawnow('limitrate');   % flush event queue so handleMessage fires
                    end
                    if ~obj.is_connected
                        warning('[API_CLIENT] No connection_confirmed received within 10 s — server may be down or unreachable.');
                    end

                catch
                    % Fallback: Try older WebSocket implementation or TCP
                    fprintf('[WARNING] Using fallback connection method\n');
                    obj.connectViaHTTP();
                end
                
            catch ME
                fprintf('[ERROR] Connection failed: %s\n', ME.message);
                obj.is_connected = false;
            end
        end
        
        
        function connectViaHTTP(obj)
            % Fallback connection using HTTP polling (slower alternative).
            % This path is taken automatically when:
            %   • MATLAB < R2022a (websocket() function not available), OR
            %   • websocket() throws an error (network / TLS issue)
            %
            % Performance note: HTTP polling is synchronous and ~2× slower
            % than the WebSocket path, but all predictions are still returned.
            % Upgrade to MATLAB R2022a+ to enable the WebSocket path.
            fprintf('[INFO] Using HTTP polling fallback (MATLAB < R2022a detected)\n');
            fprintf('[INFO]   Prediction:  POST http://127.0.0.1:8000/api/v1/predict/simulink\n');
            fprintf('[INFO]   Thermal:     POST http://127.0.0.1:8000/api/v1/predict/simulink/thermal\n');
            fprintf('[INFO]   All required fields (fault_code, rul_hours, uncertainty) are returned.\n');
            
            % Web options — generous timeout because the backend loads TF models
            % on startup which can take 60-90 s. Each attempt waits up to 30 s
            % for a response header before giving up.
            obj.http_options = weboptions('MediaType', 'application/json', ...
                                         'Timeout', 30, ...
                                         'ArrayFormat', 'csv');

            % Test connection with health check.
            % Retry up to 20 times (with 5 s gaps = up to 100 s total) to give
            % the backend time to finish loading models before we declare failure.
            try
                http_url = strrep(obj.server_url, 'ws://', 'http://');
                connected = false;
                last_err  = '';
                fprintf('[INFO] Waiting for backend to finish loading models');
                for attempt = 1:20
                    try
                        webread([http_url, '/health'], obj.http_options);
                        connected = true;
                        break;
                    catch retryME
                        last_err = retryME.message;
                        fprintf('.');
                        pause(5);   % wait 5 s between retries (models take time to load)
                    end
                end
                fprintf('\n');
                if connected
                    obj.use_http_fallback = true;
                    obj.is_connected = true;
                    fprintf('[SUCCESS] HTTP connection verified — backend ready.\n');
                else
                    error(last_err);
                end
            catch ME
                fprintf('[ERROR] HTTP Connection failed: %s\n', ME.message);
                obj.is_connected = false;
            end
        end
        
        
        function close(obj)
            % Disconnect from API
            
            if ~obj.is_connected
                fprintf('[INFO] Not connected\n');
                return;
            end
            
            try
                if ~isempty(obj.ws)
                    obj.ws.close();
                end
                obj.is_connected = false;
                fprintf('[CLOSED] ✓ Disconnected from API\n');
                fprintf('  Total samples sent: %d\n', obj.samples_sent);
                fprintf('  Total predictions received: %d\n', obj.predictions_received);
            catch ME
                fprintf('[ERROR] Close failed: %s\n', ME.message);
            end
        end
        
        
        function is_connected_status = isConnected(obj)
            % Check if connected
            is_connected_status = obj.is_connected;
        end
        
        
        % ====================================================================
        % MAIN PREDICTION API
        % ====================================================================
        
        function prediction = predict(obj, sensor_data, sensor_names, varargin)
            % Send sensor data to API and get prediction
            %
            % DATA FLOW:
            %   SIMULINK sends sensor_data
            %     ↓ (via WebSocket JSON)
            %   ws://host:port/ws/simulink/{client_id}
            %     ↓
            %   API receives in websocket_handler.py
            %     ↓
            %   PredictionEngine.predict() runs inference
            %     ↓
            %   Response returns: prediction, alert_level, model_used
            %     ↓
            %   SIMULINK receives and acts on alert
            %
            % INPUT:
            %   sensor_data  - Array of sensor readings (e.g., [0.5, 0.3, 0.8])
            %   sensor_names - Cell array of sensor names (optional)
            %                  Example: {'Vibration_X', 'Vibration_Y', 'Temperature'}
            %   (optional) machine_id - Override default machine_id
            %
            % OUTPUT:
            %   prediction - Struct with fields:
            %     .value           - Failure probability 0-1
            %     .alert_level     - 'NORMAL', 'WARNING', or 'CRITICAL'
            %     .model_used      - Which model made prediction
            %     .confidence      - Model confidence 0-1
            %     .inference_time_ms - Computation time
            %     .timestamp       - Server timestamp
            %
            % EXAMPLE:
            %   sensor_data = [0.5, 0.3, 0.8, 0.2, 0.9];
            %   names = {'Vibration_X', 'Vibration_Y', 'Temp', 'Sound', 'Pressure'};
            %   pred = client.predict(sensor_data, names);
            %   if strcmp(pred.alert_level, 'CRITICAL')
            %       disp('⚠️  ALERT: Equipment failure likely soon!');
            %   end
            
            % Check connection
            if ~obj.is_connected
                warning('Not connected to API. Call connect() first.');
                prediction = obj.getDefaultPrediction('not_connected');
                return;
            end
            
            % Parse optional arguments
            machine_id = obj.machine_id;
            if ~isempty(varargin) && ischar(varargin{1})
                machine_id = varargin{1};
            end
            
            % Default sensor names if not provided
            if nargin < 3 || isempty(sensor_names)
                num_sensors = length(sensor_data);
                sensor_names = cell(num_sensors, 1);
                for i = 1:num_sensors
                    sensor_names{i} = sprintf('Sensor_%d', i);
                end
            end
            
            % Ensure sensor_data is formatted correctly
            if isstruct(sensor_data)
                payload_data = sensor_data;
            else
                payload_data = double(sensor_data(:)');
            end
            
            % Clear stale prediction state — reset only the discriminator fields
            % so the wait-loop below doesn't match an old response.
            obj.last_prediction.timestamp = '';
            obj.last_prediction.type      = '';
            
            % Create message for API
            message = struct(...
                'type', 'sensor_data', ...
                'timestamp', obj.getISO8601Timestamp(), ...
                'sensor_data', payload_data, ...
                'sensor_names', {sensor_names}, ...
                'machine_id', machine_id ...
            );
            
            % Use HTTP REST if in Legacy Mode
            if obj.use_http_fallback
                try
                    http_url = strrep(obj.server_url, 'ws://', 'http://');
                    endpoint = [http_url, '/api/v1/predict/simulink'];
                    
                    % Perform synchronous HTTP POST
                    raw_res = webwrite(endpoint, message, obj.http_options);
                    
                    % Map response to standard structure
                    prediction = raw_res;
                    obj.last_prediction = prediction;
                    obj.predictions_received = obj.predictions_received + 1;
                    return;
                catch ME
                    warning(ME.identifier, '%s', ME.message);
                    prediction = obj.getDefaultPrediction('http_error');
                    return;
                end
            end
            
            % Send message to API via WebSocket (Standard Mode)
            obj.sendJSON(message);
            obj.samples_sent = obj.samples_sent + 1;
            
            % Wait for response (blocking until timeout)
            % drawnow('limitrate') flushes the MATLAB event queue each iteration
            % so WebSocket callbacks (handleMessage) can fire without a full repaint.
            % This prevents solver overruns in Simulink while keeping the loop tight.
            tic;
            timeout_sec = obj.config.prediction_timeout_ms / 1000;

            while toc < timeout_sec
                if ~isempty(obj.last_prediction.timestamp) && ...
                   (strcmp(obj.last_prediction.type, 'prediction') || strcmp(obj.last_prediction.type, 'prediction_error'))
                    prediction = obj.last_prediction;
                    obj.predictions_received = obj.predictions_received + 1;
                    return;
                end
                drawnow('limitrate');  % Flush event queue so WS callbacks fire (no full repaint)
            end
            
            % Timeout
            warning('API response timeout (%d ms)', obj.config.prediction_timeout_ms);
            prediction = obj.getDefaultPrediction('timeout');
        end
        
        function prediction = predict_thermal(obj, image_matrix, varargin)
            % Send thermal image to API and get prediction
            %
            % INPUT:
            %   image_matrix - 2D or 3D matrix of pixel values (0-255 or 0-1)
            
            if ~obj.is_connected
                warning('Not connected to API.');
                prediction = obj.getDefaultPrediction('not_connected');
                return;
            end
            
            % Convert matrix to Base64
            try
                base64_img = obj.matrixToBase64(image_matrix);
            catch ME
                warning(ME.identifier, '%s', ME.message);
                prediction = obj.getDefaultPrediction('encoding_error');
                return;
            end
            
            % Create message
            message = struct(...
                'type', 'thermal_image', ...
                'timestamp', obj.getISO8601Timestamp(), ...
                'image_base64', base64_img, ...
                'machine_id', obj.machine_id ...
            );
            
            % Use HTTP REST if in Legacy Mode
            if obj.use_http_fallback
                try
                    http_url = strrep(obj.server_url, 'ws://', 'http://');
                    endpoint = [http_url, '/api/v1/predict/simulink/thermal'];  % Auth-free simulink thermal route
                    
                    % Perform synchronous HTTP POST
                    raw_res = webwrite(endpoint, message, obj.http_options);
                    
                    % Map response
                    prediction = raw_res;
                    obj.last_prediction = prediction;
                    obj.predictions_received = obj.predictions_received + 1;
                    return;
                catch ME
                    warning(ME.identifier, '%s', ME.message);
                    prediction = obj.getDefaultPrediction('http_error');
                    return;
                end
            end
            
            % Send via WebSocket (Standard Mode)
            obj.sendJSON(message);
            obj.samples_sent = obj.samples_sent + 1;
            
            % Wait for response
            tic;
            timeout_sec = obj.config.prediction_timeout_ms / 1000;
            while toc < timeout_sec
                if ~isempty(obj.last_prediction) && strcmp(obj.last_prediction.type, 'prediction_thermal')
                    prediction = obj.last_prediction;
                    obj.predictions_received = obj.predictions_received + 1;
                    return;
                end
                pause(0.01);
            end
            
            warning('Thermal API timeout');
            prediction = obj.getDefaultPrediction('timeout');
        end
        
        
        % ====================================================================
        % GROUND TRUTH / LEARNING API
        % ====================================================================
        
        function sendGroundTruth(obj, actual_failure, days_to_failure, failure_type)
            % Send actual failure outcome for model retraining
            %
            % This data is collected and used in the weekly retraining pipeline.
            % Ground truth is critical for continuous learning.
            %
            % DATA FLOW:
            %   Virtual System detects actual failure
            %     ↓
            %   SIMULINK sends ground truth via WebSocket
            %     ↓
            %   ws://host:port/ws/simulink/{client_id}
            %     ↓ (type: "ground_truth")
            %   PostgreSQL table: ground_truth
            %     ↓ (every Sunday night)
            %   Weekly retraining script aggregates data
            %     ↓
            %   New model trained and validated
            %     ↓
            %   Deployed with A/B testing (10% traffic)
            %
            % INPUT:
            %   actual_failure     - Boolean/0-1, did failure actually occur?
            %   days_to_failure    - Integer, days until failure after prediction
            %   failure_type       - String (optional), type of failure
            %                        Examples: 'bearing', 'motor_winding', 'electrical'
            %
            % EXAMPLE:
            %   % Equipment actually failed 3 days after our prediction
            %   client.sendGroundTruth(true, 3, 'bearing_fault');
            %   
            %   % Equipment is still running (low failure risk confirmed)
            %   client.sendGroundTruth(false, 0, 'normal_operation');
            
            if ~obj.is_connected
                warning('Not connected. Call connect() first.');
                return;
            end
            
            if nargin < 4
                failure_type = 'unknown';
            end
            
            % Convert boolean to numeric if needed
            if islogical(actual_failure)
                actual_failure = double(actual_failure);
            end
            
            % Create ground truth message
            message = struct(...
                'type', 'ground_truth', ...
                'timestamp', obj.getISO8601Timestamp(), ...
                'actual_failure', actual_failure, ...
                'days_to_failure', days_to_failure, ...
                'failure_type', failure_type, ...
                'machine_id', obj.machine_id ...
            );
            
            % Send to API
            obj.sendJSON(message);
            fprintf('[GROUND TRUTH] Sent: %s (failure=%d, days=%d)\n', ...
                failure_type, actual_failure, days_to_failure);
        end
        
        
        % ====================================================================
        % HEALTH & MONITORING
        % ====================================================================
        
        function healthCheck(obj)
            % Send health check to API
            
            if ~obj.is_connected
                fprintf('[WARNING] Not connected\n');
                return;
            end
            
            message = struct(...
                'type', 'health_check', ...
                'timestamp', obj.getISO8601Timestamp() ...
            );
            
            obj.sendJSON(message);
            fprintf('[HEALTH CHECK] Sent\n');
        end
        
        
        function printStats(obj)
            % Print connection statistics
            
            fprintf('\n====== CONNECTION STATISTICS ======\n');
            fprintf('Server: %s\n', obj.server_url);
            fprintf('Client ID: %s\n', obj.client_id);
            fprintf('Machine: %s\n', obj.machine_id);
            fprintf('Connected: %s\n', obj.bool2str(obj.is_connected));
            fprintf('Samples Sent: %d\n', obj.samples_sent);
            fprintf('Predictions Received: %d\n', obj.predictions_received);
            
            if obj.predictions_received > 0
                fprintf('\nLast Prediction:\n');
                fprintf('  Alert:      %s\n',    obj.last_prediction.alert_level);
                fprintf('  Confidence: %.1f %%\n', obj.last_prediction.confidence * 100);
                fprintf('  Uncertainty:%.1f %%\n', obj.last_prediction.uncertainty * 100);
                if obj.last_prediction.rul_hours >= 0
                    fprintf('  RUL:        %.1f h\n', obj.last_prediction.rul_hours);
                else
                    fprintf('  RUL:        not yet determined\n');
                end
                fprintf('  Model:      %s\n', obj.last_prediction.model_used);
                fprintf('  Latency:    %.2f ms\n', obj.last_prediction.inference_time_ms);
            end
            fprintf('====================================\n\n');
        end
        
        
    end
    
    methods (Access = private)
        % ====================================================================
        % PRIVATE HELPER METHODS
        % ====================================================================
        
        function sendJSON(obj, data)
            % Send JSON message to API via WebSocket
            
            try
                json_str = jsonencode(data);
                
                if obj.config.log_messages
                    fprintf('[SEND] %s\n', json_str(1:min(80, length(json_str))));
                    if length(json_str) > 80
                        fprintf('       ...\n');
                    end
                end
                
                obj.ws.send(json_str);
                
            catch ME
                fprintf('[ERROR] Failed to send message: %s\n', ME.message);
            end
        end
        
        
        function handleMessage(obj, src, event) %#ok<INUSL>
            % Callback when message received from API.
            % Signature must be (obj, src, event) — MATLAB passes 3 arguments.
            % src  = websocket object (unused — suppressed with %#ok)
            % event.Message contains the received text payload.

            try
                data = jsondecode(event.Message);  % MATLAB websocket uses event.Message, not event.Data
                
                if obj.config.log_messages
                    msg_type = data.type;
                    fprintf('[RECEIVED] Type: %s\n', msg_type);
                end
                
                % Route message by type
                switch data.type
                    case 'connection_confirmed'
                        % Server has acknowledged the WebSocket upgrade.
                        % Only NOW mark the client as connected so that predict()
                        % calls cannot race ahead before the server is ready.
                        obj.is_connected = true;
                        fprintf('[SUCCESS] ✓ Connected to API (handshake confirmed)\n');
                        fprintf('  Server:    %s\n', obj.server_url);
                        fprintf('  Client ID: %s\n', obj.client_id);
                        fprintf('  Machine:   %s\n', obj.machine_id);

                    case {'prediction', 'prediction_thermal', 'prediction_error'}
                        % Start with safe defaults, then overlay received fields
                        obj.last_prediction.type        = data.type;
                        obj.last_prediction.timestamp   = data.timestamp;
                        obj.last_prediction.alert_level = 'UNKNOWN';
                        obj.last_prediction.confidence  = 0;
                        obj.last_prediction.uncertainty = 0;
                        obj.last_prediction.rul_hours   = -1;
                        obj.last_prediction.model_used  = '';
                        obj.last_prediction.inference_time_ms = 0;

                        % Common optional fields
                        if isfield(data, 'alert_level'),      obj.last_prediction.alert_level      = data.alert_level;      end
                        if isfield(data, 'confidence'),       obj.last_prediction.confidence       = data.confidence;       end
                        if isfield(data, 'uncertainty'),      obj.last_prediction.uncertainty      = data.uncertainty;      end
                        if isfield(data, 'rul_hours'),        obj.last_prediction.rul_hours        = data.rul_hours;        end
                        if isfield(data, 'fault_code'),       obj.last_prediction.fault_code       = data.fault_code;       end
                        if isfield(data, 'inference_time_ms'),obj.last_prediction.inference_time_ms = data.inference_time_ms; end

                        % Type-specific fields
                        if strcmp(data.type, 'prediction')
                            if isfield(data, 'prediction'),  obj.last_prediction.prediction  = data.prediction; end
                            if isfield(data, 'model_used'),  obj.last_prediction.model_used  = data.model_used; end
                        elseif strcmp(data.type, 'prediction_thermal')
                            if isfield(data, 'predicted_class')
                                obj.last_prediction.predicted_class = data.predicted_class;
                            end
                            obj.last_prediction.model_used = 'Thermal-MobileNetV2';
                        elseif strcmp(data.type, 'prediction_error')
                            if isfield(data, 'message'), obj.last_prediction.error_message = data.message; end
                            obj.last_prediction.model_used = 'UNAVAILABLE';
                        end

                        % Log significant alerts
                        if isfield(data, 'alert_level')
                            if strcmp(data.alert_level, 'CRITICAL')
                                fprintf('[ALERT] CRITICAL health state — RUL: %.1f h\n', ...
                                    obj.last_prediction.rul_hours);
                            elseif strcmp(data.alert_level, 'WARNING')
                                fprintf('[WARNING] Degraded health state — RUL: %.1f h\n', ...
                                    obj.last_prediction.rul_hours);
                            end
                        end
                        
                    case 'ground_truth_ack'
                        fprintf('[ACK] Ground truth received by API\n');
                        
                    case 'health_check_response'
                        fprintf('[OK] API is healthy\n');
                        
                    case 'error'
                        fprintf('[ERROR] API error: %s\n', data.message);
                        
                    otherwise
                        fprintf('[INFO] Received: %s\n', data.type);
                end
                
                % Store in log
                if obj.config.log_messages
                    obj.connection_log{end+1} = struct(...
                        'direction', 'receive', ...
                        'timestamp', datetime('now'), ...
                        'data', data ...
                    );
                end
                
            catch ME
                fprintf('[ERROR] Message handling failed: %s\n', ME.message);
            end
        end
        
        
        function handleError(obj, src, event) %#ok<INUSL>
            % Callback when a WebSocket error occurs.
            % Signature must be (obj, src, event) — MATLAB passes 3 arguments.
            obj.is_connected = false;
            if isfield(event, 'Message') && ~isempty(event.Message)
                fprintf('[ERROR] WebSocket error: %s\n', event.Message);
            else
                fprintf('[ERROR] WebSocket error (no message detail)\n');
            end
        end


        function handleClosing(obj, src, event) %#ok<INUSL,INUSD>
            % Callback when connection closes.
            % Signature must be (obj, src, event) — MATLAB passes 3 arguments.
            fprintf('[DISCONNECTED] WebSocket closed\n');
            obj.is_connected = false;
        end
        
        
        function id = generateClientID(~)
            % Generate unique UUID-like client ID
            id = char(java.util.UUID.randomUUID);
        end
        
        
        function timestamp = getISO8601Timestamp(~)
            % Get current timestamp in ISO8601 format
            % Uses modern datetime formatting (compatible with R2020b+)
            timestamp = char(datetime('now', 'TimeZone', 'UTC', 'Format', 'yyyy-MM-dd''T''HH:mm:ss''Z'''));
        end
        
        
        function prediction = getDefaultPrediction(obj, reason)
            % Return default prediction when API unavailable
            prediction = struct(...
                'value', 0.5, ...
                'alert_level', 'UNKNOWN', ...
                'model_used', 'UNAVAILABLE', ...
                'confidence', 0, ...
                'inference_time_ms', 0, ...
                'timestamp', obj.getISO8601Timestamp(), ...
                'status', reason ...
            );
        end
        
        
        function str = bool2str(~, bool)
            % Convert boolean to string
            if bool
                str = 'YES ✓';
            else
                str = 'NO ✗';
            end
        end
        
        function base64_str = matrixToBase64(~, img_matrix)
            % Convert matrix to Base64 JPEG string
            if ~isa(img_matrix, 'uint8')
                img_matrix = uint8(img_matrix * 255);
            end
            
            % Save to temporary file
            tmp_file = [tempname, '.jpg'];
            imwrite(img_matrix, tmp_file, 'Quality', 70);
            
            % Read bytes and encode
            fid = fopen(tmp_file, 'rb');
            bytes = fread(fid, Inf, 'uint8=>uint8');
            fclose(fid);
            delete(tmp_file);
            
            % Java-based encode (Standard in MATLAB)
            encoder = java.util.Base64.getEncoder();
            base64_str = char(encoder.encodeToString(bytes));
        end
    end
end

% ============================================================================
% EXAMPLE USAGE & INTEGRATION WITH SIMULINK
% ============================================================================
%
% 1. MATLAB SCRIPT EXAMPLE
%    ─────────────────────
%
%    % Create client
%    client = PredictiveMaintenanceClient('ws://192.168.1.100:8000', 'MOTOR-001');
%
%    % Connect to API
%    client.connect();
%
%    % Send sensor data and get prediction
%    sensor_data = [0.5, 0.3, 0.8, 0.2];
%    sensor_names = {'Vibration_X', 'Vibration_Y', 'Temperature', 'Speed'};
%    prediction = client.predict(sensor_data, sensor_names);
%
%    % Check alert level
%    if strcmp(prediction.alert_level, 'CRITICAL')
%        disp('⚠️  CRITICAL FAILURE RISK - SCHEDULE MAINTENANCE NOW');
%    end
%
%    % Clean up
%    client.close();
%
%
% 2. SIMULINK INTEGRATION
%    ────────────────────
%
%    Create a MATLAB Function Block in Simulink:
%
%    ﻿function prediction = fcn(sensor1, sensor2, sensor3, sensor4)
%        persistent client;
%
%        if isempty(client)
%            client = PredictiveMaintenanceClient('ws://192.168.1.100:8000');
%            client.connect();
%        end
%
%        if client.isConnected()
%            sensor_data = [sensor1, sensor2, sensor3, sensor4];
%            pred = client.predict(sensor_data);
%            prediction = pred.prediction;  % Return failure probability (0-1)
%        else
%            prediction = 0.5;  % Default if disconnected
%        end
%    end
%
%    Connect outputs to:
%    - Failure probability → Alerting logic
%    - Alert level → Visual indicators
%    - Inference time → Performance monitoring
%
%
% 3. WEEKLY GROUND TRUTH UPDATE
%    ─────────────────────────
%
%    % After virtual system detects actual failure
%    if actual_failure_detected
%        client.sendGroundTruth(true, 3, 'bearing_wear');  % Failed 3 days later
%    end
%
%    This data feeds the weekly retraining pipeline:
%    Sunday 2:00 AM: Aggregate ground truth + sensor data
%    Sunday 3:00 AM: Train new model
%    Sunday 4:00 AM: A/B test with 10% traffic
%    If metrics improve: Promote to 100% traffic
%

