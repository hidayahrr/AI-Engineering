import json
import urllib.request
import urllib.error
import os

# Define file paths and server URL
EVAL_CASES_PATH = os.path.join("evals", "cases.json")
API_URL = "http://127.0.0.1:8000/triage"

def run_evaluation():
    # Line 1: Verify the test cases file exists
    if not os.path.exists(EVAL_CASES_PATH):
        print(f"Error: Could not find evaluation file at {EVAL_CASES_PATH}")
        return

    # Line 2: Read and load the 8 JSON test cases from disk
    with open(EVAL_CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total_cases = len(cases)
    category_matches = 0
    urgency_matches = 0
    exact_matches = 0
    failures = []

    print(f"\n--- Running Evaluation Suite on {total_cases} Test Cases ---\n")

    # Line 3: Iterate through each test case sequentially
    for index, case in enumerate(cases, start=1):
        user_input = case["input"]
        expected_cat = case["expected_category"]
        expected_urg = case["expected_urgency"]

        # Line 4: Prepare HTTP POST payload
        payload = json.dumps({"text": user_input}).encode("utf-8")
        req = urllib.request.Request(
            API_URL, 
            data=payload, 
            headers={"Content-Type": "application/json"}
        )

        try:
            # Line 5: Send POST request to local FastAPI endpoint
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                
                actual_cat = response_data.get("category")
                actual_urg = response_data.get("urgency")

                # Line 6: Check for category and urgency matches
                cat_passed = (actual_cat == expected_cat)
                urg_passed = (actual_urg == expected_urg)

                if cat_passed:
                    category_matches += 1
                if urg_passed:
                    urgency_matches += 1
                if cat_passed and urg_passed:
                    exact_matches += 1
                else:
                    # Line 7: Record failed cases for reporting
                    failures.append({
                        "case_number": index,
                        "input": user_input,
                        "expected": {"category": expected_cat, "urgency": expected_urg},
                        "actual": {"category": actual_cat, "urgency": actual_urg}
                    })

                status_symbol = "✅" if (cat_passed and urg_passed) else "❌"
                print(f"Case {index}: {status_symbol} Expected [{expected_cat}/{expected_urg}], Got [{actual_cat}/{actual_urg}]")

        except urllib.error.HTTPError as e:
            print(f"Case {index}: ❌ HTTP Error {e.code}: {e.read().decode()}")
            failures.append({
                "case_number": index,
                "input": user_input,
                "error": f"HTTP {e.code}"
            })
        except Exception as e:
            print(f"Case {index}: ❌ Connection Failed: {str(e)}")
            return

    # Line 8: Compute accuracy metrics
    cat_accuracy = (category_matches / total_cases) * 100
    urg_accuracy = (urgency_matches / total_cases) * 100
    exact_accuracy = (exact_matches / total_cases) * 100

    # Line 9: Print final evaluation summary report
    print("\n================ EVALUATION SUMMARY ================")
    print(f"Category Accuracy (Key Field): {category_matches}/{total_cases} ({cat_accuracy:.1f}%)")
    print(f"Urgency Accuracy:            {urgency_matches}/{total_cases} ({urg_accuracy:.1f}%)")
    print(f"Exact Match Accuracy:          {exact_matches}/{total_cases} ({exact_accuracy:.1f}%)")
    print("====================================================\n")

    # Line 10: Print failures if any exist
    if failures:
        print("--- Detailed Failures ---")
        for fail in failures:
            print(json.dumps(fail, indent=2))
    else:
        print("🎉 All test cases passed perfectly!")

if __name__ == "__main__":
    run_evaluation()