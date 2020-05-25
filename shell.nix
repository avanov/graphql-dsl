{
    pkgs ? import (builtins.fetchTarball {
               # https://nixos.wiki/wiki/FAQ/Pinning_Nixpkgs
               # Descriptive name to make the store path easier to identify
               name   = "nixpkgs-unstable-2021-01-20";
               url    = https://github.com/NixOS/nixpkgs/archive/92c884dfd7140a6c3e6c717cf8990f7a78524331.tar.gz;
               # hash obtained with `nix-prefetch-url --unpack <archive>`
               sha256 = "0wk2jg2q5q31wcynknrp9v4wc4pj3iz3k7qlxvfh7gkpd8vq33aa";
           }) {}
,   pyVersion ? "39"
,   isDevEnv  ? true
}:

let
    macOsDeps = with pkgs; stdenv.lib.optionals stdenv.isDarwin [
        darwin.apple_sdk.frameworks.CoreServices
        darwin.apple_sdk.frameworks.ApplicationServices
    ];
    python = pkgs."python${pyVersion}Full";
    pythonPkgs = pkgs."python${pyVersion}Packages";
    devLibs = if isDevEnv then [ pythonPkgs.twine pythonPkgs.wheel ] else [ pythonPkgs.coveralls ];

in

# Make a new "derivation" that represents our shell
pkgs.stdenv.mkDerivation {
    name = "graphql-dsl39";

    # The packages in the `buildInputs` list will be added to the PATH in our shell
    # Python-specific guide:
    # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md
    buildInputs = with pkgs; [
        # see https://nixos.org/nixos/packages.html
        # Python distribution
        python
        pythonPkgs.virtualenv
        pythonPkgs.wheel
        pythonPkgs.twine
        taglib
        ncurses
        libxml2
        libxslt
        libzip
        zlib
        openssl

        # root CA certificates
        cacert
        which
    ] ++ macOsDeps;
    shellHook = ''
        # Set SOURCE_DATE_EPOCH so that we can use python wheels.
        # This compromises immutability, but is what we need
        # to allow package installs from PyPI
        export SOURCE_DATE_EPOCH=$(date +%s)

        export VENV_DIR="$PWD/.venv${pyVersion}"

        export PATH=$VENV_DIR/bin:$PATH
        export PYTHONPATH=""
        export LANG=en_US.UTF-8

        export PIP_CACHE_DIR="$PWD/.local/pip-cache${pyVersion}"

        # Setup virtualenv
        if [ ! -d $VENV_DIR ]; then
            virtualenv $VENV_DIR
            $VENV_DIR/bin/python -m pip install -r requirements/minimal.txt
            $VENV_DIR/bin/python -m pip install -r requirements/local.txt
            $VENV_DIR/bin/python -m pip install -r requirements/test.txt
        fi

        # Dirty fix for Linux systems
        # https://nixos.wiki/wiki/Packaging/Quirks_and_Caveats
        export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib/:$LD_LIBRARY_PATH
    '';
}