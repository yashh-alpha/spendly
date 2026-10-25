--- 
name: profile-breakdown-spacing
description: Equal spacing between category breakdown rows
metadata:
  type: project
--- 
The category breakdown rows now have consistent spacing between them by adding `margin-bottom: 1rem;` to `.profile-breakdown-row`. This ensures all rows (both visible and hidden) are equally spaced, improving visual consistency.

The layout now:
- Uses a grid template with fixed-width columns for category names, progress bars, and amounts
- Adds a bottom margin to each row to ensure equal vertical spacing
- Maintains the 5-item limit and "Show more" toggle for category breakdowns