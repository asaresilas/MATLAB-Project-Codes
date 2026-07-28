function val = safe_evalin_d(varname, default_val)
%SAFE_EVALIN_D  Read a scalar double from the MATLAB base workspace.
%   VAL = SAFE_EVALIN_D(VARNAME, DEFAULT_VAL) returns the base-workspace
%   variable VARNAME cast to double.  Returns DEFAULT_VAL if the variable
%   does not exist, is empty, or cannot be converted to double.
%
%   IMPORTANT — this file must NOT be placed inside a %#codegen function as
%   a local function.  MATLAB Coder analyzes local-function bodies even when
%   the call site is declared coder.extrinsic; try/catch would trigger
%   "TRY/CATCH is unsupported for code generation".  As a separate file,
%   the code generator never opens this file and the restriction does not
%   apply.
try
    val = double(evalin('base', varname));
catch
    val = double(default_val);
end
end
