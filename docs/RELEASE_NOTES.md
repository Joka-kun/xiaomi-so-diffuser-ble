# Xiaomi SO Diffuser BLE — v1.0.4

Home Assistant icon legibility and product fidelity update.

## Changes

- Redrew the compact integration icon with a **transparent background and close-cropped SO S5** based on [Xiaomi's official reference](https://home.mi.com/views/deviceReset.html?locale=en&model=bwj.diffuser.s5): off-white rounded case, large black circular display, thin champagne-metal rim and small lower-right button.
- Removed the pale blue tile, fake mist and decorative Bluetooth emblem. Added a defined grey body outline to preserve contrast on both light and dark Home Assistant cards, especially at 32–48 pixels.
- Removed the unused panoramic `logo.png` and `logo@2x.png`. Home Assistant automatically falls back to the square integration icon when no distinct logo is provided, as described in its [branding specification](https://contributors.home-assistant.io/core/integrations/brands/).
- Updated the editable SVG and deterministic 256/512-pixel PNG build. CI verifies pixel equality and transparent corners.
- The GitHub README hero, author-provided four-step infographic and the Bluetooth device implementation remain unchanged.

## Update

Update the custom **Xiaomi SO Diffuser BLE** integration in HACS to **v1.0.4**. Restart Home Assistant if prompted and hard-refresh the browser tab if the old icon is cached. This is an installed-integration brand image; the pre-install Marketplace catalog has a separate image index.

No BLE protocol, Xiaomi OAuth, device entities or automations changed from v1.0.3. Physical regression on this exact release remains unverified. Non-S5 SO models remain experimental.

Independent community integration, not affiliated with Xiaomi or Home Assistant.
