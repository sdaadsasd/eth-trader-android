[app]
title = ETH交易助手
package.name = ethtrader
package.domain = org.eth
version = 5.1
source.dir = .
source.main = main.py
requirements = python3,kivy==2.2.1,requests,numpy
orientation = portrait
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.accept_sdk_license = true

[buildozer]  # ← 这里是关键！
log_level = 2
