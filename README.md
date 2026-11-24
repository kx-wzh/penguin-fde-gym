# FDE-Gym public examples for PenguinHarness

This repository provides three independent Harbor tasks at the original FDE-Gym L3 instruction level.

| Harbor task | FDE-Gym engagement | Simulator model use |
| --- | --- | --- |
| `oncall-incident` | `oncall_incident` | Stakeholder questions and the customer gateway. The unchanged system can be scored without a model. |
| `campus-booking` | `campus_booking` | Stakeholder questions, the customer gateway, and simulated users during grading. |
| `robot-cell-rollout` | `robot_cell_rollout` | Stakeholder questions. The unchanged plan can be scored without a model. |

The Docker builds fetch [FDE-Gym harness 1.3.0](https://github.com/deeplethe/fde-gym/tree/1d9ed027af7c8312bacb1abad1467c87a91c004b) and the [public examples](https://huggingface.co/datasets/DeepLethe/FDE-Gym-examples/tree/10fee70cdb7e4010ea9b301359550d930b0de267). The upstream harness is Apache-2.0. The example data card specifies CC BY-NC 4.0. Each image downloads its own example from Hugging Face.

## Running a task (for agents)

Check out the full commit in the Case statement. Use Docker with Compose v2, uv, and a PenguinHarness model configured in the host Project. Set `ADAPTER_DIR` to the shared adapter directory at the commit stated in the Case. The benchmark repository documents [model setup, adapter installation, and trial handling](https://github.com/Prism-Shadow/penguin-harness-benchmark/blob/b44bb87feba731a9e342a9054b2d8641f48e589c/README.md#running-a-task-for-agents).

Before a full evaluation, the operator configures the FDE-Gym simulator separately on the machine running PenguinHarness and Harbor. For example, with DeepSeek's API:

```bash
export FDEGYM_LLM_URL=https://api.deepseek.com/chat/completions
export FDEGYM_MODEL=deepseek-flash
export FDEGYM_MODEL_KEY_FILE=/absolute/private/path/to/deepseek.key
```

The key file contains the key on one line and should have mode `0600`. Keep it outside the checkouts and logs. Compose reads the host path and mounts the file read-only in the container's private FDE-Gym directory. Set these variables before starting the PenguinHarness service when using the Evaluation Center. For OpenRouter, use its Chat Completions endpoint and model ID instead. Record the simulator endpoint and model alongside the tested agent and its model.

Run the Case's command from this repository root. The task names in the command are Harbor names. FDE-Gym resolves the original engagement ID when the task starts. Each command runs the original generated L3 instructions with no time-management prompt. The Harbor job writes its verifier report to the specified jobs directory.

### No-op checks

Use the same Harbor version to run a trial without a tested agent or its model configuration:

```bash
uvx --from harbor==0.23.0 harbor run -p tasks -i oncall-incident -a nop -k 1 -n 1 -y
uvx --from harbor==0.23.0 harbor run -p tasks -i robot-cell-rollout -a nop -k 1 -n 1 -y
```

A no-op run of `campus-booking` still needs the simulator configuration. Its verifier uses the simulator to generate customer replies.

## Scoring

The verifier saves the full official FDE-Gym report as `verifier/fde-result.json`. Harbor's `reward` is `uplift_net` limited to the inclusive range 0–1, so the Evaluation Center can display `100 × reward`. The raw report keeps negative and above-range scores, the unadjusted uplift, and the contact cost. A failed verifier or campus simulator error produces no reward and should be reported as a failed evaluation.
