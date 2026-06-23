import os
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# List of exact filenames to delete
FILES_TO_DELETE = [
    # Old Week 1 Drafts
    "WEEK1_IMPLEMENTATION_GUIDE.md",
    "WEEK1_SUMMARY.md",
    "README_WEEK1_IMPLEMENTATION.md",
    
    # Old Quick Starts
    "START_HERE.md",
    "QUICK_START.md",
    "QUICK_REFERENCE.md",
    
    # Old Architectural Plans
    "COMPLETE_PATH_MAPPING.md",
    "DATA_FLOW_PATHS.md",
    "architecture_recommendation.md",
    "technical_roadmap.txt",
    
    # Old API Test Reports
    "COMPREHENSIVE_API_TEST.md",
    "COMPREHENSIVE_TEST_SUMMARY.md",
    "RUN_API_TEST_NOW.md",
    
    # Old Submission Drafts
    "FINAL_DEPLOYMENT_SUMMARY.md",
    "FINAL_SUBMISSION_CHECKLIST.md",
    "PUBLICATION_DOC_GUIDE.md",
    "project_evaluation.md",
    "METHODOLOGY_OVERVIEW.txt",
    "RESEARCH_INTEGRITY_REPORT.txt",
    "thermal_model_explanation.txt",
    "current_signature_analysis_report.txt",
    
    # Miscellaneous Old Texts
    "build_log.txt",
    "evaluation_error.txt",
    "temp_output.txt",
    "test_output.txt",
    "data_loaders.txt",
    "versions.txt",
    "end.txt"
]

def clean_workspace():
    print(f"🧹 Starting Workspace Cleanup in: {PROJECT_ROOT}\n")
    deleted_count = 0
    
    # 1. Delete Exact Files
    for filename in FILES_TO_DELETE:
        filepath = os.path.join(PROJECT_ROOT, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"  [-] Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"  [!] Failed to delete {filename}: {e}")
                
    # 2. Delete all .log files in root
    log_files = glob.glob(os.path.join(PROJECT_ROOT, "*.log"))
    for filepath in log_files:
        try:
            os.remove(filepath)
            filename = os.path.basename(filepath)
            print(f"  [-] Deleted Log: {filename}")
            deleted_count += 1
        except Exception as e:
            print(f"  [!] Failed to delete log {filepath}: {e}")
            
    # 3. Delete old JSON api test reports
    json_reports = glob.glob(os.path.join(PROJECT_ROOT, "api_test_report_*.json"))
    for filepath in json_reports:
        try:
            os.remove(filepath)
            filename = os.path.basename(filepath)
            print(f"  [-] Deleted JSON Dump: {filename}")
            deleted_count += 1
        except Exception as e:
            pass

    print(f"\n✨ Cleanup Complete! Removed {deleted_count} unnecessary files.")
    print("Your project root is now clean and ready for final submission packaging.")

if __name__ == "__main__":
    clean_workspace()
