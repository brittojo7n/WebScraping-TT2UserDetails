{ pkgs }: {
  deps = [
    pkgs.glibcLocales
    pkgs.python-launcher
    pkgs.bashInteractive
    pkgs.nodePackages.bash-language-server
    pkgs.man
  ];
}