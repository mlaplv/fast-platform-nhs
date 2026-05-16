# Checkout Price Misrepresentation & Integrity Audit

- [x] Analyze discrepancy between Subtotal (600k) and Final Total (660k) in Order Tracker.
- [x] Audit `PricingEngine` and `PromotionService` voucher calculations for negative value bugs.
- [x] Investigate actual DB record for Order `#825718` to trace the source of the 60,000 VND.
- [x] Fix hardcoded "Miễn phí" strings on the Success/Tracker page to reflect actual metadata `shipping_fee`.
- [x] Update `DeliveryPaymentSection.svelte` on the Checkout page to display dynamic shipping fee instead of misleading "Miễn phí toàn quốc".
