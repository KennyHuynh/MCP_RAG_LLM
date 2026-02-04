# FLOW_ID: PAYMENT_PROCESS_001
Description: Process from login to payment.

## STEP 1: LOGIN_STAGE
- Target URL: User is at https://automationexercise.com/login
- Action: `fill` | Target: Email Address input | Value: "loc.huynh@agest.vn"
- Action: `fill` | Target: Password input | Value: "1" input
- Action: `click` | Target: Login button

## STEP 2: ADD_TO_CART_STAGE
- Target URL: User is at https://automationexercise.com/products
- Action: `click` | Target: Add To Cart button

## STEP 3: PAYMENT STAGE
- Target URL: User is at https://automationexercise.com/payment
- Action: `fill` | Target: Name on Card input
- Action: `fill` | Target: Card Number input
- Action: `fill` | Target: CVC input
- Action: `fill` | Target: Expire Month input
- Action: `fill` | Target: Expire Year input
- Action: `click` | Target: Pay and Confirm Order button