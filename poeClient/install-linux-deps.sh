#!/usr/bin/env bash
# Install Linux dependencies for PoE Archipelago client
# Required: xdotool (key injection into XWayland for Proton/PoE)
# Optional: xprop (focus detection — usually pre-installed)

set -e

install_pkg() {
  local pkg="$1"
  local aur_pkg="${2:-$pkg}"

  if command -v pacman &>/dev/null; then
    echo "Arch: installing $pkg"
    sudo pacman -S --needed --noconfirm "$pkg"
  elif command -v apt-get &>/dev/null; then
    echo "Debian/Ubuntu: installing $pkg"
    sudo apt-get install -y "$pkg"
  elif command -v dnf &>/dev/null; then
    echo "Fedora: installing $pkg"
    sudo dnf install -y "$pkg"
  elif command -v zypper &>/dev/null; then
    echo "openSUSE: installing $pkg"
    sudo zypper install -y "$pkg"
  else
    echo "Unknown distro — install '$pkg' manually"
    return 1
  fi
}

echo "=== PoE Archipelago Linux dependency installer ==="

# xdotool: key injection into XWayland (required for sending commands to PoE)
if command -v xdotool &>/dev/null; then
  echo "xdotool: already installed ($(xdotool --version 2>&1 | head -1))"
else
  echo "xdotool: not found — installing..."
  install_pkg xdotool
fi

# xprop: active window title detection (usually pre-installed with X11 utils)
if command -v xprop &>/dev/null; then
  echo "xprop:   already installed"
else
  echo "xprop: not found — installing..."
  if command -v pacman &>/dev/null; then
    install_pkg xorg-xprop
  elif command -v apt-get &>/dev/null; then
    install_pkg x11-utils
  else
    install_pkg xprop
  fi
fi

echo ""
echo "Done. Run the PoE Archipelago client normally."
echo "If PoE is on a different X display, set DISPLAY=:N before launching."
