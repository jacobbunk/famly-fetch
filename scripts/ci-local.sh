#!/usr/bin/env bash
#
# ci-local.sh - run the GitHub Actions CI workflow (.github/workflows/ci.yml)
# locally using `act`, reproducing the full Python version matrix as
# concurrent container builds.
#
# Requirements: act (brew install act) and a running Docker daemon.

# -e  exit on any error
# -u  treat unset variables as errors
# -o pipefail  a pipeline fails if any command in it fails
set -euo pipefail

# --- locate repo root (script lives in <root>/scripts) ---------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKFLOW=".github/workflows/ci.yml"

# Runner image: the stock catthehacker image act uses has no `node` on PATH,
# which breaks the JS actions (checkout, setup-python) and their post steps.
# ci-local.Dockerfile extends it with Node.js 24; we build that locally and
# point act at it. See ci-local.Dockerfile for details.
RUNNER_DOCKERFILE="ci-local.Dockerfile"
RUNNER_IMAGE="famly-fetch-act-runner:latest"

# --- defaults --------------------------------------------------------------
EVENT="pull_request"
CONCURRENCY=4
PY_VERSION=""
LIST_ONLY=0
REBUILD=0
# Declared empty up front so the variable exists under `set -u`. Because an
# empty array still trips "unbound variable" on bash 3.2, every expansion of
# it below is guarded by a ${#EXTRA_ARGS[@]} length check.
EXTRA_ARGS=()

usage() {
    # Here-doc avoids fragile sed-over-source-file parsing.
    cat <<'EOF'
ci-local.sh - run the GitHub Actions CI workflow (.github/workflows/ci.yml)
locally using `act`, reproducing the full Python version matrix as
concurrent container builds.

This is a faithful local mirror of "Python CI": it runs the exact same
steps (checkout, setup-python, install deps, ruff check, ruff format
--diff) inside ubuntu containers, one per matrix entry, so failures seen
here match what GitHub reports.

Usage:
  scripts/ci-local.sh                 # run all matrix builds (3.10-3.13)
  scripts/ci-local.sh -v 3.11         # run only the Python 3.11 build
  scripts/ci-local.sh -e push         # use the push event (default: pull_request)
  scripts/ci-local.sh -c 2            # limit concurrent jobs (default: 4)
  scripts/ci-local.sh -l              # list the jobs without running them
  scripts/ci-local.sh -b              # force a rebuild of the runner image
  scripts/ci-local.sh -- --verbose    # pass any extra args straight to act

Options:
  -v, --version VERSION   restrict the matrix to a single Python version
  -e, --event   EVENT     act event trigger (default: pull_request)
  -c, --concurrency N     maximum concurrent jobs (default: 4, must be a number)
  -l, --list              list jobs without running them
  -b, --rebuild           rebuild the local runner image before running
  -h, --help              show this help and exit

Requirements: act (brew install act) and a running Docker daemon.

The workflow runs in a local image (ci-local.Dockerfile) that extends the
catthehacker runner with Node.js, which the stock image lacks. The image is
built automatically on first run; use -b to rebuild it.
EOF
}

# --- arg parsing -----------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version)
            PY_VERSION="${2:?--version requires a value, e.g. 3.11}"
            shift 2
            ;;
        -e|--event)
            EVENT="${2:?--event requires a value, e.g. push}"
            shift 2
            ;;
        -c|--concurrency)
            CONCURRENCY="${2:?--concurrency requires a numeric value}"
            # Reject non-numeric values early so act gets a sensible error.
            if ! [[ "${CONCURRENCY}" =~ ^[0-9]+$ ]]; then
                echo "error: --concurrency requires a positive integer, got: ${CONCURRENCY}" >&2
                exit 2
            fi
            shift 2
            ;;
        -l|--list)
            LIST_ONLY=1
            shift
            ;;
        -b|--rebuild)
            REBUILD=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            EXTRA_ARGS=("$@")
            break
            ;;
        *)
            echo "error: unknown option: $1" >&2
            echo "Run with -h or --help for usage." >&2
            exit 2
            ;;
    esac
done

# --- prerequisite checks ---------------------------------------------------
if ! command -v act >/dev/null 2>&1; then
    echo "error: 'act' is not installed." >&2
    echo "  macOS:  brew install act" >&2
    echo "  Linux:  https://github.com/nektos/act#installation" >&2
    exit 127
fi

# docker info writes to stdout and stderr even on success; suppress both.
if ! docker info >/dev/null 2>&1; then
    echo "error: Docker daemon is not reachable. Start Docker and retry." >&2
    exit 1
fi

# Verify the workflow file exists before handing off to act.
if [[ ! -f "${REPO_ROOT}/${WORKFLOW}" ]]; then
    echo "error: workflow file not found: ${REPO_ROOT}/${WORKFLOW}" >&2
    exit 1
fi

# Verify the runner Dockerfile exists.
if [[ ! -f "${REPO_ROOT}/${RUNNER_DOCKERFILE}" ]]; then
    echo "error: runner Dockerfile not found: ${REPO_ROOT}/${RUNNER_DOCKERFILE}" >&2
    exit 1
fi

# On ARM hosts (Apple silicon "arm64", Linux ARM "aarch64") the act runner
# images are amd64; force the platform for both the build and the run so the
# container matches GitHub's runners instead of falling back to emulation.
PLATFORM_BUILD_ARGS=()
ACT_ARCH_ARGS=()
_arch="$(uname -m)"
if [[ "${_arch}" == "arm64" || "${_arch}" == "aarch64" ]]; then
    PLATFORM_BUILD_ARGS=(--platform linux/amd64)
    ACT_ARCH_ARGS=(--container-architecture linux/amd64)
fi
unset _arch

# --- ensure the Node-enabled runner image exists ---------------------------
# Listing does not run containers, so skip the (slow) build for -l.
if [[ "${LIST_ONLY}" -eq 0 ]]; then
    if [[ "${REBUILD}" -eq 1 ]] || ! docker image inspect "${RUNNER_IMAGE}" >/dev/null 2>&1; then
        echo "==> Building runner image ${RUNNER_IMAGE} from ${RUNNER_DOCKERFILE}"
        docker build "${PLATFORM_BUILD_ARGS[@]}" \
            -f "${REPO_ROOT}/${RUNNER_DOCKERFILE}" \
            -t "${RUNNER_IMAGE}" \
            "${REPO_ROOT}"
    fi
fi

# --- assemble act invocation -----------------------------------------------
# -P maps the workflow's `runs-on: ubuntu-latest` to our local Node-enabled
# image. This overrides the mapping in .actrc.
ACT_ARGS=("${EVENT}" -W "${WORKFLOW}" --concurrent-jobs "${CONCURRENCY}")
ACT_ARGS+=(-P "ubuntu-latest=${RUNNER_IMAGE}")
# Note: --pull=false lives in .actrc so act does not try to force-pull the
# local-only runner image from a registry.
if [[ ${#ACT_ARCH_ARGS[@]} -gt 0 ]]; then
    ACT_ARGS+=("${ACT_ARCH_ARGS[@]}")
fi

# Restrict to a single Python version when requested.
if [[ -n "${PY_VERSION}" ]]; then
    ACT_ARGS+=(--matrix "python-version:${PY_VERSION}")
fi

if [[ "${LIST_ONLY}" -eq 1 ]]; then
    ACT_ARGS+=(--list)
fi

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    ACT_ARGS+=("${EXTRA_ARGS[@]}")
fi

cd "${REPO_ROOT}"

echo "==> Running CI locally via act"
echo "    workflow:    ${WORKFLOW}"
echo "    runner:      ${RUNNER_IMAGE}"
echo "    event:       ${EVENT}"
if [[ -n "${PY_VERSION}" ]]; then
    echo "    matrix:      python-version:${PY_VERSION} (single build)"
else
    echo "    matrix:      3.10, 3.11, 3.12, 3.13 (up to ${CONCURRENCY} concurrent)"
fi
echo "    act:         act ${ACT_ARGS[*]}"
echo

exec act "${ACT_ARGS[@]}"
