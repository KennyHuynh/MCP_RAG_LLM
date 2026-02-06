from rapidfuzz import fuzz

actual_target = "First Name"
selectors = [{'tag': 'label', 'id': None, 'name': None, 'placeholder': 'billing_first_name', 'role': 'select2-billing_state-container', 'text': 'billing_last_name', 'type': None, 'playwright_hint': "get_by_text('Password *')"}]
print(actual_target)
for selector in selectors:
    for k,v in selector.items():
        print(f"key and value are: {k} and {v}")
        if v:
            score = fuzz.ratio(v.lower(), actual_target.lower())
            if score > 50:
                print(f"score ratio is: {score}")
                actual_target = selector[k]
                print(f"value after modifying is : {actual_target}")
                break
    break