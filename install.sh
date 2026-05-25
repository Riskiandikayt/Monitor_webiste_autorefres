#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#   W E B M O N I T O R  —  Installer Script
#   Termux Auto-Setup  |  v2.0 ELITE
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'
TICK="${GREEN}✔${RESET}"
CROSS="${RED}✘${RESET}"
ARROW="${CYAN}›${RESET}"

print_banner() {
    clear
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo " ██╗    ██╗███████╗██████╗ ███╗   ███╗ ██████╗ ███╗   ██╗██╗████████╗ ██████╗ ██████╗ "
    echo " ██║    ██║██╔════╝██╔══██╗████╗ ████║██╔═══██╗████╗  ██║██║╚══██╔══╝██╔═══██╗██╔══██╗"
    echo " ██║ █╗ ██║█████╗  ██████╔╝██╔████╔██║██║   ██║██╔██╗ ██║██║   ██║   ██║   ██║██████╔╝"
    echo " ██║███╗██║██╔══╝  ██╔══██╗██║╚██╔╝██║██║   ██║██║╚██╗██║██║   ██║   ██║   ██║██╔══██╗"
    echo " ╚███╔███╔╝███████╗██████╔╝██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║   ██║   ╚██████╔╝██║  ██║"
    echo "  ╚══╝╚══╝ ╚══════╝╚═════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝"
    echo -e "${RESET}"
    echo -e "  ${MAGENTA}${BOLD}◆  24/7 Website Monitor  ◆  Auto-Installer  ◆  Termux Edition  ◆${RESET}"
    echo ""
    echo -e "  ${DIM}─────────────────────────────────────────────────────────────${RESET}"
    echo ""
}

step() {
    echo -e "  ${ARROW} ${BOLD}$1${RESET}"
}

ok() {
    echo -e "  ${TICK} ${GREEN}$1${RESET}"
}

fail() {
    echo -e "  ${CROSS} ${RED}$1${RESET}"
}

warn() {
    echo -e "  ${YELLOW}⚠  $1${RESET}"
}

spinner() {
    local pid=$1
    local msg=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        printf "  ${CYAN}${spin:$i:1}${RESET}  %s...\r" "$msg"
        sleep 0.1
    done
    printf "%-50s\r" ""
}

print_banner

# ── Check Termux ──────────────────────────────────────────────
echo -e "  ${BOLD}[1/6] Checking environment...${RESET}"
if [ -d "/data/data/com.termux" ]; then
    ok "Termux environment detected"
else
    warn "Not running in Termux — some features may differ"
fi

# ── Update pkg ────────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}[2/6] Updating package index...${RESET}"
(pkg update -y -q 2>&1) &
spinner $! "Updating packages"
ok "Package index updated"

# ── Install Python ────────────────────────────────────────────
echo ""
echo -e "  ${BOLD}[3/6] Installing Python...${RESET}"
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    ok "Python already installed: $PY_VER"
else
    step "Installing python..."
    (pkg install python -y -q 2>&1) &
    spinner $! "Installing Python"
    if command -v python3 &>/dev/null; then
        ok "Python installed successfully"
    else
        fail "Python installation failed"
        echo -e "  ${DIM}Try: pkg install python${RESET}"
        exit 1
    fi
fi

# ── Install pip packages ──────────────────────────────────────
echo ""
echo -e "  ${BOLD}[4/6] Installing Python dependencies...${RESET}"

PACKAGES=("requests" "beautifulsoup4" "rich" "lxml")
for pkg_name in "${PACKAGES[@]}"; do
    step "Installing ${pkg_name}..."
    (pip install --quiet "$pkg_name" 2>&1) &
    spinner $! "pip install $pkg_name"
    ok "${pkg_name} installed"
done

# ── Make executable ───────────────────────────────────────────
echo ""
echo -e "  ${BOLD}[5/6] Setting permissions...${RESET}"
chmod +x monitor.py 2>/dev/null
ok "monitor.py is now executable"

# ── Create alias (optional) ───────────────────────────────────
echo ""
echo -e "  ${BOLD}[6/6] Setting up shortcut...${RESET}"
MONITOR_PATH="$(pwd)/monitor.py"
SHELL_RC="$HOME/.bashrc"
[ -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.zshrc"

ALIAS_LINE="alias webmonitor='python3 ${MONITOR_PATH}'"
if ! grep -q "alias webmonitor" "$SHELL_RC" 2>/dev/null; then
    echo "$ALIAS_LINE" >> "$SHELL_RC"
    ok "Alias 'webmonitor' added to $SHELL_RC"
else
    ok "Alias already exists in $SHELL_RC"
fi

# ── Done ──────────────────────────────────────────────────────
echo ""
echo -e "  ${DIM}─────────────────────────────────────────────────────────────${RESET}"
echo ""
echo -e "  ${GREEN}${BOLD}Installation complete!${RESET}"
echo ""
echo -e "  ${CYAN}How to run:${RESET}"
echo -e "    ${ARROW} ${BOLD}python3 monitor.py${RESET}           ${DIM}# Normal mode${RESET}"
echo -e "    ${ARROW} ${BOLD}webmonitor${RESET}                    ${DIM}# After reloading shell${RESET}"
echo -e "    ${ARROW} ${BOLD}nohup python3 monitor.py &${RESET}   ${DIM}# Background mode${RESET}"
echo ""
echo -e "  ${YELLOW}Background mode (Termux):${RESET}"
echo -e "    ${ARROW} Acquire wakelock:  ${BOLD}termux-wake-lock${RESET}"
echo -e "    ${ARROW} Run background:    ${BOLD}nohup python3 monitor.py > output.log 2>&1 &${RESET}"
echo -e "    ${ARROW} Check process:     ${BOLD}ps aux | grep monitor${RESET}"
echo -e "    ${ARROW} Kill process:      ${BOLD}kill \$(pgrep -f monitor.py)${RESET}"
echo ""
echo -e "  ${DIM}Reload shell to activate alias: source $SHELL_RC${RESET}"
echo ""
echo -e "  ${DIM}─────────────────────────────────────────────────────────────${RESET}"
echo ""
