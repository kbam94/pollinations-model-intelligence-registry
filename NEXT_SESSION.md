# Next Session

Current project version: 0.8.0.

1. Launch the interactive menu: `python menu.py`.
2. Browse local catalog snapshots with: `python catalog.py list --all-snapshots`.
3. Compare the two newest local snapshots with: `python catalog.py diff`.
4. Use `python catalog.py diff --format json` for machine-readable change reports.
5. Prepare/import at least two real, provenance-documented catalog snapshots before expecting meaningful change reports.
6. Next development milestone: verify the current official Pollinations public catalog endpoint and response schema before implementing an explicitly triggered, unauthenticated metadata fetch.
7. Any future public fetch must have strict time/size limits, validate the response, record source and timestamp, and never run automatically.
8. Continue to avoid live inference unless an individual Quest-only test is deliberately approved. No paid-enabled key, Paid Pollen, or top-ups.

All catalog comparison work is offline. No live inference or Pollen spending is needed for the next development milestone.
