#!/bin/bash
# reset_edgeap.sh
# Fixes/restarts EdgeAP hotspot for ESP32S3 compatibility

SSID="EdgeAP"
PASSWORD="CAV2007smart"

echo "[*] Resetting WiFi hotspot: $SSID"

# Make sure the connection exists
if ! sudo nmcli connection show "$SSID" &>/dev/null; then
  echo "[!] No existing connection named $SSID found. Creating it..."
  sudo nmcli device wifi hotspot ifname wlan0 ssid "$SSID" password "$PASSWORD"
fi

# Apply ESP32-safe settings
sudo nmcli connection modify "$SSID" \
  ipv4.method shared \
  802-11-wireless.mode ap \
  802-11-wireless.band bg \
  802-11-wireless.channel 6 \
  wifi-sec.key-mgmt wpa-psk \
  802-11-wireless-security.proto rsn \
  802-11-wireless-security.group ccmp \
  802-11-wireless-security.pairwise ccmp

# Restart the AP
sudo nmcli connection down "$SSID" &>/dev/null
sudo nmcli connection up "$SSID"

echo "[*] Hotspot $SSID restarted with WPA2-CCMP and shared DHCP."
