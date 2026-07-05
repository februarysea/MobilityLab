# MobilityLab Examples

These examples are intended as runnable reference projects for MobilityLab users.
Each example should show one framework capability with the smallest useful
scenario and a reproducible run command.

Examples that export visualization artifacts can be opened with the replay
viewer by pointing `MOBILITYLAB_RUN_DIR` at the completed run directory:

```bash
MOBILITYLAB_RUN_DIR=/path/to/run npm --prefix apps/visualization run dev
```

Relative `MOBILITYLAB_RUN_DIR` values are resolved from the directory where the
`npm` command is invoked.

## Learning Path

1. `basic/minimal_commute`
   - Build a small network, facilities, population, and activity plan.
   - Show both YAML config and Python API construction.
   - Run the full experiment stack.
   - Write metrics, events, replay artifacts, and visualization-ready datasets.

Planned next examples:

1. `traffic_assignment/pigou_network`
   - OD demand, route alternatives, flow-dependent link cost, and static
     assignment.
2. `traffic_assignment/braess_network`
   - Network intervention variants and baseline/intervention comparison.
3. `dynamic_traffic/vickrey_bottleneck`
   - Capacity, queueing, and departure-time dynamics.
