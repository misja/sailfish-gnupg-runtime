TEMPLATE = app
TARGET = secrets-policy-owner-recovery
QT = core dbus
CONFIG += console c++11 link_pkgconfig
CONFIG -= app_bundle
PKGCONFIG += sailfishsecrets
SOURCES = owner-recovery.cpp
