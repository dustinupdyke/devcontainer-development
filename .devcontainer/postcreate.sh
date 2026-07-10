#!/usr/bin/env bash
set -euo pipefail

# One-time provisioning. Runs once at container create and survives stop/start,
# so durable, filesystem-level setup belongs here.

echo ""
echo "========================================="
echo "Installing Microsoft Aspire..."
echo "========================================="
curl -sSL https://aspire.dev/install.sh | bash

# The installer drops the CLI in ~/.aspire/bin, which isn't on PATH yet in this shell.
export PATH="$HOME/.aspire/bin:$PATH"

# Single-file apphost.cs discovery is gated behind this feature flag (default off).
aspire config set features.singlefileAppHostEnabled true

echo ""
echo "========================================="
echo "Setup completed successfully!"
echo "========================================="
