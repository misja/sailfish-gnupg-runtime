# Packaging-only build adapter: use installed system development interfaces.
TEMPLATE = app
TARGET = pinentry
QT -= gui
QT += core dbus
CONFIG += link_pkgconfig c++11
PKGCONFIG += sailfishsecrets mlite5 gpg-error
LIBS += -lassuan
HEADERS += qassuanserver.h assuancompat.h
SOURCES += qassuanserver.cpp pinentry.cpp
