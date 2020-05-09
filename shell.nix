with (import (builtins.fetchTarball {
  # Descriptive name to make the store path easier to identify
  name = "graphql-dsl-python38";
  # Commit hash for nixos-unstable as of 2019-10-27
  url = https://github.com/NixOS/nixpkgs-channels/archive/f601ab37c2fb7e5f65989a92df383bcd6942567a.tar.gz;
  # Hash obtained using `nix-prefetch-url --unpack <url>`
  sha256 = "0ikhcmcc29iiaqjv5r91ncgxny2z67bjzkppd3wr1yx44sv7v69s";
}) {});

let macOsDeps = with pkgs; stdenv.lib.optionals stdenv.isDarwin [
    darwin.apple_sdk.frameworks.CoreServices
    darwin.apple_sdk.frameworks.ApplicationServices
];

in

# Make a new "derivation" that represents our shell
stdenv.mkDerivation {
    name = "graphql-dsl38";

    # The packages in the `buildInputs` list will be added to the PATH in our shell
    # Python-specific guide:
    # https://github.com/NixOS/nixpkgs/blob/master/doc/languages-frameworks/python.section.md
    buildInputs = [
        # see https://nixos.org/nixos/packages.html
        # Python distribution
        cookiecutter
        python38Full
        python38Packages.virtualenv
        python38Packages.wheel
        python38Packages.twine
        taglib
        ncurses
        libxml2
        libxslt
        libzip
        zlib
        libressl

        libuv
        postgresql
        # root CA certificates
        cacert
        which
    ] ++ macOsDeps;
    shellHook = ''
        # Set SOURCE_DATE_EPOCH so that we can use python wheels.
        # This compromises immutability, but is what we need
        # to allow package installs from PyPI
        export SOURCE_DATE_EPOCH=$(date +%s)

        VENV_DIR=$PWD/.venv

        export PATH=$VENV_DIR/bin:$PATH
        export PYTHONPATH=""
        export LANG=en_US.UTF-8

        export PIP_CACHE_DIR=$PWD/.local/pip-cache

        # Setup virtualenv
        if [ ! -d $VENV_DIR ]; then
            virtualenv $VENV_DIR
            $VENV_DIR/bin/python -m pip install -r requirements/minimal.txt
            $VENV_DIR/bin/python -m pip install -r requirements/local.txt
            $VENV_DIR/bin/python -m pip install -r requirements/test.txt
        fi

        # Dirty fix for Linux systems
        # https://nixos.wiki/wiki/Packaging/Quirks_and_Caveats
        export LD_LIBRARY_PATH=${stdenv.cc.cc.lib}/lib/:$LD_LIBRARY_PATH
    '';
}