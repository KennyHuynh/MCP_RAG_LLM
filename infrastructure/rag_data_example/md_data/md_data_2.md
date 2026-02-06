# FLOW_ID: PAYMENT_PROCESS_001
Description: Process from login to payment.

## STEP 1: LOGIN_STAGE
- Target URL: User is at https://demo.testarchitect.com/my-account/
- Action: `fill` | Target: Username input | Value: "loc.huynh@agest.vn"
- Action: `fill` | Target: Password input | Value: "1" input
- Action: `click` | Target: Login button

## STEP 2: ADD_TO_CART_STAGE
- Target URL: User is at https://demo.testarchitect.com/shop/
- Action: `click` | Target: Add To Cart link

## STEP 3: PAYMENT STAGE
- Target URL: User is at https://demo.testarchitect.com/checkout/
- Action: `fill` | Target: First name input
- Action: `fill` | Target: Last name input
- Action: `select` | Target: Country select
- Action: `fill` | Target: Address input
- Action: `fill` | Target: City input
- Action: `select` | Target: State select
- Action: `fill` | Target: Postcode input
- Action: `fill` | Target: Phone input
- Action: `click` | Target: Place Order button