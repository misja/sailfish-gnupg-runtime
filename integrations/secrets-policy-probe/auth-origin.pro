TEMPLATE = app
TARGET = secrets-auth-origin
QT = core dbus
CONFIG += console c++11 link_pkgconfig
CONFIG -= app_bundle
PKGCONFIG += sailfishsecrets
INCLUDEPATH += /usr/include/Sailfish
SOURCES = auth-origin.cpp
