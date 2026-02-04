# FLOW_ID: CHECKOUT_PROCESS_001
Description: Process from login to payment.

## STEP 1: LOGIN_STAGE
- Target URL: User is at https://demo.testarchitect.com/my-account/
- Action: `fill` | Target: Username or email address * input | Value: "loc.huynh@agest.vn"
- Action: `fill` | Target: Password * input | Value: "1" input
- Action: `click` | Target: Log in button

## STEP 2: ADD_TO_CART_STAGE
- Target URL: User is at https://demo.testarchitect.com/shop
- Action: `click` | Target: Add To Cart button

## STEP 3: PAYMENT STAGE
- Target URL: User is at https://demo.testarchitect.com/checkout/
- Action: `fill` | Target: First Name input
- Action: `fill` | Target: Last Name input
- Action: `select` | Target: Country / Region textbox
- Action: `fill` | Target: Street Address input
- Action: `fill` | Target: Town / City input
- Action: `select` | Target: State textbox
- Action: `fill` | Target: ZIP Code input
- Action: `fill` | Target: Phone input
- Action: `fill` | Target: Email Address input
- Action: `click` | Target: Place Order button