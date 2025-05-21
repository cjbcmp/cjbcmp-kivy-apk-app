[app]
title = StockApp
package.name = stockapp
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = kivy,requests
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 29
android.ndk = 25b
android.minapi = 21
android.gradle_dependencies = com.android.support:appcompat-v7:28.0.0

[buildozer]
log_level = 2
warn_on_root = 0
