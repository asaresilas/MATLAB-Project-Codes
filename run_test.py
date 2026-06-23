import traceback
import importlib.util

try:
    spec = importlib.util.spec_from_file_location("compare_fusion_methods", 'scripts/compare_fusion_methods.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Execute the main function if it exists
    if hasattr(module, 'main'):
        module.main()
    elif hasattr(module, '__name__'):
        # If there's a specific function to run, adjust accordingly
        pass
except Exception as e:
    with open('runtime_error.log', 'w') as errf:
        traceback.print_exc(file=errf)