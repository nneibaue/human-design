# ============================================================================
# Build stage: Compile dependencies using pip-compile
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
# Runtime stage: Minimal production image
# ============================================================================
FROM python:3.14-bookworm as runtime

ENV PYTHONUNBUFFERED=1

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

# Add user dir to PATH
ENV PATH="/home/${USER}/.local/bin:${PATH}"

# Copy compiled requirements from builder
COPY --from=builder /build/requirements.txt /tmp/requirements.txt

# Install all runtime dependencies in a single layer (optimized caching)
RUN pip install --no-cache-dir --user -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER ${USER}
WORKDIR /home/${USER}

# ============================================================================
# Development stage: Full development environment
# ============================================================================
FROM runtime as development

USER root

# Install additional build tools for development
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled dev requirements from builder
COPY --from=builder /build/requirements-dev.txt /tmp/requirements-dev.txt

# Install all dependencies (including dev) in a single layer (optimized caching)
RUN pip install --no-cache-dir --user -r /tmp/requirements-dev.txt \
    && rm /tmp/requirements-dev.txt

USER ${USER}
WORKDIR /home/${USER}