# Python package overrides shared between flake.nix and devenv.nix
final: prev: {
  "hatchling" = prev."hatchling".overrideAttrs (old: {
    propagatedBuildInputs = [ final."editables" ];
  });
  "cairocffi" = prev."cairocffi".overrideAttrs (old: {
    postInstall = (old.postInstall or "") + ''
      substituteInPlace $out/lib/python*/site-packages/cairocffi/__init__.py \
        --replace-fail \
          "('libcairo.so.2', 'libcairo.2.dylib', 'libcairo-2.dll')" \
          "('${final.pkgs.cairo}/lib/libcairo.so.2', 'libcairo.so.2', 'libcairo.2.dylib', 'libcairo-2.dll')"
    '';
  });
}
