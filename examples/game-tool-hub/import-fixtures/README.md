# Authored saved-report format fixtures

All numbers here are synthetic format examples, not captured game results or
evidence about tool costs. The importer intentionally classifies these source
formats as imported rendering summaries with missing runtime/UTC/configuration
evidence. It does not turn fixture filenames into trusted FG or measurement PASS.

- `cyberpunk-summary.example.json`: minimal `worldBenchmarkSummary` shape observed
  in a local Cyberpunk 2077 2.31 export. `gpuMemory`/`systemMemory` are capacity
  metadata, not consumption. Native FG fields are requested settings only.
- `presentmon-stats.example.csv`: nine-column PresentMon GUI stats writer shape
  reviewed at v2.6.0; the CSV itself does not embed that provider version.
- `presentmon-no-animation-stats.example.csv`: recognized missing-comma `00`
  animation tail. Only the first seven columns have an unambiguous mapping.
- `presentmon-zero-stats.example.csv`: recognized zero-count eight-zero writer
  row. FPS placeholders remain unavailable rather than measured zero FPS.

No provider binary, copyrighted report, personal path, native profile or raw trace
is included. PresentMon percentile summaries retain the provider's reciprocal
interpolated frame-time percentile definition, not a mean-of-slowest-frames low.
