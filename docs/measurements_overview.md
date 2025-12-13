# Measurements / Safety Cover & Liner Pack

This pack adds capabilities, skills, workflows, plugins, and CLI helpers for analyzing safety cover and liner measurements (AB plots, depth/breakline data, manufacturing risk).

## Capabilities
- `measurement_ocr`, `ab_plot_parse`, `shape_classification`, `breakline_validation`, `measurement_gap_detection`, `depth_profile_analysis`, `manufacturing_risk_assessment`, `cover_layout_planning`, `liner_cut_profile_estimation`.
- Automation pack additions: `measurement_table_parse`, `ab_point_extraction`, `boundary_inference`, `slope_estimation`, `risk_assessment`, `manufacturing_readiness`, `measurement_normalization`, `fitment_check`.

## Skills
- `skill_measurement_ocr`, `skill_ab_plot_parse`, `skill_pool_shape_analyzer`, `skill_breakline_validator`, `skill_manufacturing_risk_assessor`.

## Workflows
- DSL: `safety_cover_measurement_review.dsl.yaml`, `liner_measurement_review.dsl.yaml`.
- Wrappers: `godman_ai/workflows/measurements.py` with helpers for cover and liner reviews.

## Plugins
- Tolerance rules, fixup rules, and shape hints (`examples/plugins/measurements/*`).

## CLI
- `godman measures cover review <path>` and `godman measures liner review <path>` with optional `--out` report generation.

All behavior is offline/mocked; integrates with the capability mesh but remains optional.
