# FLOW_ID: CHECKOUT_PROCESS_001
Describe the checkout process from login to payment.

## STEP 1: LOGIN_STAGE
- Condition: User is at https://demo.testarchitect.com
- Action: `fill` | Target: `input#username` | Value: "loc.huynh@agest.vn"
- Action: `fill` | Target: `input#password` | Value: "1"
- Action: `click` | Target: `button#login-btn`
- Expected_URL: https://demo.testarchitect.com

## STEP 2: ADD_TO_CART_STAGE
- Condition: User is at https://demo.testarchitect.com
- Action: `click` | Target: `button.add-to-cart-1`
- Action: `click` | Target: `a.cart-icon`
- Expected_URL: https://demo.testarchitect.com

## STEP 3: PAYMENT_STAGE
- Condition: User is at https://demo.testarchitect.com
- Action: `click` | Target: `button#checkout-button`
- Action: `fill` | Target: `input#card-number` | Value: "4111..."
- Action: `click` | Target: `button#place-order`
- Expected_URL: https://demo.testarchitect.com