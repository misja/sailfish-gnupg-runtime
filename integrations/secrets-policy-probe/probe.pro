TEMPLATE = app
TARGET = secrets-policy-probe
QT -= gui
QT += core dbus
CONFIG += link_pkgconfig c++11
PKGCONFIG += sailfishsecrets
INCLUDEPATH += /usr/include/Sailfish
SOURCES += probe.cpp
