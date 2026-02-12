# ============================================================================
# Stage 1: Builder — Compile dependencies using pip-compile
# ============================================================================
FROM python:3.14-bookworm as builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pip-compile
RUN pip install --no-cache-dir pip-tools>=7.0.0

WORKDIR /build

# Copy pyproject.toml to compile dependencies
COPY pyproject.toml .

# Compile runtime dependencies directly from pyproject.toml
RUN pip-compile \
    --resolver=backtracking \
    --output-file=requirements.txt \
    pyproject.toml

# Compile development dependencies (runtime + dev extras)
RUN pip-compile \
    --resolver=backtracking \
    --output-file=requirements-dev.txt \
    --extra=dev \
    pyproject.toml

# ============================================================================
# Stage 2: Deps — Pre-compile wheels (includes C extensions like pyswisseph)
# ============================================================================
FROM python:3.14-bookworm as deps

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy compiled requirements from builder
COPY --from=builder /build/requirements.txt .
COPY --from=builder /build/requirements-dev.txt .

# Create /wheels directory and compile all wheels (prod + dev)
RUN mkdir -p /wheels \
    && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt \
    && pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements-dev.txt

# ============================================================================
# Stage 3: Base — Shared foundation (Python, deps, user)
# ============================================================================
FROM python:3.14-bookworm as base

ENV PYTHONUNBUFFERED=1

# USER arg is passed from devcontainer.json build.args to match the host user.
# This ensures file permissions work correctly when mounting volumes.
ARG USER_UID=1000
ARG USER_GID=1000
ARG USER=non_root_user

# Install minimal system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid ${USER_GID} hdgroup \
    && useradd --uid ${USER_UID} --gid ${USER_GID} --create-home --shell /bin/bash ${USER}

# Copy pre-built wheels from deps stage
COPY --from=deps /wheels /wheels

# Copy compiled requirements and install from pre-built wheels
# Note: --no-index removed to allow fallback to PyPI for any missing deps
COPY --from=builder /build/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --find-links=/wheels -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER ${USER}
WORKDIR /home/${USER}

# ============================================================================
# Stage 4: Runtime — Lambda-compatible production image
# ============================================================================
FROM base as runtime

USER root

# Install AWS Lambda Runtime Interface Client and Mangum (ASGI adapter)
RUN pip install --no-cache-dir awslambdaric mangum

# Copy application code
COPY pyproject.toml /app/
COPY src/ /app/src/
COPY lambda/handler.py /app/

WORKDIR /app

# Install the human-design package itself (no deps, they're already installed)
RUN pip install --no-cache-dir --no-deps .

# Set up PYTHONPATH so awslambdaric can resolve handler.handler
ENV PYTHONPATH=/app:$PYTHONPATH

# Lambda handler entrypoint
ENTRYPOINT ["python", "-m", "awslambdaric"]
CMD ["handler.handler"]

# ============================================================================
# Stage 5: Dev — Full development environment with build tools
# ============================================================================
FROM base as dev

# Re-declare ARG to make it available in this stage
ARG USER

USER root

# Install additional build tools for development and sudo for the non-root user
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        sudo \
    && rm -rf /var/lib/apt/lists/* \
    && echo "${USER} ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/${USER} \
    && chmod 0440 /etc/sudoers.d/${USER}

# Copy compiled dev requirements from builder
COPY --from=builder /build/requirements-dev.txt /tmp/requirements-dev.txt

# Copy wheels from deps stage for dev dependencies
COPY --from=deps /wheels /wheels

# Install dev dependencies from pre-built wheels
# Note: --no-index removed to allow fallback to PyPI for any missing deps
RUN pip install --no-cache-dir --find-links=/wheels -r /tmp/requirements-dev.txt \
    && rm /tmp/requirements-dev.txt /wheels -rf

USER ${USER}
WORKDIR /home/${USER}
