FROM python:3.12-slim-bookworm AS sources

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG FDE_GYM_REV=1d9ed027af7c8312bacb1abad1467c87a91c004b
ARG FDE_CASES_REV=10fee70cdb7e4010ea9b301359550d930b0de267

RUN git init /source/fde-gym \
    && git -C /source/fde-gym fetch --depth=1 https://github.com/deeplethe/fde-gym.git "$FDE_GYM_REV" \
    && git -C /source/fde-gym archive FETCH_HEAD LICENSE harness | tar -x -C /source/fde-gym \
    && git init /source/examples \
    && git -C /source/examples fetch --depth=1 https://huggingface.co/datasets/DeepLethe/FDE-Gym-examples "$FDE_CASES_REV" \
    && git -C /source/examples archive FETCH_HEAD cases/oncall_incident | tar -x -C /source/examples

FROM python:3.12-slim-bookworm

ENV FDEGYM_ENGAGEMENTS=/opt/fde-gym-private/cases \
    FDEGYM_RUNS=/opt/fde-gym-private/runs \
    FDEGYM_OPENROUTER_KEY_FILE=/opt/fde-gym-private/openrouter_key \
    FDEGYM_DELIVERED_UID=10002 \
    FDE_TASK_RUN=harbor \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl xz-utils \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 fde-agent \
    && useradd --uid 10002 fde-delivery \
    && install -d -m 0700 /opt/fde-gym-private

COPY --from=sources /source/fde-gym/harness /opt/fde-gym-private/harness
COPY --from=sources /source/fde-gym/LICENSE /opt/fde-gym-private/FDE-GYM-LICENSE
COPY --from=sources /source/examples/cases /opt/fde-gym-private/cases
COPY --chmod=755 tasks/oncall-incident/environment/start-task.sh /usr/local/bin/start-fde-task
COPY --chmod=755 tasks/oncall-incident/environment/check-ready.py /usr/local/bin/check-fde-task-ready

COPY shared/harbor_security.py shared/verify.py /opt/fde-gym-private/harness/
COPY shared/patch_upstream.py /tmp/fde-patch-upstream.py
RUN python3 -I /tmp/fde-patch-upstream.py /opt/fde-gym-private \
    && rm /tmp/fde-patch-upstream.py

WORKDIR /app
