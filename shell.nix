{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python312; # pinned to 3.12 for broader compatibility with dependencies
  venv = python.withPackages (ps: with ps; [ pip setuptools wheel ]);
in
pkgs.mkShell {
  name = "node-tts-workers-shell";

  buildInputs = [ 
    venv 
    pkgs.curl 
    pkgs.git 
    pkgs.jq ]; 

  shellHook = ''
    # Create and activate a venv at .venv if it doesn't exist
    if [ ! -d .venv ]; then
      echo "Creating virtualenv in .venv using ${python.interpreter}";
      ${python.interpreter} -m venv .venv
      .venv/bin/pip install --upgrade pip setuptools wheel
      if [ -f shared/requirements-base.txt ]; then
        echo "Installing pinned requirements from shared/requirements-base.txt..."
        .venv/bin/pip install -r shared/requirements-base.txt
      fi
    fi
    # Activate venv for the shell session
    source .venv/bin/activate
    export VIRTUAL_ENV="$PWD/.venv"
    export PATH="$VIRTUAL_ENV/bin:$PATH"
    echo "Activated .venv (Python $(python --version 2>&1))"
  '';

  # Optionally provide a small help message
  description = ''
    Development shell for workers. A Python virtualenv will be created at .venv
    and pinned packages from shared/requirements-base.txt will be installed.
  '';
}
