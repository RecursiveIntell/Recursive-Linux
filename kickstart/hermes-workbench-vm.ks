# Hermes Workbench OS v0.2 — disposable VM test profile
# INTENTIONALLY INSECURE PUBLIC TEST CREDENTIAL: root:hwostest
# Isolated/NAT VM testing only. Never use this fixture on hardware, a bridged
# network, an externally reachable guest, or any persistent system.
text
lang en_US.UTF-8
keyboard us
timezone America/New_York --utc
network --bootproto=dhcp --device=link --activate
firewall --enabled
selinux --enforcing
bootloader --location=mbr --boot-drive=vda --append="pcie_aspm=off"
services --enabled="NetworkManager,firewalld,sshd"
zerombr
clearpart --all --initlabel --drives=vda
autopart --type=plain
rootpw --plaintext hwostest
firstboot --disabled
%packages --excludedocs --inst-langs=en_US
@core
@hardware-support
kernel
kernel-modules
linux-firmware
amd-ucode-firmware
amd-gpu-firmware
realtek-firmware
NetworkManager
NetworkManager-wifi
wpa_supplicant
firewalld
bluez
bluez-tools
pipewire
pipewire-alsa
pipewire-pulseaudio
wireplumber
sddm
plasma-desktop
plasma-workspace
plasma-nm
plasma-pa
powerdevil
kwin
xorg-x11-server-Xwayland
xdg-desktop-portal
xdg-desktop-portal-kde
polkit-kde
qt6-qtwayland
konsole
dolphin
ark
spectacle
kio-extras
kde-gtk-config
btrfs-progs
cryptsetup
tpm2-tools
clevis
clevis-luks
fwupd
smartmontools
nvme-cli
openssh-clients
openssh-server
git
curl
jq
rsync
restic
rclone
podman
toolbox
fuse-overlayfs
slirp4netns
qemu-guest-agent
tlp
tlp-pd
-power-profiles-daemon
lm_sensors
iputils
util-linux
systemd-oomd-defaults
zram-generator-defaults
usbutils
pciutils
lsof
strace
bash-completion
vim-minimal
-anaconda-webui
%end

# @HWOS_INSTALL_OVERLAY@

%post --erroronfail --log=/root/hwos-post.log
set -eu
systemctl set-default graphical.target
systemctl enable sshd.service
# Chrome, Tailscale, Hermes, repository overlays, secrets, and experimental
# runtime policy are admitted by the signed post-install bundle, not fetched
# by an unaudited installer script.
%end

reboot
