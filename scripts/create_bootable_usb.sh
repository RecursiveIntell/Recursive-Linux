#!/bin/bash
# Intentionally quarantined: hardware-media writes require a separate,
# device-identity-bound approval and a production-safe installer artifact.
set -u

printf '%s\n' \
  'BLOCKED: direct hardware-media creation is quarantined.' \
  'This project currently has only a verified disposable-VM installer path.' \
  'Do not promote a test Kickstart or write any block device from this script.' \
  'Required first: recovery closure, versioned source, production artifact review,' \
  'media identity receipt, and explicit approval naming the exact target device.'
exit 2
